# Phase 5 verification addendum

This addendum verifies Phase 5 without replacing frozen primary models and without causal claims.

## Four-group observation and household counts

See `outputs/checkpoints/phase_05_four_group_cluster_counts.csv`. The Uzbekistan remittance-plus-work-loss cell contains 10 household-round observations from 9 households.

## Uzbekistan household fixed-effects verification

The household fixed-effects interaction is -0.6352, clustered SE 0.1961, 95% CI [-1.0196, -0.2509], p = 0.001198. The fixed-effects sample has 47135 observations and 2000 households. Switcher counts are 476 remittance switchers, 174 shock switchers, and 44 households switching both.

## Rare-cell influence checks

See `outputs/checkpoints/phase_05_uzbekistan_influence_checks.csv`. Overall status: GENERALLY STABLE.

## Bounded-outcome robustness

See `outputs/checkpoints/phase_05_bounded_outcome_robustness.csv`. Overall status: CONSISTENT. Poisson four-group predictions are standardized using observed-value standardization; raw nonlinear interaction coefficients are not interpreted alone.

## Interaction contrast validation

All four requested contrast families are validated for KG_M2 and UZ_M2 in memory and remain available in `outputs/checkpoints/phase_05_interaction_contrasts.csv`.

## Revised figures

Figures 19, 20, and 23 were redesigned as point-range plots with full labels, y-axis labels, notes, and figure-data CSV files.
