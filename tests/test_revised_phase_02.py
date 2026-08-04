"""Invariant tests for the Revised Phase 2 audit."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINTS = ROOT / "outputs" / "checkpoints"


def test_design_is_country_specific_and_phase_bounded() -> None:
    record = json.loads((CHECKPOINTS / "revised_phase_02_design_decision.json").read_text(encoding="utf-8"))
    assert record["country_strategy"].startswith("country-specific")
    assert "No final analytical dataset" in record["phase_boundary"]


def test_kazakhstan_registry_is_pending() -> None:
    with (CHECKPOINTS / "revised_phase_02_variable_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    kz = [row for row in rows if row["country"] == "kazakhstan"]
    assert len(kz) == 15
    assert all(row["status"] == "PENDING DATA ACCESS" for row in kz)
    assert all(row["raw_variable_names"] == "PENDING DATA ACCESS" for row in kz)


def test_minimum_mechanism_verified() -> None:
    record = json.loads((CHECKPOINTS / "revised_phase_02_design_decision.json").read_text(encoding="utf-8"))
    assert record["decision"] == "FULL TWO-COUNTRY DESIGN"
    assert record["kyrgyzstan_minimum_mechanism_verified"] is True
    assert record["uzbekistan_minimum_mechanism_verified"] is True


def test_key_integrity_output_is_aggregate_only() -> None:
    with (CHECKPOINTS / "revised_phase_02_key_integrity.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = {row["dataset"]: row for row in csv.DictReader(handle)}
    assert rows["L2CU household"]["duplicate_key_rows"] == "0"
    assert rows["L2CU individual roster"]["duplicate_key_rows"] == "0"
    assert "household-rounds have no individual-roster row" in rows["L2CU household"]["cross_file_note"]
    assert rows["LiK hh0"]["duplicate_key_rows"] == "0"


def test_no_analysis_side_effects_recorded() -> None:
    validation = json.loads((CHECKPOINTS / "revised_phase_02_validation.json").read_text(encoding="utf-8"))
    assert validation["processed_data_written"] is False
    assert validation["regression_run"] is False
    assert validation["countries_pooled"] is False
    assert validation["respondent_level_output_written"] is False
