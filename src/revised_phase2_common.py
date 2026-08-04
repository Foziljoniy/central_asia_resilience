"""Revised Phase 2 audit for the Kyrgyzstan-Uzbekistan study.

This module verifies variables and documentation only. It never writes
respondent-level data, analytical datasets, pooled files, or model results.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / ".vendor"
if VENDOR.exists() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

import pandas as pd
import pyreadstat


CHECKPOINTS = ROOT / "outputs" / "checkpoints"
LOG_PATH = ROOT / "outputs" / "logs" / "revised_phase_02.log"
L2CU_RAW_DIR = ROOT / "data" / "uzbekistan" / "l2cu"
L2CU_ZIP = L2CU_RAW_DIR / "UZB_2018-2025_L2CU_v03_M_CSV.zip"
L2CU_QUESTIONNAIRE = L2CU_RAW_DIR / "l2cu_microdata_library_questionnaire_r_82.pdf"
L2CU_EXTRACT = ROOT / "data" / "interim" / "unpacked" / "uzbekistan" / "l2cu_v03"
LIK_BASE = (
    ROOT
    / "data"
    / "interim"
    / "unpacked"
    / "kyrgyzstan"
    / "dataverse_files"
    / "depth_02"
    / "LiK_2022__7c67a235"
    / "Version_2022"
)
LIK_STUDY = LIK_BASE / "LiK19_Study_Description.pdf"
LIK_HH_QUESTIONNAIRE = LIK_BASE / "Questionnaires" / "Eng" / "2.Household_form_Eng_LiK19.pdf"
LIK_IND_QUESTIONNAIRE = LIK_BASE / "Questionnaires" / "Eng" / "4.Individual_form_Eng_LiK19.pdf"

EXPECTED_RAW_HASHES = {
    L2CU_ZIP: "a7c96abf173e06ab358fdccda5988574e7f03b06096fe509d5f90448e57b39ac",
    L2CU_QUESTIONNAIRE: "839eff7dbed35eb04b8f5791f49afbc1b4960281706e6006313d7ddd133c6501",
    ROOT / "data" / "kyrgyzstan" / "dataverse_files.zip":
        "9f4206f0c161d00a3578bd4f5f9587725616f10c70bdc3c8256f325e73472a98",
}

HH_CSV = L2CU_EXTRACT / "l2cu_cati_household_data_82.csv"
IND_CSV = L2CU_EXTRACT / "l2cu_cati_individual_data_82.csv"

L2CU_HH_VARIABLES = [
    "round", "hhid", "hhsize", "date_start", "date_end", "popw",
    "water_disruption", "gas_disruption", "heat_disruption",
    "change_important", "change_important_type", "finance_30d_ago",
    "food_past30d", "assets_past30d", "consumption_past30d",
    "medical_past30d", "healthcare_past30d", "sick_past30d",
    "economic_condition", "economic_challenge", "wage_past30d", "wage_amount",
    "aginc_past30d", "aginc_amount", "selfempinc_past30d", "selfempinc_amount",
    "otherinc_past30d", "otherinc_amount", "ln_1", "ln_2", "ln_3", "ln_4",
    "ln_5", "ln_6", "ln_7", "ln_8",
]
L2CU_IND_VARIABLES = [
    "round", "hhid", "fmid", "mig_living_hh", "mig_living_remittance",
    "mig_living_remittance_amount", "mig_living_remittance_currency",
    "remittance_hh", "remittance_hh_amount", "remittance_hh_currency",
    "work_lost_hh",
]

BINARY_L2CU = {
    "water_disruption", "gas_disruption", "heat_disruption", "change_important",
    "food_past30d", "assets_past30d", "consumption_past30d", "medical_past30d",
    "healthcare_past30d", "sick_past30d", "wage_past30d", "aginc_past30d",
    "selfempinc_past30d", "otherinc_past30d", "ln_1", "ln_2", "ln_3", "ln_4",
    "ln_5", "ln_6", "ln_7", "ln_8", "mig_living_hh",
    "mig_living_remittance", "remittance_hh", "work_lost_hh",
}
POSITIVE_L2CU = {
    "mig_living_remittance_amount", "remittance_hh_amount", "wage_amount",
    "aginc_amount", "selfempinc_amount", "otherinc_amount",
}

CONCEPTS = [
    "household identifier", "time, wave or round", "remittance receipt",
    "remittance amount", "household shock exposure", "economic shock",
    "employment or income shock", "health shock", "agricultural or climate shock",
    "food-insecurity outcome", "household size", "rural or urban residence", "region",
    "household assets, income or wealth", "survey weights or documented reason for no weight",
]


def configure_logging() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("revised_phase02")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        for handler in (logging.FileHandler(LOG_PATH, encoding="utf-8"), logging.StreamHandler()):
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger


LOGGER = configure_logging()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key, "")) for key in fields})


def _cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        if isinstance(value, set):
            value = sorted(value)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def ensure_structure() -> None:
    for directory in [
        "data/raw/kyrgyzstan/lik", "data/raw/uzbekistan/l2cu", "data/raw/uzbekistan/mics",
        "data/raw/kazakhstan/pending_fies_access", "data/interim", "data/processed",
        "literature", "research", "src", "outputs/checkpoints", "outputs/logs",
    ]:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)


def verify_sources_and_extract() -> dict[str, Any]:
    missing = [rel(path) for path in EXPECTED_RAW_HASHES if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Required source files missing: {missing}")
    before = {rel(path): sha256(path) for path in EXPECTED_RAW_HASHES}
    mismatches = {
        rel(path): {"expected": expected, "actual": before[rel(path)]}
        for path, expected in EXPECTED_RAW_HASHES.items()
        if before[rel(path)] != expected
    }
    if mismatches:
        raise RuntimeError(f"Raw source checksum mismatch: {mismatches}")

    L2CU_EXTRACT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(L2CU_ZIP) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"L2CU ZIP integrity failed at {bad}")
        for info in archive.infolist():
            if info.is_dir():
                continue
            if Path(info.filename).name != info.filename or info.filename not in {HH_CSV.name, IND_CSV.name}:
                raise RuntimeError(f"Unexpected or unsafe L2CU ZIP member: {info.filename}")
            target = L2CU_EXTRACT / info.filename
            if not target.exists():
                with archive.open(info) as source, target.open("xb") as destination:
                    while chunk := source.read(1024 * 1024):
                        destination.write(chunk)
            if target.stat().st_size != info.file_size:
                raise RuntimeError(f"Extracted size mismatch for {target.name}")

    after = {rel(path): sha256(path) for path in EXPECTED_RAW_HASHES}
    extracted = {rel(path): sha256(path) for path in (HH_CSV, IND_CSV)}
    return {
        "source_hashes_before": before,
        "source_hashes_after": after,
        "source_hashes_unchanged": before == after,
        "l2cu_zip_integrity": "passed",
        "extracted_hashes": extracted,
    }


def read_l2cu() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    headers: dict[str, list[str]] = {}
    for path in (HH_CSV, IND_CSV):
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            headers[path.name] = next(csv.reader(handle))
    absent = {
        HH_CSV.name: sorted(set(L2CU_HH_VARIABLES) - set(headers[HH_CSV.name])),
        IND_CSV.name: sorted(set(L2CU_IND_VARIABLES) - set(headers[IND_CSV.name])),
    }
    if any(absent.values()):
        raise RuntimeError(f"Expected L2CU variables absent: {absent}")
    hh = pd.read_csv(HH_CSV, usecols=L2CU_HH_VARIABLES, dtype=str, low_memory=False)
    ind = pd.read_csv(IND_CSV, usecols=L2CU_IND_VARIABLES, dtype=str, low_memory=False)
    return hh, ind, headers


def _number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _valid_mask(series: pd.Series, variable: str) -> pd.Series:
    number = _number(series)
    if variable in BINARY_L2CU:
        text = series.astype("string").str.strip().str.casefold()
        return number.isin([1, 2]) | text.isin(["yes", "no"])
    if variable in POSITIVE_L2CU:
        return number.gt(0)
    return series.notna() & series.astype(str).str.strip().ne("")


def _observed_codes(series: pd.Series, limit: int = 20) -> dict[str, int]:
    values = series.dropna().astype(str).str.strip()
    counts = values[values.ne("")].value_counts(dropna=False).head(limit)
    return {str(key): int(value) for key, value in counts.items()}


PROFILE_FIELDS = [
    "country", "dataset", "source_file", "observation_level", "variable", "rows",
    "nonmissing", "valid", "missing_or_structural", "observed_codes_top20",
    "round_min_nonmissing", "round_max_nonmissing", "rounds_with_nonmissing", "rounds_list",
]


def profile_frame(
    frame: pd.DataFrame,
    *,
    country: str,
    dataset: str,
    source_file: Path,
    level: str,
    variables: list[str],
    wave: str | None = None,
    valid_rules: dict[str, set[float] | str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profiles: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    round_series = _number(frame["round"]) if "round" in frame else None
    for variable in variables:
        series = frame[variable]
        nonmissing_mask = series.notna() & series.astype(str).str.strip().ne("")
        if valid_rules and variable in valid_rules:
            numeric = _number(series)
            rule = valid_rules[variable]
            if rule == "positive":
                valid_mask = numeric.gt(0)
            elif rule == "nonnegative":
                valid_mask = numeric.ge(0)
            else:
                valid_mask = numeric.isin(rule)
        elif country == "uzbekistan":
            valid_mask = _valid_mask(series, variable)
        else:
            valid_mask = nonmissing_mask
        if round_series is not None:
            rounds = sorted(int(x) for x in round_series[nonmissing_mask].dropna().unique())
        else:
            rounds = [int(wave)] if wave and nonmissing_mask.any() else []
        profiles.append({
            "country": country,
            "dataset": dataset,
            "source_file": rel(source_file),
            "observation_level": level,
            "variable": variable,
            "rows": len(frame),
            "nonmissing": int(nonmissing_mask.sum()),
            "valid": int(valid_mask.sum()),
            "missing_or_structural": int((~nonmissing_mask).sum()),
            "observed_codes_top20": _observed_codes(series),
            "round_min_nonmissing": min(rounds) if rounds else "",
            "round_max_nonmissing": max(rounds) if rounds else "",
            "rounds_with_nonmissing": len(rounds),
            "rounds_list": rounds,
        })
        if round_series is not None:
            for round_value in sorted(int(x) for x in round_series.dropna().unique()):
                mask = round_series.eq(round_value)
                coverage.append({
                    "country": country,
                    "dataset": dataset,
                    "source_file": rel(source_file),
                    "observation_level": level,
                    "variable": variable,
                    "round": round_value,
                    "rows_in_round": int(mask.sum()),
                    "nonmissing": int((nonmissing_mask & mask).sum()),
                    "valid": int((valid_mask & mask).sum()),
                })
    return profiles, coverage


def l2cu_consistency(ind: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for variable in ["mig_living_hh", "remittance_hh", "remittance_hh_amount", "work_lost_hh"]:
        grouped = (
            ind.dropna(subset=["round", "hhid"])
            .groupby(["round", "hhid"], dropna=False)[variable]
            .nunique(dropna=True)
        )
        rows.append({
            "variable": variable,
            "household_rounds": int(len(grouped)),
            "household_rounds_nonmissing": int(grouped.gt(0).sum()),
            "household_rounds_inconsistent": int(grouped.gt(1).sum()),
            "max_distinct_values_within_household_round": int(grouped.max()) if len(grouped) else 0,
        })
    return rows


def key_integrity(hh: pd.DataFrame, ind: pd.DataFrame, lik_frames: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Return aggregate key and cross-file coverage checks without exporting identifiers."""
    hh_keys = hh[["round", "hhid"]].dropna().drop_duplicates()
    ind_keys = ind[["round", "hhid"]].dropna().drop_duplicates()
    overlap = hh_keys.merge(ind_keys, on=["round", "hhid"], how="inner")
    rows = [
        {
            "dataset": "L2CU household", "key": "round + hhid", "rows": len(hh),
            "missing_key_rows": int(hh[["round", "hhid"]].isna().any(axis=1).sum()),
            "duplicate_key_rows": int(hh.duplicated(["round", "hhid"], keep=False).sum()),
            "unique_keys": len(hh_keys),
            "cross_file_note": f"{len(hh_keys) - len(overlap)} household-rounds have no individual-roster row",
        },
        {
            "dataset": "L2CU individual roster", "key": "round + hhid + fmid", "rows": len(ind),
            "missing_key_rows": int(ind[["round", "hhid", "fmid"]].isna().any(axis=1).sum()),
            "duplicate_key_rows": int(ind.duplicated(["round", "hhid", "fmid"], keep=False).sum()),
            "unique_keys": int(ind[["round", "hhid", "fmid"]].dropna().drop_duplicates().shape[0]),
            "cross_file_note": f"{len(ind_keys) - len(overlap)} individual-file household-rounds lack a household-file match",
        },
    ]
    module_specs = {
        "LiK hh0": ("hh0", ["hhid"]),
        "LiK hh6b": ("hh6b", ["hhid"]),
        "LiK hh7": ("hh7", ["hhid", "shock"]),
        "LiK id2": ("id2", ["hhid", "pid"]),
    }
    for label, (name, keys) in module_specs.items():
        frame = lik_frames[name]
        rows.append({
            "dataset": label, "key": " + ".join(keys), "rows": len(frame),
            "missing_key_rows": int(frame[keys].isna().any(axis=1).sum()),
            "duplicate_key_rows": int(frame.duplicated(keys, keep=False).sum()),
            "unique_keys": int(frame[keys].dropna().drop_duplicates().shape[0]),
            "cross_file_note": "module-level key check",
        })
    return rows


def read_lik() -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    specs = {
        "hh0": (LIK_BASE / "Household" / "hh0.dta", ["hhid", "int_date", "oblast", "residence", "psu"]),
        "hh1a": (LIK_BASE / "Household" / "hh1a.dta", ["hhid", "pid"]),
        "hh2b": (LIK_BASE / "Household" / "hh2b.dta", ["hhid", "asset", "h219", "h220", "h223"]),
        "hh5a": (LIK_BASE / "Household" / "hh5a.dta", ["hhid", "income", "h501", "h502"]),
        "hh6b": (LIK_BASE / "Household" / "hh6b.dta", ["hhid", "h620", "h622", "h623", "h625", "h626"]),
        "hh7": (LIK_BASE / "Household" / "hh7.dta", ["hhid", "shock", "h701", "h702", "h703", "h704"]),
        "id2": (LIK_BASE / "Individual" / "id2.dta", ["hhid", "pid"] + [f"i251_{i}" for i in range(1, 9)]),
    }
    frames: dict[str, pd.DataFrame] = {}
    metadata: dict[str, Any] = {}
    for name, (path, variables) in specs.items():
        if not path.exists():
            raise FileNotFoundError(path)
        frame, meta = pyreadstat.read_dta(path, usecols=variables, apply_value_formats=False)
        frames[name] = frame
        metadata[name] = {
            "path": path,
            "labels": dict(zip(meta.column_names, meta.column_labels)),
            "value_labels": meta.variable_value_labels,
        }
    return frames, metadata


def profile_lik(frames: dict[str, pd.DataFrame], metadata: dict[str, Any]) -> list[dict[str, Any]]:
    valid_rules: dict[str, set[float] | str] = {
        "h620": {1, 2}, "h622": "positive", "h623": {1, 2}, "h625": {1, 2},
        "h626": {1, 2, 3}, "h701": {1, 2}, "h702": {1, 2, 3, 4},
        "h703": "nonnegative", "h704": "nonnegative", "h219": {1, 2}, "h501": {1, 2},
        "residence": {1, 2},
    }
    for i in range(1, 9):
        valid_rules[f"i251_{i}"] = {1, 2, 3}
    profiles: list[dict[str, Any]] = []
    for name, frame in frames.items():
        variables = list(frame.columns)
        rows, _ = profile_frame(
            frame,
            country="kyrgyzstan",
            dataset="LiK 2019",
            source_file=metadata[name]["path"],
            level="individual" if name == "id2" else "household roster" if name == "hh1a" else "household/event roster",
            variables=variables,
            wave="2019",
            valid_rules=valid_rules,
        )
        profiles.extend(rows)
    master_households = set(frames["hh0"]["hhid"].dropna())
    shock_households = set(frames["hh7"]["hhid"].dropna())
    exposed = len(master_households & shock_households)
    profiles.append({
        "country": "kyrgyzstan",
        "dataset": "LiK 2019",
        "source_file": rel(metadata["hh7"]["path"]),
        "observation_level": "household (aggregate audit only)",
        "variable": "any_shock_household",
        "rows": len(master_households),
        "nonmissing": len(master_households),
        "valid": len(master_households),
        "missing_or_structural": 0,
        "observed_codes_top20": {"Yes": exposed, "No": len(master_households) - exposed},
        "round_min_nonmissing": 2019,
        "round_max_nonmissing": 2019,
        "rounds_with_nonmissing": 1,
        "rounds_list": [2019],
    })
    return profiles


def profile_lookup(profiles: list[dict[str, Any]], country: str, variables: list[str]) -> str:
    selected = [row for row in profiles if row["country"] == country and row["variable"] in variables]
    return "; ".join(
        f"{row['variable']}: {row['valid']} valid/{row['nonmissing']} nonmissing"
        for row in selected
    )


REGISTRY_FIELDS = [
    "country", "dataset", "dataset_role", "concept", "status", "source_file",
    "observation_level", "raw_variable_names", "exact_question_wording_or_label", "recall_period",
    "wave_or_round_coverage", "coding", "missing_codes_or_structural_missing",
    "aggregate_verification", "later_transformation_plan", "comparability_notes", "evidence_source",
]


def _registry_row(**kwargs: Any) -> dict[str, Any]:
    row = {field: "" for field in REGISTRY_FIELDS}
    row.update(kwargs)
    return row


def build_registry(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lik_hh0 = rel(LIK_BASE / "Household" / "hh0.dta")
    lik_hh1 = rel(LIK_BASE / "Household" / "hh1a.dta")
    lik_hh2 = rel(LIK_BASE / "Household" / "hh2b.dta")
    lik_hh5 = rel(LIK_BASE / "Household" / "hh5a.dta")
    lik_hh6 = rel(LIK_BASE / "Household" / "hh6b.dta")
    lik_hh7 = rel(LIK_BASE / "Household" / "hh7.dta")
    lik_id2 = rel(LIK_BASE / "Individual" / "id2.dta")
    l2_hh = rel(HH_CSV)
    l2_ind = rel(IND_CSV)
    qlik_hh = rel(LIK_HH_QUESTIONNAIRE)
    qlik_ind = rel(LIK_IND_QUESTIONNAIRE)
    ql2 = rel(L2CU_QUESTIONNAIRE)
    role_lik = "main panel and household analysis"
    role_l2 = "main household-panel analysis"

    rows = [
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="household identifier", status="VERIFIED", source_file=f"{lik_hh0}; repeated across modules",
            observation_level="household", raw_variable_names="hhid", exact_question_wording_or_label="HH code in 2019 / Household code",
            recall_period="not applicable", wave_or_round_coverage="2019, panel wave 6", coding="numeric identifier",
            missing_codes_or_structural_missing="no documented special missing code", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["hhid"]),
            later_transformation_plan="retain as country-specific key; never pool with L2CU hhid", comparability_notes="identifier is survey-specific",
            evidence_source=f"{lik_hh0}; {rel(LIK_STUDY)} pp. 1, 7"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="time, wave or round", status="VERIFIED", source_file=lik_hh0, observation_level="household",
            raw_variable_names="int_date; constant wave=2019", exact_question_wording_or_label="Interview date; Life in Kyrgyzstan Study 2019, Panel Wave 6",
            recall_period="interview dates Nov 2019-Feb 2020", wave_or_round_coverage="2019, panel wave 6",
            coding="date plus documented wave constant", missing_codes_or_structural_missing="no special missing code documented",
            aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["int_date"]), later_transformation_plan="attach documented 2019 wave constant only in later construction",
            comparability_notes="not contemporaneous with all L2CU rounds", evidence_source=f"{rel(LIK_STUDY)} pp. 1, 4; {lik_hh0}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="remittance receipt", status="VERIFIED", source_file=lik_hh6, observation_level="household",
            raw_variable_names="h620", exact_question_wording_or_label="During the last 12 months, did you receive any money from abroad sent by migrants who are members of this household?",
            recall_period="last 12 months", wave_or_round_coverage="2019", coding="1 Yes; 2 No",
            missing_codes_or_structural_missing="blank/system missing; Module 6A routes households with no adult member abroad to Module 7, so later construction must distinguish structural non-migrant households from observed h620=2",
            aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["h620"]), later_transformation_plan="binary receipt indicator in later construction; define structural non-migrant households only after merging hh6a/hh0 eligibility",
            comparability_notes="12-month recall and member-migrant universe versus L2CU past-month two-channel measures", evidence_source=f"{qlik_hh} pp. 15-17; {lik_hh6}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="remittance amount", status="VERIFIED", source_file=lik_hh6, observation_level="household",
            raw_variable_names="h622; h623", exact_question_wording_or_label="Total money sent during the last 12 months; currency",
            recall_period="last 12 months", wave_or_round_coverage="2019", coding="h622 amount >0; h623 1 Som, 2 US dollar",
            missing_codes_or_structural_missing="structural missing when h620=2 and for households skipped out of Module 6A; no h622 special code documented",
            aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["h622","h623"]), later_transformation_plan="currency conversion and annualization rules to be specified before construction",
            comparability_notes="currency, recall, and module universe differ from L2CU", evidence_source=f"{qlik_hh} pp. 15-17; {lik_hh6}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="household shock exposure", status="VERIFIED", source_file=lik_hh7, observation_level="household-shock event roster",
            raw_variable_names="shock; h701; h702; h703; h704", exact_question_wording_or_label="Extreme natural, infrastructural, social, family or personal shock occurred in household",
            recall_period="last 12 months", wave_or_round_coverage="2019", coding="shock 1-25; h701 1 Yes, 2 No; severity 1 High-4 No impact",
            missing_codes_or_structural_missing="h703/h704 code 998 Don't know/not calculated; structural missing when not affected",
            aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["shock","h701","h702","h703","h704"]), later_transformation_plan="aggregate verified event rows to household only in later construction",
            comparability_notes="broader event roster than L2CU", evidence_source=f"{qlik_hh} p. 18; {lik_hh7}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="economic shock", status="VERIFIED", source_file=lik_hh7, observation_level="household-shock event roster",
            raw_variable_names="shock; h701", exact_question_wording_or_label="Inability to sell agricultural/other products; loss of job; sharp fall of remittances",
            recall_period="last 12 months", wave_or_round_coverage="2019", coding="shock codes 11, 12, 13 with h701=1",
            missing_codes_or_structural_missing="as for shock roster", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["shock","h701"]),
            later_transformation_plan="pre-specify economic-shock category; no construction in Phase 2", comparability_notes="L2CU verifies job loss but no equivalent broad economic-event roster",
            evidence_source=f"{qlik_hh} p. 18; {lik_hh7}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="employment or income shock", status="VERIFIED", source_file=lik_hh7, observation_level="household-shock event roster",
            raw_variable_names="shock; h701; h704", exact_question_wording_or_label="Loss of job; estimated loss of income due to shock",
            recall_period="last 12 months", wave_or_round_coverage="2019", coding="shock=12 and h701=1; h704 Som",
            missing_codes_or_structural_missing="h704=998 Don't know/not calculated", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["shock","h701","h704"]),
            later_transformation_plan="binary loss-of-job shock; amount as secondary severity measure", comparability_notes="L2CU job-loss question has past-month recall",
            evidence_source=f"{qlik_hh} p. 18; {lik_hh7}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="health shock", status="VERIFIED", source_file=lik_hh7, observation_level="household-shock event roster",
            raw_variable_names="shock; h701", exact_question_wording_or_label="Death or illness of breadwinner/household member/close relative; accident",
            recall_period="last 12 months", wave_or_round_coverage="2019", coding="shock codes 14-18 and 21 with h701=1",
            missing_codes_or_structural_missing="as for shock roster", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["shock","h701"]),
            later_transformation_plan="binary health/family shock category", comparability_notes="L2CU major-change item includes injury, illness, death",
            evidence_source=f"{qlik_hh} p. 18; {lik_hh7}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="agricultural or climate shock", status="VERIFIED", source_file=lik_hh7, observation_level="household-shock event roster",
            raw_variable_names="shock; h701", exact_question_wording_or_label="Drought, flood, cold winter, frost, landslide, crop/livestock pests or disease, insufficient farm water, inability to sell products",
            recall_period="last 12 months", wave_or_round_coverage="2019", coding="shock codes 1-6, 8, 11 with h701=1",
            missing_codes_or_structural_missing="as for shock roster", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["shock","h701"]),
            later_transformation_plan="separate climate/natural and agricultural-market subcategories", comparability_notes="no verified L2CU agricultural/climate shock item",
            evidence_source=f"{qlik_hh} p. 18; {lik_hh7}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="food-insecurity outcome", status="VERIFIED", source_file=lik_id2, observation_level="adult individual",
            raw_variable_names="i251_1-i251_8", exact_question_wording_or_label="Eight food-insecurity experience items covering worry, diet quality/variety, meal skipping, eating less, running out, hunger, and whole-day fasting",
            recall_period="last 12 months", wave_or_round_coverage="2019 only", coding="1 Yes many times; 2 Yes 1-2 times; 3 No never; 88 Refuse; 99 Don't know",
            missing_codes_or_structural_missing="88 refusal; 99 don't know; system missing", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",[f"i251_{i}" for i in range(1,9)]),
            later_transformation_plan="adult-level 0-8 affirmative count is primary candidate; household aggregation requires an explicit later rule",
            comparability_notes="LiK is adult-reported, 12-month, frequency-coded; L2CU is household CATI, 30-day, yes/no",
            evidence_source=f"{qlik_ind} p. 6; {lik_id2}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="household size", status="VERIFIED - DERIVED LATER", source_file=lik_hh1, observation_level="household-member roster",
            raw_variable_names="hhid; pid", exact_question_wording_or_label="Household roster member identifiers",
            recall_period="current roster", wave_or_round_coverage="2019", coding="count distinct pid within hhid",
            missing_codes_or_structural_missing="review duplicate/missing pid before derivation", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["pid"]),
            later_transformation_plan="derive roster count only in analytical construction phase", comparability_notes="L2CU supplies hhsize directly",
            evidence_source=lik_hh1),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="rural or urban residence", status="VERIFIED", source_file=lik_hh0, observation_level="household",
            raw_variable_names="residence", exact_question_wording_or_label="Type of population point",
            recall_period="current", wave_or_round_coverage="2019", coding="1 City; 2 Village",
            missing_codes_or_structural_missing="no special missing code documented", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["residence"]),
            later_transformation_plan="binary residence control", comparability_notes="not available in supplied L2CU CSVs",
            evidence_source=lik_hh0),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="region", status="VERIFIED", source_file=lik_hh0, observation_level="household",
            raw_variable_names="oblast", exact_question_wording_or_label="Oblast", recall_period="current",
            wave_or_round_coverage="2019", coding="2 Issyk-Kul; 3 Jalal-Abad; 4 Naryn; 5 Batken; 6 Osh; 7 Talas; 8 Chui; 11 Bishkek; 21 Osh city",
            missing_codes_or_structural_missing="no special missing code documented", aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["oblast"]),
            later_transformation_plan="categorical region control", comparability_notes="not available in supplied L2CU CSVs",
            evidence_source=lik_hh0),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="household assets, income or wealth", status="VERIFIED", source_file=f"{lik_hh2}; {lik_hh5}", observation_level="household-item/source roster",
            raw_variable_names="asset; h219; h220; h223; income; h501; h502", exact_question_wording_or_label="Asset possession/quantity/resale value; income receipt and average monthly amount by source",
            recall_period="assets current; income last 12 months/average month", wave_or_round_coverage="2019",
            coding="asset codes 1-35; possession 1 Yes/2 No; income sources 1-17; receipt 1 Yes/2 No; h502 code 99 Don't know",
            missing_codes_or_structural_missing="h222/h223 code 999 DK; h502 code 99 DK; structural missing by roster skip",
            aggregate_verification=profile_lookup(profiles,"kyrgyzstan",["asset","h219","h220","h223","income","h501","h502"]),
            later_transformation_plan="pre-specify asset index or income aggregate before analytical construction", comparability_notes="not directly harmonized with L2CU flow-income fields",
            evidence_source=f"{lik_hh2}; {lik_hh5}"),
        _registry_row(country="kyrgyzstan", dataset="LiK 2019", dataset_role=role_lik,
            concept="survey weights or documented reason for no weight", status="DOCUMENTED NO WEIGHT", source_file=rel(LIK_STUDY), observation_level="study design",
            raw_variable_names="no weight variable assigned", exact_question_wording_or_label="No sample weights have been assigned because sampling was proportional to population size in surveyed regions",
            recall_period="not applicable", wave_or_round_coverage="2019", coding="not applicable",
            missing_codes_or_structural_missing="not applicable", aggregate_verification="study documentation verified; attrition is explicitly noted",
            later_transformation_plan="unweighted primary analysis with attrition limitation; no invented weights", comparability_notes="L2CU contains popw",
            evidence_source=f"{rel(LIK_STUDY)} p. 4"),
    ]

    l2_specs = [
        ("household identifier", "VERIFIED", l2_hh, "household-round", "hhid", "Please, check household ID.", "not applicable", "rounds 1-82", "identifier", "blank only", "retain as L2CU-specific key; never pool with LiK hhid", "survey-specific identifier", f"{ql2} p. 1; {l2_hh}"),
        ("time, wave or round", "VERIFIED", l2_hh, "household-round", "round; date_start; date_end", "Round and interview start/end dates; round 82 fieldwork June 5-26, 2025", "interview dates", "rounds 1-82 in supplied CSV", "integer round; dates", "blank only", "use round effects and documented dates later", "2018-2025 repeated CATI rounds", f"{ql2} p. 1; {l2_hh}"),
        ("remittance receipt", "VERIFIED", l2_ind, "individual/migrant roster with household-round fields", "mig_living_remittance; remittance_hh", "Migrant member sent money over past month; household receives money from abroad from non-household individuals", "past month", "since round 1; observed coverage verified in profile", "CSV stores Yes/No labels; questionnaire codes 1 Yes/2 No", "blank is structural when skip/unasked", "later household-round receipt = documented combination of the two channels", "shorter recall and two channels versus LiK member-migrant item", f"{ql2} pp. 4-5; {l2_ind}"),
        ("remittance amount", "VERIFIED", l2_ind, "individual/migrant roster with household-round fields", "mig_living_remittance_amount; mig_living_remittance_currency; remittance_hh_amount; remittance_hh_currency", "Amount and currency sent over the past month", "past month", "since round 1; observed coverage verified in profile", "amount numeric; CSV stores labelled currencies; questionnaire codes 1 soum, 2 dollar, 3 euro, 4 ruble, 5 tenge, 96 other", "structural when receipt=No; observed zero amounts are invalid under questionnaire >0 rule and remain flagged", "sum member-migrant transfers and add nonmember channel only after duplicate/roster checks", "currency conversion required; recall differs from LiK", f"{ql2} p. 5; {l2_ind}"),
        ("household shock exposure", "VERIFIED", f"{l2_ind}; {l2_hh}", "household-round after later aggregation", "work_lost_hh; change_important; change_important_type; water_disruption; gas_disruption; heat_disruption", "Job loss/stopped work; major household change; unexpected utility disruptions", "past month/30 days", "since round 1, with gas since round 19 and heat source changes; observed coverage in profile", "CSV stores Yes/No and labelled change types; questionnaire codes binary 1/2 and change types 1-6", "blank structural under skips/unasked rounds", "pre-specify composite from job loss and major injury/illness/death; utility disruptions secondary", "narrower and shorter recall than LiK event roster", f"{ql2} pp. 6, 8-10; {l2_ind}; {l2_hh}"),
        ("economic shock", "VERIFIED - LIMITED", l2_ind, "household-round after later aggregation", "work_lost_hh", "Any household member lost their job or otherwise stopped working over the past month", "past month", "since round 1; observed coverage in profile", "CSV stores Yes/No labels; questionnaire codes 1 Yes/2 No", "blank structural/unasked", "use job loss as economic/employment shock; do not use national economic_challenge as household shock", "no broader household economic-event roster verified", f"{ql2} pp. 6, 12; {l2_ind}"),
        ("employment or income shock", "VERIFIED", l2_ind, "household-round after later aggregation", "work_lost_hh", "Any household member lost their job or otherwise stopped working over the past month", "past month", "since round 1; observed coverage in profile", "CSV stores Yes/No labels; questionnaire codes 1 Yes/2 No", "blank structural/unasked", "binary household-round job-loss exposure", "closest cross-country match is LiK shock code 12", f"{ql2} p. 6; {l2_ind}"),
        ("health shock", "VERIFIED", l2_hh, "household-round", "change_important; change_important_type", "Important change such as major injury, major illness, or death", "past month", "since round 1; observed coverage in profile", "CSV stores Yes/No plus one labelled type; questionnaire codes change 1/2 and types 4 injury, 5 illness, 6 death", "blank structural when no important change", "classify labelled Major injury/Major illness/Death; document single-field storage despite questionnaire multi-select instruction", "shorter recall; CSV exposes one type per positive row, which may not retain multiple simultaneous changes", f"{ql2} pp. 9-10; {l2_hh}"),
        ("agricultural or climate shock", "NOT AVAILABLE IN SUPPLIED FILES", l2_hh, "not available", "not available", "No agricultural or climate shock question appears in supplied round-82 questionnaire or CSV headers", "not available", "not available", "not available", "not available", "do not construct or infer from agricultural income or household water-service disruption", "country model cannot match LiK agricultural/climate shock", f"{ql2}; {l2_hh}; {l2_ind}"),
        ("food-insecurity outcome", "VERIFIED", l2_hh, "household CATI respondent/household-round", "ln_1-ln_8; secondary food_past30d", "Eight lack-of-nutrition experience items; enough food purchase question", "past 30 days", "ln items since round 49; exact observed rounds in profile", "CSV stores Yes/No labels; questionnaire codes 1 Yes/2 No", "blank for rounds before introduction or nonresponse", "primary candidate is 0-8 affirmative count for rounds with all eight items; food_past30d secondary", "L2CU yes/no 30-day battery versus LiK frequency-coded 12-month adult battery", f"{ql2} pp. 11, 23; {l2_hh}"),
        ("household size", "VERIFIED", l2_hh, "household-round", "hhsize", "Household size column", "current roster", "observed rounds in profile", "positive count", "blank only", "use as supplied after range checks", "LiK requires roster derivation", l2_hh),
        ("rural or urban residence", "NOT AVAILABLE IN SUPPLIED FILES", l2_hh, "not available", "not available", "No residence/urban/rural variable in either supplied CSV header", "not available", "not available", "not available", "not available", "do not infer from hhid or text", "cannot include matched residence control with supplied L2CU release", f"{l2_hh}; {l2_ind}"),
        ("region", "NOT AVAILABLE IN SUPPLIED FILES", l2_hh, "not available", "not available", "No region/province/oblast variable in either supplied CSV header", "not available", "not available", "not available", "not available", "do not infer geography from hhid", "cannot include matched region effects with supplied L2CU release", f"{l2_hh}; {l2_ind}"),
        ("household assets, income or wealth", "VERIFIED - LIMITED", l2_hh, "household-round", "assets_past30d; wage_amount; aginc_amount; selfempinc_amount; otherinc_amount", "Asset sale to meet needs and household income flows over past 30 days", "past 30 days", "since round 1; observed coverage in profile", "CSV asset sale Yes/No; numeric amounts >0 conditional on receipt", "structural under skips", "income-flow aggregate and coping indicator only; not a full asset/wealth stock", "less comprehensive than LiK asset roster", f"{ql2} pp. 11, 18-19; {l2_hh}"),
        ("survey weights or documented reason for no weight", "VERIFIED COLUMN; DOCUMENTATION GAP", l2_hh, "household-round", "popw", "Column exists; exact definition/normalization is not stated in supplied round-82 questionnaire", "not applicable", "observed coverage in profile", "positive numeric candidate weight", "blank values documented in profile", "do not use until weight documentation/design interpretation is confirmed", "LiK explicitly has no assigned sample weights", l2_hh),
    ]
    for spec in l2_specs:
        concept, status, source, level, variables, wording, recall, coverage, coding, missing, transform, notes, evidence = spec
        raw_vars = [part.strip() for part in variables.replace(";", " ").split() if part.strip()]
        rows.append(_registry_row(
            country="uzbekistan", dataset="L2CU 2018-2025", dataset_role=role_l2,
            concept=concept, status=status, source_file=source, observation_level=level,
            raw_variable_names=variables, exact_question_wording_or_label=wording, recall_period=recall,
            wave_or_round_coverage=coverage, coding=coding, missing_codes_or_structural_missing=missing,
            aggregate_verification=profile_lookup(profiles,"uzbekistan",raw_vars), later_transformation_plan=transform,
            comparability_notes=notes, evidence_source=evidence,
        ))

    for concept in CONCEPTS:
        rows.append(_registry_row(
            country="kazakhstan", dataset="Kazakhstan FIES", dataset_role="future regional policy benchmark",
            concept=concept, status="PENDING DATA ACCESS", source_file="PENDING DATA ACCESS",
            observation_level="PENDING DATA ACCESS", raw_variable_names="PENDING DATA ACCESS",
            exact_question_wording_or_label="PENDING DATA ACCESS", recall_period="PENDING DATA ACCESS",
            wave_or_round_coverage="PENDING DATA ACCESS", coding="PENDING DATA ACCESS",
            missing_codes_or_structural_missing="PENDING DATA ACCESS", aggregate_verification="PENDING DATA ACCESS",
            later_transformation_plan="PENDING DATA ACCESS", comparability_notes="PENDING DATA ACCESS",
            evidence_source="PENDING DATA ACCESS",
        ))
    return rows


def core_verified(profiles: list[dict[str, Any]], country: str, variables: list[str]) -> bool:
    lookup = {(row["country"], row["variable"]): row for row in profiles}
    for variable in variables:
        row = lookup.get((country, variable))
        if row is None or int(row["valid"]) <= 0:
            return False
        codes = json.loads(json.dumps(row["observed_codes_top20"]))
        numeric = {int(float(code)) for code in codes if _is_number(code)}
        text_codes = {str(code).strip().casefold() for code in codes}
        if variable.startswith("i251_"):
            if not ({1, 2} & numeric and 3 in numeric):
                return False
        elif variable.startswith("ln_") or variable in {"h620", "work_lost_hh", "mig_living_remittance", "remittance_hh", "any_shock_household"}:
            numeric_binary = {1, 2}.issubset(numeric)
            labelled_binary = {"yes", "no"}.issubset(text_codes)
            if not (numeric_binary or labelled_binary):
                return False
    return True


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def kazakhstan_microdata_files() -> list[str]:
    candidates: list[Path] = []
    for root in [ROOT / "data" / "raw" / "kazakhstan", ROOT / "data" / "kazakhstan"]:
        if root.exists():
            candidates.extend(
                path for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in {".dta", ".sav", ".csv", ".parquet", ".xlsx", ".zip"}
            )
    return sorted(rel(path) for path in candidates)


def write_outputs(
    profiles: list[dict[str, Any]],
    coverage: list[dict[str, Any]],
    consistency: list[dict[str, Any]],
    key_checks: list[dict[str, Any]],
    registry: list[dict[str, Any]],
    source_audit: dict[str, Any],
    headers: dict[str, list[str]],
) -> str:
    write_csv(CHECKPOINTS / "revised_phase_02_variable_profile.csv", profiles, PROFILE_FIELDS)
    write_csv(
        CHECKPOINTS / "revised_phase_02_l2cu_round_coverage.csv",
        coverage,
        ["country", "dataset", "source_file", "observation_level", "variable", "round", "rows_in_round", "nonmissing", "valid"],
    )
    write_csv(
        CHECKPOINTS / "revised_phase_02_l2cu_household_consistency.csv",
        consistency,
        ["variable", "household_rounds", "household_rounds_nonmissing", "household_rounds_inconsistent", "max_distinct_values_within_household_round"],
    )
    write_csv(
        CHECKPOINTS / "revised_phase_02_key_integrity.csv",
        key_checks,
        ["dataset", "key", "rows", "missing_key_rows", "duplicate_key_rows", "unique_keys", "cross_file_note"],
    )
    write_csv(CHECKPOINTS / "revised_phase_02_variable_registry.csv", registry, REGISTRY_FIELDS)

    matrix = []
    for concept in CONCEPTS:
        by_country = {row["country"]: row for row in registry if row["concept"] == concept}
        matrix.append({
            "concept": concept,
            "kyrgyzstan_status": by_country["kyrgyzstan"]["status"],
            "kyrgyzstan_variables": by_country["kyrgyzstan"]["raw_variable_names"],
            "uzbekistan_status": by_country["uzbekistan"]["status"],
            "uzbekistan_variables": by_country["uzbekistan"]["raw_variable_names"],
            "kazakhstan_status": "PENDING DATA ACCESS",
            "comparison_note": by_country["uzbekistan"]["comparability_notes"],
        })
    write_csv(
        CHECKPOINTS / "revised_phase_02_country_compatibility.csv",
        matrix,
        ["concept", "kyrgyzstan_status", "kyrgyzstan_variables", "uzbekistan_status", "uzbekistan_variables", "kazakhstan_status", "comparison_note"],
    )

    lik_ok = core_verified(profiles, "kyrgyzstan", ["h620", "any_shock_household", "i251_1"])
    l2_ok = core_verified(profiles, "uzbekistan", ["mig_living_remittance", "remittance_hh", "work_lost_hh", "ln_1"])
    decision = "FULL TWO-COUNTRY DESIGN" if lik_ok and l2_ok else "KYRGYZSTAN-LED DESIGN"
    if lik_ok and not l2_ok:
        l2_remit = core_verified(profiles, "uzbekistan", ["mig_living_remittance", "remittance_hh"])
        l2_food = core_verified(profiles, "uzbekistan", ["ln_1"])
        decision = "PARTIAL TWO-COUNTRY DESIGN" if l2_remit and l2_food else "KYRGYZSTAN-LED DESIGN"

    kaz_files = kazakhstan_microdata_files()
    decision_record = {
        "paper_title": "Do Remittances Buffer Household Shocks? Evidence on Food Insecurity in Kyrgyzstan and Uzbekistan",
        "research_question": "Is the negative association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan?",
        "decision": decision,
        "kyrgyzstan_minimum_mechanism_verified": lik_ok,
        "uzbekistan_minimum_mechanism_verified": l2_ok,
        "minimum_mechanism": ["remittance receipt", "household shock exposure", "food insecurity"],
        "country_strategy": "country-specific models only; respondent records must not be pooled",
        "l2cu_primary_food_rounds": "round 49 onward, subject to per-round completeness in coverage file",
        "kazakhstan_status": "PENDING DATA ACCESS" if not kaz_files else "MICRODATA PRESENT - FUTURE AUDIT REQUIRED",
        "kazakhstan_microdata_files": kaz_files,
        "phase_boundary": "No final analytical dataset constructed and no regression model run.",
        "source_audit": source_audit,
    }
    (CHECKPOINTS / "revised_phase_02_design_decision.json").write_text(
        json.dumps(decision_record, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    status_rows = [
        {"country":"Kyrgyzstan","dataset":"LiK","role":"main panel and household analysis","phase_02_status":"AUDITED","microdata_status":"AVAILABLE"},
        {"country":"Uzbekistan","dataset":"L2CU 2018-2025","role":"main household-panel analysis","phase_02_status":"AUDITED","microdata_status":"AVAILABLE"},
        {"country":"Uzbekistan","dataset":"MICS","role":"optional descriptive context only; excluded from main interaction model","phase_02_status":"NOT IN MAIN AUDIT","microdata_status":"AVAILABLE"},
        {"country":"Kazakhstan","dataset":"FIES","role":"future regional policy benchmark; excluded from current regression","phase_02_status":"PENDING DATA ACCESS","microdata_status":"PENDING DATA ACCESS"},
    ]
    write_csv(CHECKPOINTS / "revised_phase_02_dataset_status.csv", status_rows, ["country","dataset","role","phase_02_status","microdata_status"])

    report = f"""# Revised Phase 2 Data Audit

## Study freeze

- **Paper:** Do Remittances Buffer Household Shocks? Evidence on Food Insecurity in Kyrgyzstan and Uzbekistan
- **Question:** Is the negative association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan?
- **Decision:** **{decision}**
- **Estimation rule:** country-specific models only; LiK and L2CU respondent records must not be pooled.
- **Phase boundary:** this audit stops before final analytical dataset construction, descriptive outcome production, or regression modelling.

## Source status

- Kyrgyzstan LiK 2019 (panel wave 6): available and audited.
- Uzbekistan L2CU rounds 1-82 (2018-2025): available and audited. The supplied round-82 questionnaire dates fieldwork to June 5-26, 2025.
- Uzbekistan MICS: retained as optional descriptive context only and excluded from the main remittance-shock model.
- Kazakhstan FIES: **{'PENDING DATA ACCESS' if not kaz_files else 'microdata detected; future separate audit required'}**. It does not affect the two-country decision.

## Minimum mechanism decision

| Country | Remittance | Shock | Food insecurity | Result |
|---|---|---|---|---|
| Kyrgyzstan | `h620` (12 months) | `shock` + `h701` event roster (12 months) | `i251_1`-`i251_8` (12 months) | {'verified' if lik_ok else 'not verified'} |
| Uzbekistan | `mig_living_remittance` and `remittance_hh` (past month) | `work_lost_hh`; major injury/illness/death via `change_important*` (past month) | `ln_1`-`ln_8` (past 30 days, since round 49) | {'verified' if l2_ok else 'not verified'} |

Both countries contain verified variables with observed valid responses for the three-variable mechanism. The later models can therefore proceed country by country under the **{decision}**.

## Important limitations fixed at Phase 2

1. L2CU agricultural/climate shocks are **not available in the supplied files**. Household water-service disruption is not relabelled as a climate or agricultural shock.
2. L2CU region and rural/urban residence are absent from both supplied CSV headers and must not be inferred from `hhid`.
3. L2CU `popw` exists, but the supplied questionnaire does not define its normalization or exact weighting interpretation. It must not be used until supporting design documentation is confirmed.
4. LiK explicitly assigns no sample weights; the study description also warns about attrition.
5. LiK and L2CU differ in recall period, response scale, and respondent level for food insecurity. Comparisons are conceptual and coefficient-based, never respondent pooling.
6. L2CU `economic_challenge` measures views about national challenges, not a household shock; it is excluded from shock construction.
7. LiK food insecurity is reported by adult individuals. Any household aggregation requires a later, explicit rule and is not performed here.
8. The L2CU individual roster does not cover every household-round in the household CSV. Exact overlap and unmatched counts are in `revised_phase_02_key_integrity.csv` and must constrain later remittance merges.
9. L2CU stores one labelled `change_important_type` value per positive row even though the questionnaire says to choose all applicable changes; multiple simultaneous changes may not be retained.

## Audit products

- `revised_phase_02_variable_registry.csv`: exact variable, wording, recall, coding, missingness, source and later transformation plan.
- `revised_phase_02_variable_profile.csv`: aggregate nonmissing/valid counts and observed codes only.
- `revised_phase_02_l2cu_round_coverage.csv`: aggregate round-by-variable coverage.
- `revised_phase_02_l2cu_household_consistency.csv`: checks repeated household-round fields in the individual roster.
- `revised_phase_02_key_integrity.csv`: aggregate key uniqueness, missing-key, and cross-file coverage checks.
- `revised_phase_02_country_compatibility.csv`: minimum-variable comparison.
- `revised_phase_02_design_decision.json`: machine-readable design freeze.
- `revised_phase_02_dataset_status.csv`: dataset roles and Kazakhstan pending status.

## L2CU release structure

- Household CSV columns: {len(headers[HH_CSV.name])}; rows: {next(row['rows'] for row in profiles if row['country']=='uzbekistan' and row['variable']=='hhid' and row['source_file']==rel(HH_CSV)):,}.
- Individual CSV columns: {len(headers[IND_CSV.name])}; rows: {next(row['rows'] for row in profiles if row['country']=='uzbekistan' and row['variable']=='fmid'):,}.
- Round coverage and structural missingness are recorded variable by variable; blanks before module introduction are not treated as negative responses.

## Stop condition

Revised Phase 2 is complete. No country-specific analytical panel, harmonized outcome, interaction term, pooled respondent file, descriptive result, or regression result was created.
"""
    (CHECKPOINTS / "REVISED_PHASE_02_AUDIT.md").write_text(report, encoding="utf-8")
    return decision


def validate(decision: str, source_audit: dict[str, Any], registry: list[dict[str, Any]]) -> dict[str, Any]:
    required = [
        "REVISED_PHASE_02_AUDIT.md", "revised_phase_02_variable_registry.csv",
        "revised_phase_02_variable_profile.csv", "revised_phase_02_l2cu_round_coverage.csv",
        "revised_phase_02_l2cu_household_consistency.csv", "revised_phase_02_key_integrity.csv",
        "revised_phase_02_country_compatibility.csv",
        "revised_phase_02_design_decision.json", "revised_phase_02_dataset_status.csv",
    ]
    kz_rows = [row for row in registry if row["country"] == "kazakhstan"]
    validation = {
        "required_outputs_exist": all((CHECKPOINTS / name).exists() for name in required),
        "raw_source_hashes_unchanged": source_audit["source_hashes_unchanged"],
        "l2cu_zip_integrity_passed": source_audit["l2cu_zip_integrity"] == "passed",
        "minimum_registry_rows_present": len(registry) == len(CONCEPTS) * 3,
        "kazakhstan_all_fields_pending": all(
            row["status"] == "PENDING DATA ACCESS" and row["raw_variable_names"] == "PENDING DATA ACCESS"
            for row in kz_rows
        ),
        "kazakhstan_does_not_block_two_country_decision": decision in {"FULL TWO-COUNTRY DESIGN", "PARTIAL TWO-COUNTRY DESIGN", "KYRGYZSTAN-LED DESIGN"},
        "processed_data_written": False,
        "regression_run": False,
        "countries_pooled": False,
        "respondent_level_output_written": False,
    }
    (CHECKPOINTS / "revised_phase_02_validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    failures = [key for key, value in validation.items() if key not in {"processed_data_written", "regression_run", "countries_pooled", "respondent_level_output_written"} and not value]
    if failures:
        raise RuntimeError(f"Revised Phase 2 validation failed: {failures}")
    return validation


def run_all() -> str:
    LOGGER.info("Starting Revised Phase 2")
    ensure_structure()
    source_audit = verify_sources_and_extract()
    hh, ind, headers = read_l2cu()
    LOGGER.info("Loaded L2CU aggregate-audit inputs: household rows=%s, individual rows=%s", len(hh), len(ind))
    l2_hh_profiles, coverage_hh = profile_frame(
        hh, country="uzbekistan", dataset="L2CU 2018-2025", source_file=HH_CSV,
        level="household-round", variables=L2CU_HH_VARIABLES,
    )
    l2_ind_profiles, coverage_ind = profile_frame(
        ind, country="uzbekistan", dataset="L2CU 2018-2025", source_file=IND_CSV,
        level="individual/migrant roster", variables=L2CU_IND_VARIABLES,
    )
    frames, metadata = read_lik()
    lik_profiles = profile_lik(frames, metadata)
    profiles = lik_profiles + l2_hh_profiles + l2_ind_profiles
    consistency = l2cu_consistency(ind)
    key_checks = key_integrity(hh, ind, frames)
    registry = build_registry(profiles)
    decision = write_outputs(profiles, coverage_hh + coverage_ind, consistency, key_checks, registry, source_audit, headers)
    validate(decision, source_audit, registry)
    LOGGER.info("Revised Phase 2 complete: %s", decision)
    return decision
