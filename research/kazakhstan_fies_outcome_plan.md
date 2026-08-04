# Kazakhstan FIES Outcome Plan

## Preferred Raw Outcome

`Raw_score`, the official sum of affirmative FIES responses from 0 to 8, exists in all four canonical files.

## Preferred Binary Outcome

No respondent-level binary class variable is supplied. For later adult prevalence, the preferred official measure is `Prob_Mod_Sev`, weighted by `wt` using the supplied technical documentation. A binary respondent class should not be created without supervisor approval.

## Preferred Severe-Food-Insecurity Outcome

`Prob_sev` exists in all four years and is documented as the individual probability of severe food insecurity. It should be used for later severe-prevalence benchmarking with `wt`; no prevalence is calculated in this phase.

## Official Derived Variables

All four years include `Raw_score`, `Raw_score_par`, `Raw_score_par_error`, `Prob_Mod_Sev`, and `Prob_sev`.

## Cross-Year Availability

The same outcomes exist in 2014, 2015, 2016, and 2017.

## Recalibration

Later recalibration is not required to use the supplied official variables. Recalibration or Rasch modelling would be a separate Phase 3+ decision and was not performed here.
