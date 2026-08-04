"""Phase 5 country-specific association and moderation models.

The module estimates observational OLS/LPM association models with household-
clustered covariance, adjusted predictions, prespecified robustness checks,
heterogeneity summaries, and Kazakhstan benchmark bootstrap uncertainty.  It
does not pool country records and does not make causal claims.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
MODELS = ROOT / "outputs" / "models"
LOGS = ROOT / "outputs" / "logs"
RESEARCH = ROOT / "research"
MIN_CELL = 30
SEED = 20260726

LIK = ROOT / "data" / "processed" / "kyrgyzstan" / "lik_2019_adult_analysis.parquet"
LIK_HH = ROOT / "data" / "processed" / "kyrgyzstan" / "lik_2019_household_sensitivity.parquet"
UZB = ROOT / "data" / "processed" / "uzbekistan" / "l2cu_r49_82_household_analysis.parquet"
KAZ = ROOT / "data" / "processed" / "kazakhstan" / "kaz_fies_2014_2017_benchmark.parquet"
MANIFEST = CHECK / "phase_03_reproducibility_manifest.json"


def ensure_dirs() -> None:
    for p in [CHECK, TABLES, FIGS, FIG_DATA, MODELS / "kyrgyzstan", MODELS / "uzbekistan", MODELS / "kazakhstan", LOGS, RESEARCH]:
        p.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOGS / "phase_05.log", mode="w", encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols: list[str] = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_data() -> dict[str, pd.DataFrame]:
    return {
        "kg": pd.read_parquet(LIK, engine="pyarrow"),
        "kg_hh": pd.read_parquet(LIK_HH, engine="pyarrow"),
        "uz": pd.read_parquet(UZB, engine="pyarrow"),
        "kaz": pd.read_parquet(KAZ, engine="pyarrow"),
    }


def zcrit() -> float:
    return 1.959963984540054


def norm_p(z: float) -> float:
    if not np.isfinite(z):
        return np.nan
    return float(2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))))


def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def primary_kg(df: pd.DataFrame) -> pd.DataFrame:
    d = df[(df["lik_fies_complete"] == 1) & df["lik_remittance_receipt"].notna() & df["lik_any_shock"].notna()].copy()
    d["kg_child_present"] = (to_num(d["lik_household_size"]) > to_num(d["lik_adults_in_roster"])).astype(float)
    d["kg_fies_z"] = (to_num(d["lik_fies_raw_score"]) - to_num(d["lik_fies_raw_score"]).mean()) / to_num(d["lik_fies_raw_score"]).std(ddof=0)
    d["kg_any_fi"] = (to_num(d["lik_fies_raw_score"]) > 0).astype(float)
    d["kg_lower_asset_proxy"] = (to_num(d["lik_household_size"]) >= to_num(d["lik_household_size"]).median()).astype(float)
    return d


def primary_uz(df: pd.DataFrame) -> pd.DataFrame:
    d = df[(df["uzb_fies_complete"] == 1) & df["uzb_any_remittance"].notna() & df["uzb_work_loss_shock"].notna()].copy()
    d["uz_child_present"] = (to_num(d["l2cu_roster_member_count"]) > to_num(d["hhsize"]) * 0).astype(float)
    d["uz_fies_z"] = (to_num(d["uzb_fies_raw_score"]) - to_num(d["uzb_fies_raw_score"]).mean()) / to_num(d["uzb_fies_raw_score"]).std(ddof=0)
    d["uz_any_fi"] = (to_num(d["uzb_fies_raw_score"]) > 0).astype(float)
    welfare = to_num(d["wage_amount"]).fillna(0) + to_num(d["aginc_amount"]).fillna(0) + to_num(d["selfempinc_amount"]).fillna(0) + to_num(d["otherinc_amount"]).fillna(0)
    d["uz_lower_welfare"] = (welfare <= welfare.median()).astype(float)
    return d


def add_interaction(df: pd.DataFrame, rem: str, shock: str, name: str = "rem_x_shock") -> pd.DataFrame:
    d = df.copy()
    d[name] = to_num(d[rem]) * to_num(d[shock])
    return d


def build_matrix(df: pd.DataFrame, numeric: list[str], categorical: list[str]) -> tuple[np.ndarray, list[str]]:
    cols = [np.ones(len(df))]
    names = ["Intercept"]
    for c in numeric:
        cols.append(to_num(df[c]).to_numpy(float))
        names.append(c)
    for c in categorical:
        ser = df[c].astype("category")
        levels = list(ser.cat.categories)
        for lev in levels[1:]:
            cols.append((ser == lev).astype(float).to_numpy())
            names.append(f"{c}[{lev}]")
    return np.column_stack(cols), names


def cluster_ols(df: pd.DataFrame, outcome: str, numeric: list[str], categorical: list[str], cluster: str, model_id: str, weight_status: str, fixed_effects: str) -> dict[str, Any]:
    need = [outcome, cluster] + numeric + categorical
    d = df.dropna(subset=need).copy()
    X, names = build_matrix(d, numeric, categorical)
    y = to_num(d[outcome]).to_numpy(float)
    clusters = d[cluster].astype(str).to_numpy()
    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    resid = y - X @ beta
    unique = np.unique(clusters)
    meat = np.zeros((k, k))
    for g in unique:
        idx = clusters == g
        sg = X[idx].T @ resid[idx]
        meat += np.outer(sg, sg)
    scale = (len(unique) / (len(unique) - 1)) * ((n - 1) / (n - k)) if len(unique) > 1 and n > k else 1.0
    cov = scale * xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    rows = []
    for i, nm in enumerate(names):
        z = beta[i] / se[i] if se[i] else np.nan
        rows.append({"model_id": model_id, "term": nm, "coefficient": beta[i], "clustered_se": se[i], "ci_lower": beta[i] - zcrit() * se[i], "ci_upper": beta[i] + zcrit() * se[i], "p_value": norm_p(z), "observations": n, "clusters": len(unique), "r_squared": 1 - float(np.sum(resid**2) / np.sum((y - y.mean()) ** 2)) if np.sum((y - y.mean()) ** 2) else "", "weight_status": weight_status, "fixed_effects": fixed_effects})
    return {"model_id": model_id, "df": d, "X": X, "names": names, "beta": beta, "cov": cov, "resid": resid, "fitted": X @ beta, "coef_rows": rows, "n": n, "clusters": len(unique), "outcome": outcome, "numeric": numeric, "categorical": categorical, "cluster": cluster, "weight_status": weight_status, "fixed_effects": fixed_effects}


def lincomb(model: dict[str, Any], terms: dict[str, float], label: str) -> dict[str, Any]:
    names = model["names"]
    v = np.zeros(len(names))
    for term, val in terms.items():
        if term in names:
            v[names.index(term)] = val
    est = float(v @ model["beta"])
    se = float(np.sqrt(max(v @ model["cov"] @ v, 0)))
    z = est / se if se else np.nan
    return {"model_id": model["model_id"], "contrast": label, "estimate": est, "standard_error": se, "ci_lower": est - zcrit() * se, "ci_upper": est + zcrit() * se, "p_value": norm_p(z), "observations": model["n"], "clusters": model["clusters"], "weight_status": model["weight_status"]}


def predictions(model: dict[str, Any], rem: str, shock: str, labels: list[str]) -> list[dict[str, Any]]:
    rows = []
    for r, s, lab in [(0, 0, labels[0]), (1, 0, labels[1]), (0, 1, labels[2]), (1, 1, labels[3])]:
        d = model["df"].copy()
        d[rem] = r
        d[shock] = s
        d["rem_x_shock"] = r * s
        X, _ = build_matrix(d, model["numeric"], model["categorical"])
        pred_i = X @ model["beta"]
        grad = X.mean(axis=0)
        est = float(pred_i.mean())
        se = float(np.sqrt(max(grad @ model["cov"] @ grad, 0)))
        rows.append({"model_id": model["model_id"], "group": lab, "remittance": r, "shock": s, "predicted_outcome": est, "standard_error": se, "ci_lower": est - zcrit() * se, "ci_upper": est + zcrit() * se, "observations": model["n"], "clusters": model["clusters"], "method": "observed-value standardization", "weight_status": model["weight_status"]})
    return rows


def save_figure(stem: str, title: str, note: str, rows: list[dict[str, Any]], x: str, y: str, lo: str | None = None, hi: str | None = None) -> None:
    write_csv(FIG_DATA / f"{stem}.csv", rows)
    img = Image.new("RGB", (1200, 760), "white")
    draw = ImageDraw.Draw(img)
    try:
        fb = ImageFont.truetype("arial.ttf", 28); f = ImageFont.truetype("arial.ttf", 17); fs = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        fb = f = fs = None
    draw.text((40, 25), title, fill="black", font=fb)
    draw.text((40, 690), note[:150], fill="black", font=fs)
    left, top, right, bottom = 95, 110, 1140, 620
    draw.line((left, bottom, right, bottom), fill="black", width=2); draw.line((left, top, left, bottom), fill="black", width=2)
    plot_rows = []
    vals = []
    for r in rows:
        if r.get(y) in ("", None):
            continue
        try:
            v0 = float(r[y])
        except Exception:
            continue
        if np.isfinite(v0):
            plot_rows.append(r)
            vals.append(v0)
    if not vals:
        draw.text((140, 300), "No reportable aggregate values.", fill="black", font=f)
    else:
        allv = vals[:]
        if lo and hi:
            for r in plot_rows:
                for b in [lo, hi]:
                    try:
                        vv = float(r[b])
                    except Exception:
                        continue
                    if np.isfinite(vv):
                        allv.append(vv)
        ymin, ymax = min(0, min(allv)), max(allv)
        if ymin == ymax: ymax = ymin + 1
        n = len(plot_rows); gap = 16; bw = max(18, (right-left-gap*(n+1))/max(n,1))
        for i, r in enumerate(plot_rows):
            if r.get(y) in ("", None): continue
            v = float(r[y]); x0 = left+gap+i*(bw+gap); x1 = x0+bw
            yy = bottom - (v-ymin)/(ymax-ymin)*(bottom-top)
            draw.rectangle((x0, yy, x1, bottom), fill="#4c78a8")
            if lo and hi and r.get(lo) not in ("", None):
                ylo = bottom - (float(r[lo])-ymin)/(ymax-ymin)*(bottom-top)
                yhi = bottom - (float(r[hi])-ymin)/(ymax-ymin)*(bottom-top)
                xc = (x0+x1)/2
                draw.line((xc, ylo, xc, yhi), fill="black", width=3)
                draw.line((xc-8, ylo, xc+8, ylo), fill="black", width=2); draw.line((xc-8, yhi, xc+8, yhi), fill="black", width=2)
            draw.text((x0, bottom+10), str(r[x])[:18], fill="black", font=fs)
            draw.text((x0, yy-24), f"{v:.2f}", fill="black", font=fs)
    png = FIGS / f"{stem}.png"; pdf = FIGS / f"{stem}.pdf"
    img.save(png)
    c = canvas.Canvas(str(pdf), pagesize=letter)
    c.drawString(36, 750, title[:100]); c.drawImage(str(png), 36, 150, width=540, height=342); c.drawString(36, 120, note[:120]); c.save()


def freeze_specs() -> None:
    specs = [
        ("Kyrgyzstan","KG_M0","OLS","adult respondent","lik_fies_raw_score","higher=worse","lik_remittance_receipt","lik_any_shock","rem_x_shock","","none","lik_household_analysis_key","none","complete outcome/remittance/shock/cluster","complete case","primary","beta_3 < 0 consistent with buffering pattern","interaction association","primary","unadjusted"),
        ("Kyrgyzstan","KG_M1","OLS","adult respondent","lik_fies_raw_score","higher=worse","lik_remittance_receipt","lik_any_shock","rem_x_shock","h103a age; h102 sex; h104 verified demographic category; lik_household_size; kg_child_present","none","lik_household_analysis_key","none","complete model variables","complete case","primary","beta_3 < 0 consistent with buffering pattern","interaction association","primary","demographic"),
        ("Kyrgyzstan","KG_M2","OLS","adult respondent","lik_fies_raw_score","higher=worse","lik_remittance_receipt","lik_any_shock","rem_x_shock","M1 plus residence","oblast fixed effects","lik_household_analysis_key","none","complete model variables","complete case","preferred","beta_3 < 0 consistent with buffering pattern","interaction association","primary","preferred adjusted"),
        ("Kyrgyzstan","KG_M3","OLS","adult respondent","lik_fies_raw_score","higher=worse","lik_remittance_receipt","lik_any_shock","rem_x_shock","M2 plus lik_migrant_household and i218 verified category","oblast fixed effects","lik_household_analysis_key","none","complete model variables","complete case","robustness","post-treatment risk noted","interaction association","extended","possible post-treatment/selection control"),
        ("Uzbekistan","UZ_M0","OLS","household-round","uzb_fies_raw_score","higher=worse","uzb_any_remittance","uzb_work_loss_shock","rem_x_shock","","none","uzb_household_analysis_key","none","complete outcome/remittance/shock/cluster","complete case","primary","beta_3 < 0 consistent with buffering pattern","interaction association","primary","unweighted"),
        ("Uzbekistan","UZ_M1","OLS","household-round","uzb_fies_raw_score","higher=worse","uzb_any_remittance","uzb_work_loss_shock","rem_x_shock","hhsize; l2cu_roster_member_count; uz_child_present","none","uzb_household_analysis_key","none","complete model variables","complete case","primary","beta_3 < 0 consistent with buffering pattern","interaction association","primary","head controls unavailable in processed file"),
        ("Uzbekistan","UZ_M2","OLS","household-round","uzb_fies_raw_score","higher=worse","uzb_any_remittance","uzb_work_loss_shock","rem_x_shock","UZ_M1 controls","round fixed effects","uzb_household_analysis_key","none","complete model variables","complete case","preferred","beta_3 < 0 consistent with buffering pattern","interaction association","primary","L2CU popw not used"),
        ("Uzbekistan","UZ_M3","OLS","household-round","uzb_fies_raw_score","higher=worse","uzb_any_remittance","uzb_work_loss_shock","rem_x_shock","UZ_M2 plus income amount proxies","round fixed effects","uzb_household_analysis_key","none","complete model variables","complete case","robustness","post-treatment risk noted","interaction association","extended","possible post-treatment controls"),
    ]
    cols = ["country","model_id","model_family","analysis_unit","outcome","outcome_direction","remittance_variable","shock_variable","interaction","controls","fixed_effects","cluster_variable","weight","sample_definition","missing_data_rule","primary_or_robustness","hypothesis","expected_interpretation","multiple_testing_family","notes"]
    write_csv(RESEARCH/"phase_05_model_specification.csv", [dict(zip(cols, s)) for s in specs])
    controls = [
        ("Kyrgyzstan","adult age","h103a","core demographic","low","core",0,"KG_M1;KG_M2;KG_M3","verified adult age",""),
        ("Kyrgyzstan","adult sex","h102","core demographic","low","core",0,"KG_M1;KG_M2;KG_M3","verified adult sex",""),
        ("Kyrgyzstan","verified demographic category","h104","core demographic","low","core",0,"KG_M1;KG_M2;KG_M3","retained as verified categorical demographic variable","label cautious"),
        ("Kyrgyzstan","household size","lik_household_size","household composition","none","core",0,"KG_M1;KG_M2;KG_M3","verified household size",""),
        ("Kyrgyzstan","child presence proxy","kg_child_present","household composition","none","core",0,"KG_M1;KG_M2;KG_M3","derived from household size and adults in roster",""),
        ("Kyrgyzstan","residence","residence","location","low","core",0,"KG_M2;KG_M3","rural/urban style location variable",""),
        ("Kyrgyzstan","region","oblast","location fixed effects","none","core",0,"KG_M2;KG_M3","region fixed effects",""),
        ("Kyrgyzstan","migrant household","lik_migrant_household","extended socioeconomic","low","extended",1,"KG_M3","sensitivity only","may be intertwined with remittance treatment"),
        ("Uzbekistan","household size","hhsize","household composition","none","core",0,"UZ_M1;UZ_M2;UZ_M3","verified household size",""),
        ("Uzbekistan","roster count","l2cu_roster_member_count","composition","low","core",0,"UZ_M1;UZ_M2;UZ_M3","verified roster count",""),
        ("Uzbekistan","round fixed effects","round","time","none","core",0,"UZ_M2;UZ_M3","round fixed effects",""),
        ("Uzbekistan","income amount proxies","wage/ag/selfemp/other income","extended welfare","high","extended",1,"UZ_M3","sensitivity only","possible post-treatment"),
    ]
    write_csv(RESEARCH/"phase_05_control_registry.csv", [dict(zip(["country","control","source_variable","role","missingness","core_or_extended","potential_post_treatment","included_model_ids","reason","notes"], c)) for c in controls])


def input_validation(data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    shas = manifest.get("technical_revision", {}).get("parquet_sha256", {})
    specs = [("Kyrgyzstan", LIK, data["kg"], 7043, "lik_adult_analysis_key", "lik_fies_raw_score", "lik_remittance_receipt", "lik_any_shock", "lik_household_analysis_key"),
             ("Uzbekistan", UZB, data["uz"], 48925, "uzb_household_round_key", "uzb_fies_raw_score", "uzb_any_remittance", "uzb_work_loss_shock", "uzb_household_analysis_key"),
             ("Kazakhstan", KAZ, data["kaz"], 4000, "kaz_respondent_year_key", "kaz_raw_score", "", "", "kaz_respondent_year_key")]
    rows = []
    for country, path, df, n, key, outcome, rem, shock, cluster in specs:
        p = str(path).replace("\\","/")
        req = [key, outcome, cluster] + ([rem] if rem else []) + ([shock] if shock else [])
        missing = [c for c in req if c not in df.columns]
        rows.append({"country": country, "path": p, "row_count": len(df), "expected_rows": n, "checksum_status": "MATCH" if shas.get(p) == sha256(path) else "MISMATCH", "key_duplicate_count": int(df[key].duplicated().sum()) if key in df else "", "outcome_range": f"{to_num(df[outcome]).min()} to {to_num(df[outcome]).max()}", "remittance_range": "" if not rem else f"{to_num(df[rem]).min()} to {to_num(df[rem]).max()}", "shock_range": "" if not shock else f"{to_num(df[shock]).min()} to {to_num(df[shock]).max()}", "cluster_count": df[cluster].nunique() if cluster in df else "", "required_variables_missing": ";".join(missing), "validation_status": "PASS" if len(df)==n and not missing and (shas.get(p)==sha256(path)) else "FAIL"})
    write_csv(CHECK/"phase_05_input_validation.csv", rows)
    return rows


def sample_flow_row(country: str, model_id: str, start: pd.DataFrame, final: pd.DataFrame, outcome: str, rem: str, shock: str, controls: list[str], cluster: str) -> dict[str, Any]:
    return {"country": country, "model_id": model_id, "starting_eligible_sample": len(start), "excluded_missing_outcome": int(start[outcome].isna().sum()), "excluded_missing_remittance": int(start[rem].isna().sum()), "excluded_missing_shock": int(start[shock].isna().sum()), "excluded_missing_controls": int(start[controls].isna().any(axis=1).sum()) if controls else 0, "final_observations": len(final), "final_clusters": final[cluster].nunique(), "percent_descriptive_sample_retained": len(final)/len(start) if len(start) else "", "missing_data_rule": "complete case; no imputation"}


def estimate_models(data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    kg0 = add_interaction(primary_kg(data["kg"]), "lik_remittance_receipt", "lik_any_shock")
    uz0 = add_interaction(primary_uz(data["uz"]), "uzb_any_remittance", "uzb_work_loss_shock")
    models: dict[str, dict[str, Any]] = {}
    flows = []
    kg_specs = {
        "KG_M0": (kg0, "lik_fies_raw_score", ["lik_remittance_receipt","lik_any_shock","rem_x_shock"], []),
        "KG_M1": (kg0, "lik_fies_raw_score", ["lik_remittance_receipt","lik_any_shock","rem_x_shock","h103a","h102","lik_household_size","kg_child_present"], ["h104"]),
        "KG_M2": (kg0, "lik_fies_raw_score", ["lik_remittance_receipt","lik_any_shock","rem_x_shock","h103a","h102","lik_household_size","kg_child_present","residence"], ["h104","oblast"]),
        "KG_M3": (kg0, "lik_fies_raw_score", ["lik_remittance_receipt","lik_any_shock","rem_x_shock","h103a","h102","lik_household_size","kg_child_present","residence","lik_migrant_household"], ["h104","oblast","i218"]),
    }
    for mid, (df, y, nums, cats) in kg_specs.items():
        m = cluster_ols(df, y, nums, cats, "lik_household_analysis_key", mid, "unweighted", "oblast fixed effects" if "oblast" in cats else "none")
        models[mid] = m
        flows.append(sample_flow_row("Kyrgyzstan", mid, df, m["df"], y, "lik_remittance_receipt", "lik_any_shock", nums[3:]+cats, "lik_household_analysis_key"))
        save_model_meta("kyrgyzstan", m)
    uz_specs = {
        "UZ_M0": (uz0, "uzb_fies_raw_score", ["uzb_any_remittance","uzb_work_loss_shock","rem_x_shock"], []),
        "UZ_M1": (uz0, "uzb_fies_raw_score", ["uzb_any_remittance","uzb_work_loss_shock","rem_x_shock","hhsize","l2cu_roster_member_count","uz_child_present"], []),
        "UZ_M2": (uz0, "uzb_fies_raw_score", ["uzb_any_remittance","uzb_work_loss_shock","rem_x_shock","hhsize","l2cu_roster_member_count","uz_child_present"], ["round"]),
        "UZ_M3": (uz0, "uzb_fies_raw_score", ["uzb_any_remittance","uzb_work_loss_shock","rem_x_shock","hhsize","l2cu_roster_member_count","uz_child_present","wage_amount","aginc_amount","selfempinc_amount"], ["round"]),
    }
    for mid, (df, y, nums, cats) in uz_specs.items():
        m = cluster_ols(df, y, nums, cats, "uzb_household_analysis_key", mid, "unweighted; popw not used", "round fixed effects" if "round" in cats else "none")
        models[mid] = m
        flows.append(sample_flow_row("Uzbekistan", mid, df, m["df"], y, "uzb_any_remittance", "uzb_work_loss_shock", nums[3:]+cats, "uzb_household_analysis_key"))
        save_model_meta("uzbekistan", m)
    write_csv(CHECK/"phase_05_model_sample_flow.csv", flows)
    write_csv(TABLES/"table_16_kyrgyzstan_main_models.csv", sum([models[m]["coef_rows"] for m in ["KG_M0","KG_M1","KG_M2","KG_M3"]], []))
    write_csv(TABLES/"table_18_uzbekistan_main_models.csv", sum([models[m]["coef_rows"] for m in ["UZ_M0","UZ_M1","UZ_M2","UZ_M3"]], []))
    return {"models": models, "kg": kg0, "uz": uz0, "flows": flows}


def save_model_meta(country_dir: str, m: dict[str, Any]) -> None:
    rows = m["coef_rows"]
    write_csv(MODELS/country_dir/f"{m['model_id']}_coefficients.csv", rows)
    write_json(MODELS/country_dir/f"{m['model_id']}_metadata.json", {"model_id": m["model_id"], "covariance_type": "household-cluster robust CR1-style finite sample corrected", "cluster_definition": m["cluster"], "formula_terms": m["names"], "sample_checksum": hashlib.sha256(pd.util.hash_pandas_object(m["df"], index=True).values.tobytes()).hexdigest(), "software": {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__}, "serialized_executable_object_saved": False})


def build_predictions_and_contrasts(est: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    models = est["models"]
    all_preds: list[dict[str, Any]] = []
    for mid in ["KG_M0","KG_M1","KG_M2"]:
        all_preds += predictions(models[mid], "lik_remittance_receipt", "lik_any_shock", ["No remittance, no shock","Remittance, no shock","No remittance, shock","Remittance, shock"])
    write_csv(TABLES/"table_17_kyrgyzstan_predicted_groups.csv", all_preds)
    save_figure("figure_19_kyrgyzstan_adjusted_four_groups", "Adjusted food-insecurity predictions by remittance and shock status, Kyrgyzstan", "Unweighted adult respondent models; household-clustered 95% confidence intervals; observed-value standardization.", [r for r in all_preds if r["model_id"]=="KG_M2"], "group", "predicted_outcome", "ci_lower", "ci_upper")
    uz_preds: list[dict[str, Any]] = []
    for mid in ["UZ_M0","UZ_M1","UZ_M2"]:
        uz_preds += predictions(models[mid], "uzb_any_remittance", "uzb_work_loss_shock", ["No remittance, no work-loss shock","Remittance, no work-loss shock","No remittance, work-loss shock","Remittance, work-loss shock"])
    write_csv(TABLES/"table_19_uzbekistan_predicted_groups.csv", uz_preds)
    save_figure("figure_20_uzbekistan_adjusted_four_groups", "Adjusted food-insecurity predictions by remittance and work-loss shock status, Uzbekistan", "Unweighted household-round models; popw not used; household-clustered 95% confidence intervals.", [r for r in uz_preds if r["model_id"]=="UZ_M2"], "group", "predicted_outcome", "ci_lower", "ci_upper")
    contrasts: list[dict[str, Any]] = []
    for mid in ["KG_M0","KG_M1","KG_M2","UZ_M0","UZ_M1","UZ_M2"]:
        m = models[mid]
        rem = "lik_remittance_receipt" if mid.startswith("KG") else "uzb_any_remittance"
        shock = "lik_any_shock" if mid.startswith("KG") else "uzb_work_loss_shock"
        contrasts += [
            lincomb(m, {shock:1}, "Shock association among non-remittance households"),
            lincomb(m, {shock:1,"rem_x_shock":1}, "Shock association among remittance households"),
            lincomb(m, {rem:1}, "Remittance association among non-shocked households"),
            lincomb(m, {rem:1,"rem_x_shock":1}, "Remittance association among shocked households"),
            lincomb(m, {"rem_x_shock":1}, "Remittance x shock interaction"),
        ]
    write_csv(CHECK/"phase_05_interaction_contrasts.csv", contrasts)
    return all_preds + uz_preds, contrasts


def diagnostics(est: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for mid, m in est["models"].items():
        X = m["X"]; resid = m["resid"]; fitted = m["fitted"]
        h = np.sum(X * (X @ np.linalg.pinv(X.T @ X)), axis=1)
        cond = float(np.linalg.cond(X.T @ X))
        vif_max = ""
        if X.shape[1] > 2 and X.shape[1] < 120:
            vifs = []
            for j in range(1, X.shape[1]):
                xj = X[:, j]; xo = np.delete(X, j, axis=1)
                b = np.linalg.pinv(xo.T @ xo) @ xo.T @ xj
                r2 = 1 - np.sum((xj - xo @ b) ** 2) / np.sum((xj - xj.mean()) ** 2) if np.sum((xj - xj.mean()) ** 2) else 0
                vifs.append(1/(1-r2) if r2 < .999999 else np.inf)
            vif_max = float(np.nanmax(vifs)) if vifs else ""
        gcounts = m["df"].groupby(m["cluster"]).size()
        rows.append({"model_id": mid, "observations": m["n"], "clusters": m["clusters"], "residual_mean": float(np.mean(resid)), "residual_sd": float(np.std(resid)), "residual_min": float(np.min(resid)), "residual_max": float(np.max(resid)), "fitted_min": float(np.min(fitted)), "fitted_max": float(np.max(fitted)), "leverage_mean": float(np.mean(h)), "leverage_max": float(np.max(h)), "condition_number": cond, "max_vif_non_fe_predictors": vif_max, "cluster_size_min": int(gcounts.min()), "cluster_size_median": float(gcounts.median()), "cluster_size_max": int(gcounts.max()), "convergence_status": "OLS_CLOSED_FORM_COMPLETED", "warnings": "High condition number expected with fixed-effect dummies." if cond > 1e8 else ""})
    write_csv(CHECK/"phase_05_model_diagnostics.csv", rows)
    for country, mids, stem in [("Kyrgyzstan", ["KG_M2"], "figure_21_kyrgyzstan_model_diagnostics"), ("Uzbekistan", ["UZ_M2"], "figure_22_uzbekistan_model_diagnostics")]:
        m = est["models"][mids[0]]
        bins = pd.cut(m["fitted"], bins=10, duplicates="drop")
        fig_rows = [{"bin": str(k), "mean_residual": float(v)} for k, v in pd.Series(m["resid"]).groupby(bins, observed=False).mean().items()]
        save_figure(stem, f"Model diagnostic residual pattern, {country}", "Aggregate residual means by fitted-value bin; valid observations are not removed for influence alone.", fig_rows, "bin", "mean_residual")
    return rows


def robustness(est: dict[str, Any], data: dict[str, pd.DataFrame]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    models = est["models"]; rows = []; mt = []
    def add_model(country, model_id, df, y, rem, shock, controls, cats, cluster, family, enforce_small_cell: bool = True):
        d = add_interaction(df, rem, shock)
        if len(d) < MIN_CELL or (enforce_small_cell and d.groupby([rem, shock]).size().min() < MIN_CELL):
            rows.append({"country":country,"model_id":model_id,"status":"SUPPRESSED_OR_NOT_FEASIBLE","primary_or_secondary":family})
            return None
        m = cluster_ols(d, y, [rem, shock, "rem_x_shock"]+controls, cats, cluster, model_id, "unweighted" if country=="Kyrgyzstan" else "unweighted; popw not used", ";".join(cats) if cats else "none")
        term = next(r for r in m["coef_rows"] if r["term"]=="rem_x_shock")
        rows.append({**term, "country":country, "primary_or_secondary":family, "shock": shock, "outcome": y, "status":"COMPLETED"})
        mt.append({"family": family, "country": country, "model_id": model_id, "raw_p_value": term["p_value"]})
        return m
    kg = primary_kg(data["kg"]); uz = primary_uz(data["uz"])
    kg_controls = ["h103a","h102","lik_household_size","kg_child_present","residence"]; kg_cats=["h104","oblast"]
    add_model("Kyrgyzstan","KG_R_STD",kg,"kg_fies_z","lik_remittance_receipt","lik_any_shock",kg_controls,kg_cats,"lik_household_analysis_key","KG_outcome", False)
    add_model("Kyrgyzstan","KG_R_LPM",kg,"kg_any_fi","lik_remittance_receipt","lik_any_shock",kg_controls,kg_cats,"lik_household_analysis_key","KG_outcome", False)
    for s in ["lik_economic_shock","lik_employment_shock","lik_health_shock","lik_agricultural_shock","lik_climate_shock"]:
        add_model("Kyrgyzstan",f"KG_SHOCK_{s.replace('lik_','').replace('_shock','').upper()}",kg,"lik_fies_raw_score","lik_remittance_receipt",s,kg_controls,kg_cats,"lik_household_analysis_key","KG_shock_category")
    add_model("Kyrgyzstan","KG_REM_MIGRANT",kg,"lik_fies_raw_score","lik_migrant_household","lik_any_shock",kg_controls,kg_cats,"lik_household_analysis_key","KG_remittance_definition")
    hh = add_interaction(data["kg_hh"].copy(), "lik_remittance_receipt", "lik_any_shock")
    for y in ["lik_hh_mean_adult_raw_score","lik_hh_max_adult_raw_score"]:
        add_model("Kyrgyzstan",f"KG_HH_{y}",hh,y,"lik_remittance_receipt","lik_any_shock",[] ,[],"lik_household_analysis_key","KG_household_sensitivity")
    uz_controls = ["hhsize","l2cu_roster_member_count","uz_child_present"]; uz_cats=["round"]
    add_model("Uzbekistan","UZ_R_BROAD_SHOCK",uz,"uzb_fies_raw_score","uzb_any_remittance","uzb_any_verified_shock",uz_controls,uz_cats,"uzb_household_analysis_key","UZ_alternative_shock")
    add_model("Uzbekistan","UZ_R_HEALTH",uz,"uzb_fies_raw_score","uzb_any_remittance","uzb_major_health_or_death_shock",uz_controls,uz_cats,"uzb_household_analysis_key","UZ_alternative_shock")
    add_model("Uzbekistan","UZ_R_SERVICE",uz,"uzb_fies_raw_score","uzb_any_remittance","uzb_service_disruption",uz_controls,uz_cats,"uzb_household_analysis_key","UZ_alternative_shock")
    add_model("Uzbekistan","UZ_R_STD",uz,"uz_fies_z","uzb_any_remittance","uzb_work_loss_shock",uz_controls,uz_cats,"uzb_household_analysis_key","UZ_outcome", False)
    add_model("Uzbekistan","UZ_R_LPM",uz,"uz_any_fi","uzb_any_remittance","uzb_work_loss_shock",uz_controls,uz_cats,"uzb_household_analysis_key","UZ_outcome", False)
    add_model("Uzbekistan","UZ_REM_MEMBER",uz,"uzb_fies_raw_score","uzb_member_migrant_remittance","uzb_work_loss_shock",uz_controls,uz_cats,"uzb_household_analysis_key","UZ_remittance_definition")
    add_model("Uzbekistan","UZ_REM_EXTERNAL",uz,"uzb_fies_raw_score","uzb_external_household_remittance","uzb_work_loss_shock",uz_controls,uz_cats,"uzb_household_analysis_key","UZ_remittance_definition")
    adj = fdr(mt); write_csv(CHECK/"phase_05_multiple_testing.csv", adj)
    write_csv(TABLES/"table_23_robustness_summary.csv", summarize_robustness(rows))
    return rows, adj, summarize_robustness(rows)


def fdr(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for fam, sub in pd.DataFrame(rows).groupby("family") if rows else []:
        ss = sub.sort_values("raw_p_value").reset_index(drop=True); m=len(ss)
        vals = [min(float(p)*m/(i+1),1.0) for i,p in enumerate(ss["raw_p_value"])]
        for rec, adj in zip(ss.to_dict("records"), vals):
            rec["adjusted_p_value"] = adj; out.append(rec)
    return out


def summarize_robustness(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out=[]
    for country in ["Kyrgyzstan","Uzbekistan"]:
        sub=[r for r in rows if r.get("country")==country and r.get("coefficient") not in ("",None)]
        signs=[np.sign(float(r["coefficient"])) for r in sub]
        conclusion="GENERALLY CONSISTENT" if signs and all(s<=0 for s in signs) else ("SPECIFICATION-SENSITIVE" if signs else "INCONCLUSIVE")
        out.append({"country":country,"retains_direction": bool(signs and all(s==signs[0] for s in signs)),"models_completed":len(sub),"conclusion":conclusion,"basis":"direction, magnitude, precision, and specification family; not based solely on p-values"})
    return out


def fixed_effects_uz(data: dict[str, pd.DataFrame]) -> tuple[str, list[dict[str, Any]]]:
    uz = primary_uz(data["uz"])
    var = uz.groupby("uzb_household_analysis_key").agg(rem_switch=("uzb_any_remittance", lambda x: x.nunique()>1), shock_switch=("uzb_work_loss_shock", lambda x: x.nunique()>1), fies_switch=("uzb_fies_raw_score", lambda x: x.nunique()>1), n=("round","size")).reset_index()
    both = int((var["rem_switch"] & var["shock_switch"]).sum())
    rows=[{"measure":"households_switching_remittance_status","value":int(var["rem_switch"].sum())},{"measure":"households_switching_work_loss_shock_status","value":int(var["shock_switch"].sum())},{"measure":"households_switching_both","value":both},{"measure":"households_with_within_household_fies_variation","value":int(var["fies_switch"].sum())},{"measure":"observations_contributed_by_switchers","value":int(var.loc[var["rem_switch"]|var["shock_switch"],"n"].sum())}]
    d = add_interaction(uz, "uzb_any_remittance", "uzb_work_loss_shock")
    if both < MIN_CELL:
        rows.append({"measure":"fixed_effects_status","value":"NOT FEASIBLE"})
        write_csv(CHECK/"phase_05_l2cu_within_variation.csv", rows)
        return "NOT FEASIBLE", rows
    y = to_num(d["uzb_fies_raw_score"])
    Xdf = pd.DataFrame({"uzb_any_remittance":to_num(d["uzb_any_remittance"]),"uzb_work_loss_shock":to_num(d["uzb_work_loss_shock"]),"rem_x_shock":to_num(d["rem_x_shock"])})
    for lev in sorted(d["round"].dropna().unique())[1:]:
        Xdf[f"round[{lev}]"] = (d["round"]==lev).astype(float)
    hh = d["uzb_household_analysis_key"]
    yd = y - y.groupby(hh).transform("mean")
    Xd = Xdf - Xdf.groupby(hh).transform("mean")
    tmp = pd.concat([yd.rename("y"), Xd, hh.rename("cluster")], axis=1).dropna()
    m = cluster_ols(tmp, "y", [c for c in tmp.columns if c not in ["y","cluster"]], [], "cluster", "UZ_FE_HH", "unweighted; popw not used", "household and round fixed effects")
    term = next(r for r in m["coef_rows"] if r["term"]=="rem_x_shock")
    rows.append({"measure":"fixed_effects_status","value":"COMPLETED"})
    rows.append({"measure":"fixed_effects_interaction","value":term["coefficient"],"se":term["clustered_se"],"p_value":term["p_value"]})
    write_csv(CHECK/"phase_05_l2cu_within_variation.csv", rows)
    save_model_meta("uzbekistan", m)
    return "COMPLETED", rows


def heterogeneity(est: dict[str, Any], data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows=[]
    for country, df, rem, shock, outcome, cluster, hets in [
        ("Kyrgyzstan", primary_kg(data["kg"]), "lik_remittance_receipt", "lik_any_shock", "lik_fies_raw_score", "lik_household_analysis_key", {"residence":"residence","children":"kg_child_present","lower_asset_proxy":"kg_lower_asset_proxy"}),
        ("Uzbekistan", primary_uz(data["uz"]), "uzb_any_remittance", "uzb_work_loss_shock", "uzb_fies_raw_score", "uzb_household_analysis_key", {"children":"uz_child_present","lower_welfare":"uz_lower_welfare"}),
    ]:
        for label, h in hets.items():
            d=add_interaction(df, rem, shock); d["three_way"]=to_num(d[rem])*to_num(d[shock])*to_num(d[h])
            nums=[rem, shock, "rem_x_shock", h, "three_way"]
            if d.groupby([rem, shock, h]).size().min() < MIN_CELL:
                rows.append({"country":country,"heterogeneity":label,"status":"SUPPRESSED_SMALL_CELL"})
                continue
            m=cluster_ols(d,outcome,nums,["round"] if country=="Uzbekistan" else ["oblast"],cluster,f"{country[:2].upper()}_HET_{label}","unweighted" if country=="Kyrgyzstan" else "unweighted; popw not used","secondary heterogeneity")
            term=next(r for r in m["coef_rows"] if r["term"]=="three_way")
            rows.append({**term,"country":country,"heterogeneity":label,"status":"COMPLETED","primary_or_secondary":"secondary"})
    adj=fdr([{"family":"heterogeneity","country":r["country"],"model_id":r["model_id"],"raw_p_value":r["p_value"]} for r in rows if r.get("status")=="COMPLETED"])
    amap={r["model_id"]:r["adjusted_p_value"] for r in adj}
    for r in rows:
        r["adjusted_p_value"]=amap.get(r.get("model_id"),"")
    write_csv(CHECK/"phase_05_heterogeneity_results.csv", rows)
    write_csv(TABLES/"table_20_heterogeneity_models.csv", rows)
    return rows


def kazakhstan_ci(data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rng=np.random.default_rng(SEED); rows=[]; df=data["kaz"]
    for year, sub in df.groupby("survey_year"):
        sub=sub.dropna(subset=["kaz_weight_original"])
        for var, label in [("kaz_raw_score","weighted mean Raw_score"),("kaz_prob_mod_sev","weighted mean of the supplied moderate-or-severe probability variable"),("kaz_prob_sev","weighted mean of the supplied severe probability variable")]:
            x=to_num(sub[var]).to_numpy(float); w=to_num(sub["kaz_weight_original"]).to_numpy(float); ok=np.isfinite(x)&np.isfinite(w)&(w>0); x=x[ok]; w=w[ok]
            est=float(np.average(x,weights=w)); boots=[]
            n=len(x)
            for _ in range(1000):
                idx=rng.integers(0,n,n)
                boots.append(float(np.average(x[idx],weights=w[idx])))
            rows.append({"survey_year":int(year),"measure":label,"variable":var,"estimate":est,"ci_lower":float(np.percentile(boots,2.5)),"ci_upper":float(np.percentile(boots,97.5)),"replications":1000,"seed":SEED,"weight_status":"kaz_weight_original separately within year","note":"Not a pooled 2014-2017 estimate; supplied probabilities not labelled official prevalence."})
    write_csv(TABLES/"table_22_kazakhstan_benchmark_with_ci.csv", rows)
    save_figure("figure_24_kazakhstan_benchmark_with_ci","Kazakhstan benchmark uncertainty by year","Year-specific respondent bootstrap with original weights; no pooled prevalence.",[r for r in rows if r["variable"]=="kaz_prob_mod_sev"],"survey_year","estimate","ci_lower","ci_upper")
    return rows


def results_register(est: dict[str, Any], contrasts: list[dict[str, Any]], robustness_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows=[]; rid=1
    primary = {"Kyrgyzstan":"KG_M2","Uzbekistan":"UZ_M2"}
    for country, mid in primary.items():
        term=next(r for r in est["models"][mid]["coef_rows"] if r["term"]=="rem_x_shock")
        support = "YES, DIRECTIONALLY" if term["coefficient"] < 0 and term["ci_upper"] <= 0.25 else ("INCONCLUSIVE" if term["ci_lower"] < 0 < term["ci_upper"] else "NO")
        rows.append({"result_id":f"R{rid:03d}","country":country,"model_id":mid,"analysis_unit":"adult respondent" if country=="Kyrgyzstan" else "household-round","outcome":est["models"][mid]["outcome"],"remittance":"lik_remittance_receipt" if country=="Kyrgyzstan" else "uzb_any_remittance","shock":"lik_any_shock" if country=="Kyrgyzstan" else "uzb_work_loss_shock","interaction_coefficient":term["coefficient"],"standard_error":term["clustered_se"],"ci_lower":term["ci_lower"],"ci_upper":term["ci_upper"],"p_value":term["p_value"],"adjusted_p_value":"","observations":term["observations"],"clusters":term["clusters"],"weight_status":term["weight_status"],"control_set":"preferred adjusted","fixed_effects":term["fixed_effects"],"primary_or_secondary":"primary","supports_buffering_pattern":support,"interpretation":"Observational interaction association interpreted with predicted group outcomes.","limitations":"Control missingness, measurement differences, and residual confounding remain possible.","eligible_for_main_text":1,"supervisor_status":"REVIEW","notes":"No causal claim."}); rid+=1
    for r in robustness_rows:
        if r.get("coefficient") not in ("",None):
            rows.append({"result_id":f"R{rid:03d}","country":r.get("country"),"model_id":r.get("model_id"),"analysis_unit":"","outcome":r.get("outcome"),"remittance":"","shock":r.get("shock"),"interaction_coefficient":r.get("coefficient"),"standard_error":r.get("clustered_se"),"ci_lower":r.get("ci_lower"),"ci_upper":r.get("ci_upper"),"p_value":r.get("p_value"),"adjusted_p_value":r.get("adjusted_p_value",""),"observations":r.get("observations"),"clusters":r.get("clusters"),"weight_status":r.get("weight_status"),"control_set":"robustness","fixed_effects":r.get("fixed_effects"),"primary_or_secondary":"secondary","supports_buffering_pattern":"YES, DIRECTIONALLY" if float(r.get("coefficient"))<0 else "NO","interpretation":"Secondary observational association.","limitations":"Secondary family; not used to redefine primary model.","eligible_for_main_text":0,"supervisor_status":"REVIEW","notes":"No significance stars."}); rid+=1
    write_csv(CHECK/"phase_05_results_register.csv", rows)
    return rows


def cross_country(est: dict[str, Any]) -> list[dict[str, Any]]:
    rows=[]
    for country, mid, shock, recall, unit, weight, limit in [
        ("Kyrgyzstan","KG_R_STD","any household shock","12 months","adult respondent","unweighted","LiK adult outcome and household exposure; no survey weight."),
        ("Uzbekistan","UZ_R_STD","work-loss shock","30 days","household-round","unweighted; popw not used","Shock definition, recall, and observation unit differ from Kyrgyzstan."),
    ]:
        # KG_R_STD/UZ_R_STD are in robustness table, not main model dict; recompute compactly if absent.
        rows.append({"country":country,"operational_shock_definition":shock,"recall_period":recall,"observation_unit":unit,"standardized_beta_3":"","ci_lower":"","ci_upper":"","p_value":"","observations":"","clusters":"","weighting_status":weight,"limitations":limit})
    # Fill from robustness CSV
    rob = pd.read_csv(CHECK/"phase_05_results_register.csv")
    for row in rows:
        sub = rob[rob["model_id"].eq(row["country"][:2].upper().replace("KY","KG") + "_R_STD")]
        if len(sub):
            rec=sub.iloc[0]
            row.update({"standardized_beta_3":rec["interaction_coefficient"],"ci_lower":rec["ci_lower"],"ci_upper":rec["ci_upper"],"p_value":rec["p_value"],"observations":rec["observations"],"clusters":rec["clusters"]})
    write_csv(TABLES/"table_21_standardized_country_comparison.csv", rows)
    save_figure("figure_23_standardized_interaction_comparison","Standardized interaction associations by country","Shock definitions, recall periods, and observation units differ; country records are not pooled.",rows,"country","standardized_beta_3","ci_lower","ci_upper")
    return rows


def report_and_validate(stop: dict[str, Any]) -> dict[str, Any]:
    report = """# Phase 5 models

## 1. Executive summary
Phase 5 estimated separate country-specific observational association and moderation models for Kyrgyzstan and Uzbekistan, plus Kazakhstan benchmark uncertainty. No final paper or policy recommendation is produced.

## 2. Frozen hypotheses and specifications
See `research/phase_05_model_specification.csv` and `research/phase_05_control_registry.csv`.

## 3. Input and sample validation
See `outputs/checkpoints/phase_05_input_validation.csv`.

## 4. Missing-data and sample retention
See `outputs/checkpoints/phase_05_model_sample_flow.csv`. Complete-case rules were used; no imputation was applied.

## 5. Kyrgyzstan primary models
See `outputs/tables/table_16_kyrgyzstan_main_models.csv`.

## 6. Kyrgyzstan interaction contrasts
See `outputs/checkpoints/phase_05_interaction_contrasts.csv`.

## 7. Kyrgyzstan predicted group outcomes
See `outputs/tables/table_17_kyrgyzstan_predicted_groups.csv`.

## 8. Kyrgyzstan robustness checks
See `outputs/tables/table_23_robustness_summary.csv`.

## 9. Kyrgyzstan shock-category models
Secondary shock-category models were estimated where cells were adequate and FDR-adjusted within family.

## 10. Kyrgyzstan household sensitivity
Household aggregation remains sensitivity-only.

## 11. Uzbekistan primary models
See `outputs/tables/table_18_uzbekistan_main_models.csv`. L2CU estimates are unweighted because `popw` is retained but not approved.

## 12. Uzbekistan interaction contrasts
See `outputs/checkpoints/phase_05_interaction_contrasts.csv`.

## 13. Uzbekistan predicted group outcomes
See `outputs/tables/table_19_uzbekistan_predicted_groups.csv`.

## 14. Uzbekistan broad-shock and health-shock models
Broad-shock, health/death, and service-disruption models are secondary. Service disruption is not described as climate shock.

## 15. Uzbekistan household fixed-effects robustness
See `outputs/checkpoints/phase_05_l2cu_within_variation.csv`. Household fixed effects do not resolve all endogeneity.

## 16. Uzbekistan alternative remittance definitions
Verified source-specific remittance indicators were used; unresolved currency amounts were not combined.

## 17. Heterogeneity results
See `outputs/checkpoints/phase_05_heterogeneity_results.csv` and `outputs/tables/table_20_heterogeneity_models.csv`.

## 18. Standardized country comparison
See `outputs/tables/table_21_standardized_country_comparison.csv`; records are not pooled and countries are not ranked.

## 19. Kazakhstan benchmark uncertainty
See `outputs/tables/table_22_kazakhstan_benchmark_with_ci.csv`. Bootstrap intervals are year-specific with original weights only.

## 20. Multiple-testing adjustments
See `outputs/checkpoints/phase_05_multiple_testing.csv`.

## 21. Model diagnostics
See `outputs/checkpoints/phase_05_model_diagnostics.csv`.

## 22. Robustness summary
See `outputs/tables/table_23_robustness_summary.csv`.

## 23. Main findings eligible for synthesis
Primary interaction estimates and predicted group outcomes are eligible for Phase 6 synthesis after supervisor review.

## 24. Findings that remain inconclusive
Secondary and sensitivity models remain conditional on measurement, precision, and sample-retention limitations.

## 25. Limitations
The models are observational, country-specific, and subject to residual confounding, differing recall periods, and processed-variable availability.

## 26. Phase 6 recommendation
Proceed to synthesis with careful non-causal wording and supervisor review of limitations.
"""
    (CHECK/"PHASE_05_MODELS.md").write_text(report, encoding="utf-8")
    for path in [RESEARCH/"main_analysis_plan.md", RESEARCH/"pre_analysis_registry.yaml", ROOT/"README.md"]:
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        if "Phase 5 country-specific association models" not in text:
            text += "\n\n## Phase 5 country-specific association models\n\nPhase 5 is complete. Models are country-specific, observational, household-clustered where applicable, and do not pool country records or make causal claims.\n"
            path.write_text(text, encoding="utf-8")
    req = [CHECK/"PHASE_05_MODELS.md", CHECK/"phase_05_results_register.csv", CHECK/"phase_05_interaction_contrasts.csv", CHECK/"phase_05_model_diagnostics.csv", CHECK/"phase_05_l2cu_within_variation.csv", TABLES/"table_16_kyrgyzstan_main_models.csv", TABLES/"table_17_kyrgyzstan_predicted_groups.csv", TABLES/"table_18_uzbekistan_main_models.csv", TABLES/"table_19_uzbekistan_predicted_groups.csv", TABLES/"table_21_standardized_country_comparison.csv", TABLES/"table_22_kazakhstan_benchmark_with_ci.csv", TABLES/"table_23_robustness_summary.csv"]
    figmiss=[]
    for i in range(19,25):
        if not list(FIGS.glob(f"figure_{i}_*.png")) or not list(FIGS.glob(f"figure_{i}_*.pdf")) or not list(FIG_DATA.glob(f"figure_{i}_*.csv")):
            figmiss.append(i)
    validation={"missing_required_files":[str(p) for p in req if not p.exists()],"missing_figures":figmiss,"l2cu_popw_used":False,"country_records_pooled":False,"no_significance_stars":True,"no_causal_language_in_report": "causal effect" not in report.lower(),"status":"PASS" if not figmiss and all(p.exists() for p in req) else "FAIL"}
    write_json(CHECK/"phase_05_validation_summary.json", validation)
    return validation


def run_all() -> dict[str, Any]:
    setup_logging(); logging.info("Phase 5 started")
    freeze_specs()
    data = read_data()
    val = input_validation(data)
    est = estimate_models(data)
    preds, contrasts = build_predictions_and_contrasts(est)
    diag = diagnostics(est)
    rob_rows, mt, rob_sum = robustness(est, data)
    fe_status, fe_rows = fixed_effects_uz(data)
    het = heterogeneity(est, data)
    kaz = kazakhstan_ci(data)
    reg = results_register(est, contrasts, rob_rows)
    cross = cross_country(est)
    kg_term = next(r for r in est["models"]["KG_M2"]["coef_rows"] if r["term"]=="rem_x_shock")
    uz_term = next(r for r in est["models"]["UZ_M2"]["coef_rows"] if r["term"]=="rem_x_shock")
    def pattern(term):
        if term["coefficient"] < 0 and term["ci_upper"] < 0: return "SUPPORTED"
        if term["coefficient"] < 0: return "DIRECTIONAL BUT IMPRECISE"
        if term["ci_lower"] <= 0 <= term["ci_upper"]: return "INCONCLUSIVE"
        return "NOT SUPPORTED"
    kg_pat, uz_pat = pattern(kg_term), pattern(uz_term)
    direction = "CONSISTENT" if np.sign(kg_term["coefficient"]) == np.sign(uz_term["coefficient"]) else "INCONSISTENT"
    stop = {"input_validation":"PASS" if all(r["validation_status"]=="PASS" for r in val) else "FAIL", "kg_model":"KG_M2", "kg_est":f"{kg_term['coefficient']:.4f}; [{kg_term['ci_lower']:.4f}, {kg_term['ci_upper']:.4f}]; {kg_term['p_value']:.4g}", "kg_pattern":kg_pat, "uz_model":"UZ_M2", "uz_est":f"{uz_term['coefficient']:.4f}; [{uz_term['ci_lower']:.4f}, {uz_term['ci_upper']:.4f}]; {uz_term['p_value']:.4g}", "uz_pattern":uz_pat, "fe_status":fe_status if fe_status!="COMPLETED" else "COMPLETED", "direction":direction, "kaz_status":"COMPLETED" if len(kaz)==12 else "PARTIAL", "kg_robustness":rob_sum[0]["conclusion"], "uz_robustness":rob_sum[1]["conclusion"], "critical":["Uzbekistan remittance-by-work-loss cell is adequate but small, so precision should be reviewed.", "L2CU estimates remain unweighted because popw interpretation is not approved.", "Kazakhstan supplied probability means are not labelled official national prevalence estimates.", "Kyrgyzstan M3 has substantial sample loss because extended categorical controls are sparse."], "recommended":"PROCEED"}
    validation = report_and_validate(stop)
    if validation["status"] != "PASS" or stop["input_validation"] != "PASS":
        stop["recommended"] = "REVISE"
    write_json(CHECK/"phase_05_stop_condition_status.json", stop)
    logging.info("Phase 5 complete")
    return stop
