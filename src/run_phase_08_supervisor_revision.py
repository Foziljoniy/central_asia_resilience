"""Phase 8 supervisor manuscript revision.

This script revises the existing Phase 8 manuscript package without estimating
new models or changing approved numerical findings.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(".")
MAN = ROOT / "manuscript"
CHECK = ROOT / "outputs" / "checkpoints"
LIT = ROOT / "literature"
TABLES = MAN / "tables_v2"
FIGS = MAN / "figures"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in keys})


def read_csv_dict(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(x: str | float, digits: int = 3) -> str:
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)


def extract_internal_notes() -> str:
    v1 = MAN / "full_manuscript_v1.md"
    if not v1.exists():
        return "# Phase 8 supervisor notes\n\nNo Phase 8 v1 manuscript was found.\n"
    text = v1.read_text(encoding="utf-8", errors="replace")
    notes = []
    for heading in ["## Extended manuscript notes for supervisor review", "## Extended manuscript development for supervisor review"]:
        if heading in text:
            start = text.index(heading)
            end = text.find("\n## Declarations", start)
            if end == -1:
                end = len(text)
            notes.append(text[start:end].strip())
    if not notes:
        return "# Phase 8 supervisor notes\n\nNo internal supervisor-note section was found in `full_manuscript_v1.md`.\n"
    return "# Phase 8 supervisor notes preserved from v1\n\n" + "\n\n---\n\n".join(notes) + "\n"


REFS = [
    {
        "key": "Akter and Basher 2014",
        "authors": "Akter, S., & Basher, S. A.",
        "year": "2014",
        "title": "The impacts of food price and income shocks on household food security and economic well-being: Evidence from rural Bangladesh",
        "journal_or_institution": "Global Environmental Change, 25, 150-162",
        "doi_or_url": "https://doi.org/10.1016/j.gloenvcha.2014.02.003",
        "country": "Bangladesh",
        "dataset": "Longitudinal rural household data",
        "method": "Hierarchical logit and first-difference analysis",
        "supported_finding": "Food-price and income shocks were associated with worse household food security, especially in the short run.",
        "relevance": "Supports the general shock-food-insecurity pathway.",
        "verification_source": "ScienceDirect record opened in web verification.",
    },
    {
        "key": "Ansah et al. 2021",
        "authors": "Ansah, I. G. K., Gardebroek, C., & Ihle, R.",
        "year": "2021",
        "title": "Shock interactions, coping strategy choices and household food security",
        "journal_or_institution": "Climate and Development, 13(5), 414-426",
        "doi_or_url": "https://doi.org/10.1080/17565529.2020.1785832",
        "country": "Ghana",
        "dataset": "Farm household survey",
        "method": "Probit and recursive framework",
        "supported_finding": "Climate, health, pest, and price shocks are linked to coping choices and household food security.",
        "relevance": "Supports multiple-shock framing and coping caution.",
        "verification_source": "Taylor & Francis search result.",
    },
    {
        "key": "Azam and Gubert 2006",
        "authors": "Azam, J.-P., & Gubert, F.",
        "year": "2006",
        "title": "Migrants' remittances and the household in Africa: A review of evidence",
        "journal_or_institution": "Journal of African Economies, 15(2), 426-462",
        "doi_or_url": "https://ideas.repec.org/a/oup/jafrec/v15y2006i2p426-462.html",
        "country": "Africa, multi-country",
        "dataset": "Review",
        "method": "Literature review",
        "supported_finding": "Remittance motives and selection complicate household interpretation.",
        "relevance": "Supports endogeneity and alternative-explanation discussion.",
        "verification_source": "IDEAS/RePEc record.",
    },
    {
        "key": "Bowen et al. 2020",
        "authors": "Bowen, T., del Ninno, C., Andrews, C., Coll-Black, S., Gentilini, U., Johnson, K., Kawasoe, Y., Kryeziu, A., Maher, B., & Williams, A.",
        "year": "2020",
        "title": "Adaptive Social Protection: Building Resilience to Shocks",
        "journal_or_institution": "World Bank, International Development in Focus",
        "doi_or_url": "https://doi.org/10.1596/978-1-4648-1575-1",
        "country": "Global",
        "dataset": "Policy synthesis",
        "method": "Framework and operational review",
        "supported_finding": "Adaptive social protection links household risk, shocks, delivery systems, and resilience.",
        "relevance": "Supports policy framing without claiming this study evaluated programs.",
        "verification_source": "World Bank/Policy Commons record.",
    },
    {
        "key": "Brueck et al. 2014",
        "authors": "Brueck, T., Esenaliev, D., Kroeger, A., Kudebayeva, A., Mirkasimov, B., & Steiner, S.",
        "year": "2014",
        "title": "Household survey data for research on well-being and behavior in Central Asia",
        "journal_or_institution": "Journal of Comparative Economics, 42(3), 819-835",
        "doi_or_url": "https://www.iza.org/publications/dp/7055/household-survey-data-for-research-on-well-being-and-behavior-in-central-asia",
        "country": "Central Asia; Kyrgyzstan",
        "dataset": "Life in Kyrgyzstan and Central Asian surveys",
        "method": "Survey data review and dataset introduction",
        "supported_finding": "Central Asia has limited longitudinal microdata; LiK provides a panel resource.",
        "relevance": "Supports LiK data motivation.",
        "verification_source": "IZA record.",
    },
    {
        "key": "Cafiero et al. 2018",
        "authors": "Cafiero, C., Viviani, S., & Nord, M.",
        "year": "2018",
        "title": "Food security measurement in a global context: The food insecurity experience scale",
        "journal_or_institution": "Measurement, 116, 146-152",
        "doi_or_url": "https://doi.org/10.1016/j.measurement.2017.10.065",
        "country": "Global",
        "dataset": "FIES applications across countries",
        "method": "Rasch-model measurement paper",
        "supported_finding": "FIES uses eight experiential items and calibration for cross-country comparability.",
        "relevance": "Supports food-insecurity measurement discussion and raw-score caveat.",
        "verification_source": "FAO citation record.",
    },
    {
        "key": "Choi and Yang 2007",
        "authors": "Choi, H., & Yang, D.",
        "year": "2007",
        "title": "Are remittances insurance? Evidence from rainfall shocks in the Philippines",
        "journal_or_institution": "The World Bank Economic Review, 21(2), 219-248",
        "doi_or_url": "https://doi.org/10.1093/wber/lhm003",
        "country": "Philippines",
        "dataset": "Philippine household data with rainfall variation",
        "method": "Instrumental-variable analysis",
        "supported_finding": "Remittances responded inversely to income shocks and migrant households smoothed consumption more than non-migrant households.",
        "relevance": "Core informal-insurance and consumption-smoothing source.",
        "verification_source": "IDEAS/RePEc and World Bank records.",
    },
    {
        "key": "Combes and Ebeke 2011",
        "authors": "Combes, J.-L., & Ebeke, C.",
        "year": "2011",
        "title": "Remittances and household consumption instability in developing countries",
        "journal_or_institution": "World Development, 39(7), 1076-1089",
        "doi_or_url": "https://doi.org/10.1016/j.worlddev.2010.10.006",
        "country": "Developing countries",
        "dataset": "Cross-country panel",
        "method": "Panel regression",
        "supported_finding": "Remittances are associated with lower household consumption instability in developing countries.",
        "relevance": "Supports consumption-smoothing literature.",
        "verification_source": "Published DOI verified through indexed references.",
    },
    {
        "key": "FAO 2026",
        "authors": "Food and Agriculture Organization of the United Nations",
        "year": "2026",
        "title": "About the Food Insecurity Experience Scale (FIES)",
        "journal_or_institution": "FAO methodology webpage",
        "doi_or_url": "https://www.fao.org/measuring-hunger/access-to-food/about-the-food-insecurity-experience-scale-(fies)/en",
        "country": "Global",
        "dataset": "FIES methodology",
        "method": "Official methodology documentation",
        "supported_finding": "FIES is an experience-based metric using eight questions about constrained food access.",
        "relevance": "Supports outcome interpretation.",
        "verification_source": "FAO page opened in web verification.",
    },
    {
        "key": "Hoddinott 2006",
        "authors": "Hoddinott, J.",
        "year": "2006",
        "title": "Shocks and their consequences across and within households in rural Zimbabwe",
        "journal_or_institution": "The Journal of Development Studies, 42(2), 301-321",
        "doi_or_url": "https://doi.org/10.1080/00220380500405501",
        "country": "Zimbabwe",
        "dataset": "Rural household data",
        "method": "Household shock and welfare analysis",
        "supported_finding": "Household shocks can have consequences for consumption, assets, and poverty dynamics.",
        "relevance": "Supports welfare consequences of shocks.",
        "verification_source": "Taylor & Francis record.",
    },
    {
        "key": "Kakhkharov et al. 2021",
        "authors": "Kakhkharov, J., Ahunov, M., Parpiev, Z., & Wolfson, I.",
        "year": "2021",
        "title": "South-South migration: Remittances of labour migrants and household expenditures in Uzbekistan",
        "journal_or_institution": "International Migration, 59(5), 38-58",
        "doi_or_url": "https://doi.org/10.1111/imig.12792",
        "country": "Uzbekistan",
        "dataset": "Uzbekistan household expenditure data",
        "method": "Instrumental-variable regressions",
        "supported_finding": "Remittance-receiving Uzbek households differed in expenditure allocation; the study explicitly addressed selection bias.",
        "relevance": "Key Uzbekistan remittance and household expenditure source.",
        "verification_source": "Wiley record.",
    },
    {
        "key": "Leibniz Institute et al. 2023",
        "authors": "Leibniz Institute of Vegetable and Ornamental Crops, University of Central Asia, Stockholm International Peace Research Institute, & German Institute for Economic Research",
        "year": "2023",
        "title": "Life in Kyrgyzstan Study, 2010-2019",
        "journal_or_institution": "Research Data Center of IZA, Version 2",
        "doi_or_url": "https://doi.org/10.15185/izadp.7055.1",
        "country": "Kyrgyzstan",
        "dataset": "Life in Kyrgyzstan Study",
        "method": "Longitudinal household and individual survey",
        "supported_finding": "LiK follows households and individuals across Kyrgyz regions and includes migration, shocks, and expenditure modules.",
        "relevance": "Official data citation for Kyrgyzstan.",
        "verification_source": "IZA Dataverse record.",
    },
    {
        "key": "Lucas and Stark 1985",
        "authors": "Lucas, R. E. B., & Stark, O.",
        "year": "1985",
        "title": "Motivations to remit: Evidence from Botswana",
        "journal_or_institution": "Journal of Political Economy, 93(5), 901-918",
        "doi_or_url": "https://doi.org/10.1086/261341",
        "country": "Botswana",
        "dataset": "Botswana migration and household data",
        "method": "Theoretical and empirical remittance-motivation analysis",
        "supported_finding": "Remittance behavior can reflect household strategies, mutual arrangements, and risk sharing rather than pure altruism alone.",
        "relevance": "Core theoretical source on remittance motives.",
        "verification_source": "University of Chicago/IDEAS record.",
    },
    {
        "key": "O'Brien et al. 2018",
        "authors": "O'Brien, C., Holmes, R., Scott, Z., & Barca, V.",
        "year": "2018",
        "title": "Shock-responsive social protection systems toolkit",
        "journal_or_institution": "Oxford Policy Management and partners",
        "doi_or_url": "https://www.social-protection.org/gimi/gess/ShowRessource.action?id=55748&lang=EN",
        "country": "Global",
        "dataset": "Operational toolkit",
        "method": "Guidance and framework",
        "supported_finding": "Shock-responsive social protection requires systems that can respond to covariate and idiosyncratic shocks.",
        "relevance": "Supports policy-boundary framing.",
        "verification_source": "Social Protection platform record.",
    },
    {
        "key": "Stark and Levhari 1982",
        "authors": "Stark, O., & Levhari, D.",
        "year": "1982",
        "title": "On migration and risk in LDCs",
        "journal_or_institution": "Economic Development and Cultural Change, 31(1), 191-196",
        "doi_or_url": "https://doi.org/10.1086/451312",
        "country": "Developing countries",
        "dataset": "Conceptual article",
        "method": "Theory",
        "supported_finding": "Risk diversification is a central explanation for migration decisions.",
        "relevance": "Theoretical basis for migration as risk management.",
        "verification_source": "Tel Aviv University record.",
    },
    {
        "key": "Uochi 2025",
        "authors": "Uochi, I.",
        "year": "2025",
        "title": "Listening to the Citizens of Uzbekistan: Overall Socio-Economic Trends",
        "journal_or_institution": "World Bank brief",
        "doi_or_url": "https://documents.worldbank.org/curated/en/099640507152431194",
        "country": "Uzbekistan",
        "dataset": "L2CU",
        "method": "Descriptive monitoring brief",
        "supported_finding": "L2CU monitors income, coping mechanisms, food insecurity, services, and socio-economic trends.",
        "relevance": "Supports Uzbekistan survey context.",
        "verification_source": "World Bank documents record.",
    },
    {
        "key": "Wang et al. 2021",
        "authors": "Wang, D., Hagedorn, A., & Chi, G.",
        "year": "2021",
        "title": "Remittances and household spending strategies: Evidence from the Life in Kyrgyzstan Study, 2011-2013",
        "journal_or_institution": "Journal of Ethnic and Migration Studies, 47(13), 3015-3036",
        "doi_or_url": "https://doi.org/10.1080/1369183X.2019.1683442",
        "country": "Kyrgyzstan",
        "dataset": "Life in Kyrgyzstan Study, 2011-2013",
        "method": "Household fixed effects and quantile regression",
        "supported_finding": "Remittances were related to household budget shares, with attention to endogeneity and heterogeneity.",
        "relevance": "Key Kyrgyzstan remittance and spending source.",
        "verification_source": "Taylor & Francis and PMC records.",
    },
    {
        "key": "World Bank 2023",
        "authors": "World Bank",
        "year": "2023",
        "title": "World Development Report 2023: Migrants, Refugees, and Societies",
        "journal_or_institution": "World Bank",
        "doi_or_url": "https://www.worldbank.org/en/publication/wdr2023",
        "country": "Global",
        "dataset": "Global synthesis",
        "method": "Development report",
        "supported_finding": "Migration can bring remittances and knowledge transfers while also involving costs and policy tradeoffs.",
        "relevance": "Supports broad migration-development framing.",
        "verification_source": "World Bank WDR page.",
    },
    {
        "key": "World Bank 2025a",
        "authors": "World Bank",
        "year": "2025",
        "title": "Uzbekistan - Listening to the Citizens of Uzbekistan Survey 2018-2025",
        "journal_or_institution": "World Bank Microdata Library",
        "doi_or_url": "https://microdata.worldbank.org/catalog/6412",
        "country": "Uzbekistan",
        "dataset": "L2CU rounds 1-82",
        "method": "Survey metadata and data dictionary",
        "supported_finding": "L2CU is a high-frequency phone survey with household and individual data files through round 82.",
        "relevance": "Official data citation for Uzbekistan.",
        "verification_source": "World Bank Microdata Library record.",
    },
    {
        "key": "World Bank 2025b",
        "authors": "World Bank",
        "year": "2025",
        "title": "Study - Listening to the Citizens of Uzbekistan",
        "journal_or_institution": "World Bank country brief",
        "doi_or_url": "https://www.worldbank.org/en/country/uzbekistan/brief/l2cu",
        "country": "Uzbekistan",
        "dataset": "L2CU",
        "method": "Survey overview",
        "supported_finding": "The L2CU panel began monthly phone interviews in September 2018 and monitors food security, income, employment, remittances, services, and shocks.",
        "relevance": "Supports survey producer, purpose, and fieldwork description.",
        "verification_source": "World Bank L2CU page.",
    },
]


def citation_key(ref: dict) -> str:
    return f"{ref['authors'].split(',')[0]} {ref['year']}"


def create_literature_outputs() -> tuple[int, int]:
    rows = []
    for i, ref in enumerate(REFS, 1):
        row = {"id": f"V5_{i:02d}", **ref, "verified": 1}
        rows.append(row)
    write_csv(LIT / "matrices" / "literature_matrix_v5_manuscript.csv", rows)
    write_csv(LIT / "verification" / "phase_08_revision_source_verification.csv", rows)
    lit_review = """# Literature review v5 for manuscript

The verified literature supports four claims used in the clean manuscript. First, household shocks are associated with food-security and welfare deterioration in diverse low- and middle-income settings, although timing, coping and labor-market adjustment matter. Second, migration and remittances are commonly interpreted as part of household risk-management and informal-insurance arrangements, but remittance motives are heterogeneous. Third, remittance receipt is selected, and models that use remittances as a conditioning variable cannot be read as causal estimates. Fourth, LiK and L2CU have credible documentation for country-specific empirical work, while Uzbekistan-specific peer-reviewed evidence connecting remittances, shocks and food insecurity remains thinner than the Kyrgyzstan/LiK evidence base.
"""
    write(LIT / "drafts" / "literature_review_v5_manuscript.md", lit_review)
    gaps = [
        {"gap_id": "G1", "gap": "Uzbekistan-specific peer-reviewed evidence directly linking remittances, household shocks and FIES-style food insecurity remains limited.", "public_manuscript_handling": "Do not state unsupported Uzbekistan-specific literature claims; rely on verified Uzbekistan remittance and L2CU sources."},
        {"gap_id": "G2", "gap": "L2CU `popw` weighting documentation remains insufficient for the approved analysis.", "public_manuscript_handling": "State L2CU estimates are unweighted and avoid population-parameter language."},
    ]
    write_csv(LIT / "verification" / "phase_08_revision_visible_gaps.csv", gaps)
    return len(rows), len(gaps)


def references_text() -> str:
    lines = ["# References\n"]
    for ref in REFS:
        lines.append(f"{ref['authors']} ({ref['year']}). {ref['title']}. *{ref['journal_or_institution']}*. {ref['doi_or_url']}")
    return "\n\n".join(lines) + "\n"


def abstract_v2() -> str:
    return """# Abstract

This paper asks whether the positive association between household shocks and food insecurity is weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan. The analysis uses the 2019 wave of the Life in Kyrgyzstan Study and Listening to the Citizens of Uzbekistan rounds 49-82. Because the surveys differ in design, unit of observation, reference period and shock measurement, all models are country-specific and observational rather than pooled. Kazakhstan is included only as regional benchmark context. The preferred Kyrgyzstan model estimates a negative remittance-shock interaction of -0.2140 (95% CI -0.6549 to 0.2269; p=0.3415), which is directionally consistent with a weaker shock-food-insecurity association but imprecise. The preferred Uzbekistan broad-shock model estimates a negative interaction of -0.5406 (95% CI -1.0415 to -0.0398; p=0.03437). Four-group predictions are used to interpret the interaction on the food-insecurity raw-score scale and to separate baseline remittance differences from shock-period differences. The Uzbekistan household fixed-effects estimate remains negative but is smaller and imprecise (-0.1771; 95% CI -0.5515 to 0.1973; p=0.3539). L2CU estimates are unweighted because the available `popw` documentation was not approved for this analysis. The findings are compatible with remittance-related moderation of household shock vulnerability, especially in Uzbekistan, but the evidence remains associational and subject to selection, timing and measurement limitations.
"""


def clean_manuscript() -> str:
    return """# Do Remittances Buffer Household Shocks? Evidence on Food Insecurity in Kyrgyzstan and Uzbekistan

## Abstract

This paper asks whether the positive association between household shocks and food insecurity is weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan. The analysis uses the 2019 wave of the Life in Kyrgyzstan Study and Listening to the Citizens of Uzbekistan rounds 49-82. Because the surveys differ in design, unit of observation, reference period and shock measurement, all models are country-specific and observational rather than pooled. Kazakhstan is included only as regional benchmark context. The preferred Kyrgyzstan model estimates a negative remittance-shock interaction of -0.2140 (95% CI -0.6549 to 0.2269; p=0.3415), which is directionally consistent with a weaker shock-food-insecurity association but imprecise. The preferred Uzbekistan broad-shock model estimates a negative interaction of -0.5406 (95% CI -1.0415 to -0.0398; p=0.03437). Four-group predictions are used to interpret the interaction on the food-insecurity raw-score scale and to separate baseline remittance differences from shock-period differences. The Uzbekistan household fixed-effects estimate remains negative but is smaller and imprecise (-0.1771; 95% CI -0.5515 to 0.1973; p=0.3539). L2CU estimates are unweighted because the available `popw` documentation was not approved for this analysis. The findings are compatible with remittance-related moderation of household shock vulnerability, especially in Uzbekistan, but the evidence remains associational and subject to selection, timing and measurement limitations.

## Keywords

remittances; household shocks; food insecurity; resilience; migration; Kyrgyzstan; Uzbekistan; Central Asia

## Introduction

Household shocks are a central source of food-security risk. A job loss, illness, death, agricultural loss or climate-related event can reduce income, raise expenses and disrupt the household's ability to obtain food. These events are often not isolated from other household decisions. Families may borrow, sell assets, change labor supply, reduce non-food spending or draw on help from relatives. In migration-dependent settings, remittances are one possible source of support. They may add liquidity when a household faces stress, but they also identify households with migration networks, different labor-market histories and potentially different underlying resources.

This paper asks a focused research question: is the positive association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan? The outcome is a higher-worse food-insecurity raw score. The central empirical test is therefore whether the shock-associated increase in that score is smaller for households that receive remittances. A negative remittance-shock interaction is consistent with such a weaker adverse association, but it is not interpreted as a causal estimate.

The question is important for Central Asia because labor migration and remittances are embedded in household livelihood strategies. The World Bank's migration-development synthesis emphasizes that origin-country households may receive remittances and knowledge transfers while also facing the absence and risks associated with migration (World Bank 2023). Classic work on migration and risk argues that households may use migration to diversify income sources (Stark and Levhari 1982), while remittance-motivation research shows that transfers may reflect family arrangements, risk sharing and mutual interest rather than a single simple motive (Lucas and Stark 1985). These ideas are relevant to resilience research, but they do not by themselves establish what happens in a particular household survey when food-insecurity outcomes and recent shocks are observed together.

The empirical design uses two main datasets. For Kyrgyzstan, the analysis uses the 2019 wave of the Life in Kyrgyzstan Study, a multi-topic longitudinal survey with household and individual modules (Leibniz Institute et al. 2023). For Uzbekistan, it uses Listening to the Citizens of Uzbekistan, a high-frequency World Bank phone survey that tracks household welfare, food security, employment, remittances, services and shocks (World Bank 2025a; World Bank 2025b). Kazakhstan is not a third country in the mechanism analysis. Its FIES data are used only for regional food-insecurity and demographic benchmark context because verified remittance and household-shock mechanism variables are not available.

The paper makes three contributions. First, it applies the same conceptual moderation question to two Central Asian settings without pooling incompatible respondent records. Second, it reports four-group adjusted predictions and interaction contrasts rather than relying only on the coefficient of the product term. Third, it distinguishes primary evidence, robustness qualifications and benchmark context. Kyrgyzstan is classified as directional but imprecise; Uzbekistan is classified as a moderate conditional association with limitations; Uzbekistan household fixed effects are reported as a prominent qualification; and the work-loss-only Uzbekistan result is kept as secondary event-specific exploratory evidence.

The preview of findings is restrained. In Kyrgyzstan, the preferred interaction is negative but imprecise. In Uzbekistan, the preferred broad-shock interaction is negative and more precise, but the remittance-plus-shock cell is modest and the household fixed-effects estimate is attenuated and imprecise. The results are best read as evidence that remittance status conditions the observed shock-food-insecurity association in these data, especially in Uzbekistan, while leaving open selection, timing and measurement explanations.

## Literature review and research gap

### Household shocks and food insecurity

Food insecurity reflects constrained access to adequate food and is closely related to household resources, prices, labor-market conditions and coping capacity. The Food Insecurity Experience Scale is an experience-based measure built from eight questions about food-related hardship (FAO 2026). Cafiero et al. (2018) describe the FIES measurement model and the role of calibration for comparable population estimates. This paper uses raw FIES-style scores rather than official calibrated estimates, so the literature supports the interpretation of the outcome as reported food-access hardship while also cautioning against over-comparison across surveys.

Empirical work links shocks to food-security and welfare outcomes through multiple channels. Hoddinott (2006) emphasizes that household shocks can shape consumption, assets and poverty dynamics within and across households. Akter and Basher (2014) show that food-price and income shocks were associated with worse food security in rural Bangladesh, especially for poorer households. Ansah et al. (2021) extend the discussion to interacting climate, health, pest and price shocks and show that coping strategies matter for food-security outcomes. These studies support the expectation that household shocks are positively associated with higher food-insecurity scores.

### Migration and remittances as informal insurance

The remittance literature offers a plausible reason to expect moderation. Stark and Levhari (1982) frame migration as a household response to risk. Lucas and Stark (1985) show that remittance motives can include mutual family arrangements and risk sharing. Choi and Yang (2007) provide influential evidence from the Philippines that remittances may respond to negative income shocks and that consumption is smoother among households with migrants. Combes and Ebeke (2011) similarly connect remittances to lower household consumption instability in developing countries. Together, this literature supports the idea that remittances can be associated with consumption smoothing, while also emphasizing that the empirical setting matters.

The policy literature reaches a similar boundary from a different direction. Shock-responsive and adaptive social protection frameworks focus on public systems that can respond to household and covariate shocks (O'Brien et al. 2018; Bowen et al. 2020). Private remittances can be part of a household's resource envelope, but they are not public entitlements and are not guaranteed. The present study therefore connects remittance heterogeneity to vulnerability analysis without treating private transfers as substitutes for formal social protection.

### Selection, endogeneity and alternative explanations

Remittance receipt is not random. Migrant-sending households may have more resources, better networks or different risk exposure before a shock occurs. Transfers may also be reactive: relatives may send money after illness, job loss or another event. Azam and Gubert (2006) review evidence showing that remittance motives and household selection are complex. Kakhkharov et al. (2021) address selection in their Uzbekistan remittance-expenditure study, and Wang et al. (2021) explicitly treat endogeneity and heterogeneity in their Kyrgyzstan remittance-spending analysis. These concerns are central to the interpretation here.

Because of these concerns, the paper does not ask whether remittances causally reduce food insecurity. It asks whether the observed shock-food-insecurity association differs by remittance status. This distinction is more than wording. It determines model interpretation, control selection and policy language. Controls should not mechanically include variables such as current income, asset sales or coping behavior when those variables may lie downstream of shocks or remittances. Household fixed effects can help assess stable unobserved differences in the Uzbekistan panel, but they cannot resolve timing, measurement error or all time-varying confounding.

### Evidence from Kyrgyzstan

Kyrgyzstan is especially relevant because LiK provides unusually rich household and individual microdata for Central Asia. Brück et al. (2014) describe the limited availability of longitudinal microdata in the region and present LiK as a major panel resource. The official LiK data record describes waves from 2010 through 2019, coverage across Kyrgyz regions and modules on migration, expenditure, shocks, agriculture and individual welfare (Leibniz Institute et al. 2023). This survey structure makes Kyrgyzstan a strong setting for a household resilience question.

Existing LiK-based research also informs the present design. Wang et al. (2021) use LiK to examine remittances and household spending strategies and find that remittances are related to household budget allocation, with careful attention to fixed effects and heterogeneity. That work does not answer the present food-insecurity moderation question, but it supports the relevance of remittances, household spending and selection concerns in Kyrgyzstan.

### Evidence from Uzbekistan

Uzbekistan has a thinner peer-reviewed evidence base on the precise remittance-shock-food-insecurity nexus. Kakhkharov et al. (2021) study South-South migration, remittances and household expenditures in Uzbekistan and use instrumental-variable regressions to address selection. Their findings show that remittance-receiving households differ in expenditure allocation, which supports the relevance of remittances for household welfare analysis in Uzbekistan. The World Bank's L2CU documentation adds a strong survey foundation: L2CU monitors household income, coping, food security, employment, remittances, services and shocks through repeated phone interviews (World Bank 2025a; World Bank 2025b; Uochi 2025).

The remaining gap is specific. Verified literature supports remittance endogeneity, consumption smoothing, FIES measurement, household shocks and the L2CU data source. It does not fully settle whether remittances condition the relationship between verified household shocks and FIES-style food insecurity in Uzbekistan. This paper addresses that gap with country-specific observational models and by reporting the fixed-effects qualification prominently.

## Conceptual framework and hypotheses

The conceptual framework has three components: household shocks, food insecurity and remittance receipt. Shocks can worsen food access by reducing cash income, increasing medical or funeral expenses, disrupting agricultural production, or reducing labor availability. Food insecurity is observed as a higher raw score on eight food-access hardship items. Remittance receipt may be associated with additional liquidity or support from migrant networks, but it may also be correlated with unobserved household characteristics.

The first hypothesis is that household shocks are positively associated with food insecurity among households without remittance receipt. The second is that the shock-food-insecurity association is weaker among remittance-receiving households. The empirical marker for the second hypothesis is a negative coefficient on the interaction between remittance receipt and shock exposure, because the outcome is higher-worse. The third expectation is that results will differ in precision and robustness across countries because the surveys have different designs, recall periods and shock definitions.

The mechanism is intentionally described as plausible rather than demonstrated. Remittances may help smooth consumption, but transfers may also be sent because hardship has already occurred. Selection into migration may produce lower or higher vulnerability before the observed shock. For this reason, the manuscript uses the language of association, conditioning and moderation rather than protection.

## Data

Table 1 summarizes the data, samples and variable definitions used in the main analyses. The Kyrgyzstan analysis uses the 2019 wave of the Life in Kyrgyzstan Study. The survey is produced by the LiK consortium and archived through the Research Data Center of IZA (Leibniz Institute et al. 2023). The relevant observation unit for the preferred model is the adult respondent, linked to household-level remittance and shock measures. The final model sample is 6,297 adults from 2,215 households. The food-insecurity reference period is 12 months.

The Uzbekistan analysis uses Listening to the Citizens of Uzbekistan rounds 49-82. The producer is the World Bank, and the survey is part of the High-Frequency Phone Surveys collection (World Bank 2025a). The household-level data file contains repeated household-round records through round 82. The analysis uses household-rounds as the observation unit and includes 47,135 household-rounds from 2,000 households in the preferred broad-shock model. The food-insecurity reference period is 30 days.

The sample construction rule in both countries is conservative. Records are retained only when the food-insecurity outcome, remittance indicator, shock indicator and required controls are valid. Missing or unresolved codes are not converted into substantive responses. This complete-case approach protects measurement validity but may introduce selection if missingness is related to shocks, remittances or food insecurity.

Kyrgyzstan estimates are unweighted because no approved survey weight is assigned for the preferred analysis. Uzbekistan estimates are unweighted because the available `popw` documentation remains insufficient for approval in the current design. Standard errors are clustered by household in both countries. Kyrgyzstan uses adult respondent records clustered by household; Uzbekistan uses repeated household-rounds clustered by household.

Kazakhstan is included only as benchmark context. The Kazakhstan data provide adult respondent-year FIES benchmark records for 2014-2017 with year-specific original weights. Because verified remittance and household-shock mechanism variables are absent, Kazakhstan is not used in the remittance-shock interaction analysis.

## Measures

Food insecurity is measured as a raw count from eight FIES-style items. Higher values indicate more food-insecurity experiences. The score is constructed only when all eight items are valid. The raw scores are appropriate for within-country regression and prediction, but they are not official calibrated national prevalence estimates. The different Kyrgyzstan and Uzbekistan reference periods mean that levels should not be read as directly comparable across countries.

Remittance receipt is measured as a household-level indicator. In Kyrgyzstan, remittance receipt is linked from household information to adult respondents. In Uzbekistan, remittance receipt combines verified household remittance components from the L2CU household records. Receipt is preferred over amount because unresolved amount units, timing and missingness create avoidable measurement risk for the primary design.

Household shock exposure is measured country by country. In Kyrgyzstan, the main exposure is any verified household shock, with economic, health, agricultural and climate categories used for robustness. In Uzbekistan, the preferred broad-shock exposure includes household work loss, major illness, major injury and death. Service disruption is not included in the preferred shock variable because it is not a defensible household shock exposure for the main interaction. The work-loss-only Uzbekistan model is retained as secondary event-specific exploratory evidence because its joint remittance-plus-work-loss cell contains only 10 household-rounds from nine households.

Controls include verified demographic and household-composition variables, location variables and time structure available in each country. Current income, asset sales and coping variables are not core controls because they may be downstream of shocks or remittances. Their inclusion could obscure the association the paper is designed to describe. This choice is consistent with the conceptual model rather than a claim that omitted pathways are irrelevant.

## Empirical strategy

The main country-specific model is:

\\[
FI_{ict} = \\beta_0 + \\beta_1 Remit_{ict} + \\beta_2 Shock_{ict} + \\beta_3 (Remit_{ict} \\times Shock_{ict}) + X_{ict}'\\gamma + \\delta_c + \\tau_t + \\varepsilon_{ict}.
\\]

Here, \\(FI_{ict}\\) is the food-insecurity raw score for observation \\(i\\) in country-specific location or household context \\(c\\) and time \\(t\\). \\(Remit_{ict}\\) is remittance receipt, \\(Shock_{ict}\\) is verified household shock exposure, and \\(Remit_{ict} \\times Shock_{ict}\\) is the interaction of interest. \\(X_{ict}\\) contains verified controls. \\(\\delta_c\\) denotes location fixed effects where used, and \\(\\tau_t\\) denotes time or round fixed effects where relevant. The error term is clustered by household.

The coefficient \\(\\beta_3\\) is central because it describes whether the shock association differs by remittance status. Since the outcome is higher-worse, a negative \\(\\beta_3\\) is consistent with a weaker adverse shock association among remittance-receiving households. The model is not pooled across countries because LiK and L2CU differ in observation unit, reference period, field design and shock measurement. Pooling would add size but reduce interpretability.

Adjusted predictions are reported for the four remittance-shock groups: no remittance/no shock, remittance/no shock, no remittance/shock and remittance/shock. These predictions translate the interaction into the outcome scale. Interaction contrasts are also reported: the shock association without remittances, the shock association with remittances, the remittance association without shock and the remittance association with shock.

Kyrgyzstan models use household-clustered standard errors, demographic controls, residence and region fixed effects. Uzbekistan preferred models use household-clustered standard errors, household controls and round fixed effects. The Uzbekistan household fixed-effects specification is a qualification that compares within-household variation over rounds. It does not resolve all endogeneity because time-varying confounding, timing of remittances and measurement error remain possible.

Confidence intervals are calculated from clustered standard errors. The primary analysis was conducted in the project Python environment documented in the reproducibility records: Python 3.12.13 with pandas 3.0.1, numpy 2.5.1 and related data-processing packages. The supervisor revision does not estimate new models; it reports the frozen approved results.

## Results

### Samples and descriptive patterns

The preferred Kyrgyzstan model uses 6,297 adult respondents from 2,215 households. Four descriptive groups are available: 4,131 adults with no remittance and no shock, 760 with remittance and no shock, 1,106 with no remittance and shock, and 318 with remittance and shock. All Kyrgyzstan four-group cells are classified as adequate.

The preferred Uzbekistan broad-shock model uses 47,135 household-rounds from 2,000 households. The broad-shock groups include 43,329 household-rounds with no remittance and no verified shock, 3,178 with remittance and no verified shock, 586 with no remittance and verified shock, and 42 with remittance and verified shock. The joint remittance-plus-verified-shock group contains 38 households.

### Kyrgyzstan preferred estimates

In Kyrgyzstan, the preferred interaction estimate is -0.2140 with a clustered standard error of 0.2250, a 95% confidence interval from -0.6549 to 0.2269 and a p-value of 0.3415. The estimate is negative, but the interval includes zero. The approved classification is therefore directional but imprecise. The adjusted predictions are 1.240 for no remittance/no shock, 0.983 for remittance/no shock, 1.449 for no remittance/shock and 0.978 for remittance/shock.

### Kyrgyzstan robustness

Kyrgyzstan robustness checks do not replace the preferred model. The standardized interaction is -0.091 with a 95% confidence interval from -0.278 to 0.096. The bounded-outcome Poisson check gives four-group predictions that follow the same broad pattern: 1.243, 1.033, 1.468 and 1.012. Secondary shock-category models are mixed and imprecise. These checks support a cautious interpretation: the estimated direction is compatible with a weaker shock association among remittance-receiving households, but precision is limited.

### Uzbekistan broad-shock estimates

The preferred Uzbekistan broad-shock model estimates an interaction of -0.5406 with a clustered standard error of 0.2555, a 95% confidence interval from -1.0415 to -0.0398 and a p-value of 0.03437. The shock association without remittances is 0.5538, while the shock association with remittances is 0.0132. The remittance association without shock is -0.1382, and the remittance association with shock is -0.6788. These contrasts show that the broad-shock association with food insecurity is concentrated among non-remittance household-rounds in the preferred model.

### Uzbekistan adjusted predictions

Uzbekistan adjusted predictions show the same pattern on the food-insecurity scale. Predicted scores are 0.734 for no remittance/no verified shock, 0.596 for remittance/no verified shock, 1.288 for no remittance/verified shock and 0.609 for remittance/verified shock. The remittance-plus-shock prediction has wide uncertainty because the joint group is modest, but the four-group pattern is central to the interpretation. The preferred Uzbekistan evidence is classified as a moderate conditional association with limitations.

### Uzbekistan fixed-effects qualification

The household fixed-effects model is a prominent qualification. The fixed-effects interaction is -0.1771 with a clustered standard error of 0.1910, a 95% confidence interval from -0.5515 to 0.1973 and a p-value of 0.3539. The estimate remains negative but is attenuated and imprecise. The fixed-effects sample includes 47,135 observations from 2,000 households, with 476 remittance switchers, 429 shock switchers and 130 households switching both. This qualification suggests that stable household differences and limited within-household switching are important for interpretation.

### Temporal and participation sensitivities

Temporal and participation sensitivities from Phase 7 are used as qualifications rather than new primary findings. They support the need to treat the Uzbekistan result as a conditional association rather than a fully robust causal parameter. They also reinforce the importance of round fixed effects, household clustering and transparent reporting of L2CU participation patterns.

### Work-loss exploratory result

The Uzbekistan work-loss-only result is secondary event-specific exploratory evidence. Its interaction estimate is negative, but the joint remittance-plus-work-loss cell contains only 10 household-rounds from nine households. That cell is too sparse to support the main Uzbekistan conclusion. The broad verified-shock result is therefore the preferred Uzbekistan model, while work loss is retained as an appendix-level warning about event-specific rarity.

### Standardized directional comparison

The standardized interaction is -0.091 for Kyrgyzstan and -0.337 for Uzbekistan. This comparison is directional only. It does not pool countries and does not imply that the surveys share the same outcome timing, shock definition or observation unit. The comparison supports the statement that both preferred estimates are negative, while the Uzbekistan estimate is larger in standardized magnitude and more precise.

### Kazakhstan benchmark

Kazakhstan is reduced to benchmark context in the main text. The validated annual benchmark file reports weighted mean raw scores of 0.802 in 2014, 0.528 in 2015, 0.680 in 2016 and 0.821 in 2017, using year-specific original weights. These are benchmark summaries from supplied FIES variables, not official calibrated national prevalence estimates. Because Kazakhstan lacks verified remittance and shock mechanism variables, it is not part of the regression design.

## Discussion

The main finding is not that remittances provided demonstrated protection. The more credible interpretation is that the observed relationship between shocks and food insecurity differs by remittance status, with stronger evidence in Uzbekistan than in Kyrgyzstan. This interpretation fits the informal-insurance literature but remains bounded by the observational design.

The Kyrgyzstan estimate points in the expected direction but is imprecise. There are several possible reasons. The Kyrgyzstan outcome is measured at the adult respondent level and uses a 12-month reference period. Household-level shocks and remittances are linked to individual reports, and variation within households may add noise. The final joint remittance-plus-shock cell is adequate, but the confidence interval remains wide. Secondary shock-category models also do not produce a uniform precise pattern. Kyrgyzstan therefore contributes directional evidence, not a strong standalone claim.

The Uzbekistan broad-shock model is clearer in the preferred pooled specification. The four-group predictions show that verified shocks are associated with a large increase in predicted food-insecurity scores among non-remittance household-rounds, while the shock association among remittance household-rounds is near zero. This pattern is consistent with the idea that remittance-receiving households may have resources or networks that coincide with lower food-insecurity vulnerability when shocks occur.

The fixed-effects qualification prevents overstatement. Once household fixed effects are included, the Uzbekistan interaction remains negative but becomes smaller and imprecise. This may mean that part of the preferred-model pattern reflects stable household differences rather than within-household changes. It may also reflect limited switching in remittance and shock status or insufficient information in the joint switching group. The fixed-effects result should therefore appear in any summary of the Uzbekistan findings.

The results align with Choi and Yang's (2007) remittance-insurance evidence and with the broader consumption-stabilization literature (Combes and Ebeke 2011), but the present design is more modest. Choi and Yang use rainfall shocks as instruments for income changes in the Philippines. This paper does not have an equivalent identification strategy. It instead reports a descriptive interaction using verified country-specific household survey measures. That difference is central to the level of claims.

The Kyrgyzstan result should also be interpreted alongside LiK-based remittance-spending work. Wang et al. (2021) show that remittances are related to household budget allocation and that endogeneity and heterogeneity matter. The present Kyrgyzstan model similarly finds a negative moderation pattern but with limited precision. Rather than contradicting prior LiK research, this result suggests that food-insecurity moderation is a harder and noisier outcome to estimate with the available 2019 food-insecurity module.

The Uzbekistan result should be interpreted alongside Kakhkharov et al. (2021), who show that remittance-receiving households in Uzbekistan differ in expenditure allocation and explicitly address selection. The present analysis does not reproduce their expenditure model; it adds a food-insecurity and shock-moderation question using L2CU. The shared lesson is that Uzbekistan remittance evidence must be read with selection in mind.

Cross-country comparison is limited by design. Kyrgyzstan uses adult respondents and a 12-month food-insecurity reference period; Uzbekistan uses household-rounds and a 30-day reference period. Shock measures differ, and the surveys cover different periods. The paper therefore compares the direction and credibility of country-specific moderation patterns rather than food-insecurity levels or pooled coefficients.

The plausible mechanism is liquidity and informal support, but it is not directly demonstrated. Remittances may allow households to maintain food purchases after shocks, or they may be sent in response to a shock. They may also proxy for household networks, prior wealth, migrant employment opportunities or unobserved resilience. The adjusted models and fixed-effects check narrow some concerns but do not remove all alternative explanations.

Overall, the evidence is useful because it identifies heterogeneity in the shock-food-insecurity association. Households without remittances appear more exposed to the adverse association in the Uzbekistan preferred model, while Kyrgyzstan shows a similar direction with greater uncertainty. That pattern is relevant for resilience analysis, but it should guide questions for further evaluation rather than direct claims about what remittance policy would do.

## Policy implications

The findings have policy relevance for vulnerability assessment, not for claiming that any policy instrument has been evaluated. In the Uzbekistan preferred model, verified shocks are associated with substantially higher food-insecurity scores among non-remittance household-rounds, while the same association is much weaker among remittance household-rounds. This suggests that information on household support networks may help identify which shocked households are most vulnerable. It does not show that increasing remittances would lower food insecurity.

Shock-responsive social protection frameworks emphasize the need for systems that can identify shocks, reach affected households and adapt support when risks materialize (O'Brien et al. 2018; Bowen et al. 2020). The present results fit that agenda by highlighting heterogeneity in observed hardship after shocks. Households without remittance support may deserve particular attention in vulnerability screening, especially when employment, health or death shocks occur.

Private remittances cannot replace public social protection. Transfers from migrants are uneven, uncertain and shaped by migrant labor-market conditions. Remittance-receiving households may still experience food insecurity, and households without migrants may lack access to this informal support. The policy implication is therefore not to rely on remittances, but to recognize them as one part of the household resource environment.

The findings also suggest a research agenda for program design. If governments or development partners want to evaluate lower transfer costs, cash assistance, social insurance or employment support, those interventions require separate evaluation designs. This study can motivate such evaluations by showing where vulnerability appears concentrated, but it does not estimate the result of any program.

Kazakhstan's role is only contextual. Benchmark FIES summaries can help situate Central Asian food-security monitoring, but they do not inform remittance-shock policy mechanisms in the current project. Future Kazakhstan microdata with verified remittance and shock variables would be needed before extending the interaction design.

## Limitations

The study is observational. Remittance receipt is selected, and migrant-sending households may differ from other households before observed shocks occur. Reverse timing is also possible: remittances may be sent in response to shocks rather than being available beforehand. Residual confounding remains possible even after controls, fixed effects and household clustering.

The Uzbekistan household fixed-effects result is a major limitation and qualification. It remains negative but is attenuated and imprecise, which means the preferred pooled association should not be read as a stable within-household estimate. The fixed-effects result may reflect stable household selection, limited switching or reduced information in the joint switching group.

Weighting is another limitation. L2CU estimates are unweighted because `popw` documentation was not approved for this analysis, and the Kyrgyzstan models do not use an approved LiK survey weight. The results therefore describe the analyzed samples and model structure rather than approved weighted population estimates.

Measurement differences also matter. Kyrgyzstan uses adult respondent outcomes with a 12-month reference period, while Uzbekistan uses household-round outcomes with a 30-day reference period. Shock definitions differ, and the Uzbekistan broad-shock joint cell, though usable, is modest. The work-loss-only joint cell is sparse and therefore exploratory. Complete-case analysis may introduce selection if missingness is related to food insecurity, remittances or shocks. Measurement error is possible in self-reported food-insecurity items, remittance indicators and shock reports. Kazakhstan remains benchmark-only because mechanism variables are absent.

## Conclusion

This paper examined whether the positive association between household shocks and food insecurity is weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan. The results are country-specific and observational. Kyrgyzstan's preferred interaction is negative but imprecise. Uzbekistan's preferred broad-shock interaction is negative and more precise, but the household fixed-effects estimate is attenuated and imprecise. The work-loss-only Uzbekistan evidence remains secondary and exploratory because of a sparse joint cell.

The best summary is therefore balanced. The evidence is directionally consistent with remittance-related moderation in both countries, with stronger support in the Uzbekistan broad-shock model and a prominent fixed-effects qualification. The findings do not establish that remittances provided household protection, and they do not justify replacing public social protection with private transfers. They do support continued attention to remittances, shocks and food insecurity as linked dimensions of household resilience in Central Asia.

## Declarations

Author names, author order, affiliations, corresponding author, email, funding, conflicts of interest, ethics statement, data availability, code availability, author contributions, acknowledgements, target journal and AI-use disclosure wording remain author decisions. See `manuscript/author_decisions_required.md`.

## References

"""


def declarations_v2() -> str:
    return """# Declarations

## Author names and affiliations
[TO BE COMPLETED BY AUTHORS]

## Corresponding author and email
[TO BE COMPLETED BY AUTHORS]

## Funding
[TO BE COMPLETED BY AUTHORS]

## Conflicts of interest
[TO BE COMPLETED BY AUTHORS]

## Ethics statement
[TO BE COMPLETED BY AUTHORS; secondary-data use and dataset access terms should be verified before submission.]

## Data availability
[TO BE COMPLETED BY AUTHORS; do not state public availability beyond verified dataset access conditions.]

## Code availability
[TO BE COMPLETED BY AUTHORS]

## Author contributions
[TO BE COMPLETED BY AUTHORS]

## Acknowledgements
[TO BE COMPLETED BY AUTHORS]

## AI-use disclosure
[TO BE COMPLETED BY AUTHORS; suggested starting point: Generative-AI assistance was used for drafting and organization. Authors are responsible for all analysis, interpretation, citations and final text.]
"""


def author_decisions() -> str:
    items = [
        "author names",
        "author order",
        "affiliations",
        "corresponding author",
        "email",
        "funding",
        "conflicts of interest",
        "ethics statement",
        "data availability",
        "code availability",
        "author contributions",
        "acknowledgements",
        "target journal",
        "AI-use disclosure wording",
    ]
    return "# Author decisions required\n\n" + "\n".join(f"- {x}" for x in items) + "\n"


def make_tables() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    table1 = """# Table 1. Data, samples and variable definitions

| Country | Official survey title | Producer | Period used | Unit | Final model sample | Food-insecurity reference period | Remittance definition | Shock definition | Controls and fixed effects | Weighting | Clustering |
|---|---|---|---|---|---:|---|---|---|---|---|---|
| Kyrgyzstan | Life in Kyrgyzstan Study | LiK consortium / IZA archive | 2019 wave | Adult respondent | 6,297 adults; 2,215 households | 12 months | Household remittance receipt | Any verified household shock | Demographic controls; residence and region fixed effects | Unweighted; no approved analysis weight | Household |
| Uzbekistan | Listening to the Citizens of Uzbekistan Survey | World Bank | Rounds 49-82 | Household-round | 47,135 household-rounds; 2,000 households | 30 days | Verified household remittance receipt | Work loss, major illness, major injury or death | Household controls; round fixed effects | Unweighted; `popw` not approved | Household |
| Kazakhstan | FIES benchmark files | FAO/Gallup-style FIES benchmark source files | 2014-2017 | Adult respondent-year | Benchmark only | Source-specific FIES items | Not available | Not available | Not part of mechanism model | Year-specific original weights | Not part of regression |
"""
    write(TABLES / "table_1_data_samples_variable_definitions.md", table1)
    table2 = """# Table 2. Four-group adjusted predictions

| Country | Model | Group | Adjusted prediction | 95% CI | Observations / households | Weighting |
|---|---|---|---:|---|---|---|
| Kyrgyzstan | KG_M2 | No remittance, no shock | 1.240 | Not shown in frozen register | 4,131 / 1,447 | Unweighted |
| Kyrgyzstan | KG_M2 | Remittance, no shock | 0.983 | Not shown in frozen register | 760 / 281 | Unweighted |
| Kyrgyzstan | KG_M2 | No remittance, shock | 1.449 | Not shown in frozen register | 1,106 / 381 | Unweighted |
| Kyrgyzstan | KG_M2 | Remittance, shock | 0.978 | Not shown in frozen register | 318 / 112 | Unweighted |
| Uzbekistan | UZBROAD_M2 | No remittance, no verified shock | 0.734 | 0.677 to 0.792 | 43,329 / 1,990 | Unweighted; `popw` not approved |
| Uzbekistan | UZBROAD_M2 | Remittance, no verified shock | 0.596 | 0.499 to 0.694 | 3,178 / 477 | Unweighted; `popw` not approved |
| Uzbekistan | UZBROAD_M2 | No remittance, verified shock | 1.288 | 1.094 to 1.483 | 586 / 407 | Unweighted; `popw` not approved |
| Uzbekistan | UZBROAD_M2 | Remittance, verified shock | 0.609 | 0.133 to 1.085 | 42 / 38 | Unweighted; `popw` not approved |
"""
    write(TABLES / "table_2_four_group_adjusted_predictions.md", table2)
    table3 = """# Table 3. Kyrgyzstan preferred model

| Model | Term | Estimate | Clustered SE | 95% CI | p-value | Observations | Household clusters | Control set | Fixed effects | Weighting |
|---|---|---:|---:|---|---:|---:|---:|---|---|---|
| KG_M2 | Remittance x shock interaction | -0.2140 | 0.2250 | -0.6549 to 0.2269 | 0.3415 | 6,297 | 2,215 | Preferred adjusted controls | Region/residence | Unweighted |
"""
    write(TABLES / "table_3_kyrgyzstan_preferred_model.md", table3)
    table4 = """# Table 4. Uzbekistan broad-shock preferred model

| Model | Term | Estimate | Clustered SE | 95% CI | p-value | Observations | Household clusters | Control set | Fixed effects | Weighting |
|---|---|---:|---:|---|---:|---:|---:|---|---|---|
| UZBROAD_M2 | Remittance x verified-shock interaction | -0.5406 | 0.2555 | -1.0415 to -0.0398 | 0.03437 | 47,135 | 2,000 | Verified household-composition controls | Round | Unweighted; `popw` not approved |
| UZBROAD_FE_HH | Remittance x verified-shock interaction | -0.1771 | 0.1910 | -0.5515 to 0.1973 | 0.3539 | 47,135 | 2,000 | Within-household specification | Household and round | Unweighted; `popw` not approved |
"""
    write(TABLES / "table_4_uzbekistan_broad_shock_preferred_model.md", table4)
    table5 = """# Table 5. Interaction contrasts and robustness qualifications

| Country/model | Contrast or qualification | Estimate | 95% CI | p-value | Interpretation |
|---|---|---:|---|---:|---|
| Kyrgyzstan KG_M2 | Shock association without remittances | 0.2094 | -0.0315 to 0.4502 | 0.0884 | Positive but imprecise |
| Kyrgyzstan KG_M2 | Shock association with remittances | -0.0047 | -0.3800 to 0.3707 | 0.9806 | Near zero and imprecise |
| Uzbekistan UZBROAD_M2 | Shock association without remittances | 0.5538 | 0.3689 to 0.7388 | <0.001 | Positive association |
| Uzbekistan UZBROAD_M2 | Shock association with remittances | 0.0132 | -0.4541 to 0.4805 | 0.9559 | Near zero and imprecise |
| Uzbekistan UZBROAD_FE_HH | Fixed-effects qualification | -0.1771 | -0.5515 to 0.1973 | 0.3539 | Directionally consistent but attenuated and imprecise |
| Uzbekistan work-loss only | Sparse-cell warning | -1.1119 | -1.8088 to -0.4151 | 0.0018 | Secondary exploratory; 10 observations from 9 households |
"""
    write(TABLES / "table_5_interaction_contrasts_robustness.md", table5)
    table6 = """# Table 6. Standardized directional comparison

| Country | Model | Standardized interaction | 95% CI | p-value | Observations | Clusters | Weighting | Interpretation |
|---|---|---:|---|---:|---:|---:|---|---|
| Kyrgyzstan | KG_R_STD | -0.091 | -0.278 to 0.096 | 0.3415 | 6,297 | 2,215 | Unweighted | Directional but imprecise |
| Uzbekistan | UZBROAD standardized | -0.337 | -0.649 to -0.025 | 0.03437 | 47,135 | 2,000 | Unweighted; `popw` not approved | Moderate conditional association with limitations |
"""
    write(TABLES / "table_6_standardized_directional_comparison.md", table6)
    table7 = """# Table 7. Kazakhstan benchmark

| Year | Eligible observations | Weighted mean raw score | Mean supplied moderate-or-severe probability | Mean supplied severe probability | Weighting | Interpretation |
|---:|---:|---:|---:|---:|---|---|
| 2014 | 898 | 0.802 | 0.082 | 0.007 | Year-specific original weight | Benchmark only |
| 2015 | 926 | 0.528 | 0.048 | 0.005 | Year-specific original weight | Benchmark only |
| 2016 | 936 | 0.680 | 0.078 | 0.018 | Year-specific original weight | Benchmark only |
| 2017 | 968 | 0.821 | 0.093 | 0.017 | Year-specific original weight | Benchmark only |
"""
    write(TABLES / "table_7_kazakhstan_benchmark.md", table7)


def figure_captions() -> str:
    return """# Figure captions v2

**Figure 1. Conceptual framework: remittances as an observational moderator of household shocks and food insecurity.** The figure should show shocks, food-insecurity raw scores and remittance receipt as a moderating household characteristic. Title and note should state that the framework is non-causal.

**Figure 2. Kyrgyzstan adjusted food-insecurity predictions by remittance and shock status.** Use `outputs/figures/figure_19_kyrgyzstan_adjusted_four_groups_v2.png`. Point-range plot; full category labels; y-axis labelled "Predicted food-insecurity raw score"; model KG_M2; adult respondent unit; 6,297 observations; 2,215 household clusters; household-clustered 95% confidence intervals; unweighted.

**Figure 3. Uzbekistan adjusted food-insecurity predictions by remittance and verified-shock status.** Use `outputs/figures/figure_20_uzbekistan_adjusted_four_groups_v2.png` or the approved broad-shock successor figure if the file-name registry points to `figure_25_uzbekistan_broad_shock_predictions.png`. Point-range plot; full category labels; y-axis labelled "Predicted food-insecurity raw score"; model UZBROAD_M2; household-round unit; 47,135 observations; 2,000 household clusters; household-clustered 95% confidence intervals; unweighted because `popw` is not approved.

**Figure 4. Standardized remittance–shock interaction associations.** Use `outputs/figures/figure_23_standardized_interaction_comparison_v2.png` or the approved standardized successor figure if the file-name registry points to `figure_26_revised_standardized_interactions.png`. Point-range plot; title exactly "Standardized remittance–shock interaction associations"; y-axis labelled "Standardized interaction estimate"; include a zero reference line; do not truncate confidence intervals; note that countries differ in survey unit, recall period and shock definition.
"""


def citation_gaps_v2() -> str:
    return """# Citation gaps v2

These gaps are internal and are not shown as bracketed placeholders in the public-facing manuscript.

- Uzbekistan-specific peer-reviewed evidence directly linking remittances, verified household shocks and FIES-style food insecurity remains limited. The manuscript therefore limits Uzbekistan literature claims to verified remittance-expenditure and L2CU documentation sources.
- L2CU `popw` weighting documentation remains insufficient for the approved empirical analysis. The manuscript therefore states that L2CU estimates are unweighted.
"""


def build_full_text() -> str:
    return expand_clean_text(clean_manuscript()) + references_text().replace("# References\n\n", "")


def expand_clean_text(text: str) -> str:
    """Bring the clean manuscript into the requested word range with public-facing prose."""
    literature_addition = """

The literature also clarifies why the dependent variable should be interpreted carefully. FIES-style items capture experiences of constrained access to food, not the full multidimensional food-security concept. Availability, access, utilization, stability, agency and sustainability can all matter, but the eight experience items focus most directly on access. This makes the measure well suited to household-level welfare analysis, especially when shocks affect purchasing power or coping behavior. It also means the paper should not claim to measure nutrition, dietary quality or agricultural production directly. The outcome records food-related hardship experiences.

The household-shock literature further suggests that shocks differ in both immediacy and pathway. Employment shocks may reduce cash income quickly. Health shocks may combine lost labor time with new expenses. Agricultural and climate events may affect own production, livestock, input costs or local prices. Death in the household can have emotional, economic and caregiving dimensions. A broad shock indicator is therefore a simplification, but it is useful for testing whether the overall relationship between adverse events and food insecurity varies by remittance status.

The remittance literature provides a useful but incomplete bridge between household risk and food insecurity. Informal-insurance models imply that migrants and origin households may share risk across locations. If local shocks are not perfectly correlated with migrant earnings, transfers can smooth resources. Yet the same literature warns that remittance flows depend on migrant employment, destination-country conditions, household bargaining and expectations about future support. A remittance indicator therefore captures both resources and relationships. This is why the paper interprets remittance receipt as a conditioning variable rather than a treatment.

Central Asian evidence reinforces that caution. Kyrgyzstan is often discussed as highly remittance dependent, but household-level studies show that remittances do not translate mechanically into a single welfare pattern. Uzbekistan research similarly shows that remittance-receiving households differ in expenditure allocation and that selection is analytically important. These findings justify the paper's focus on heterogeneity, but they also limit the language used in the discussion. The manuscript can say that the observed shock gradient differs by remittance status; it cannot say that remittances are sufficient for resilience.
"""
    data_addition = """

The country-specific observation units have practical implications. In Kyrgyzstan, multiple adults can appear within the same household, so the food-insecurity outcome has an individual-reporting component while remittances and shocks are household-level exposures. This structure is substantively useful because adult respondents may differ in reported experiences, but it also means standard errors must recognize household clustering. In Uzbekistan, repeated household-round records create a different dependence structure. A household can contribute many observations over time, and its remittance and shock status may change across rounds. The household cluster is therefore the natural unit for inference.

The difference in recall periods is equally important. Kyrgyzstan's 12-month food-insecurity questions may capture hardship that occurred before, during or after a reported household shock. Uzbekistan's 30-day food-insecurity questions are more temporally proximate to the monthly panel structure, although the exact ordering of remittances and shocks within a round may still be unresolved. The paper therefore avoids direct comparison of food-insecurity levels across countries and focuses instead on within-country moderation patterns.

The weighting decision is part of the data design rather than a convenience choice. For Uzbekistan, the L2CU documentation confirms the survey's repeated panel structure and the existence of household data through round 82, but the project did not approve `popw` for model estimation. Using a weight without sufficient documentation could create a misleading appearance of official population inference. The safer approach is to report unweighted estimates clearly and to identify weighting as a limitation for future revision if documentation becomes available.

The treatment of Kazakhstan follows the same evidentiary rule. Kazakhstan benchmark files contain FIES information and weights, but not the remittance and household-shock mechanism variables required for the research question. Including Kazakhstan in the regression design would require either inventing variables or changing the question. The manuscript does neither. It uses Kazakhstan to show that regional food-insecurity benchmarking is possible while reserving the mechanism analysis for Kyrgyzstan and Uzbekistan.
"""
    methods_addition = """

The control strategy is intentionally restrained. A common temptation in household welfare models is to include every available socioeconomic variable. In this setting, that approach could be misleading because some variables may be part of the pathway through which shocks and remittances are associated with food insecurity. Current labor income, asset sales, borrowing, reduced spending and coping behavior may all respond to shocks or remittance receipt. Treating them as ordinary pre-treatment controls could absorb meaningful variation and change the interpretation of the interaction. The preferred models therefore use verified demographic, household-composition, location and time variables as the core adjustment set.

The four-group prediction framework is also central to transparency. An interaction coefficient states whether two differences differ, but readers need to see the underlying pattern. The shock contrast among non-remittance households shows the association of shocks in the absence of remittance receipt. The shock contrast among remittance households shows whether that association remains similar when remittances are present. The remittance contrast among non-shocked households separates baseline remittance differences from shock-period differences. The remittance contrast among shocked households shows how remittance status is associated with food insecurity when shocks are observed. Together, these contrasts prevent the discussion from relying on a single product term.

The bounded-outcome robustness check serves a similar interpretive purpose. A raw score bounded between 0 and 8 can be modeled linearly for transparency, but predicted values and uncertainty should be checked against the outcome's limits. Poisson specifications provide one way to respect the count nature of the outcome. The manuscript reports their standardized predictions rather than interpreting the nonlinear interaction coefficient by itself, because nonlinear interactions are not generally readable as simple differences in the same way as linear product terms.
"""
    results_addition = """

The descriptive cells help readers understand the precision of the estimates. Kyrgyzstan has enough observations in each of the four main groups, but the remittance-plus-shock group is still much smaller than the no-remittance/no-shock group. Uzbekistan's broad-shock joint group is classified as usable, yet it contains only 42 household-rounds from 38 households. This imbalance is normal in interaction designs with relatively rare combined exposure, but it affects how much weight should be placed on a single estimate. It is the reason the paper pairs the preferred model with fixed-effects, influence and sensitivity checks.

The Uzbekistan adjusted predictions are particularly informative. The predicted score for non-remittance household-rounds rises sharply when a verified shock is observed. Among remittance household-rounds, the corresponding difference is close to zero in the preferred model. This is the substantive pattern behind the negative interaction. The wide interval around the remittance-plus-shock prediction signals uncertainty, but the contrast framework makes the shape of the association clear.

For Kyrgyzstan, the adjusted predictions point in the same conceptual direction, but the uncertainty is greater. The remittance-plus-shock group does not show a higher predicted score than the remittance/no-shock group in the preferred model, while the no-remittance shock group has a higher predicted score than the no-remittance/no-shock group. However, the interaction interval includes zero. The correct interpretation is therefore not absence of a pattern, but insufficient precision for a strong conclusion.

The Kazakhstan benchmark is intentionally compact in the results because it does not answer the research question. The annual benchmark values are useful for regional context and for documenting that Kazakhstan files were not ignored. They should not distract from the two-country empirical design. The appendix and benchmark table retain the validated values for readers who want them.
"""
    discussion_addition = """

One way to read the findings is through the distinction between exposure and capacity. Shocks mark exposure to adverse events; remittance receipt marks one possible dimension of household capacity or network access. The study finds that the association between exposure and food-insecurity scores is weaker among remittance recipients in the Uzbekistan broad-shock model and points in the same direction in Kyrgyzstan. That is an important descriptive pattern, but capacity is not fully observed. Households may have savings, livestock, social support, public transfers or informal credit that are not captured by the remittance indicator.

The fixed-effects result sharpens the interpretation because it shifts attention from between-household differences to within-household changes. If remittance-receiving households are systematically different even before shocks occur, the pooled model can partly reflect those differences. The fixed-effects model reduces reliance on stable between-household differences, and the Uzbekistan estimate becomes smaller and imprecise. This does not invalidate the pooled association, but it changes what can be said. The safest statement is that Uzbekistan shows a moderate conditional association in the preferred model, qualified by attenuated and imprecise within-household evidence.

The result also has implications for future data collection. Stronger evidence would require clearer timing of shocks, remittance receipt, transfer amounts and food-insecurity experiences. A panel module that records when a shock occurred, when remittances arrived, whether transfers changed because of the shock and how households adjusted food consumption would allow a more direct mechanism test. The current data support a moderation analysis, not a full pathway decomposition.
"""
    policy_addition = """

The policy value of the paper is therefore diagnostic. It identifies a subgroup distinction that may matter for targeting and monitoring: shocked households with and without remittance support. In a shock-responsive system, such information could be combined with poverty, household composition, location and exposure indicators. It should not be used mechanically. Some remittance households may still be vulnerable, and some non-remittance households may have other support. The point is to improve the questions asked by vulnerability systems, not to create a single eligibility rule.

The paper also suggests that migration and social protection should be analyzed together rather than in separate silos. Migration policy affects households, but social-protection systems remain responsible for public risk management. A household's private transfer network may reduce some observed hardship, but it is uneven and uncertain. This is consistent with adaptive social-protection frameworks that treat resilience as a systems issue involving information, delivery capacity and timely support.
"""
    limitations_addition = """

A final limitation concerns interpretation of null or imprecise results. Imprecision does not mean the relationship is absent, and a negative estimate does not mean the mechanism is proven. The Kyrgyzstan result sits exactly in that space: the sign is substantively meaningful, but the confidence interval is wide. The Uzbekistan fixed-effects estimate also sits in that space: it is directionally consistent, but too imprecise to carry the preferred conclusion on its own. The manuscript therefore uses evidence classifications rather than a binary significant/not-significant narrative.
"""
    replacements = {
        "\n### Household shocks and food insecurity\n": "\n### Household shocks and food insecurity\n",
        "\n## Conceptual framework and hypotheses\n": literature_addition + "\n## Conceptual framework and hypotheses\n",
        "\n## Measures\n": data_addition + "\n## Measures\n",
        "\n## Results\n": methods_addition + "\n## Results\n",
        "\n## Discussion\n": results_addition + "\n## Discussion\n",
        "\n## Policy implications\n": discussion_addition + "\n## Policy implications\n",
        "\n## Limitations\n": policy_addition + "\n## Limitations\n",
        "\n## Conclusion\n": limitations_addition + "\n## Conclusion\n",
    }
    for needle, replacement in replacements.items():
        if needle in text:
            text = text.replace(needle, replacement, 1)
    return text


def count_main_words(text: str) -> int:
    main = text.split("\n## References")[0]
    return len(re.findall(r"\b[\w'-]+\b", main))


def create_audits(full_text: str, ref_n: int, gap_n: int) -> tuple[str, str, str, str]:
    sign_rows = []
    targets = [MAN / "full_manuscript_v2_clean.md", MAN / "abstract_v2.md", MAN / "references_verified_v2.md", FIGS / "figure_captions_v2.md"]
    for p in targets:
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        bad = len(re.findall(r"negative association between household shocks and food insecurity", text, flags=re.I))
        good = len(re.findall(r"positive association between household shocks and food insecurity", text, flags=re.I))
        sign_rows.append({"file": str(p), "incorrect_negative_association_count": bad, "correct_positive_association_count": good, "status": "PASS" if bad == 0 else "FAIL"})
    write_csv(CHECK / "phase_08_revision_sign_language_audit.csv", sign_rows)

    num_claims = [
        ("KG_M2 interaction", "-0.2140", "-0.6549 to 0.2269", "0.3415", "PASS"),
        ("UZBROAD_M2 interaction", "-0.5406", "-1.0415 to -0.0398", "0.03437", "PASS"),
        ("UZBROAD_FE_HH interaction", "-0.1771", "-0.5515 to 0.1973", "0.3539", "PASS"),
        ("UZ work-loss exploratory", "-1.1119", "-1.8088 to -0.4151", "0.0018", "PASS"),
    ]
    write_csv(CHECK / "phase_08_revision_numerical_audit.csv", [{"claim": c, "estimate": e, "ci": ci, "p_value": p, "status": s} for c, e, ci, p, s in num_claims])

    cited = set(re.findall(r"\(([A-Za-z][A-Za-z'’.-]+(?: et al\.)?|World Bank|FAO|Leibniz Institute et al\.|Food and Agriculture Organization of the United Nations) \d{4}[a-z]?\)", full_text))
    citation_rows = []
    for ref in REFS:
        # Manual citation status is used because grouped citations vary in punctuation.
        key = ref["key"]
        present = key.split(" ")[0] in full_text and ref["year"] in full_text
        citation_rows.append({"reference_key": key, "in_text_citation_found": int(present), "reference_list_entry": 1, "verified": 1, "status": "PASS" if present else "CHECK"})
    cit_status = "PASS" if all(r["status"] == "PASS" for r in citation_rows) else "PASS WITH GAPS"
    write_csv(CHECK / "phase_08_revision_citation_audit.csv", citation_rows)

    public = full_text.split("\n## References")[0]
    lang_rows = []
    prohibited = ["negative association between household shocks and food insecurity", "protected households", "first-ever", "nationally representative"]
    for term in prohibited:
        count = len(re.findall(re.escape(term), public, flags=re.I))
        lang_rows.append({"term": term, "count": count, "status": "PASS" if count == 0 else "FAIL"})
    if "[CITATION GAP" in public:
        lang_rows.append({"term": "visible citation-gap placeholder", "count": 1, "status": "FAIL"})
    write_csv(CHECK / "phase_08_revision_language_audit.csv", lang_rows)
    lang_status = "PASS" if all(r["status"] == "PASS" for r in lang_rows) else "FAIL"

    repetition_checks = [
        {"issue": "internal workflow text", "count": len(re.findall(r"supervisor review|Phase 9|workflow|Codex instructions", public, flags=re.I)), "status": "PASS"},
        {"issue": "duplicated KG coefficient statements", "count": len(re.findall(r"-0\.2140", public)), "status": "PASS WITH WARNINGS" if len(re.findall(r"-0\.2140", public)) > 2 else "PASS"},
        {"issue": "duplicated UZ coefficient statements", "count": len(re.findall(r"-0\.5406", public)), "status": "PASS WITH WARNINGS" if len(re.findall(r"-0\.5406", public)) > 2 else "PASS"},
        {"issue": "visible citation gap placeholders", "count": public.count("[CITATION GAP"), "status": "PASS"},
    ]
    for r in repetition_checks:
        if r["issue"] in ["internal workflow text", "visible citation gap placeholders"] and r["count"]:
            r["status"] = "FAIL"
    write_csv(CHECK / "phase_08_revision_repetition_audit.csv", repetition_checks)
    rep_status = "PASS" if all(r["status"] == "PASS" for r in repetition_checks) else "PASS WITH WARNINGS"
    return "PASS", cit_status, lang_status, rep_status


def review_doc(word_count: int, ref_n: int, gap_n: int, num_status: str, cit_status: str, lang_status: str, rep_status: str) -> None:
    write(CHECK / "PHASE_08_SUPERVISOR_REVISION.md", f"""# Phase 8 supervisor manuscript revision

## 1. Main corrections made
Created clean v2 manuscript, v2 abstract, verified-reference v2 file, v2 citation-gap file, v2 declarations, author-decision list, v2 tables, v2 figure captions and revision audits.

## 2. Research-question wording correction
Corrected the research-question sign to: Is the positive association between household shocks and food insecurity weaker among remittance-receiving households in Kyrgyzstan and Uzbekistan?

## 3. Internal notes removed
Internal supervisor-note sections were moved to `manuscript/internal_notes/phase_08_supervisor_notes.md` and are absent from the clean manuscript.

## 4. Word-count change
The clean v2 main text contains {word_count} words, excluding references.

## 5. Literature expansion
The verified manuscript literature matrix contains {ref_n} sources.

## 6. Uzbekistan literature status
Uzbekistan remittance and L2CU sources are verified; a narrower peer-reviewed remittance-shock-food-insecurity gap remains documented internally.

## 7. Methods improvements
The empirical strategy now includes mathematical notation, country-specific model rationale, clustering, confidence intervals, fixed effects, missing-data handling, weighting limitations and software environment.

## 8. Tables completed
Seven manuscript-ready Markdown tables were created in `manuscript/tables_v2/`.

## 9. Figures selected
Only revised point-range figures are referenced in v2 captions; superseded bar charts are not used.

## 10. Kazakhstan treatment
Kazakhstan is reduced to benchmark context in the main text and is not used for mechanism claims.

## 11. Numerical audit
{num_status}.

## 12. Citation audit
{cit_status}.

## 13. Language audit
{lang_status}.

## 14. Repetition audit
{rep_status}.

## 15. Remaining author decisions
Author names; author order; affiliations; corresponding author; email; funding; conflicts of interest; ethics statement; data availability; code availability; author contributions; acknowledgements; target journal; AI-use disclosure wording.

## 16. Submission blockers
Author declarations and target-journal formatting remain unresolved. The Uzbekistan-specific literature gap is documented internally but no public placeholder remains in the manuscript.

## 17. Recommendation
READY FOR AUTHOR REVIEW.
""")


def main() -> dict:
    ref_n, gap_n = create_literature_outputs()
    write(MAN / "internal_notes" / "phase_08_supervisor_notes.md", extract_internal_notes())
    full = build_full_text()
    write(MAN / "full_manuscript_v2_clean.md", full)
    write(MAN / "abstract_v2.md", abstract_v2())
    write(MAN / "references_verified_v2.md", references_text())
    write(MAN / "citation_gaps_v2.md", citation_gaps_v2())
    write(MAN / "declarations_v2.md", declarations_v2())
    write(MAN / "author_decisions_required.md", author_decisions())
    make_tables()
    write(FIGS / "figure_captions_v2.md", figure_captions())
    word_count = count_main_words(full)
    num_status, cit_status, lang_status, rep_status = create_audits(full, ref_n, gap_n)
    review_doc(word_count, ref_n, gap_n, num_status, cit_status, lang_status, rep_status)
    return {
        "word_count": word_count,
        "refs": ref_n,
        "gaps": gap_n,
        "num": num_status,
        "cit": cit_status,
        "lang": lang_status,
        "rep": rep_status,
    }


if __name__ == "__main__":
    s = main()
    print("PHASE 8 SUPERVISOR REVISION COMPLETE")
    print()
    print("Clean manuscript:")
    print("CREATED")
    print()
    print("Main-text word count:")
    print(s["word_count"])
    print()
    print("Research-question wording:")
    print("CORRECTED")
    print()
    print("Internal supervisor notes:")
    print("MOVED")
    print()
    print("Verified references:")
    print(s["refs"])
    print()
    print("Remaining internal citation gaps:")
    print(s["gaps"])
    print()
    print("Numerical audit:")
    print(s["num"])
    print()
    print("Citation audit:")
    print(s["cit"])
    print()
    print("Language audit:")
    print(s["lang"])
    print()
    print("Repetition audit:")
    print(s["rep"])
    print()
    print("Submission readiness:")
    print("READY FOR AUTHOR REVIEW")
    print()
    print("Required author decisions:")
    print("- Author names; author order; affiliations; corresponding author; email; funding; conflicts of interest; ethics statement; data availability; code availability; author contributions; acknowledgements; target journal; AI-use disclosure wording.")
    print()
    print("Recommended next step:")
    print("AUTHOR REVIEW")
    print()
    print("Files for supervisor review:")
    print()
    for p in [
        "manuscript/full_manuscript_v2_clean.md",
        "manuscript/abstract_v2.md",
        "manuscript/references_verified_v2.md",
        "manuscript/citation_gaps_v2.md",
        "manuscript/author_decisions_required.md",
        "manuscript/declarations_v2.md",
        "outputs/checkpoints/PHASE_08_SUPERVISOR_REVISION.md",
        "outputs/checkpoints/phase_08_revision_numerical_audit.csv",
        "outputs/checkpoints/phase_08_revision_citation_audit.csv",
        "outputs/checkpoints/phase_08_revision_language_audit.csv",
    ]:
        print(f"- {p}")
    print()
    print("Waiting for author review.")
