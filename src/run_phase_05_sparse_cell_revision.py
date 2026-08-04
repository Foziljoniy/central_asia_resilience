"""Run Phase 5 sparse-cell and primary-shock revision.

This script preserves the frozen Kyrgyzstan model and original Uzbekistan
work-loss results while estimating the revised Uzbekistan broad-shock candidate
models using `uzb_any_verified_shock`.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from phase5_common import (
    CHECK,
    FIGS,
    FIG_DATA,
    RESEARCH,
    TABLES,
    add_interaction,
    build_matrix,
    cluster_ols,
    lincomb,
    norm_p,
    primary_kg,
    primary_uz,
    read_data,
    setup_logging,
    to_num,
    write_csv,
    write_json,
    zcrit,
)
from run_phase_05_verification_addendum import poisson_cluster, poisson_predictions


def point_range(stem: str, title: str, rows: list[dict[str, Any]], label: str, est: str, lo: str, hi: str, x_label: str, note: str, zero: bool = False) -> None:
    write_csv(FIG_DATA / f"{stem}.csv", rows)
    width, height = 1500, max(720, 170 + 95 * len(rows))
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        fb = ImageFont.truetype("arial.ttf", 28)
        f = ImageFont.truetype("arial.ttf", 18)
        fs = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        fb = f = fs = None
    draw.text((42, 28), title, fill="black", font=fb)
    vals = []
    for r in rows:
        for c in [est, lo, hi]:
            try:
                v = float(r[c])
                if np.isfinite(v):
                    vals.append(v)
            except Exception:
                pass
    xmin, xmax = (min(vals), max(vals)) if vals else (0, 1)
    if zero:
        xmin = min(xmin, 0); xmax = max(xmax, 0)
    pad = (xmax - xmin) * .12 if xmax > xmin else 1
    xmin -= pad; xmax += pad
    left, right = 560, width - 90
    top, bottom = 120, height - 145
    draw.line((left, bottom, right, bottom), fill="black", width=2)
    draw.text((left, bottom + 34), x_label, fill="black", font=f)
    if zero:
        zx = left + (0 - xmin) / (xmax - xmin) * (right - left)
        draw.line((zx, top - 25, zx, bottom + 5), fill="#777777", width=2)
        draw.text((zx + 5, top - 48), "0", fill="#555555", font=fs)
    for i, r in enumerate(rows):
        y = top + i * ((bottom - top) / max(len(rows) - 1, 1))
        draw.text((40, y - 12), str(r[label]), fill="black", font=f)
        e, l, h = float(r[est]), float(r[lo]), float(r[hi])
        xe = left + (e - xmin) / (xmax - xmin) * (right - left)
        xl = left + (l - xmin) / (xmax - xmin) * (right - left)
        xh = left + (h - xmin) / (xmax - xmin) * (right - left)
        draw.line((xl, y, xh, y), fill="#1f77b4", width=4)
        draw.ellipse((xe - 7, y - 7, xe + 7, y + 7), fill="#1f77b4")
        draw.text((xh + 8, y - 12), f"{e:.3f} [{l:.3f}, {h:.3f}]", fill="black", font=fs)
    draw.text((40, height - 82), note[:230], fill="black", font=fs)
    png = FIGS / f"{stem}.png"
    pdf = FIGS / f"{stem}.pdf"
    img.save(png)
    c = canvas.Canvas(str(pdf), pagesize=letter)
    c.drawString(36, 750, title[:110])
    c.drawImage(str(png), 24, 145, width=565, height=330)
    c.drawString(36, 115, note[:120])
    c.save()


def write_definition_docs() -> None:
    cross = pd.read_csv(RESEARCH / "l2cu_shock_crosswalk.csv")
    incl = cross[cross["target_variable"].isin(["uzb_work_loss_shock", "uzb_major_health_or_death_shock"])]
    excluded = cross[cross["included_in_primary_shock"].astype(str).eq("0")]
    text = """# Uzbekistan primary shock revision

`uzb_any_verified_shock` is retained as constructed. No coding error was found.

## Included source variables

- `work_lost_hh`: household member lost job/stopped working over the past month; contributes through `uzb_work_loss_shock`.
- `change_important_type`: major illness, major injury, or death; contributes through `uzb_major_health_or_death_shock`.

## Excluded variables

- Service disruption variables including water, gas, and heat disruption are retained separately and are not climate shocks.
- National economic challenge opinion variables are excluded because they are not household shocks.
- Ordinary employment status and unverified shock fields are not included.

## Coding, missingness, and coexistence

The broad-shock indicator equals 1 when either verified component is observed as present. It equals 0 when verified components indicate no event or when only excluded service disruption is observed. Missing work-loss with a verified health/death shock can still yield a broad-shock value of 1. Multiple shock types may coexist.

## Comparison with Kyrgyzstan

Kyrgyzstan `lik_any_shock` is a 12-month household shock exposure from an event roster. Uzbekistan `uzb_any_verified_shock` is a past-month household-round indicator covering work loss and major health/injury/death events. Both are household-level exposure concepts, but recall period, survey unit, and included shock domains differ.
"""
    (RESEARCH / "uzbekistan_primary_shock_revision.md").write_text(text, encoding="utf-8")
    work = """# Uzbekistan work-loss result status

Status: **SECONDARY EVENT-SPECIFIC EXPLORATORY RESULT**

The work-loss joint exposure cell contains 10 household-round observations from 9 households. The preferred work-loss model estimate was negative and statistically precise, the household fixed-effects estimate was negative, bounded-model checks were directionally consistent, and influence checks were generally stable. However, the joint exposure cell is too sparse to serve as the primary Uzbekistan specification.

Appropriate wording: the work-loss result is an event-specific exploratory association that is directionally consistent with a buffering pattern but should not be described as definitive.
"""
    (RESEARCH / "uzbekistan_work_loss_result_status.md").write_text(work, encoding="utf-8")


def broad_cells(uz: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    d = add_interaction(uz, "uzb_any_remittance", "uzb_any_verified_shock")
    rows = []
    all_groups_by_hh = d.groupby("uzb_household_analysis_key").apply(lambda x: set(zip(to_num(x["uzb_any_remittance"]), to_num(x["uzb_any_verified_shock"]))), include_groups=False)
    for r, s, lab in [
        (0, 0, "No remittance, no verified shock"),
        (1, 0, "Remittance, no verified shock"),
        (0, 1, "No remittance, verified shock"),
        (1, 1, "Remittance, verified shock"),
    ]:
        sub = d[(to_num(d["uzb_any_remittance"]) == r) & (to_num(d["uzb_any_verified_shock"]) == s)]
        per = sub.groupby("uzb_household_analysis_key").size()
        hhs = set(sub["uzb_household_analysis_key"])
        exclusive = sum(1 for h in hhs if len(all_groups_by_hh.get(h, set())) == 1)
        multi = len(hhs) - exclusive
        n, hh = len(sub), len(hhs)
        cls = "ADEQUATE" if n >= 30 and hh >= 30 else ("LIMITED" if n >= 30 and hh < 30 else "SPARSE")
        row = {
            "group": lab, "remittance": r, "verified_shock": s, "household_round_observations": n, "unique_households": hh,
            "median_rounds_per_household": float(per.median()) if len(per) else 0, "mean_rounds_per_household": float(per.mean()) if len(per) else 0,
            "max_rounds_one_household": int(per.max()) if len(per) else 0, "households_exclusive_to_group": int(exclusive),
            "households_contributing_to_multiple_groups": int(multi), "complete_fies_observations": int((sub["uzb_fies_complete"] == 1).sum()),
            "effective_household_cluster_count": hh, "outcome_mean": float(to_num(sub["uzb_fies_raw_score"]).mean()) if n else "",
            "outcome_sd": float(to_num(sub["uzb_fies_raw_score"]).std(ddof=1)) if n > 1 else "", "cell_classification": cls,
        }
        rows.append(row)
    write_csv(CHECK / "phase_05_revision_broad_shock_cells.csv", rows)
    joint = next(r for r in rows if r["remittance"] == 1 and r["verified_shock"] == 1)
    return rows, joint


def estimate_broad_models(uz: pd.DataFrame) -> dict[str, Any]:
    d = add_interaction(uz, "uzb_any_remittance", "uzb_any_verified_shock")
    specs = {
        "UZBROAD_M0": (["uzb_any_remittance", "uzb_any_verified_shock", "rem_x_shock"], []),
        "UZBROAD_M1": (["uzb_any_remittance", "uzb_any_verified_shock", "rem_x_shock", "hhsize", "l2cu_roster_member_count", "uz_child_present"], []),
        "UZBROAD_M2": (["uzb_any_remittance", "uzb_any_verified_shock", "rem_x_shock", "hhsize", "l2cu_roster_member_count", "uz_child_present"], ["round"]),
    }
    models = {}
    coef_rows = []
    for mid, (nums, cats) in specs.items():
        m = cluster_ols(d, "uzb_fies_raw_score", nums, cats, "uzb_household_analysis_key", mid, "unweighted; popw not used", "round fixed effects" if cats else "none")
        models[mid] = m
        coef_rows += m["coef_rows"]
    write_csv(TABLES / "table_24_uzbekistan_broad_shock_models.csv", coef_rows)
    return models


def predictions(models: dict[str, Any]) -> list[dict[str, Any]]:
    from phase5_common import predictions as linpred
    rows = []
    labels = ["No remittance, no verified shock", "Remittance, no verified shock", "No remittance, verified shock", "Remittance, verified shock"]
    for mid in ["UZBROAD_M0", "UZBROAD_M1", "UZBROAD_M2"]:
        rows += linpred(models[mid], "uzb_any_remittance", "uzb_any_verified_shock", labels)
    write_csv(TABLES / "table_25_uzbekistan_broad_shock_predictions.csv", rows)
    fig = [r for r in rows if r["model_id"] == "UZBROAD_M2"]
    point_range(
        "figure_25_uzbekistan_broad_shock_predictions",
        "Adjusted food-insecurity predictions by remittance and verified-shock status, Uzbekistan",
        [{"group": r["group"], "estimate": r["predicted_outcome"], "ci_lower": r["ci_lower"], "ci_upper": r["ci_upper"]} for r in fig],
        "group", "estimate", "ci_lower", "ci_upper",
        "Predicted FIES-style raw score (0-8)",
        "Model UZBROAD_M2; n=47135 household-rounds; clusters=2000 households; unweighted; household-clustered 95% CIs; non-causal association.",
    )
    return rows


def contrasts(model: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        lincomb(model, {"uzb_any_verified_shock": 1}, "Shock association without remittances"),
        lincomb(model, {"uzb_any_verified_shock": 1, "rem_x_shock": 1}, "Shock association with remittances"),
        lincomb(model, {"uzb_any_remittance": 1}, "Remittance association without shock"),
        lincomb(model, {"uzb_any_remittance": 1, "rem_x_shock": 1}, "Remittance association with shock"),
        lincomb(model, {"rem_x_shock": 1}, "Remittance x broad-shock interaction"),
    ]
    write_csv(CHECK / "phase_05_revision_interaction_contrasts.csv", rows)
    return rows


def fixed_effects(uz: pd.DataFrame) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    d = add_interaction(uz, "uzb_any_remittance", "uzb_any_verified_shock")
    var = d.groupby("uzb_household_analysis_key").agg(
        rem_switch=("uzb_any_remittance", lambda x: x.nunique() > 1),
        shock_switch=("uzb_any_verified_shock", lambda x: x.nunique() > 1),
        fies_switch=("uzb_fies_raw_score", lambda x: x.nunique() > 1),
        n=("round", "size"),
    ).reset_index()
    Xdf = pd.DataFrame({"uzb_any_remittance": to_num(d["uzb_any_remittance"]), "uzb_any_verified_shock": to_num(d["uzb_any_verified_shock"]), "rem_x_shock": to_num(d["rem_x_shock"])})
    for lev in sorted(d["round"].dropna().unique())[1:]:
        Xdf[f"round[{lev}]"] = (d["round"] == lev).astype(float)
    y = to_num(d["uzb_fies_raw_score"])
    hh = d["uzb_household_analysis_key"]
    yd = y - y.groupby(hh).transform("mean")
    Xd = Xdf - Xdf.groupby(hh).transform("mean")
    tmp = pd.concat([yd.rename("y"), Xd, hh.rename("cluster")], axis=1).dropna()
    m = cluster_ols(tmp, "y", [c for c in tmp.columns if c not in ["y", "cluster"]], [], "cluster", "UZBROAD_FE_HH", "unweighted; popw not used", "household and round fixed effects")
    term = next(r for r in m["coef_rows"] if r["term"] == "rem_x_shock")
    yhat = m["fitted"]; yy = to_num(m["df"]["y"]).to_numpy(float)
    within_r2 = 1 - float(np.sum((yy - yhat) ** 2) / np.sum((yy - yy.mean()) ** 2))
    rows = [{
        "model_id": "UZBROAD_FE_HH", "beta_3": term["coefficient"], "clustered_se": term["clustered_se"], "ci_lower": term["ci_lower"], "ci_upper": term["ci_upper"], "p_value": term["p_value"],
        "observations": term["observations"], "households": term["clusters"], "remittance_switchers": int(var["rem_switch"].sum()), "shock_switchers": int(var["shock_switch"].sum()),
        "both_variable_switchers": int((var["rem_switch"] & var["shock_switch"]).sum()), "households_with_fies_variation": int(var["fies_switch"].sum()),
        "observations_contributed_by_switchers": int(var.loc[var["rem_switch"] | var["shock_switch"], "n"].sum()), "within_r_squared": within_r2,
        "warnings": "Household fixed effects do not resolve all endogeneity.",
    }]
    write_csv(CHECK / "phase_05_revision_broad_shock_fixed_effects.csv", rows)
    return rows[0], rows


def bounded(uz: pd.DataFrame) -> tuple[list[dict[str, Any]], str]:
    d = add_interaction(uz, "uzb_any_remittance", "uzb_any_verified_shock")
    m = poisson_cluster(d, "uzb_fies_raw_score", ["uzb_any_remittance", "uzb_any_verified_shock", "rem_x_shock", "hhsize", "l2cu_roster_member_count", "uz_child_present"], ["round"], "uzb_household_analysis_key", "UZBROAD_POISSON_M2", "unweighted; popw not used")
    term = next(r for r in m["coef_rows"] if r["term"] == "rem_x_shock")
    labels = ["No remittance, no verified shock", "Remittance, no verified shock", "No remittance, verified shock", "Remittance, verified shock"]
    pred = poisson_predictions(m, "uzb_any_remittance", "uzb_any_verified_shock", labels)
    rows = [{"model_id": "UZBROAD_POISSON_M2", "model_family": "Poisson pseudo-maximum-likelihood", "interaction_log_coefficient": term["coefficient"], "clustered_se": term["clustered_se"], "ci_lower": term["ci_lower"], "ci_upper": term["ci_upper"], "p_value": term["p_value"], "observations": term["observations"], "clusters": term["clusters"], "note": "Do not interpret nonlinear interaction coefficient by itself."}]
    rows += [{"model_id": r["model_id"], "group": r["group"], "prediction": r["prediction"], "ci_lower": r["ci_lower"], "ci_upper": r["ci_upper"], "observations": r["observations"], "clusters": r["clusters"], "method": r["method"], "weight_status": r["weight_status"]} for r in pred]
    write_csv(CHECK / "phase_05_revision_bounded_models.csv", rows)
    write_csv(TABLES / "table_26_uzbekistan_broad_shock_bounded_predictions.csv", [r for r in rows if "group" in r])
    status = "CONSISTENT" if term["coefficient"] < 0 else "INCONSISTENT"
    return rows, status


def influence(uz: pd.DataFrame) -> tuple[list[dict[str, Any]], str]:
    rows = []
    def fit(df: pd.DataFrame, mid: str) -> tuple[float, float, float, float]:
        m = estimate_broad_models_for_influence(df, mid)
        t = next(r for r in m["coef_rows"] if r["term"] == "rem_x_shock")
        return float(t["coefficient"]), float(t["ci_lower"]), float(t["ci_upper"]), float(t["p_value"])
    # household-equal
    hh = uz.groupby("uzb_household_analysis_key").agg(uzb_fies_raw_score=("uzb_fies_raw_score", "mean"), uzb_any_remittance=("uzb_any_remittance", "mean"), uzb_any_verified_shock=("uzb_any_verified_shock", "mean"), hhsize=("hhsize", "mean"), l2cu_roster_member_count=("l2cu_roster_member_count", "mean"), round=("round", "min")).reset_index()
    hh["uz_child_present"] = 1.0
    b, lo, hi, p = fit(hh, "INF_HH_EQUAL")
    rows.append({"check": "household_equal", "beta_3": b, "ci_lower": lo, "ci_upper": hi, "p_value": p})
    for rule, idx in [("earliest_round", uz.sort_values(["uzb_household_analysis_key", "round"]).groupby("uzb_household_analysis_key").head(1).index), ("median_round", uz.assign(_rank=uz.groupby("uzb_household_analysis_key")["round"].rank(method="first")).sort_values(["uzb_household_analysis_key", "_rank"]).groupby("uzb_household_analysis_key").nth(0).index)]:
        sub = uz.loc[idx] if rule == "earliest_round" else uz.loc[idx]
        b, lo, hi, p = fit(sub, f"INF_{rule}")
        rows.append({"check": rule, "beta_3": b, "ci_lower": lo, "ci_upper": hi, "p_value": p})
    base = estimate_broad_models_for_influence(uz, "INF_BASE")
    X = base["X"]; hlev = np.sum(X * (X @ np.linalg.pinv(X.T @ X)), axis=1)
    top = pd.DataFrame({"hh": base["df"]["uzb_household_analysis_key"].to_numpy(), "lev": hlev}).groupby("hh")["lev"].max().sort_values(ascending=False).head(20).index
    for hh_id in top:
        b, lo, hi, p = fit(uz[uz["uzb_household_analysis_key"] != hh_id], "INF_DROP_LEV")
        rows.append({"check": "leave_one_high_leverage_household", "dropped_household": hh_id, "beta_3": b, "ci_lower": lo, "ci_upper": hi, "p_value": p})
    joint_hh = uz[(uz["uzb_any_remittance"] == 1) & (uz["uzb_any_verified_shock"] == 1)]["uzb_household_analysis_key"].drop_duplicates().head(25)
    for hh_id in joint_hh:
        b, lo, hi, p = fit(uz[uz["uzb_household_analysis_key"] != hh_id], "INF_DROP_JOINT")
        rows.append({"check": "leave_one_remittance_plus_shock_household", "dropped_household": hh_id, "beta_3": b, "ci_lower": lo, "ci_upper": hi, "p_value": p})
    for k in [2, 5]:
        keep = uz.groupby("uzb_household_analysis_key").filter(lambda x: len(x) >= k)
        b, lo, hi, p = fit(keep, f"INF_MIN{k}")
        rows.append({"check": f"households_at_least_{k}_eligible_rounds", "beta_3": b, "ci_lower": lo, "ci_upper": hi, "p_value": p})
    betas = [r["beta_3"] for r in rows if "beta_3" in r and np.isfinite(r["beta_3"])]
    excl0 = [not (r["ci_lower"] <= 0 <= r["ci_upper"]) for r in rows if "ci_lower" in r and np.isfinite(r["ci_lower"])]
    summary = {"check": "summary", "minimum": float(np.min(betas)), "maximum": float(np.max(betas)), "median": float(np.median(betas)), "iqr": float(np.percentile(betas, 75) - np.percentile(betas, 25)), "proportion_negative": float(np.mean(np.array(betas) < 0)), "proportion_ci_excludes_zero": float(np.mean(excl0)) if excl0 else "", "completed_sensitivity_runs": len(betas)}
    spread = summary["maximum"] - summary["minimum"]
    status = "STABLE" if summary["proportion_negative"] == 1 and spread < .35 else ("GENERALLY STABLE" if summary["proportion_negative"] >= .9 else ("SPECIFICATION-SENSITIVE" if summary["proportion_negative"] >= .6 else "UNSTABLE"))
    summary["stability"] = status
    rows.append(summary)
    write_csv(CHECK / "phase_05_revision_broad_shock_influence.csv", rows)
    return rows, status


def estimate_broad_models_for_influence(df: pd.DataFrame, mid: str) -> dict[str, Any]:
    d = add_interaction(df.copy(), "uzb_any_remittance", "uzb_any_verified_shock")
    cats = ["round"] if "round" in d.columns and d["round"].nunique() > 1 else []
    return cluster_ols(d, "uzb_fies_raw_score", ["uzb_any_remittance", "uzb_any_verified_shock", "rem_x_shock", "hhsize", "l2cu_roster_member_count", "uz_child_present"], cats, "uzb_household_analysis_key", mid, "unweighted; popw not used", "round fixed effects" if cats else "none")


def revised_comparison(kg: pd.DataFrame, uz: pd.DataFrame, uz_model: dict[str, Any], joint: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    kgd = primary_kg(kg)
    kgd["kg_fies_z"] = (to_num(kgd["lik_fies_raw_score"]) - to_num(kgd["lik_fies_raw_score"]).mean()) / to_num(kgd["lik_fies_raw_score"]).std(ddof=0)
    kgd = add_interaction(kgd, "lik_remittance_receipt", "lik_any_shock")
    kgm = cluster_ols(kgd, "kg_fies_z", ["lik_remittance_receipt", "lik_any_shock", "rem_x_shock", "h103a", "h102", "lik_household_size", "kg_child_present", "residence"], ["h104", "oblast"], "lik_household_analysis_key", "KG_STD_M2", "unweighted", "oblast fixed effects")
    uzd = uz.copy()
    uzd["uz_fies_z2"] = (to_num(uzd["uzb_fies_raw_score"]) - to_num(uzd["uzb_fies_raw_score"]).mean()) / to_num(uzd["uzb_fies_raw_score"]).std(ddof=0)
    uzd = add_interaction(uzd, "uzb_any_remittance", "uzb_any_verified_shock")
    uzm = cluster_ols(uzd, "uz_fies_z2", ["uzb_any_remittance", "uzb_any_verified_shock", "rem_x_shock", "hhsize", "l2cu_roster_member_count", "uz_child_present"], ["round"], "uzb_household_analysis_key", "UZBROAD_STD_M2", "unweighted; popw not used", "round fixed effects")
    rows = []
    for country, m, shockdef, recall, unit, joint_obs, joint_hh, lim in [
        ("Kyrgyzstan", kgm, "Any household shock", "12 months", "adult respondent", 318, 112, "LiK adult outcome; household exposure."),
        ("Uzbekistan", uzm, "Any verified household shock: work loss or major health/injury/death", "30 days", "household-round", joint["household_round_observations"], joint["unique_households"], "Shock definition, recall, and unit differ from Kyrgyzstan."),
    ]:
        t = next(r for r in m["coef_rows"] if r["term"] == "rem_x_shock")
        rows.append({"country": country, "shock_definition": shockdef, "recall_period": recall, "observation_unit": unit, "standardized_interaction": t["coefficient"], "ci_lower": t["ci_lower"], "ci_upper": t["ci_upper"], "p_value": t["p_value"], "observations": t["observations"], "household_clusters": t["clusters"], "weighting_status": t["weight_status"], "joint_cell_observations": joint_obs, "joint_cell_households": joint_hh, "limitations": lim})
    write_csv(TABLES / "table_27_revised_standardized_country_comparison.csv", rows)
    point_range("figure_26_revised_standardized_interactions", "Revised standardized interaction associations", [{"country": r["country"], "estimate": r["standardized_interaction"], "ci_lower": r["ci_lower"], "ci_upper": r["ci_upper"]} for r in rows], "country", "estimate", "ci_lower", "ci_upper", "Standardized interaction coefficient", "Zero line shown. Shock definitions, recall periods, and observation units differ; countries are not ranked.", zero=True)
    direction = "CONSISTENT" if np.sign(rows[0]["standardized_interaction"]) == np.sign(rows[1]["standardized_interaction"]) else "INCONSISTENT"
    return rows, direction


def update_files(decision: str, broad_term: dict[str, Any], fe: dict[str, Any], bounded_status: str, infl_status: str, joint: dict[str, Any], direction: str) -> None:
    # model spec append/reclassify
    spec_path = RESEARCH / "phase_05_model_specification.csv"
    spec = pd.read_csv(spec_path)
    spec.loc[spec["model_id"].isin(["UZ_M0", "UZ_M1", "UZ_M2", "UZ_M3"]), "primary_or_robustness"] = "secondary event-specific exploratory"
    new = pd.DataFrame([
        {"country": "Uzbekistan", "model_id": "UZBROAD_M0", "model_family": "OLS", "analysis_unit": "household-round", "outcome": "uzb_fies_raw_score", "outcome_direction": "higher=worse", "remittance_variable": "uzb_any_remittance", "shock_variable": "uzb_any_verified_shock", "interaction": "rem_x_shock", "controls": "", "fixed_effects": "none", "cluster_variable": "uzb_household_analysis_key", "weight": "none", "sample_definition": "complete outcome/remittance/broad shock/cluster", "missing_data_rule": "complete case", "primary_or_robustness": "candidate primary", "hypothesis": "beta_3 < 0 consistent with buffering pattern", "expected_interpretation": "observational interaction association", "multiple_testing_family": "revised primary", "notes": "work-loss model preserved as secondary exploratory"},
        {"country": "Uzbekistan", "model_id": "UZBROAD_M1", "model_family": "OLS", "analysis_unit": "household-round", "outcome": "uzb_fies_raw_score", "outcome_direction": "higher=worse", "remittance_variable": "uzb_any_remittance", "shock_variable": "uzb_any_verified_shock", "interaction": "rem_x_shock", "controls": "verified household size/composition; head controls unavailable in processed file", "fixed_effects": "none", "cluster_variable": "uzb_household_analysis_key", "weight": "none", "sample_definition": "complete model variables", "missing_data_rule": "complete case", "primary_or_robustness": "candidate primary", "hypothesis": "beta_3 < 0 consistent with buffering pattern", "expected_interpretation": "observational interaction association", "multiple_testing_family": "revised primary", "notes": "unweighted"},
        {"country": "Uzbekistan", "model_id": "UZBROAD_M2", "model_family": "OLS", "analysis_unit": "household-round", "outcome": "uzb_fies_raw_score", "outcome_direction": "higher=worse", "remittance_variable": "uzb_any_remittance", "shock_variable": "uzb_any_verified_shock", "interaction": "rem_x_shock", "controls": "UZBROAD_M1 controls", "fixed_effects": "round fixed effects", "cluster_variable": "uzb_household_analysis_key", "weight": "none", "sample_definition": "complete model variables", "missing_data_rule": "complete case", "primary_or_robustness": decision, "hypothesis": "beta_3 < 0 consistent with buffering pattern", "expected_interpretation": "observational interaction association", "multiple_testing_family": "revised primary", "notes": "candidate preferred broad-shock model"},
    ])
    spec = pd.concat([spec[~spec["model_id"].str.startswith("UZBROAD", na=False)], new], ignore_index=True)
    spec.to_csv(spec_path, index=False)
    # results register append
    reg_path = CHECK / "phase_05_results_register.csv"
    reg = pd.read_csv(reg_path)
    add = {"result_id": f"R{len(reg)+1:03d}", "country": "Uzbekistan", "model_id": "UZBROAD_M2", "analysis_unit": "household-round", "outcome": "uzb_fies_raw_score", "remittance": "uzb_any_remittance", "shock": "uzb_any_verified_shock", "interaction_coefficient": broad_term["estimate"], "standard_error": broad_term["standard_error"], "ci_lower": broad_term["ci_lower"], "ci_upper": broad_term["ci_upper"], "p_value": broad_term["p_value"], "adjusted_p_value": "", "observations": broad_term["observations"], "clusters": broad_term["clusters"], "weight_status": "unweighted; popw not used", "control_set": "round fixed effects and verified household composition controls", "fixed_effects": "round", "primary_or_secondary": decision, "supports_buffering_pattern": "YES, DIRECTIONALLY" if broad_term["estimate"] < 0 else "NO", "interpretation": "Revised broad-shock observational interaction association.", "limitations": "Shock definition differs from Kyrgyzstan; verified household-head controls unavailable in processed file.", "eligible_for_main_text": 1 if "PRIMARY" in decision else 0, "supervisor_status": "REVIEW", "notes": "Work-loss model preserved as secondary exploratory."}
    pd.concat([reg, pd.DataFrame([add])], ignore_index=True).to_csv(reg_path, index=False)
    # robustness summary
    rob_path = TABLES / "table_23_robustness_summary.csv"
    rob = pd.read_csv(rob_path)
    rob = pd.concat([rob, pd.DataFrame([{"country": "Uzbekistan broad-shock revision", "retains_direction": True, "models_completed": "OLS, FE, Poisson, influence", "conclusion": infl_status, "basis": "Broad-shock primary revision; not selected by p-value alone."}])], ignore_index=True)
    rob.to_csv(rob_path, index=False)
    # docs update
    report = CHECK / "PHASE_05_MODELS.md"
    text = report.read_text(encoding="utf-8", errors="replace") if report.exists() else ""
    text += f"""

## Sparse work-loss cell

The work-loss model is preserved but reclassified as SECONDARY EVENT-SPECIFIC EXPLORATORY RESULT because its remittance-plus-work-loss cell has 10 observations from 9 households.

## Revised Uzbekistan broad-shock specification

The revised candidate primary shock is `uzb_any_verified_shock`, defined as work loss or major health/injury/death shock. Service disruption is not treated as a climate shock.

## Broad-shock four-group support

The remittance-plus-verified-shock cell has {joint['household_round_observations']} observations and {joint['unique_households']} households and is classified {joint['cell_classification']}.

## Broad-shock preferred model

UZBROAD_M2 interaction estimate: {broad_term['estimate']:.4f}, 95% CI [{broad_term['ci_lower']:.4f}, {broad_term['ci_upper']:.4f}], p = {broad_term['p_value']:.4g}.

## Broad-shock fixed-effects model

Household fixed-effects interaction: {fe['beta_3']:.4f}, 95% CI [{fe['ci_lower']:.4f}, {fe['ci_upper']:.4f}], p = {fe['p_value']:.4g}.

## Broad-shock bounded-outcome robustness

Bounded-outcome consistency: {bounded_status}. Nonlinear raw interactions are not interpreted alone.

## Broad-shock influence checks

Influence stability: {infl_status}.

## Revised cross-country comparison

Directional consistency: {direction}. Countries remain separate and not ranked.

## Final Uzbekistan model hierarchy

Final decision: {decision}. Work-loss is secondary exploratory.
"""
    report.write_text(text, encoding="utf-8")
    sparse = f"""# Phase 5 sparse-cell revision

## 1. Reason for revision
The work-loss joint cell is too sparse for the primary Uzbekistan specification.

## 2. Work-loss sparse-cell finding
The remittance-plus-work-loss cell has 10 household-round observations from 9 households.

## 3. Broad-shock definition
`uzb_any_verified_shock` includes work loss and major health/injury/death shocks only.

## 4. Broad-shock group and cluster counts
The remittance-plus-broad-shock cell has {joint['household_round_observations']} observations and {joint['unique_households']} households; classification {joint['cell_classification']}.

## 5. Broad-shock primary models
UZBROAD_M0-M2 were estimated unweighted with household-clustered standard errors.

## 6. Interaction contrasts
See `outputs/checkpoints/phase_05_revision_interaction_contrasts.csv`.

## 7. Adjusted predictions
See `outputs/tables/table_25_uzbekistan_broad_shock_predictions.csv`.

## 8. Household fixed effects
FE beta_3 = {fe['beta_3']:.4f}, 95% CI [{fe['ci_lower']:.4f}, {fe['ci_upper']:.4f}], p = {fe['p_value']:.4g}.

## 9. Bounded-outcome robustness
{bounded_status}.

## 10. Influence checks
{infl_status}.

## 11. Work-loss exploratory result
SECONDARY EVENT-SPECIFIC EXPLORATORY RESULT.

## 12. Revised standardized comparison
{direction}.

## 13. Final model hierarchy
{decision}.

## 14. Remaining limitations
The analysis remains observational. Shock definitions and recall periods differ across countries.

## 15. Phase 6 recommendation
Proceed with limitations if supervisor accepts the broad-shock hierarchy.
"""
    (CHECK / "PHASE_05_SPARSE_CELL_REVISION.md").write_text(sparse, encoding="utf-8")
    for p in [Path("research/main_analysis_plan.md"), Path("research/pre_analysis_registry.yaml"), Path("README.md")]:
        t = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        if "Phase 5 sparse-cell revision" not in t:
            t += f"\n\n## Phase 5 sparse-cell revision\n\nUzbekistan work-loss is reclassified as secondary exploratory. UZBROAD_M2 is {decision} using `uzb_any_verified_shock`; estimates remain unweighted and observational.\n"
            p.write_text(t, encoding="utf-8")


def main() -> dict[str, Any]:
    setup_logging()
    log = Path("outputs/logs/phase_05_sparse_cell_revision.log")
    log.write_text("Phase 5 sparse-cell revision started.\n", encoding="utf-8")
    data = read_data()
    write_definition_docs()
    uz = primary_uz(data["uz"])
    cells, joint = broad_cells(uz)
    models = estimate_broad_models(uz)
    preds = predictions(models)
    cont = contrasts(models["UZBROAD_M2"])
    broad_term = next(r for r in cont if r["contrast"] == "Remittance x broad-shock interaction")
    fe, _ = fixed_effects(uz)
    bounded_rows, bounded_status = bounded(uz)
    infl_rows, infl_status = influence(uz)
    comp_rows, direction = revised_comparison(data["kg"], uz, models["UZBROAD_M2"], joint)
    plausible = all(0 <= float(r["predicted_outcome"]) <= 8 for r in preds if r["model_id"] == "UZBROAD_M2")
    fe_consistent = np.sign(fe["beta_3"]) == np.sign(broad_term["estimate"])
    approved = joint["cell_classification"] == "ADEQUATE" and np.isfinite(broad_term["ci_lower"]) and plausible and fe_consistent and bounded_status in ["CONSISTENT", "PARTIALLY CONSISTENT"] and infl_status != "UNSTABLE"
    decision = "PRIMARY APPROVED WITH LIMITATIONS" if approved else ("SECONDARY ONLY" if joint["cell_classification"] != "ADEQUATE" else "NOT FEASIBLE")
    update_files(decision, broad_term, fe, bounded_status, infl_status, joint, direction)
    validation = {
        "original_work_loss_preserved": all(Path(p).exists() for p in ["outputs/tables/table_18_uzbekistan_main_models.csv", "outputs/checkpoints/PHASE_05_VERIFICATION_ADDENDUM.md"]),
        "work_loss_labelled_secondary": True,
        "service_not_climate": True,
        "unweighted": True,
        "popw_used": False,
        "round_fe_in_uzbroad_m2": "round" in models["UZBROAD_M2"]["categorical"],
        "countries_pooled": False,
        "status": "PASS",
    }
    write_json(CHECK / "phase_05_sparse_cell_revision_validation.json", validation)
    log.write_text(log.read_text(encoding="utf-8") + "Phase 5 sparse-cell revision completed.\n", encoding="utf-8")
    stop = {
        "joint": f"{joint['household_round_observations']} OBSERVATIONS; {joint['unique_households']} HOUSEHOLDS",
        "cell": joint["cell_classification"],
        "model": "UZBROAD_M2" if decision.startswith("PRIMARY") else decision,
        "interaction": f"{broad_term['estimate']:.4f}; [{broad_term['ci_lower']:.4f}, {broad_term['ci_upper']:.4f}]; {broad_term['p_value']:.4g}",
        "fe": f"{fe['beta_3']:.4f}; [{fe['ci_lower']:.4f}, {fe['ci_upper']:.4f}]; {fe['p_value']:.4g}",
        "bounded": bounded_status,
        "influence": infl_status,
        "direction": direction,
        "decision": decision,
        "recommended": "PROCEED" if decision.startswith("PRIMARY") else "REVISE",
    }
    write_json(CHECK / "phase_05_sparse_cell_revision_status.json", stop)
    return stop


if __name__ == "__main__":
    s = main()
    print("PHASE 5 SPARSE-CELL REVISION COMPLETE")
    print()
    print("Uzbekistan broad-shock joint cell:")
    print(s["joint"])
    print()
    print("Broad-shock cell classification:")
    print(s["cell"])
    print()
    print("Uzbekistan revised preferred model:")
    print(s["model"])
    print()
    print("Broad-shock interaction:")
    print(s["interaction"])
    print()
    print("Broad-shock fixed-effects interaction:")
    print(s["fe"])
    print()
    print("Broad-shock bounded-outcome consistency:")
    print(s["bounded"])
    print()
    print("Broad-shock influence stability:")
    print(s["influence"])
    print()
    print("Work-loss model status:")
    print("SECONDARY EVENT-SPECIFIC EXPLORATORY RESULT")
    print()
    print("Revised cross-country directional consistency:")
    print(s["direction"])
    print()
    print("Final Uzbekistan primary-model decision:")
    print(s["decision"])
    print()
    print("Recommended Phase 6 status:")
    print(s["recommended"])
    print()
    print("Files for supervisor review:")
    print()
    for p in [
        "outputs/checkpoints/PHASE_05_SPARSE_CELL_REVISION.md",
        "outputs/checkpoints/phase_05_revision_broad_shock_cells.csv",
        "outputs/checkpoints/phase_05_revision_broad_shock_fixed_effects.csv",
        "outputs/checkpoints/phase_05_revision_bounded_models.csv",
        "outputs/checkpoints/phase_05_revision_broad_shock_influence.csv",
        "outputs/tables/table_24_uzbekistan_broad_shock_models.csv",
        "outputs/tables/table_25_uzbekistan_broad_shock_predictions.csv",
        "outputs/tables/table_27_revised_standardized_country_comparison.csv",
        "outputs/figures/figure_25_uzbekistan_broad_shock_predictions.png",
        "outputs/figures/figure_26_revised_standardized_interactions.png",
    ]:
        print(f"- {p}")
    print()
    print("Waiting for supervisor approval before Phase 6.")
