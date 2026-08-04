# Revised Phase 2 Harmonization Registry

The machine-readable registry is [revised_phase_02_variable_registry.csv](D:/howgart/central_asia_resilience/outputs/checkpoints/revised_phase_02_variable_registry.csv). This note records the main harmonization decisions without constructing variables.

## Kyrgyzstan LiK

- Remittance receipt: `h620`, last 12 months, member-migrant universe. Module 6A routes households without adult members abroad to Module 7, so later construction must explicitly define how structural non-migrant households enter the binary receipt indicator.
- Shock exposure: household event roster `shock`/`h701`, last 12 months. Later construction may aggregate event rows to any shock and category-specific shocks.
- Food insecurity: adult items `i251_1`-`i251_8`, last 12 months. Later scoring should treat 1 and 2 as affirmative, 3 as no, and 88/99 as missing.
- Weights: LiK study documentation says no sample weights were assigned.

## Uzbekistan L2CU

- Remittance receipt: combine `mig_living_remittance` and `remittance_hh` at household-round level only after using the key-integrity and roster consistency checks.
- Shock exposure: primary candidate is `work_lost_hh`; major illness, injury, and death can be secondary health/family shocks from `change_important*`.
- Food insecurity: FIES items `ln_1`-`ln_8`, past 30 days, observed from round 49 onward.
- Location: no region or rural/urban columns were found in the supplied CSV headers.
- Weights: `popw` exists and is complete, but the supplied questionnaire does not define its normalization or interpretation.

## Cross-Country Rule

Harmonization should be conceptual and country-specific. Differences in recall period, universe, scale, respondent level, and panel structure should be documented in model tables rather than hidden by pooling respondent records.
