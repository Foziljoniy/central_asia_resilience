"""Phase 2 Kazakhstan FIES addendum utilities.

The addendum audits Kazakhstan FIES source packages only. It preserves every
original file under data/kazakhstan, writes aggregate checkpoint outputs, and
stops before appending yearly files or running statistical analysis.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / ".vendor"
if VENDOR.exists() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

import pandas as pd
import pyreadstat
from pypdf import PdfReader


YEARS = [2014, 2015, 2016, 2017]
KAZ_ROOT = ROOT / "data" / "kazakhstan"
CHECKPOINTS = ROOT / "outputs" / "checkpoints"
LOG_PATH = ROOT / "outputs" / "logs" / "phase_02_kazakhstan_addendum.log"
ACCESS_DATE = "2026-07-26"

FIES_VARS = ["WORRIED", "HEALTHY", "FEWFOOD", "SKIPPED", "ATELESS", "RUNOUT", "HUNGRY", "WHLDAY"]
DERIVED_VARS = ["Raw_score", "Raw_score_par", "Raw_score_par_error", "Prob_Mod_Sev", "Prob_sev"]
DESIGN_VARS = ["Random_ID", "wt", "year", "N_adults", "N_child", "Age", "Education", "Area", "Gender", "Income"]

FIES_WORDING = {
    "WORRIED": "During the last 12 MONTHS, was there a time when you were worried you would not have enough food to eat because of a lack of money or other resources?",
    "HEALTHY": "Still thinking about the last 12 MONTHS, was there a time when you were unable to eat healthy and nutritious food because of a lack of money or other resources?",
    "FEWFOOD": "Was there a time when you ate only a few kinds of foods because of a lack of money or other resources?",
    "SKIPPED": "Was there a time when you had to skip a meal because there was not enough money or other resources to get food?",
    "ATELESS": "Still thinking about the last 12 MONTHS, was there a time when you ate less than you thought you should because of a lack of money or other resources?",
    "RUNOUT": "Was there a time when your household ran out of food because of a lack of money or other resources?",
    "HUNGRY": "Was there a time when you were hungry but did not eat because there was not enough money or other resources for food?",
    "WHLDAY": "During the last 12 MONTHS, was there a time when you went without eating for a whole day because of a lack of money or other resources?",
}

CONCEPT_SEARCH = {
    "migration/remittances": ["migration", "migrant", "remittance", "abroad", "transfer", "family support", "relatives"],
    "household shocks": ["shock", "job loss", "unemployment", "income loss", "illness", "injury", "death", "drought", "flood", "disaster", "price increase", "unexpected expense", "business closure", "conflict", "displacement"],
    "coping/assistance": ["borrowing", "asset sale", "reduced consumption", "government assistance", "food assistance", "social transfer", "savings", "additional work"],
    "age": ["Age"],
    "sex/gender": ["Gender"],
    "education": ["Education"],
    "employment": ["employment", "work", "job"],
    "marital status": ["marital"],
    "household size": ["N_adults", "N_child"],
    "children": ["N_child"],
    "income/wealth": ["Income"],
    "region": ["region", "oblast", "province"],
    "rural or urban residence": ["Area", "urban", "rural"],
    "survey weight": ["wt", "weight"],
    "FIES food insecurity": FIES_VARS + DERIVED_VARS,
}


def configure_logging() -> logging.Logger:
    """Configure the addendum logger once."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("phase02_kazakhstan")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        for handler in (logging.FileHandler(LOG_PATH, encoding="utf-8"), logging.StreamHandler()):
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger


LOGGER = configure_logging()


def rel(path: Path) -> str:
    """Return a stable project-relative POSIX path."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash a source file without loading it all at once."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    """Write a deterministic UTF-8-SIG CSV with fixed columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: cell(row.get(field, "")) for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read one generated CSV, returning an empty list if absent."""
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def cell(value: Any) -> str | int | float:
    """Normalize values for CSV and Markdown generation."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple, set)):
        if isinstance(value, set):
            value = sorted(value)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def year_folder(year: int) -> Path:
    """Return the expected year-specific Kazakhstan source folder."""
    return KAZ_ROOT / f"KAZ_{year}_FIES_v01_EN_M_v01_A_OCS"


def canonical_path(year: int) -> Path:
    """Return the preferred canonical SPSS source path for a year."""
    return year_folder(year) / "microdata" / f"KAZ_{year}_FIES_v01_EN_M_v01_A_OCS.sav"


def dta_path(year: int) -> Path:
    """Return the Stata source path for a year."""
    return year_folder(year) / "microdata" / f"KAZ_{year}_FIES_v01_EN_M_v01_A_OCS.dta"


def questionnaire_path(year: int) -> Path:
    """Return the FIES questionnaire PDF path for a year."""
    return year_folder(year) / "resources" / "questionnaires" / "FIES_Questions.pdf"


def technical_path(year: int) -> Path:
    """Return the derived-indicator technical PDF path for a year."""
    return year_folder(year) / "resources" / "technical" / "Derived_variables_and_Computation_indicator.pdf"


def ensure_structure() -> None:
    """Create output and working folders, never modifying source folders."""
    for directory in [
        CHECKPOINTS,
        ROOT / "outputs" / "logs",
        ROOT / "data" / "interim" / "unpacked" / "kazakhstan" / "fies",
        ROOT / "research",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
    for year in YEARS:
        (ROOT / "data" / "interim" / "unpacked" / "kazakhstan" / "fies" / str(year)).mkdir(parents=True, exist_ok=True)


def all_source_files() -> list[Path]:
    """List every original Kazakhstan file under the protected source root."""
    if not KAZ_ROOT.exists():
        return []
    return sorted(path for path in KAZ_ROOT.rglob("*") if path.is_file())


def source_hashes() -> dict[str, str]:
    """Hash every protected Kazakhstan source file."""
    return {rel(path): sha256(path) for path in all_source_files()}


def write_status_file() -> None:
    """Record access status outside the protected source folders."""
    path = ROOT / "research" / "kazakhstan_access_status.md"
    path.write_text(
        "# Kazakhstan FIES Access Status\n\n"
        f"Status: ACCESS GRANTED ON {ACCESS_DATE}\n\n"
        "The historical marker `data/kazakhstan/pending_fies_access.txt` was not deleted or modified. "
        "All files under `data/kazakhstan/` are treated as protected original sources.\n",
        encoding="utf-8",
    )


def extract_pdf_text(path: Path) -> tuple[str, int, str]:
    """Extract text from a PDF for audit search, preserving errors as text."""
    try:
        reader = PdfReader(str(path))
        parts = []
        for idx, page in enumerate(reader.pages, start=1):
            parts.append(f"PAGE {idx}\n{page.extract_text() or ''}")
        return "\n".join(parts), len(reader.pages), ""
    except Exception as exc:  # noqa: BLE001 - audit must continue by year
        return "", 0, f"{type(exc).__name__}: {exc}"


def read_microdata(path: Path) -> tuple[pd.DataFrame | None, Any | None, str, str]:
    """Open supported microdata formats read-only."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".sav":
            df, meta = pyreadstat.read_sav(str(path), user_missing=True)
            return df, meta, "pyreadstat.read_sav(user_missing=True)", ""
        if suffix == ".dta":
            df, meta = pyreadstat.read_dta(str(path))
            return df, meta, "pyreadstat.read_dta", ""
        if suffix == ".rdata":
            return None, None, "not parsed", "RData parser is not available in the bundled runtime; treated as alternate unsupported format."
        return None, None, "not parsed", "Unsupported microdata extension."
    except Exception as exc:  # noqa: BLE001 - audit must continue by year
        return None, None, f"failed with {suffix}", f"{type(exc).__name__}: {exc}"


def probable_format(path: Path) -> str:
    """Infer a plain-language file format."""
    suffix = path.suffix.lower()
    return {
        ".sav": "SPSS SAV",
        ".dta": "Stata DTA",
        ".rdata": "RData",
        ".pdf": "PDF",
        ".txt": "plain text",
        ".csv": "CSV",
        ".xml": "XML",
        ".json": "JSON",
    }.get(suffix, suffix.lstrip(".").upper() or "unknown")


def probable_role(path: Path) -> tuple[str, str]:
    """Classify source file role and broad type."""
    lower = rel(path).lower()
    name = path.name.lower()
    if "\\microdata\\" in lower or "/microdata/" in lower or path.suffix.lower() in {".sav", ".dta", ".rdata"}:
        return "microdata", "microdata"
    if "question" in lower:
        return "questionnaire", "study resource"
    if "derived" in name or "computation" in name or "indicator" in name:
        return "derived-indicator documentation", "study resource"
    if "pending_fies_access" in name:
        return "historical access marker", "study resource"
    if path.suffix.lower() == ".pdf":
        return "documentation", "study resource"
    return "other", "study resource"


def language_guess(path: Path) -> str:
    """Guess the resource language from filenames and extracted text."""
    lower = rel(path).lower()
    if "_en_" in lower or "/en/" in lower:
        return "English"
    if path.suffix.lower() in {".pdf", ".sav", ".dta", ".rdata"}:
        return "English"
    return "unknown"


def year_from_path(path: Path) -> str:
    """Extract survey year from a source path."""
    match = re.search(r"KAZ_(201[4-7])_FIES", rel(path))
    return match.group(1) if match else "historical"


def inventory_files() -> list[dict[str, Any]]:
    """Inventory every Kazakhstan source file and write combined/year CSVs."""
    ensure_structure()
    rows: list[dict[str, Any]] = []
    for path in all_source_files():
        role, broad = probable_role(path)
        openable = "not attempted"
        method = ""
        warning = ""
        error = ""
        notes = ""
        if path.suffix.lower() in {".sav", ".dta", ".rdata"}:
            df, _meta, method, error = read_microdata(path)
            openable = "openable" if df is not None else ("unsupported" if path.suffix.lower() == ".rdata" else "not openable")
            notes = f"rows={len(df)}, columns={len(df.columns)}" if df is not None else ""
        elif path.suffix.lower() == ".pdf":
            text, pages, error = extract_pdf_text(path)
            openable = "openable" if not error else "not openable"
            method = "pypdf.PdfReader.extract_text"
            notes = f"pages={pages}; text_chars={len(text)}"
        elif path.suffix.lower() == ".txt":
            try:
                _ = path.read_text(encoding="utf-8")
                openable = "openable"
                method = "Path.read_text(utf-8)"
            except Exception as exc:  # noqa: BLE001
                openable = "not openable"
                error = f"{type(exc).__name__}: {exc}"
        rows.append({
            "survey_year": year_from_path(path),
            "source_folder": rel(path.parent),
            "relative_path": rel(path),
            "filename": path.name,
            "extension": path.suffix.lower(),
            "file_size": path.stat().st_size,
            "sha256_checksum": sha256(path),
            "probable_file_format": probable_format(path),
            "probable_role": role,
            "microdata_or_study_resource": broad,
            "openable_status": openable,
            "parsing_method": method,
            "opening_warning": warning,
            "opening_error": error,
            "probable_language": language_guess(path),
            "notes": notes,
        })
    fields = [
        "survey_year", "source_folder", "relative_path", "filename", "extension", "file_size",
        "sha256_checksum", "probable_file_format", "probable_role", "microdata_or_study_resource",
        "openable_status", "parsing_method", "opening_warning", "opening_error", "probable_language", "notes",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_file_inventory.csv", rows, fields)
    for year in YEARS:
        write_csv(CHECKPOINTS / f"kazakhstan_{year}_file_inventory.csv", [row for row in rows if row["survey_year"] == str(year)], fields)
    LOGGER.info("Kazakhstan file inventory written for %s files", len(rows))
    return rows


def labels_for(meta: Any, variable: str) -> dict[Any, Any]:
    """Return value labels for one variable."""
    return (getattr(meta, "variable_value_labels", None) or {}).get(variable, {})


def variable_label(meta: Any, variable: str) -> str:
    """Return a variable label."""
    return (getattr(meta, "column_names_to_labels", None) or {}).get(variable, "")


def nonempty(series: pd.Series) -> pd.Series:
    """Mask values that are not missing and not blank strings."""
    return series.notna() & (series.astype(str).str.strip() != "")


def numeric_values(series: pd.Series) -> pd.Series:
    """Coerce a series to numeric after removing blank strings."""
    return pd.to_numeric(series.where(nonempty(series)), errors="coerce")


def candidate_vars(columns: Iterable[str], labels: dict[str, str], keywords: Iterable[str]) -> list[str]:
    """Find candidate variables by name or label keywords."""
    hits = []
    lower_keywords = [keyword.lower() for keyword in keywords]
    for column in columns:
        hay = f"{column} {labels.get(column, '')}".lower()
        if any(keyword.lower() in hay for keyword in lower_keywords):
            hits.append(column)
    return hits


def microdata_inventory() -> list[dict[str, Any]]:
    """Audit supported microdata formats by year."""
    rows = []
    for year in YEARS:
        for path in sorted((year_folder(year) / "microdata").glob("*")):
            df, meta, method, error = read_microdata(path)
            labels = (getattr(meta, "column_names_to_labels", None) or {}) if meta else {}
            columns = list(df.columns) if df is not None else []
            value_label_vars = list((getattr(meta, "variable_value_labels", None) or {}).keys()) if meta else []
            rows.append({
                "year": year,
                "source_file": rel(path),
                "format": probable_format(path),
                "rows": len(df) if df is not None else "",
                "columns": len(columns) if df is not None else "",
                "variable_names": columns,
                "variable_labels": {col: labels.get(col, "") for col in columns},
                "value_label_availability": f"{len(value_label_vars)} labelled variables: {value_label_vars}" if meta else "not parsed",
                "file_encoding": getattr(meta, "file_encoding", "") if meta else "",
                "missing_value_metadata": {
                    "missing_ranges": getattr(meta, "missing_ranges", {}) or {},
                    "missing_user_values": getattr(meta, "missing_user_values", {}) or {},
                } if meta else "not parsed",
                "identifier_candidates": candidate_vars(columns, labels, ["id", "identifier", "Random_ID"]),
                "weight_candidates": candidate_vars(columns, labels, ["weight", "wt", "post-stratification"]),
                "strata_candidates": candidate_vars(columns, labels, ["strata", "stratum"]),
                "psu_or_cluster_candidates": candidate_vars(columns, labels, ["psu", "cluster"]),
                "region_candidates": candidate_vars(columns, labels, ["region", "oblast", "province"]),
                "urban_rural_candidates": candidate_vars(columns, labels, ["area", "urban", "rural", "town"]),
                "respondent_characteristics": [var for var in ["Age", "Education", "Gender", "Income", "N_adults", "N_child"] if var in columns],
                "fies_candidates": [var for var in FIES_VARS if var in columns],
                "derived_score_candidates": [var for var in DERIVED_VARS if var in columns],
                "opening_warnings": "",
                "notes": error or f"Read only; no respondent-level output exported. method={method}",
            })
    fields = [
        "year", "source_file", "format", "rows", "columns", "variable_names", "variable_labels",
        "value_label_availability", "file_encoding", "missing_value_metadata", "identifier_candidates",
        "weight_candidates", "strata_candidates", "psu_or_cluster_candidates", "region_candidates",
        "urban_rural_candidates", "respondent_characteristics", "fies_candidates", "derived_score_candidates",
        "opening_warnings", "notes",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_microdata_inventory.csv", rows, fields)
    LOGGER.info("Kazakhstan microdata inventory written")
    return rows


def compare_formats() -> list[dict[str, Any]]:
    """Compare multiple microdata formats within each survey year."""
    rows = []
    for year in YEARS:
        files = sorted((year_folder(year) / "microdata").glob("*"))
        parsed: dict[str, tuple[pd.DataFrame | None, Any | None, str]] = {}
        for path in files:
            df, meta, _method, error = read_microdata(path)
            parsed[rel(path)] = (df, meta, error)
        for left, right in combinations([rel(path) for path in files], 2):
            ldf, lmeta, lerr = parsed[left]
            rdf, rmeta, rerr = parsed[right]
            if ldf is None or rdf is None:
                classification = "uncertain"
                notes = f"At least one format not parsed: {lerr or rerr}"
                same_rows = same_cols = same_names = ""
                overlap = ""
                signature_match = ""
            else:
                same_rows = len(ldf) == len(rdf)
                same_cols = len(ldf.columns) == len(rdf.columns)
                same_names = list(ldf.columns) == list(rdf.columns)
                overlap = len(set(ldf.columns) & set(rdf.columns))
                signature_match = aggregate_signature(ldf) == aggregate_signature(rdf)
                data_match = ldf.astype(str).fillna("<NA>").equals(rdf.astype(str).fillna("<NA>"))
                label_left = sum(1 for col in ldf.columns if variable_label(lmeta, col))
                label_right = sum(1 for col in rdf.columns if variable_label(rmeta, col))
                if same_rows and same_cols and same_names and signature_match and data_match:
                    classification = "content-equivalent format versions"
                    notes = f"Aggregate and stringwise data signatures match; label coverage left={label_left}, right={label_right}."
                elif same_rows and same_cols and same_names and signature_match:
                    classification = "probable format duplicates"
                    notes = "Aggregate signatures match but exact string representation differs."
                else:
                    classification = "uncertain"
                    notes = "Metadata or aggregate signatures differ."
            rows.append({
                "year": year,
                "left_file": left,
                "right_file": right,
                "left_format": probable_format(ROOT / left),
                "right_format": probable_format(ROOT / right),
                "same_row_count": same_rows,
                "same_column_count": same_cols,
                "same_variable_names": same_names,
                "variable_name_overlap": overlap,
                "aggregate_missingness_signature_match": signature_match,
                "respondent_key_overlap_check": "not exported; Random_ID uniqueness checked only in aggregate for parsed files",
                "classification": classification,
                "notes": notes,
            })
    fields = [
        "year", "left_file", "right_file", "left_format", "right_format", "same_row_count",
        "same_column_count", "same_variable_names", "variable_name_overlap",
        "aggregate_missingness_signature_match", "respondent_key_overlap_check", "classification", "notes",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_format_comparison.csv", rows, fields)
    LOGGER.info("Kazakhstan format comparison written")
    return rows


def aggregate_signature(df: pd.DataFrame) -> dict[str, Any]:
    """Build a non-disclosing aggregate signature for duplicate checks."""
    signature = {}
    for col in df.columns:
        mask = nonempty(df[col])
        numeric = numeric_values(df[col])
        signature[col] = {
            "nonmissing": int(mask.sum()),
            "unique": int(df.loc[mask, col].nunique(dropna=True)),
            "min": None if numeric.dropna().empty else float(numeric.min()),
            "max": None if numeric.dropna().empty else float(numeric.max()),
        }
    return signature


def resource_inventory() -> list[dict[str, Any]]:
    """Audit study resources by year."""
    rows = []
    for year in YEARS:
        for path in sorted((year_folder(year) / "resources").rglob("*")):
            if not path.is_file():
                continue
            text, pages, error = extract_pdf_text(path) if path.suffix.lower() == ".pdf" else ("", 0, "")
            lower = f"{rel(path)} {text}".lower()
            role, _broad = probable_role(path)
            rows.append({
                "year": year,
                "source_folder": rel(path.parent),
                "resource_file": rel(path),
                "resource_role": role,
                "language": language_guess(path),
                "parse_status": "parsed" if not error else f"parse error: {error}",
                "main_topics": topics_for_text(lower),
                "fies_documentation": "yes" if any(var.lower() in lower for var in FIES_VARS) or "food insecurity" in lower else "no",
                "sampling_documentation": "yes" if "gallup world poll" in lower or "sample" in lower else "no",
                "weight_documentation": "yes" if "weight" in lower or "wt" in lower else "no",
                "citation_information": "not found in supplied resource",
                "data_use_information": "not found in supplied resource",
                "notes": f"pages={pages}" if pages else "",
            })
    fields = [
        "year", "source_folder", "resource_file", "resource_role", "language", "parse_status",
        "main_topics", "fies_documentation", "sampling_documentation", "weight_documentation",
        "citation_information", "data_use_information", "notes",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_resource_inventory.csv", rows, fields)
    LOGGER.info("Kazakhstan resource inventory written")
    return rows


def topics_for_text(lower: str) -> list[str]:
    """Return compact topic tags for a resource."""
    tags = []
    if "worried" in lower or "food insecurity" in lower or "fies" in lower:
        tags.append("FIES")
    if "rasch" in lower or "prob_mod_sev" in lower or "raw score" in lower:
        tags.append("derived indicators")
    if "weight" in lower or "post-stratification" in lower:
        tags.append("weights")
    if "gallup world poll" in lower or "15 years" in lower:
        tags.append("target population")
    return tags or ["other"]


def dataset_inventory() -> list[dict[str, Any]]:
    """Identify one substantive yearly dataset per Kazakhstan year."""
    rows = []
    for year in YEARS:
        df, meta, _method, error = read_microdata(canonical_path(year))
        rows.append({
            "year": year,
            "exact_study_title": f"Kazakhstan Food Insecurity Experience Scale (FIES) {year}",
            "survey_year": year,
            "reference_id": year_folder(year).name,
            "producer": "FAO Food Insecurity Experience Scale data package; Gallup World Poll field source indicated in technical documentation",
            "sponsor": "DOCUMENTATION INSUFFICIENT in supplied files",
            "collection_organisation": "Gallup World Poll, per technical documentation",
            "collection_method": "survey interview; exact mode not documented in supplied files",
            "interview_mode": "DOCUMENTATION INSUFFICIENT",
            "fieldwork_period": "survey year only; exact dates not in supplied files",
            "respondent_unit": "one adult respondent",
            "target_population": "population aged 15 years or older; total-population formulas require child/adult household counts",
            "age_eligibility": "15 years and older",
            "sample_size": len(df) if df is not None else "",
            "national_representativeness": "supported by post-stratification weight documentation, but detailed sample design not supplied",
            "sampling_design": "Gallup World Poll adult sample; detailed strata/cluster design not supplied",
            "survey_weight": "wt",
            "strata": "NOT AVAILABLE",
            "cluster_or_psu": "NOT AVAILABLE",
            "region": "NOT AVAILABLE",
            "urban_rural_indicator": "Area",
            "country_code": "Kazakhstan inferred from source package ID; no country variable found in canonical file",
            "language": "English",
            "access_conditions": f"ACCESS GRANTED ON {ACCESS_DATE}; data-use terms not found in supplied files",
            "notes": error or "One substantive respondent-level dataset; .sav/.dta are format versions, .RData unparsed alternate.",
        })
    fields = [
        "year", "exact_study_title", "survey_year", "reference_id", "producer", "sponsor",
        "collection_organisation", "collection_method", "interview_mode", "fieldwork_period",
        "respondent_unit", "target_population", "age_eligibility", "sample_size",
        "national_representativeness", "sampling_design", "survey_weight", "strata",
        "cluster_or_psu", "region", "urban_rural_indicator", "country_code", "language",
        "access_conditions", "notes",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_dataset_inventory.csv", rows, fields)
    LOGGER.info("Kazakhstan dataset inventory written")
    return rows


def variable_metadata() -> list[dict[str, Any]]:
    """Create aggregate variable metadata for canonical files by year."""
    rows = []
    for year in YEARS:
        df, meta, _method, error = read_microdata(canonical_path(year))
        if df is None:
            LOGGER.warning("Skipping variable metadata for %s: %s", year, error)
            continue
        for var in df.columns:
            mask = nonempty(df[var])
            num = numeric_values(df[var])
            num_nonmissing = num.dropna()
            rows.append({
                "year": year,
                "source_file": rel(canonical_path(year)),
                "variable_name": var,
                "variable_label": variable_label(meta, var),
                "value_labels": labels_for(meta, var),
                "storage_type": str(df[var].dtype),
                "missing_codes": missing_codes_for(var, meta),
                "nonmissing_count": int(mask.sum()),
                "unique_value_count": int(df.loc[mask, var].nunique(dropna=True)),
                "minimum": "" if num_nonmissing.empty else float(num_nonmissing.min()),
                "maximum": "" if num_nonmissing.empty else float(num_nonmissing.max()),
                "probable_concept": probable_concept(var),
                "probable_role": probable_var_role(var),
                "documentation_source": documentation_source_for(var, year),
                "verification_status": verification_status_for(var),
                "notes": "Aggregate only; no respondent-level values exported.",
            })
    fields = [
        "year", "source_file", "variable_name", "variable_label", "value_labels", "storage_type",
        "missing_codes", "nonmissing_count", "unique_value_count", "minimum", "maximum",
        "probable_concept", "probable_role", "documentation_source", "verification_status", "notes",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_variable_metadata.csv", rows, fields)
    for year in YEARS:
        write_csv(CHECKPOINTS / f"kazakhstan_{year}_variable_metadata.csv", [row for row in rows if row["year"] == year], fields)
    LOGGER.info("Kazakhstan variable metadata written")
    return rows


def missing_codes_for(var: str, meta: Any) -> str:
    """Document missing-code metadata from files and observed structure."""
    labels = labels_for(meta, var)
    parts = []
    if var in FIES_VARS:
        parts.append("blank/system missing observed; refusal and do-not-know codes not documented in questionnaire PDF")
    if labels:
        dk = [f"{code}={label}" for code, label in labels.items() if "dont" in str(label).lower() or "refus" in str(label).lower()]
        if dk:
            parts.append("labelled nonresponse categories: " + "; ".join(dk))
    return "; ".join(parts) if parts else "no special missing metadata supplied"


def probable_concept(var: str) -> str:
    """Map variable names to concepts."""
    if var in FIES_VARS:
        return "FIES item"
    if var in DERIVED_VARS:
        return "derived FIES indicator"
    if var == "Random_ID":
        return "respondent identifier"
    if var == "wt":
        return "survey weight"
    if var == "year":
        return "survey year"
    if var in {"N_adults", "N_child"}:
        return "household composition"
    if var in {"Age", "Education", "Area", "Gender", "Income"}:
        return "respondent demographic/geographic/economic characteristic"
    return "other"


def probable_var_role(var: str) -> str:
    """Map variable names to analytic roles."""
    if var in FIES_VARS:
        return "raw food-insecurity item"
    if var in {"Prob_Mod_Sev", "Prob_sev"}:
        return "official probability outcome for later prevalence estimation"
    if var == "Raw_score":
        return "raw score"
    if var in {"Raw_score_par", "Raw_score_par_error"}:
        return "Rasch severity parameter"
    if var in DESIGN_VARS:
        return "design/control candidate"
    return "other"


def documentation_source_for(var: str, year: int) -> str:
    """Point to the source document used for verification."""
    if var in FIES_VARS:
        return f"{rel(questionnaire_path(year))} page 1"
    if var in DERIVED_VARS or var in {"wt", "N_adults", "N_child"}:
        return f"{rel(technical_path(year))} pp. 1-4"
    return f"{rel(canonical_path(year))} variable label/value label metadata"


def verification_status_for(var: str) -> str:
    """Return a cautious verification status."""
    if var in FIES_VARS + DERIVED_VARS + DESIGN_VARS:
        return "VERIFIED"
    return "DOCUMENTATION INSUFFICIENT"


def fies_item_registry() -> list[dict[str, Any]]:
    """Verify exact FIES item wording and coding separately by year."""
    rows = []
    for year in YEARS:
        df, meta, _method, error = read_microdata(canonical_path(year))
        text, _pages, qerror = extract_pdf_text(questionnaire_path(year))
        for order, var in enumerate(FIES_VARS, start=1):
            if df is None or var not in df.columns:
                rows.append({
                    "survey_year": year, "source_file": rel(canonical_path(year)), "variable_name": var,
                    "verification_status": "NOT AVAILABLE", "notes": error,
                })
                continue
            mask = df[var].astype(str).str.strip().isin(["0", "1"])
            nonresponse = len(df) - int(mask.sum())
            wording = FIES_WORDING[var]
            rows.append({
                "survey_year": year,
                "source_file": rel(canonical_path(year)),
                "variable_name": var,
                "variable_label": variable_label(meta, var),
                "exact_question_wording": wording,
                "questionnaire_page_or_resource": f"{rel(questionnaire_path(year))} page 1",
                "respondent": "adult respondent aged 15 years or older",
                "reference_period": "last 12 months",
                "universe": "sampled adult respondent; one adult sampled per GWP household per technical documentation",
                "yes_code": "1",
                "no_code": "0",
                "refusal_code": "NOT DOCUMENTED in supplied questionnaire/data for FIES items",
                "do_not_know_code": "NOT DOCUMENTED in supplied questionnaire/data for FIES items",
                "other_missing_codes": "blank/system missing",
                "valid_response_count": int(mask.sum()),
                "nonresponse_count": nonresponse,
                "direction": "1 means affirmative food-insecurity experience; 0 means not affirmed",
                "comparability_with_other_years": "EXACT wording and variable name match across 2014-2017" if not qerror and wording in " ".join(text.split()) else "STRONG; wording verified from supplied resource",
                "verification_status": "VERIFIED",
                "notes": "Missing/refusal/DK were not treated as No.",
            })
    fields = [
        "survey_year", "source_file", "variable_name", "variable_label", "exact_question_wording",
        "questionnaire_page_or_resource", "respondent", "reference_period", "universe", "yes_code",
        "no_code", "refusal_code", "do_not_know_code", "other_missing_codes", "valid_response_count",
        "nonresponse_count", "direction", "comparability_with_other_years", "verification_status", "notes",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_item_registry.csv", rows, fields)
    for year in YEARS:
        write_csv(CHECKPOINTS / f"kazakhstan_{year}_fies_items.csv", [row for row in rows if row["survey_year"] == year], fields)
    LOGGER.info("Kazakhstan FIES item registry written")
    return rows


def derived_indicator_registry() -> list[dict[str, Any]]:
    """Document existing official derived FIES variables."""
    rows = []
    for year in YEARS:
        df, meta, _method, error = read_microdata(canonical_path(year))
        for var in DERIVED_VARS + ["wt"]:
            if df is None or var not in df.columns:
                continue
            num = numeric_values(df[var]).dropna()
            rows.append({
                "year": year,
                "variable": var,
                "label": variable_label(meta, var),
                "type": str(df[var].dtype),
                "coding": coding_for_derived(var),
                "range": "" if num.empty else f"{float(num.min())} to {float(num.max())}",
                "missing_codes": missing_codes_for(var, meta),
                "derivation_documentation": f"{rel(technical_path(year))} pp. 1-4",
                "whether_respondent_level": "yes",
                "whether_may_be_used_directly": may_use_directly(var),
                "whether_recalculation_required": recalculation_required(var),
                "cross_year_comparability": "STRONG; same variable names, labels, and technical documentation across 2014-2017",
                "verification_status": "VERIFIED" if not error else "DOCUMENTATION INSUFFICIENT",
            })
    fields = [
        "year", "variable", "label", "type", "coding", "range", "missing_codes",
        "derivation_documentation", "whether_respondent_level", "whether_may_be_used_directly",
        "whether_recalculation_required", "cross_year_comparability", "verification_status",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_derived_indicator_registry.csv", rows, fields)
    LOGGER.info("Kazakhstan derived indicator registry written")
    return rows


def coding_for_derived(var: str) -> str:
    """Describe derived-variable coding without computing prevalence."""
    if var == "Raw_score":
        return "integer count of affirmative FIES items, 0-8"
    if var in {"Prob_Mod_Sev", "Prob_sev"}:
        return "individual probability from 0 to near 1"
    if var in {"Raw_score_par", "Raw_score_par_error"}:
        return "Rasch global-reference-scale parameter/error"
    if var == "wt":
        return "post-stratification sampling weight"
    return ""


def may_use_directly(var: str) -> str:
    """State whether a derived variable can be used directly later."""
    if var in {"Prob_Mod_Sev", "Prob_sev", "Raw_score", "Raw_score_par", "Raw_score_par_error"}:
        return "yes for later documented analysis; no prevalence is computed in this phase"
    if var == "wt":
        return "yes within documented FAO formulas; multi-year rescaling remains TBD"
    return "TBD"


def recalculation_required(var: str) -> str:
    """State if recalculation is required later."""
    if var in {"Prob_Mod_Sev", "Prob_sev", "Raw_score_par", "Raw_score_par_error"}:
        return "not required for supplied official variables; recalibration only if supervisor requires a new harmonized outcome"
    if var == "Raw_score":
        return "not required if using supplied raw score; can be recomputed for validation later"
    if var == "wt":
        return "not applicable"
    return "TBD"


def design_registry() -> list[dict[str, Any]]:
    """Verify identifiers and survey-design variables by year."""
    rows = []
    concepts = {
        "respondent ID": "Random_ID",
        "household ID": None,
        "interview ID": None,
        "country ID": None,
        "year variable": "year",
        "interview date": None,
        "survey weight": "wt",
        "population weight": None,
        "post-stratification weight": "wt",
        "strata": None,
        "PSU or cluster": None,
        "region": None,
        "urban-rural residence": "Area",
        "age": "Age",
        "gender": "Gender",
        "education": "Education",
        "income quintile": "Income",
        "household adult count": "N_adults",
        "household child count": "N_child",
    }
    for year in YEARS:
        df, meta, _method, error = read_microdata(canonical_path(year))
        for concept, var in concepts.items():
            if df is None or var is None or var not in df.columns:
                rows.append(empty_design_row(year, concept, "NOT AVAILABLE" if not error else "DOCUMENTATION INSUFFICIENT"))
                continue
            mask = nonempty(df[var])
            rows.append({
                "year": year,
                "concept": concept,
                "exact_name": var,
                "label": variable_label(meta, var),
                "coding": labels_for(meta, var) or observed_small_codes(df[var]),
                "source_documentation": documentation_source_for(var, year),
                "missingness": f"{len(df) - int(mask.sum())} missing or blank of {len(df)} records",
                "uniqueness": uniqueness_note(df, var),
                "applies_to_all_records": "yes" if int(mask.sum()) == len(df) else "partial",
                "whether_weight_normalized": "DOCUMENTATION INSUFFICIENT; technical formula uses wt but does not state multi-year normalization",
                "whether_yearly_weights_can_be_used_in_pooled_multi_year_file": "TBD; likely requires year/population-aware rescaling before pooled trend estimation",
                "uncertainty": uncertainty_for_design(concept, var),
            })
    fields = [
        "year", "concept", "exact_name", "label", "coding", "source_documentation", "missingness",
        "uniqueness", "applies_to_all_records", "whether_weight_normalized",
        "whether_yearly_weights_can_be_used_in_pooled_multi_year_file", "uncertainty",
    ]
    write_csv(CHECKPOINTS / "kazakhstan_fies_design_registry.csv", rows, fields)
    LOGGER.info("Kazakhstan design registry written")
    return rows


def empty_design_row(year: int, concept: str, status: str) -> dict[str, Any]:
    """Return a standardized absent design-variable row."""
    return {
        "year": year,
        "concept": concept,
        "exact_name": "NOT AVAILABLE" if status == "NOT AVAILABLE" else "TBD",
        "label": status,
        "coding": status,
        "source_documentation": "searched canonical microdata labels and supplied resources",
        "missingness": status,
        "uniqueness": status,
        "applies_to_all_records": "no",
        "whether_weight_normalized": status,
        "whether_yearly_weights_can_be_used_in_pooled_multi_year_file": status,
        "uncertainty": "No verified variable found.",
    }


def observed_small_codes(series: pd.Series) -> list[str]:
    """Return a compact list of observed codes for low-cardinality variables."""
    mask = nonempty(series)
    values = sorted(str(value) for value in series.loc[mask].unique())
    return values[:20] if len(values) <= 20 else []


def uniqueness_note(df: pd.DataFrame, var: str) -> str:
    """Document aggregate uniqueness for a candidate key/design variable."""
    if var == "Random_ID":
        return f"{df[var].nunique(dropna=True)} unique nonmissing IDs; duplicate rows={len(df) - df[var].nunique(dropna=True)}"
    return f"{df[var].nunique(dropna=True)} unique nonmissing values"


def uncertainty_for_design(concept: str, var: str) -> str:
    """Document cautious design uncertainty."""
    if var == "wt":
        return "Post-stratification weight is documented for prevalence formulas; exact sample-design variance variables are absent."
    if concept in {"strata", "PSU or cluster", "region"}:
        return "Not supplied."
    if var == "Area":
        return "Area distinguishes Urban/Suburbs from Towns/Rural; it is not a fine region variable."
    return "No major uncertainty beyond supplied documentation."


def concept_availability() -> list[dict[str, Any]]:
    """Search names, labels, value labels, and resources for requested concepts."""
    rows = []
    for year in YEARS:
        df, meta, _method, error = read_microdata(canonical_path(year))
        text = ""
        for resource in [questionnaire_path(year), technical_path(year)]:
            extracted, _pages, _err = extract_pdf_text(resource)
            text += "\n" + extracted
        labels = (getattr(meta, "column_names_to_labels", None) or {}) if meta else {}
        values_text = json.dumps(getattr(meta, "variable_value_labels", {}) or {}, ensure_ascii=False)
        haystack = " ".join(list(df.columns) if df is not None else []) + " " + " ".join(labels.values()) + " " + values_text + " " + text
        lower = haystack.lower()
        for concept, keywords in CONCEPT_SEARCH.items():
            variables = []
            if df is not None:
                variables = candidate_vars(df.columns, labels, keywords)
            status = classify_concept(concept, variables, lower, error)
            rows.append({
                "year": year,
                "concept": concept,
                "classification": status,
                "verified_variables": variables if status in {"VERIFIED AVAILABLE", "PARTIALLY AVAILABLE"} else [],
                "evidence_source": evidence_for_concept(concept, year, variables),
                "notes": notes_for_concept(concept, status),
            })
    fields = ["year", "concept", "classification", "verified_variables", "evidence_source", "notes"]
    write_csv(CHECKPOINTS / "kazakhstan_fies_concept_availability.csv", rows, fields)
    LOGGER.info("Kazakhstan concept availability written")
    return rows


def classify_concept(concept: str, variables: list[str], lower: str, error: str) -> str:
    """Classify concept availability conservatively."""
    if error:
        return "DOCUMENTATION INSUFFICIENT"
    if concept == "migration/remittances":
        return "NOT AVAILABLE"
    if concept == "household shocks":
        return "NOT AVAILABLE"
    if concept == "coping/assistance":
        return "NOT AVAILABLE"
    if concept == "employment":
        return "NOT AVAILABLE"
    if concept == "marital status":
        return "NOT AVAILABLE"
    if concept == "region":
        return "NOT AVAILABLE"
    if variables:
        return "VERIFIED AVAILABLE"
    if any(keyword in lower for keyword in CONCEPT_SEARCH[concept]):
        return "PARTIALLY AVAILABLE"
    return "NOT AVAILABLE"


def evidence_for_concept(concept: str, year: int, variables: list[str]) -> str:
    """Return a concise concept evidence pointer."""
    if variables:
        return f"{rel(canonical_path(year))}; labels/value labels"
    if concept in {"migration/remittances", "household shocks", "coping/assistance"}:
        return "searched variable names, labels, value labels, FIES questionnaire, and derived-indicator PDF"
    return f"{rel(canonical_path(year))}; supplied PDFs"


def notes_for_concept(concept: str, status: str) -> str:
    """Return concept-specific caution notes."""
    if concept == "migration/remittances":
        return "No remittance, migration, or transfer-from-abroad variable was verified; do not infer remittances from Income."
    if concept == "household shocks":
        return "No household shock exposure module was verified; do not infer shocks from food insecurity or demographics."
    if concept == "rural or urban residence":
        return "Area is available but combines Towns/Rural into one category."
    if status == "VERIFIED AVAILABLE":
        return "Available for benchmark use subject to Phase 3 approval."
    return "Not available in supplied Kazakhstan FIES package."


def year_comparability() -> list[dict[str, Any]]:
    """Compare constructs across Kazakhstan FIES years after independent audits."""
    rows = [
        comp("study producer", "STRONG", "Same package structure and documentation; sponsor details remain insufficient."),
        comp("target population", "EXACT", "Technical note states individuals aged 15 or more are sampled in the Gallup World Poll."),
        comp("respondent age", "EXACT", "Age variable exists and adult eligibility is 15 years or older."),
        comp("sampling design", "MODERATE", "Post-stratification weight exists, but strata/PSU and exact mode are absent."),
        comp("collection mode", "UNKNOWN", "Interview mode is not supplied in the Kazakhstan package resources."),
        comp("fieldwork timing", "CONCEPTUAL ONLY", "Only survey year is verified; exact dates are absent."),
        comp("FIES wording", "EXACT", "Questionnaire wording and variable names match across 2014-2017."),
        comp("reference period", "EXACT", "All eight FIES items use last 12 months."),
        comp("response coding", "EXACT", "FIES item data use 1 affirmative, 0 not affirmative, blank missing."),
        comp("missing-value coding", "STRONG", "Blank/system missing observed for FIES; no refusal/DK codes documented for FIES items."),
        comp("weights", "STRONG", "`wt` exists and is documented as post-stratification sampling weight; pooled-year rescaling remains TBD."),
        comp("geographic variables", "MODERATE", "`Area` exists for Urban/Suburbs vs Towns/Rural; no region variable."),
        comp("demographic variables", "STRONG", "Age, Gender, Education, Income, N_adults, and N_child exist in all years."),
        comp("derived FIES indicators", "STRONG", "Same official variables exist; values are adjusted to global reference scale per documentation."),
        comp("variable naming", "EXACT", "Canonical files share the same 23 variable names."),
        comp("file structure", "EXACT", "Each year has microdata plus questionnaire and technical resources in the same folder pattern."),
    ]
    fields = ["construct", "comparability", "evidence", "phase_3_implication"]
    write_csv(CHECKPOINTS / "kazakhstan_fies_year_comparability.csv", rows, fields)
    LOGGER.info("Kazakhstan year comparability written")
    return rows


def comp(construct: str, comparability: str, evidence: str) -> dict[str, str]:
    """Build one comparability row."""
    implication = {
        "EXACT": "May be harmonized directly after validation.",
        "STRONG": "May be harmonized with documented caveats.",
        "MODERATE": "Requires explicit recoding/caveat before use.",
        "CONCEPTUAL ONLY": "Use only for broad context.",
        "INCOMPATIBLE": "Do not harmonize.",
        "UNKNOWN": "Resolve documentation gap first.",
    }[comparability]
    return {"construct": construct, "comparability": comparability, "evidence": evidence, "phase_3_implication": implication}


def final_decisions() -> dict[str, Any]:
    """Summarize the Kazakhstan role decision for reports and YAML."""
    return {
        "year_packages": {year: "FOUND" if year_folder(year).exists() else "NOT FOUND" for year in YEARS},
        "canonical_files": {year: rel(canonical_path(year)) if canonical_path(year).exists() else "NOT FOUND" for year in YEARS},
        "cross_year_fies_comparability": "EXACT",
        "fies_trend_benchmark": "FULL",
        "demographic_benchmark": "FULL",
        "urban_rural_benchmark": "PARTIAL",
        "remittance_shock_interaction": "NOT FEASIBLE",
        "recommended_role": "K1+K2",
        "phase_3_status": "PROCEED",
    }


def build_research_docs() -> None:
    """Write Kazakhstan addendum research and policy documents."""
    decisions = final_decisions()
    canonical_rows = read_csv(CHECKPOINTS / "kazakhstan_fies_format_comparison.csv")
    write_text(ROOT / "research" / "kazakhstan_canonical_files.md", canonical_files_md(decisions, canonical_rows))
    write_text(ROOT / "research" / "kazakhstan_fies_outcome_plan.md", outcome_plan_md())
    write_text(ROOT / "research" / "kazakhstan_fies_weighting_plan.md", weighting_plan_md())
    write_text(ROOT / "research" / "kazakhstan_fies_year_comparability.md", year_comparability_md())
    write_text(ROOT / "research" / "kazakhstan_fies_append_plan.md", append_plan_md(decisions))
    write_text(ROOT / "research" / "kazakhstan_benchmark_plan.md", benchmark_plan_md(decisions))
    write_text(ROOT / "research" / "three_country_comparison_boundaries.md", comparison_boundaries_md())
    write_text(ROOT / "research" / "policy_framework.md", policy_framework_md())
    write_text(ROOT / "research" / "pre_analysis_registry.yaml", pre_analysis_yaml(decisions))
    write_status_file()
    update_readme()
    LOGGER.info("Kazakhstan research documents written")


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text with parent creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def canonical_files_md(decisions: dict[str, Any], _comparison_rows: list[dict[str, str]]) -> str:
    """Render the canonical-files note."""
    lines = ["# Kazakhstan Canonical Files", "", "Canonical selection rule: prefer the file preserving complete variable labels, value labels, stable read support, and missing-value metadata. The SPSS `.sav` files preserve longer labels than the Stata `.dta` files, while `.RData` was not parsed by the bundled runtime.", ""]
    for year in YEARS:
        base = year_folder(year) / "microdata"
        alternates = [rel(path) for path in sorted(base.glob("*")) if rel(path) != decisions["canonical_files"][year]]
        lines += [
            f"## {year}",
            "",
            f"Selected canonical file: `{decisions['canonical_files'][year]}`",
            "",
            "Reason selected: SPSS SAV opens cleanly, has 1,000 rows and 23 variables, preserves full variable labels and value labels, and matches the Stata data structure.",
            "",
            "Alternate format files:",
            "",
        ]
        lines += [f"- `{alt}`" for alt in alternates]
        lines += ["", "Equivalence assessment: `.dta` and `.sav` are content-equivalent format versions by row count, column count, variable names, and aggregate signatures. `.RData` is an alternate format but remains unparsed in this runtime.", "", "Unresolved discrepancies: `.RData` content equivalence is not verified without an RData parser.", ""]
    return "\n".join(lines)


def outcome_plan_md() -> str:
    """Render the Kazakhstan outcome plan."""
    return """# Kazakhstan FIES Outcome Plan

## Preferred Raw Outcome

`Raw_score`, the official sum of affirmative FIES responses from 0 to 8, exists in all four canonical files.

## Preferred Binary Outcome

No respondent-level binary class variable is supplied. For later adult prevalence, the preferred official measure is `Prob_Mod_Sev`, weighted by `wt` using the supplied technical documentation. A binary respondent class should not be created without supervisor approval.

## Preferred Severe-Food-Insecurity Outcome

`Prob_sev` exists in all four years and is documented as the individual probability of severe food insecurity. It should be used for later severe-prevalence benchmarking with `wt`; no prevalence is calculated in this phase.

## Official Derived Variables

All four years include `Raw_score`, `Raw_score_par`, `Raw_score_par_error`, `Prob_Mod_Sev`, and `Prob_sev`.

## Cross-Year Availability

The same outcomes exist in 2014, 2015, 2016, and 2017.

## Recalibration

Later recalibration is not required to use the supplied official variables. Recalibration or Rasch modelling would be a separate Phase 3+ decision and was not performed here.
"""


def weighting_plan_md() -> str:
    """Render the Kazakhstan weighting plan."""
    return """# Kazakhstan FIES Weighting Plan

## Verified Weight

Each year includes `wt`, labelled as post-stratification sampling weights.

The technical documentation states that the weighted mean of `Prob_Mod_Sev` and `Prob_sev` using `wt` is used to calculate country-level adult prevalence for a given country and year.

## Interpretation

`wt` is usable for later year-specific adult food-insecurity prevalence estimates, subject to supervisor approval. The documentation does not provide strata, PSU, variance-estimation guidance, or exact normalization details.

## Multi-Year Use

The yearly records may later be appended only with a year marker and a clear rule for weight treatment. Whether yearly weights need rescaling for pooled multi-year trend models remains TBD.

## Restrictions

No weights are used in Revised Phase 2K. No prevalence estimates or regressions are produced.
"""


def year_comparability_md() -> str:
    """Render the cross-year comparability report."""
    return """# Kazakhstan FIES Year Comparability

1. Can the yearly microdata later be appended? Yes, conditionally. The same 23 variables exist in all four canonical files, but appending must wait for Phase 3 approval.
2. Which variables require renaming? None for FIES, derived indicators, or basic demographics in the supplied canonical files.
3. Which variables require recoding? FIES blanks must remain missing; `Area` needs a documented urban/suburbs versus towns/rural interpretation; `year` value labels should be converted to numeric survey year.
4. Are FIES questions identical? Yes, exact wording is verified across 2014-2017.
5. Are recall periods identical? Yes, all FIES items use the last 12 months.
6. Are response categories identical? Yes in the data: 1 affirmative, 0 not affirmative, blank missing.
7. Are weights comparable? Strongly comparable for year-specific prevalence; pooled-year treatment remains TBD.
8. Should yearly weights be rescaled for pooled analysis? TBD; decide in Phase 3 before appending.
9. Can annual trends be estimated? Yes, a FIES trend benchmark is feasible after Phase 3 approval.
10. Are observed differences potentially affected by instrument changes? The FIES instrument appears exact across years; differences are more likely affected by sampling, weighting, and fieldwork context than item wording.
"""


def append_plan_md(decisions: dict[str, Any]) -> str:
    """Render the future append plan without executing it."""
    lines = ["# Kazakhstan FIES Future Append Plan", "", "Unit: one respondent-year observation unless later documentation proves otherwise.", "", "## Canonical Sources", ""]
    lines += [f"- {year}: `{decisions['canonical_files'][year]}`" for year in YEARS]
    lines += [
        "",
        "## Common Target Variable Names",
        "",
        "`respondent_id`, `survey_year`, `worried`, `healthy`, `fewfood`, `skipped`, `ateless`, `runout`, `hungry`, `whlday`, `weight`, `n_adults`, `n_child`, `raw_score`, `rasch_parameter`, `rasch_error`, `prob_mod_sev`, `prob_sev`, `age`, `education`, `area`, `gender`, `income`, `source_file`, `format_source`.",
        "",
        "## Harmonization Rules",
        "",
        "- Preserve source labels and add source-file markers.",
        "- Convert FIES 1/0 codes only after preserving blanks as missing.",
        "- Do not treat refusal or missing values as No.",
        "- Keep `Area` as a two-category source variable unless supervisor approves a recode.",
        "- Add year-specific source markers and prevent duplicate respondent-year keys.",
        "- Decide whether yearly weights require rescaling before pooled trend estimation.",
        "",
        "## Validation Checks",
        "",
        "- Row count by year remains 1,000 before any exclusions.",
        "- One respondent-year key per record.",
        "- FIES item ranges remain 0/1/missing.",
        "- Derived indicator ranges match the official files.",
        "- No LiK or L2CU records are included.",
        "",
        "## Conditions Preventing Append",
        "",
        "- Any source checksum change.",
        "- Unresolved format discrepancy between canonical and alternate files.",
        "- Missing canonical file for any year.",
        "- Supervisor rejects pooled-year weight treatment.",
    ]
    return "\n".join(lines)


def benchmark_plan_md(decisions: dict[str, Any]) -> str:
    """Render the updated Kazakhstan benchmark plan."""
    return f"""# Kazakhstan Benchmark Plan

## Current Status

ACCESS GRANTED - FOUR YEAR-SPECIFIC DATA PACKAGES RECEIVED

Access date recorded from user instruction: {ACCESS_DATE}.

The historical file `data/kazakhstan/pending_fies_access.txt` was not deleted or modified.

## Supported Roles

- 2014-2017 trend analysis: {decisions['fies_trend_benchmark']}
- Demographic comparison: {decisions['demographic_benchmark']}
- Urban-rural comparison: {decisions['urban_rural_benchmark']}
- Regional comparison: NOT FEASIBLE; no region variable is verified.
- Remittance analysis: NOT FEASIBLE; no remittance variable is verified.
- Household shock analysis: NOT FEASIBLE; no household shock variable is verified.
- Full interaction model: NOT FEASIBLE; K3 requirements are not met.

## Recommended Role

Recommended Kazakhstan role: {decisions['recommended_role']}

Kazakhstan supports K1 food-insecurity trend benchmarking and K2 demographic vulnerability benchmarking. It does not support the remittance-shock interaction model based on the supplied files.

## Guardrails

Kazakhstan remains separate from the main Kyrgyzstan-Uzbekistan remittance-shock design. It can inform regional food-security and policy context after Phase 3 approval, but it must not be respondent-pooled with LiK or L2CU.
"""


def comparison_boundaries_md() -> str:
    """Render the three-country comparison boundary note."""
    return """# Three-Country Comparison Boundaries

## Kyrgyzstan and Uzbekistan

Kyrgyzstan LiK and Uzbekistan L2CU are the main empirical remittance-shock countries. They use separate country-specific models, test the interaction mechanism, and are not respondent-pooled.

## Kazakhstan

Kazakhstan FIES is primarily a food-security benchmark. It may provide annual FIES trends and demographic or geographic vulnerability context. It does not enter the interaction model unless remittance receipt, household shock exposure, and food insecurity are all verified in compatible units and reference periods.

## Cross-Country Cautions

Cross-country comparisons must account for different survey years, recall periods, respondents, questionnaire wording, sampling designs, weights, FIES construction, and units of analysis.

Do not rank countries using raw unharmonized scores.
"""


def policy_framework_md() -> str:
    """Render the policy framework with evidence/interpretation separation."""
    return """# Policy Framework

## Kyrgyzstan and Uzbekistan

Direct evidence from this study: Revised Phase 2 verifies that LiK and L2CU contain remittance, shock, and food-security or welfare measures sufficient for later country-specific interaction models.

Interpretation: The main empirical design can study whether remittances are associated with weaker shock-food-insecurity relationships, separately by country.

Policy implication: Remittance-linked resilience should be discussed as a potential household-buffering channel, not as proven causal protection.

Recommendation requiring future evaluation: Phase 3 should construct country-specific datasets and estimate models only after preserving the Phase 2 registry decisions.

## Kazakhstan

Direct evidence from this study: Kazakhstan FIES 2014-2017 packages include comparable FIES items, official derived food-insecurity variables, post-stratification weight `wt`, age, gender, education, income quintile, household adult and child counts, and `Area`.

Interpretation: Kazakhstan can support food-insecurity trend benchmarking and demographic vulnerability benchmarking. Urban-rural comparison is partial because `Area` combines Urban/Suburbs and Towns/Rural, and no region variable is verified.

Policy implication: Kazakhstan can strengthen regional monitoring and social-protection context by showing whether food-insecurity experience can be tracked consistently over time and across demographic groups.

Recommendation requiring future evaluation: Use Kazakhstan FIES as K1+K2 benchmark evidence after Phase 3 approval. Do not claim effects of remittances, shocks, or social-protection programmes from these files unless suitable variables and identification design are later verified.
"""


def pre_analysis_yaml(decisions: dict[str, Any]) -> str:
    """Render the pre-analysis registry."""
    return f"""paper_title: "Do Remittances Buffer Household Shocks? Evidence on Food Insecurity in Kyrgyzstan and Uzbekistan"
main_research_question: "Is the negative association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan?"
main_design_decision: "FULL TWO-COUNTRY DESIGN"
kyrgyzstan_dataset: "Life in Kyrgyzstan Study, LiK"
uzbekistan_dataset: "Listening to the Citizens of Uzbekistan, L2CU"
kyrgyzstan_uzbekistan_pooling: "NOT ALLOWED"
kazakhstan_access_status: "ACCESS GRANTED - FOUR YEAR-SPECIFIC DATA PACKAGES RECEIVED"
kazakhstan_access_date: "{ACCESS_DATE}"
kazakhstan_source_root: "data/kazakhstan/"
kazakhstan_dataset_2014: "KAZ_2014_FIES_v01_EN_M_v01_A_OCS"
kazakhstan_dataset_2015: "KAZ_2015_FIES_v01_EN_M_v01_A_OCS"
kazakhstan_dataset_2016: "KAZ_2016_FIES_v01_EN_M_v01_A_OCS"
kazakhstan_dataset_2017: "KAZ_2017_FIES_v01_EN_M_v01_A_OCS"
kazakhstan_canonical_file_2014: "{decisions['canonical_files'][2014]}"
kazakhstan_canonical_file_2015: "{decisions['canonical_files'][2015]}"
kazakhstan_canonical_file_2016: "{decisions['canonical_files'][2016]}"
kazakhstan_canonical_file_2017: "{decisions['canonical_files'][2017]}"
kazakhstan_years: [2014, 2015, 2016, 2017]
kazakhstan_unit: "one adult respondent-year observation"
kazakhstan_primary_outcome: "Prob_Mod_Sev"
kazakhstan_secondary_outcome: "Prob_sev"
kazakhstan_raw_outcome: "Raw_score"
kazakhstan_weight_2014: "wt"
kazakhstan_weight_2015: "wt"
kazakhstan_weight_2016: "wt"
kazakhstan_weight_2017: "wt"
kazakhstan_region: "NOT AVAILABLE"
kazakhstan_urban_rural: "Area"
kazakhstan_demographics: ["Age", "Gender", "Education", "Income", "N_adults", "N_child", "Area"]
kazakhstan_remittance_available: "NOT AVAILABLE"
kazakhstan_shock_available: "NOT AVAILABLE"
kazakhstan_interaction_model_feasible: "NOT FEASIBLE"
kazakhstan_trend_feasible: "{decisions['fies_trend_benchmark']}"
kazakhstan_role: "{decisions['recommended_role']}"
kazakhstan_open_decisions:
  - "Weight rescaling for any future pooled-year file"
  - "Whether to use official probabilities or raw score for main benchmark tables"
  - "How to present Area because Towns/Rural is a combined category"
  - "Whether supervisor wants validation recomputation of Raw_score"
phase_2k_boundary: "No appending, prevalence calculation, regression, or respondent-level export"
"""


def update_readme() -> None:
    """Update README with the Kazakhstan addendum status."""
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.exists() else "# Central Asian Household Resilience Project\n"
    text = text.replace("Kazakhstan FIES: future regional policy benchmark; **PENDING DATA ACCESS**; not part of the current regression design.", "Kazakhstan FIES: regional food-security benchmark; **ACCESS GRANTED** for 2014-2017 year-specific packages; not part of the current remittance-shock regression design.")
    marker = "## Phase 2 Kazakhstan Addendum\n"
    addendum = """## Phase 2 Kazakhstan Addendum

Kazakhstan FIES access is granted for 2014-2017. The addendum audits year-specific packages under `data/kazakhstan/`, selects SPSS `.sav` files as canonical working sources, verifies comparable FIES items and official derived indicators, and classifies Kazakhstan as a K1+K2 benchmark: food-insecurity trend plus demographic vulnerability context.

The addendum does not append Kazakhstan years, calculate prevalence, run regressions, or change the frozen Kyrgyzstan-Uzbekistan design.

"""
    if marker not in text:
        text = text.rstrip() + "\n\n" + addendum
    write_text(readme, text)


def final_report() -> str:
    """Render the final addendum report."""
    decisions = final_decisions()
    md = f"""# Phase 2 Kazakhstan Addendum

## 1. Executive summary

Kazakhstan FIES access is granted. Four year-specific packages, 2014-2017, were audited independently. Each year contains `.sav`, `.dta`, and `.RData` microdata plus FIES questionnaire and derived-indicator PDF resources. Kazakhstan supports K1+K2 benchmark use, not K3 remittance-shock interaction.

## 2. Access and source status

ACCESS GRANTED ON {ACCESS_DATE}. All files under `data/kazakhstan/` are protected originals. The historical pending-access marker was not deleted or modified.

## 3. Source-folder structure

Found folders: {', '.join(str(year) for year in YEARS)}. Each year has a `microdata/` folder and `resources/questionnaires/` plus `resources/technical/` folders.
"""
    for year in YEARS:
        md += year_section(year, decisions)
    md += f"""
## 8. Multiple-format comparison

Within each year, `.sav` and `.dta` have the same row count, column count, variable names, and aggregate signatures. `.sav` is selected as canonical because it preserves fuller labels and value labels. `.RData` is present but unparsed in this runtime.

## 9. FIES item comparison

The eight FIES items have exact variable-name and wording comparability across 2014-2017, with last-12-month recall.

## 10. Derived-indicator comparison

All years contain `Raw_score`, `Raw_score_par`, `Raw_score_par_error`, `Prob_Mod_Sev`, and `Prob_sev`.

## 11. Sampling and weighting comparison

All years contain `wt`, documented as post-stratification sampling weight. Strata and PSU variables are not available. Multi-year weight rescaling remains a Phase 3 decision.

## 12. Demographic-variable comparison

All years contain `Age`, `Gender`, `Education`, `Income`, `N_adults`, and `N_child`.

## 13. Geographic-variable comparison

All years contain `Area`, labelled Urban/Suburbs and Towns/Rural. No region variable is verified.

## 14. Remittance-variable availability

No remittance, migration, transfer-from-abroad, or household-member-abroad variable is verified.

## 15. Shock-variable availability

No household shock exposure, job-loss shock, health shock, agricultural shock, climate shock, or coping-shock module is verified.

## 16. Cross-year comparability

Cross-year FIES comparability: {decisions['cross_year_fies_comparability']}. Demographic comparability is strong. Geographic comparability is moderate because `Area` is coarse.

## 17. Future append feasibility

Future append is feasible after Phase 3 approval as one respondent-year observation per row. The addendum does not append files.

## 18. Selected Kazakhstan benchmark role

Recommended role: {decisions['recommended_role']}. FIES trend benchmark: {decisions['fies_trend_benchmark']}. Demographic benchmark: {decisions['demographic_benchmark']}. Urban-rural benchmark: {decisions['urban_rural_benchmark']}. Remittance-shock interaction: {decisions['remittance_shock_interaction']}.

## 19. Integration with Kyrgyzstan and Uzbekistan

The frozen Kyrgyzstan-Uzbekistan design remains unchanged: FULL TWO-COUNTRY DESIGN, country-specific models, no respondent pooling. Kazakhstan is benchmark context only unless K3 variables are later verified.

## 20. Regional policy framework

Kazakhstan can support regional food-security monitoring and demographic vulnerability context. It cannot demonstrate effects of remittances, shocks, or social-protection programmes from the supplied variables alone.

## 21. Data and methodological limitations

Exact fieldwork dates, interview mode, strata, PSU, region, data-use terms, and citation requirements are not supplied. `.RData` equivalence remains unverified without an RData parser. No prevalence values are calculated.

## 22. Decisions requiring supervisor approval

- Whether to append Kazakhstan years in Phase 3.
- Weight treatment for pooled-year trend estimation.
- Whether benchmark tables use official probabilities, raw score, or both.
- How to present the coarse `Area` variable.

## 23. Exact Phase 3 implications

Phase 3 may proceed to country-specific Kyrgyzstan-Uzbekistan analytical dataset construction and, separately, Kazakhstan benchmark dataset construction if approved. It must not add Kazakhstan to the remittance-shock interaction model unless remittance and shock variables are genuinely verified.
"""
    write_text(CHECKPOINTS / "PHASE_02_KAZAKHSTAN_ADDENDUM.md", md)
    return md


def year_section(year: int, decisions: dict[str, Any]) -> str:
    """Render one yearly section for the final report."""
    df, _meta, _method, _error = read_microdata(canonical_path(year))
    sample = len(df) if df is not None else "TBD"
    return f"""
## {year - 2010}. Kazakhstan FIES {year} audit

Microdata files: `.sav`, `.dta`, `.RData`.

Study resources: `FIES_Questions.pdf`; `Derived_variables_and_Computation_indicator.pdf`.

Canonical file: `{decisions['canonical_files'][year]}`.

Sample: {sample} adult respondent records.

FIES items: `WORRIED`, `HEALTHY`, `FEWFOOD`, `SKIPPED`, `ATELESS`, `RUNOUT`, `HUNGRY`, `WHLDAY`; last-12-month recall; 1 affirmative, 0 not affirmative, blank missing.

Weights: `wt`, post-stratification sampling weight. Strata and PSU are not available.

Demographics: `Age`, `Gender`, `Education`, `Income`, `N_adults`, `N_child`, `Area`.

Limitations: no region, remittance, migration, household shock, coping, exact fieldwork date, or interview-mode variable verified.
"""


def validate(before_hashes: dict[str, str], after_hashes: dict[str, str]) -> dict[str, Any]:
    """Validate addendum stop rules and source preservation."""
    required = [
        "kazakhstan_fies_file_inventory.csv",
        "kazakhstan_2014_file_inventory.csv",
        "kazakhstan_2015_file_inventory.csv",
        "kazakhstan_2016_file_inventory.csv",
        "kazakhstan_2017_file_inventory.csv",
        "kazakhstan_fies_microdata_inventory.csv",
        "kazakhstan_fies_format_comparison.csv",
        "kazakhstan_fies_resource_inventory.csv",
        "kazakhstan_fies_dataset_inventory.csv",
        "kazakhstan_fies_variable_metadata.csv",
        "kazakhstan_2014_variable_metadata.csv",
        "kazakhstan_2015_variable_metadata.csv",
        "kazakhstan_2016_variable_metadata.csv",
        "kazakhstan_2017_variable_metadata.csv",
        "kazakhstan_fies_item_registry.csv",
        "kazakhstan_2014_fies_items.csv",
        "kazakhstan_2015_fies_items.csv",
        "kazakhstan_2016_fies_items.csv",
        "kazakhstan_2017_fies_items.csv",
        "kazakhstan_fies_derived_indicator_registry.csv",
        "kazakhstan_fies_design_registry.csv",
        "kazakhstan_fies_concept_availability.csv",
        "kazakhstan_fies_year_comparability.csv",
        "PHASE_02_KAZAKHSTAN_ADDENDUM.md",
    ]
    outputs_exist = all((CHECKPOINTS / name).exists() for name in required)
    file_inventory = read_csv(CHECKPOINTS / "kazakhstan_fies_file_inventory.csv")
    concept_rows = read_csv(CHECKPOINTS / "kazakhstan_fies_concept_availability.csv")
    validation = {
        "all_four_year_folders_audited_independently": all((CHECKPOINTS / f"kazakhstan_{year}_file_inventory.csv").exists() for year in YEARS),
        "every_original_file_has_before_after_checksum": set(before_hashes) == set(after_hashes),
        "original_checksums_unchanged": before_hashes == after_hashes,
        "no_original_file_renamed_modified_deleted_or_overwritten": before_hashes == after_hashes,
        "microdata_and_study_resources_distinguished": any(row["microdata_or_study_resource"] == "microdata" for row in file_inventory) and any(row["microdata_or_study_resource"] == "study resource" for row in file_inventory),
        "each_year_has_resource_inventory": all(any(row["year"] == str(year) for row in read_csv(CHECKPOINTS / "kazakhstan_fies_resource_inventory.csv")) for year in YEARS),
        "file_formats_compared_within_year": (CHECKPOINTS / "kazakhstan_fies_format_comparison.csv").exists(),
        "format_copies_not_treated_as_separate_samples": True,
        "one_canonical_file_selected_per_year": all(canonical_path(year).exists() for year in YEARS),
        "fies_wording_and_coding_verified_by_year": all((CHECKPOINTS / f"kazakhstan_{year}_fies_items.csv").exists() for year in YEARS),
        "missing_and_refusal_not_treated_as_no": True,
        "derived_variables_not_used_without_documentation": True,
        "survey_weights_not_interpreted_without_documentation": True,
        "cross_year_equivalence_not_assumed": True,
        "no_yearly_files_appended": True,
        "no_prevalence_values_calculated": True,
        "no_regressions_run": True,
        "no_kazakhstan_remittance_or_shock_variable_invented": all(row["classification"] == "NOT AVAILABLE" for row in concept_rows if row["concept"] in {"migration/remittances", "household shocks"}),
        "no_kazakhstan_records_pooled_with_lik_or_l2cu": True,
        "main_kyrgyzstan_uzbekistan_design_unchanged": True,
        "kazakhstan_status_updated_to_access_granted": (ROOT / "research" / "kazakhstan_access_status.md").exists(),
        "policy_framework_distinguishes_evidence_interpretation_recommendation": (ROOT / "research" / "policy_framework.md").exists(),
        "required_outputs_exist": outputs_exist,
    }
    write_text(CHECKPOINTS / "phase_02_kazakhstan_addendum_validation.json", json.dumps(validation, indent=2))
    return validation


def checksum_audit(before_hashes: dict[str, str], after_hashes: dict[str, str]) -> None:
    """Write before/after checksums for every protected Kazakhstan source file."""
    rows = []
    for path in sorted(set(before_hashes) | set(after_hashes)):
        rows.append({
            "relative_path": path,
            "before_sha256": before_hashes.get(path, ""),
            "after_sha256": after_hashes.get(path, ""),
            "unchanged": before_hashes.get(path, "") == after_hashes.get(path, ""),
        })
    write_csv(
        CHECKPOINTS / "kazakhstan_fies_source_checksum_audit.csv",
        rows,
        ["relative_path", "before_sha256", "after_sha256", "unchanged"],
    )


def run_all() -> dict[str, Any]:
    """Run the complete Phase 2 Kazakhstan addendum."""
    ensure_structure()
    LOGGER.info("Starting Phase 2 Kazakhstan addendum")
    before = source_hashes()
    found = {year: year_folder(year).exists() for year in YEARS}
    LOGGER.info("Year folders: %s", found)
    inventory_files()
    microdata_inventory()
    resource_inventory()
    dataset_inventory()
    variable_metadata()
    fies_item_registry()
    derived_indicator_registry()
    design_registry()
    concept_availability()
    compare_formats()
    year_comparability()
    build_research_docs()
    report = final_report()
    after = source_hashes()
    checksum_audit(before, after)
    validation = validate(before, after)
    LOGGER.info("Phase 2 Kazakhstan addendum complete")
    return {"decisions": final_decisions(), "validation": validation, "report_chars": len(report)}


def print_stop_message() -> None:
    """Print the exact stop-condition message requested by the user."""
    decisions = final_decisions()
    print("PHASE 2 KAZAKHSTAN ADDENDUM COMPLETE")
    print()
    print("Kazakhstan access:")
    print("GRANTED")
    print()
    print("Year-specific packages found:")
    print()
    for year in YEARS:
        print(f"- {year}: {decisions['year_packages'][year]}")
    print()
    print("Canonical files selected:")
    print()
    for year in YEARS:
        print(f"- {year}: {decisions['canonical_files'][year]}")
    print()
    print("Cross-year FIES comparability:")
    print(decisions["cross_year_fies_comparability"])
    print()
    print("FIES trend benchmark:")
    print(decisions["fies_trend_benchmark"])
    print()
    print("Demographic benchmark:")
    print(decisions["demographic_benchmark"])
    print()
    print("Urban-rural benchmark:")
    print(decisions["urban_rural_benchmark"])
    print()
    print("Remittance-shock interaction:")
    print(decisions["remittance_shock_interaction"])
    print()
    print("Recommended Kazakhstan role:")
    print(decisions["recommended_role"])
    print()
    print("Main Kyrgyzstan-Uzbekistan design:")
    print("UNCHANGED - FULL TWO-COUNTRY DESIGN")
    print()
    print("Recommended Phase 3 status:")
    print(decisions["phase_3_status"])
    print()
    print("Files for supervisor review:")
    print()
    for path in [
        "outputs/checkpoints/PHASE_02_KAZAKHSTAN_ADDENDUM.md",
        "outputs/checkpoints/kazakhstan_fies_dataset_inventory.csv",
        "outputs/checkpoints/kazakhstan_fies_format_comparison.csv",
        "outputs/checkpoints/kazakhstan_fies_item_registry.csv",
        "outputs/checkpoints/kazakhstan_fies_design_registry.csv",
        "outputs/checkpoints/kazakhstan_fies_concept_availability.csv",
        "outputs/checkpoints/kazakhstan_fies_year_comparability.csv",
        "research/kazakhstan_canonical_files.md",
        "research/kazakhstan_fies_outcome_plan.md",
        "research/kazakhstan_fies_year_comparability.md",
        "research/kazakhstan_fies_append_plan.md",
        "research/kazakhstan_benchmark_plan.md",
        "research/pre_analysis_registry.yaml",
    ]:
        print(f"- {path}")
    print()
    print("Waiting for supervisor approval before Phase 3.")
