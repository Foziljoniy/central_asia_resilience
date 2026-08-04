# Do Remittances Buffer Household Shocks? Evidence on Food Insecurity in Kyrgyzstan and Uzbekistan

## Abstract

Household shocks can worsen food insecurity, while remittances may provide liquidity that helps households smooth consumption. This paper asks whether the negative association between household shocks and food insecurity is weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan. The analysis uses country-specific observational models rather than pooling incompatible surveys: adult respondents from the 2019 Life in Kyrgyzstan Study and household-rounds from Listening to the Citizens of Uzbekistan rounds 49-82. Kazakhstan is used only as a regional food-insecurity and demographic benchmark. In Kyrgyzstan, the preferred interaction estimate was negative but imprecise (-0.214; 95% CI -0.655 to 0.227). In Uzbekistan, the revised broad-shock model showed a negative interaction (-0.541; 95% CI -1.041 to -0.040), with 42 household-rounds from 38 households in the joint remittance-plus-shock cell. The Uzbekistan household fixed-effects estimate remained negative but was attenuated and imprecise (-0.177; 95% CI -0.551 to 0.197). All L2CU estimates are unweighted because `popw` documentation remains insufficient. The findings are consistent with a remittance-related buffering pattern, especially in Uzbekistan, but they are observational and do not establish causal protection.

## Keywords

remittances; household shocks; food insecurity; resilience; migration; Kyrgyzstan; Uzbekistan; Central Asia

## Introduction

Households in Central Asia face income, employment, health, and environmental shocks that can disrupt access to food. These disruptions matter not only because they reduce current welfare, but also because they may force households to draw down assets, defer expenditures, or rely on informal support. Migration and remittances are central to household livelihoods in parts of the region, and remittance receipt may be associated with additional liquidity when shocks occur. Yet the same relationships are difficult to interpret. Households receiving remittances differ from non-receiving households, and adverse circumstances may themselves trigger transfers.

This paper asks whether remittance receipt is associated with a weaker relationship between verified household shocks and food insecurity in Kyrgyzstan and Uzbekistan. The design is explicitly observational. The aim is not to estimate the causal effect of remittances, but to assess whether the shock-food-insecurity association differs by remittance status after country-specific adjustment.

Central Asia is a useful setting because migration, household vulnerability, and social protection questions intersect sharply. The paper uses two main empirical datasets: the Life in Kyrgyzstan Study and Listening to the Citizens of Uzbekistan. These surveys differ in observation unit, reference period, design, and shock measurement, so the analysis keeps them separate. Kazakhstan is included only as a benchmark for regional food-insecurity and demographic context.

Existing verified literature supports the broad relevance of remittances, household spending, and consumption smoothing, including work using the Life in Kyrgyzstan Study and conceptual work on remittances as informal insurance (Food and Agriculture Organization of the United Nations, n.d.; World Bank, 2025; Remittances and Household Spending Strategies, n.d.; Ebeke and Combes, 2017; Otame, 2023). However, Uzbekistan-specific peer-reviewed evidence connecting remittances, household shocks, and food insecurity remains a citation gap: [CITATION GAP - UZBEKISTAN-SPECIFIC SOURCE REQUIRED].

The contribution is therefore empirical and methodological. The study examines the moderating association between remittance receipt and verified shocks in two Central Asian settings, estimates country-specific models rather than pooled regressions, distinguishes preferred findings from exploratory work-loss results, and reports how household fixed effects and additional robustness checks qualify the Uzbekistan evidence.

[Table 1 about here]

## Conceptual framework and hypotheses

Household shocks may worsen food insecurity through several channels. Employment loss can reduce cash income. Health shocks can increase expenditures and reduce labor supply. Agricultural and climate-related shocks can affect production and food availability. These channels can reduce purchasing power or available food, increasing the number of food-insecurity experiences reported by households or individuals.

Remittances may moderate this relationship by providing liquidity, supporting consumption smoothing, or functioning as informal insurance. Remittances may help households buy food, maintain essential spending, or avoid coping strategies that reduce future welfare. At the same time, remittance receipt is endogenous. Migrant-sending households may be positively selected, adverse household conditions may trigger transfers, and the poorest households may be unable to finance migration. Migrant income may also be unstable.

The empirical hypotheses are therefore stated cautiously. H1 is that household shocks are associated with higher food-insecurity scores. H2 is that remittance receipt is associated with lower food-insecurity scores conditional on observed characteristics. H3 is that the positive shock-food-insecurity association is weaker among remittance-receiving households. H3 is tested through the interaction between remittance receipt and shock exposure.

## Data

### Kyrgyzstan: Life in Kyrgyzstan

The Kyrgyzstan analysis uses the Life in Kyrgyzstan Study. The preferred model uses 6,297 adults from 2,215 households. The outcome is an adult respondent FIES-style raw score, linked to household-level remittance and shock exposure. The main shock is `lik_any_shock`, with secondary economic, health, agricultural, and climate categories available for robustness. The analysis is unweighted because no approved survey weight is assigned. The food-insecurity reference period is 12 months.

### Uzbekistan: Listening to the Citizens of Uzbekistan

The Uzbekistan analysis uses Listening to the Citizens of Uzbekistan rounds 49-82, with household-rounds as the unit. The preferred broad-shock model uses 47,135 household-rounds from 2,000 households. The outcome is a complete eight-item FIES-style raw score. The primary shock, `uzb_any_verified_shock`, includes household work loss, major illness, major injury, and death. Service disruption is not treated as a climate shock. L2CU `popw` remains unapproved because documentation is insufficient, so estimates are unweighted. The food-insecurity reference period is 30 days.

### Kazakhstan benchmark

Kazakhstan provides 2014-2017 adult respondent-year FIES benchmark context. Year-specific original weights are used for benchmark estimates. Kazakhstan does not contain verified remittance or household-shock variables, so it is not part of the mechanism analysis.

## Measures

### Food insecurity

Food insecurity is measured with eight binary items summed to a raw score from 0 to 8. Higher scores indicate worse food insecurity. Scores are constructed only when all eight items are valid. The Kyrgyzstan score refers to a 12-month period, while the Uzbekistan score refers to a 30-day period. These raw scores are not official calibrated national prevalence estimates.

### Remittance receipt

Kyrgyzstan remittance receipt is measured at the household level and linked to adult respondents. Uzbekistan remittance receipt combines verified member-migrant and external household remittance components. Receipt, not amount, is the primary measure because remittance amounts involve unresolved currencies and units.

### Household shocks

Kyrgyzstan uses any verified household shock as the primary exposure. Uzbekistan uses the broad verified shock described above. The work-loss-specific Uzbekistan model is retained as a secondary event-specific exploratory result because the joint remittance-plus-work-loss cell contains only 10 household-rounds from nine households.

### Control variables

Core controls include verified demographic, household composition, location, and time variables available in each country. Current income, expenditure, asset sales, and related variables are not core controls because they may lie downstream of shocks or remittances.

## Empirical strategy

The country-specific model is:

FoodInsecurity_it = beta_0 + beta_1 Remittance_it + beta_2 Shock_it + beta_3(Remittance_it x Shock_it) + gamma X_it + fixed effects + error_it.

The main parameter is beta_3. Because higher food-insecurity scores are worse, a negative beta_3 is compatible with a weaker adverse shock association among remittance-receiving households. Main effects are interpreted conditionally and together with adjusted predictions. Kyrgyzstan models use household-clustered standard errors, demographic controls, residence, and region fixed effects. Uzbekistan models use household-clustered standard errors, household controls, and round fixed effects. Observed-value standardization is used to calculate adjusted four-group predictions.

Robustness checks include standardized outcomes, bounded-outcome models, influence checks, household fixed effects for Uzbekistan, round-sensitive inference, lagged sensitivity, participation restrictions, and complete-case assessment. Household fixed effects do not resolve all endogeneity.

## Results

### Analytical samples

The preferred Kyrgyzstan model uses 6,297 adults from 2,215 households. The preferred Uzbekistan model uses 47,135 household-rounds from 2,000 households. Kazakhstan contributes benchmark records for 2014-2017 only. Countries are not respondent-pooled.

### Descriptive four-group patterns

In Kyrgyzstan, adjusted KG_M2 predictions are 1.240 for no remittance/no shock, 0.983 for remittance/no shock, 1.449 for no remittance/shock, and 0.978 for remittance/shock. In Uzbekistan, UZBROAD_M2 predictions are 0.734 (95% CI 0.677 to 0.792) for no remittance/no verified shock, 0.596 (95% CI 0.499 to 0.694) for remittance/no verified shock, 1.288 (95% CI 1.094 to 1.483) for no remittance/verified shock, and 0.609 (95% CI 0.133 to 1.085) for remittance/verified shock.

[Figure 2 about here]

[Figure 3 about here]

### Kyrgyzstan preferred model

The preferred Kyrgyzstan interaction estimate was -0.2140 (95% CI -0.6549 to 0.2269; p=0.3415), based on 6,297 adults from 2,215 households. The standardized interaction was -0.091 (95% CI -0.278 to 0.096). The estimate is directionally consistent with a weaker shock-food-insecurity association among remittance-receiving households, but the confidence interval includes zero. Kyrgyzstan is therefore classified as directional but imprecise.

### Kyrgyzstan robustness

Phase 7 confirmed that Kyrgyzstan remains directional but imprecise. Household-clustered inference, robust inference, household sensitivity, and cluster influence checks did not justify replacing the frozen primary model.

### Uzbekistan broad-shock preferred model

The preferred Uzbekistan broad-shock interaction estimate was -0.5406 (95% CI -1.0415 to -0.0398; p=0.03437), based on 47,135 household-rounds from 2,000 households. The joint remittance-plus-verified-shock group contains 42 observations from 38 households. The standardized interaction was -0.337 (95% CI -0.649 to -0.025). The evidence is classified as a moderate conditional association, not a causal result.

### Uzbekistan adjusted predictions

The model-adjusted predictions imply a shock-associated difference of 0.554 among non-remittance households and 0.013 among remittance-receiving households. This contrast is consistent with a weaker shock-food-insecurity association among remittance-receiving households.

### Uzbekistan household fixed effects

The household fixed-effects interaction remained negative but was smaller and imprecisely estimated: -0.1771 (95% CI -0.5515 to 0.1973; p=0.3539). This qualification is important because it suggests that time-invariant household characteristics may account for part of the pooled adjusted association.

### Uzbekistan temporal and participation sensitivity

Round-sensitive inference was consistent. Lagged exposure sensitivity was directionally consistent. Participation sensitivity was generally stable. Complete-case weighting was not implemented because the assumptions for an inverse-probability complete-case model were insufficient.

### Uzbekistan work-loss exploratory model

The work-loss-only model remains a secondary event-specific exploratory result. Its joint cell contains only 10 household-round observations from nine households, so it is not the headline Uzbekistan result.

### Standardized cross-country comparison

The standardized interaction estimates are negative in both country-specific analyses. Kyrgyzstan is -0.091 (95% CI -0.278 to 0.096), while Uzbekistan is -0.337 (95% CI -0.649 to -0.025). These are not formally comparable magnitudes because shock definitions, recall periods, observation units, and survey designs differ.

[Figure 4 about here]

### Kazakhstan benchmark

Kazakhstan contributes annual weighted benchmark estimates and demographic context. The results are described as weighted means of supplied moderate-or-severe and severe probability variables, not official national prevalence estimates. Kazakhstan is not included in the remittance-shock conclusions.

[Figure 5 about here]

## Discussion

The findings point in a consistent negative direction across the two main countries, but the strength of evidence differs. Kyrgyzstan shows a negative interaction that is compatible with a buffering pattern, but the estimate is imprecise. Uzbekistan shows a clearer preferred-model association for the broad verified shock measure, but the household fixed-effects estimate is smaller and imprecise.

For Kyrgyzstan, the evidence should be read as suggestive rather than confirmatory. The adult-level outcome, absence of approved survey weights, and 12-month recall period shape interpretation. For Uzbekistan, the preferred model is more precise, and robustness checks support the direction, but the joint exposure cell remains modest, estimates are unweighted, and fixed effects attenuate the association.

The findings are consistent with the idea that remittances may help households smooth food access when shocks occur. That interpretation aligns with conceptual literature on remittances and consumption smoothing, but alternative explanations remain plausible. Migrant-sending households may differ systematically from other households, and remittance flows may respond to shocks rather than precede them.

The cross-country synthesis is directional only. The study does not claim that the Uzbekistan interaction is larger than the Kyrgyzstan interaction, and it does not treat the two surveys as measuring an identical estimand. The evidence is best read as two country-specific association analyses that point toward a similar moderating pattern with different precision.

## Policy implications

### What the study directly shows

The models show country-specific associations between household shocks, remittance receipt, and food-insecurity scores.

### What the findings may suggest

The results may suggest that remittance-receiving households are less exposed to the food-insecurity consequences associated with verified shocks, especially in Uzbekistan's broad-shock model.

### What requires policy evaluation

Shock-responsive cash assistance, food assistance, lower-cost remittance channels, emergency savings products, social insurance, rural climate-risk programmes, and food-security monitoring should be evaluated prospectively or quasi-experimentally. Remittances should not be treated as a replacement for public social protection.

## Limitations

The study is observational. Selection into migration and remittance receipt may bias associations, and reverse causality is possible if adverse conditions trigger transfers. Residual time-varying confounding remains a concern, especially because Uzbekistan fixed effects attenuate the preferred estimate. L2CU estimates are unweighted because `popw` documentation is insufficient, and no approved LiK survey weight is used. Recall periods differ: 12 months in Kyrgyzstan and 30 days in Uzbekistan. Observation units also differ: adult respondents in Kyrgyzstan and household-rounds in Uzbekistan. Shock definitions are not identical, and the Uzbekistan remittance-plus-broad-shock group is modest. The work-loss-specific subgroup is very sparse. Complete-case analysis may introduce selection. Kazakhstan lacks the mechanism variables and is benchmark context only.

## Conclusion

The interaction estimates are negative in both country-specific analyses. Kyrgyzstan provides directional but imprecise evidence. Uzbekistan's revised broad-shock model provides a clearer moderate conditional association, though household fixed effects attenuate the estimate and reduce confidence in a purely within-household interpretation. These findings are observational. Remittances may be one component of household resilience, but they cannot substitute for public social protection. Better harmonized, causally informative data are needed to test mechanisms more directly.

## Extended manuscript notes for supervisor review

This first manuscript draft intentionally preserves the project’s staged evidence hierarchy. The empirical contribution rests on a narrow and transparent question: whether the association between shocks and food insecurity is weaker among remittance-receiving households. That framing matters because the available data do not randomly assign remittance receipt, migration, or shock exposure. The estimates therefore speak to conditional relationships in observed survey data. They do not establish that remittances generated the observed differences, nor do they show that policies designed around remittance channels would necessarily reduce food insecurity.

The Kyrgyzstan analysis is informative because it links adult food-insecurity responses to household-level remittance and shock measures in the Life in Kyrgyzstan Study. The preferred estimate is negative, which is the hypothesized direction, but the interval is wide. This means the data are compatible with a meaningful buffering pattern, a small relationship, or little relationship. In manuscript language, the Kyrgyzstan finding should therefore be described as directional and imprecise. It should not be promoted as confirmatory evidence. The adjusted predictions are still useful because they show how the model organizes the four remittance-shock groups, but they should be read as model-based summaries rather than direct estimates of household protection.

The Uzbekistan analysis provides stronger preferred-model evidence, but it also requires more qualification. The broad verified-shock measure was selected after the work-loss-only interaction cell was shown to be too sparse for a primary result. That revision improved empirical support for the joint exposure group: the remittance-plus-broad-shock cell contains 42 household-rounds from 38 households. This clears the project’s adequacy rule, but it remains modest. The preferred broad-shock interaction is negative and its confidence interval excludes zero. However, household fixed effects reduce the magnitude and widen the uncertainty interval. That attenuation is substantively important. It suggests that part of the pooled adjusted association may reflect stable differences between households rather than within-household changes alone.

The work-loss-only result should remain visible because it is part of the project history and because it helps explain why the broad-shock revision was necessary. The correct treatment is not to delete or bury the result, but to label it as a secondary event-specific exploratory analysis. A sparse result can be useful for hypothesis generation, especially when its direction aligns with broader models, but it cannot carry the headline Uzbekistan claim. The appendix should present it with the 10-observation and nine-household warning in the table title or note.

Cross-country synthesis should remain restrained. The standardized interactions are negative in both countries, and this directional consistency is a meaningful pattern. Still, the estimates do not share a common estimand. Kyrgyzstan uses adult respondent outcomes, a 12-month food-insecurity reference period, and a broad household shock measure. Uzbekistan uses household-round outcomes, a 30-day food-insecurity reference period, and a broad shock measure restricted to work loss and major health, injury, or death events. The surveys also differ in structure: one is essentially cross-sectional for the analysis, while the other is a repeated household panel. For these reasons, the manuscript should not rank countries or test whether the Uzbekistan interaction is larger than the Kyrgyzstan interaction.

Kazakhstan should be used sparingly and clearly. Its value is regional context: annual food-insecurity benchmarks, demographic profiles, and a reminder that food-security vulnerability varies across Central Asia. Because Kazakhstan does not contain the verified remittance and shock variables used in the main models, it cannot test the mechanism. The safest phrasing is to refer to weighted means of supplied probability variables, not official national prevalence estimates, unless additional technical documentation is later verified.

The literature review remains incomplete in one important respect. Verified sources support the survey context, FIES interpretation, Kyrgyzstan remittance-spending work, and broader remittance-as-insurance ideas. The main unresolved gap is Uzbekistan-specific peer-reviewed evidence linking remittances, household shocks, and food insecurity. The manuscript draft keeps that gap visible rather than substituting generic claims. Before journal submission, the supervisor should decide whether to conduct a targeted literature update or retain a transparent citation-gap note.

The policy implications should be written as implications for evaluation and monitoring, not as prescriptions already validated by this study. The results can motivate interest in shock-responsive social protection, remittance access, savings products, and food-security monitoring. They cannot show that any policy would work. The cleanest framing is that remittance-receiving households may have different food-security trajectories when shocks occur, and public systems should account for both remittance access and remittance absence when identifying vulnerable households.


## Extended manuscript development for supervisor review

### Motivation and scope

The manuscript is organized around a deliberately narrow question: whether the observed relationship between household shocks and food insecurity is weaker among households that receive remittances. This is narrower than asking whether migration raises welfare, whether remittances reduce poverty, or whether remittance-receiving households are generally more resilient. Those broader questions would require different designs, stronger assumptions, and additional attention to selection into migration. The present draft instead treats remittance receipt as a conditioning household characteristic and asks whether the shock gradient in food insecurity differs across remittance status.

This narrow framing matches both the data and the policy problem. Households experience shocks at irregular intervals, and food insecurity can respond quickly when employment, health, or household resources deteriorate. Remittances, when present, may be part of the household resource envelope at the time hardship occurs. The empirical task is therefore to compare the food-insecurity difference associated with shock exposure among households with and without remittance receipt. The interaction term gives a compact summary, but the manuscript emphasizes adjusted predictions and contrasts because they are easier to interpret on the raw food-insecurity scale.

The analysis also respects the fact that Kyrgyzstan and Uzbekistan are not interchangeable survey settings. The Life in Kyrgyzstan Study and Listening to the Citizens of Uzbekistan differ in unit of observation, field period, food-insecurity reference period, and shock detail. Combining records across the two countries would create a larger file, but it would also conceal design differences that are central to interpretation. The paper therefore uses parallel country-specific models and then synthesizes the direction, precision, and robustness of the results.

Kazakhstan has a different role. The Kazakhstan FIES data provide regional food-insecurity and demographic context, but they do not contain the remittance and household-shock variables required for the mechanism tested in Kyrgyzstan and Uzbekistan. The manuscript therefore describes Kazakhstan as benchmark context only. This avoids overstating the geographic scope of the empirical interaction design while still making use of the available regional information in a transparent way.

The title retains the word "buffer" because it communicates the substantive idea of a weaker adverse shock association among remittance-receiving households. Throughout the manuscript, however, the text interprets buffering as an observational moderation pattern, not as demonstrated household protection. This distinction matters. It allows the paper to speak to resilience debates while keeping the inferential burden aligned with the available data.

The supervisor-review version is written as a complete manuscript draft rather than as a short results note. Some items remain intentionally bracketed because they require author decisions outside the data workflow, including affiliations, funding, ethics wording, and target-journal formatting. Those decisions should be made after the supervisor has reviewed the empirical framing and the balance between main findings, caveats, and contribution claims.

### Regional and empirical context

Migration and remittances are central to household livelihoods in parts of Central Asia. Remittance flows may support consumption, debt repayment, housing investment, education spending, and informal insurance within extended family networks. At the same time, migration is not available to all households on equal terms. It may require up-front resources, social networks, legal or logistical access, and household arrangements that permit one or more members to work elsewhere. These conditions mean that remittance receipt is both a potential resource and a marker of underlying household differences.

Food insecurity is a particularly relevant outcome because it is sensitive to short-run resource constraints. A household that loses work, faces illness, or experiences another serious event may need to adjust food quantity, food quality, or meal patterns. Food-insecurity experience items capture these adjustments as reported by respondents. The raw score is not a monetary welfare measure, but it gives a direct view of food-related hardship. For the purposes of this study, the raw score is also useful because it can be linked to remittance receipt, shock indicators, and household characteristics.

The Kyrgyzstan and Uzbekistan surveys capture food insecurity over different reference periods, which shapes interpretation. The Kyrgyzstan measure refers to a 12-month period, while the Uzbekistan measure refers to a 30-day period. A 12-month window may capture a broader accumulation of hardship experiences but can be less tightly tied to the timing of a specific household shock. A 30-day window may be closer to recent household conditions, but it may miss earlier episodes. The manuscript therefore avoids direct claims that one country has a higher or lower comparable level of food insecurity on the same metric.

The shock variables also differ. Kyrgyzstan has a verified household shock measure that can be connected to broader categories, while Uzbekistan's revised broad-shock measure includes household work loss, major illness, major injury, and death. The Uzbekistan revision intentionally excludes service disruption from the primary shock measure because that item does not provide a defensible household shock exposure for the main interaction. This conservative coding makes the primary Uzbekistan exposure narrower but more interpretable.

The Uzbekistan work-loss result is handled separately because the remittance-plus-work-loss cell is extremely small. The sparse joint cell makes a single coefficient vulnerable to a few household clusters. The broader verified-shock measure increases the usable shock variation and aligns better with the household hardship concept. The work-loss result remains informative as event-specific exploratory evidence, but it is not allowed to carry the main Uzbekistan conclusion.

The literature base for the paper is adequate for the general framing but incomplete for some country-specific claims. Verified sources support the relevance of remittances, food-security monitoring, the Life in Kyrgyzstan Study, and the general informal-insurance interpretation. The most visible gap is the need for stronger Uzbekistan-specific peer-reviewed evidence connecting remittances, household shocks, and food insecurity. The manuscript flags this gap directly rather than filling it with unsupported generalizations.

### Data construction and sample interpretation

The Kyrgyzstan analytical sample consists of adult respondents nested within households. This matters because household-level remittance and shock measures are linked to adult-level food-insecurity reports. Multiple adults in the same household may share household exposures but report food-insecurity experiences individually. The preferred Kyrgyzstan specification therefore clusters standard errors at the household level. This keeps the precision statement aligned with the household-level exposure structure.

The Uzbekistan analytical sample consists of repeated household-round observations. Household-rounds are the relevant unit because L2CU repeatedly observes households over rounds 49-82 and measures the food-insecurity outcome at the household-round level. The preferred model includes round fixed effects and clusters standard errors by household. This design uses within-period comparisons after accounting for round-specific shifts, while the clustering recognizes repeated household observations.

Survey weights are handled conservatively. Kyrgyzstan has no approved survey weight for the analysis, and Uzbekistan's `popw` variable is not approved because documentation remains insufficient for the current empirical design. The main Uzbekistan estimates are therefore unweighted. This is a limitation, not a technical footnote. The manuscript states the unweighted status wherever model notes or interpretive statements could otherwise be read as population-level estimates.

The Kazakhstan benchmark is weighted using year-specific original weights supplied with the FIES benchmark files. The Kazakhstan estimates are described as weighted means of supplied moderate-or-severe and severe probability variables, not official calibrated national prevalence estimates. This language is intentionally precise. It allows Kazakhstan to provide regional context without implying that the project recalibrated official food-insecurity metrics or tested the same remittance-shock mechanism.

The analytical samples also differ in period and outcome reference window. Kyrgyzstan uses the 2019 LiK food-insecurity questions; Uzbekistan uses L2CU rounds 49-82. The project does not claim that the two surveys describe identical moments in time. Instead, the comparison is conceptual: in each country, does the observed shock-food-insecurity association look weaker among remittance-receiving households? The country-specific designs make that comparison possible without treating survey records as if they came from a common integrated survey.

Complete-case restrictions and eligibility decisions are carried through the manuscript as part of the empirical design. The goal is not to maximize the number of records at any cost. The goal is to preserve verified measures of remittance receipt, shock exposure, food insecurity, and core controls. When variables have unresolved coding or documentation problems, they are excluded from the primary model and noted for possible future work.

### Measurement choices and interpretation

The dependent variable is a raw count of affirmative food-insecurity experiences. Because the score runs from 0 to 8, the linear model is an approximation. It is useful because the interaction, contrasts, and adjusted predictions are transparent, and because household-clustered standard errors are straightforward. The manuscript supplements the linear specification with bounded-outcome robustness checks and explicitly avoids interpreting the nonlinear interaction coefficient alone.

The food-insecurity raw score should be read as an index of reported hardship experiences, not as an official calibrated measure. This is especially important for cross-country discussion. Differences in language, implementation, reference period, and survey design can affect item responses. The manuscript therefore focuses on within-country associations and treats cross-country synthesis as a comparison of pattern and robustness rather than a direct comparison of levels.

Remittance receipt is the primary remittance measure because it is the most consistently defensible indicator across the two main countries. Remittance amounts are substantively attractive, but amount variables can involve currency, timing, source, and missingness issues that are not resolved for the primary design. Receipt also aligns with the central question: whether households with remittance inflows show a different shock-food-insecurity association.

The remittance indicator should not be interpreted as an exogenous treatment. It reflects migration history, household networks, labor-market opportunities, household composition, and potentially the household's prior vulnerability. A household receiving remittances may differ from a non-receiving household in ways that are only partly observed. For that reason, the manuscript uses the language of association and moderation throughout.

Shock exposure is also a measured household condition rather than a randomized event. Some shocks may be more likely among households with particular age structures, health profiles, employment arrangements, or economic positions. Controls and fixed effects can reduce some forms of confounding, but they do not eliminate all concerns. The analysis therefore treats the shock coefficient and interaction as descriptive conditional associations.

The interaction term is the central parameter, but it is not self-explanatory on its own. The manuscript reports the four relevant contrasts: the shock association without remittances, the shock association with remittances, the remittance association without shock, and the remittance association with shock. These contrasts allow readers to see the full moderation pattern rather than relying only on the sign and p-value of the product term.

### Empirical strategy in greater detail

The preferred country-specific regression relates food-insecurity raw scores to remittance receipt, shock exposure, their interaction, verified controls, and appropriate fixed effects. In Kyrgyzstan, the fixed components include residence and region structure, while standard errors are clustered by household. In Uzbekistan, round fixed effects absorb common round-level shifts and household-clustered standard errors account for repeated observations within households.

The interaction coefficient can be interpreted as a difference in differences on the raw-score scale within each country-specific model. It asks whether the shock-associated difference in food-insecurity scores is smaller among remittance recipients than among non-recipients. Because higher scores mean worse food insecurity, a negative interaction is compatible with a weaker adverse shock association among remittance-receiving households.

Adjusted predictions translate the model into four group means after standardizing over the observed covariate distribution. These predictions are central to the manuscript because they show the substantive pattern on the outcome scale. For example, in Uzbekistan, the no-remittance shock contrast is large, while the remittance-plus-shock prediction is much closer to the remittance/no-shock prediction. That pattern is easier to communicate than the coefficient alone.

The models are not designed to recover all household dynamics. A shock may affect remittance receipt, remittance timing, household composition, labor supply, coping strategies, and reporting. Some of these pathways may unfold over time. The current design captures the conditional association available in the survey structure and then tests whether the pattern remains similar across robustness checks.

Household fixed effects are especially important for Uzbekistan because the L2CU panel structure allows a within-household check. The household fixed-effects estimate remains negative but is much smaller and statistically imprecise. This does not erase the preferred broad-shock pattern, but it does qualify the interpretation. It suggests that part of the cross-sectional association may reflect stable household differences, limited within-household switching, or both.

The sparse-cell diagnostics matter because interaction estimates can be sensitive when the remittance-plus-shock group is small. The Uzbekistan broad-shock joint cell includes 42 household-rounds from 38 households, while the work-loss-only joint cell includes only 10 household-rounds from nine households. The manuscript uses the broad-shock model as the primary Uzbekistan result and explicitly labels the work-loss-only result as exploratory.

### Main empirical findings in context

Kyrgyzstan shows a negative interaction estimate in the preferred model, but the confidence interval crosses zero. The adjusted predictions show that among non-remittance observations the predicted food-insecurity score is higher with shock exposure, while among remittance observations the predicted score is similar or lower in the shock group. This is directionally consistent with buffering, but the imprecision means the result should be described cautiously.

The Kyrgyzstan interpretation is therefore not that remittances clearly moderate shocks. The better phrasing is that the preferred estimate points in the expected direction but is not precise enough to rule out no moderation. This distinction is important for supervisor review because it keeps the paper from overstating a result that is suggestive but not conclusive. Kyrgyzstan contributes meaningful evidence through direction and design, not through statistical precision.

Uzbekistan provides the stronger primary pattern. The revised broad-shock interaction estimate is -0.5406 with a 95% confidence interval from -1.0415 to -0.0398 and a p-value of 0.03437. The corresponding standardized estimate is -0.337 with a 95% confidence interval from -0.649 to -0.025. The adjusted predictions show a high predicted food-insecurity score for non-remittance households with a verified shock and a much lower prediction for the remittance-plus-shock group.

The Uzbekistan result is still qualified. The broad-shock joint cell is small, L2CU estimates are unweighted, and the household fixed-effects model attenuates the interaction to -0.1771 with a 95% confidence interval from -0.5515 to 0.1973 and a p-value of 0.3539. The manuscript therefore describes the Uzbekistan evidence as a moderate conditional association with fixed-effects qualification. That phrase is intentionally calibrated: it recognizes the primary result while acknowledging the within-household sensitivity.

The Uzbekistan fixed-effects result is not framed as the single definitive result. Fixed effects answer a different question by relying more heavily on within-household changes over observed rounds. If few households switch remittance or shock status, the estimate can become imprecise even when the pooled pattern is informative. The manuscript therefore uses fixed effects as a robustness qualification rather than replacing the frozen primary model.

The work-loss-only Uzbekistan result is separated from the broad-shock finding because the joint cell is too rare for a stable primary claim. This distinction strengthens the paper. It allows the manuscript to preserve event-specific information while preventing a fragile sparse-cell coefficient from driving the main conclusion. The supervisor can decide whether to leave the work-loss result in the appendix, summarize it briefly in the main text, or remove it from the manuscript.

### Cross-country synthesis

The cross-country synthesis is based on direction, scale, precision, and robustness rather than pooled estimation. Both countries show negative preferred interaction estimates. That directional consistency is substantively interesting because the surveys differ in design and measurement. At the same time, only the Uzbekistan broad-shock preferred estimate is statistically distinguishable from zero at conventional levels, while Kyrgyzstan is imprecise. The paper should therefore avoid any sentence suggesting that both countries show strong or equally precise evidence.

The most defensible synthesis is that the evidence is compatible with remittances moderating the relationship between shocks and food insecurity, with stronger support in Uzbekistan than Kyrgyzstan. The phrase "compatible with" is useful because it communicates that the pattern matches the conceptual expectation without implying that the study demonstrates a causal pathway. The phrase also leaves room for selection, measurement differences, and unobserved household characteristics.

The Kyrgyzstan and Uzbekistan results may differ for several reasons. The outcome reference period differs, the unit of observation differs, and the shock measures differ. The migration-remittance environment may also differ across countries and survey periods. These differences are not necessarily a weakness. They clarify why a two-country design should be interpreted as a set of parallel tests rather than as a single pooled regional estimate.

The Kazakhstan benchmark provides a regional backdrop but does not change the empirical interpretation. It can help readers understand that food insecurity is a regional policy concern and that the paper sits within a broader Central Asian context. It cannot support claims about remittance moderation because the required mechanism variables are absent. The manuscript keeps that boundary visible in the data section, results section, and conclusion.

### Robustness, uncertainty, and reviewer-facing caveats

The manuscript should anticipate reviewer concerns about endogeneity. Remittance receipt is not random, and households receiving transfers may differ systematically from those that do not. The current design adjusts for verified covariates and uses country-specific fixed structures, but it cannot rule out unobserved selection. The paper should therefore present the findings as conditional associations and avoid phrasing that implies an intervention result.

Another likely reviewer concern is timing. If remittances arrive after a shock in response to distress, then remittance receipt may be partly reactive. In that situation, the interaction may reflect household support networks activated by hardship rather than a pre-existing buffer. The survey data do not fully resolve this ordering. This uncertainty does not make the descriptive pattern irrelevant, but it limits how strongly the mechanism can be stated.

Measurement comparability is also central. The raw FIES-style scores are useful within each country, but their reference periods and implementation contexts differ. The manuscript should avoid saying that one country has more food insecurity than the other based on raw-score comparisons. It can say that within each country, the modeled shock-remittance pattern is evaluated on that country's verified outcome scale.

The L2CU weighting decision should remain visible. Unweighted estimates are appropriate given the unresolved `popw` documentation, but they limit population interpretation. The manuscript should not describe the Uzbekistan estimates as representative population parameters. A future revision could revisit weighting if documentation becomes sufficient, but the frozen Phase 8 draft should not add weights or imply that weighting has been approved.

Rare-cell sensitivity is another important qualification. The Uzbekistan broad-shock joint group is not as sparse as the work-loss-only joint group, but it is still small relative to the full household-round sample. The influence checks reduce concern that one household fully determines the result, yet the manuscript should describe the rare-cell structure transparently. This builds trust and helps readers understand why the fixed-effects qualification matters.

The bounded-outcome robustness models provide a useful check because the raw score is bounded between 0 and 8. These models should be interpreted through standardized four-group predictions, not through the raw nonlinear interaction coefficient alone. The manuscript includes this rule because nonlinear interaction terms can be misleading when read without contrasts or predictions on the outcome scale.

### Policy interpretation

The paper has policy relevance but should not make program-evaluation claims. The findings suggest that households receiving remittances may show a weaker shock-food-insecurity association, especially in the Uzbekistan broad-shock specification. This is relevant for shock-responsive social protection because it points to heterogeneity in household vulnerability and private support networks. However, it does not show that remittance promotion would reduce food insecurity or that public transfers can be replaced by private transfers.

A careful policy implication is that social-protection systems should consider both shocks and household support networks when identifying vulnerability. Households without remittance support may face larger food-insecurity increases after verified shocks in the observed Uzbekistan data. That pattern, if corroborated, could motivate attention to households lacking external support when designing shock-responsive outreach or temporary assistance.

Another implication is that remittance-receiving households should not automatically be classified as secure. Remittance receipt may reduce some observed shock-associated hardship, but remittance households can still experience food insecurity. They may also face risks tied to migrant labor markets, exchange rates, transfer costs, and family obligations. The manuscript should therefore present remittances as one element in household resilience, not as a substitute for formal protection.

The Kyrgyzstan result supports cautious language. Because the estimate is negative but imprecise, the policy discussion should not treat Kyrgyzstan as confirming the same pattern as Uzbekistan. Instead, it can say that the Kyrgyzstan evidence points in a similar direction and justifies further work with richer timing, weights, or alternative shock definitions if available. That is a measured contribution rather than a weak claim dressed as certainty.

For Uzbekistan, the fixed-effects qualification should be mentioned wherever the main result is summarized. A reader should not reach the conclusion with only the broad-shock estimate in mind. The more balanced statement is that the broad-shock model shows a moderate negative interaction, but within-household evidence is negative and imprecise. This is the core interpretation that should be carried into Phase 9 or journal preparation.

Kazakhstan should be used sparingly in the policy section. It can be described as showing why regional benchmarking is useful, but it cannot support a statement about remittances and shocks. If Kazakhstan microdata with remittance and shock measures become available later, the benchmark plan can be revisited. Until then, Kazakhstan remains outside the main regression design.

### Contribution and manuscript positioning

The paper contributes by bringing a transparent interaction design to two Central Asian household datasets and by being explicit about what the data can and cannot support. A common risk in resilience research is to slide from suggestive associations into strong claims about household capacity. This manuscript resists that move. Its value is partly empirical and partly procedural: it shows a careful way to handle heterogeneous surveys, sparse interaction cells, and incomplete regional coverage.

The country-specific design is a strength because it preserves the structure of each dataset. Instead of forcing LiK and L2CU into a single harmonized file, the paper asks the same conceptual question separately. This makes the results less tidy but more honest. Readers can see that the Uzbekistan evidence is stronger in the primary model, while Kyrgyzstan is directionally aligned but imprecise.

The paper also contributes by distinguishing primary, secondary, and benchmark evidence. The Kyrgyzstan and Uzbekistan broad-shock models are the main empirical tests. The Uzbekistan work-loss result is secondary and exploratory. Kazakhstan is benchmark context. This hierarchy keeps the manuscript from drifting into overclaiming and gives supervisors and reviewers a clear map of which evidence supports which statement.

Another contribution is the emphasis on interaction contrasts. Many empirical papers report interaction coefficients without showing what they imply for the four underlying groups. This manuscript reports both the coefficient and the adjusted predictions. That choice makes the substantive pattern visible: how food-insecurity scores differ by shock status among remittance and non-remittance households, and how remittance status is associated with food insecurity within shock groups.

The manuscript is not positioned as a final journal submission package. It is a supervisor-review draft. The next stage should refine the literature review, resolve citation gaps, finalize declarations, and choose a target journal. Once the supervisor confirms the empirical framing, the draft can be converted into the selected journal format and the reference list can be completed with full bibliographic metadata.

### Limitations and future research

The first limitation is observational design. The models estimate conditional associations, not causal parameters. Remittance receipt may be selected on household resources, migration networks, risk exposure, or unmeasured need. Shock exposure may also be correlated with unobserved household conditions. These issues are addressed through transparent language and robustness checks, but they are not fully resolved.

The second limitation is timing. The surveys do not fully establish whether remittances preceded shocks, followed shocks, or changed in response to shocks. This matters because the conceptual idea of a buffer can involve both pre-existing resources and reactive support. Future work with higher-frequency remittance timing or event histories could distinguish these pathways more clearly.

The third limitation is measurement comparability. Kyrgyzstan and Uzbekistan use different survey instruments and reference periods. The paper therefore avoids direct pooled estimation and level comparisons. Future work could examine whether more harmonized food-insecurity timing or comparable shock modules change the cross-country synthesis.

The fourth limitation is weighting. The L2CU primary estimates are unweighted because `popw` is not approved for this analysis. If documentation later supports a specific weight strategy, a future revision should compare weighted and unweighted results. Until then, the manuscript must keep the Uzbekistan interpretation at the level of the analyzed household-round sample.

The fifth limitation is sparse cells. Interaction designs require observations in all four remittance-shock groups. The Uzbekistan broad-shock joint cell is limited, and the work-loss-only joint cell is very small. The influence checks are useful, but they cannot create information that is not present in the data. Future research could pool additional rounds, use external data, or focus on more common shock categories if verified.

The sixth limitation is remittance measurement. Receipt is easier to defend than amount, but amount, frequency, source, and reliability are substantively important. A small irregular transfer may not function like a stable monthly remittance. Future work should examine remittance intensity if the currency, timing, and missing-code issues can be resolved consistently.

The seventh limitation concerns coping behavior. Food insecurity is an outcome, but households may respond to shocks through borrowing, asset sales, reduced non-food spending, changes in labor supply, or support from relatives and institutions. Some of these responses may mediate the observed association. Including them as controls in the main model could block meaningful pathways, so they are not part of the core adjustment set. Future work could model coping as a separate outcome.

The eighth limitation is external validity. The findings are specific to the analyzed surveys, periods, and verified variables. They should not be generalized to all Central Asian households or all remittance corridors without additional evidence. The manuscript's value lies in a careful two-country empirical study with a clearly bounded Kazakhstan benchmark, not in a sweeping regional claim.

### Conclusion refinement

The completed manuscript should leave readers with three points. First, the research question is empirically feasible in Kyrgyzstan and Uzbekistan when country-specific designs are used. Second, the preferred estimates point in the expected negative direction in both countries, but the strength of evidence differs: Kyrgyzstan is directional but imprecise, while Uzbekistan shows a moderate conditional association that is qualified by household fixed effects. Third, the paper is useful for resilience and social-protection discussions precisely because it states its limits.

The final interpretation should be compact. In Kyrgyzstan, remittance receipt is associated with a weaker estimated shock-food-insecurity relationship, but uncertainty is wide. In Uzbekistan, remittance receipt is associated with a substantially weaker verified-shock relationship in the broad-shock model, but the result should be read alongside the smaller and imprecise household fixed-effects estimate. Kazakhstan remains a benchmark-only setting until mechanism variables become available.

For the next phase, the main task is not new modeling. The empirical foundation is frozen for this manuscript-preparation step. The next task is supervisor review: deciding whether the current framing is sufficiently balanced, which citation gaps must be filled before submission, and which journal format should guide the conversion from Markdown into a final manuscript file.

## Declarations

[See manuscript/declarations.md]

## References

[See manuscript/references_verified.md]

## Appendix

[See manuscript/appendix_v1.md]
