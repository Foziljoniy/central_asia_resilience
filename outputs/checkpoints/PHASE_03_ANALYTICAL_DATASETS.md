# Phase 3 Analytical Datasets

## 1. Executive summary

Phase 3 constructed country-specific analytical datasets, wrote the required Parquet files, and produced QA registries, dictionaries, sample-flow tables, and reproducibility metadata.

## 2. Frozen research design

The main Kyrgyzstan-Uzbekistan design remains unchanged: FULL TWO-COUNTRY DESIGN, country-specific models, no respondent pooling. Kazakhstan is K1+K2 benchmark context only.

## 3. Input sources and checksums

Input checksums are recorded in `phase_03_reproducibility_manifest.json`. Raw source checksums remain unchanged.

## 4. Kyrgyzstan source joins

Join audit is in `phase_03_lik_join_audit.csv`; one-to-many modules were aggregated before merging. No uncontrolled many-to-many merge was performed.

## 5. Kyrgyzstan remittance construction

`lik_remittance_receipt` uses direct `h620` responses and Module 6A structural-zero evidence only when no eligible migrant is verified. Provenance is stored in `lik_remittance_receipt_source`.

## 6. Kyrgyzstan shock construction

The shock event roster was aggregated using `lik_shock_crosswalk.csv`.

## 7. Kyrgyzstan food-insecurity construction

LiK FIES items are scored only when all eight items have valid responses; incomplete responses are not silently scored.

## 8. Kyrgyzstan analytical datasets

Adult rows constructed: 7043. Household sensitivity rows constructed: 2314. Parquet status: adult=CREATED, household=CREATED.

## 9. Uzbekistan source joins

Join audit is in `phase_03_l2cu_join_audit.csv`. Unmatched household-rounds are flagged, not silently dropped.

## 10. Uzbekistan remittance construction

Member-migrant and external household remittances are kept separately and combined only when rules establish receipt or non-receipt.

## 11. Uzbekistan shock construction

Primary shock is `uzb_work_loss_shock`; secondary verified shock is major illness, injury, or death. Water, gas, and heat disruption are retained as service disruptions, not climate shocks.

## 12. Uzbekistan food-insecurity construction

L2CU is restricted to rounds 49-82. FIES raw scores require all eight valid items.

## 13. Uzbekistan analytical dataset

Household-round rows constructed: 48925. Parquet status: CREATED.

## 14. Kazakhstan yearly construction

Four yearly Kazakhstan dataframes were standardized from canonical SAV files.

## 15. Kazakhstan append validation

Append validation is in `phase_03_kazakhstan_append_validation.csv`; 4,000 expected respondent-year records are accounted for in memory, with no format duplicates appended.

## 16. Kazakhstan benchmark dataset

Combined benchmark rows constructed: 4000. Parquet status: CREATED.

## 17. Cross-country comparability

Documented in `phase_03_cross_country_concept_registry.csv`; no country respondent records are pooled.

## 18. Sample-flow results

Kyrgyzstan eligible adults: 6315. Uzbekistan eligible household-rounds: 47135. Kazakhstan benchmark-eligible records: 3728.

## 19. Missing-data patterns

Aggregate missingness is reported in the country quality report CSVs only; no substantive means or prevalence estimates are reported.

## 20. Data-quality warnings

L2CU `popw` is retained only as unverified. Kazakhstan original weights are retained; `kaz_weight_mean1_within_year` is constructed only for later sensitivity and is not used. Exact prompt-named Phase 2 input files were absent and approved revised outputs were used.

## 21. Remaining methodological decisions

L2CU popw remains unapproved for analytical weighting.; Kazakhstan pooled prevalence is not approved; mean-1 weight is retained only for later sensitivity.; LiK household-level food-insecurity aggregation remains sensitivity-only.; Exact prompt-named Phase 2 files absent; revised Phase 2 approved outputs used instead.

## 22. Phase 4 recommendation

Recommended status: PROCEED.

## Phase 3 Technical Revision

## 1. Reason for revision

Phase 3 was substantively complete, but required Parquet exports were blocked because no Parquet engine was installed.

## 2. Pyarrow installation and version

`pyarrow` was installed with `python -m pip install pyarrow`. Verified version: 25.0.0.

## 3. Regeneration-count validation

Regenerated counts status: MATCH. Details are in `phase_03_regeneration_count_validation.csv`.

## 4. Kyrgyzstan Parquet exports

Adult dataset: VALID. Household sensitivity dataset: VALID.

## 5. Uzbekistan Parquet export

Household-round dataset: VALID.

## 6. Kazakhstan Parquet exports

Yearly datasets: 2014=VALID, 2015=VALID, 2016=VALID, 2017=VALID. Combined benchmark: VALID.

## 7. Read-back validation

Every required Parquet file was read back with pandas/pyarrow. Details are in `phase_03_parquet_file_validation.csv`.

## 8. Checksum validation

Parquet SHA-256 values are recorded in `phase_03_parquet_file_validation.csv` and the reproducibility manifest.

## 9. Weight decisions

L2CU `popw` is retained but not approved. Kazakhstan original yearly weights are approved for later year-specific estimates only; pooled primary estimates are not approved. `kaz_weight_mean1_within_year` is created for later sensitivity and not used.

## 10. Outcome-level decision

Kyrgyzstan adult outcome remains primary. Household summaries are sensitivity only.

## 11. Phase 2 file mapping

Exact missing Phase 2 filenames are documented in `phase_03_phase2_input_mapping.csv`.

## 12. Remaining limitations

No substantive analysis was run. L2CU weight documentation remains unresolved. Kazakhstan pooled prevalence remains not approved.

## 13. Phase 4 recommendation

Recommended Phase 4 status: PROCEED.
