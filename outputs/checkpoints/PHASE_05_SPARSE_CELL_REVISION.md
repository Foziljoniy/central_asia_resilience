# Phase 5 sparse-cell revision

## 1. Reason for revision
The work-loss joint cell is too sparse for the primary Uzbekistan specification.

## 2. Work-loss sparse-cell finding
The remittance-plus-work-loss cell has 10 household-round observations from 9 households.

## 3. Broad-shock definition
`uzb_any_verified_shock` includes work loss and major health/injury/death shocks only.

## 4. Broad-shock group and cluster counts
The remittance-plus-broad-shock cell has 42 observations and 38 households; classification ADEQUATE.

## 5. Broad-shock primary models
UZBROAD_M0-M2 were estimated unweighted with household-clustered standard errors.

## 6. Interaction contrasts
See `outputs/checkpoints/phase_05_revision_interaction_contrasts.csv`.

## 7. Adjusted predictions
See `outputs/tables/table_25_uzbekistan_broad_shock_predictions.csv`.

## 8. Household fixed effects
FE beta_3 = -0.1771, 95% CI [-0.5515, 0.1973], p = 0.3539.

## 9. Bounded-outcome robustness
CONSISTENT.

## 10. Influence checks
GENERALLY STABLE.

## 11. Work-loss exploratory result
SECONDARY EVENT-SPECIFIC EXPLORATORY RESULT.

## 12. Revised standardized comparison
CONSISTENT.

## 13. Final model hierarchy
PRIMARY APPROVED WITH LIMITATIONS.

## 14. Remaining limitations
The analysis remains observational. Shock definitions and recall periods differ across countries.

## 15. Phase 6 recommendation
Proceed with limitations if supervisor accepts the broad-shock hierarchy.
