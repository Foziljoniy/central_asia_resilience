# Phase 2 Kazakhstan Addendum

## 1. Executive summary

Kazakhstan FIES access is granted. Four year-specific packages, 2014-2017, were audited independently. Each year contains `.sav`, `.dta`, and `.RData` microdata plus FIES questionnaire and derived-indicator PDF resources. Kazakhstan supports K1+K2 benchmark use, not K3 remittance-shock interaction.

## 2. Access and source status

ACCESS GRANTED ON 2026-07-26. All files under `data/kazakhstan/` are protected originals. The historical pending-access marker was not deleted or modified.

## 3. Source-folder structure

Found folders: 2014, 2015, 2016, 2017. Each year has a `microdata/` folder and `resources/questionnaires/` plus `resources/technical/` folders.

## 4. Kazakhstan FIES 2014 audit

Microdata files: `.sav`, `.dta`, `.RData`.

Study resources: `FIES_Questions.pdf`; `Derived_variables_and_Computation_indicator.pdf`.

Canonical file: `data/kazakhstan/KAZ_2014_FIES_v01_EN_M_v01_A_OCS/microdata/KAZ_2014_FIES_v01_EN_M_v01_A_OCS.sav`.

Sample: 1000 adult respondent records.

FIES items: `WORRIED`, `HEALTHY`, `FEWFOOD`, `SKIPPED`, `ATELESS`, `RUNOUT`, `HUNGRY`, `WHLDAY`; last-12-month recall; 1 affirmative, 0 not affirmative, blank missing.

Weights: `wt`, post-stratification sampling weight. Strata and PSU are not available.

Demographics: `Age`, `Gender`, `Education`, `Income`, `N_adults`, `N_child`, `Area`.

Limitations: no region, remittance, migration, household shock, coping, exact fieldwork date, or interview-mode variable verified.

## 5. Kazakhstan FIES 2015 audit

Microdata files: `.sav`, `.dta`, `.RData`.

Study resources: `FIES_Questions.pdf`; `Derived_variables_and_Computation_indicator.pdf`.

Canonical file: `data/kazakhstan/KAZ_2015_FIES_v01_EN_M_v01_A_OCS/microdata/KAZ_2015_FIES_v01_EN_M_v01_A_OCS.sav`.

Sample: 1000 adult respondent records.

FIES items: `WORRIED`, `HEALTHY`, `FEWFOOD`, `SKIPPED`, `ATELESS`, `RUNOUT`, `HUNGRY`, `WHLDAY`; last-12-month recall; 1 affirmative, 0 not affirmative, blank missing.

Weights: `wt`, post-stratification sampling weight. Strata and PSU are not available.

Demographics: `Age`, `Gender`, `Education`, `Income`, `N_adults`, `N_child`, `Area`.

Limitations: no region, remittance, migration, household shock, coping, exact fieldwork date, or interview-mode variable verified.

## 6. Kazakhstan FIES 2016 audit

Microdata files: `.sav`, `.dta`, `.RData`.

Study resources: `FIES_Questions.pdf`; `Derived_variables_and_Computation_indicator.pdf`.

Canonical file: `data/kazakhstan/KAZ_2016_FIES_v01_EN_M_v01_A_OCS/microdata/KAZ_2016_FIES_v01_EN_M_v01_A_OCS.sav`.

Sample: 1000 adult respondent records.

FIES items: `WORRIED`, `HEALTHY`, `FEWFOOD`, `SKIPPED`, `ATELESS`, `RUNOUT`, `HUNGRY`, `WHLDAY`; last-12-month recall; 1 affirmative, 0 not affirmative, blank missing.

Weights: `wt`, post-stratification sampling weight. Strata and PSU are not available.

Demographics: `Age`, `Gender`, `Education`, `Income`, `N_adults`, `N_child`, `Area`.

Limitations: no region, remittance, migration, household shock, coping, exact fieldwork date, or interview-mode variable verified.

## 7. Kazakhstan FIES 2017 audit

Microdata files: `.sav`, `.dta`, `.RData`.

Study resources: `FIES_Questions.pdf`; `Derived_variables_and_Computation_indicator.pdf`.

Canonical file: `data/kazakhstan/KAZ_2017_FIES_v01_EN_M_v01_A_OCS/microdata/KAZ_2017_FIES_v01_EN_M_v01_A_OCS.sav`.

Sample: 1000 adult respondent records.

FIES items: `WORRIED`, `HEALTHY`, `FEWFOOD`, `SKIPPED`, `ATELESS`, `RUNOUT`, `HUNGRY`, `WHLDAY`; last-12-month recall; 1 affirmative, 0 not affirmative, blank missing.

Weights: `wt`, post-stratification sampling weight. Strata and PSU are not available.

Demographics: `Age`, `Gender`, `Education`, `Income`, `N_adults`, `N_child`, `Area`.

Limitations: no region, remittance, migration, household shock, coping, exact fieldwork date, or interview-mode variable verified.

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

Cross-year FIES comparability: EXACT. Demographic comparability is strong. Geographic comparability is moderate because `Area` is coarse.

## 17. Future append feasibility

Future append is feasible after Phase 3 approval as one respondent-year observation per row. The addendum does not append files.

## 18. Selected Kazakhstan benchmark role

Recommended role: K1+K2. FIES trend benchmark: FULL. Demographic benchmark: FULL. Urban-rural benchmark: PARTIAL. Remittance-shock interaction: NOT FEASIBLE.

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
