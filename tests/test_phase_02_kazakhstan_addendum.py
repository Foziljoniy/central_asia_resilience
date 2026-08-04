"""Invariant tests for the Phase 2 Kazakhstan FIES addendum."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINTS = ROOT / "outputs" / "checkpoints"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_kazakhstan_addendum_validation_passed() -> None:
    validation = json.loads((CHECKPOINTS / "phase_02_kazakhstan_addendum_validation.json").read_text(encoding="utf-8"))
    assert all(validation.values())


def test_all_source_hashes_unchanged() -> None:
    rows = read_csv(CHECKPOINTS / "kazakhstan_fies_source_checksum_audit.csv")
    assert len(rows) == 21
    assert all(row["unchanged"] == "true" for row in rows)


def test_fies_items_verified_for_each_year() -> None:
    rows = read_csv(CHECKPOINTS / "kazakhstan_fies_item_registry.csv")
    by_year = {}
    for row in rows:
        by_year.setdefault(row["survey_year"], set()).add(row["variable_name"])
        assert row["yes_code"] == "1"
        assert row["no_code"] == "0"
        assert row["other_missing_codes"] == "blank/system missing"
    for year in ["2014", "2015", "2016", "2017"]:
        assert by_year[year] == {"WORRIED", "HEALTHY", "FEWFOOD", "SKIPPED", "ATELESS", "RUNOUT", "HUNGRY", "WHLDAY"}


def test_kazakhstan_does_not_enter_interaction_model() -> None:
    rows = read_csv(CHECKPOINTS / "kazakhstan_fies_concept_availability.csv")
    blocked = [row for row in rows if row["concept"] in {"migration/remittances", "household shocks"}]
    assert blocked
    assert all(row["classification"] == "NOT AVAILABLE" for row in blocked)
    registry = (ROOT / "research" / "pre_analysis_registry.yaml").read_text(encoding="utf-8")
    assert 'kazakhstan_interaction_model_feasible: "NOT FEASIBLE"' in registry
    assert 'main_design_decision: "FULL TWO-COUNTRY DESIGN"' in registry
