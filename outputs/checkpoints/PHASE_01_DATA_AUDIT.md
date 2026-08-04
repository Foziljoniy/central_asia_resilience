# Phase 1 Data Audit

## 1. Executive summary

Two outer archives were found: one Kyrgyzstan LiK collection and one Uzbekistan UNICEF collection. The audit recursively found 10 nested archives. Supported archives were integrity-tested and extracted to `data/interim/unpacked/`; original archives remained in their legacy `data/<country>/` locations. Uzbekistan is identified as a UNICEF Multiple Indicator Cluster Survey collection containing 2000 MICS2, 2006 MICS, and 2021-22 MICS6 materials—not L2CU. The current automated evidence recommends **Path C** with status **KYRGYZSTAN ONLY**: Kyrgyzstan has preliminary full-model candidates; Uzbekistan lacks a verified usable remittance construct for the main interaction.

## 2. Raw archive status

- `data/kyrgyzstan/dataverse_files.zip` — 72,129,966 bytes; SHA-256 `9f4206f0c161d00a3578bd4f5f9587725616f10c70bdc3c8256f325e73472a98`; integrity: passed; nested archives below this outer archive are shown in Section 3; extraction: verified existing extraction; warnings: none; errors: none.
- `data/uzbekistan/UNICEF-UZ-20250314T080638Z-001.zip` — 29,646,052 bytes; SHA-256 `9ba1340266a52a942583616c67e1970313713df4ffde3529ed0d2520489bcc42`; integrity: passed; nested archives below this outer archive are shown in Section 3; extraction: verified existing extraction; warnings: none; errors: none.

The archives were located outside the requested `data/raw/` folders. They were treated as protected originals and were not moved, renamed, or modified.

## 3. Nested archive hierarchy

- **Kyrgyzstan**
  - dataverse_files.zip [zip; passed; verified existing extraction]
    - Documentation.zip [zip; passed; verified existing extraction]
    - IDSC_repository.zip [zip; passed; verified existing extraction]
      - LIK_10_13_Docu.zip [zip; passed; verified existing extraction]
      - LIK_10_13_spss.zip [zip; passed; verified existing extraction]
      - LIK_10_13_stata.zip [zip; passed; verified existing extraction]
      - LiK_2016.zip [zip; passed; verified existing extraction]
        - LiK16_Questionnaires_Eng.zip [zip; passed; verified existing extraction]
        - LiK16_Questionnaires_Kyr.zip [zip; passed; verified existing extraction]
        - LiK16_Questionnaires_Rus.zip [zip; passed; verified existing extraction]
      - LiK_2022.zip [zip; passed; verified existing extraction]
- **Uzbekistan**
  - UNICEF-UZ-20250314T080638Z-001.zip [zip; passed; verified existing extraction]

See `phase_01_archive_inventory.csv` and `phase_01_archive_members.csv` for complete member-level detail.

## 4. Kyrgyzstan dataset inventory

- Survey: Life in Kyrgyzstan Study (LiK).
- Waves/releases found: 2010, 2011, 2012, 2013, 2016, 2019.
- The “Version 2022” package documents and labels its survey wave as LiK19 (2019); 2022 is treated as a release/version marker, not automatically as the survey year.
- Metadata-readable dataset files: 462.
- File families include household, individual/person, community, agriculture, control/panel-roster, and youth modules.
- The original 3,000-household sample used stratified two-stage random sampling over 16 strata. The 2019 study description states that no sample weights were assigned; attrition makes proportional representativeness uneven and must be treated as a limitation.
- Both SPSS and Stata copies exist for 2010-13 and 2016; the 2019 release is supplied in Stata format. Format duplicates are not treated as independent samples.
- The LiK 2019 community file `Community/cm1.dta` could not be decoded by `pyreadstat` because of an invalid byte sequence. The containing archives passed ZIP integrity tests; this file requires manual Stata review if community controls are needed.
- Candidate identifiers, weights, regions, residence, migration/remittance, shocks, expenditure/consumption, assets, and employment variables are listed in the checkpoint CSVs. Exact questionnaire confirmation remains a Phase 1 review task where labels are incomplete.

## 5. Uzbekistan survey identification

- Exact collection: UNICEF Uzbekistan Multiple Indicator Cluster Survey materials.
- Components: MICS2 2000, MICS 2006, and MICS Round 6 2021-22.
- Organization: the 2021-22 survey was carried out by the State Committee of the Republic of Uzbekistan on Statistics as part of UNICEF's Global MICS Programme, with UNICEF technical support.
- Representativeness and design: the report describes a new representative Round 2 sample, estimates at national/urban-rural/six-zone levels, a stratified three-stage design with mahalla PSUs, and separate non-self-weighting survey weights by round.
- Questionnaire types: household; all women age 15-49; all children under five through mothers/caretakers; and one randomly selected child age 5-17 through a mother/caretaker (with a limited emancipated-child exception).
- Modules include household members, education, household characteristics, social transfers, energy, WASH, women's background/fertility/maternal health, child background/labour/discipline/functioning, early childhood development, diet, immunisation, illness care, and anthropometry.
- Metadata-readable dataset files: 15; survey years/components: 2000, 2006, 2021-22.
- Respondent-specific weights and design variables must be selected at the matching observation level; they are not interchangeable. The report states that the sample is not self-weighting.
- `fs.sav` is the children age 5-17 dataset (its identifiers begin `FS`); it is not a food-security module. No household food-insecurity-experience or expenditure module was found in the MICS6 data supplied.
- This collection is not identified as L2CU.

## 6. Primary-topic variable availability

### Kyrgyzstan preliminary candidates

**Remittances and migration**

- `h620` (2019; H620 During the last 12 months, did you receive any money from abroad sent by mi; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h625` (2019; H625 Did you receive regularly the money sent by the migrant(s)? (use the case o; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h626` (2019; H626 How regularly your household received migrant's remittances?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `i500_8` (2019; (how to use remittances) i500 which member of the family had the main decision-m; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id5.dta`)
- `h627_3` (2019; Money exchanged with someone in the country and abroad; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h628_10` (2019; H628 What did you spend the money on? Please indicate what the migrants' remitta; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h628_11` (2019; H628 What did you spend the money on? Please indicate what the migrants' remitta; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h628_12` (2019; H628 What did you spend the money on? Please indicate what the migrants' remitta; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)

**Shocks**

- `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- `h701` (2019; Was HH affected by shocks in last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- `h703` (2019; Estimate extra expenses made due to this shock, Soms; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- `h704` (2019; Estimate loss of income due to this shock, Soms; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- `i214_6` (2010; Have you suffered from other serious illnesses in the last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LIK_10_13_stata__4f932d8b/stata/data2010/individial/id2.dta`)
- `i214_6` (2010; Have you suffered from other serious illnesses in the last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LIK_10_13_spss__b52af7b0/spss/data2010/individial/id2.sav`)
- `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- `a708` (2019; how many animals were lost due to death during the last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Agriculture/ag71.dta`)

**Food security, expenditure, welfare, and assets**

- `i251_1` (2019; Were you worried that you wouldn't have enough food due to lack of money?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id2.dta`)
- `i251_2` (2019; Have you been unable to eat healthy and nutritious food due to lack of money?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id2.dta`)
- `i251_3` (2019; Have you eaten only a few types of food due to lack of money or other resources?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id2.dta`)
- `i251_4` (2019; Have you missed a meal because you don't have enough money or other resources?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id2.dta`)
- `i251_5` (2019; Have you eaten less than you should have due to lack of money or other resources; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id2.dta`)
- `i251_6` (2019; Has your household run out of food due to lack of money or other resources?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id2.dta`)
- `i251_7` (2019; Were you hungry but unable to eat because you lacked money or other resources; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id2.dta`)
- `i251_8` (2019; Have you not eaten all day due to lack of money or other resources?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id2.dta`)
- `y312_1` (2019; you were worried you would not have enough food to eat because of a lack of mone; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Youth/yt3.dta`)
- `y312_2` (2019; you were unable to eat healthy and nutritious food because of a lack of money or; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Youth/yt3.dta`)

### Uzbekistan preliminary candidates

**Remittances and migration**

- `WB15` (2021-22; Duration of living in current place; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `WB16` (2021-22; Place of living prior to moving to current place; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `WB17` (2021-22; Region prior to moving to current place; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)

**Shocks**

- No label-supported candidate found.

**Food security, expenditure, welfare, and assets**

- `windex10` (2021-22; Wealth index decile; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `windex10r` (2021-22; Rural wealth index decile; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `windex10u` (2021-22; Urban wealth index decile; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `windex5` (2021-22; Wealth index quintile; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `windex5r` (2021-22; Rural wealth index quintile; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `windex5u` (2021-22; Urban wealth index quintile; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `wscore` (2021-22; Combined wealth score; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `wscorer` (2021-22; Rural wealth score; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `wscoreu` (2021-22; Urban wealth score; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/wm.sav`)
- `windex10` (2021-22; Wealth index decile; `data/interim/unpacked/uzbekistan/UNICEF-UZ-20250314T080638Z-001/depth_00/UNICEF-UZ/Uzbekistan_MICS6_Datasets/Uzbekistan_MICS6_SPSS_Datasets/hl.sav`)

## 7. Can the research question be tested in Kyrgyzstan?

**Preliminary answer: yes, subject to questionnaire and variation checks.** LiK contains longitudinal household/person modules and label-supported candidates for parts of the remittance-shock-welfare mechanism. Phase 2 must verify exact constructs, joins, missingness, and within-wave/within-household variation before model construction.

## 8. Can the research question be tested in Uzbekistan?

**Preliminary answer: not as the full remittance-by-shock interaction from currently verified evidence.** MICS6 supports household wealth/assets, WASH, women, child, education, nutrition, and social-transfer constructs, plus women's residential-migration history (`WB15`/`WB16`). No household remittance receipt/amount, household shock module, household food-expenditure module, or household food-insecurity-experience module was found in the supplied MICS6 metadata.

## 9. Can the two countries be compared?

**Classification: conceptual only.** The instruments are not contemporaneous and differ in design, respondents, weights, observation levels, and wording. Country-specific analysis is required; pooling is not supported.

## 10. Recommended research path

**Path C.** Kyrgyzstan has preliminary full-model candidates; Uzbekistan lacks a verified usable remittance construct for the main interaction. This recommendation is preliminary and explicitly subject to supervisor approval and manual confirmation of the top variable candidates.

## 11. Candidate primary outcomes

Provisional ranking, conditional on exact questionnaire verification:

1. LiK 2019 eight-item food-insecurity experience battery (`i251_1`-`i251_8`), with an explicit decision on individual versus household aggregation.
2. LiK household food expenditure (`hh4a`: `h401c`, by `food_item`, with period/unit fields).
3. LiK household food consumption from own production (`h402a`), acknowledging that it is not total consumption by itself.
4. LiK household shock-related income loss or extra expense (`hh7`: `h703`/`h704`) as secondary welfare outcomes, not food-security outcomes.
5. Household assets/wealth for secondary descriptive analysis; MICS wealth is not a substitute for the missing remittance-shock interaction.

## 12. Candidate remittance measures

- `h620` (2019; H620 During the last 12 months, did you receive any money from abroad sent by mi; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h625` (2019; H625 Did you receive regularly the money sent by the migrant(s)? (use the case o; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h626` (2019; H626 How regularly your household received migrant's remittances?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `i500_8` (2019; (how to use remittances) i500 which member of the family had the main decision-m; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Individual/id5.dta`)
- `h627_3` (2019; Money exchanged with someone in the country and abroad; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h622` (2019; H622 How much money in total did the migrant(s) send during the last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh6b.dta`)
- `h617_c` (2013; how much money did the migrant(s) send during the last 12 months?  currency; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LIK_10_13_stata__4f932d8b/stata/data2013/household/hh6b.dta`)
- `h617_s` (2013; how much money did the migrant(s) send during the last 12 months?  amount; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LIK_10_13_stata__4f932d8b/stata/data2013/household/hh6b.dta`)

No candidate should be treated as remittance receipt or amount solely from a short name.

## 13. Candidate shock measures

- **Economic:** `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`), `h701` (2019; Was HH affected by shocks in last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`), `h703` (2019; Estimate extra expenses made due to this shock, Soms; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- **Employment:** `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`)
- **Health:** `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`), `i214_6` (2010; Have you suffered from other serious illnesses in the last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LIK_10_13_stata__4f932d8b/stata/data2010/individial/id2.dta`), `i214_6` (2010; Have you suffered from other serious illnesses in the last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LIK_10_13_spss__b52af7b0/spss/data2010/individial/id2.sav`)
- **Agricultural:** `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`), `a708` (2019; how many animals were lost due to death during the last 12 months?; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Agriculture/ag71.dta`), `h701_6` (2016; pest or diseases (crops or livestock); `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2016__e03a0c74/LiK16_IDSC-IZA/LiK16_data_stata/Household/hh7.dta`)
- **Climate-related:** `shock` (2019; Name of shock; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh7.dta`), `h804_1` (2019; Drought; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh8.dta`), `h804_2` (2019; Too much rain or floods; `data/interim/unpacked/kyrgyzstan/dataverse_files/depth_02/LiK_2022__7c67a235/Version_2022/Household/hh8.dta`)

## 14. Candidate control variables

Household size, dependency composition, head age/sex/education, employment, rural residence, region, assets/wealth, survey wave/round, interview month/season, and sampling-design variables are provisional controls. Their exact files and labels are in `phase_01_variable_candidates.csv` and `phase_01_topic_feasibility_matrix.csv`.

## 15. Literature review status

- Literature records inventoried: 4.
- Core seed: Sultakeev and Petrick (2025), not full-text verified from supplied files unless noted in the literature matrix.
- Supporting seed: Egamberdiev et al. (2025), same verification caveat.
- Optional seeds: Bozkuş Kahyaoğlu et al. (2025) and Kovaleva et al. (2025).
- Missing areas: remittances/expenditure, migration as insurance, shocks and migration, food-security resilience, Uzbekistan evidence, and broader Central Asian resilience.
- No findings or missing citation details were invented.

## 16. Recommended main project

- **Title:** Migration, Remittances, Shocks, and Household Food Security in Kyrgyzstan and Uzbekistan.
- **Question:** Are remittances associated with a weaker negative relationship between household shocks and food security or household welfare?
- **Hypotheses:** H1 better outcomes among remittance recipients; H2 worse outcomes with shocks; H3 an interaction consistent with buffering; H4 stronger moderation in rural, lower-wealth, child-containing, or agriculture/climate-exposed households.
- **Outcome/remittance/shock:** TBD after supervisor review of exact candidates.
- **Controls:** verified household composition, head characteristics, employment, residence, region, assets/wealth, and wave/season.
- **Country strategy:** country-specific models first; no automatic pooling.
- **Limitations:** selection, endogeneity, reverse causality, self-report, measurement error, attrition, and cross-survey comparability.
- **One-week/four-student feasibility:** feasible only with a narrowly scoped country-specific specification and a supervisor-approved variable map; a harmonized two-country interaction is higher risk.

## 17. Backup projects

1. **Wealth, WASH, and child nutrition/health:** strong MICS constructs, with conceptual LiK living-condition comparison only where compatible.
2. **Rural-urban digital and educational inequality:** use residence, wealth/assets, internet/computer/mobile access, and education outcomes where label and respondent universes align.

## 18. Missing materials

- Full texts and verified citation details for the four literature seeds.
- Any separate LiK codebooks or weighting/attrition documentation not present in the archive.
- Uzbekistan MICS6 full questionnaires/codebooks if the supplied report/readme does not document every required construct.
- Explicit data-use terms where absent from the files.

## 19. Questions requiring supervisor approval

1. Confirm Path C after manual review of the top remittance and shock candidates.
2. Confirm whether LiK 2019 is the preferred main wave or whether the 2010-16 panel is central.
3. Approve the primary outcome and its direction before any coding.
4. Decide whether Uzbekistan is a secondary descriptive/welfare analysis if no true remittance construct exists.
5. Approve any necessary manual translation/interpretation of Russian or Kyrgyz questionnaire wording.

## 20. Exact Phase 2 proposal

After supervisor approval only: manually verify the shortlisted variables against questionnaires and value labels; document universes, units, missing codes, and recall periods; select the country path; create a signed variable-harmonization registry; specify household/person joins and survey weights; and freeze a pre-analysis specification. Do not construct analytical datasets or run descriptive/regression analysis until that registry is approved.

## Phase boundary

No harmonization, cleaning, analytical dataset construction, descriptive analysis, regression, robustness analysis, pooling, or final-paper writing was performed.
