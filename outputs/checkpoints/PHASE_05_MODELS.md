# Phase 5 models

## 1. Executive summary
Phase 5 estimated separate observational association and moderation models for Kyrgyzstan and Uzbekistan, plus Kazakhstan benchmark uncertainty. The frozen primary models were not replaced by this verification addendum.

Preferred interaction estimates:

- Kyrgyzstan KG_M2: beta_3 = -0.2140, 95% CI [-0.6549, 0.2269], p = 0.3415.
- Uzbekistan UZ_M2: beta_3 = -1.1119, 95% CI [-1.8088, -0.4151], p = 0.001764.

## 2. Frozen hypotheses and specifications
The frozen specifications remain in `research/phase_05_model_specification.csv`. The primary interaction coefficient is beta_3, interpreted together with predicted group outcomes.

## 3. Input and sample validation
Input validation passed. Country respondent records were not pooled.

## 4. Missing-data and sample retention
Complete-case rules were used. Kyrgyzstan KG_M2 retained 6297 observations across 2215 households. Uzbekistan UZ_M2 retained 47135 household-rounds across 2000 households.

## 5. Kyrgyzstan primary models
KG_M2 is the preferred adjusted model. The interaction estimate is directionally negative but imprecise.

## 6. Kyrgyzstan interaction contrasts
For KG_M2, the shock association without remittances is 0.2094; with remittances it is -0.0047. The remittance association without shock is -0.2574; with shock it is -0.4714.

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
For UZ_M2, the shock association without remittances is 0.8142; with remittances it is -0.2977. The remittance association without shock is -0.1406; with shock it is -1.2525.

## 13. Uzbekistan predicted group outcomes
Adjusted predicted raw-score outcomes are shown in `outputs/tables/table_19_uzbekistan_predicted_groups.csv` and redesigned in Figure 20 v2. The linear prediction confidence interval for the remittance-plus-work-loss group extends below the valid raw-score lower bound, so it should be read as a linear-model uncertainty interval rather than a feasible outcome value.

## 14. Uzbekistan broad-shock and health-shock models
Alternative-shock models remain secondary. Service disruption is not described as a climate shock.

## 15. Uzbekistan household fixed-effects robustness
The household fixed-effects interaction is -0.6352, 95% CI [-1.0196, -0.2509], p = 0.001198. Switcher counts: 476 remittance switchers, 174 shock switchers, and 44 households switching both.

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


## Sparse work-loss cell

The work-loss model is preserved but reclassified as SECONDARY EVENT-SPECIFIC EXPLORATORY RESULT because its remittance-plus-work-loss cell has 10 observations from 9 households.

## Revised Uzbekistan broad-shock specification

The revised candidate primary shock is `uzb_any_verified_shock`, defined as work loss or major health/injury/death shock. Service disruption is not treated as a climate shock.

## Broad-shock four-group support

The remittance-plus-verified-shock cell has 42 observations and 38 households and is classified ADEQUATE.

## Broad-shock preferred model

UZBROAD_M2 interaction estimate: -0.5406, 95% CI [-1.0415, -0.0398], p = 0.03437.

## Broad-shock fixed-effects model

Household fixed-effects interaction: -0.1771, 95% CI [-0.5515, 0.1973], p = 0.3539.

## Broad-shock bounded-outcome robustness

Bounded-outcome consistency: CONSISTENT. Nonlinear raw interactions are not interpreted alone.

## Broad-shock influence checks

Influence stability: GENERALLY STABLE.

## Revised cross-country comparison

Directional consistency: CONSISTENT. Countries remain separate and not ranked.

## Final Uzbekistan model hierarchy

Final decision: PRIMARY APPROVED WITH LIMITATIONS. Work-loss is secondary exploratory.
