# Central Asian Household Resilience Project

Working paper: **Do Remittances Buffer Household Shocks? Evidence on Food Insecurity in Kyrgyzstan and Uzbekistan**.

Current status: **Phase 4 complete** for aggregate descriptive analysis, measurement validation, missingness assessment, and model-readiness review. Countries remain non-pooled, and final regression models have not been produced.

## Current Research Question

Is the negative association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan?

This is an observational association and moderation question. Causal language is reserved for a later design only if a credible identification strategy is developed.

## Dataset Roles

- Kyrgyzstan LiK: main panel and household analysis; migration/remittances; household shocks; food expenditure and welfare; 2019 food-insecurity questions.
- Uzbekistan L2CU 2018-2025: main household-panel analysis; migration/remittances; shocks and coping; Food Insecurity Experience Scale; household characteristics and welfare.
- Uzbekistan MICS: optional descriptive context only; not part of the main remittance-shock model.
- Kazakhstan FIES: regional food-security benchmark; **ACCESS GRANTED** for 2014-2017 year-specific packages; not part of the current remittance-shock regression design.

LiK and L2CU respondent records must not be pooled. Later models should be country-specific.

## Revised Phase 2 Decision

The audited files verify the minimum three-variable mechanism in both main countries:

- remittance receipt;
- household shock exposure;
- food insecurity or a defensible welfare outcome.

The current design decision is therefore **FULL TWO-COUNTRY DESIGN**. See [REVISED_PHASE_02_AUDIT.md](D:/howgart/central_asia_resilience/outputs/checkpoints/REVISED_PHASE_02_AUDIT.md) and [revised_phase_02_design_decision.json](D:/howgart/central_asia_resilience/outputs/checkpoints/revised_phase_02_design_decision.json).

## Raw-Data Protection

The original archives remain in their legacy source locations and are treated as immutable originals. Revised Phase 2 creates the requested `data/raw/` folder structure for project organization but does not move, edit, or overwrite supplied microdata. Extraction occurs only below `data/interim/unpacked/`; source SHA-256 hashes are recorded before and after the audit.

## Run Audits

From the project root:

```powershell
python src/run_phase_01.py
python src/run_revised_phase_02.py
```

In this workspace, the bundled Codex Python runtime includes the libraries used for the audit. The runner writes aggregate-only outputs under `outputs/checkpoints/`.

## Phase Boundary

Revised Phase 2 stops before analytical dataset construction and regression modelling. The next phase may construct country-specific analysis files only after preserving the registry decisions and resolving documented caveats such as L2CU location variables, L2CU weight documentation, LiK remittance-module universe, and differing recall periods.

## Phase 2 Kazakhstan Addendum

Kazakhstan FIES access is granted for 2014-2017. The addendum audits year-specific packages under `data/kazakhstan/`, selects SPSS `.sav` files as canonical working sources, verifies comparable FIES items and official derived indicators, and classifies Kazakhstan as a K1+K2 benchmark: food-insecurity trend plus demographic vulnerability context.

The addendum does not append Kazakhstan years, calculate prevalence, run regressions, or change the frozen Kyrgyzstan-Uzbekistan design.

## Phase 3 Analytical Dataset Construction

Phase 3 construction scripts and QA outputs have been added. Analytical dataframes are built in memory and all aggregate QA documentation is produced. Required Parquet exports are blocked in this environment until a Parquet engine such as `pyarrow` or `fastparquet` is approved/installed.

No substantive descriptive analysis, prevalence estimates, regressions, hypothesis tests, or policy-effect calculations are run in Phase 3.


## Phase 3 Technical Revision

`pyarrow` 25.0.0 was installed and the required Phase 3 Parquet files were exported and validated. The previous blocked-marker JSON files were archived under `outputs/archive/phase_03_blocked_markers/`.


## Kazakhstan Phase 4 status

Kazakhstan FIES access is granted. Kazakhstan is used as a K1+K2 food-insecurity trend and demographic benchmark. It is not part of the remittance-shock interaction model.


## Phase 4 descriptive analysis

Aggregate descriptive outputs, measurement validation, missingness assessment, and model-readiness checks are complete. No final regression model was estimated. Kazakhstan FIES access is granted. Kazakhstan is used as a K1+K2 food-insecurity trend and demographic benchmark. It is not part of the remittance-shock interaction model.


## Phase 5 country-specific association models

Phase 5 is complete. Models are country-specific, observational, household-clustered where applicable, and do not pool country records or make causal claims.


## Phase 5 sparse-cell revision

Uzbekistan work-loss is reclassified as secondary exploratory. UZBROAD_M2 is PRIMARY APPROVED WITH LIMITATIONS using `uzb_any_verified_shock`; estimates remain unweighted and observational.


## Phase 6 evidence synthesis

Phase 6 is complete. Evidence is synthesized for manuscript preparation with non-causal wording, country-specific interpretation, and Kazakhstan benchmark boundaries.


Phase 7 limited robustness: completed; primary findings preserved; remaining literature and weight limitations documented.


## Phase 8 manuscript preparation

Markdown manuscript draft and internal review package created. No journal-formatted DOCX/PDF generated.
