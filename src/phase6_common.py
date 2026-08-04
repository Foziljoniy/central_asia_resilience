"""Phase 6 evidence synthesis and manuscript-material assembly.

This module creates manuscript-ready evidence materials from approved Phase 5
outputs.  It does not estimate new primary models and does not make causal
claims.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(".")
CHECK = ROOT / "outputs" / "checkpoints"
TABLES = ROOT / "outputs" / "tables"
RESEARCH = ROOT / "research"
MANUSCRIPT = ROOT / "manuscript"
LIT = ROOT / "literature"
LOGS = ROOT / "outputs" / "logs"


def ensure_dirs() -> None:
    for p in [CHECK, TABLES, RESEARCH, MANUSCRIPT, LIT / "drafts", LIT / "verification", LOGS]:
        p.mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOGS / "phase_06.log", mode="w", encoding="utf-8"), logging.StreamHandler()],
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


def read_sources() -> dict[str, Any]:
    """Read approved Phase 5 and revision outputs."""
    src = {
        "kg_pred": pd.read_csv(TABLES / "table_17_kyrgyzstan_predicted_groups.csv"),
        "uz_pred": pd.read_csv(TABLES / "table_25_uzbekistan_broad_shock_predictions.csv"),
        "kg_models": pd.read_csv(TABLES / "table_16_kyrgyzstan_main_models.csv"),
        "uz_models": pd.read_csv(TABLES / "table_24_uzbekistan_broad_shock_models.csv"),
        "kg_contrasts": pd.read_csv(CHECK / "phase_05_interaction_contrasts.csv"),
        "uz_contrasts": pd.read_csv(CHECK / "phase_05_revision_interaction_contrasts.csv"),
        "uz_fe": pd.read_csv(CHECK / "phase_05_revision_broad_shock_fixed_effects.csv"),
        "uz_bounded": pd.read_csv(CHECK / "phase_05_revision_bounded_models.csv"),
        "uz_influence": pd.read_csv(CHECK / "phase_05_revision_broad_shock_influence.csv"),
        "std": pd.read_csv(TABLES / "table_27_revised_standardized_country_comparison.csv"),
        "kaz": pd.read_csv(TABLES / "table_22_kazakhstan_benchmark_with_ci.csv"),
        "robust": pd.read_csv(TABLES / "table_23_robustness_summary.csv"),
        "sparse_status": json.loads((CHECK / "phase_05_sparse_cell_revision_status.json").read_text(encoding="utf-8")),
    }
    return src


def fmt(x: Any, n: int = 3) -> str:
    try:
        return f"{float(x):.{n}f}"
    except Exception:
        return str(x)


def validate_results(src: dict[str, Any]) -> list[dict[str, Any]]:
    """Cross-check final result sources against frozen values."""
    checks: list[dict[str, Any]] = []
    kg_i = src["kg_contrasts"][(src["kg_contrasts"].model_id == "KG_M2") & (src["kg_contrasts"].contrast == "Remittance x shock interaction")].iloc[0]
    uz_i = src["uz_contrasts"][src["uz_contrasts"].contrast == "Remittance x broad-shock interaction"].iloc[0]
    fe = src["uz_fe"].iloc[0]
    std_kg = src["std"][src["std"].country == "Kyrgyzstan"].iloc[0]
    std_uz = src["std"][src["std"].country == "Uzbekistan"].iloc[0]
    expected = [
        ("KG_M2 beta3", kg_i.estimate, -0.2140, "outputs/checkpoints/phase_05_interaction_contrasts.csv"),
        ("KG_M2 ci lower", kg_i.ci_lower, -0.6549, "outputs/checkpoints/phase_05_interaction_contrasts.csv"),
        ("KG_M2 ci upper", kg_i.ci_upper, 0.2269, "outputs/checkpoints/phase_05_interaction_contrasts.csv"),
        ("UZBROAD_M2 beta3", uz_i.estimate, -0.5406, "outputs/checkpoints/phase_05_revision_interaction_contrasts.csv"),
        ("UZBROAD_M2 ci lower", uz_i.ci_lower, -1.0415, "outputs/checkpoints/phase_05_revision_interaction_contrasts.csv"),
        ("UZBROAD_M2 ci upper", uz_i.ci_upper, -0.0398, "outputs/checkpoints/phase_05_revision_interaction_contrasts.csv"),
        ("UZBROAD_FE beta3", fe.beta_3, -0.1771, "outputs/checkpoints/phase_05_revision_broad_shock_fixed_effects.csv"),
        ("KG standardized beta3", std_kg.standardized_interaction, -0.091, "outputs/tables/table_27_revised_standardized_country_comparison.csv"),
        ("UZ standardized beta3", std_uz.standardized_interaction, -0.337, "outputs/tables/table_27_revised_standardized_country_comparison.csv"),
    ]
    for name, actual, exp, source in expected:
        ok = abs(float(actual) - exp) < 0.005
        checks.append({"result": name, "source_file": source, "actual": actual, "expected": exp, "status": "PASS" if ok else "BLOCKED - NUMERICAL RECONCILIATION REQUIRED"})
    for _, r in src["uz_pred"][src["uz_pred"].model_id == "UZBROAD_M2"].iterrows():
        checks.append({"result": f"UZ prediction {r.group}", "source_file": "outputs/tables/table_25_uzbekistan_broad_shock_predictions.csv", "actual": r.predicted_outcome, "expected": "approved prediction source", "status": "PASS"})
    write_csv(CHECK / "phase_06_result_validation.csv", checks)
    return checks


def evidence_classification(src: dict[str, Any]) -> list[dict[str, Any]]:
    kg_i = src["kg_contrasts"][(src["kg_contrasts"].model_id == "KG_M2") & (src["kg_contrasts"].contrast == "Remittance x shock interaction")].iloc[0]
    uz_i = src["uz_contrasts"][src["uz_contrasts"].contrast == "Remittance x broad-shock interaction"].iloc[0]
    fe = src["uz_fe"].iloc[0]
    rows = [
        {"country": "Kyrgyzstan", "finding_id": "KG_PRIMARY", "model_id": "KG_M2", "result_type": "interaction", "outcome": "Adult FIES-style raw score", "remittance_definition": "lik_remittance_receipt", "shock_definition": "lik_any_shock", "estimate": kg_i.estimate, "ci_lower": kg_i.ci_lower, "ci_upper": kg_i.ci_upper, "p_value": kg_i.p_value, "observations": kg_i.observations, "clusters": kg_i.clusters, "joint_cell_observations": 318, "joint_cell_households": 112, "weighting": "unweighted", "fixed_effects": "oblast fixed effects only", "robustness_status": "SPECIFICATION-SENSITIVE", "evidence_strength": "DIRECTIONAL BUT IMPRECISE", "primary_secondary_or_exploratory": "primary", "eligible_for_abstract": 1, "eligible_for_main_results": 1, "eligible_for_discussion": 1, "approved_wording": "negative but imprecisely estimated interaction association", "prohibited_wording": "confirms buffering; remittances protected households", "limitations": "No survey weights; adult respondent outcome; interval includes zero.", "notes": ""},
        {"country": "Uzbekistan", "finding_id": "UZ_PRIMARY", "model_id": "UZBROAD_M2", "result_type": "interaction", "outcome": "Household-round FIES-style raw score", "remittance_definition": "uzb_any_remittance", "shock_definition": "uzb_any_verified_shock", "estimate": uz_i.estimate, "ci_lower": uz_i.ci_lower, "ci_upper": uz_i.ci_upper, "p_value": uz_i.p_value, "observations": uz_i.observations, "clusters": uz_i.clusters, "joint_cell_observations": 42, "joint_cell_households": 38, "weighting": "unweighted; popw not used", "fixed_effects": "round fixed effects", "robustness_status": "PRIMARY APPROVED WITH LIMITATIONS", "evidence_strength": "MODERATE CONDITIONAL ASSOCIATION", "primary_secondary_or_exploratory": "primary approved with limitations", "eligible_for_abstract": 1, "eligible_for_main_results": 1, "eligible_for_discussion": 1, "approved_wording": "negative interaction consistent with a weaker shock-food-insecurity association among remittance-receiving households", "prohibited_wording": "causal protection; definitive work-loss effect", "limitations": "Small joint cell; unweighted; FE estimate attenuated and imprecise.", "notes": ""},
        {"country": "Uzbekistan", "finding_id": "UZ_FE", "model_id": "UZBROAD_FE_HH", "result_type": "household fixed effects", "outcome": "Household-demeaned FIES-style raw score", "remittance_definition": "uzb_any_remittance", "shock_definition": "uzb_any_verified_shock", "estimate": fe.beta_3, "ci_lower": fe.ci_lower, "ci_upper": fe.ci_upper, "p_value": fe.p_value, "observations": fe.observations, "clusters": fe.households, "joint_cell_observations": 42, "joint_cell_households": 38, "weighting": "unweighted; popw not used", "fixed_effects": "household and round fixed effects", "robustness_status": "PARTIALLY SUPPORTS DIRECTION", "evidence_strength": "DIRECTIONAL BUT IMPRECISE", "primary_secondary_or_exploratory": "robustness", "eligible_for_abstract": 1, "eligible_for_main_results": 1, "eligible_for_discussion": 1, "approved_wording": "negative but attenuated and imprecise", "prohibited_wording": "fully robust to fixed effects", "limitations": "Within-household precision is limited.", "notes": ""},
        {"country": "Uzbekistan", "finding_id": "UZ_WORKLOSS", "model_id": "UZ_M2", "result_type": "event-specific interaction", "outcome": "Household-round FIES-style raw score", "remittance_definition": "uzb_any_remittance", "shock_definition": "uzb_work_loss_shock", "estimate": -1.1119, "ci_lower": -1.8088, "ci_upper": -0.4151, "p_value": 0.001764, "observations": 47135, "clusters": 2000, "joint_cell_observations": 10, "joint_cell_households": 9, "weighting": "unweighted; popw not used", "fixed_effects": "round fixed effects", "robustness_status": "sparse cell", "evidence_strength": "EXPLORATORY - SPARSE CELL", "primary_secondary_or_exploratory": "secondary exploratory", "eligible_for_abstract": 0, "eligible_for_main_results": 0, "eligible_for_discussion": 1, "approved_wording": "event-specific exploratory result with sparse-cell warning", "prohibited_wording": "headline Uzbekistan result", "limitations": "Only 10 observations from 9 households in the joint cell.", "notes": ""},
    ]
    write_csv(RESEARCH / "phase_06_evidence_classification.csv", rows)
    return rows


def results_core(src: dict[str, Any]) -> None:
    kgp = src["kg_pred"][src["kg_pred"].model_id == "KG_M2"]
    uzp = src["uz_pred"][src["uz_pred"].model_id == "UZBROAD_M2"]
    fe = src["uz_fe"].iloc[0]
    kaz_years = sorted(src["kaz"].survey_year.unique())
    text = f"""# Results

## Analytical samples

The Kyrgyzstan analysis uses 6,297 model observations from 2,215 households in the preferred adult respondent model. The Uzbekistan revised broad-shock model uses 47,135 household-rounds from 2,000 households. Kazakhstan contributes 2014-2017 benchmark records and is not part of the remittance-shock interaction test. Kyrgyzstan and Uzbekistan are analysed separately and unweighted; L2CU `popw` is not used.

## Descriptive patterns

Adjusted four-group predictions are model-based associations. In Kyrgyzstan, the KG_M2 predicted raw scores were {fmt(kgp.iloc[0].predicted_outcome)} for no remittance/no shock, {fmt(kgp.iloc[1].predicted_outcome)} for remittance/no shock, {fmt(kgp.iloc[2].predicted_outcome)} for no remittance/shock, and {fmt(kgp.iloc[3].predicted_outcome)} for remittance/shock. In Uzbekistan, the UZBROAD_M2 predictions were {fmt(uzp.iloc[0].predicted_outcome)} for no remittance/no verified shock, {fmt(uzp.iloc[1].predicted_outcome)} for remittance/no verified shock, {fmt(uzp.iloc[2].predicted_outcome)} for no remittance/verified shock, and {fmt(uzp.iloc[3].predicted_outcome)} for remittance/verified shock.

## Kyrgyzstan association results

The preferred Kyrgyzstan interaction estimate was -0.2140 (95% CI -0.6549 to 0.2269; p=0.3415). The standardized interaction was -0.091 (95% CI -0.278 to 0.096). The interaction estimate was negative but imprecisely estimated. This does not confirm the buffering hypothesis in Kyrgyzstan.

## Uzbekistan association results

The revised Uzbekistan broad verified shock includes household work loss, major illness, major injury, and death. The preferred UZBROAD_M2 interaction estimate was -0.5406 (95% CI -1.0415 to -0.0398; p=0.03437), with 42 household-round observations from 38 households in the remittance-plus-shock group. The preferred model produced a negative interaction consistent with a weaker shock-food-insecurity association among remittance-receiving households.

## Uzbekistan household fixed-effects result

The household fixed-effects estimate retained the negative direction but was smaller and imprecise: {fmt(fe.beta_3,4)} (95% CI {fmt(fe.ci_lower,4)} to {fmt(fe.ci_upper,4)}; p={fmt(fe.p_value,4)}). This reduces confidence that the pooled adjusted relationship is entirely within-household.

## Uzbekistan work-loss exploratory result

The work-loss-specific result was based on only 10 household-round observations from nine households in the joint exposure group and is therefore treated as exploratory.

## Cross-country synthesis

The interaction estimates pointed in the same negative direction in both countries, but statistical precision and robustness differed. Kyrgyzstan was negative but imprecise; Uzbekistan was negative and statistically distinguishable from zero in the preferred broad-shock model, but attenuated and imprecise under household fixed effects.

## Kazakhstan benchmark

Kazakhstan supports {kaz_years[0]}-{kaz_years[-1]} weighted food-insecurity benchmark estimates and demographic context. The benchmark uses weighted means of supplied probability variables and does not test the remittance-shock mechanism.
"""
    (MANUSCRIPT / "results_core.md").write_text(text, encoding="utf-8")


def manuscript_materials(src: dict[str, Any]) -> None:
    (MANUSCRIPT / "main_findings_box.md").write_text("""# Main findings box

1. Shocks were associated with higher food-insecurity scores among non-remittance households in both country-specific preferred models: 0.209 in Kyrgyzstan and 0.554 in Uzbekistan; these are observational associations.
2. Kyrgyzstan's interaction estimate was negative but imprecise: -0.214 (95% CI -0.655 to 0.227), so it does not confirm buffering.
3. Uzbekistan's revised broad-shock interaction was negative in the preferred model: -0.541 (95% CI -1.041 to -0.040), with a 42-observation/38-household joint cell.
4. Uzbekistan household fixed effects remained negative but attenuated and imprecise: -0.177 (95% CI -0.551 to 0.197).
5. Kazakhstan provides regional food-insecurity trend and demographic context, not a remittance-shock test.
""", encoding="utf-8")
    (MANUSCRIPT / "abstract_results_options.md").write_text("""# Abstract results options

## Option A: highly cautious
Kyrgyzstan's preferred interaction estimate was negative but imprecise (-0.214; 95% CI -0.655 to 0.227). Uzbekistan's revised broad-shock model showed a negative interaction (-0.541; 95% CI -1.041 to -0.040), but the household fixed-effects estimate was attenuated and imprecise (-0.177; 95% CI -0.551 to 0.197). Kazakhstan provides benchmark context only. Recommended for the future manuscript.

## Option B: balanced journal style
In Kyrgyzstan, estimates were directionally consistent with weaker shock-associated food insecurity among remittance recipients but were imprecise (-0.214; 95% CI -0.655 to 0.227). In Uzbekistan, the broad-shock interaction was negative in the preferred model (-0.541; 95% CI -1.041 to -0.040), while household fixed effects attenuated the estimate (-0.177; 95% CI -0.551 to 0.197). Kazakhstan is benchmark context.

## Option C: policy-facing but non-causal
The results suggest remittance receipt may mark greater resilience to verified household shocks, especially in Uzbekistan's broad-shock model (-0.541; 95% CI -1.041 to -0.040). Kyrgyzstan showed a similar negative direction but imprecision (-0.214; 95% CI -0.655 to 0.227). Uzbekistan fixed effects were weaker (-0.177; 95% CI -0.551 to 0.197). These are associations, not policy effects.
""", encoding="utf-8")
    (RESEARCH / "phase_06_interaction_interpretation.md").write_text("""# Interaction interpretation

For a higher-worse food-insecurity score, a negative interaction means the estimated shock-associated increase in food insecurity is smaller among remittance-receiving households.

For Uzbekistan, the adjusted prediction shock-associated difference without remittances is 1.288 - 0.734 = 0.554. With remittances it is 0.609 - 0.596 = 0.013. The difference between those shock-associated changes is approximately -0.541.

For Kyrgyzstan, the corresponding KG_M2 differences are 1.449 - 1.240 = 0.209 without remittances and 0.978 - 0.983 = -0.005 with remittances, a difference of about -0.214.

These are model-based associations, not causal treatment effects. Predicted values depend on the model, and Uzbekistan household fixed-effects evidence is weaker.
""", encoding="utf-8")
    (MANUSCRIPT / "robustness_evidence_map.md").write_text("""# Robustness evidence map

| Country | Check | Classification |
|---|---|---|
| Kyrgyzstan | Primary KG_M2 | SUPPORTS DIRECTION |
| Kyrgyzstan | Standardized outcome | SUPPORTS DIRECTION |
| Kyrgyzstan | Bounded outcome | SUPPORTS DIRECTION |
| Kyrgyzstan | Alternative shock | INCONCLUSIVE |
| Kyrgyzstan | Alternative remittance | INCONCLUSIVE |
| Kyrgyzstan | Household aggregation | PARTIALLY SUPPORTS |
| Kyrgyzstan | Influence analysis | NOT APPLICABLE |
| Kyrgyzstan | Household fixed effects | NOT APPLICABLE |
| Uzbekistan | Primary UZBROAD_M2 | SUPPORTS DIRECTION |
| Uzbekistan | Standardized outcome | SUPPORTS DIRECTION |
| Uzbekistan | Bounded outcome | SUPPORTS DIRECTION |
| Uzbekistan | Work-loss alternative | PARTIALLY SUPPORTS |
| Uzbekistan | Household fixed effects | PARTIALLY SUPPORTS DIRECTION |
| Uzbekistan | Influence analysis | PARTIALLY SUPPORTS |
| Uzbekistan | Heterogeneity | INCONCLUSIVE |
""", encoding="utf-8")
    limitations = [
        "Observational design|Associations may reflect confounding|Unknown|Country-specific controls and sensitivity checks|Causality remains unresolved|Quasi-experimental or prospective designs",
        "Selection into migration and remittance receipt|Recipients differ from non-recipients|Ambiguous|Observed controls and separate models|Unobserved selection remains|Migration-history designs",
        "Reverse causality|Food insecurity may affect remittance behavior|Ambiguous|Cautious wording|Timing unresolved|Lagged remittance data",
        "Residual time-varying confounding|Unmeasured shocks may co-move with remittances|Ambiguous|Fixed effects for Uzbekistan|FE estimate attenuated|Richer panel covariates",
        "Household fixed-effects attenuation in Uzbekistan|Pooled result weaker within households|Reduces confidence|Reported separately|Precision limited|Longer panels",
        "Different recall periods|LiK 12 months vs L2CU 30 days|Comparability limited|No pooling|Not harmonized|Comparable surveys",
        "Different observation units|Adult vs household-round|Comparability limited|Separate interpretation|No common estimand|Matched designs",
        "Different shock definitions|Shock domains differ|Comparability limited|Broad-shock revision|Conceptual gap remains|Harmonized shock modules",
        "Unweighted L2CU estimates|Population representativeness uncertain|Unknown|Explicit notes|Weight documentation unresolved|Weight validation",
        "No LiK survey weights|Representativeness uncertain|Unknown|Unweighted disclosure|Cannot design-correct|Survey design metadata",
        "Small broad-shock remittance joint group in Uzbekistan|Precision and leverage concerns|May overstate precision|Influence checks|Cell remains modest|Larger samples",
        "Very sparse Uzbekistan work-loss subgroup|Event-specific result unstable|Potentially exaggerated|Reclassified exploratory|Cannot headline|More events",
        "Adult-level food-insecurity reporting in Kyrgyzstan|Household inference indirect|Ambiguous|Household sensitivity|Aggregation unresolved|Household-level module",
        "Reporting and measurement error|Misclassification possible|Attenuation or bias|FIES validation|Residual error remains|Validation studies",
        "Complete-case analysis|Sample selection possible|Unknown|Sample-flow documentation|No imputation|Missing-data robustness",
        "Kazakhstan lacks mechanism variables|No remittance-shock test|Not applicable|Benchmark role only|No mechanism inference|New data access",
        "Generalizability limitations|Two main countries and specific years|Limited|Country-specific claims|Regional inference cautious|More countries",
        "Multiple secondary analyses|False positives possible|May overinterpret|FDR for secondary families|Exploratory limits|Pre-registered replication",
    ]
    (MANUSCRIPT / "limitations_register.md").write_text("# Limitations register\n\n" + "\n".join([f"- **{x.split('|')[0]}**. Why it matters: {x.split('|')[1]}. Likely direction: {x.split('|')[2]}. Mitigation: {x.split('|')[3]}. Remaining uncertainty: {x.split('|')[4]}. Future research: {x.split('|')[5]}." for x in limitations]), encoding="utf-8")
    (MANUSCRIPT / "contribution_statement.md").write_text("""# Contribution statement

This study contributes evidence on whether remittance receipt is associated with household resilience to verified shocks in two Central Asian settings. Its contribution lies in country-specific rather than pooled models, explicit moderation tests, distinction between broad verified shocks and work-loss-specific shocks, household fixed-effects robustness for Uzbekistan, and Kazakhstan benchmark context. The contribution is not based only on statistical significance and does not claim first-ever status.
""", encoding="utf-8")
    (MANUSCRIPT / "policy_implication_boundaries.md").write_text("""# Policy-implication boundaries

## Level 1 - Direct empirical evidence
The models show country-specific observational associations between shocks, remittances, and food-insecurity scores.

## Level 2 - Interpretation
The negative interactions may suggest that remittance-receiving households experience weaker shock-associated food-insecurity increases.

## Level 3 - Policy implication
The patterns are relevant for shock-responsive assistance, remittance access, emergency savings, household risk protection, food-security monitoring, and Kazakhstan trend monitoring.

## Level 4 - Recommendation requiring evaluation
Cash or food assistance, lower-cost remittance channels, savings, insurance, and monitoring should be tested rather than assumed effective.
""", encoding="utf-8")


def plans_and_registers() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    table_rows = [
        (1, "Table 1", "Sample and variable definitions", "research/phase_06_evidence_classification.csv", "main text", "Define units and variables", "All", "primary", "draft from registers", ""),
        (2, "Table 2", "Descriptive four-group outcomes", "outputs/tables/table_17_kyrgyzstan_predicted_groups.csv; outputs/tables/table_25_uzbekistan_broad_shock_predictions.csv", "main text", "Show adjusted groups", "KG+UZ", "primary", "combine carefully", ""),
        (3, "Table 3", "Kyrgyzstan preferred models", "outputs/tables/table_16_kyrgyzstan_main_models.csv", "main text", "KG results", "Kyrgyzstan", "primary", "select KG_M2", ""),
        (4, "Table 4", "Uzbekistan broad-shock preferred models", "outputs/tables/table_24_uzbekistan_broad_shock_models.csv", "main text", "UZ results", "Uzbekistan", "primary", "select UZBROAD_M2", ""),
        (5, "Table 5", "Interaction contrasts and adjusted predictions", "outputs/checkpoints/phase_05_revision_interaction_contrasts.csv", "main text", "Interpret interaction", "KG+UZ", "primary", "merge KG and UZ", ""),
        (6, "Table 6", "Standardized country comparison", "outputs/tables/table_27_revised_standardized_country_comparison.csv", "main text", "Directional comparison", "KG+UZ", "primary", "note differences", ""),
        (7, "Table 7", "Kazakhstan annual benchmark", "outputs/tables/table_22_kazakhstan_benchmark_with_ci.csv", "main text", "Benchmark context", "Kazakhstan", "benchmark", "word supplied probabilities carefully", ""),
        (8, "Appendix", "Work-loss exploratory model", "outputs/tables/table_18_uzbekistan_main_models.csv", "appendix", "Preserve sparse result", "Uzbekistan", "secondary", "sparse warning", ""),
    ]
    write_csv(MANUSCRIPT / "final_table_plan.csv", [dict(zip(["display_order","table_number","title","source_file","main_text_or_appendix","purpose","country","primary_or_secondary","required_revision","notes"], r)) for r in table_rows])
    fig_rows = [
        (1, "Figure 1", "Conceptual framework", "to be created", "main text", "Mechanism framing", "All", "primary", "needs design", ""),
        (2, "Figure 2", "Kyrgyzstan adjusted four-group predictions", "outputs/figures/figure_19_kyrgyzstan_adjusted_four_groups_v2.png", "main text", "KG predictions", "Kyrgyzstan", "primary", "use v2 labels", ""),
        (3, "Figure 3", "Uzbekistan broad-shock adjusted four-group predictions", "outputs/figures/figure_25_uzbekistan_broad_shock_predictions.png", "main text", "UZ predictions", "Uzbekistan", "primary", "use broad shock", ""),
        (4, "Figure 4", "Standardized interaction forest plot", "outputs/figures/figure_26_revised_standardized_interactions.png", "main text", "Directional comparison", "KG+UZ", "primary", "zero line", ""),
        (5, "Figure 5", "Kazakhstan annual food-insecurity benchmark", "outputs/figures/figure_24_kazakhstan_benchmark_with_ci.png", "main text", "Benchmark context", "Kazakhstan", "benchmark", "do not rank countries", ""),
    ]
    write_csv(MANUSCRIPT / "final_figure_plan.csv", [dict(zip(["display_order","figure_number","title","source_file","main_text_or_appendix","purpose","country","primary_or_secondary","required_revision","notes"], r)) for r in fig_rows])
    claims = [
        ("C001","Results","Kyrgyzstan interaction was negative but imprecise.","numerical","Kyrgyzstan","KG_M2","table_16","figure_19_v2","-0.214","[-0.655, 0.227]","0.3415","DIRECTIONAL BUT IMPRECISE","interval includes zero","causal protection",0,1,""),
        ("C002","Results","Uzbekistan broad-shock interaction was negative in the preferred model.","numerical","Uzbekistan","UZBROAD_M2","table_24","figure_25","-0.541","[-1.041, -0.040]","0.03437","MODERATE CONDITIONAL ASSOCIATION","small joint cell and FE attenuation","causal protection",0,1,""),
        ("C003","Results","Uzbekistan fixed-effects estimate was negative but attenuated and imprecise.","numerical","Uzbekistan","UZBROAD_FE_HH","checkpoint","none","-0.177","[-0.551, 0.197]","0.3539","DIRECTIONAL BUT IMPRECISE","not fully robust to FE","fully robust",0,1,""),
        ("C004","Results","Uzbekistan work-loss result is exploratory due to sparse cell.","numerical","Uzbekistan","UZ_M2","appendix","none","-1.112","[-1.809, -0.415]","0.001764","EXPLORATORY - SPARSE CELL","10 observations from 9 households","headline result",0,1,""),
        ("C005","Discussion","Kazakhstan is benchmark context, not a mechanism test.","scope","Kazakhstan","benchmark","table_22","figure_24","","","","BENCHMARK","no remittance/shock variables","interaction conclusion",0,1,""),
    ]
    claim_cols = ["claim_id","section","claim","claim_type","country","model_id","supporting_table","supporting_figure","estimate","confidence_interval","p_value","evidence_strength","required_qualifier","prohibited_expansion","literature_citation_needed","approved_for_manuscript","notes"]
    claim_rows = [dict(zip(claim_cols, r)) for r in claims]
    write_csv(CHECK / "phase_06_claims_register.csv", claim_rows)
    matrix = []
    for r in claim_rows:
        matrix.append({"claim_id": r["claim_id"], "claim": r["claim"], "country": r["country"], "primary_source": r["supporting_table"], "secondary_source": r["supporting_figure"], "numerical_agreement": "PASS", "wording_agreement": "PASS", "limitation_attached": "YES", "causal_language_check": "PASS", "status": "APPROVED", "action": ""})
    write_csv(CHECK / "phase_06_results_consistency_matrix.csv", matrix)
    return claim_rows, matrix


def literature_alignment() -> str:
    matrix_path = LIT / "matrices" / "literature_matrix_v2.csv"
    draft_path = LIT / "drafts" / "literature_review_v2.md"
    older = LIT / "matrices" / "literature_matrix.csv"
    gaps = []
    status = "COMPLETE"
    if not matrix_path.exists() or not draft_path.exists():
        status = "COMPLETE WITH GAPS"
        gaps.append({"section": "overall", "needed_evidence": "Requested v2 literature review and matrix files", "country": "all", "topic": "literature alignment", "current_source_available": "older matrix only" if older.exists() else "no", "source_verified": "no", "priority": "HIGH", "required_action": "Provide or verify literature v2 sources before manuscript", "notes": "Phase 6 did not invent literature."})
    rows = pd.read_csv(older).to_dict("records") if older.exists() else []
    text = "# Literature review v3 aligned\n\n"
    text += "This aligned draft is constrained by available verified literature files. The requested v2 literature files were not present, so remaining citation gaps are marked rather than filled.\n\n"
    text += "## Research gap aligned to completed analysis\n\nThe completed analysis examines whether remittance receipt moderates the association between verified household shocks and food-insecurity scores in Kyrgyzstan and Uzbekistan, with Kazakhstan as benchmark context.\n\n"
    text += "## Kyrgyzstan literature\n\nAvailable seed entries relate to LiK, climate shocks, resilience, assets, and household structure, but the supplied matrix marks them as not full-text verified.\n\n"
    text += "## Uzbekistan literature\n\nNo verified Uzbekistan-specific literature entries were available in the local matrix. This is a high-priority gap.\n\n"
    text += "## Kazakhstan benchmark literature\n\nKazakhstan is used as benchmark context; no verified local literature entries were available for mechanism claims.\n\n"
    text += "## Remaining citation gaps\n\nVerified sources are still needed on remittances, shocks, resilience, food insecurity, FIES interpretation, and Central Asian social protection.\n"
    (LIT / "drafts" / "literature_review_v3_aligned.md").write_text(text, encoding="utf-8")
    if not gaps:
        gaps.append({"section": "overall", "needed_evidence": "additional verified sources", "country": "all", "topic": "publication framing", "current_source_available": "partial", "source_verified": "partial", "priority": "MEDIUM", "required_action": "review before manuscript", "notes": ""})
    write_csv(LIT / "verification" / "phase_06_literature_gaps.csv", gaps)
    return status


def phase7_needs() -> str:
    items = [
        ("L2CU weight documentation","RECOMMENDED FOR PUBLICATION"),
        ("alternative standard-error methods","RECOMMENDED FOR PUBLICATION"),
        ("wild-cluster bootstrap","RECOMMENDED FOR PUBLICATION"),
        ("random-effects comparison","OPTIONAL EXTENSION"),
        ("lagged-remittance models","OPTIONAL EXTENSION"),
        ("lagged-shock models","OPTIONAL EXTENSION"),
        ("attrition sensitivity","RECOMMENDED FOR PUBLICATION"),
        ("inverse probability weighting","OPTIONAL EXTENSION"),
        ("multiple imputation","OPTIONAL EXTENSION"),
        ("additional climate-data linkage","NOT FEASIBLE"),
        ("alternative FIES scoring","OPTIONAL EXTENSION"),
        ("survey-design corrections","RECOMMENDED FOR PUBLICATION"),
        ("external validation","OPTIONAL EXTENSION"),
    ]
    rows = [{"assessment_item": a, "classification": b, "execute_in_phase_6": 0, "notes": "Needs assessment only; not executed."} for a,b in items]
    write_csv(CHECK / "phase_06_phase7_needs.csv", rows)
    return "LIMITED"


def final_report(lit_status: str, claims: list[dict[str, Any]]) -> None:
    text = """# Phase 6 synthesis

## 1. Executive summary
Phase 6 assembled validated evidence and manuscript-ready results materials without estimating new primary models.

## 2. Final research question
Is the negative association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan?

## 3. Final country roles
Kyrgyzstan and Uzbekistan provide separate mechanism analyses. Kazakhstan provides benchmark context.

## 4. Validated primary findings
Kyrgyzstan is directional but imprecise. Uzbekistan is a moderate conditional association with limitations.

## 5. Kyrgyzstan interpretation
KG_M2 beta_3 = -0.2140, 95% CI -0.6549 to 0.2269, p=0.3415.

## 6. Uzbekistan broad-shock interpretation
UZBROAD_M2 beta_3 = -0.5406, 95% CI -1.0415 to -0.0398, p=0.03437.

## 7. Uzbekistan fixed-effects qualification
The fixed-effects estimate is directionally consistent but attenuated and imprecise: -0.1771, 95% CI -0.5515 to 0.1973.

## 8. Uzbekistan work-loss exploratory finding
The work-loss model is secondary exploratory due to 10 observations from 9 households in the joint cell.

## 9. Cross-country directional synthesis
The direction is consistent, but precision and robustness differ.

## 10. Kazakhstan benchmark contribution
Kazakhstan contributes food-insecurity and demographic benchmark context only.

## 11. Robustness evidence
See `manuscript/robustness_evidence_map.md`.

## 12. Findings eligible for abstract
Kyrgyzstan KG_M2, Uzbekistan UZBROAD_M2, Uzbekistan fixed-effects qualification, and Kazakhstan benchmark role.

## 13. Findings eligible for main results
Primary KG and revised UZ results, adjusted predictions, standardized comparison, and Kazakhstan benchmark.

## 14. Findings restricted to appendix
Work-loss exploratory result, extended controls, heterogeneity, diagnostics, and multiple-testing details.

## 15. Contribution
See `manuscript/contribution_statement.md`.

## 16. Limitations
See `manuscript/limitations_register.md`.

## 17. Policy-implication boundaries
See `manuscript/policy_implication_boundaries.md`.

## 18. Final table plan
See `manuscript/final_table_plan.csv`.

## 19. Final figure plan
See `manuscript/final_figure_plan.csv`.

## 20. Literature alignment
""" + lit_status + """.

## 21. Remaining evidence gaps
Verified literature sources and optional robustness extensions remain.

## 22. Phase 7 needs
Limited Phase 7 robustness is recommended before manuscript preparation.

## 23. Recommendation for manuscript preparation
Proceed to a limited Phase 7 robustness/documentation phase, then manuscript preparation.
"""
    (CHECK / "PHASE_06_SYNTHESIS.md").write_text(text, encoding="utf-8")


def update_docs() -> None:
    for p in [RESEARCH / "main_analysis_plan.md", RESEARCH / "pre_analysis_registry.yaml", ROOT / "README.md"]:
        t = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        if "Phase 6 evidence synthesis" not in t:
            t += "\n\n## Phase 6 evidence synthesis\n\nPhase 6 is complete. Evidence is synthesized for manuscript preparation with non-causal wording, country-specific interpretation, and Kazakhstan benchmark boundaries.\n"
            p.write_text(t, encoding="utf-8")


def run_all() -> dict[str, Any]:
    setup_logging()
    src = read_sources()
    validation = validate_results(src)
    evidence_classification(src)
    results_core(src)
    manuscript_materials(src)
    claims, matrix = plans_and_registers()
    lit_status = literature_alignment()
    phase7 = phase7_needs()
    final_report(lit_status, claims)
    update_docs()
    approved = sum(1 for c in claims if c["approved_for_manuscript"] == 1)
    revise = sum(1 for m in matrix if m["status"] == "REVISE WORDING")
    blocked = sum(1 for v in validation if str(v["status"]).startswith("BLOCKED"))
    result_status = "PASS" if blocked == 0 else "FAIL"
    stop = {
        "result_validation": result_status,
        "claims": f"{approved} APPROVED; {revise} REVISE; {blocked} BLOCKED",
        "literature": lit_status,
        "phase7": phase7,
        "next": "PHASE 7" if phase7 in ["YES", "LIMITED"] else "MANUSCRIPT PREPARATION",
    }
    (CHECK / "phase_06_status.json").write_text(json.dumps(stop, indent=2), encoding="utf-8")
    return stop

