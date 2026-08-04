# Phase 1 Compatibility and Risk Report

## Overall assessment

- Preliminary research path: **Path C**.
- Primary-question status: **KYRGYZSTAN ONLY**.
- Basis: Kyrgyzstan has preliminary full-model candidates; Uzbekistan lacks a verified usable remittance construct for the main interaction.
- This is a feasibility audit, not harmonization or analysis. Automated candidates require questionnaire confirmation.

## Archive and extraction risks

- Archives inventoried: 12.
- Archive records with errors or integrity failures: 0.
- Unsupported RAR/7Z archives: 0.
- Exact duplicate archives were skipped by SHA-256; duplicate member paths were preserved with deterministic suffixes.
- Path traversal, absolute paths, links, encrypted entries, compression ratios, member counts, and size limits were checked before extraction.
- Original archives were detected in legacy `data/<country>/` folders and left unchanged; the requested `data/raw/<country>/` folders were created but remain empty.

## Documentation and metadata risks

- Missing or incomplete codebooks may make short module names (`hh*`, `id*`, `ag*`) insufficient for substantive mapping.
- Candidate extraction uses variable labels/value labels and documented exact design-variable names; short names alone do not establish meaning.
- Some legacy `.doc` or image-only PDF content may require manual review.
- SPSS and Stata label metadata may omit full question wording, units, recall-period detail, skip logic, or constructed-variable provenance.
- Missing weights, identifiers, labels, and questionnaires must be assessed file by file; absence from an automated search is not proof of absence.

## Cross-country construct risks

- LiK is a longitudinal household study; Uzbekistan files are repeated MICS cross-sections (2000, 2006, and 2021-22), not L2CU.
- Latest relevant years differ: LiK 2019 (distributed in a Version 2022 package) versus Uzbekistan MICS6 2021-22.
- Household definitions, respondents, eligibility universes, observation levels, sampling designs, and weights differ.
- Remittance constructs may distinguish receipt, amount, sender, domestic/international source, and reference period differently.
- Shock constructs may differ in event definition, subjectivity, reference period, and household versus individual reporting.
- Food-security experience, food consumption, and expenditure are not interchangeable outcomes.
- Currency, price period, season, inflation, and recall windows would require explicit Phase 2 harmonization.
- Uzbekistan MICS women's, child, household, household-member, birth-history, and children-age-5-17 files use different respondent-specific weights. The file `fs.sav` is the children age 5-17 questionnaire, not a food-security file.
- LiK panel attrition and refreshment/replacement households require explicit panel-roster review.

## Data governance risks

- No respondent-level values are written to reports or inventories.
- Identifiers are inventoried only by variable name/label, not value.
- Data-use restrictions were not inferred where documentation was silent; supervisor/manual review is required before publication or sharing.
- Potential personal-information fields must be excluded from any future analytical exports.

## Main-topic decision risks

- A full two-country comparison requires verified remittance receipt, shock exposure, and comparable welfare/food-security constructs in both countries.
- If Uzbekistan lacks a true remittance construct, Path C is required even though MICS supports strong secondary welfare, food-security, women, child, WASH, and wealth analyses.
- Country-specific models are required before any cross-country synthesis. Pooling is not justified in Phase 1.
- Alternative topics should be considered only if the primary question is not feasible after manual confirmation.

## Dataset parsing status

- Dataset files inventoried: 477 (including SPSS/Stata format copies that are not independent samples).
- Metadata read limitations: 9.
- `LiK 2019/Community/cm1.dta` produced an invalid-byte-sequence error in `pyreadstat`. Its containing ZIP passed integrity testing, so this is documented as a metadata-decoding limitation rather than proof of archive corruption; manual Stata review is required if community variables are used.

## Phase boundary

No cleaning, harmonization, analytical dataset construction, descriptive statistics, regression, pooling, or robustness analysis was performed.
