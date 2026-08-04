# Kazakhstan FIES Future Append Plan

Unit: one respondent-year observation unless later documentation proves otherwise.

## Canonical Sources

- 2014: `data/kazakhstan/KAZ_2014_FIES_v01_EN_M_v01_A_OCS/microdata/KAZ_2014_FIES_v01_EN_M_v01_A_OCS.sav`
- 2015: `data/kazakhstan/KAZ_2015_FIES_v01_EN_M_v01_A_OCS/microdata/KAZ_2015_FIES_v01_EN_M_v01_A_OCS.sav`
- 2016: `data/kazakhstan/KAZ_2016_FIES_v01_EN_M_v01_A_OCS/microdata/KAZ_2016_FIES_v01_EN_M_v01_A_OCS.sav`
- 2017: `data/kazakhstan/KAZ_2017_FIES_v01_EN_M_v01_A_OCS/microdata/KAZ_2017_FIES_v01_EN_M_v01_A_OCS.sav`

## Common Target Variable Names

`respondent_id`, `survey_year`, `worried`, `healthy`, `fewfood`, `skipped`, `ateless`, `runout`, `hungry`, `whlday`, `weight`, `n_adults`, `n_child`, `raw_score`, `rasch_parameter`, `rasch_error`, `prob_mod_sev`, `prob_sev`, `age`, `education`, `area`, `gender`, `income`, `source_file`, `format_source`.

## Harmonization Rules

- Preserve source labels and add source-file markers.
- Convert FIES 1/0 codes only after preserving blanks as missing.
- Do not treat refusal or missing values as No.
- Keep `Area` as a two-category source variable unless supervisor approves a recode.
- Add year-specific source markers and prevent duplicate respondent-year keys.
- Decide whether yearly weights require rescaling before pooled trend estimation.

## Validation Checks

- Row count by year remains 1,000 before any exclusions.
- One respondent-year key per record.
- FIES item ranges remain 0/1/missing.
- Derived indicator ranges match the official files.
- No LiK or L2CU records are included.

## Conditions Preventing Append

- Any source checksum change.
- Unresolved format discrepancy between canonical and alternate files.
- Missing canonical file for any year.
- Supervisor rejects pooled-year weight treatment.