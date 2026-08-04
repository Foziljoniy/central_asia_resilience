# Revised Phase 2 Data Audit

## Study freeze

- **Paper:** Do Remittances Buffer Household Shocks? Evidence on Food Insecurity in Kyrgyzstan and Uzbekistan
- **Question:** Is the negative association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan?
- **Decision:** **FULL TWO-COUNTRY DESIGN**
- **Estimation rule:** country-specific models only; LiK and L2CU respondent records must not be pooled.
- **Phase boundary:** this audit stops before final analytical dataset construction, descriptive outcome production, or regression modelling.

## Source status

- Kyrgyzstan LiK 2019 (panel wave 6): available and audited.
- Uzbekistan L2CU rounds 1-82 (2018-2025): available and audited. The supplied round-82 questionnaire dates fieldwork to June 5-26, 2025.
- Uzbekistan MICS: retained as optional descriptive context only and excluded from the main remittance-shock model.
- Kazakhstan FIES: **PENDING DATA ACCESS**. It does not affect the two-country decision.

## Minimum mechanism decision

| Country | Remittance | Shock | Food insecurity | Result |
|---|---|---|---|---|
| Kyrgyzstan | `h620` (12 months) | `shock` + `h701` event roster (12 months) | `i251_1`-`i251_8` (12 months) | verified |
| Uzbekistan | `mig_living_remittance` and `remittance_hh` (past month) | `work_lost_hh`; major injury/illness/death via `change_important*` (past month) | `ln_1`-`ln_8` (past 30 days, since round 49) | verified |

Both countries contain verified variables with observed valid responses for the three-variable mechanism. The later models can therefore proceed country by country under the **FULL TWO-COUNTRY DESIGN**.

## Important limitations fixed at Phase 2

1. L2CU agricultural/climate shocks are **not available in the supplied files**. Household water-service disruption is not relabelled as a climate or agricultural shock.
2. L2CU region and rural/urban residence are absent from both supplied CSV headers and must not be inferred from `hhid`.
3. L2CU `popw` exists, but the supplied questionnaire does not define its normalization or exact weighting interpretation. It must not be used until supporting design documentation is confirmed.
4. LiK explicitly assigns no sample weights; the study description also warns about attrition.
5. LiK and L2CU differ in recall period, response scale, and respondent level for food insecurity. Comparisons are conceptual and coefficient-based, never respondent pooling.
6. L2CU `economic_challenge` measures views about national challenges, not a household shock; it is excluded from shock construction.
7. LiK food insecurity is reported by adult individuals. Any household aggregation requires a later, explicit rule and is not performed here.
8. The L2CU individual roster does not cover every household-round in the household CSV. Exact overlap and unmatched counts are in `revised_phase_02_key_integrity.csv` and must constrain later remittance merges.
9. L2CU stores one labelled `change_important_type` value per positive row even though the questionnaire says to choose all applicable changes; multiple simultaneous changes may not be retained.

## Audit products

- `revised_phase_02_variable_registry.csv`: exact variable, wording, recall, coding, missingness, source and later transformation plan.
- `revised_phase_02_variable_profile.csv`: aggregate nonmissing/valid counts and observed codes only.
- `revised_phase_02_l2cu_round_coverage.csv`: aggregate round-by-variable coverage.
- `revised_phase_02_l2cu_household_consistency.csv`: checks repeated household-round fields in the individual roster.
- `revised_phase_02_key_integrity.csv`: aggregate key uniqueness, missing-key, and cross-file coverage checks.
- `revised_phase_02_country_compatibility.csv`: minimum-variable comparison.
- `revised_phase_02_design_decision.json`: machine-readable design freeze.
- `revised_phase_02_dataset_status.csv`: dataset roles and Kazakhstan pending status.

## L2CU release structure

- Household CSV columns: 262; rows: 121,618.
- Individual CSV columns: 54; rows: 635,150.
- Round coverage and structural missingness are recorded variable by variable; blanks before module introduction are not treated as negative responses.

## Stop condition

Revised Phase 2 is complete. No country-specific analytical panel, harmonized outcome, interaction term, pooled respondent file, descriptive result, or regression result was created.
