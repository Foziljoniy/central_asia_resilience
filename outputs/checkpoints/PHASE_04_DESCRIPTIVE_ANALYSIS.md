# Phase 4 descriptive analysis

## 1. Executive summary

Phase 4 produced aggregate-only descriptive, missingness, FIES measurement-quality, group-comparison, trend, benchmark, and model-readiness outputs. Final interaction regressions and hypothesis-test quantities were not estimated.

## 2. Administrative closeout

Kazakhstan FIES access is granted. Kazakhstan is used as a K1+K2 food-insecurity trend and demographic benchmark. It is not part of the remittance-shock interaction model.

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

The minimum reportable analytical cell size is 30. Cells below this threshold are marked `SUPPRESSED_SMALL_CELL`.

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
