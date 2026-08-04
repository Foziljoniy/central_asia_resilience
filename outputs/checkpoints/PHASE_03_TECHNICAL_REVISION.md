# Phase 3 Technical Revision

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
