# Kazakhstan FIES Weighting Plan

## Verified Weight

Each year includes `wt`, labelled as post-stratification sampling weights.

The technical documentation states that the weighted mean of `Prob_Mod_Sev` and `Prob_sev` using `wt` is used to calculate country-level adult prevalence for a given country and year.

## Interpretation

`wt` is usable for later year-specific adult food-insecurity prevalence estimates, subject to supervisor approval. The documentation does not provide strata, PSU, variance-estimation guidance, or exact normalization details.

## Multi-Year Use

The yearly records may later be appended only with a year marker and a clear rule for weight treatment. Whether yearly weights need rescaling for pooled multi-year trend models remains TBD.

## Restrictions

No weights are used in Revised Phase 2K. No prevalence estimates or regressions are produced.


## Phase 3 Technical Revision

Each yearly file retains `kaz_weight_original` and sets `kaz_year_specific_weight_approved = 1`. The combined benchmark file also includes `kaz_weight_mean1_within_year`, calculated as original weight divided by mean original weight within survey year. This normalized variable is for later sensitivity only and is not used for estimates in this revision. `kaz_weight_pooling_approved = 0`.
