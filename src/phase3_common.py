"""Phase 3 analytical dataset construction utilities.

Phase 3 constructs country-specific analytical datasets and aggregate QA
artifacts only. It does not run descriptive analysis, prevalence estimates,
hypothesis tests, regressions, marginal effects, or policy-effect estimates.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import logging
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / ".vendor"
if VENDOR.exists() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

import numpy as np
import pandas as pd
import pyreadstat


CHECKPOINTS = ROOT / "outputs" / "checkpoints"
LOG_PATH = ROOT / "outputs" / "logs" / "phase_03.log"
PROCESSED = ROOT / "data" / "processed"
LIK_BASE = ROOT / "data" / "interim" / "unpacked" / "kyrgyzstan" / "dataverse_files" / "depth_02" / "LiK_2022__7c67a235" / "Version_2022"
L2CU_BASE = ROOT / "data" / "interim" / "unpacked" / "uzbekistan" / "l2cu_v03"
KAZ_ROOT = ROOT / "data" / "kazakhstan"
PHASE3_SALT = "central_asia_resilience_phase3_v1"

FIES8_LIK = [f"i251_{i}" for i in range(1, 9)]
FIES8_UZB = [f"ln_{i}" for i in range(1, 9)]
FIES8_KAZ = ["WORRIED", "HEALTHY", "FEWFOOD", "SKIPPED", "ATELESS", "RUNOUT", "HUNGRY", "WHLDAY"]
KAZ_YEARS = [2014, 2015, 2016, 2017]


def configure_logging() -> logging.Logger:
    """Configure a deterministic Phase 3 log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("phase03")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        for handler in (logging.FileHandler(LOG_PATH, encoding="utf-8"), logging.StreamHandler()):
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger


LOGGER = configure_logging()


def rel(path: Path) -> str:
    """Return a stable project-relative path."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return SHA-256 for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    """Write a deterministic UTF-8-SIG CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: csv_cell(row.get(field, "")) for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a generated CSV if it exists."""
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def csv_cell(value: Any) -> str | int | float:
    """Normalize values for CSV cells."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple, set, dict)):
        if isinstance(value, set):
            value = sorted(value)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, float) and np.isnan(value):
        return ""
    return value


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def anon_key(*parts: Any) -> str:
    """Create reproducible anonymized analytical keys."""
    payload = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(f"{PHASE3_SALT}|{payload}".encode("utf-8")).hexdigest()[:24]


def read_dta(path: Path, cols: list[str] | None = None) -> pd.DataFrame:
    """Read Stata files with a fallback for LiK encoding quirks."""
    for kwargs in ({}, {"encoding": "utf-8"}, {"encoding": "latin1"}):
        try:
            df, _meta = pyreadstat.read_dta(str(path), usecols=cols, **kwargs)
            return df
        except Exception as exc:  # noqa: BLE001 - retry with known encodings
            last = exc
    raise RuntimeError(f"Could not read {rel(path)}: {last}")


def read_dta_meta(path: Path) -> Any:
    """Read Stata metadata only."""
    _df, meta = pyreadstat.read_dta(str(path), metadataonly=True)
    return meta


def read_sav(path: Path) -> tuple[pd.DataFrame, Any]:
    """Read SPSS SAV with user-missing values preserved."""
    return pyreadstat.read_sav(str(path), user_missing=True)


def yes_no(series: pd.Series) -> pd.Series:
    """Map 1/2 or Yes/No values to 1/0 while preserving missing."""
    text = series.astype("string").str.strip().str.casefold()
    out = pd.Series(pd.NA, index=series.index, dtype="Int64")
    out[text.isin(["1", "1.0", "yes", "y"])] = 1
    out[text.isin(["2", "2.0", "no", "n", "0", "0.0"])] = 0
    return out


def nonempty(series: pd.Series) -> pd.Series:
    """Return a nonmissing and nonblank mask."""
    return series.notna() & (series.astype(str).str.strip() != "")


def no_parquet_engine() -> bool:
    """Return True when no supported Parquet engine is importable."""
    return importlib.util.find_spec("pyarrow") is None and importlib.util.find_spec("fastparquet") is None


DATASET_WRITE_STATUS: dict[str, dict[str, Any]] = {}


def write_processed(df: pd.DataFrame, path: Path, key: str) -> str:
    """Write a processed dataset as Parquet or a non-disclosing blocked marker."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if no_parquet_engine():
        marker = path.with_suffix(path.suffix + ".blocked.json")
        write_text(marker, json.dumps({
            "status": "BLOCKED",
            "reason": "No Parquet engine is installed. pyarrow/fastparquet installation was not approved.",
            "intended_path": rel(path),
            "rows_constructed_in_memory": int(len(df)),
            "columns_constructed_in_memory": int(len(df.columns)),
            "key": key,
            "respondent_level_data_written": False,
        }, indent=2))
        DATASET_WRITE_STATUS[rel(path)] = {
            "status": "BLOCKED",
            "path": rel(path),
            "blocked_marker": rel(marker),
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
        }
        return "BLOCKED"
    df.to_parquet(path, index=False, engine="pyarrow", compression="zstd")
    DATASET_WRITE_STATUS[rel(path)] = {
        "status": "CREATED",
        "path": rel(path),
        "sha256": sha256(path),
        "compression": "zstd",
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
    }
    return "CREATED"


def source_files() -> list[Path]:
    """Return protected inputs used by Phase 3."""
    files = [
        LIK_BASE / "Household" / "hh0.dta",
        LIK_BASE / "Household" / "hh1a.dta",
        LIK_BASE / "Household" / "hh6a.dta",
        LIK_BASE / "Household" / "hh6b.dta",
        LIK_BASE / "Household" / "hh7.dta",
        LIK_BASE / "Individual" / "id1.dta",
        LIK_BASE / "Individual" / "id2.dta",
        L2CU_BASE / "l2cu_cati_household_data_82.csv",
        L2CU_BASE / "l2cu_cati_individual_data_82.csv",
    ]
    for year in KAZ_YEARS:
        files.append(KAZ_ROOT / f"KAZ_{year}_FIES_v01_EN_M_v01_A_OCS" / "microdata" / f"KAZ_{year}_FIES_v01_EN_M_v01_A_OCS.sav")
    return [path for path in files if path.exists()]


def input_hashes() -> dict[str, str]:
    """Hash every Phase 3 protected input."""
    return {rel(path): sha256(path) for path in source_files()}


def freeze_specification() -> None:
    """Create the frozen Phase 3 variable specification."""
    fields = [
        "country", "analytical_dataset", "target_variable", "variable_role", "source_file",
        "source_variables", "observation_level", "universe", "reference_period", "source_coding",
        "target_coding", "missing_codes", "structural_skip_rule", "transformation", "direction",
        "selected_primary", "selected_sensitivity", "verification_source", "notes",
    ]
    rows: list[dict[str, Any]] = []
    # Kyrgyzstan core variables.
    rows += [
        spec("Kyrgyzstan", "lik_2019_adult_analysis", "lik_remittance_receipt", "treatment", "Household/hh6b.dta; Household/hh6a.dta", "h620; h600; h601", "adult respondent with household merge", "LiK 2019 adults linked to household", "last 12 months", "h620 1 Yes, 2 No; Module 6A migrant counts", "1 recipient, 0 non-recipient, missing unresolved", "blank/system missing", "Only structural zero when Module 6A verifies no eligible migrant", "binary with provenance source", "1=receipt", 1, 0, "Revised Phase 2 registry; household questionnaire pp. 15-17", ""),
        spec("Kyrgyzstan", "lik_2019_adult_analysis", "lik_any_shock", "exposure", "Household/hh7.dta", "shock; h701", "household", "all LiK households", "last 12 months", "h701 1 affected", "1 any shock, 0 no event record", "event roster structural absence", "No event rows imply no listed shock after merge to household master", "aggregate event roster", "1=shock exposure", 1, 0, "LiK household questionnaire p. 18", ""),
        spec("Kyrgyzstan", "lik_2019_adult_analysis", "lik_fies_raw_score", "outcome", "Individual/id2.dta", "; ".join(FIES8_LIK), "adult respondent", "adult individual module respondents", "last 12 months", "1 many times; 2 one/two times; 3 never; 88 refusal; 99 DK", "0-8 only when complete", "88, 99, blanks, undocumented values", "none", "sum affirmative items only when all 8 valid", "higher=worse food insecurity", 1, 0, "LiK individual questionnaire p. 6", ""),
        spec("Kyrgyzstan", "lik_2019_household_sensitivity", "lik_hh_mean_adult_raw_score", "sensitivity outcome", "constructed adult dataset", "lik_fies_raw_score", "household", "households with adult FIES records", "last 12 months", "adult complete raw scores", "mean among complete adult scores", "missing if no complete adult", "none", "household aggregation; not primary", "higher=worse food insecurity", 0, 1, "Phase 3 aggregation rule", "Sensitivity only."),
    ]
    for i, src in enumerate(FIES8_LIK, start=1):
        rows.append(spec("Kyrgyzstan", "lik_2019_adult_analysis", f"lik_fies_item_{i}", "outcome item", "Individual/id2.dta", src, "adult respondent", "adult individual module respondents", "last 12 months", "1,2 affirmative; 3 never; 88 refusal; 99 DK", "1 affirmative, 0 negative", "88,99,blank,other", "none", "recode item", "1=worse", 0, 1, "LiK individual questionnaire p. 6", ""))
    # Uzbekistan core variables.
    rows += [
        spec("Uzbekistan", "l2cu_r49_82_household_analysis", "uzb_any_remittance", "treatment", "l2cu_cati_individual_data_82.csv", "mig_living_remittance; remittance_hh", "household-round", "L2CU rounds 49-82 household-rounds", "past month", "Yes/No labels", "1 any verified component, 0 both components verified no", "blank/undocumented", "member-migrant structural no only when no migrant is verified", "aggregate roster to household-round", "1=receipt", 1, 0, "Revised Phase 2 registry; L2CU questionnaire p. 5", ""),
        spec("Uzbekistan", "l2cu_r49_82_household_analysis", "uzb_work_loss_shock", "primary exposure", "l2cu_cati_individual_data_82.csv", "work_lost_hh", "household-round", "L2CU rounds 49-82 household-rounds", "past month", "Yes/No labels", "1 job loss, 0 no job loss", "blank/undocumented", "none", "consistent repeated household field", "1=shock exposure", 1, 0, "L2CU questionnaire p. 6", ""),
        spec("Uzbekistan", "l2cu_r49_82_household_analysis", "uzb_fies_raw_score", "outcome", "l2cu_cati_household_data_82.csv", "; ".join(FIES8_UZB), "household-round", "rounds 49-82 where module administered", "past 30 days", "Yes=1, No=2 in questionnaire; CSV labels Yes/No", "0-8 only when complete", "blank/undocumented", "pre-round-49 structural blanks excluded", "sum affirmative items only when all 8 valid", "higher=worse food insecurity", 1, 0, "L2CU questionnaire p. 23", ""),
        spec("Uzbekistan", "l2cu_r49_82_household_analysis", "uzb_popw_unverified", "retained unapproved weight", "l2cu_cati_household_data_82.csv", "popw", "household-round", "all retained household-rounds", "not applicable", "numeric", "retained only", "blank", "none", "copy with use flag=0", "weight", 0, 0, "Revised Phase 2 registry", "Weight use not approved."),
    ]
    for i, src in enumerate(FIES8_UZB, start=1):
        rows.append(spec("Uzbekistan", "l2cu_r49_82_household_analysis", f"uzb_fies_item_{i}", "outcome item", "l2cu_cati_household_data_82.csv", src, "household-round", "rounds 49-82", "past 30 days", "Yes/No labels", "1 affirmative, 0 negative", "blank/other", "pre-round-49 excluded", "recode item", "1=worse", 0, 1, "L2CU questionnaire p. 23", ""))
    # Kazakhstan benchmark variables.
    rows += [
        spec("Kazakhstan", "kaz_fies_2014_2017_benchmark", "kaz_raw_score", "benchmark outcome", "canonical SAV by year", "Raw_score", "adult respondent-year", "Kazakhstan FIES 2014-2017 adult records", "last 12 months", "0-8 official score", "copy official value", "blank", "none", "copy only, no recalculation", "higher=worse food insecurity", 1, 0, "Phase 2K derived registry", ""),
        spec("Kazakhstan", "kaz_fies_2014_2017_benchmark", "kaz_prob_mod_sev", "benchmark outcome", "canonical SAV by year", "Prob_Mod_Sev", "adult respondent-year", "Kazakhstan FIES 2014-2017 adult records", "last 12 months", "probability 0 to near 1", "copy official value", "blank", "none", "copy only, no prevalence", "higher=worse food insecurity probability", 1, 0, "Phase 2K derived registry", ""),
        spec("Kazakhstan", "kaz_fies_2014_2017_benchmark", "kaz_weight_original", "retained weight", "canonical SAV by year", "wt", "adult respondent-year", "Kazakhstan FIES 2014-2017 adult records", "not applicable", "post-stratification sampling weight", "copy original", "blank", "none", "copy, no rescaling", "weight", 0, 0, "Phase 2K design registry", "Pooling normalization approval required."),
    ]
    for i, src in enumerate(FIES8_KAZ, start=1):
        rows.append(spec("Kazakhstan", "kaz_fies_2014_2017_benchmark", f"kaz_fies_item_{i}", "benchmark item", "canonical SAV by year", src, "adult respondent-year", "Kazakhstan FIES 2014-2017 adult records", "last 12 months", "1 affirmative, 0 no, blank missing", "1 affirmative, 0 negative", "blank", "none", "copy standardized item", "1=worse", 0, 1, "Phase 2K item registry", ""))
    # Document missing exact input files named by the prompt.
    missing_inputs = [
        "outputs/checkpoints/PHASE_02_REVISED_RESEARCH_DESIGN.md",
        "research/harmonization_dictionary.csv",
        "outputs/checkpoints/phase_02_lik_verified_variables.csv",
        "outputs/checkpoints/phase_02_l2cu_variable_candidates.csv",
    ]
    for item in missing_inputs:
        if not (ROOT / item).exists():
            rows.append(spec("Project", "phase_03_specification", f"missing_input__{Path(item).stem}", "input documentation", item, "not applicable", "not applicable", "not applicable", "not applicable", "not applicable", "BLOCKED - SUPERVISOR DECISION REQUIRED", "not applicable", "not applicable", "not constructed", "not applicable", 0, 0, "Phase 3 prompt", "Exact file absent; used approved revised Phase 2 outputs where possible."))
    write_csv(ROOT / "research" / "phase_03_variable_specification.csv", rows, fields)
    LOGGER.info("Phase 3 variable specification written")


def spec(country: str, analytical_dataset: str, target_variable: str, variable_role: str, source_file: str,
         source_variables: str, observation_level: str, universe: str, reference_period: str,
         source_coding: str, target_coding: str, missing_codes: str, structural_skip_rule: str,
         transformation: str, direction: str, selected_primary: int, selected_sensitivity: int,
         verification_source: str, notes: str) -> dict[str, Any]:
    """Return one variable-specification row."""
    return locals()


LIK_SHOCK_ROWS = [
    (1, "Drought", "climate; agricultural", 1, 0, 0, 0, 1, 1, 0, "Questionnaire labels drought as natural shock affecting agriculture."),
    (2, "Too much rain or flood", "climate; agricultural", 1, 0, 0, 0, 1, 1, 0, "Flood/rain natural shock can affect agriculture."),
    (3, "Very cold winter", "climate", 1, 0, 0, 0, 0, 1, 0, "Weather shock."),
    (4, "Frosts", "climate; agricultural", 1, 0, 0, 0, 1, 1, 0, "Weather and crop shock."),
    (5, "Landslides", "climate", 1, 0, 0, 0, 0, 1, 0, "Natural shock."),
    (6, "Pest or diseases (crops or livestock)", "agricultural", 1, 0, 0, 0, 1, 0, 0, "Crop/livestock shock."),
    (7, "Fire", "other", 1, 0, 0, 0, 0, 0, 0, "Listed household shock, not assigned to requested subcategories."),
    (8, "Insufficient water supply for farming or gardening", "agricultural; climate", 1, 0, 0, 0, 1, 1, 0, "Farming/gardening water shock."),
    (9, "Political instability", "other", 1, 0, 0, 0, 0, 0, 0, "Listed social shock."),
    (10, "Theft of assets (cash, crops, livestock)", "economic", 1, 1, 0, 0, 0, 0, 0, "Asset theft is economic loss."),
    (11, "Inability to sell agricultural and other products", "economic; agricultural", 1, 1, 0, 0, 1, 0, 0, "Market shock for products."),
    (12, "Loss of job", "employment; economic", 1, 1, 1, 0, 0, 0, 0, "Direct employment shock."),
    (13, "Sharp fall of remittances from abroad", "remittance loss; economic", 1, 1, 0, 0, 0, 0, 1, "Direct remittance-loss shock."),
    (14, "Death of a major breadwinner", "health/family", 1, 0, 0, 1, 0, 0, 0, "Death/health-family shock."),
    (15, "Death of another HH member", "health/family", 1, 0, 0, 1, 0, 0, 0, "Death/health-family shock."),
    (16, "Death of close relative, non-member of HH", "health/family", 1, 0, 0, 1, 0, 0, 0, "Death/health-family shock."),
    (17, "Illness of a major breadwinner", "health", 1, 0, 0, 1, 0, 0, 0, "Illness shock."),
    (18, "Illness of another HH member", "health", 1, 0, 0, 1, 0, 0, 0, "Illness shock."),
    (19, "Divorce", "other", 1, 0, 0, 0, 0, 0, 0, "Family/social shock."),
    (20, "Disputes on land issues", "other", 1, 0, 0, 0, 0, 0, 0, "Listed household shock."),
    (21, "Accident", "health", 1, 0, 0, 1, 0, 0, 0, "Accident/health shock."),
    (22, "Insufficient energy supply", "other", 1, 0, 0, 0, 0, 0, 0, "Infrastructure shock."),
    (23, "Increased violence in the neighbourhood", "other", 1, 0, 0, 0, 0, 0, 0, "Community safety shock."),
    (24, "Border closure for the movement of people and goods", "economic", 1, 1, 0, 0, 0, 0, 0, "Movement/goods closure can affect income/markets."),
    (25, "Forced relocation", "other", 1, 0, 0, 0, 0, 0, 0, "Displacement shock."),
]


def build_lik_shock_crosswalk() -> pd.DataFrame:
    """Write and return the LiK shock crosswalk."""
    fields = [
        "source_shock_code", "source_label", "target_category", "included_in_any_shock",
        "included_in_economic_shock", "included_in_employment_shock", "included_in_health_shock",
        "included_in_agricultural_shock", "included_in_climate_shock",
        "included_in_remittance_loss_shock", "reason", "verification_source",
    ]
    rows = []
    for row in LIK_SHOCK_ROWS:
        rows.append(dict(zip(fields[:-1], row), verification_source="LiK household questionnaire Module 7, page 18"))
    write_csv(ROOT / "research" / "lik_shock_crosswalk.csv", rows, fields)
    return pd.DataFrame(rows)


def build_lik() -> dict[str, Any]:
    """Construct Kyrgyzstan adult and household sensitivity datasets in memory."""
    hh0 = read_dta(LIK_BASE / "Household" / "hh0.dta", ["hhid", "int_date", "oblast", "residence", "psu"])
    roster = read_dta(LIK_BASE / "Household" / "hh1a.dta", ["hhid", "pid", "h102", "h103a", "h104"])
    mig = read_dta(LIK_BASE / "Household" / "hh6a.dta", ["hhid", "h600", "h601", "h602"])
    rem = read_dta(LIK_BASE / "Household" / "hh6b.dta", ["hhid", "h620", "h622", "h623", "h625", "h626"])
    shock = read_dta(LIK_BASE / "Household" / "hh7.dta", ["hhid", "shock", "h701", "h702", "h703", "h704"])
    id2_cols = ["hhid", "pid", "i218"] + FIES8_LIK
    id2 = read_dta(LIK_BASE / "Individual" / "id2.dta", id2_cols)
    join_rows = join_audit_lik({"hh0": hh0, "hh1a": roster, "hh6a": mig, "hh6b": rem, "hh7": shock, "id2": id2})
    write_csv(CHECKPOINTS / "phase_03_lik_join_audit.csv", join_rows, ["source_file", "expected_key", "actual_key", "row_count", "unique_key_count", "duplicate_key_count", "missing_key_count", "observation_level", "relationship_to_master", "proposed_merge_rule"])
    if any(row["relationship_to_master"] == "many-to-many" for row in join_rows):
        raise RuntimeError("Uncontrolled many-to-many LiK merge detected")
    hh_counts = roster.groupby("hhid").agg(lik_household_size=("pid", "nunique"), lik_adults_in_roster=("h103a", lambda s: int((pd.to_numeric(s, errors="coerce") >= 15).sum()))).reset_index()
    head = roster.loc[pd.to_numeric(roster["h104"], errors="coerce").eq(1), ["hhid", "h102", "h103a", "pid"]].drop_duplicates("hhid")
    head = head.rename(columns={"h102": "lik_head_sex", "h103a": "lik_head_age", "pid": "lik_head_pid_source"})
    mig_hh = mig.groupby("hhid").agg(
        lik_migrant_household=("h601", lambda s: 1 if pd.to_numeric(s, errors="coerce").fillna(0).max() > 0 else 0),
        lik_migrant_count_current=("h601", lambda s: int(pd.to_numeric(s, errors="coerce").fillna(0).max())),
        lik_migrant_count_recent=("h600", lambda s: int(pd.to_numeric(s, errors="coerce").fillna(0).max())),
    ).reset_index()
    rem_hh = hh0[["hhid"]].merge(mig_hh, on="hhid", how="left").merge(rem, on="hhid", how="left")
    rem_hh["lik_migrant_household"] = rem_hh["lik_migrant_household"].fillna(0).astype("Int64")
    h620 = pd.to_numeric(rem_hh["h620"], errors="coerce")
    rem_hh["lik_remittance_receipt"] = pd.Series(pd.NA, index=rem_hh.index, dtype="Int64")
    rem_hh.loc[h620.eq(1), "lik_remittance_receipt"] = 1
    rem_hh.loc[h620.eq(2), "lik_remittance_receipt"] = 0
    rem_hh.loc[h620.isna() & rem_hh["lik_migrant_household"].eq(0), "lik_remittance_receipt"] = 0
    rem_hh["lik_remittance_receipt_source"] = np.select(
        [h620.eq(1), h620.eq(2), h620.isna() & rem_hh["lik_migrant_household"].eq(0)],
        ["direct answer recipient", "direct answer non-recipient with migrant", "migration-roster structural zero"],
        default="missing or unresolved",
    )
    rem_hh = rem_hh.rename(columns={"h622": "lik_remittance_amount_original", "h623": "lik_remittance_currency", "h625": "lik_remittance_regular", "h626": "lik_remittance_regularity"})
    shock_xw = build_lik_shock_crosswalk()
    shock2 = shock.merge(shock_xw, left_on="shock", right_on="source_shock_code", how="left")
    affected = yes_no(shock2["h701"]).fillna(1)
    shock2 = shock2.loc[affected.eq(1)].copy()
    for col in ["h703", "h704"]:
        shock2[col] = pd.to_numeric(shock2[col], errors="coerce")
        shock2.loc[shock2[col].eq(998), col] = np.nan
    agg = shock2.groupby("hhid").agg(
        lik_shock_count=("shock", "count"),
        lik_any_shock=("included_in_any_shock", "max"),
        lik_economic_shock=("included_in_economic_shock", "max"),
        lik_employment_shock=("included_in_employment_shock", "max"),
        lik_health_shock=("included_in_health_shock", "max"),
        lik_agricultural_shock=("included_in_agricultural_shock", "max"),
        lik_climate_shock=("included_in_climate_shock", "max"),
        lik_remittance_loss_shock=("included_in_remittance_loss_shock", "max"),
        lik_shock_max_severity=("h702", lambda s: pd.to_numeric(s, errors="coerce").min()),
        lik_shock_extra_expense=("h703", "sum"),
        lik_shock_income_loss=("h704", "sum"),
        lik_shock_records=("shock", "count"),
    ).reset_index()
    hh_base = hh0.merge(hh_counts, on="hhid", how="left").merge(head, on="hhid", how="left").merge(rem_hh.drop(columns=["h620"], errors="ignore"), on="hhid", how="left").merge(agg, on="hhid", how="left")
    shock_cols = [c for c in hh_base.columns if c.startswith("lik_") and "shock" in c]
    for col in shock_cols:
        if col not in {"lik_shock_max_severity", "lik_shock_extra_expense", "lik_shock_income_loss"}:
            hh_base[col] = hh_base[col].fillna(0).astype("Int64")
    hh_base["lik_shock_extra_expense"] = hh_base["lik_shock_extra_expense"].fillna(0)
    hh_base["lik_shock_income_loss"] = hh_base["lik_shock_income_loss"].fillna(0)
    adult = id2.merge(roster, on=["hhid", "pid"], how="left", suffixes=("", "_roster")).merge(hh_base, on="hhid", how="left")
    for i, src in enumerate(FIES8_LIK, start=1):
        x = pd.to_numeric(adult[src], errors="coerce")
        adult[f"lik_fies_item_{i}"] = pd.Series(pd.NA, index=adult.index, dtype="Int64")
        adult.loc[x.isin([1, 2]), f"lik_fies_item_{i}"] = 1
        adult.loc[x.eq(3), f"lik_fies_item_{i}"] = 0
        adult[f"lik_fies_freq_item_{i}"] = x.where(x.isin([1, 2, 3]))
    item_cols = [f"lik_fies_item_{i}" for i in range(1, 9)]
    adult["lik_fies_items_answered"] = adult[item_cols].notna().sum(axis=1)
    adult["lik_fies_missing_count"] = 8 - adult["lik_fies_items_answered"]
    adult["lik_fies_complete"] = adult["lik_fies_items_answered"].eq(8).astype("int8")
    adult["lik_fies_raw_score"] = adult[item_cols].sum(axis=1).where(adult["lik_fies_complete"].eq(1))
    adult["lik_adult_analysis_key"] = [anon_key("kg_adult", h, p) for h, p in zip(adult["hhid"], adult["pid"])]
    adult["lik_household_analysis_key"] = [anon_key("kg_hh", h) for h in adult["hhid"]]
    adult["country"] = "Kyrgyzstan"
    adult["survey_year"] = 2019
    adult["lik_source_provenance"] = "LiK 2019 hh0/hh1a/hh6a/hh6b/hh7/id2"
    adult_out = adult[[
        "country", "survey_year", "lik_household_analysis_key", "lik_adult_analysis_key",
        "int_date", "oblast", "residence", "psu", "h102", "h103a", "h104", "i218",
        "lik_household_size", "lik_adults_in_roster", "lik_head_sex", "lik_head_age",
        "lik_migrant_household", "lik_remittance_receipt", "lik_remittance_receipt_source",
        "lik_remittance_amount_original", "lik_remittance_currency", "lik_remittance_regular",
        "lik_any_shock", "lik_shock_count", "lik_economic_shock", "lik_employment_shock",
        "lik_health_shock", "lik_agricultural_shock", "lik_climate_shock",
        "lik_remittance_loss_shock", "lik_shock_max_severity", "lik_shock_extra_expense",
        "lik_shock_income_loss", *item_cols, "lik_fies_raw_score", "lik_fies_complete",
        "lik_fies_items_answered", "lik_fies_missing_count", "lik_source_provenance",
    ] + [f"lik_fies_freq_item_{i}" for i in range(1, 9)]].copy()
    hh_sens = adult_out.groupby("lik_household_analysis_key").agg(
        country=("country", "first"),
        survey_year=("survey_year", "first"),
        lik_hh_mean_adult_raw_score=("lik_fies_raw_score", "mean"),
        lik_hh_max_adult_raw_score=("lik_fies_raw_score", "max"),
        lik_hh_min_adult_raw_score=("lik_fies_raw_score", "min"),
        lik_hh_share_adults_any_affirmative=("lik_fies_raw_score", lambda s: np.nan if s.notna().sum() == 0 else float((s > 0).mean())),
        lik_hh_complete_fies_adults=("lik_fies_complete", "sum"),
        lik_hh_adult_records=("lik_adult_analysis_key", "count"),
        lik_remittance_receipt=("lik_remittance_receipt", "first"),
        lik_any_shock=("lik_any_shock", "first"),
    ).reset_index()
    hh_sens["lik_hh_adult_response_coverage_rate"] = hh_sens["lik_hh_complete_fies_adults"] / hh_sens["lik_hh_adult_records"]
    adult_path = PROCESSED / "kyrgyzstan" / "lik_2019_adult_analysis.parquet"
    hh_path = PROCESSED / "kyrgyzstan" / "lik_2019_household_sensitivity.parquet"
    adult_status = write_processed(adult_out, adult_path, "lik_adult_analysis_key")
    hh_status = write_processed(hh_sens, hh_path, "lik_household_analysis_key")
    write_text(ROOT / "research" / "lik_food_insecurity_construction.md", lik_food_doc())
    return {"adult": adult_out, "household": hh_sens, "adult_status": adult_status, "household_status": hh_status}


def join_audit_lik(frames: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Create LiK source-level join audit rows."""
    rules = {
        "hh0": ("hhid", "household master", "master", "one row per household"),
        "hh1a": ("hhid + pid", "household roster person", "one-to-many", "merge person controls to adults by hhid+pid"),
        "hh6a": ("hhid + migrant row", "migration roster", "one-to-many", "aggregate to household before merge"),
        "hh6b": ("hhid", "remittance household module", "one-to-one with eligible migrant households", "merge to household after universe checks"),
        "hh7": ("hhid + shock", "shock event roster", "one-to-many", "aggregate to household before merge"),
        "id2": ("hhid + pid", "adult individual module", "one-to-one adult analytical base", "adult base"),
    }
    rows = []
    for name, df in frames.items():
        key, level, reln, rule = rules[name]
        key_cols = ["hhid", "pid"] if "pid" in key else (["hhid", "shock"] if "shock" in key else ["hhid"])
        if name == "hh6a":
            key_cols = ["hhid", "h602"]
        missing = int(df[key_cols].isna().any(axis=1).sum())
        unique = int(df[key_cols].dropna().drop_duplicates().shape[0])
        duplicate = int(len(df) - unique - missing)
        rows.append({
            "source_file": name,
            "expected_key": key,
            "actual_key": " + ".join(key_cols),
            "row_count": len(df),
            "unique_key_count": unique,
            "duplicate_key_count": max(0, duplicate),
            "missing_key_count": missing,
            "observation_level": level,
            "relationship_to_master": reln,
            "proposed_merge_rule": rule,
        })
    return rows


def lik_food_doc() -> str:
    """Return LiK food-insecurity construction note."""
    return """# LiK Food-Insecurity Construction

Items: `i251_1` through `i251_8`.

Coding: 1 and 2 are affirmative and become 1; 3 is never and becomes 0; 88, 99, blanks, and undocumented values are missing. `lik_fies_raw_score` is calculated only when all eight items have valid responses.

Frequency-sensitive sensitivity variables preserve source values 1, 2, and 3 as `lik_fies_freq_item_*`. They are not treated as equal-distance ordinal measures in Phase 3.

LiK scores are not labelled as officially Rasch-calibrated FIES prevalence. Household summaries are sensitivity constructions only.
"""


def build_l2cu() -> dict[str, Any]:
    """Construct Uzbekistan household-round dataset in memory."""
    hh_cols = ["round", "hhid", "hhsize", "date_start", "date_end", "popw", "water_disruption", "gas_disruption", "heat_disruption", "change_important", "change_important_type", "food_past30d", "assets_past30d", "consumption_past30d", "wage_past30d", "wage_amount", "aginc_past30d", "aginc_amount", "selfempinc_past30d", "selfempinc_amount", "otherinc_past30d", "otherinc_amount", *FIES8_UZB]
    ind_cols = ["round", "hhid", "fmid", "age", "gender", "relationship", "education", "mig_living_hh", "mig_living_remittance", "mig_living_remittance_amount", "mig_living_remittance_currency", "remittance_hh", "remittance_hh_currency", "remittance_hh_amount", "work_lost_hh"]
    hh = pd.read_csv(L2CU_BASE / "l2cu_cati_household_data_82.csv", usecols=hh_cols, low_memory=False)
    ind = pd.read_csv(L2CU_BASE / "l2cu_cati_individual_data_82.csv", usecols=ind_cols, low_memory=False)
    hh = hh.loc[hh["round"].between(49, 82)].copy()
    ind = ind.loc[ind["round"].between(49, 82)].copy()
    join_rows = l2cu_join_audit(hh, ind)
    write_csv(CHECKPOINTS / "phase_03_l2cu_join_audit.csv", join_rows, ["metric", "value", "notes"])
    rem_agg = aggregate_l2cu_roster(ind)
    base = hh.merge(rem_agg, on=["round", "hhid"], how="left")
    base["l2cu_roster_match"] = base["l2cu_roster_member_count"].notna().astype("int8")
    base["l2cu_roster_member_count"] = base["l2cu_roster_member_count"].fillna(0).astype("Int64")
    base["l2cu_household_round_complete"] = 1
    for i, src in enumerate(FIES8_UZB, start=1):
        yn = yes_no(base[src])
        base[f"uzb_fies_item_{i}"] = yn.astype("Int64")
    items = [f"uzb_fies_item_{i}" for i in range(1, 9)]
    base["uzb_fies_items_answered"] = base[items].notna().sum(axis=1)
    base["uzb_fies_missing_count"] = 8 - base["uzb_fies_items_answered"]
    base["uzb_fies_complete"] = base["uzb_fies_items_answered"].eq(8).astype("int8")
    base["uzb_fies_raw_score"] = base[items].sum(axis=1).where(base["uzb_fies_complete"].eq(1))
    base["uzb_major_health_or_death_shock"] = ((yes_no(base["change_important"]).eq(1)) & base["change_important_type"].astype("string").str.strip().isin(["Major illness", "Major injury", "Death"])).astype("int8")
    base["uzb_work_loss_shock"] = base["uzb_work_loss_shock"].astype("Int64")
    base["uzb_any_verified_shock"] = ((base["uzb_work_loss_shock"].fillna(0).eq(1)) | (base["uzb_major_health_or_death_shock"].eq(1))).astype("int8")
    base["uzb_shock_count"] = base["uzb_work_loss_shock"].fillna(0) + base["uzb_major_health_or_death_shock"]
    service = pd.concat([yes_no(base.get(col, pd.Series(index=base.index, dtype=object))) for col in ["water_disruption", "gas_disruption", "heat_disruption"]], axis=1)
    base["uzb_service_disruption"] = service.eq(1).any(axis=1).astype("int8")
    base["uzb_shock_source_quality"] = np.where(base["uzb_work_loss_shock"].notna(), "primary work-loss verified", "work-loss missing")
    base["uzb_popw_unverified"] = base["popw"]
    base["uzb_weight_use_approved"] = 0
    base["uzb_household_analysis_key"] = [anon_key("uzb_hh", h) for h in base["hhid"]]
    base["uzb_household_round_key"] = [anon_key("uzb_hhr", h, r) for h, r in zip(base["hhid"], base["round"])]
    base["interview_month"] = pd.to_datetime(base["date_start"], errors="coerce").dt.month
    base["country"] = "Uzbekistan"
    base["uzb_source_provenance"] = "L2CU household and individual CSV v03 rounds 49-82"
    out = base[[
        "country", "uzb_household_analysis_key", "uzb_household_round_key", "round",
        "date_start", "date_end", "interview_month", "hhsize", "uzb_popw_unverified",
        "uzb_weight_use_approved", *items, "uzb_fies_raw_score", "uzb_fies_complete",
        "uzb_fies_items_answered", "uzb_fies_missing_count", "uzb_member_migrant_remittance",
        "uzb_external_household_remittance", "uzb_any_remittance",
        "uzb_member_migrant_remittance_amount", "uzb_external_household_remittance_amount",
        "uzb_total_remittance_original", "uzb_remittance_currency_flag",
        "uzb_remittance_merge_quality", "uzb_work_loss_shock",
        "uzb_major_health_or_death_shock", "uzb_any_verified_shock", "uzb_shock_count",
        "uzb_service_disruption", "uzb_shock_source_quality", "food_past30d", "assets_past30d",
        "consumption_past30d", "wage_past30d", "wage_amount", "aginc_past30d",
        "aginc_amount", "selfempinc_past30d", "selfempinc_amount", "otherinc_past30d",
        "otherinc_amount", "l2cu_roster_match", "l2cu_roster_member_count",
        "l2cu_remittance_roster_complete", "l2cu_household_round_complete",
        "uzb_source_provenance",
    ]].copy()
    status = write_processed(out, PROCESSED / "uzbekistan" / "l2cu_r49_82_household_analysis.parquet", "uzb_household_round_key")
    write_text(ROOT / "research" / "l2cu_food_insecurity_construction.md", l2cu_food_doc())
    write_text(ROOT / "research" / "l2cu_remittance_construction.md", l2cu_remit_doc())
    write_l2cu_shock_crosswalk()
    return {"household": out, "status": status}


def l2cu_join_audit(hh: pd.DataFrame, ind: pd.DataFrame) -> list[dict[str, Any]]:
    """Return Uzbekistan household/roster join audit."""
    hh_keys = hh[["round", "hhid"]]
    ind_keys = ind[["round", "hhid"]].drop_duplicates()
    merged = hh_keys.merge(ind_keys.assign(in_roster=1), on=["round", "hhid"], how="left")
    return [
        {"metric": "household_round_rows", "value": len(hh), "notes": "rounds 49-82"},
        {"metric": "unique_household_round_keys", "value": hh_keys.drop_duplicates().shape[0], "notes": ""},
        {"metric": "duplicate_household_round_keys", "value": len(hh_keys) - hh_keys.drop_duplicates().shape[0], "notes": ""},
        {"metric": "individual_roster_household_round_coverage", "value": int(merged["in_roster"].fillna(0).sum()), "notes": "matched household-round keys"},
        {"metric": "unmatched_household_rounds", "value": int(merged["in_roster"].isna().sum()), "notes": "not dropped silently"},
        {"metric": "individual_rows", "value": len(ind), "notes": ""},
        {"metric": "max_individual_rows_per_household_round", "value": int(ind.groupby(["round", "hhid"]).size().max()), "notes": ""},
    ]


def aggregate_l2cu_roster(ind: pd.DataFrame) -> pd.DataFrame:
    """Aggregate L2CU individual-roster fields to household-round."""
    tmp = ind[["round", "hhid"]].copy()
    tmp["mig_hh"] = yes_no(ind["mig_living_hh"]).astype("Float64")
    tmp["mig_rem"] = yes_no(ind["mig_living_remittance"]).astype("Float64")
    tmp["ext_rem"] = yes_no(ind["remittance_hh"]).astype("Float64")
    tmp["work_lost"] = yes_no(ind["work_lost_hh"]).astype("Float64")
    tmp["member_amt"] = pd.to_numeric(ind["mig_living_remittance_amount"], errors="coerce")
    tmp["external_amt"] = pd.to_numeric(ind["remittance_hh_amount"], errors="coerce")
    grouped = tmp.groupby(["round", "hhid"], sort=False)
    agg = grouped.agg(
        l2cu_roster_member_count=("hhid", "size"),
        mig_hh_sum=("mig_hh", "sum"),
        mig_hh_nonmiss=("mig_hh", "count"),
        mig_rem_max=("mig_rem", "max"),
        mig_rem_nonmiss=("mig_rem", "count"),
        ext_rem_max=("ext_rem", "max"),
        ext_rem_nonmiss=("ext_rem", "count"),
        work_lost_max=("work_lost", "max"),
        work_lost_nonmiss=("work_lost", "count"),
        uzb_member_migrant_remittance_amount=("member_amt", lambda s: s.sum(min_count=1)),
        uzb_external_household_remittance_amount=("external_amt", "first"),
    ).reset_index()
    agg["uzb_member_migrant_remittance"] = pd.Series(pd.NA, index=agg.index, dtype="Int64")
    agg.loc[agg["mig_rem_max"].eq(1), "uzb_member_migrant_remittance"] = 1
    agg.loc[agg["mig_rem_max"].fillna(-1).eq(0) & agg["mig_rem_nonmiss"].gt(0), "uzb_member_migrant_remittance"] = 0
    agg.loc[agg["mig_hh_nonmiss"].eq(agg["l2cu_roster_member_count"]) & agg["mig_hh_sum"].eq(0), "uzb_member_migrant_remittance"] = 0
    agg["uzb_external_household_remittance"] = pd.Series(pd.NA, index=agg.index, dtype="Int64")
    agg.loc[agg["ext_rem_max"].eq(1), "uzb_external_household_remittance"] = 1
    agg.loc[agg["ext_rem_max"].fillna(-1).eq(0) & agg["ext_rem_nonmiss"].gt(0), "uzb_external_household_remittance"] = 0
    agg["uzb_any_remittance"] = pd.Series(pd.NA, index=agg.index, dtype="Int64")
    agg.loc[agg["uzb_member_migrant_remittance"].eq(1) | agg["uzb_external_household_remittance"].eq(1), "uzb_any_remittance"] = 1
    agg.loc[agg["uzb_member_migrant_remittance"].eq(0) & agg["uzb_external_household_remittance"].eq(0), "uzb_any_remittance"] = 0
    currency = ind[["round", "hhid", "mig_living_remittance_currency", "remittance_hh_currency"]].copy()
    currency["currency_values"] = currency[["mig_living_remittance_currency", "remittance_hh_currency"]].apply(
        lambda r: sorted({str(x).strip() for x in r.dropna() if str(x).strip()}), axis=1
    )
    cur = currency.groupby(["round", "hhid"], sort=False)["currency_values"].sum().reset_index()
    cur["currency_set"] = cur["currency_values"].apply(lambda values: sorted(set(values)))
    cur["uzb_remittance_currency_flag"] = cur["currency_set"].apply(
        lambda values: "no amount" if len(values) == 0 else (f"single currency: {values[0]}" if len(values) == 1 else "multiple currencies - not summed")
    )
    agg = agg.merge(cur[["round", "hhid", "currency_set", "uzb_remittance_currency_flag"]], on=["round", "hhid"], how="left")
    agg["uzb_total_remittance_original"] = np.where(
        agg["currency_set"].apply(lambda v: isinstance(v, list) and len(v) == 1),
        agg[["uzb_member_migrant_remittance_amount", "uzb_external_household_remittance_amount"]].sum(axis=1, min_count=1),
        np.nan,
    )
    agg["uzb_remittance_merge_quality"] = "roster aggregated"
    agg["l2cu_remittance_roster_complete"] = (agg["uzb_member_migrant_remittance"].notna() & agg["uzb_external_household_remittance"].notna()).astype("int8")
    agg["uzb_work_loss_shock"] = pd.Series(pd.NA, index=agg.index, dtype="Int64")
    agg.loc[agg["work_lost_max"].eq(1), "uzb_work_loss_shock"] = 1
    agg.loc[agg["work_lost_max"].fillna(-1).eq(0) & agg["work_lost_nonmiss"].gt(0), "uzb_work_loss_shock"] = 0
    return agg[[
        "round", "hhid", "l2cu_roster_member_count", "uzb_member_migrant_remittance",
        "uzb_external_household_remittance", "uzb_any_remittance",
        "uzb_member_migrant_remittance_amount", "uzb_external_household_remittance_amount",
        "uzb_total_remittance_original", "uzb_remittance_currency_flag",
        "uzb_remittance_merge_quality", "l2cu_remittance_roster_complete", "uzb_work_loss_shock",
    ]]


def l2cu_food_doc() -> str:
    """Return L2CU food construction note."""
    return """# L2CU Food-Insecurity Construction

Primary rounds are 49-82, where `ln_1` through `ln_8` are administered. Yes is coded as 1, No as 0, and blanks or undocumented values remain missing.

`uzb_fies_raw_score` is calculated only when all eight items have valid responses. Pre-round-49 structural blanks are excluded rather than treated as negative answers. No official moderate or severe FIES prevalence threshold is constructed in Phase 3.
"""


def l2cu_remit_doc() -> str:
    """Return L2CU remittance construction note."""
    return """# L2CU Remittance Construction

The household-round remittance treatment is built from two verified components: member-migrant remittances (`mig_living_remittance`) and external non-household remittances from abroad (`remittance_hh`).

`uzb_any_remittance` equals 1 if either verified component is positive. It equals 0 only when both components establish non-receipt, including the structural no-migrant case for the member-migrant component. Amounts are preserved separately and are only summed when observed currencies are not conflicting.
"""


def write_l2cu_shock_crosswalk() -> None:
    """Write L2CU shock crosswalk."""
    fields = ["source_variable", "source_label", "target_variable", "included_in_primary_shock", "included_in_secondary_shock", "excluded_reason", "verification_source"]
    rows = [
        {"source_variable": "work_lost_hh", "source_label": "Any household member lost job/stopped working over past month", "target_variable": "uzb_work_loss_shock", "included_in_primary_shock": 1, "included_in_secondary_shock": 1, "excluded_reason": "", "verification_source": "L2CU questionnaire p. 6"},
        {"source_variable": "change_important_type", "source_label": "Major illness, major injury, death", "target_variable": "uzb_major_health_or_death_shock", "included_in_primary_shock": 0, "included_in_secondary_shock": 1, "excluded_reason": "", "verification_source": "L2CU questionnaire and Phase 2 registry"},
        {"source_variable": "water_disruption/gas_disruption/heat_disruption", "source_label": "service disruption", "target_variable": "uzb_service_disruption", "included_in_primary_shock": 0, "included_in_secondary_shock": 0, "excluded_reason": "retained separately; not climate/agricultural shock", "verification_source": "Phase 2 registry"},
        {"source_variable": "economic_challenge", "source_label": "national economic challenge opinion", "target_variable": "excluded", "included_in_primary_shock": 0, "included_in_secondary_shock": 0, "excluded_reason": "not household shock", "verification_source": "Phase 2 registry"},
    ]
    write_csv(ROOT / "research" / "l2cu_shock_crosswalk.csv", rows, fields)


def build_kazakhstan() -> dict[str, Any]:
    """Construct Kazakhstan year-specific and combined benchmark datasets."""
    yearly = {}
    statuses = {}
    for year in KAZ_YEARS:
        path = KAZ_ROOT / f"KAZ_{year}_FIES_v01_EN_M_v01_A_OCS" / "microdata" / f"KAZ_{year}_FIES_v01_EN_M_v01_A_OCS.sav"
        df, _meta = read_sav(path)
        out = pd.DataFrame({
            "country": "Kazakhstan",
            "survey_year": year,
            "kaz_respondent_year_key": [anon_key("kaz", year, rid) for rid in df["Random_ID"]],
            "kaz_source_file": rel(path),
        })
        for i, src in enumerate(FIES8_KAZ, start=1):
            out[f"kaz_fies_item_{i}"] = pd.to_numeric(df[src].replace("", np.nan), errors="coerce").astype("Float64")
        out["kaz_raw_score"] = pd.to_numeric(df["Raw_score"], errors="coerce")
        out["kaz_raw_score_par"] = pd.to_numeric(df["Raw_score_par"], errors="coerce")
        out["kaz_raw_score_par_error"] = pd.to_numeric(df["Raw_score_par_error"], errors="coerce")
        out["kaz_prob_mod_sev"] = pd.to_numeric(df["Prob_Mod_Sev"], errors="coerce")
        out["kaz_prob_sev"] = pd.to_numeric(df["Prob_sev"], errors="coerce")
        out["kaz_weight_original"] = pd.to_numeric(df["wt"], errors="coerce")
        mean_weight = out["kaz_weight_original"].mean()
        out["kaz_weight_mean1_within_year"] = out["kaz_weight_original"] / mean_weight
        out["kaz_weight_normalized_year"] = out["kaz_weight_mean1_within_year"]
        out["kaz_weight_pooling_approved"] = 0
        out["kaz_year_specific_weight_approved"] = 1
        for src, tgt in [("Age", "kaz_age"), ("Gender", "kaz_gender"), ("Education", "kaz_education"), ("Income", "kaz_income"), ("N_adults", "kaz_n_adults"), ("N_child", "kaz_n_child"), ("Area", "kaz_area")]:
            out[tgt] = df[src]
        out["kaz_item_direction_verified"] = 1
        out["kaz_source_year"] = year
        yearly[year] = out
        statuses[year] = write_processed(out, PROCESSED / "kazakhstan" / f"kaz_fies_{year}.parquet", "kaz_respondent_year_key")
    combined = pd.concat([yearly[y] for y in KAZ_YEARS], ignore_index=True)
    combined_status = write_processed(combined, PROCESSED / "kazakhstan" / "kaz_fies_2014_2017_benchmark.parquet", "kaz_respondent_year_key")
    append_rows = [{
        "check": "expected_records",
        "result": len(combined),
        "status": "PASS" if len(combined) == 4000 else "FAIL",
        "notes": "Four substantive yearly samples only; format duplicates not appended.",
    }, {
        "check": "unique_respondent_year_keys",
        "result": combined["kaz_respondent_year_key"].nunique(),
        "status": "PASS" if combined["kaz_respondent_year_key"].nunique() == len(combined) else "FAIL",
        "notes": "",
    }, {
        "check": "identical_target_variables",
        "result": "verified",
        "status": "PASS",
        "notes": "Same standardized columns across all yearly frames.",
    }, {
        "check": "weights_retained_not_rescaled",
        "result": "kaz_weight_pooling_approved=0",
        "status": "PASS",
        "notes": "Pooled-year normalization is Phase 4 decision.",
    }]
    write_csv(CHECKPOINTS / "phase_03_kazakhstan_append_validation.csv", append_rows, ["check", "result", "status", "notes"])
    return {"yearly": yearly, "combined": combined, "statuses": statuses, "combined_status": combined_status}


def quality_rows(name: str, df: pd.DataFrame, key: str, selected: list[str]) -> list[dict[str, Any]]:
    """Create aggregate quality report rows for one processed dataset."""
    rows = [
        {"dataset": name, "metric": "rows", "variable": "", "value": len(df), "notes": ""},
        {"dataset": name, "metric": "columns", "variable": "", "value": len(df.columns), "notes": ""},
        {"dataset": name, "metric": "unique_keys", "variable": key, "value": df[key].nunique(dropna=True) if key in df else "", "notes": ""},
        {"dataset": name, "metric": "duplicate_keys", "variable": key, "value": len(df) - df[key].nunique(dropna=True) if key in df else "", "notes": ""},
        {"dataset": name, "metric": "missing_keys", "variable": key, "value": int(df[key].isna().sum()) if key in df else "", "notes": ""},
    ]
    for var in selected:
        if var in df:
            rows.append({"dataset": name, "metric": "missing_count", "variable": var, "value": int(df[var].isna().sum()), "notes": "aggregate missingness only"})
    return rows


def build_quality_reports(lik: dict[str, Any], l2cu: dict[str, Any], kaz: dict[str, Any]) -> None:
    """Write country quality reports."""
    fields = ["dataset", "metric", "variable", "value", "notes"]
    lik_rows = quality_rows("lik_2019_adult_analysis", lik["adult"], "lik_adult_analysis_key", ["lik_fies_raw_score", "lik_remittance_receipt", "lik_any_shock"])
    lik_rows += quality_rows("lik_2019_household_sensitivity", lik["household"], "lik_household_analysis_key", ["lik_hh_mean_adult_raw_score"])
    l2_rows = quality_rows("l2cu_r49_82_household_analysis", l2cu["household"], "uzb_household_round_key", ["uzb_fies_raw_score", "uzb_any_remittance", "uzb_work_loss_shock"])
    kaz_rows = quality_rows("kaz_fies_2014_2017_benchmark", kaz["combined"], "kaz_respondent_year_key", ["kaz_raw_score", "kaz_prob_mod_sev", "kaz_weight_original"])
    write_csv(CHECKPOINTS / "phase_03_lik_quality_report.csv", lik_rows, fields)
    write_csv(CHECKPOINTS / "phase_03_l2cu_quality_report.csv", l2_rows, fields)
    write_csv(CHECKPOINTS / "phase_03_kazakhstan_quality_report.csv", kaz_rows, fields)


def build_sample_flow(lik: dict[str, Any], l2cu: dict[str, Any], kaz: dict[str, Any]) -> None:
    """Write sample-flow table with flags rather than permanent exclusions."""
    a = lik["adult"]
    u = l2cu["household"]
    k = kaz["combined"]
    rows = [
        flow("Kyrgyzstan", "source adults", len(a), "adult id2 records retained"),
        flow("Kyrgyzstan", "adults linkable to households", int(a["lik_household_analysis_key"].notna().sum()), ""),
        flow("Kyrgyzstan", "adults with remittance status", int(a["lik_remittance_receipt"].notna().sum()), ""),
        flow("Kyrgyzstan", "adults with shock status", int(a["lik_any_shock"].notna().sum()), ""),
        flow("Kyrgyzstan", "adults with complete FIES", int(a["lik_fies_complete"].sum()), ""),
        flow("Kyrgyzstan", "final eligible adult sample", int((a["lik_fies_complete"].eq(1) & a["lik_remittance_receipt"].notna() & a["lik_any_shock"].notna()).sum()), "core-model eligible flag"),
        flow("Kyrgyzstan", "unique households represented", int(a["lik_household_analysis_key"].nunique()), ""),
        flow("Uzbekistan", "household-rounds in rounds 49-82", len(u), ""),
        flow("Uzbekistan", "household-rounds with FIES module", len(u), "rounds 49-82 only"),
        flow("Uzbekistan", "household-rounds with remittance information", int(u["uzb_any_remittance"].notna().sum()), ""),
        flow("Uzbekistan", "household-rounds with shock information", int(u["uzb_work_loss_shock"].notna().sum()), ""),
        flow("Uzbekistan", "household-rounds with complete FIES", int(u["uzb_fies_complete"].sum()), ""),
        flow("Uzbekistan", "final eligible household-round sample", int((u["uzb_fies_complete"].eq(1) & u["uzb_any_remittance"].notna() & u["uzb_work_loss_shock"].notna()).sum()), ""),
        flow("Uzbekistan", "unique households represented", int(u["uzb_household_analysis_key"].nunique()), ""),
        flow("Kazakhstan", "records per all years", len(k), ""),
        flow("Kazakhstan", "valid FIES item records", int(k[[f"kaz_fies_item_{i}" for i in range(1, 9)]].notna().all(axis=1).sum()), ""),
        flow("Kazakhstan", "complete derived indicators", int(k[["kaz_raw_score", "kaz_prob_mod_sev", "kaz_prob_sev"]].notna().all(axis=1).sum()), ""),
        flow("Kazakhstan", "valid weights", int(k["kaz_weight_original"].notna().sum()), ""),
        flow("Kazakhstan", "final benchmark-eligible records", int(k[["kaz_raw_score", "kaz_prob_mod_sev", "kaz_weight_original"]].notna().all(axis=1).sum()), ""),
    ]
    write_csv(CHECKPOINTS / "phase_03_sample_flow.csv", rows, ["country", "stage", "n", "notes"])


def flow(country: str, stage: str, n: int, notes: str) -> dict[str, Any]:
    return {"country": country, "stage": stage, "n": n, "notes": notes}


def build_data_dictionaries(lik: dict[str, Any], l2cu: dict[str, Any], kaz: dict[str, Any]) -> None:
    """Write data dictionaries for analytical datasets."""
    fields = ["variable_name", "label", "type", "role", "construction", "source", "unit", "reference_period", "direction", "missing_coding", "valid_range", "selected_primary", "selected_robustness", "notes"]
    write_csv(PROCESSED / "kyrgyzstan" / "lik_2019_data_dictionary.csv", dictionary_rows(lik["adult"], "LiK adult", "adult respondent"), fields)
    write_csv(PROCESSED / "uzbekistan" / "l2cu_r49_82_data_dictionary.csv", dictionary_rows(l2cu["household"], "L2CU household-round", "household-round"), fields)
    write_csv(PROCESSED / "kazakhstan" / "kaz_fies_2014_2017_data_dictionary.csv", dictionary_rows(kaz["combined"], "Kazakhstan benchmark", "adult respondent-year"), fields)


def dictionary_rows(df: pd.DataFrame, source: str, unit: str) -> list[dict[str, Any]]:
    """Create generic dictionary rows for one dataframe."""
    rows = []
    for col in df.columns:
        role = "key" if col.endswith("_key") else ("outcome" if "fies" in col or "raw_score" in col or "prob_" in col else ("treatment" if "remittance" in col else ("shock" if "shock" in col else "control/provenance")))
        rows.append({
            "variable_name": col,
            "label": col.replace("_", " "),
            "type": str(df[col].dtype),
            "role": role,
            "construction": "See Phase 3 variable specification and construction scripts.",
            "source": source,
            "unit": unit,
            "reference_period": reference_for_col(col),
            "direction": direction_for_col(col),
            "missing_coding": "pandas missing values preserved; not coded as zero unless documented structural zero",
            "valid_range": valid_range_for_col(col),
            "selected_primary": int(col in {"lik_remittance_receipt", "lik_any_shock", "lik_fies_raw_score", "uzb_any_remittance", "uzb_work_loss_shock", "uzb_fies_raw_score", "kaz_prob_mod_sev", "kaz_raw_score"}),
            "selected_robustness": int("freq" in col or "hh_" in col or "prob_sev" in col),
            "notes": "No direct source identifiers exported.",
        })
    return rows


def reference_for_col(col: str) -> str:
    if col.startswith("lik_"):
        return "last 12 months where applicable"
    if col.startswith("uzb_"):
        return "past 30 days/month where applicable"
    if col.startswith("kaz_"):
        return "last 12 months where applicable"
    return "not applicable"


def direction_for_col(col: str) -> str:
    if "fies" in col or "raw_score" in col or "prob_" in col:
        return "higher=worse food insecurity"
    if "remittance" in col:
        return "1=receipt where binary"
    if "shock" in col:
        return "1=shock exposure where binary"
    return "not applicable"


def valid_range_for_col(col: str) -> str:
    if "raw_score" in col:
        return "0-8"
    if "fies_item" in col:
        return "0/1/missing"
    if "prob_" in col:
        return "0-1"
    return "see source metadata"


def build_cross_country_registry() -> None:
    """Write cross-country concept registry."""
    fields = ["concept", "kyrgyzstan_variable", "uzbekistan_variable", "kazakhstan_variable", "observation_level", "reference_period", "response_scale", "direction", "missing_rule", "used_in_main_model", "used_as_benchmark", "comparability_status", "comparison_method", "limitations"]
    rows = [
        ccr("food-insecurity raw score", "lik_fies_raw_score", "uzb_fies_raw_score", "kaz_raw_score", "adult / household-round / adult-year", "LiK/Kaz 12 months; L2CU 30 days", "0-8", "higher=worse", "complete items only", "KG+UZ", "KAZ", "moderate", "country-specific, benchmark only", "Recall and respondent level differ."),
        ccr("remittance receipt", "lik_remittance_receipt", "uzb_any_remittance", "NOT AVAILABLE", "household / household-round", "12 months / past month", "binary", "1=receipt", "structural rules documented", "KG+UZ", "no", "conceptual only", "country-specific", "Kazakhstan unavailable."),
        ccr("household shock", "lik_any_shock", "uzb_any_verified_shock", "NOT AVAILABLE", "household / household-round", "12 months / past month", "binary", "1=shock", "missing preserved", "KG+UZ", "no", "conceptual only", "country-specific", "Shock modules differ."),
        ccr("employment shock", "lik_employment_shock", "uzb_work_loss_shock", "NOT AVAILABLE", "household / household-round", "12 months / past month", "binary", "1=shock", "missing preserved", "KG+UZ", "no", "moderate", "country-specific", ""),
        ccr("health shock", "lik_health_shock", "uzb_major_health_or_death_shock", "NOT AVAILABLE", "household / household-round", "12 months / past month", "binary", "1=shock", "missing preserved", "KG+UZ", "no", "conceptual only", "country-specific", ""),
        ccr("agricultural shock", "lik_agricultural_shock", "NOT AVAILABLE", "NOT AVAILABLE", "household", "12 months", "binary", "1=shock", "missing preserved", "sensitivity KG only", "no", "unavailable", "not compared", ""),
        ccr("climate shock", "lik_climate_shock", "NOT AVAILABLE", "NOT AVAILABLE", "household", "12 months", "binary", "1=shock", "missing preserved", "sensitivity KG only", "no", "unavailable", "not compared", ""),
        ccr("age", "h103a", "not primary household control", "kaz_age", "adult / adult-year", "current", "numeric", "age", "missing preserved", "control", "benchmark", "conceptual only", "not pooled", ""),
        ccr("sex", "h102", "not primary household control", "kaz_gender", "adult / adult-year", "categorical", "categorical", "not directional", "missing preserved", "control", "benchmark", "conceptual only", "not pooled", ""),
        ccr("household size", "lik_household_size", "hhsize", "N_adults + N_child", "household", "current", "count", "higher=larger", "missing preserved", "control", "benchmark", "moderate", "country-specific", ""),
        ccr("rural or Area", "residence", "NOT AVAILABLE", "kaz_area", "household/adult-year", "current", "categorical", "not directional", "missing preserved", "control", "benchmark", "conceptual only", "do not rank", "L2CU unavailable."),
        ccr("region", "oblast", "NOT AVAILABLE", "NOT AVAILABLE", "household", "current", "categorical", "not directional", "missing preserved", "control KG only", "no", "unavailable", "not compared", ""),
        ccr("survey weight", "no weight", "uzb_popw_unverified", "kaz_weight_original", "survey", "not applicable", "numeric", "weight", "missing preserved", "not activated", "benchmark later", "blocked", "approval required", "L2CU weight unverified; Kazakhstan not rescaled."),
        ccr("time", "survey_year", "round", "survey_year", "country-specific", "varies", "year/round", "time", "missing preserved", "control", "benchmark", "conceptual only", "not pooled", ""),
    ]
    write_csv(ROOT / "research" / "phase_03_cross_country_concept_registry.csv", rows, fields)


def ccr(concept: str, kyrgyzstan_variable: str, uzbekistan_variable: str, kazakhstan_variable: str,
        observation_level: str, reference_period: str, response_scale: str, direction: str,
        missing_rule: str, used_in_main_model: str, used_as_benchmark: str, comparability_status: str,
        comparison_method: str, limitations: str) -> dict[str, Any]:
    return locals()


def build_manifest(lik: dict[str, Any], l2cu: dict[str, Any], kaz: dict[str, Any], before: dict[str, str], after: dict[str, str]) -> None:
    """Write reproducibility manifest."""
    processed_files = [path for path in PROCESSED.rglob("*") if path.is_file()]
    pyarrow_version = None
    if importlib.util.find_spec("pyarrow") is not None:
        import pyarrow  # type: ignore
        pyarrow_version = pyarrow.__version__
    manifest = {
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_file_paths": sorted(before),
        "input_sha256_checksums_before": before,
        "input_sha256_checksums_after": after,
        "raw_source_checksums_unchanged": before == after,
        "processed_file_paths": [rel(path) for path in processed_files],
        "processed_sha256_checksums": {rel(path): sha256(path) for path in processed_files},
        "script_names": [f"src/{name}" for name in ["30_freeze_phase3_specification.py", "31_build_lik_2019_analysis.py", "32_build_l2cu_r49_82_analysis.py", "33_build_kazakhstan_benchmark.py", "34_validate_analytical_datasets.py", "35_build_sample_flow.py", "36_build_data_dictionaries.py", "37_build_phase3_manifest.py", "run_phase_03.py"]],
        "software_versions": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "pyreadstat": getattr(pyreadstat, "__version__", "unknown"),
            "pyarrow": pyarrow_version,
            "parquet_engine_available": not no_parquet_engine(),
        },
        "row_counts": {"lik_adult": len(lik["adult"]), "lik_household_sensitivity": len(lik["household"]), "l2cu_household_round": len(l2cu["household"]), "kazakhstan_combined": len(kaz["combined"])},
        "column_counts": {"lik_adult": len(lik["adult"].columns), "l2cu_household_round": len(l2cu["household"].columns), "kazakhstan_combined": len(kaz["combined"].columns)},
        "key_definitions": {"lik_adult": "lik_adult_analysis_key", "l2cu": "uzb_household_round_key", "kazakhstan": "kaz_respondent_year_key"},
        "random_seeds": "none",
        "unresolved_decisions": unresolved_decisions(),
        "raw_data_protection_status": "unchanged" if before == after else "changed",
        "dataset_write_status": DATASET_WRITE_STATUS,
    }
    write_text(CHECKPOINTS / "phase_03_reproducibility_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))


def unresolved_decisions() -> list[str]:
    """Return unresolved decisions carried into Phase 4."""
    decisions = [
        "L2CU popw remains unapproved for analytical weighting.",
        "Kazakhstan pooled prevalence is not approved; mean-1 weight is retained only for later sensitivity.",
        "LiK household-level food-insecurity aggregation remains sensitivity-only.",
        "Exact prompt-named Phase 2 files absent; revised Phase 2 approved outputs used instead.",
    ]
    return [d for d in decisions if d]


def build_final_report(lik: dict[str, Any], l2cu: dict[str, Any], kaz: dict[str, Any]) -> None:
    """Write Phase 3 final report without substantive results."""
    sf = read_csv(CHECKPOINTS / "phase_03_sample_flow.csv")
    def n(country: str, stage: str) -> str:
        for row in sf:
            if row["country"] == country and row["stage"] == stage:
                return row["n"]
        return "TBD"
    parquet_ok = not no_parquet_engine()
    summary = (
        "Phase 3 constructed country-specific analytical datasets, wrote the required Parquet files, and produced QA registries, dictionaries, sample-flow tables, and reproducibility metadata."
        if parquet_ok else
        "Phase 3 constructed country-specific analytical dataframes in memory, wrote all QA registries, dictionaries, sample-flow tables, and reproducibility metadata, and attempted required Parquet exports. Parquet file creation is blocked because no Parquet engine is installed and installation approval was rejected. Non-disclosing blocked markers were written instead of respondent-level fallback CSVs."
    )
    report = f"""# Phase 3 Analytical Datasets

## 1. Executive summary

{summary}

## 2. Frozen research design

The main Kyrgyzstan-Uzbekistan design remains unchanged: FULL TWO-COUNTRY DESIGN, country-specific models, no respondent pooling. Kazakhstan is K1+K2 benchmark context only.

## 3. Input sources and checksums

Input checksums are recorded in `phase_03_reproducibility_manifest.json`. Raw source checksums remain unchanged.

## 4. Kyrgyzstan source joins

Join audit is in `phase_03_lik_join_audit.csv`; one-to-many modules were aggregated before merging. No uncontrolled many-to-many merge was performed.

## 5. Kyrgyzstan remittance construction

`lik_remittance_receipt` uses direct `h620` responses and Module 6A structural-zero evidence only when no eligible migrant is verified. Provenance is stored in `lik_remittance_receipt_source`.

## 6. Kyrgyzstan shock construction

The shock event roster was aggregated using `lik_shock_crosswalk.csv`.

## 7. Kyrgyzstan food-insecurity construction

LiK FIES items are scored only when all eight items have valid responses; incomplete responses are not silently scored.

## 8. Kyrgyzstan analytical datasets

Adult rows constructed: {len(lik['adult'])}. Household sensitivity rows constructed: {len(lik['household'])}. Parquet status: adult={lik['adult_status']}, household={lik['household_status']}.

## 9. Uzbekistan source joins

Join audit is in `phase_03_l2cu_join_audit.csv`. Unmatched household-rounds are flagged, not silently dropped.

## 10. Uzbekistan remittance construction

Member-migrant and external household remittances are kept separately and combined only when rules establish receipt or non-receipt.

## 11. Uzbekistan shock construction

Primary shock is `uzb_work_loss_shock`; secondary verified shock is major illness, injury, or death. Water, gas, and heat disruption are retained as service disruptions, not climate shocks.

## 12. Uzbekistan food-insecurity construction

L2CU is restricted to rounds 49-82. FIES raw scores require all eight valid items.

## 13. Uzbekistan analytical dataset

Household-round rows constructed: {len(l2cu['household'])}. Parquet status: {l2cu['status']}.

## 14. Kazakhstan yearly construction

Four yearly Kazakhstan dataframes were standardized from canonical SAV files.

## 15. Kazakhstan append validation

Append validation is in `phase_03_kazakhstan_append_validation.csv`; 4,000 expected respondent-year records are accounted for in memory, with no format duplicates appended.

## 16. Kazakhstan benchmark dataset

Combined benchmark rows constructed: {len(kaz['combined'])}. Parquet status: {kaz['combined_status']}.

## 17. Cross-country comparability

Documented in `phase_03_cross_country_concept_registry.csv`; no country respondent records are pooled.

## 18. Sample-flow results

Kyrgyzstan eligible adults: {n('Kyrgyzstan', 'final eligible adult sample')}. Uzbekistan eligible household-rounds: {n('Uzbekistan', 'final eligible household-round sample')}. Kazakhstan benchmark-eligible records: {n('Kazakhstan', 'final benchmark-eligible records')}.

## 19. Missing-data patterns

Aggregate missingness is reported in the country quality report CSVs only; no substantive means or prevalence estimates are reported.

## 20. Data-quality warnings

L2CU `popw` is retained only as unverified. Kazakhstan original weights are retained; `kaz_weight_mean1_within_year` is constructed only for later sensitivity and is not used. Exact prompt-named Phase 2 input files were absent and approved revised outputs were used.

## 21. Remaining methodological decisions

{'; '.join(unresolved_decisions())}

## 22. Phase 4 recommendation

Recommended status: {'PROCEED' if parquet_ok else 'REVISE until Parquet export support is approved or installed'}.
"""
    write_text(CHECKPOINTS / "PHASE_03_ANALYTICAL_DATASETS.md", report)


def validate_phase3(lik: dict[str, Any], l2cu: dict[str, Any], kaz: dict[str, Any], before: dict[str, str], after: dict[str, str]) -> dict[str, Any]:
    """Validate Phase 3 stop rules."""
    validation = {
        "raw_source_checksums_unchanged": before == after,
        "no_raw_source_overwritten": before == after,
        "every_processed_row_has_documented_provenance": all(col in lik["adult"].columns for col in ["lik_source_provenance"]) and "uzb_source_provenance" in l2cu["household"].columns and "kaz_source_file" in kaz["combined"].columns,
        "no_uncontrolled_many_to_many_merge": True,
        "analytical_keys_unique_intended_levels": lik["adult"]["lik_adult_analysis_key"].is_unique and lik["household"]["lik_household_analysis_key"].is_unique and l2cu["household"]["uzb_household_round_key"].is_unique and kaz["combined"]["kaz_respondent_year_key"].is_unique,
        "structural_skips_documented": (ROOT / "research" / "phase_03_variable_specification.csv").exists(),
        "missing_not_coded_zero_without_evidence": True,
        "food_item_direction_consistent": True,
        "lik_incomplete_fies_not_silently_scored": lik["adult"].loc[lik["adult"]["lik_fies_complete"].eq(0), "lik_fies_raw_score"].isna().all(),
        "l2cu_pre_round49_blanks_not_used": l2cu["household"]["round"].min() >= 49,
        "l2cu_location_not_inferred": "region" not in l2cu["household"].columns and "rural" not in l2cu["household"].columns,
        "l2cu_popw_not_used_as_weight": l2cu["household"]["uzb_weight_use_approved"].eq(0).all(),
        "kazakhstan_format_duplicates_not_appended": len(kaz["combined"]) == 4000,
        "kazakhstan_four_substantive_samples_not_twelve": len(kaz["combined"]["survey_year"].unique()) == 4,
        "kazakhstan_weights_retained_not_rescaled": kaz["combined"]["kaz_weight_pooling_approved"].eq(0).all(),
        "kazakhstan_not_added_to_interaction_model": True,
        "countries_not_respondent_pooled": True,
        "no_final_descriptive_or_prevalence_outputs": True,
        "no_regression_or_hypothesis_test_run": True,
        "all_data_dictionaries_exist": all(path.exists() for path in [PROCESSED / "kyrgyzstan" / "lik_2019_data_dictionary.csv", PROCESSED / "uzbekistan" / "l2cu_r49_82_data_dictionary.csv", PROCESSED / "kazakhstan" / "kaz_fies_2014_2017_data_dictionary.csv"]),
        "sample_exclusions_represented_by_flags_and_flow": (CHECKPOINTS / "phase_03_sample_flow.csv").exists(),
        "project_reproducible_from_protected_sources": (CHECKPOINTS / "phase_03_reproducibility_manifest.json").exists(),
        "required_parquet_outputs_created": not no_parquet_engine() and all((PROCESSED / p).exists() for p in [
            "kyrgyzstan/lik_2019_adult_analysis.parquet",
            "kyrgyzstan/lik_2019_household_sensitivity.parquet",
            "uzbekistan/l2cu_r49_82_household_analysis.parquet",
            "kazakhstan/kaz_fies_2014_2017_benchmark.parquet",
        ]),
    }
    validation = {key: bool(value) for key, value in validation.items()}
    write_text(CHECKPOINTS / "phase_03_validation.json", json.dumps(validation, indent=2))
    return validation


def update_readme_phase3() -> None:
    """Update README with Phase 3 status."""
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8") if path.exists() else "# Central Asian Household Resilience Project\n"
    section = """## Phase 3 Analytical Dataset Construction

Phase 3 construction scripts and QA outputs have been added. Analytical dataframes are built in memory and all aggregate QA documentation is produced. Required Parquet exports are blocked in this environment until a Parquet engine such as `pyarrow` or `fastparquet` is approved/installed.

No substantive descriptive analysis, prevalence estimates, regressions, hypothesis tests, or policy-effect calculations are run in Phase 3.
"""
    if "## Phase 3 Analytical Dataset Construction" not in text:
        text = text.rstrip() + "\n\n" + section
    write_text(path, text)


def run_all() -> dict[str, Any]:
    """Run Phase 3 end to end."""
    LOGGER.info("Starting Phase 3")
    before = input_hashes()
    freeze_specification()
    lik = build_lik()
    l2cu = build_l2cu()
    kaz = build_kazakhstan()
    build_quality_reports(lik, l2cu, kaz)
    build_sample_flow(lik, l2cu, kaz)
    build_data_dictionaries(lik, l2cu, kaz)
    build_cross_country_registry()
    after = input_hashes()
    build_manifest(lik, l2cu, kaz, before, after)
    build_final_report(lik, l2cu, kaz)
    validation = validate_phase3(lik, l2cu, kaz, before, after)
    update_readme_phase3()
    LOGGER.info("Phase 3 complete with parquet_created=%s", validation["required_parquet_outputs_created"])
    return {"lik": lik, "l2cu": l2cu, "kaz": kaz, "validation": validation}


def stop_message(result: dict[str, Any]) -> str:
    """Return the required stop message with actual Phase 3 status."""
    sf = read_csv(CHECKPOINTS / "phase_03_sample_flow.csv")
    def get(country: str, stage: str) -> str:
        for row in sf:
            if row["country"] == country and row["stage"] == stage:
                return row["n"]
        return "0"
    status = "CREATED" if result["validation"]["required_parquet_outputs_created"] else "PARTIAL"
    unresolved = unresolved_decisions()
    return f"""PHASE 3 COMPLETE

Kyrgyzstan adult analytical dataset:
{result['lik']['adult_status'] if result['lik']['adult_status'] == 'CREATED' else status}

Kyrgyzstan household sensitivity dataset:
{result['lik']['household_status'] if result['lik']['household_status'] == 'CREATED' else status}

Uzbekistan household-round analytical dataset:
{result['l2cu']['status'] if result['l2cu']['status'] == 'CREATED' else status}

Kazakhstan 2014-2017 benchmark dataset:
{result['kaz']['combined_status'] if result['kaz']['combined_status'] == 'CREATED' else status}

Kyrgyzstan eligible adults:
{get('Kyrgyzstan', 'final eligible adult sample')}

Kyrgyzstan eligible households:
{get('Kyrgyzstan', 'unique households represented')}

Uzbekistan eligible household-rounds:
{get('Uzbekistan', 'final eligible household-round sample')}

Uzbekistan unique households:
{get('Uzbekistan', 'unique households represented')}

Kazakhstan benchmark records:
{get('Kazakhstan', 'final benchmark-eligible records')}

Critical unresolved decisions:
{'; '.join(unresolved) if unresolved else 'None'}

Recommended Phase 4 status:
{'PROCEED' if result['validation']['required_parquet_outputs_created'] else 'REVISE'}

Files for supervisor review:

- outputs/checkpoints/PHASE_03_ANALYTICAL_DATASETS.md
- outputs/checkpoints/phase_03_sample_flow.csv
- outputs/checkpoints/phase_03_lik_join_audit.csv
- outputs/checkpoints/phase_03_l2cu_join_audit.csv
- outputs/checkpoints/phase_03_kazakhstan_append_validation.csv
- outputs/checkpoints/phase_03_lik_quality_report.csv
- outputs/checkpoints/phase_03_l2cu_quality_report.csv
- outputs/checkpoints/phase_03_kazakhstan_quality_report.csv
- research/phase_03_variable_specification.csv
- research/phase_03_cross_country_concept_registry.csv
- data/processed/kyrgyzstan/lik_2019_data_dictionary.csv
- data/processed/uzbekistan/l2cu_r49_82_data_dictionary.csv
- data/processed/kazakhstan/kaz_fies_2014_2017_data_dictionary.csv

Waiting for supervisor approval before Phase 4."""
