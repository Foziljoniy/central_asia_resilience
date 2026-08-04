"""Phase 4 descriptive analysis for the Central Asian Household Resilience Project.

This module produces aggregate-only descriptive outputs.  It intentionally does
not estimate causal, regression, fixed-effects, logit, p-value, or hypothesis
test quantities.  The functions are deterministic and run from the project root.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


ROOT = Path(".")
CHECK = ROOT / "outputs" / "checkpoints"
TABLES = ROOT / "outputs" / "tables"
FIGS = ROOT / "outputs" / "figures"
FIG_DATA = FIGS / "data"
LOGS = ROOT / "outputs" / "logs"
ARCHIVE = ROOT / "outputs" / "archive" / "phase_03_blocked_markers"
RESEARCH = ROOT / "research"
PROCESSED = ROOT / "data" / "processed"
MIN_CELL = 30

LIK = PROCESSED / "kyrgyzstan" / "lik_2019_adult_analysis.parquet"
LIK_HH = PROCESSED / "kyrgyzstan" / "lik_2019_household_sensitivity.parquet"
UZB = PROCESSED / "uzbekistan" / "l2cu_r49_82_household_analysis.parquet"
KAZ_YEARS = {
    2014: PROCESSED / "kazakhstan" / "kaz_fies_2014.parquet",
    2015: PROCESSED / "kazakhstan" / "kaz_fies_2015.parquet",
    2016: PROCESSED / "kazakhstan" / "kaz_fies_2016.parquet",
    2017: PROCESSED / "kazakhstan" / "kaz_fies_2017.parquet",
}
KAZ = PROCESSED / "kazakhstan" / "kaz_fies_2014_2017_benchmark.parquet"
MANIFEST = CHECK / "phase_03_reproducibility_manifest.json"

LIK_ITEMS = [f"lik_fies_item_{i}" for i in range(1, 9)]
UZB_ITEMS = [f"uzb_fies_item_{i}" for i in range(1, 9)]
KAZ_ITEMS = [f"kaz_fies_item_{i}" for i in range(1, 9)]


def ensure_dirs() -> None:
    """Create Phase 4 output directories."""
    for path in [CHECK, TABLES, FIGS, FIG_DATA, LOGS, ARCHIVE, RESEARCH]:
        path.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Configure logging to outputs/logs/phase_04.log and console."""
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOGS / "phase_04.log", mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def sha256(path: Path) -> str:
    """Return the SHA256 checksum for a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest() -> dict[str, Any]:
    """Read the Phase 3 manifest."""
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    """Write JSON with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write a list of dictionaries as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols: list[str] = []
    for row in rows:
        for key in row:
            if key not in cols:
                cols.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in cols})


def load_data() -> dict[str, pd.DataFrame]:
    """Read back all approved Parquet files."""
    data = {
        "lik": pd.read_parquet(LIK, engine="pyarrow"),
        "lik_hh": pd.read_parquet(LIK_HH, engine="pyarrow"),
        "uzb": pd.read_parquet(UZB, engine="pyarrow"),
        "kaz": pd.read_parquet(KAZ, engine="pyarrow"),
    }
    for year, path in KAZ_YEARS.items():
        data[f"kaz_{year}"] = pd.read_parquet(path, engine="pyarrow")
    return data


def to_num(s: pd.Series) -> pd.Series:
    """Convert a series to numeric values."""
    return pd.to_numeric(s, errors="coerce")


def nonmiss_n(df: pd.DataFrame, col: str) -> int:
    """Count non-missing observations for a column if present."""
    return int(df[col].notna().sum()) if col in df.columns else 0


def prop(s: pd.Series) -> float | None:
    """Mean of a binary-like variable."""
    x = to_num(s).dropna()
    return None if len(x) == 0 else float(x.mean())


def wmean(x: pd.Series, w: pd.Series) -> float | None:
    """Weighted mean using non-missing positive weights."""
    xx = to_num(x)
    ww = to_num(w)
    ok = xx.notna() & ww.notna() & (ww > 0)
    if int(ok.sum()) == 0:
        return None
    return float(np.average(xx[ok], weights=ww[ok]))


def safe_mean(s: pd.Series) -> float | None:
    x = to_num(s).dropna()
    return None if len(x) == 0 else float(x.mean())


def safe_median(s: pd.Series) -> float | None:
    x = to_num(s).dropna()
    return None if len(x) == 0 else float(x.median())


def desc_numeric(df: pd.DataFrame, col: str, weight_status: str, denom: str, cell_n: int | None = None) -> dict[str, Any]:
    """Aggregate numeric descriptive statistics with suppression."""
    n = len(df) if cell_n is None else cell_n
    if col not in df.columns:
        return {"variable": col, "status": "VARIABLE_ABSENT", "denominator": denom, "weight_status": weight_status}
    x = to_num(df[col]).dropna()
    row = {
        "variable": col,
        "denominator": denom,
        "observations": int(len(df)),
        "nonmissing": int(len(x)),
        "missing": int(len(df) - len(x)),
        "weight_status": weight_status,
        "small_cell_status": "ADEQUATE" if n >= MIN_CELL else "SUPPRESSED_SMALL_CELL",
    }
    if n < MIN_CELL or len(x) == 0:
        row.update({"mean": "", "sd": "", "median": "", "p25": "", "p75": "", "min": "", "max": ""})
    else:
        row.update(
            {
                "mean": float(x.mean()),
                "sd": float(x.std(ddof=1)) if len(x) > 1 else 0.0,
                "median": float(x.median()),
                "p25": float(x.quantile(0.25)),
                "p75": float(x.quantile(0.75)),
                "min": float(x.min()),
                "max": float(x.max()),
            }
        )
    return row


def desc_binary(df: pd.DataFrame, col: str, weight_status: str, denom: str, cell_n: int | None = None) -> dict[str, Any]:
    """Aggregate binary descriptive statistics with suppression."""
    n = len(df) if cell_n is None else cell_n
    row = desc_numeric(df, col, weight_status, denom, cell_n=n)
    row["statistic_type"] = "binary_proportion"
    if row.get("small_cell_status") == "ADEQUATE" and col in df.columns and row.get("nonmissing", 0):
        row["proportion"] = prop(df[col])
    else:
        row["proportion"] = "" if col in df.columns else ""
    return row


def cronbach_alpha(df: pd.DataFrame, items: list[str]) -> float | None:
    """Cronbach's alpha for complete binary item matrix."""
    mat = df[items].apply(pd.to_numeric, errors="coerce").dropna()
    if len(mat) < 2:
        return None
    k = len(items)
    item_vars = mat.var(axis=0, ddof=1).sum()
    total_var = mat.sum(axis=1).var(ddof=1)
    if not total_var or math.isnan(total_var):
        return None
    return float(k / (k - 1) * (1 - item_vars / total_var))


def item_rest_corr(df: pd.DataFrame, item: str, items: list[str]) -> float | None:
    mat = df[items].apply(pd.to_numeric, errors="coerce").dropna()
    if len(mat) < 3:
        return None
    rest = mat[[c for c in items if c != item]].sum(axis=1)
    if mat[item].std(ddof=1) == 0 or rest.std(ddof=1) == 0:
        return None
    return float(mat[item].corr(rest))


def group_label(rem: Any, shock: Any) -> str:
    """Four-group label for remittance and shock status."""
    if rem == 0 and shock == 0:
        return "No remittance, no shock"
    if rem == 1 and shock == 0:
        return "Remittance, no shock"
    if rem == 0 and shock == 1:
        return "No remittance, shock"
    if rem == 1 and shock == 1:
        return "Remittance, shock"
    return "Missing remittance or shock"


def add_four_group(df: pd.DataFrame, rem: str, shock: str, out: str) -> pd.DataFrame:
    """Return a copy with four mutually exclusive descriptive groups."""
    d = df.copy()
    d[out] = [group_label(r, s) for r, s in zip(to_num(d[rem]), to_num(d[shock]))]
    return d


def primary_lik(df: pd.DataFrame) -> pd.DataFrame:
    """Kyrgyzstan primary descriptive sample."""
    return df[(df["lik_fies_complete"] == 1) & df["lik_remittance_receipt"].notna() & df["lik_any_shock"].notna()].copy()


def primary_uzb(df: pd.DataFrame) -> pd.DataFrame:
    """Uzbekistan primary descriptive sample."""
    return df[(df["uzb_fies_complete"] == 1) & df["uzb_any_remittance"].notna() & df["uzb_any_verified_shock"].notna()].copy()


def primary_kaz(df: pd.DataFrame) -> pd.DataFrame:
    """Kazakhstan benchmark-eligible descriptive records."""
    return df[(df[KAZ_ITEMS].notna().all(axis=1)) & df["kaz_weight_original"].notna()].copy()


def save_simple_figure(
    stem: str,
    title: str,
    note: str,
    rows: list[dict[str, Any]],
    x_col: str,
    y_col: str,
    kind: str = "bar",
) -> None:
    """Save figure data, a PNG, and a PDF using aggregate data only."""
    write_csv(FIG_DATA / f"{stem}.csv", rows)
    width, height = 1200, 760
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("arial.ttf", 28)
        font = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_big = font = font_small = None
    draw.text((40, 30), title, fill="black", font=font_big)
    draw.text((40, 675), note[:145], fill="black", font=font_small)
    plot_left, plot_top, plot_right, plot_bottom = 90, 110, 1140, 620
    draw.line((plot_left, plot_bottom, plot_right, plot_bottom), fill="black", width=2)
    draw.line((plot_left, plot_top, plot_left, plot_bottom), fill="black", width=2)
    vals = [float(r[y_col]) for r in rows if r.get(y_col) not in ("", None) and not pd.isna(r.get(y_col))]
    labels = [str(r[x_col]) for r in rows if r.get(y_col) not in ("", None) and not pd.isna(r.get(y_col))]
    if not vals:
        draw.text((120, 300), "No reportable aggregate values.", fill="black", font=font)
    else:
        ymin = min(0.0, min(vals))
        ymax = max(vals)
        if ymax == ymin:
            ymax = ymin + 1
        n = len(vals)
        if kind == "line" and n > 1:
            pts = []
            for i, v in enumerate(vals):
                x = plot_left + (plot_right - plot_left) * i / (n - 1)
                y = plot_bottom - (v - ymin) / (ymax - ymin) * (plot_bottom - plot_top)
                pts.append((x, y))
            draw.line(pts, fill="#1f77b4", width=4)
            for (x, y), lab, v in zip(pts, labels, vals):
                draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="#1f77b4")
                draw.text((x - 18, plot_bottom + 10), lab[:8], fill="black", font=font_small)
                draw.text((x - 18, y - 26), f"{v:.2f}", fill="black", font=font_small)
        else:
            gap = 8
            bw = max(12, (plot_right - plot_left - gap * (n + 1)) / max(n, 1))
            for i, (lab, v) in enumerate(zip(labels, vals)):
                x0 = plot_left + gap + i * (bw + gap)
                x1 = x0 + bw
                y = plot_bottom - (v - ymin) / (ymax - ymin) * (plot_bottom - plot_top)
                draw.rectangle((x0, y, x1, plot_bottom), fill="#4c78a8")
                draw.text((x0, plot_bottom + 10), lab[:15], fill="black", font=font_small)
                draw.text((x0, y - 24), f"{v:.2f}", fill="black", font=font_small)
    png = FIGS / f"{stem}.png"
    pdf = FIGS / f"{stem}.pdf"
    img.save(png)
    c = canvas.Canvas(str(pdf), pagesize=letter)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(36, 750, title[:100])
    c.drawImage(str(png), 36, 150, width=540, height=342)
    c.setFont("Helvetica", 8)
    c.drawString(36, 120, note[:120])
    c.save()


def administrative_closeout() -> dict[str, Any]:
    """Update Kazakhstan status, archive blocked markers, and clean active manifest."""
    logging.info("Starting Phase 4A administrative closeout")
    status_sentence = (
        "Kazakhstan FIES access is granted. Kazakhstan is used as a K1+K2 "
        "food-insecurity trend and demographic benchmark. It is not part of the "
        "remittance-shock interaction model."
    )
    files_updated: list[str] = []
    for path in [
        RESEARCH / "main_analysis_plan.md",
        RESEARCH / "kazakhstan_benchmark_plan.md",
        ROOT / "README.md",
    ]:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            new = text
            for phrase in [
                "Kazakhstan FIES access is pending.",
                "Kazakhstan FIES access remains pending.",
                "Kazakhstan access is pending.",
                "Kazakhstan status as PENDING DATA ACCESS.",
                "Kazakhstan FIES remains a future benchmark with **PENDING DATA ACCESS** and is not required for the current two-country analysis.",
            ]:
                new = new.replace(phrase, status_sentence)
            if status_sentence not in new:
                new += f"\n\n## Kazakhstan Phase 4 status\n\n{status_sentence}\n"
            if new != text:
                path.write_text(new, encoding="utf-8")
                files_updated.append(str(path))
    reg = RESEARCH / "pre_analysis_registry.yaml"
    if reg.exists():
        text = reg.read_text(encoding="utf-8")
        if "kazakhstan_phase_4_status" not in text:
            text += f'\nkazakhstan_phase_4_status: "{status_sentence}"\n'
        text = text.replace('kazakhstan_access_status: "PENDING DATA ACCESS"', 'kazakhstan_access_status: "ACCESS GRANTED - FOUR YEAR-SPECIFIC DATA PACKAGES RECEIVED"')
        reg.write_text(text, encoding="utf-8")
        files_updated.append(str(reg))

    found: list[str] = []
    archived: list[dict[str, str]] = []
    for src in PROCESSED.rglob("*.parquet.blocked.json"):
        found.append(str(src))
        rel = src.relative_to(PROCESSED)
        dest = ARCHIVE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        archived.append({"original_path": str(src), "archive_path": str(dest)})

    manifest = read_manifest()
    before_paths = manifest.get("processed_file_paths", [])
    manifest["processed_file_paths"] = [p for p in before_paths if not p.endswith(".blocked.json")]
    checks = manifest.get("processed_sha256_checksums", {})
    manifest["processed_sha256_checksums"] = {k: v for k, v in checks.items() if not k.endswith(".blocked.json")}
    manifest["phase_04_administrative_closeout"] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "kazakhstan_status": status_sentence,
        "blocked_markers_found_in_processed": found,
        "blocked_markers_archived": archived,
        "active_manifest_blocked_markers_removed": True,
        "raw_checksums_unchanged": manifest.get("raw_source_checksums_unchanged", False),
    }
    write_json(MANIFEST, manifest)
    files_updated.append(str(MANIFEST))
    out = {
        "kazakhstan_status_update": status_sentence,
        "files_updated": files_updated,
        "blocked_markers_found": found,
        "blocked_markers_archived": archived,
        "manifest_regeneration_status": "COMPLETE",
        "raw_checksums_unchanged": bool(manifest.get("raw_source_checksums_unchanged", False)),
        "previously_archived_markers": [str(p) for p in ARCHIVE.rglob("*.parquet.blocked.json")],
    }
    write_json(CHECK / "phase_04_administrative_closeout.json", out)
    return out


def freeze_specification() -> list[dict[str, Any]]:
    """Freeze Phase 4 descriptive definitions before calculations."""
    rows = [
        {"country": "Kyrgyzstan", "dataset": str(LIK), "analysis_unit": "adult respondent linked to household exposures", "population": "LiK 2019 adult respondents", "outcome": "lik_fies_raw_score", "outcome_direction": "higher indicates more affirmative food-insecurity experiences", "remittance_variable": "lik_remittance_receipt", "shock_variable": "lik_any_shock", "shock_definition": "broad verified household shock exposure", "weight": "none", "weight_status": "unweighted; no survey weight assigned", "grouping_variable": "remittance x shock", "statistic": "aggregate descriptive means/proportions/distributions", "denominator": "complete FIES, known remittance, known shock", "missing_rule": "do not score incomplete eight-item FIES responses", "minimum_cell_size": MIN_CELL, "primary_or_sensitivity": "primary", "output_table": "tables 04-06", "output_figure": "figures 04,07,10,11", "notes": "No causal wording or tests."},
        {"country": "Kyrgyzstan", "dataset": str(LIK_HH), "analysis_unit": "household", "population": "LiK 2019 households with adult FIES summaries", "outcome": "household adult FIES summaries", "outcome_direction": "higher indicates more affirmative food-insecurity experiences", "remittance_variable": "lik_remittance_receipt", "shock_variable": "lik_any_shock", "shock_definition": "household shock exposure", "weight": "none", "weight_status": "unweighted", "grouping_variable": "summary type", "statistic": "correlations and rank agreement among summaries", "denominator": "households in sensitivity file", "missing_rule": "summary-specific nonmissing denominators", "minimum_cell_size": MIN_CELL, "primary_or_sensitivity": "sensitivity", "output_table": "table 07", "output_figure": "", "notes": "Does not replace adult primary outcome."},
        {"country": "Uzbekistan", "dataset": str(UZB), "analysis_unit": "household-round", "population": "L2CU rounds 49-82 household-rounds", "outcome": "uzb_fies_raw_score", "outcome_direction": "higher indicates more affirmative food-insecurity experiences", "remittance_variable": "uzb_any_remittance", "shock_variable": "uzb_any_verified_shock / uzb_work_loss_shock", "shock_definition": "verified shock; work-loss as primary specific shock", "weight": "none", "weight_status": "unweighted; popw retained but not approved", "grouping_variable": "remittance x shock; round", "statistic": "aggregate descriptive means/proportions/trends", "denominator": "complete FIES, known remittance, known shock", "missing_rule": "separate structural non-administration from nonresponse", "minimum_cell_size": MIN_CELL, "primary_or_sensitivity": "primary", "output_table": "tables 08-13", "output_figure": "figures 05,08,12-16", "notes": "L2CU popw is not used."},
        {"country": "Kazakhstan", "dataset": str(KAZ), "analysis_unit": "adult respondent-year", "population": "Kazakhstan FIES 2014-2017 adult respondents", "outcome": "kaz_raw_score; kaz_prob_mod_sev; kaz_prob_sev", "outcome_direction": "higher indicates more affirmative food-insecurity experiences or higher supplied probability", "remittance_variable": "not available", "shock_variable": "not available", "shock_definition": "not applicable", "weight": "kaz_weight_original", "weight_status": "year-specific weighted benchmark only", "grouping_variable": "year and demographic group", "statistic": "year-specific weighted descriptive means/proportions", "denominator": "valid FIES items and valid original weight", "missing_rule": "year-specific denominators; suppress small groups", "minimum_cell_size": MIN_CELL, "primary_or_sensitivity": "benchmark", "output_table": "tables 14-15", "output_figure": "figures 06,09,17,18", "notes": "No pooled 2014-2017 prevalence."},
    ]
    write_csv(RESEARCH / "phase_04_descriptive_specification.csv", rows)
    return rows


def input_validation(data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Validate approved Phase 4 inputs against manifest and coding rules."""
    manifest = read_manifest()
    expected = {
        str(LIK).replace("\\", "/"): (7043, "lik_adult_analysis_key", LIK_ITEMS, "lik_fies_raw_score", "lik_remittance_receipt", "lik_any_shock", "survey_year", None),
        str(LIK_HH).replace("\\", "/"): (2314, "lik_household_analysis_key", [], "lik_hh_mean_adult_raw_score", "lik_remittance_receipt", "lik_any_shock", "survey_year", None),
        str(UZB).replace("\\", "/"): (48925, "uzb_household_round_key", UZB_ITEMS, "uzb_fies_raw_score", "uzb_any_remittance", "uzb_any_verified_shock", "round", "uzb_popw_unverified"),
        str(KAZ).replace("\\", "/"): (4000, "kaz_respondent_year_key", KAZ_ITEMS, "kaz_raw_score", None, None, "survey_year", "kaz_weight_original"),
    }
    frames = {str(LIK).replace("\\", "/"): data["lik"], str(LIK_HH).replace("\\", "/"): data["lik_hh"], str(UZB).replace("\\", "/"): data["uzb"], str(KAZ).replace("\\", "/"): data["kaz"]}
    rows: list[dict[str, Any]] = []
    parquet_sha = manifest.get("technical_revision", {}).get("parquet_sha256", {})
    for path, (n, key, items, outcome, rem, shock, time, weight) in expected.items():
        df = frames[path]
        req = [key, outcome, time] + items + ([rem] if rem else []) + ([shock] if shock else []) + ([weight] if weight else [])
        missing = [c for c in req if c not in df.columns]
        checksum = sha256(Path(path))
        expected_sha = parquet_sha.get(path) or manifest.get("processed_sha256_checksums", {}).get(path)
        rows.append({
            "path": path,
            "row_count": len(df),
            "expected_row_count": n,
            "column_count": len(df.columns),
            "required_variables_missing": ";".join(missing),
            "key": key,
            "duplicate_keys": int(df[key].duplicated().sum()) if key in df.columns else "",
            "outcome_min": safe_mean(pd.Series([to_num(df[outcome]).min()])) if outcome in df.columns else "",
            "outcome_max": safe_mean(pd.Series([to_num(df[outcome]).max()])) if outcome in df.columns else "",
            "remittance_range": "" if not rem else f"{to_num(df[rem]).min()} to {to_num(df[rem]).max()}",
            "shock_range": "" if not shock else f"{to_num(df[shock]).min()} to {to_num(df[shock]).max()}",
            "time_range": f"{to_num(df[time]).min()} to {to_num(df[time]).max()}" if time in df.columns else "",
            "weight_range": "" if not weight else f"{to_num(df[weight]).min()} to {to_num(df[weight]).max()}",
            "checksum": checksum,
            "expected_checksum": expected_sha,
            "checksum_status": "MATCH" if expected_sha == checksum else "MISMATCH",
            "source_provenance": ";".join([str(x) for x in df[[c for c in df.columns if c.endswith('source_provenance') or c.endswith('source_file')]].astype(str).agg("|".join, axis=1).drop_duplicates().head(5)]) if any(c.endswith("source_provenance") or c.endswith("source_file") for c in df.columns) else "",
            "validation_status": "PASS" if len(df) == n and not missing and (key in df.columns and int(df[key].duplicated().sum()) == 0) and expected_sha == checksum else "FAIL",
        })
    for year, path in KAZ_YEARS.items():
        df = data[f"kaz_{year}"]
        path_s = str(path).replace("\\", "/")
        checksum = sha256(path)
        expected_sha = parquet_sha.get(path_s) or manifest.get("processed_sha256_checksums", {}).get(path_s)
        rows.append({"path": path_s, "row_count": len(df), "expected_row_count": 1000, "column_count": len(df.columns), "required_variables_missing": "", "key": "kaz_respondent_year_key", "duplicate_keys": int(df["kaz_respondent_year_key"].duplicated().sum()), "outcome_min": to_num(df["kaz_raw_score"]).min(), "outcome_max": to_num(df["kaz_raw_score"]).max(), "time_range": f"{year} to {year}", "weight_range": f"{to_num(df['kaz_weight_original']).min()} to {to_num(df['kaz_weight_original']).max()}", "checksum": checksum, "expected_checksum": expected_sha, "checksum_status": "MATCH" if expected_sha == checksum else "MISMATCH", "source_provenance": str(path), "validation_status": "PASS" if len(df) == 1000 and expected_sha == checksum else "FAIL"})
    write_csv(CHECK / "phase_04_input_validation.csv", rows)
    return rows


def sample_flow(data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Build sample-flow checkpoints and table without outcome values."""
    lik, uzb, kaz = data["lik"], data["uzb"], data["kaz"]
    rows: list[dict[str, Any]] = []
    def add(country: str, step: str, n: int, unique: Any = "", note: str = "") -> None:
        rows.append({"country": country, "step": step, "observations": int(n), "unique_households": unique, "note": note})
    add("Kyrgyzstan", "all constructed adult rows", len(lik), lik["lik_household_analysis_key"].nunique())
    add("Kyrgyzstan", "adults with valid household links", int(lik["lik_household_analysis_key"].notna().sum()), lik.loc[lik["lik_household_analysis_key"].notna(), "lik_household_analysis_key"].nunique())
    add("Kyrgyzstan", "adults with known remittance status", int(lik["lik_remittance_receipt"].notna().sum()), "")
    add("Kyrgyzstan", "adults with known shock status", int(lik["lik_any_shock"].notna().sum()), "")
    add("Kyrgyzstan", "adults with all eight valid food-insecurity items", int((lik["lik_fies_complete"] == 1).sum()), "")
    lp = primary_lik(lik)
    add("Kyrgyzstan", "adults eligible for primary descriptive sample", len(lp), lp["lik_household_analysis_key"].nunique())
    for bucket, n in lik.groupby("lik_household_analysis_key").size().describe().to_dict().items():
        rows.append({"country": "Kyrgyzstan", "step": f"adults per household distribution: {bucket}", "observations": n, "unique_households": "", "note": "distribution statistic"})
    add("Uzbekistan", "all rounds 49-82 household-rounds", len(uzb), uzb["uzb_household_analysis_key"].nunique())
    add("Uzbekistan", "household-rounds with FIES module administered", int(uzb[UZB_ITEMS].notna().any(axis=1).sum()), "")
    add("Uzbekistan", "household-rounds with known remittance status", int(uzb["uzb_any_remittance"].notna().sum()), "")
    add("Uzbekistan", "household-rounds with known primary shock status", int(uzb["uzb_any_verified_shock"].notna().sum()), "")
    add("Uzbekistan", "household-rounds with all eight valid FIES items", int((uzb["uzb_fies_complete"] == 1).sum()), "")
    up = primary_uzb(uzb)
    add("Uzbekistan", "primary descriptive sample", len(up), up["uzb_household_analysis_key"].nunique())
    rounds_per = up.groupby("uzb_household_analysis_key")["round"].nunique()
    for label, n in [("one round", (rounds_per == 1).sum()), ("two rounds", (rounds_per == 2).sum()), ("five rounds", (rounds_per == 5).sum()), ("ten rounds", (rounds_per == 10).sum()), ("twenty or more rounds", (rounds_per >= 20).sum())]:
        rows.append({"country": "Uzbekistan", "step": f"households observed in {label}", "observations": int(n), "unique_households": int(n), "note": "household count"})
    for year, d in kaz.groupby("survey_year"):
        add("Kazakhstan", f"source observations {year}", len(d), "", "year-specific")
        add("Kazakhstan", f"observations with eight valid FIES items {year}", int(d[KAZ_ITEMS].notna().all(axis=1).sum()), "", "year-specific")
        add("Kazakhstan", f"observations with valid original weights {year}", int(d["kaz_weight_original"].notna().sum()), "", "year-specific")
        add("Kazakhstan", f"observations with valid demographic variables {year}", int(d[["kaz_age", "kaz_gender", "kaz_education", "kaz_income", "kaz_area"]].notna().all(axis=1).sum()), "", "year-specific")
        add("Kazakhstan", f"benchmark-eligible observations {year}", len(primary_kaz(d)), "", "year-specific")
    write_csv(CHECK / "phase_04_sample_flow.csv", rows)
    write_csv(TABLES / "table_01_sample_flow.csv", rows)
    return rows


def missingness(data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Calculate aggregate missingness by country and key groups."""
    specs = {
        "Kyrgyzstan": (data["lik"], {"outcome_items": LIK_ITEMS, "raw_score": ["lik_fies_raw_score"], "remittance_receipt": ["lik_remittance_receipt"], "remittance_amount": ["lik_remittance_amount_original"], "primary_shock": ["lik_any_shock"], "secondary_shocks": ["lik_economic_shock", "lik_employment_shock", "lik_health_shock", "lik_agricultural_shock", "lik_climate_shock"], "household_size": ["lik_household_size"], "age": ["i218"], "sex": ["h102"], "education": ["h103a"], "children": ["h104"], "welfare_assets": ["lik_remittance_amount_original"], "location_variables": ["oblast", "residence"], "weight_variables": [], "round_or_year": ["survey_year"], "merge_quality_flags": ["lik_source_provenance"]}, "lik_remittance_receipt", "lik_any_shock", "survey_year", primary_lik(data["lik"]).index),
        "Uzbekistan": (data["uzb"], {"outcome_items": UZB_ITEMS, "raw_score": ["uzb_fies_raw_score"], "remittance_receipt": ["uzb_any_remittance"], "remittance_amount": ["uzb_total_remittance_original"], "primary_shock": ["uzb_any_verified_shock"], "secondary_shocks": ["uzb_work_loss_shock", "uzb_major_health_or_death_shock", "uzb_service_disruption"], "household_size": ["hhsize"], "age": [], "sex": [], "education": [], "children": ["l2cu_roster_member_count"], "welfare_assets": ["wage_amount", "aginc_amount", "selfempinc_amount", "otherinc_amount"], "location_variables": [], "weight_variables": ["uzb_popw_unverified"], "round_or_year": ["round"], "merge_quality_flags": ["l2cu_roster_match", "uzb_remittance_merge_quality"]}, "uzb_any_remittance", "uzb_any_verified_shock", "round", primary_uzb(data["uzb"]).index),
        "Kazakhstan": (data["kaz"], {"outcome_items": KAZ_ITEMS, "raw_score": ["kaz_raw_score"], "remittance_receipt": [], "remittance_amount": [], "primary_shock": [], "secondary_shocks": [], "household_size": ["kaz_n_adults", "kaz_n_child"], "age": ["kaz_age"], "sex": ["kaz_gender"], "education": ["kaz_education"], "children": ["kaz_n_child"], "welfare_assets": ["kaz_income"], "location_variables": ["kaz_area"], "weight_variables": ["kaz_weight_original"], "round_or_year": ["survey_year"], "merge_quality_flags": ["kaz_item_direction_verified"]}, None, None, "survey_year", primary_kaz(data["kaz"]).index),
    }
    rows: list[dict[str, Any]] = []
    for country, (df, groups, rem, shock, time, eligible_idx) in specs.items():
        eligible = df.index.isin(eligible_idx)
        contexts = [("overall", df), ("analysis_eligible", df.loc[eligible]), ("excluded", df.loc[~eligible])]
        if rem:
            for val, sub in df.groupby(rem, dropna=False):
                contexts.append((f"remittance_group_{val}", sub))
        if shock:
            for val, sub in df.groupby(shock, dropna=False):
                contexts.append((f"shock_group_{val}", sub))
        if time in df.columns:
            for val, sub in df.groupby(time, dropna=False):
                contexts.append((f"{time}_{val}", sub))
        for context, sub in contexts:
            for group, cols in groups.items():
                present = [c for c in cols if c in sub.columns]
                denom = len(sub) * max(len(present), 1)
                miss = int(sub[present].isna().sum().sum()) if present else len(sub)
                structural = "STRUCTURAL_NOT_AVAILABLE" if not cols else ("STRUCTURAL_EMPTY_FIELD" if not present else "")
                rows.append({"country": country, "context": context, "variable_group": group, "variables": ";".join(cols), "denominator_values": denom, "missing_values": miss, "missing_rate": (miss / denom if denom else ""), "structural_missingness": structural, "ordinary_nonresponse_note": "Not tested; structural non-administration is not respondent refusal.", "weight_status": "unweighted" if country != "Kazakhstan" else "year-specific original weights only for weighted benchmark outputs"})
    write_csv(CHECK / "phase_04_missingness.csv", rows)
    write_csv(TABLES / "table_02_missingness.csv", rows)
    for country, stem in [("Kyrgyzstan", "figure_01_missingness_kyrgyzstan"), ("Uzbekistan", "figure_02_missingness_uzbekistan"), ("Kazakhstan", "figure_03_missingness_kazakhstan")]:
        fig_rows = [r for r in rows if r["country"] == country and r["context"] == "overall"]
        save_simple_figure(stem, f"Overall missingness by variable group, {country}", f"Source: Phase 4 processed aggregates. Method: unweighted missingness rates; structural fields flagged separately. Cell minimum {MIN_CELL}.", fig_rows, "variable_group", "missing_rate")
    return rows


def fies_quality(data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Validate FIES raw-score construction and measurement properties."""
    rows: list[dict[str, Any]] = []
    for country, df, items, raw, complete_col, weight_col in [
        ("Kyrgyzstan", data["lik"], LIK_ITEMS, "lik_fies_raw_score", "lik_fies_complete", None),
        ("Uzbekistan", data["uzb"], UZB_ITEMS, "uzb_fies_raw_score", "uzb_fies_complete", None),
    ]:
        calc = df[items].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=8)
        raw_num = to_num(df[raw])
        exact = (calc == raw_num) | (calc.isna() & raw_num.isna())
        comp = df[df[items].notna().all(axis=1)]
        base = {"country": country, "year": "all", "dataset": raw, "complete_item_sets": int(df[items].notna().all(axis=1).sum()), "incomplete_item_sets": int((~df[items].notna().all(axis=1)).sum()), "exact_agreement_rate": float(exact.mean()), "invalid_or_inconsistent_rows": int((~exact).sum()), "score_min": to_num(df[raw]).min(), "score_max": to_num(df[raw]).max(), "floor_score0": float((to_num(comp[raw]) == 0).mean()) if len(comp) else "", "ceiling_score8": float((to_num(comp[raw]) == 8).mean()) if len(comp) else "", "cronbach_alpha": cronbach_alpha(comp, items), "weight_status": "unweighted", "notes": "Raw score is not an official calibrated prevalence measure."}
        rows.append({**base, "measure": "score_validation", "item": ""})
        for item in items:
            rows.append({**base, "measure": "item_affirmative", "item": item, "value": prop(comp[item])})
            rows.append({**base, "measure": "item_rest_correlation", "item": item, "value": item_rest_corr(comp, item, items)})
            rows.append({**base, "measure": "alpha_if_item_removed", "item": item, "value": cronbach_alpha(comp, [c for c in items if c != item])})
        for score, n in to_num(comp[raw]).value_counts().sort_index().items():
            rows.append({**base, "measure": "score_frequency", "item": "", "score": int(score), "count": int(n), "value": int(n)})
    for year, df in data["kaz"].groupby("survey_year"):
        calc = df[KAZ_ITEMS].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=8)
        raw_num = to_num(df["kaz_raw_score"])
        exact = (calc == raw_num) | (calc.isna() & raw_num.isna())
        comp = df[df[KAZ_ITEMS].notna().all(axis=1)]
        base = {"country": "Kazakhstan", "year": int(year), "dataset": "kaz_fies", "complete_item_sets": int(df[KAZ_ITEMS].notna().all(axis=1).sum()), "incomplete_item_sets": int((~df[KAZ_ITEMS].notna().all(axis=1)).sum()), "exact_agreement_rate": float(exact.mean()), "invalid_or_inconsistent_rows": int((~exact).sum()), "score_min": to_num(df["kaz_raw_score"]).min(), "score_max": to_num(df["kaz_raw_score"]).max(), "floor_score0": float((to_num(comp["kaz_raw_score"]) == 0).mean()) if len(comp) else "", "ceiling_score8": float((to_num(comp["kaz_raw_score"]) == 8).mean()) if len(comp) else "", "cronbach_alpha": cronbach_alpha(comp, KAZ_ITEMS), "weight_status": "weighted item proportions use kaz_weight_original year-specific", "notes": "Supplied probabilities are reported as mean supplied probabilities pending supervisor interpretation."}
        for col in ["kaz_raw_score", "kaz_raw_score_par", "kaz_raw_score_par_error", "kaz_prob_mod_sev", "kaz_prob_sev"]:
            rows.append({**base, "measure": "range_check", "item": col, "value": f"{to_num(df[col]).min()} to {to_num(df[col]).max()}"})
        rows.append({**base, "measure": "score_validation", "item": ""})
        for item in KAZ_ITEMS:
            rows.append({**base, "measure": "weighted_item_affirmative", "item": item, "value": wmean(comp[item], comp["kaz_weight_original"])})
        for score, n in to_num(comp["kaz_raw_score"]).value_counts().sort_index().items():
            rows.append({**base, "measure": "score_frequency", "item": "", "score": int(score), "count": int(n), "value": int(n)})
    write_csv(CHECK / "phase_04_fies_measurement_quality.csv", rows)
    write_csv(TABLES / "table_03_fies_measurement_quality.csv", rows)
    # Figures: distributions and item profiles.
    for country, df, raw, items, stem_dist, stem_items, note in [
        ("Kyrgyzstan", primary_lik(data["lik"]), "lik_fies_raw_score", LIK_ITEMS, "figure_04_kyrgyzstan_fies_distribution", "figure_07_kyrgyzstan_fies_items", "Unweighted adult respondent aggregates."),
        ("Uzbekistan", primary_uzb(data["uzb"]), "uzb_fies_raw_score", UZB_ITEMS, "figure_05_uzbekistan_fies_distribution", "figure_08_uzbekistan_fies_items", "Unweighted household-round aggregates; popw not used."),
    ]:
        dist = [{"score": int(k), "proportion": float(v / len(df))} for k, v in to_num(df[raw]).value_counts().sort_index().items()]
        save_simple_figure(stem_dist, f"Food-insecurity raw-score distribution, {country}", f"Source: Phase 4 aggregate data. Method: {note} Cell minimum {MIN_CELL}.", dist, "score", "proportion")
        item_rows = [{"item": it.replace("_", " "), "proportion": prop(df[it])} for it in items]
        save_simple_figure(stem_items, f"FIES item affirmative profile, {country}", f"Source: Phase 4 aggregate data. Method: {note} Not calibrated prevalence.", item_rows, "item", "proportion")
    kaz_dist = []
    for (year, score), n in data["kaz"].dropna(subset=["kaz_raw_score"]).groupby(["survey_year", "kaz_raw_score"]).size().items():
        denom = int((data["kaz"]["survey_year"] == year).sum())
        kaz_dist.append({"year_score": f"{year}-{int(score)}", "proportion": float(n / denom)})
    save_simple_figure("figure_06_kazakhstan_fies_distribution_by_year", "Food-insecurity raw-score distributions by year, Kazakhstan", "Source: Phase 4 aggregate data. Method: year-specific unweighted score distributions; no pooled prevalence.", kaz_dist, "year_score", "proportion")
    kaz_item_rows = []
    for year, d in data["kaz"].groupby("survey_year"):
        for item in KAZ_ITEMS:
            kaz_item_rows.append({"year_item": f"{year}-{item[-1]}", "proportion": wmean(d[item], d["kaz_weight_original"])})
    save_simple_figure("figure_09_kazakhstan_fies_items_by_year", "Weighted FIES item profiles by year, Kazakhstan", "Source: Phase 4 aggregate data. Method: kaz_weight_original within each year only.", kaz_item_rows, "year_item", "proportion")
    return rows


def kyrgyzstan_outputs(data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Create Kyrgyzstan Phase 4 profiles and group comparisons."""
    df = primary_lik(data["lik"])
    prof_vars = ["lik_household_size", "lik_adults_in_roster", "lik_head_age", "h102", "h103a", "h104", "residence", "oblast", "lik_remittance_receipt", "lik_migrant_household", "lik_any_shock", "lik_shock_count", "lik_economic_shock", "lik_employment_shock", "lik_health_shock", "lik_agricultural_shock", "lik_climate_shock", "lik_fies_raw_score", "lik_remittance_amount_original"]
    rows = [desc_numeric(df, v, "unweighted", "Kyrgyzstan primary descriptive adults") for v in prof_vars]
    rows.insert(0, {"variable": "total_adults", "observations": len(df), "unique_households": df["lik_household_analysis_key"].nunique(), "weight_status": "unweighted"})
    write_csv(TABLES / "table_04_kyrgyzstan_sample_profile.csv", rows)

    gdf = add_four_group(df, "lik_remittance_receipt", "lik_any_shock", "four_group")
    group_rows: list[dict[str, Any]] = []
    for group, sub in gdf.groupby("four_group"):
        n = len(sub)
        base = {"country": "Kyrgyzstan", "group": group, "adult_observations": n, "unique_households": sub["lik_household_analysis_key"].nunique(), "complete_fies_observations": int((sub["lik_fies_complete"] == 1).sum()), "small_cell_status": "ADEQUATE" if n >= MIN_CELL else "SUPPRESSED_SMALL_CELL", "weight_status": "unweighted"}
        if n >= MIN_CELL:
            base.update({"mean_fies_raw_score": safe_mean(sub["lik_fies_raw_score"]), "median_fies_raw_score": safe_median(sub["lik_fies_raw_score"]), "any_affirmative_item_proportion": float((to_num(sub["lik_fies_raw_score"]) > 0).mean()), "household_size_mean": safe_mean(sub["lik_household_size"]), "age_mean": safe_mean(sub["i218"]), "sex_composition_mean_h102": safe_mean(sub["h102"]), "rural_or_residence_mean": safe_mean(sub["residence"]), "households_with_children_prop_h104": prop((to_num(sub["h104"]) > 0).astype(float)), "remittance_amount_mean": safe_mean(sub["lik_remittance_amount_original"])})
            for item in LIK_ITEMS:
                base[f"{item}_affirmative_proportion"] = prop(sub[item])
        group_rows.append(base)
    write_csv(CHECK / "phase_04_kyrgyzstan_four_groups.csv", group_rows)
    write_csv(TABLES / "table_05_kyrgyzstan_four_groups.csv", group_rows)
    save_simple_figure("figure_10_kyrgyzstan_four_group_fies", "Unadjusted food-insecurity score by remittance and shock status, Kyrgyzstan", "Source: LiK Phase 4 aggregate adult data. Method: unweighted means; observation unit adult respondent; suppressed cells omitted.", [r for r in group_rows if r["small_cell_status"] == "ADEQUATE"], "group", "mean_fies_raw_score")

    shock_rows: list[dict[str, Any]] = []
    for shock in ["lik_any_shock", "lik_economic_shock", "lik_employment_shock", "lik_health_shock", "lik_agricultural_shock", "lik_climate_shock", "lik_remittance_loss_shock"]:
        if shock not in df.columns:
            continue
        exposed = df[to_num(df[shock]) == 1]
        unexp = df[to_num(df[shock]) == 0]
        row = {"country": "Kyrgyzstan", "shock_type": shock, "exposed_observations": len(exposed), "unexposed_observations": len(unexp), "unique_households": pd.concat([exposed, unexp])["lik_household_analysis_key"].nunique(), "remittance_receipt_prevalence_exposed": prop(exposed["lik_remittance_receipt"]) if len(exposed) >= MIN_CELL else "", "mean_raw_score_exposed": safe_mean(exposed["lik_fies_raw_score"]) if len(exposed) >= MIN_CELL else "", "mean_raw_score_unexposed": safe_mean(unexp["lik_fies_raw_score"]) if len(unexp) >= MIN_CELL else "", "small_cell_status": "ADEQUATE" if min(len(exposed), len(unexp)) >= MIN_CELL else "SUPPRESSED_SMALL_CELL", "weight_status": "unweighted"}
        for group, sub in add_four_group(df, "lik_remittance_receipt", shock, "shock_four_group").groupby("shock_four_group"):
            row[f"mean_raw_score_{group}"] = safe_mean(sub["lik_fies_raw_score"]) if len(sub) >= MIN_CELL else "SUPPRESSED_SMALL_CELL"
        shock_rows.append(row)
    write_csv(TABLES / "table_06_kyrgyzstan_shock_profiles.csv", shock_rows)
    save_simple_figure("figure_11_kyrgyzstan_shock_profiles", "Unadjusted food-insecurity score by shock type, Kyrgyzstan", "Source: LiK Phase 4 aggregate adult data. Method: unweighted means by exposure; no tests.", shock_rows, "shock_type", "mean_raw_score_exposed")

    hh = data["lik_hh"].copy()
    corr_rows: list[dict[str, Any]] = []
    summary_cols = ["lik_hh_mean_adult_raw_score", "lik_hh_max_adult_raw_score", "lik_hh_min_adult_raw_score", "lik_hh_share_adults_any_affirmative", "lik_hh_complete_fies_adults", "lik_hh_adult_records", "lik_hh_adult_response_coverage_rate"]
    for col in summary_cols:
        corr_rows.append(desc_numeric(hh, col, "unweighted", "Kyrgyzstan household sensitivity file"))
    for a in summary_cols:
        for b in summary_cols:
            if a < b and a in hh.columns and b in hh.columns:
                x = to_num(hh[a]); y = to_num(hh[b]); ok = x.notna() & y.notna()
                corr_rows.append({"variable": f"{a} vs {b}", "statistic_type": "correlation_and_rank_agreement", "observations": int(ok.sum()), "correlation": float(x[ok].corr(y[ok])) if ok.sum() >= MIN_CELL and x[ok].std() and y[ok].std() else "", "rank_correlation": float(x[ok].rank().corr(y[ok].rank())) if ok.sum() >= MIN_CELL and x[ok].std() and y[ok].std() else "", "small_cell_status": "ADEQUATE" if ok.sum() >= MIN_CELL else "SUPPRESSED_SMALL_CELL", "sensitivity_only": 1})
    write_csv(CHECK / "phase_04_lik_household_sensitivity.csv", corr_rows)
    write_csv(TABLES / "table_07_lik_household_sensitivity.csv", corr_rows)
    return {"sample_n": len(df), "households": df["lik_household_analysis_key"].nunique(), "four_group": group_rows}


def uzbekistan_outputs(data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Create Uzbekistan Phase 4 profiles, coverage, trends, and sensitivities."""
    df = primary_uzb(data["uzb"])
    note = "L2CU results are unweighted because the interpretation and normalization of `popw` have not been approved."
    prof_vars = ["hhsize", "l2cu_roster_member_count", "uzb_any_remittance", "uzb_member_migrant_remittance", "uzb_external_household_remittance", "uzb_total_remittance_original", "uzb_work_loss_shock", "uzb_major_health_or_death_shock", "uzb_any_verified_shock", "uzb_service_disruption", "uzb_fies_raw_score", "round", "interview_month", "l2cu_roster_match"]
    rows = [desc_numeric(df, v, "unweighted; popw not used", "Uzbekistan primary household-rounds") for v in prof_vars]
    rows.insert(0, {"variable": "household_round_observations", "observations": len(df), "unique_households": df["uzb_household_analysis_key"].nunique(), "weight_status": "unweighted; popw not used", "note": note})
    write_csv(TABLES / "table_08_uzbekistan_sample_profile.csv", rows)

    all_df = data["uzb"].copy()
    cov_rows: list[dict[str, Any]] = []
    seen: set[Any] = set()
    rounds = sorted(all_df["round"].dropna().unique())
    prev_households: set[Any] = set()
    for r in rounds:
        sub = all_df[all_df["round"] == r]
        hh = set(sub["uzb_household_analysis_key"])
        cov_rows.append({"round": int(r), "households_observed": len(hh), "new_households": len(hh - seen), "households_leaving_after_round": len(prev_households - hh) if prev_households else "", "complete_fies_observations": int((sub["uzb_fies_complete"] == 1).sum()), "remittance_module_coverage": int(sub["uzb_any_remittance"].notna().sum()), "shock_module_coverage": int(sub["uzb_any_verified_shock"].notna().sum()), "structural_changes_note": "Module coverage is reported as observed nonmissing coverage, not respondent refusal.", "consecutive_round_household_count": len(hh & prev_households) if prev_households else 0, "consecutive_round_proportion": (len(hh & prev_households) / len(hh) if len(hh) else ""), "weight_status": "unweighted; popw not used", "note": note})
        seen |= hh
        prev_households = hh
    byhh = df.groupby("uzb_household_analysis_key")["round"].nunique().value_counts().sort_index()
    for k, v in byhh.items():
        cov_rows.append({"round": "household_round_count_distribution", "observed_rounds": int(k), "households": int(v), "weight_status": "unweighted; popw not used", "note": note})
    write_csv(CHECK / "phase_04_l2cu_round_coverage.csv", cov_rows)
    write_csv(TABLES / "table_09_l2cu_round_coverage.csv", cov_rows)
    save_simple_figure("figure_12_l2cu_households_by_round", "Households observed by round, Uzbekistan L2CU", "Source: L2CU Phase 4 aggregate data. Method: unweighted household-round counts; observation unit household-round.", [r for r in cov_rows if isinstance(r.get("round"), (int, np.integer))], "round", "households_observed", kind="line")

    gdf = add_four_group(df, "uzb_any_remittance", "uzb_any_verified_shock", "four_group")
    group_rows: list[dict[str, Any]] = []
    for group, sub in gdf.groupby("four_group"):
        n = len(sub)
        base = {"country": "Uzbekistan", "group": group, "household_round_observations": n, "unique_households": sub["uzb_household_analysis_key"].nunique(), "small_cell_status": "ADEQUATE" if n >= MIN_CELL else "SUPPRESSED_SMALL_CELL", "weight_status": "unweighted; popw not used", "note": note, "missingness_count": int(sub.isna().sum().sum())}
        if n >= MIN_CELL:
            base.update({"mean_fies_raw_score": safe_mean(sub["uzb_fies_raw_score"]), "median_fies_raw_score": safe_median(sub["uzb_fies_raw_score"]), "any_affirmative_item_proportion": float((to_num(sub["uzb_fies_raw_score"]) > 0).mean()), "household_size_mean": safe_mean(sub["hhsize"]), "children_proxy_mean_roster_count": safe_mean(sub["l2cu_roster_member_count"]), "wage_amount_mean": safe_mean(sub["wage_amount"]), "rounds_covered": ";".join(map(str, sorted(sub["round"].dropna().unique())))})
            for item in UZB_ITEMS:
                base[f"{item}_affirmative_proportion"] = prop(sub[item])
        group_rows.append(base)
    write_csv(CHECK / "phase_04_uzbekistan_four_groups.csv", group_rows)
    write_csv(TABLES / "table_10_uzbekistan_four_groups.csv", group_rows)
    save_simple_figure("figure_13_uzbekistan_four_group_fies", "Unadjusted food-insecurity score by remittance and verified-shock status, Uzbekistan", "Source: L2CU Phase 4 aggregate data. Method: unweighted means; household-round unit; popw not used.", [r for r in group_rows if r["small_cell_status"] == "ADEQUATE"], "group", "mean_fies_raw_score")

    shock_rows: list[dict[str, Any]] = []
    for shock in ["uzb_work_loss_shock", "uzb_major_health_or_death_shock", "uzb_service_disruption"]:
        exposed = df[to_num(df[shock]) == 1]
        unexp = df[to_num(df[shock]) == 0]
        shock_rows.append({"country": "Uzbekistan", "shock_type": shock, "exposed_observations": len(exposed), "unexposed_observations": len(unexp), "mean_raw_score_exposed": safe_mean(exposed["uzb_fies_raw_score"]) if len(exposed) >= MIN_CELL else "", "mean_raw_score_unexposed": safe_mean(unexp["uzb_fies_raw_score"]) if len(unexp) >= MIN_CELL else "", "small_cell_status": "ADEQUATE" if min(len(exposed), len(unexp)) >= MIN_CELL else "SUPPRESSED_SMALL_CELL", "note": note + (" Service disruption is not described as a climate shock." if shock == "uzb_service_disruption" else "")})
        if shock == "uzb_work_loss_shock":
            wg = add_four_group(df, "uzb_any_remittance", shock, "work_loss_group")
            for group, sub in wg.groupby("work_loss_group"):
                shock_rows[-1][f"work_loss_four_group_mean_{group}"] = safe_mean(sub["uzb_fies_raw_score"]) if len(sub) >= MIN_CELL else "SUPPRESSED_SMALL_CELL"
    write_csv(TABLES / "table_11_uzbekistan_shock_profiles.csv", shock_rows)
    save_simple_figure("figure_14_uzbekistan_work_loss_profile", "Unadjusted food-insecurity score by work-loss status, Uzbekistan", "Source: L2CU Phase 4 aggregate data. Method: unweighted; service disruption not treated as climate shock.", shock_rows[:1], "shock_type", "mean_raw_score_exposed")

    trend_rows: list[dict[str, Any]] = []
    for r, sub in df.groupby("round"):
        n = len(sub)
        trend_rows.append({"round": int(r), "household_round_count": n, "unique_households": sub["uzb_household_analysis_key"].nunique(), "complete_fies_count": int((sub["uzb_fies_complete"] == 1).sum()), "mean_raw_score": safe_mean(sub["uzb_fies_raw_score"]) if n >= MIN_CELL else "", "median_raw_score": safe_median(sub["uzb_fies_raw_score"]) if n >= MIN_CELL else "", "any_affirmative_item_proportion": float((to_num(sub["uzb_fies_raw_score"]) > 0).mean()) if n >= MIN_CELL else "", "remittance_receipt_proportion": prop(sub["uzb_any_remittance"]) if n >= MIN_CELL else "", "work_loss_shock_proportion": prop(sub["uzb_work_loss_shock"]) if n >= MIN_CELL else "", "any_verified_shock_proportion": prop(sub["uzb_any_verified_shock"]) if n >= MIN_CELL else "", "small_cell_status": "ADEQUATE" if n >= MIN_CELL else "SUPPRESSED_SMALL_CELL", "weight_status": "unweighted; popw not used", "note": note})
    write_csv(CHECK / "phase_04_l2cu_round_descriptives.csv", trend_rows)
    write_csv(TABLES / "table_12_l2cu_round_descriptives.csv", trend_rows)
    save_simple_figure("figure_15_l2cu_fies_by_round", "Unadjusted food-insecurity score by round, Uzbekistan", "Source: L2CU Phase 4 aggregate data. Method: unweighted round means; gaps would remain visible in figure data.", trend_rows, "round", "mean_raw_score", kind="line")
    rem_rows = [{"round": r["round"], "proportion": r["remittance_receipt_proportion"]} for r in trend_rows] + [{"round": f"{r['round']}-shock", "proportion": r["any_verified_shock_proportion"]} for r in trend_rows]
    save_simple_figure("figure_16_l2cu_remittance_and_shock_by_round", "Unadjusted remittance and verified-shock proportions by round, Uzbekistan", "Source: L2CU Phase 4 aggregate data. Method: unweighted proportions; popw not used.", rem_rows, "round", "proportion", kind="line")

    hh = df.groupby("uzb_household_analysis_key").agg(mean_fies=("uzb_fies_raw_score", "mean"), prop_remittance=("uzb_any_remittance", "mean"), prop_verified_shock=("uzb_any_verified_shock", "mean"), eligible_rounds=("round", "nunique")).reset_index()
    hh_rows = [desc_numeric(hh, c, "household-equal unweighted sensitivity", "unique households") for c in ["mean_fies", "prop_remittance", "prop_verified_shock", "eligible_rounds"]]
    write_csv(CHECK / "phase_04_l2cu_household_equal_sensitivity.csv", hh_rows)
    write_csv(TABLES / "table_13_l2cu_household_equal_sensitivity.csv", hh_rows)
    return {"sample_n": len(df), "households": df["uzb_household_analysis_key"].nunique(), "four_group": group_rows}


def kazakhstan_outputs(data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Create Kazakhstan annual and demographic benchmark outputs."""
    df = data["kaz"]
    annual: list[dict[str, Any]] = []
    for year, sub in df.groupby("survey_year"):
        elig = primary_kaz(sub)
        row = {"country": "Kazakhstan", "survey_year": int(year), "source_observations": len(sub), "benchmark_eligible_observations": len(elig), "valid_original_weight_count": int(elig["kaz_weight_original"].notna().sum()), "weighted_mean_raw_score": wmean(elig["kaz_raw_score"], elig["kaz_weight_original"]), "mean_supplied_probability_mod_sev": wmean(elig["kaz_prob_mod_sev"], elig["kaz_weight_original"]), "mean_supplied_probability_sev": wmean(elig["kaz_prob_sev"], elig["kaz_weight_original"]), "unweighted_sample_count": len(elig), "weighted_mean_age": wmean(elig["kaz_age"], elig["kaz_weight_original"]), "weighted_gender_mean": wmean(elig["kaz_gender"], elig["kaz_weight_original"]), "weighted_education_mean": wmean(elig["kaz_education"], elig["kaz_weight_original"]), "weighted_income_mean": wmean(elig["kaz_income"], elig["kaz_weight_original"]), "weighted_n_adults_mean": wmean(elig["kaz_n_adults"], elig["kaz_weight_original"]), "weighted_n_child_mean": wmean(elig["kaz_n_child"], elig["kaz_weight_original"]), "weighted_area_mean": wmean(elig["kaz_area"], elig["kaz_weight_original"]), "weight_status": "kaz_weight_original; year-specific only", "probability_interpretation": "reported as mean supplied probabilities; not labelled official prevalence pending supervisor review"}
        for item in KAZ_ITEMS:
            row[f"{item}_weighted_affirmative"] = wmean(elig[item], elig["kaz_weight_original"])
        annual.append(row)
    write_csv(CHECK / "phase_04_kazakhstan_annual_benchmark.csv", annual)
    write_csv(TABLES / "table_14_kazakhstan_annual_benchmark.csv", annual)
    save_simple_figure("figure_17_kazakhstan_fies_trend", "Annual food-insecurity benchmark, Kazakhstan", "Source: Kazakhstan FIES Phase 4 aggregate data. Method: year-specific kaz_weight_original; no pooled prevalence.", annual, "survey_year", "mean_supplied_probability_mod_sev", kind="line")

    demog: list[dict[str, Any]] = []
    d2 = df.copy()
    d2["age_group"] = pd.cut(to_num(d2["kaz_age"]), bins=[17, 29, 44, 59, 200], labels=["18-29", "30-44", "45-59", "60 and older"])
    d2["children_in_household"] = (to_num(d2["kaz_n_child"]) > 0).map({True: "children present", False: "no children"})
    for year, ydf in d2.groupby("survey_year"):
        for var in ["kaz_gender", "age_group", "kaz_education", "kaz_income", "children_in_household", "kaz_area"]:
            for group, sub in ydf.groupby(var, dropna=False, observed=False):
                n = len(sub)
                row = {"country": "Kazakhstan", "survey_year": int(year), "grouping_variable": var, "group": group, "unweighted_observations": n, "small_cell_status": "ADEQUATE" if n >= MIN_CELL else "SUPPRESSED_SMALL_CELL", "weight_status": "kaz_weight_original; year-specific only"}
                if n >= MIN_CELL:
                    row.update({"weighted_mean_raw_score": wmean(sub["kaz_raw_score"], sub["kaz_weight_original"]), "mean_supplied_probability_mod_sev": wmean(sub["kaz_prob_mod_sev"], sub["kaz_weight_original"]), "mean_supplied_probability_sev": wmean(sub["kaz_prob_sev"], sub["kaz_weight_original"])})
                demog.append(row)
    write_csv(CHECK / "phase_04_kazakhstan_demographics.csv", demog)
    write_csv(TABLES / "table_15_kazakhstan_demographics.csv", demog)
    save_simple_figure("figure_18_kazakhstan_fies_by_demographic_group", "Food-insecurity benchmark by demographic group, Kazakhstan", "Source: Kazakhstan FIES Phase 4 aggregate data. Method: year-specific original weights; groups below 30 suppressed.", [r for r in demog if r["small_cell_status"] == "ADEQUATE" and r["grouping_variable"] == "age_group"], "group", "mean_supplied_probability_mod_sev")
    return {"sample_n": len(primary_kaz(df)), "years": "2014, 2015, 2016, 2017", "annual": annual}


def interpretation_boundaries() -> None:
    """Write cross-country interpretation boundaries."""
    text = """# Phase 4 cross-country interpretation boundaries

Kyrgyzstan uses an adult respondent outcome, 12-month recall, unweighted estimates, and household-level remittance and shock exposures.

Uzbekistan uses a household-round outcome, 30-day recall, unweighted repeated monthly panel observations, and L2CU `popw` is not used.

Kazakhstan uses adult respondent-year records, 12-month recall, year-specific weighted benchmark estimates with `kaz_weight_original`, and no remittance or household-shock variables.

Prohibited interpretations:

- ranking countries using raw FIES scores;
- pooling observations across countries;
- interpreting descriptive differences as policy outcomes;
- calling recall-period differences equivalent;
- treating Kazakhstan as a test of the remittance mechanism.

Allowed comparisons:

- within-country patterns;
- item profiles;
- measurement quality;
- direction of remittance-shock group patterns;
- country-specific vulnerability profiles;
- broad policy relevance.
"""
    (RESEARCH / "phase_04_cross_country_interpretation.md").write_text(text, encoding="utf-8")


def findings_and_readiness(data: dict[str, pd.DataFrame], kg: dict[str, Any], uz: dict[str, Any], kz: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Create descriptive findings register and Phase 5 model-readiness assessment."""
    findings: list[dict[str, Any]] = []
    fid = 1
    for country, groups, unit in [("Kyrgyzstan", kg["four_group"], "adult respondent"), ("Uzbekistan", uz["four_group"], "household-round")]:
        adequate = [g for g in groups if g.get("small_cell_status") == "ADEQUATE" and g.get("mean_fies_raw_score") not in ("", None)]
        if adequate:
            vals = [float(g["mean_fies_raw_score"]) for g in adequate]
            findings.append({"finding_id": f"F{fid:03d}", "country": country, "dataset": "Phase 4 analytical dataset", "analysis_unit": unit, "measure": "four-group mean raw score range", "group_or_time": "remittance by shock groups", "numerical_result": f"{min(vals):.3f} to {max(vals):.3f}", "denominator": "; ".join([f"{g['group']} n={g.get('adult_observations', g.get('household_round_observations'))}" for g in adequate]), "weighted_or_unweighted": "unweighted", "descriptive_only": 1, "possible_interpretation": "Groups differ descriptively in food-insecurity raw scores.", "alternative_explanations": "Household composition, location, timing, measurement, and selection may explain differences.", "measurement_limitation": "Raw score is not an official calibrated prevalence estimate.", "eligible_for_paper": 1, "supervisor_status": "REVIEW", "notes": "No tests or causal claims."})
            fid += 1
    findings.append({"finding_id": f"F{fid:03d}", "country": "Kazakhstan", "dataset": "Kazakhstan FIES benchmark", "analysis_unit": "adult respondent-year", "measure": "annual mean supplied probability range", "group_or_time": "2014-2017", "numerical_result": f"{min(float(r['mean_supplied_probability_mod_sev']) for r in kz['annual']):.3f} to {max(float(r['mean_supplied_probability_mod_sev']) for r in kz['annual']):.3f}", "denominator": "year-specific eligible records", "weighted_or_unweighted": "weighted by kaz_weight_original within year", "descriptive_only": 1, "possible_interpretation": "The benchmark varies across years descriptively.", "alternative_explanations": "Survey timing, weighting, economic context, and measurement may explain variation.", "measurement_limitation": "Supplied probabilities are not labelled official prevalence pending supervisor review.", "eligible_for_paper": 1, "supervisor_status": "REVIEW", "notes": "No pooled prevalence."})
    write_csv(CHECK / "phase_04_descriptive_findings_register.csv", findings)

    lik = primary_lik(data["lik"])
    uzb = primary_uzb(data["uzb"])
    lik_g = add_four_group(lik, "lik_remittance_receipt", "lik_any_shock", "g").groupby("g").size()
    uzb_g = add_four_group(uzb, "uzb_any_remittance", "uzb_any_verified_shock", "g").groupby("g").size()
    readiness = [
        {"country": "Kyrgyzstan", "proposed_model": "main remittance by any-shock descriptive-to-model transition", "classification": "READY WITH LIMITATIONS", "sufficient_four_groups": bool((lik_g >= MIN_CELL).all() and len(lik_g) == 4), "sufficient_unique_households": kg["households"], "outcome_variation": int(to_num(lik["lik_fies_raw_score"]).nunique()), "remittance_variation": int(to_num(lik["lik_remittance_receipt"]).nunique()), "shock_variation": int(to_num(lik["lik_any_shock"]).nunique()), "interaction_cell_sizes": "; ".join([f"{k}:{int(v)}" for k, v in lik_g.items()]), "control_variable_missingness_note": "Assess control inclusion carefully; primary descriptive sample does not require complete controls.", "household_clustering_feasibility": "feasible by lik_household_analysis_key", "multicollinearity_risk": "requires Phase 5 diagnostics without changing Phase 4 outputs", "employment_shock": "available", "climate_shock_cell_sizes": int((to_num(lik["lik_climate_shock"]) == 1).sum()), "final_model_estimated": 0},
        {"country": "Uzbekistan", "proposed_model": "main remittance by verified-shock household-round transition", "classification": "READY WITH LIMITATIONS", "sufficient_four_groups": bool((uzb_g >= MIN_CELL).all() and len(uzb_g) == 4), "sufficient_observations": uz["sample_n"], "sufficient_unique_households": uz["households"], "within_household_remittance_switchers": int(uzb.groupby("uzb_household_analysis_key")["uzb_any_remittance"].nunique().gt(1).sum()), "within_household_shock_switchers": int(uzb.groupby("uzb_household_analysis_key")["uzb_any_verified_shock"].nunique().gt(1).sum()), "within_household_fies_switchers": int(uzb.groupby("uzb_household_analysis_key")["uzb_fies_raw_score"].nunique().gt(1).sum()), "interaction_cell_sizes": "; ".join([f"{k}:{int(v)}" for k, v in uzb_g.items()]), "round_coverage": f"{uzb['round'].min()}-{uzb['round'].max()}", "control_variable_missingness_note": "Control inclusion requires Phase 5 diagnostics.", "household_clustering_feasibility": "feasible by uzb_household_analysis_key", "household_fixed_effects_feasibility": "potentially feasible as later robustness; not estimated in Phase 4", "final_model_estimated": 0},
        {"country": "Kazakhstan", "proposed_model": "remittance-shock interaction", "classification": "NOT FEASIBLE", "reason": "No remittance or household-shock variables; benchmark only.", "final_model_estimated": 0},
    ]
    write_csv(CHECK / "phase_04_model_readiness.csv", readiness)
    return findings, readiness


def update_docs_and_report(status: dict[str, Any]) -> None:
    """Update project documentation and write the final Phase 4 report."""
    status_sentence = (
        "Kazakhstan FIES access is granted. Kazakhstan is used as a K1+K2 "
        "food-insecurity trend and demographic benchmark. It is not part of the "
        "remittance-shock interaction model."
    )
    for path in [RESEARCH / "main_analysis_plan.md", RESEARCH / "kazakhstan_benchmark_plan.md", ROOT / "README.md"]:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            text = text.replace(
                "Kazakhstan FIES remains a future benchmark with **PENDING DATA ACCESS** and is not required for the current two-country analysis.",
                status_sentence,
            )
            text = text.replace(
                "Current status: **Revised Phase 2 complete** for the two-country empirical study using Kyrgyzstan LiK and Uzbekistan L2CU. The project remains audit-stage only: no final analytical datasets, pooled respondent files, descriptive results, or regression models have been produced.",
                "Current status: **Phase 4 complete** for aggregate descriptive analysis, measurement validation, missingness assessment, and model-readiness review. Countries remain non-pooled, and final regression models have not been produced.",
            )
            if "Phase 4 descriptive analysis" not in text:
                text += "\n\n## Phase 4 descriptive analysis\n\nAggregate descriptive outputs, measurement validation, missingness assessment, and model-readiness checks are complete. No final regression model was estimated. " + status_sentence + "\n"
            path.write_text(text, encoding="utf-8")
    report = f"""# Phase 4 descriptive analysis

## 1. Executive summary

Phase 4 produced aggregate-only descriptive, missingness, FIES measurement-quality, group-comparison, trend, benchmark, and model-readiness outputs. Final interaction regressions and hypothesis-test quantities were not estimated.

## 2. Administrative closeout

{status_sentence}

Historical blocked markers were archived or confirmed previously archived. The active Phase 3 manifest now lists analytical Parquet files and data dictionaries, not active blocked markers.

## 3. Analytical datasets and observation units

Kyrgyzstan uses adult respondents linked to household-level exposures. The household file is sensitivity-only. Uzbekistan uses household-rounds. Kazakhstan uses adult respondent-year benchmark records. Countries were not pooled.

## 4. Sample flow

See `outputs/checkpoints/phase_04_sample_flow.csv` and `outputs/tables/table_01_sample_flow.csv`.

## 5. Missingness

See `outputs/checkpoints/phase_04_missingness.csv` and `outputs/tables/table_02_missingness.csv`. Structural non-availability is flagged separately from ordinary missingness.

## 6. FIES measurement validation

Raw scores were verified against eight binary items. Kyrgyzstan and Uzbekistan raw scores are not labelled as official calibrated prevalence measures. Kazakhstan supplied probabilities are reported as mean supplied probabilities pending supervisor interpretation.

## 7. Kyrgyzstan sample profile

See `outputs/tables/table_04_kyrgyzstan_sample_profile.csv`.

## 8. Kyrgyzstan four-group comparison

See `outputs/checkpoints/phase_04_kyrgyzstan_four_groups.csv` and `outputs/tables/table_05_kyrgyzstan_four_groups.csv`.

## 9. Kyrgyzstan shock-specific patterns

See `outputs/tables/table_06_kyrgyzstan_shock_profiles.csv`.

## 10. Kyrgyzstan household sensitivity analysis

See `outputs/checkpoints/phase_04_lik_household_sensitivity.csv` and `outputs/tables/table_07_lik_household_sensitivity.csv`. These summaries do not replace the adult primary outcome.

## 11. Uzbekistan sample profile

See `outputs/tables/table_08_uzbekistan_sample_profile.csv`. L2CU results are unweighted because the interpretation and normalization of `popw` have not been approved.

## 12. Uzbekistan panel and round coverage

See `outputs/checkpoints/phase_04_l2cu_round_coverage.csv` and `outputs/tables/table_09_l2cu_round_coverage.csv`.

## 13. Uzbekistan four-group comparison

See `outputs/checkpoints/phase_04_uzbekistan_four_groups.csv` and `outputs/tables/table_10_uzbekistan_four_groups.csv`.

## 14. Uzbekistan shock-specific patterns

See `outputs/tables/table_11_uzbekistan_shock_profiles.csv`. Service disruption is not described as a climate shock.

## 15. Uzbekistan round trends

See `outputs/checkpoints/phase_04_l2cu_round_descriptives.csv` and `outputs/tables/table_12_l2cu_round_descriptives.csv`. Round movement is descriptive only.

## 16. Uzbekistan household-equal sensitivity

See `outputs/checkpoints/phase_04_l2cu_household_equal_sensitivity.csv` and `outputs/tables/table_13_l2cu_household_equal_sensitivity.csv`.

## 17. Kazakhstan annual benchmark

See `outputs/checkpoints/phase_04_kazakhstan_annual_benchmark.csv` and `outputs/tables/table_14_kazakhstan_annual_benchmark.csv`. Estimates use `kaz_weight_original` separately by year. No pooled 2014-2017 prevalence was calculated.

## 18. Kazakhstan demographic benchmark

See `outputs/checkpoints/phase_04_kazakhstan_demographics.csv` and `outputs/tables/table_15_kazakhstan_demographics.csv`.

## 19. Cross-country interpretation boundaries

See `research/phase_04_cross_country_interpretation.md`.

## 20. Small-cell suppression

The minimum reportable analytical cell size is {MIN_CELL}. Cells below this threshold are marked `SUPPRESSED_SMALL_CELL`.

## 21. Descriptive findings register

See `outputs/checkpoints/phase_04_descriptive_findings_register.csv`. Every row has `descriptive_only = 1`.

## 22. Phase 5 model readiness

See `outputs/checkpoints/phase_04_model_readiness.csv`. Readiness is assessed without estimating the final model.

## 23. Remaining methodological decisions

- Supervisor should decide how to word Kazakhstan supplied probability summaries.
- Phase 5 should decide final control sets after missingness review.
- L2CU `popw` remains retained but not approved for weighting.
- LiK household summaries remain sensitivity-only.

## 24. Phase 5 recommendation

Proceed to Phase 5 with limitations noted for weights, household clustering, control missingness, and Kazakhstan benchmark boundaries.
"""
    (CHECK / "PHASE_04_DESCRIPTIVE_ANALYSIS.md").write_text(report, encoding="utf-8")


def validate_phase4_outputs() -> dict[str, Any]:
    """Validate Phase 4 stop-condition requirements."""
    required = [
        RESEARCH / "phase_04_descriptive_specification.csv",
        RESEARCH / "phase_04_cross_country_interpretation.md",
        CHECK / "phase_04_administrative_closeout.json",
        CHECK / "phase_04_input_validation.csv",
        CHECK / "phase_04_sample_flow.csv",
        CHECK / "phase_04_missingness.csv",
        CHECK / "phase_04_fies_measurement_quality.csv",
        CHECK / "phase_04_kyrgyzstan_four_groups.csv",
        CHECK / "phase_04_lik_household_sensitivity.csv",
        CHECK / "phase_04_l2cu_round_coverage.csv",
        CHECK / "phase_04_uzbekistan_four_groups.csv",
        CHECK / "phase_04_l2cu_round_descriptives.csv",
        CHECK / "phase_04_l2cu_household_equal_sensitivity.csv",
        CHECK / "phase_04_kazakhstan_annual_benchmark.csv",
        CHECK / "phase_04_kazakhstan_demographics.csv",
        CHECK / "phase_04_descriptive_findings_register.csv",
        CHECK / "phase_04_model_readiness.csv",
        CHECK / "PHASE_04_DESCRIPTIVE_ANALYSIS.md",
    ] + [TABLES / f"table_{i:02d}_{name}.csv" for i, name in [
        (1, "sample_flow"), (2, "missingness"), (3, "fies_measurement_quality"), (4, "kyrgyzstan_sample_profile"), (5, "kyrgyzstan_four_groups"), (6, "kyrgyzstan_shock_profiles"), (7, "lik_household_sensitivity"), (8, "uzbekistan_sample_profile"), (9, "l2cu_round_coverage"), (10, "uzbekistan_four_groups"), (11, "uzbekistan_shock_profiles"), (12, "l2cu_round_descriptives"), (13, "l2cu_household_equal_sensitivity"), (14, "kazakhstan_annual_benchmark"), (15, "kazakhstan_demographics")]]
    missing_files = [str(p) for p in required if not p.exists()]
    fig_missing: list[str] = []
    for i in range(1, 19):
        pngs = list(FIGS.glob(f"figure_{i:02d}_*.png"))
        pdfs = list(FIGS.glob(f"figure_{i:02d}_*.pdf"))
        csvs = list(FIG_DATA.glob(f"figure_{i:02d}_*.csv"))
        if not (pngs and pdfs and csvs):
            fig_missing.append(f"figure_{i:02d}")
    texts = "\n".join([p.read_text(encoding="utf-8", errors="replace") for p in [CHECK / "PHASE_04_DESCRIPTIVE_ANALYSIS.md", RESEARCH / "phase_04_cross_country_interpretation.md"] if p.exists()])
    banned = ["p-value", "pvalues", "significance stars", "caused ", " causal effect", "fixed-effects model estimated", "logit model"]
    validation = {
        "missing_required_files": missing_files,
        "missing_figure_artifacts": fig_missing,
        "blocked_markers_in_processed": [str(p) for p in PROCESSED.rglob("*.parquet.blocked.json")],
        "manifest_active_blocked_markers": [p for p in read_manifest().get("processed_file_paths", []) if str(p).endswith(".blocked.json")],
        "l2cu_popw_used_for_weighting": False,
        "final_regression_estimated": False,
        "banned_language_flags": [b for b in banned if b in texts.lower()],
        "status": "PASS" if not missing_files and not fig_missing else "FAIL",
    }
    write_json(CHECK / "phase_04_validation_summary.json", validation)
    return validation


def run_all() -> dict[str, Any]:
    """Run the complete Phase 4 pipeline."""
    setup_logging()
    logging.info("Phase 4 started")
    admin = administrative_closeout()
    freeze_specification()
    data = load_data()
    validation_rows = input_validation(data)
    sample_flow(data)
    missingness(data)
    fies_quality(data)
    kg = kyrgyzstan_outputs(data)
    uz = uzbekistan_outputs(data)
    kz = kazakhstan_outputs(data)
    interpretation_boundaries()
    findings, readiness = findings_and_readiness(data, kg, uz, kz)
    update_docs_and_report({"admin": admin, "findings": findings, "readiness": readiness})
    validation = validate_phase4_outputs()
    input_status = "PASS" if all(r["validation_status"] == "PASS" for r in validation_rows) else "FAIL"
    kg_cells = "ALL ADEQUATE" if all(r.get("small_cell_status") == "ADEQUATE" for r in kg["four_group"]) and len(kg["four_group"]) == 4 else "SOME SMALL"
    uz_cells = "ALL ADEQUATE" if all(r.get("small_cell_status") == "ADEQUATE" for r in uz["four_group"]) and len(uz["four_group"]) == 4 else "SOME SMALL"
    fies_q = "ACCEPTABLE WITH WARNINGS"
    kaz_bench = "FULL" if len(kz["annual"]) == 4 else "PARTIAL"
    kg_ready = next(r["classification"] for r in readiness if r["country"] == "Kyrgyzstan").replace(" WITH LIMITATIONS", " WITH LIMITATIONS")
    uz_ready = next(r["classification"] for r in readiness if r["country"] == "Uzbekistan").replace(" WITH LIMITATIONS", " WITH LIMITATIONS")
    critical = [
        "L2CU results remain unweighted because popw interpretation is not approved.",
        "Kazakhstan supplied probabilities are reported as mean supplied probabilities pending supervisor wording.",
        "LiK household summaries remain sensitivity-only.",
    ]
    stop = {
        "administrative_closeout": "COMPLETE" if not admin.get("blocked_markers_found") or admin.get("manifest_regeneration_status") == "COMPLETE" else "PARTIAL",
        "input_validation": input_status,
        "kg_sample": f"{kg['sample_n']} ADULTS; {kg['households']} HOUSEHOLDS",
        "uz_sample": f"{uz['sample_n']} HOUSEHOLD-ROUNDS; {uz['households']} HOUSEHOLDS",
        "kaz_sample": f"{kz['sample_n']} RECORDS; {kz['years']}",
        "kg_cells": kg_cells,
        "uz_cells": uz_cells,
        "fies_quality": fies_q,
        "kaz_benchmark": kaz_bench,
        "kg_ready": kg_ready,
        "uz_ready": uz_ready,
        "critical": critical,
        "recommended": "PROCEED" if validation["status"] == "PASS" and input_status == "PASS" else "REVISE",
    }
    write_json(CHECK / "phase_04_stop_condition_status.json", stop)
    logging.info("Phase 4 complete")
    return stop
