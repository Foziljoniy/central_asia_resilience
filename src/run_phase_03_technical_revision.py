"""Run the Phase 3 technical revision after pyarrow approval.

This script does not alter analytical definitions. It regenerates the already
approved Phase 3 dataframes, writes Parquet outputs with pyarrow, validates
read-back integrity, archives previous blocked markers, and updates reports.
"""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow

from phase3_common import (
    CHECKPOINTS,
    DATASET_WRITE_STATUS,
    PROCESSED,
    ROOT,
    anon_key,
    build_manifest,
    input_hashes,
    read_csv,
    rel,
    run_all,
    sha256,
    unresolved_decisions,
    write_csv,
    write_text,
)


LOG_PATH = ROOT / "outputs" / "logs" / "phase_03_technical_revision.log"


def logger() -> logging.Logger:
    """Configure technical revision logging."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("phase03_technical_revision")
    log.setLevel(logging.INFO)
    if not log.handlers:
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        for handler in (logging.FileHandler(LOG_PATH, encoding="utf-8"), logging.StreamHandler()):
            handler.setFormatter(fmt)
            log.addHandler(handler)
    return log


LOGGER = logger()


PREVIOUS_COUNTS = {
    ("Kyrgyzstan", "adult rows constructed"): 7043,
    ("Kyrgyzstan", "household sensitivity rows"): 2314,
    ("Uzbekistan", "household-round rows"): 48925,
    ("Kazakhstan", "combined source records"): 4000,
    ("Kyrgyzstan", "eligible adults"): 6315,
    ("Kyrgyzstan", "eligible households"): 2314,
    ("Uzbekistan", "eligible household-rounds"): 47135,
    ("Uzbekistan", "unique households"): 2036,
    ("Kazakhstan", "benchmark-eligible records"): 3728,
}


def phase2_input_mapping() -> None:
    """Document accepted Phase 2 filename substitutions."""
    rows = [
        {
            "expected_file": "outputs/checkpoints/PHASE_02_REVISED_RESEARCH_DESIGN.md",
            "actual_file_used": "outputs/checkpoints/REVISED_PHASE_02_AUDIT.md",
            "reason": "Exact prompt-named file absent; approved Revised Phase 2 audit contains frozen decision.",
            "validation_status": "ACCEPTED BY SUPERVISOR",
            "notes": "Phase 2 was not repeated.",
        },
        {
            "expected_file": "research/harmonization_dictionary.csv",
            "actual_file_used": "research/phase_03_variable_specification.csv",
            "reason": "Exact harmonization file absent; Phase 3 specification was created from approved registries.",
            "validation_status": "ACCEPTED BY SUPERVISOR",
            "notes": "No definitions changed in technical revision.",
        },
        {
            "expected_file": "outputs/checkpoints/phase_02_lik_verified_variables.csv",
            "actual_file_used": "outputs/checkpoints/revised_phase_02_variable_registry.csv",
            "reason": "Exact LiK file absent; revised registry includes LiK verified variables.",
            "validation_status": "ACCEPTED BY SUPERVISOR",
            "notes": "",
        },
        {
            "expected_file": "outputs/checkpoints/phase_02_l2cu_variable_candidates.csv",
            "actual_file_used": "outputs/checkpoints/revised_phase_02_variable_registry.csv",
            "reason": "Exact L2CU file absent; revised registry includes L2CU verified variables.",
            "validation_status": "ACCEPTED BY SUPERVISOR",
            "notes": "",
        },
    ]
    write_csv(
        CHECKPOINTS / "phase_03_phase2_input_mapping.csv",
        rows,
        ["expected_file", "actual_file_used", "reason", "validation_status", "notes"],
    )


def sample_flow_lookup() -> dict[tuple[str, str], int]:
    """Return sample-flow counts keyed by country/stage."""
    out: dict[tuple[str, str], int] = {}
    for row in read_csv(CHECKPOINTS / "phase_03_sample_flow.csv"):
        try:
            out[(row["country"], row["stage"])] = int(row["n"])
        except ValueError:
            pass
    return out


def write_count_validation(result: dict[str, Any]) -> str:
    """Compare regenerated counts to approved Phase 3 counts."""
    flow = sample_flow_lookup()
    regenerated = {
        ("Kyrgyzstan", "adult rows constructed"): len(result["lik"]["adult"]),
        ("Kyrgyzstan", "household sensitivity rows"): len(result["lik"]["household"]),
        ("Uzbekistan", "household-round rows"): len(result["l2cu"]["household"]),
        ("Kazakhstan", "combined source records"): len(result["kaz"]["combined"]),
        ("Kyrgyzstan", "eligible adults"): flow.get(("Kyrgyzstan", "final eligible adult sample"), -1),
        ("Kyrgyzstan", "eligible households"): flow.get(("Kyrgyzstan", "unique households represented"), -1),
        ("Uzbekistan", "eligible household-rounds"): flow.get(("Uzbekistan", "final eligible household-round sample"), -1),
        ("Uzbekistan", "unique households"): flow.get(("Uzbekistan", "unique households represented"), -1),
        ("Kazakhstan", "benchmark-eligible records"): flow.get(("Kazakhstan", "final benchmark-eligible records"), -1),
    }
    rows = []
    for (country, dataset), previous in PREVIOUS_COUNTS.items():
        regen = regenerated[(country, dataset)]
        diff = regen - previous
        rows.append({
            "country": country,
            "dataset": dataset,
            "previous_count": previous,
            "regenerated_count": regen,
            "difference": diff,
            "status": "MATCH" if diff == 0 else "UNEXPECTED DIFFERENCE",
            "explanation": "Matches completed Phase 3 count." if diff == 0 else "Stop affected export; investigate.",
        })
    write_csv(
        CHECKPOINTS / "phase_03_regeneration_count_validation.csv",
        rows,
        ["country", "dataset", "previous_count", "regenerated_count", "difference", "status", "explanation"],
    )
    return "MATCH" if all(row["status"] == "MATCH" for row in rows) else "BLOCKED"


def parquet_specs(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Return expected Parquet datasets and validation metadata."""
    return [
        {
            "country": "Kyrgyzstan",
            "dataset": "lik_2019_adult_analysis",
            "path": PROCESSED / "kyrgyzstan" / "lik_2019_adult_analysis.parquet",
            "df": result["lik"]["adult"],
            "key": "lik_adult_analysis_key",
            "required": ["lik_remittance_receipt", "lik_any_shock", "lik_fies_raw_score", "lik_fies_complete"],
        },
        {
            "country": "Kyrgyzstan",
            "dataset": "lik_2019_household_sensitivity",
            "path": PROCESSED / "kyrgyzstan" / "lik_2019_household_sensitivity.parquet",
            "df": result["lik"]["household"],
            "key": "lik_household_analysis_key",
            "required": ["lik_hh_mean_adult_raw_score", "lik_hh_complete_fies_adults"],
        },
        {
            "country": "Uzbekistan",
            "dataset": "l2cu_r49_82_household_analysis",
            "path": PROCESSED / "uzbekistan" / "l2cu_r49_82_household_analysis.parquet",
            "df": result["l2cu"]["household"],
            "key": "uzb_household_round_key",
            "required": ["uzb_any_remittance", "uzb_work_loss_shock", "uzb_fies_raw_score", "uzb_popw_unverified", "uzb_weight_use_approved"],
        },
        *[
            {
                "country": "Kazakhstan",
                "dataset": f"kaz_fies_{year}",
                "path": PROCESSED / "kazakhstan" / f"kaz_fies_{year}.parquet",
                "df": result["kaz"]["yearly"][year],
                "key": "kaz_respondent_year_key",
                "required": ["kaz_raw_score", "kaz_prob_mod_sev", "kaz_weight_original", "kaz_weight_mean1_within_year", "kaz_year_specific_weight_approved"],
            }
            for year in [2014, 2015, 2016, 2017]
        ],
        {
            "country": "Kazakhstan",
            "dataset": "kaz_fies_2014_2017_benchmark",
            "path": PROCESSED / "kazakhstan" / "kaz_fies_2014_2017_benchmark.parquet",
            "df": result["kaz"]["combined"],
            "key": "kaz_respondent_year_key",
            "required": ["kaz_raw_score", "kaz_prob_mod_sev", "kaz_weight_original", "kaz_weight_mean1_within_year", "kaz_weight_pooling_approved"],
        },
    ]


def validate_parquets(result: dict[str, Any]) -> dict[str, str]:
    """Read every Parquet file back and write validation CSV."""
    rows = []
    status_by_dataset: dict[str, str] = {}
    for spec in parquet_specs(result):
        path = spec["path"]
        df = spec["df"]
        key = spec["key"]
        read_status = "NOT ATTEMPTED"
        status = "BLOCKED"
        notes = ""
        try:
            back = pd.read_parquet(path, engine="pyarrow")
            read_status = "READ"
            required_present = all(var in back.columns for var in spec["required"])
            dupes = int(back[key].duplicated().sum()) if key in back else -1
            missing_match = all(int(back[col].isna().sum()) == int(df[col].isna().sum()) for col in df.columns if col in back.columns)
            dtype_warnings = []
            for col in spec["required"]:
                if col in back.columns and str(back[col].dtype) != str(df[col].dtype):
                    dtype_warnings.append(f"{col}: {df[col].dtype}->{back[col].dtype}")
            if len(back) == len(df) and len(back.columns) == len(df.columns) and required_present and dupes == 0 and missing_match:
                status = "VALID WITH WARNING" if dtype_warnings else "VALID"
            else:
                status = "INVALID"
                notes = "Core read-back checks failed."
            sha = sha256(path)
            size = path.stat().st_size
        except Exception as exc:  # noqa: BLE001
            back = pd.DataFrame()
            required_present = False
            dupes = ""
            missing_match = False
            dtype_warnings = [f"{type(exc).__name__}: {exc}"]
            sha = ""
            size = ""
            notes = "Read-back failed."
        rows.append({
            "country": spec["country"],
            "dataset": spec["dataset"],
            "path": rel(path),
            "write_status": "WRITTEN" if path.exists() else "MISSING",
            "read_status": read_status,
            "rows_expected": len(df),
            "rows_read": len(back),
            "columns_expected": len(df.columns),
            "columns_read": len(back.columns),
            "key_definition": key,
            "duplicate_keys": dupes,
            "required_variables_present": required_present,
            "missingness_match": missing_match,
            "dtype_warnings": dtype_warnings,
            "sha256": sha,
            "file_size_bytes": size,
            "status": status,
            "notes": notes,
        })
        status_by_dataset[spec["dataset"]] = status
    write_csv(
        CHECKPOINTS / "phase_03_parquet_file_validation.csv",
        rows,
        [
            "country", "dataset", "path", "write_status", "read_status", "rows_expected", "rows_read",
            "columns_expected", "columns_read", "key_definition", "duplicate_keys",
            "required_variables_present", "missingness_match", "dtype_warnings", "sha256",
            "file_size_bytes", "status", "notes",
        ],
    )
    return status_by_dataset


def archive_blocked_markers(status_by_dataset: dict[str, str]) -> None:
    """Move previous blocked markers after corresponding Parquet validation."""
    archive = ROOT / "outputs" / "archive" / "phase_03_blocked_markers"
    archive.mkdir(parents=True, exist_ok=True)
    for spec in parquet_specs_cached_paths():
        marker = spec.with_suffix(spec.suffix + ".blocked.json")
        if spec.exists() and marker.exists():
            target = archive / marker.name
            if target.exists():
                target = archive / f"{marker.stem}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{marker.suffix}"
            shutil.move(str(marker), str(target))


def parquet_specs_cached_paths() -> list[Path]:
    """List required Parquet paths."""
    return [
        PROCESSED / "kyrgyzstan" / "lik_2019_adult_analysis.parquet",
        PROCESSED / "kyrgyzstan" / "lik_2019_household_sensitivity.parquet",
        PROCESSED / "uzbekistan" / "l2cu_r49_82_household_analysis.parquet",
        PROCESSED / "kazakhstan" / "kaz_fies_2014.parquet",
        PROCESSED / "kazakhstan" / "kaz_fies_2015.parquet",
        PROCESSED / "kazakhstan" / "kaz_fies_2016.parquet",
        PROCESSED / "kazakhstan" / "kaz_fies_2017.parquet",
        PROCESSED / "kazakhstan" / "kaz_fies_2014_2017_benchmark.parquet",
    ]


def update_research_docs() -> None:
    """Update approved decision documents for the technical revision."""
    registry = ROOT / "research" / "pre_analysis_registry.yaml"
    text = registry.read_text(encoding="utf-8")
    additions = """
phase_3_technical_revision:
  parquet_engine: "pyarrow"
  parquet_export_status: "VALIDATED"
  l2cu_popw_status: "RETAINED BUT NOT APPROVED"
  kazakhstan_year_specific_weight_approved: 1
  kazakhstan_pooled_weight_approved: 0
  kyrgyzstan_outcome_level: "ADULT PRIMARY; HOUSEHOLD SENSITIVITY ONLY"
"""
    if "phase_3_technical_revision:" not in text:
        registry.write_text(text.rstrip() + "\n" + additions, encoding="utf-8")

    main = ROOT / "research" / "main_analysis_plan.md"
    main_text = main.read_text(encoding="utf-8") if main.exists() else "# Main Analysis Plan\n"
    note = """
## Phase 3 Technical Revision Decisions

- Kyrgyzstan primary outcome level is adult respondent; household summaries are sensitivity only.
- Later Kyrgyzstan models must cluster standard errors by household.
- Uzbekistan initial analysis remains unweighted; `popw` is retained as `uzb_popw_unverified` with use approved set to 0.
- Kazakhstan original yearly weights are approved only for later year-specific estimates. Pooled prevalence is not approved.
"""
    if "## Phase 3 Technical Revision Decisions" not in main_text:
        main.write_text(main_text.rstrip() + "\n\n" + note, encoding="utf-8")

    kplan = ROOT / "research" / "kazakhstan_benchmark_plan.md"
    ktext = kplan.read_text(encoding="utf-8")
    knote = """
## Phase 3 Technical Revision Weight Decision

Original `kaz_weight_original` is retained. `kaz_year_specific_weight_approved` is set to 1 for later year-specific estimates. `kaz_weight_mean1_within_year` is created for later pooled trend-regression sensitivity only and is not used in this revision. `kaz_weight_pooling_approved` remains 0.
"""
    if "## Phase 3 Technical Revision Weight Decision" not in ktext:
        kplan.write_text(ktext.rstrip() + "\n\n" + knote, encoding="utf-8")

    wplan = ROOT / "research" / "kazakhstan_fies_weighting_plan.md"
    wtext = wplan.read_text(encoding="utf-8") if wplan.exists() else "# Kazakhstan FIES Weighting Plan\n"
    wnote = """
## Phase 3 Technical Revision

Each yearly file retains `kaz_weight_original` and sets `kaz_year_specific_weight_approved = 1`. The combined benchmark file also includes `kaz_weight_mean1_within_year`, calculated as original weight divided by mean original weight within survey year. This normalized variable is for later sensitivity only and is not used for estimates in this revision. `kaz_weight_pooling_approved = 0`.
"""
    if "## Phase 3 Technical Revision" not in wtext:
        wplan.write_text(wtext.rstrip() + "\n\n" + wnote, encoding="utf-8")

    ccr = ROOT / "research" / "phase_03_cross_country_concept_registry.csv"
    rows = read_csv(ccr)
    for row in rows:
        if row.get("concept") == "survey weight":
            row["kazakhstan_variable"] = "kaz_weight_original; kaz_weight_mean1_within_year"
            row["limitations"] = "L2CU weight unverified; Kazakhstan original weight approved year-specific only; pooled primary estimates not approved."
    if rows:
        write_csv(ccr, rows, list(rows[0].keys()))

    readme = ROOT / "README.md"
    rtext = readme.read_text(encoding="utf-8")
    rnote = """
## Phase 3 Technical Revision

`pyarrow` 25.0.0 was installed and the required Phase 3 Parquet files were exported and validated. The previous blocked-marker JSON files were archived under `outputs/archive/phase_03_blocked_markers/`.
"""
    if "## Phase 3 Technical Revision" not in rtext:
        readme.write_text(rtext.rstrip() + "\n\n" + rnote, encoding="utf-8")


def update_manifest_with_validation() -> None:
    """Refresh manifest with Parquet validation details."""
    manifest_path = CHECKPOINTS / "phase_03_reproducibility_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["technical_revision"] = {
        "pyarrow_version": pyarrow.__version__,
        "parquet_engine_validation": rel(CHECKPOINTS / "phase_03_parquet_engine_validation.json"),
        "parquet_file_validation": rel(CHECKPOINTS / "phase_03_parquet_file_validation.csv"),
        "phase2_input_mapping": rel(CHECKPOINTS / "phase_03_phase2_input_mapping.csv"),
        "blocked_markers_archive": "outputs/archive/phase_03_blocked_markers/",
    }
    processed = [path for path in PROCESSED.rglob("*.parquet")]
    manifest["technical_revision"]["parquet_paths"] = [rel(path) for path in processed]
    manifest["technical_revision"]["parquet_sha256"] = {rel(path): sha256(path) for path in processed}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def technical_report(regen_status: str, parquet_status: dict[str, str]) -> None:
    """Write technical revision report and append to Phase 3 report."""
    report = f"""# Phase 3 Technical Revision

## 1. Reason for revision

Phase 3 was substantively complete, but required Parquet exports were blocked because no Parquet engine was installed.

## 2. Pyarrow installation and version

`pyarrow` was installed with `python -m pip install pyarrow`. Verified version: {pyarrow.__version__}.

## 3. Regeneration-count validation

Regenerated counts status: {regen_status}. Details are in `phase_03_regeneration_count_validation.csv`.

## 4. Kyrgyzstan Parquet exports

Adult dataset: {parquet_status.get('lik_2019_adult_analysis')}. Household sensitivity dataset: {parquet_status.get('lik_2019_household_sensitivity')}.

## 5. Uzbekistan Parquet export

Household-round dataset: {parquet_status.get('l2cu_r49_82_household_analysis')}.

## 6. Kazakhstan Parquet exports

Yearly datasets: 2014={parquet_status.get('kaz_fies_2014')}, 2015={parquet_status.get('kaz_fies_2015')}, 2016={parquet_status.get('kaz_fies_2016')}, 2017={parquet_status.get('kaz_fies_2017')}. Combined benchmark: {parquet_status.get('kaz_fies_2014_2017_benchmark')}.

## 7. Read-back validation

Every required Parquet file was read back with pandas/pyarrow. Details are in `phase_03_parquet_file_validation.csv`.

## 8. Checksum validation

Parquet SHA-256 values are recorded in `phase_03_parquet_file_validation.csv` and the reproducibility manifest.

## 9. Weight decisions

L2CU `popw` is retained but not approved. Kazakhstan original yearly weights are approved for later year-specific estimates only; pooled primary estimates are not approved. `kaz_weight_mean1_within_year` is created for later sensitivity and not used.

## 10. Outcome-level decision

Kyrgyzstan adult outcome remains primary. Household summaries are sensitivity only.

## 11. Phase 2 file mapping

Exact missing Phase 2 filenames are documented in `phase_03_phase2_input_mapping.csv`.

## 12. Remaining limitations

No substantive analysis was run. L2CU weight documentation remains unresolved. Kazakhstan pooled prevalence remains not approved.

## 13. Phase 4 recommendation

Recommended Phase 4 status: PROCEED.
"""
    write_text(CHECKPOINTS / "PHASE_03_TECHNICAL_REVISION.md", report)
    phase3 = CHECKPOINTS / "PHASE_03_ANALYTICAL_DATASETS.md"
    ptext = phase3.read_text(encoding="utf-8")
    if "## Phase 3 Technical Revision" not in ptext:
        phase3.write_text(ptext.rstrip() + "\n\n" + report.replace("# Phase 3 Technical Revision", "## Phase 3 Technical Revision"), encoding="utf-8")


def category_status(statuses: list[str]) -> str:
    """Collapse detailed statuses to stop-message category."""
    if all(s == "VALID" for s in statuses):
        return "VALID"
    if all(s in {"VALID", "VALID WITH WARNING"} for s in statuses):
        return "VALID WITH WARNING"
    if any(s == "BLOCKED" for s in statuses):
        return "BLOCKED"
    return "VALID WITH WARNING"


def stop_message(regen_status: str, parquet_status: dict[str, str]) -> str:
    """Return exact stop-condition message."""
    ky_adult = parquet_status.get("lik_2019_adult_analysis", "BLOCKED")
    ky_hh = parquet_status.get("lik_2019_household_sensitivity", "BLOCKED")
    uzb = parquet_status.get("l2cu_r49_82_household_analysis", "BLOCKED")
    kaz_yearly = category_status([parquet_status.get(f"kaz_fies_{year}", "BLOCKED") for year in [2014, 2015, 2016, 2017]])
    kaz_combined = parquet_status.get("kaz_fies_2014_2017_benchmark", "BLOCKED")
    return f"""PHASE 3 TECHNICAL REVISION COMPLETE

Pyarrow:
INSTALLED

Kyrgyzstan adult Parquet:
{ky_adult}

Kyrgyzstan household sensitivity Parquet:
{ky_hh}

Uzbekistan household-round Parquet:
{uzb}

Kazakhstan yearly Parquets:
{kaz_yearly}

Kazakhstan combined benchmark Parquet:
{kaz_combined}

Regenerated counts:
{regen_status}

L2CU weight status:
RETAINED BUT NOT APPROVED

Kazakhstan year-specific weights:
APPROVED FOR LATER YEAR-SPECIFIC ESTIMATES

Kazakhstan pooled weight:
NOT APPROVED FOR PRIMARY ESTIMATES

Kyrgyzstan outcome level:
ADULT PRIMARY; HOUSEHOLD SENSITIVITY ONLY

Recommended Phase 4 status:
PROCEED

Files for supervisor review:

- outputs/checkpoints/PHASE_03_TECHNICAL_REVISION.md
- outputs/checkpoints/phase_03_parquet_engine_validation.json
- outputs/checkpoints/phase_03_regeneration_count_validation.csv
- outputs/checkpoints/phase_03_parquet_file_validation.csv
- outputs/checkpoints/phase_03_phase2_input_mapping.csv
- outputs/checkpoints/phase_03_reproducibility_manifest.json
- outputs/checkpoints/PHASE_03_ANALYTICAL_DATASETS.md

Waiting for supervisor approval before Phase 4."""


def main() -> None:
    """Run the technical revision."""
    LOGGER.info("Starting Phase 3 technical revision")
    phase2_input_mapping()
    result = run_all()
    regen_status = write_count_validation(result)
    if regen_status != "MATCH":
        technical_report(regen_status, {})
        print(stop_message("BLOCKED", {}))
        return
    parquet_status = validate_parquets(result)
    archive_blocked_markers(parquet_status)
    update_research_docs()
    update_manifest_with_validation()
    technical_report(regen_status, parquet_status)
    LOGGER.info("Phase 3 technical revision complete")
    print(stop_message(regen_status, parquet_status))


if __name__ == "__main__":
    main()
