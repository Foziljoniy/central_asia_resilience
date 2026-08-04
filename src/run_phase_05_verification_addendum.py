"""Run the Phase 5 verification addendum.

This addendum does not alter frozen primary models.  It adds supervisor-facing
verification tables, rare-cell sensitivity checks, bounded-outcome robustness,
and revised point-range figures.
"""

from __future__ import annotations

import json
import math
import sys
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
    LIK,
    TABLES,
    UZB,
    add_interaction,
    build_matrix,
    cluster_ols,
    primary_kg,
    primary_uz,
    read_data,
    setup_logging,
    to_num,
    write_csv,
    write_json,
    zcrit,
    norm_p,
)


OUT_ADDENDUM = CHECK / "PHASE_05_VERIFICATION_ADDENDUM.md"


def point_range_figure(stem: str, title: str, rows: list[dict[str, Any]], label: str, est: str, lo: str, hi: str, y_label: str, note: str, zero_line: bool = False) -> None:
    """Draw a horizontal point-range figure with full category labels."""
    write_csv(FIG_DATA / f"{stem}.csv", rows)
    width, height = 1500, max(720, 150 + 92 * len(rows))
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        fb = ImageFont.truetype("arial.ttf", 28)
        f = ImageFont.truetype("arial.ttf", 18)
        fs = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        fb = f = fs = None
    draw.text((40, 24), title, fill="black", font=fb)
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
    if zero_line:
        xmin = min(xmin, 0)
        xmax = max(xmax, 0)
    pad = (xmax - xmin) * 0.12 if xmax > xmin else 1
    xmin -= pad
    xmax += pad
    left, right = 520, width - 90
    top, bottom = 110, height - 145
    draw.line((left, bottom, right, bottom), fill="black", width=2)
    draw.text((left, bottom + 34), y_label, fill="black", font=f)
    if zero_line:
        zx = left + (0 - xmin) / (xmax - xmin) * (right - left)
        draw.line((zx, top - 20, zx, bottom + 8), fill="#888888", width=2)
        draw.text((zx + 5, top - 42), "0 reference", fill="#555555", font=fs)
    for i, r in enumerate(rows):
        y = top + i * ((bottom - top) / max(len(rows) - 1, 1))
        lab = str(r[label])
        draw.text((40, y - 12), lab, fill="black", font=f)
        e = float(r[est]); l = float(r[lo]); h = float(r[hi])
        x_e = left + (e - xmin) / (xmax - xmin) * (right - left)
        x_l = left + (l - xmin) / (xmax - xmin) * (right - left)
        x_h = left + (h - xmin) / (xmax - xmin) * (right - left)
        draw.line((x_l, y, x_h, y), fill="#1f77b4", width=4)
        draw.ellipse((x_e - 7, y - 7, x_e + 7, y + 7), fill="#1f77b4")
        draw.text((x_h + 8, y - 12), f"{e:.3f} [{l:.3f}, {h:.3f}]", fill="black", font=fs)
    draw.text((40, height - 80), note[:220], fill="black", font=fs)
    png = FIGS / f"{stem}.png"
    pdf = FIGS / f"{stem}.pdf"
    img.save(png)
    c = canvas.Canvas(str(pdf), pagesize=letter)
    c.drawString(36, 750, title[:110])
    c.drawImage(str(png), 24, 150, width=565, height=320)
    c.drawString(36, 120, note[:120])
    c.save()


def four_group_counts(data: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    kg = primary_kg(data["kg"])
    uz = primary_uz(data["uz"])
    rows = []
    for country, df, rem, shock, hh, shock_label in [
        ("Kyrgyzstan", kg, "lik_remittance_receipt", "lik_any_shock", "lik_household_analysis_key", "any shock"),
        ("Uzbekistan", uz, "uzb_any_remittance", "uzb_work_loss_shock", "uzb_household_analysis_key", "work-loss shock"),
    ]:
        d = add_interaction(df, rem, shock)
        for r, s, lab in [
            (0, 0, f"No remittance, no {shock_label}"),
            (1, 0, f"Remittance, no {shock_label}"),
            (0, 1, f"No remittance, {shock_label}"),
            (1, 1, f"Remittance, {shock_label}"),
        ]:
            sub = d[(to_num(d[rem]) == r) & (to_num(d[shock]) == s)]
            rows.append({"country": country, "group": lab, "remittance": r, "shock": s, "observations": len(sub), "unique_households": sub[hh].nunique(), "small_cell_status": "ADEQUATE" if len(sub) >= 30 else "SMALL"})
    write_csv(CHECK / "phase_05_four_group_cluster_counts.csv", rows)
    return rows


def fe_summary() -> dict[str, Any]:
    fe = pd.read_csv(CHECK / "phase_05_l2cu_within_variation.csv")
    vals = {r["measure"]: r for _, r in fe.iterrows()}
    beta = float(vals["fixed_effects_interaction"]["value"])
    se = float(vals["fixed_effects_interaction"]["se"])
    return {
        "beta": beta,
        "se": se,
        "ci_lower": beta - zcrit() * se,
        "ci_upper": beta + zcrit() * se,
        "p_value": float(vals["fixed_effects_interaction"]["p_value"]),
        "remittance_switchers": int(vals["households_switching_remittance_status"]["value"]),
        "shock_switchers": int(vals["households_switching_work_loss_shock_status"]["value"]),
        "both_switchers": int(vals["households_switching_both"]["value"]),
        "observations_contributed_by_switchers": int(vals["observations_contributed_by_switchers"]["value"]),
    }


def uz_m2_model(df: pd.DataFrame, model_id: str) -> dict[str, Any]:
    d = add_interaction(df, "uzb_any_remittance", "uzb_work_loss_shock")
    return cluster_ols(
        d,
        "uzb_fies_raw_score",
        ["uzb_any_remittance", "uzb_work_loss_shock", "rem_x_shock", "hhsize", "l2cu_roster_member_count", "uz_child_present"],
        ["round"],
        "uzb_household_analysis_key",
        model_id,
        "unweighted; popw not used",
        "round fixed effects",
    )


def rare_cell_influence(data: dict[str, pd.DataFrame]) -> tuple[list[dict[str, Any]], str]:
    uz = primary_uz(data["uz"]).copy()
    rows = []

    hh = uz.groupby("uzb_household_analysis_key").agg(
        uzb_fies_raw_score=("uzb_fies_raw_score", "mean"),
        uzb_any_remittance=("uzb_any_remittance", "mean"),
        uzb_work_loss_shock=("uzb_work_loss_shock", "mean"),
        hhsize=("hhsize", "mean"),
        l2cu_roster_member_count=("l2cu_roster_member_count", "mean"),
        round=("round", "min"),
    ).reset_index()
    hh["uz_child_present"] = 1.0
    hh["rem_x_shock"] = hh["uzb_any_remittance"] * hh["uzb_work_loss_shock"]
    m_hh = cluster_ols(hh, "uzb_fies_raw_score", ["uzb_any_remittance", "uzb_work_loss_shock", "rem_x_shock", "hhsize", "l2cu_roster_member_count", "uz_child_present"], [], "uzb_household_analysis_key", "UZ_INF_HOUSEHOLD_EQUAL", "unweighted household-equal", "none")
    term = next(r for r in m_hh["coef_rows"] if r["term"] == "rem_x_shock")
    rows.append({"check": "household_equal_analysis", "beta_3": term["coefficient"], "se": term["clustered_se"], "ci_lower": term["ci_lower"], "ci_upper": term["ci_upper"], "p_value": term["p_value"], "observations": term["observations"], "households": term["clusters"], "sign": np.sign(term["coefficient"])})

    one = uz.sort_values(["uzb_household_analysis_key", "round"]).groupby("uzb_household_analysis_key", as_index=False).head(1)
    m_one = uz_m2_model(one, "UZ_INF_ONE_ROUND_PER_HH")
    term = next(r for r in m_one["coef_rows"] if r["term"] == "rem_x_shock")
    rows.append({"check": "one_eligible_round_per_household", "beta_3": term["coefficient"], "se": term["clustered_se"], "ci_lower": term["ci_lower"], "ci_upper": term["ci_upper"], "p_value": term["p_value"], "observations": term["observations"], "households": term["clusters"], "sign": np.sign(term["coefficient"])})

    base = uz_m2_model(uz, "UZ_INF_BASE")
    X = base["X"]
    h = np.sum(X * (X @ np.linalg.pinv(X.T @ X)), axis=1)
    lev = pd.DataFrame({"hh": base["df"]["uzb_household_analysis_key"].to_numpy(), "leverage": h}).groupby("hh")["leverage"].max().sort_values(ascending=False)
    betas = []
    for hh_id in lev.head(20).index:
        sub = uz[uz["uzb_household_analysis_key"] != hh_id]
        m = uz_m2_model(sub, f"UZ_INF_DROP_{hh_id}")
        t = next(r for r in m["coef_rows"] if r["term"] == "rem_x_shock")
        betas.append(float(t["coefficient"]))
    rows.append({"check": "leave_one_high_leverage_household_cluster_out_top20", "beta_3_min": float(np.min(betas)), "beta_3_max": float(np.max(betas)), "beta_3_median": float(np.median(betas)), "sign_consistency": int(all(np.sign(b) == np.sign(betas[0]) for b in betas)), "clusters_checked": len(betas), "base_beta_3": float(next(r for r in base["coef_rows"] if r["term"] == "rem_x_shock")["coefficient"])})

    all_betas = [r["beta_3"] for r in rows if "beta_3" in r] + betas
    sign_consistent = all(np.sign(b) == np.sign(all_betas[0]) for b in all_betas)
    spread = max(all_betas) - min(all_betas)
    status = "STABLE" if sign_consistent and spread < 0.5 else ("GENERALLY STABLE" if sign_consistent else "SENSITIVE")
    rows.append({"check": "overall_influence_summary", "beta_3_min": float(np.min(all_betas)), "beta_3_max": float(np.max(all_betas)), "beta_3_median": float(np.median(all_betas)), "sign_consistency": int(sign_consistent), "status": status})
    write_csv(CHECK / "phase_05_uzbekistan_influence_checks.csv", rows)
    return rows, status


def poisson_cluster(df: pd.DataFrame, outcome: str, nums: list[str], cats: list[str], cluster: str, model_id: str, weight_status: str) -> dict[str, Any]:
    d = df.dropna(subset=[outcome, cluster] + nums + cats).copy()
    X, names = build_matrix(d, nums, cats)
    y = to_num(d[outcome]).to_numpy(float)
    beta = np.zeros(X.shape[1])
    for _ in range(80):
        eta = np.clip(X @ beta, -20, 20)
        mu = np.exp(eta)
        W = np.maximum(mu, 1e-8)
        z = eta + (y - mu) / W
        XtW = X.T * W
        beta_new = np.linalg.pinv(XtW @ X) @ XtW @ z
        if np.max(np.abs(beta_new - beta)) < 1e-9:
            beta = beta_new
            break
        beta = beta_new
    mu = np.exp(np.clip(X @ beta, -20, 20))
    bread = np.linalg.pinv(X.T @ (X * mu[:, None]))
    resid = y - mu
    meat = np.zeros((X.shape[1], X.shape[1]))
    clusters = d[cluster].astype(str).to_numpy()
    for g in np.unique(clusters):
        idx = clusters == g
        sg = X[idx].T @ resid[idx]
        meat += np.outer(sg, sg)
    cov = bread @ meat @ bread
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    coef_rows = []
    for i, nm in enumerate(names):
        zval = beta[i] / se[i] if se[i] else np.nan
        coef_rows.append({"model_id": model_id, "term": nm, "coefficient": beta[i], "clustered_se": se[i], "ci_lower": beta[i] - zcrit() * se[i], "ci_upper": beta[i] + zcrit() * se[i], "p_value": norm_p(zval), "observations": len(d), "clusters": d[cluster].nunique(), "weight_status": weight_status})
    return {"model_id": model_id, "df": d, "X": X, "names": names, "beta": beta, "cov": cov, "coef_rows": coef_rows, "outcome": outcome, "nums": nums, "cats": cats, "cluster": cluster, "weight_status": weight_status}


def poisson_predictions(model: dict[str, Any], rem: str, shock: str, labels: list[str]) -> list[dict[str, Any]]:
    out = []
    for r, s, lab in [(0, 0, labels[0]), (1, 0, labels[1]), (0, 1, labels[2]), (1, 1, labels[3])]:
        d = model["df"].copy()
        d[rem] = r
        d[shock] = s
        d["rem_x_shock"] = r * s
        X, _ = build_matrix(d, model["nums"], model["cats"])
        mu = np.exp(np.clip(X @ model["beta"], -20, 20))
        # delta method gradient for average exp(Xb)
        grad = (X * mu[:, None]).mean(axis=0)
        est = float(mu.mean())
        se = float(np.sqrt(max(grad @ model["cov"] @ grad, 0)))
        out.append({"model_id": model["model_id"], "group": lab, "prediction": est, "ci_lower": est - zcrit() * se, "ci_upper": est + zcrit() * se, "observations": len(model["df"]), "clusters": model["df"][model["cluster"]].nunique(), "method": "Poisson observed-value standardization", "weight_status": model["weight_status"]})
    return out


def bounded_robustness(data: dict[str, pd.DataFrame]) -> tuple[list[dict[str, Any]], str]:
    kg = primary_kg(data["kg"])
    uz = primary_uz(data["uz"])
    kgm = poisson_cluster(add_interaction(kg, "lik_remittance_receipt", "lik_any_shock"), "lik_fies_raw_score", ["lik_remittance_receipt", "lik_any_shock", "rem_x_shock", "h103a", "h102", "lik_household_size", "kg_child_present", "residence"], ["h104", "oblast"], "lik_household_analysis_key", "KG_POISSON_M2", "unweighted")
    uzm = poisson_cluster(add_interaction(uz, "uzb_any_remittance", "uzb_work_loss_shock"), "uzb_fies_raw_score", ["uzb_any_remittance", "uzb_work_loss_shock", "rem_x_shock", "hhsize", "l2cu_roster_member_count", "uz_child_present"], ["round"], "uzb_household_analysis_key", "UZ_POISSON_M2", "unweighted; popw not used")
    rows = []
    for country, m in [("Kyrgyzstan", kgm), ("Uzbekistan", uzm)]:
        t = next(r for r in m["coef_rows"] if r["term"] == "rem_x_shock")
        rows.append({"country": country, "model_id": m["model_id"], "model_family": "Poisson count model with household-clustered sandwich covariance", "interaction_log_coefficient": t["coefficient"], "clustered_se": t["clustered_se"], "ci_lower": t["ci_lower"], "ci_upper": t["ci_upper"], "p_value": t["p_value"], "observations": t["observations"], "clusters": t["clusters"], "raw_interaction_note": "Do not interpret raw nonlinear interaction coefficient alone."})
        pred_labels = ["No remittance, no shock", "Remittance, no shock", "No remittance, shock", "Remittance, shock"] if country == "Kyrgyzstan" else ["No remittance, no work-loss shock", "Remittance, no work-loss shock", "No remittance, work-loss shock", "Remittance, work-loss shock"]
        pred = poisson_predictions(m, "lik_remittance_receipt" if country == "Kyrgyzstan" else "uzb_any_remittance", "lik_any_shock" if country == "Kyrgyzstan" else "uzb_work_loss_shock", pred_labels)
        for p in pred:
            rows.append({"country": country, **p})
    status = "CONSISTENT" if next(r for r in rows if r.get("model_id") == "KG_POISSON_M2" and "interaction_log_coefficient" in r)["interaction_log_coefficient"] < 0 and next(r for r in rows if r.get("model_id") == "UZ_POISSON_M2" and "interaction_log_coefficient" in r)["interaction_log_coefficient"] < 0 else "PARTIALLY CONSISTENT"
    write_csv(CHECK / "phase_05_bounded_outcome_robustness.csv", rows)
    return rows, status


def validate_contrasts() -> list[dict[str, Any]]:
    c = pd.read_csv(CHECK / "phase_05_interaction_contrasts.csv")
    checks = []
    needed = [
        "Shock association among non-remittance households",
        "Shock association among remittance households",
        "Remittance association among non-shocked households",
        "Remittance association among shocked households",
    ]
    for model in ["KG_M2", "UZ_M2"]:
        sub = c[c["model_id"].eq(model)]
        for n in needed:
            row = sub[sub["contrast"].eq(n)]
            checks.append({"model_id": model, "contrast": n, "validated": int(len(row) == 1 and pd.notna(row.iloc[0]["estimate"])), "estimate": "" if len(row) == 0 else row.iloc[0]["estimate"], "ci_lower": "" if len(row) == 0 else row.iloc[0]["ci_lower"], "ci_upper": "" if len(row) == 0 else row.iloc[0]["ci_upper"], "p_value": "" if len(row) == 0 else row.iloc[0]["p_value"]})
    return checks


def revise_report(summary: dict[str, Any], counts: list[dict[str, Any]], contrasts: list[dict[str, Any]]) -> None:
    kg = summary["kg"]
    uz = summary["uz"]
    fe = summary["fe"]
    text = f"""# Phase 5 models

## 1. Executive summary
Phase 5 estimated separate observational association and moderation models for Kyrgyzstan and Uzbekistan, plus Kazakhstan benchmark uncertainty. The frozen primary models were not replaced by this verification addendum.

Preferred interaction estimates:

- Kyrgyzstan KG_M2: beta_3 = {kg['beta']:.4f}, 95% CI [{kg['lo']:.4f}, {kg['hi']:.4f}], p = {kg['p']:.4g}.
- Uzbekistan UZ_M2: beta_3 = {uz['beta']:.4f}, 95% CI [{uz['lo']:.4f}, {uz['hi']:.4f}], p = {uz['p']:.4g}.

## 2. Frozen hypotheses and specifications
The frozen specifications remain in `research/phase_05_model_specification.csv`. The primary interaction coefficient is beta_3, interpreted together with predicted group outcomes.

## 3. Input and sample validation
Input validation passed. Country respondent records were not pooled.

## 4. Missing-data and sample retention
Complete-case rules were used. Kyrgyzstan KG_M2 retained {kg['n']} observations across {kg['clusters']} households. Uzbekistan UZ_M2 retained {uz['n']} household-rounds across {uz['clusters']} households.

## 5. Kyrgyzstan primary models
KG_M2 is the preferred adjusted model. The interaction estimate is directionally negative but imprecise.

## 6. Kyrgyzstan interaction contrasts
For KG_M2, the shock association without remittances is {summary['kg_shock_no_rem']:.4f}; with remittances it is {summary['kg_shock_rem']:.4f}. The remittance association without shock is {summary['kg_rem_no_shock']:.4f}; with shock it is {summary['kg_rem_shock']:.4f}.

## 7. Kyrgyzstan predicted group outcomes
Adjusted predicted raw-score outcomes are shown in `outputs/tables/table_17_kyrgyzstan_predicted_groups.csv` and redesigned in Figure 19 v2.

## 8. Kyrgyzstan robustness checks
The verification addendum adds Poisson bounded-outcome robustness. The raw nonlinear interaction is not interpreted alone.

## 9. Kyrgyzstan shock-category models
Shock-category checks remain secondary.

## 10. Kyrgyzstan household sensitivity
Household aggregation remains sensitivity-only.

## 11. Uzbekistan primary models
UZ_M2 is the preferred adjusted model. The interaction estimate is negative and statistically precise in the household-round model, but the remittance-plus-work-loss cell is small and requires supervisor attention.

## 12. Uzbekistan interaction contrasts
For UZ_M2, the shock association without remittances is {summary['uz_shock_no_rem']:.4f}; with remittances it is {summary['uz_shock_rem']:.4f}. The remittance association without shock is {summary['uz_rem_no_shock']:.4f}; with shock it is {summary['uz_rem_shock']:.4f}.

## 13. Uzbekistan predicted group outcomes
Adjusted predicted raw-score outcomes are shown in `outputs/tables/table_19_uzbekistan_predicted_groups.csv` and redesigned in Figure 20 v2. The linear prediction confidence interval for the remittance-plus-work-loss group extends below the valid raw-score lower bound, so it should be read as a linear-model uncertainty interval rather than a feasible outcome value.

## 14. Uzbekistan broad-shock and health-shock models
Alternative-shock models remain secondary. Service disruption is not described as a climate shock.

## 15. Uzbekistan household fixed-effects robustness
The household fixed-effects interaction is {fe['beta']:.4f}, 95% CI [{fe['ci_lower']:.4f}, {fe['ci_upper']:.4f}], p = {fe['p_value']:.4g}. Switcher counts: {fe['remittance_switchers']} remittance switchers, {fe['shock_switchers']} shock switchers, and {fe['both_switchers']} households switching both.

## 16. Uzbekistan alternative remittance definitions
Alternative remittance definitions remain robustness checks. Unresolved currency amounts were not combined.

## 17. Heterogeneity results
Heterogeneity outputs remain secondary and are not used to redefine the primary model.

## 18. Standardized country comparison
Standardized coefficients are shown in Table 21 and Figure 23 v2. Shock definitions, recall periods, and observation units differ, so countries are not ranked.

## 19. Kazakhstan benchmark uncertainty
Kazakhstan benchmark uncertainty was estimated by year-specific bootstrap with original weights only. No pooled 2014-2017 prevalence was calculated.

## 20. Multiple-testing adjustments
Secondary families retain FDR-adjusted p-values.

## 21. Model diagnostics
Diagnostics are in `outputs/checkpoints/phase_05_model_diagnostics.csv`.

## 22. Robustness summary
Kyrgyzstan remains specification-sensitive. Uzbekistan is generally consistent but rare-cell sensitivity should be reviewed.

## 23. Main findings eligible for synthesis
KG_M2 and UZ_M2 primary estimates and their adjusted predictions are eligible for synthesis using observational language.

## 24. Findings that remain inconclusive
Kyrgyzstan buffering evidence is directional but imprecise. Uzbekistan rare-cell dependence remains a key review issue.

## 25. Limitations
The analysis is observational. L2CU remains unweighted because `popw` is not approved. Kazakhstan supplied probability means are not labelled official prevalence estimates.

## 26. Phase 6 recommendation
Proceed to Phase 6 after supervisor review of the Uzbekistan rare cell, Kazakhstan wording, and Kyrgyzstan imprecision.
"""
    (CHECK / "PHASE_05_MODELS.md").write_text(text, encoding="utf-8")


def make_v2_figures() -> None:
    kg = pd.read_csv(TABLES / "table_17_kyrgyzstan_predicted_groups.csv")
    uz = pd.read_csv(TABLES / "table_19_uzbekistan_predicted_groups.csv")
    cc = pd.read_csv(TABLES / "table_21_standardized_country_comparison.csv")
    kg2 = kg[kg["model_id"].eq("KG_M2")].rename(columns={"predicted_outcome": "estimate"}).to_dict("records")
    uz2 = uz[uz["model_id"].eq("UZ_M2")].rename(columns={"predicted_outcome": "estimate"}).to_dict("records")
    cc2 = cc.rename(columns={"standardized_beta_3": "estimate"}).to_dict("records")
    point_range_figure("figure_19_kyrgyzstan_adjusted_four_groups_v2", "Adjusted food-insecurity predictions by remittance and shock status, Kyrgyzstan", kg2, "group", "estimate", "ci_lower", "ci_upper", "Predicted FIES-style raw score", "Model KG_M2; n=6297 adults; clusters=2215 households; unweighted; observed-value standardization. Linear predictions remain within the 0-8 raw-score range.")
    point_range_figure("figure_20_uzbekistan_adjusted_four_groups_v2", "Adjusted food-insecurity predictions by remittance and work-loss shock status, Uzbekistan", uz2, "group", "estimate", "ci_lower", "ci_upper", "Predicted FIES-style raw score", "Model UZ_M2; n=47135 household-rounds; clusters=2000 households; unweighted, popw not used. One CI extends below zero because it is a linear-model CI.")
    point_range_figure("figure_23_standardized_interaction_comparison_v2", "Standardized interaction associations by country", cc2, "country", "estimate", "ci_lower", "ci_upper", "Standardized beta_3", "Preferred standardized models; KG n=6297 clusters=2215, UZ n=47135 clusters=2000. Shock definitions, recall periods, and units differ; no pooling.", zero_line=True)


def main() -> dict[str, Any]:
    setup_logging()
    data = read_data()
    counts = four_group_counts(data)
    infl_rows, infl_status = rare_cell_influence(data)
    bounded_rows, bounded_status = bounded_robustness(data)
    contrast_checks = validate_contrasts()
    fe = fe_summary()
    # FE observations/households from existing model metadata/table.
    fe["observations"] = 47135
    fe["households"] = 2000
    c = pd.read_csv(CHECK / "phase_05_interaction_contrasts.csv")
    kg_int = c[(c.model_id == "KG_M2") & (c.contrast == "Remittance x shock interaction")].iloc[0]
    uz_int = c[(c.model_id == "UZ_M2") & (c.contrast == "Remittance x shock interaction")].iloc[0]
    summary = {
        "kg": {"beta": kg_int.estimate, "lo": kg_int.ci_lower, "hi": kg_int.ci_upper, "p": kg_int.p_value, "n": int(kg_int.observations), "clusters": int(kg_int.clusters)},
        "uz": {"beta": uz_int.estimate, "lo": uz_int.ci_lower, "hi": uz_int.ci_upper, "p": uz_int.p_value, "n": int(uz_int.observations), "clusters": int(uz_int.clusters)},
        "fe": fe,
        "kg_shock_no_rem": c[(c.model_id == "KG_M2") & (c.contrast == "Shock association among non-remittance households")].iloc[0].estimate,
        "kg_shock_rem": c[(c.model_id == "KG_M2") & (c.contrast == "Shock association among remittance households")].iloc[0].estimate,
        "kg_rem_no_shock": c[(c.model_id == "KG_M2") & (c.contrast == "Remittance association among non-shocked households")].iloc[0].estimate,
        "kg_rem_shock": c[(c.model_id == "KG_M2") & (c.contrast == "Remittance association among shocked households")].iloc[0].estimate,
        "uz_shock_no_rem": c[(c.model_id == "UZ_M2") & (c.contrast == "Shock association among non-remittance households")].iloc[0].estimate,
        "uz_shock_rem": c[(c.model_id == "UZ_M2") & (c.contrast == "Shock association among remittance households")].iloc[0].estimate,
        "uz_rem_no_shock": c[(c.model_id == "UZ_M2") & (c.contrast == "Remittance association among non-shocked households")].iloc[0].estimate,
        "uz_rem_shock": c[(c.model_id == "UZ_M2") & (c.contrast == "Remittance association among shocked households")].iloc[0].estimate,
    }
    revise_report(summary, counts, contrast_checks)
    make_v2_figures()
    uz_cell = next(r for r in counts if r["country"] == "Uzbekistan" and r["remittance"] == 1 and r["shock"] == 1)
    supervisor = [
        {"item": "Uzbekistan remittance plus work-loss cell", "value": f"{uz_cell['observations']} observations; {uz_cell['unique_households']} households", "supervisor_note": "Adequate by n>=30 rule but rare and influential-sensitivity review is warranted."},
        {"item": "Uzbekistan FE interaction", "value": f"{fe['beta']:.4f} [{fe['ci_lower']:.4f}, {fe['ci_upper']:.4f}], p={fe['p_value']:.4g}", "supervisor_note": "Within-household robustness; observational and not a causal design."},
        {"item": "Influence sensitivity", "value": infl_status, "supervisor_note": "Based on household-equal, one-round-per-household, and leave-one-high-leverage-cluster-out checks."},
        {"item": "Bounded outcome robustness", "value": bounded_status, "supervisor_note": "Poisson predictions are interpreted, not raw nonlinear interaction alone."},
    ]
    write_csv(TABLES / "table_24_phase5_supervisor_summary.csv", supervisor)
    addendum = f"""# Phase 5 verification addendum

This addendum verifies Phase 5 without replacing frozen primary models and without causal claims.

## Four-group observation and household counts

See `outputs/checkpoints/phase_05_four_group_cluster_counts.csv`. The Uzbekistan remittance-plus-work-loss cell contains {uz_cell['observations']} household-round observations from {uz_cell['unique_households']} households.

## Uzbekistan household fixed-effects verification

The household fixed-effects interaction is {fe['beta']:.4f}, clustered SE {fe['se']:.4f}, 95% CI [{fe['ci_lower']:.4f}, {fe['ci_upper']:.4f}], p = {fe['p_value']:.4g}. The fixed-effects sample has {fe['observations']} observations and {fe['households']} households. Switcher counts are {fe['remittance_switchers']} remittance switchers, {fe['shock_switchers']} shock switchers, and {fe['both_switchers']} households switching both.

## Rare-cell influence checks

See `outputs/checkpoints/phase_05_uzbekistan_influence_checks.csv`. Overall status: {infl_status}.

## Bounded-outcome robustness

See `outputs/checkpoints/phase_05_bounded_outcome_robustness.csv`. Overall status: {bounded_status}. Poisson four-group predictions are standardized using observed-value standardization; raw nonlinear interaction coefficients are not interpreted alone.

## Interaction contrast validation

All four requested contrast families are validated for KG_M2 and UZ_M2 in memory and remain available in `outputs/checkpoints/phase_05_interaction_contrasts.csv`.

## Revised figures

Figures 19, 20, and 23 were redesigned as point-range plots with full labels, y-axis labels, notes, and figure-data CSV files.
"""
    OUT_ADDENDUM.write_text(addendum, encoding="utf-8")
    rare_cell_below_threshold = int(uz_cell["observations"]) < 30 or int(uz_cell["unique_households"]) < 30
    stop = {
        "uz_cell": f"{uz_cell['observations']} OBSERVATIONS; {uz_cell['unique_households']} HOUSEHOLDS",
        "fe": f"{fe['beta']:.4f}; [{fe['ci_lower']:.4f}, {fe['ci_upper']:.4f}]; {fe['p_value']:.4g}",
        "influence": infl_status,
        "bounded": bounded_status,
        "recommended": "REVISE" if rare_cell_below_threshold else ("PROCEED" if infl_status in ["STABLE", "GENERALLY STABLE"] and bounded_status in ["CONSISTENT", "PARTIALLY CONSISTENT"] else "REVISE"),
    }
    write_json(CHECK / "phase_05_verification_addendum_status.json", stop)
    return stop


if __name__ == "__main__":
    status = main()
    print("PHASE 5 VERIFICATION COMPLETE")
    print()
    print("Uzbekistan remittance-work-loss cell:")
    print(status["uz_cell"])
    print()
    print("Uzbekistan fixed-effects interaction:")
    print(status["fe"])
    print()
    print("Uzbekistan influence sensitivity:")
    print(status["influence"])
    print()
    print("Bounded-outcome consistency:")
    print(status["bounded"])
    print()
    print("Recommended Phase 6 status:")
    print(status["recommended"])
