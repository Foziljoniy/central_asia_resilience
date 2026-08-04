# Main Analysis Plan

## Scope Frozen After Revised Phase 2

The main empirical paper uses Kyrgyzstan LiK and Uzbekistan L2CU. Kazakhstan FIES access is granted. Kazakhstan is used as a K1+K2 food-insecurity trend and demographic benchmark. It is not part of the remittance-shock interaction model. Uzbekistan MICS is optional descriptive context only and is not part of the remittance-shock model.

LiK and L2CU respondent records must not be pooled. Later phases should estimate country-specific models and compare patterns conceptually.

## Research Question

Is the negative association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan?

## Country-Specific Design Candidates

Kyrgyzstan LiK:

- Candidate unit: adult respondent in 2019 linked to household-level remittance and shock measures, with any household aggregation rule specified before construction.
- Candidate remittance receipt: `h620`, subject to the Module 6A migration-universe caveat.
- Candidate shock exposure: aggregate `shock`/`h701` event roster to household indicators.
- Candidate food-insecurity outcome: adult FIES-style items `i251_1`-`i251_8`, with 1 and 2 treated as affirmative and 88/99 treated as missing in a later construction step.

Uzbekistan L2CU:

- Candidate unit: household-round.
- Candidate food-insecurity rounds: rounds 49-82, where `ln_1`-`ln_8` are observed.
- Candidate remittance receipt: household-round combination of member-migrant remittances (`mig_living_remittance`) and non-household transfers from abroad (`remittance_hh`) after roster consistency checks.
- Candidate primary shock: `work_lost_hh`.
- Candidate secondary shocks: major injury, major illness, or death from `change_important`/`change_important_type`; utility disruptions as separate service-shock measures.
- Agricultural or climate shock is not verified in the supplied L2CU files and should not be inferred from water-service disruption.

## Model Family for Later Phases

Later country-specific models may use:

```text
FoodInsecurity_it = beta_0
  + beta_1 Remittance_it
  + beta_2 Shock_it
  + beta_3 Remittance_it x Shock_it
  + gamma X_it
  + time effects
  + error_it
```

The main coefficient is `beta_3`. If higher outcome values mean worse food insecurity, a negative `beta_3` is consistent with remittances buffering shocks.

## Controls to Reassess During Dataset Construction

- household size;
- rural/urban residence where verified;
- region where verified;
- assets, income, wealth, or expenditure;
- survey weights or documented reason for no weights;
- wave/round/time controls;
- household fixed effects where panel structure and variable availability support them.

L2CU region and rural/urban variables were not found in the supplied CSV headers. L2CU `popw` exists but needs weight documentation before use. LiK documents no sample weights.

## Stop Boundary

This plan records Phase 2 design decisions only. It does not construct final analytical datasets, harmonize variables, compute descriptive results, or run regressions.


## Phase 3 Technical Revision Decisions

- Kyrgyzstan primary outcome level is adult respondent; household summaries are sensitivity only.
- Later Kyrgyzstan models must cluster standard errors by household.
- Uzbekistan initial analysis remains unweighted; `popw` is retained as `uzb_popw_unverified` with use approved set to 0.
- Kazakhstan original yearly weights are approved only for later year-specific estimates. Pooled prevalence is not approved.


## Kazakhstan Phase 4 status

Kazakhstan FIES access is granted. Kazakhstan is used as a K1+K2 food-insecurity trend and demographic benchmark. It is not part of the remittance-shock interaction model.


## Phase 4 descriptive analysis

Aggregate descriptive outputs, measurement validation, missingness assessment, and model-readiness checks are complete. No final regression model was estimated. Kazakhstan FIES access is granted. Kazakhstan is used as a K1+K2 food-insecurity trend and demographic benchmark. It is not part of the remittance-shock interaction model.


## Phase 5 country-specific association models

Phase 5 is complete. Models are country-specific, observational, household-clustered where applicable, and do not pool country records or make causal claims.


## Phase 5 sparse-cell revision

Uzbekistan work-loss is reclassified as secondary exploratory. UZBROAD_M2 is PRIMARY APPROVED WITH LIMITATIONS using `uzb_any_verified_shock`; estimates remain unweighted and observational.


## Phase 6 evidence synthesis

Phase 6 is complete. Evidence is synthesized for manuscript preparation with non-causal wording, country-specific interpretation, and Kazakhstan benchmark boundaries.


Phase 7 limited robustness: completed; primary findings preserved; remaining literature and weight limitations documented.
