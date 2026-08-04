"""Run complete Phase 5 from the project root."""
from phase5_common import run_all

if __name__ == "__main__":
    status = run_all()
    print("PHASE 5 COMPLETE")
    print()
    print("Input validation:")
    print(status["input_validation"])
    print()
    print("Kyrgyzstan preferred model:")
    print(status["kg_model"])
    print()
    print("Kyrgyzstan interaction estimate:")
    print(status["kg_est"])
    print()
    print("Kyrgyzstan buffering pattern:")
    print(status["kg_pattern"])
    print()
    print("Uzbekistan preferred model:")
    print(status["uz_model"])
    print()
    print("Uzbekistan interaction estimate:")
    print(status["uz_est"])
    print()
    print("Uzbekistan buffering pattern:")
    print(status["uz_pattern"])
    print()
    print("Uzbekistan household fixed-effects robustness:")
    print(status["fe_status"])
    print()
    print("Cross-country directional consistency:")
    print(status["direction"])
    print()
    print("Kazakhstan benchmark uncertainty:")
    print(status["kaz_status"])
    print()
    print("Robustness assessment:")
    print()
    print(f"- Kyrgyzstan: {status['kg_robustness']}")
    print(f"- Uzbekistan: {status['uz_robustness']}")
    print()
    print("Critical findings requiring supervisor review:")
    for item in status["critical"]:
        print(f"- {item}")
    print()
    print("Recommended Phase 6 status:")
    print(status["recommended"])
    print()
    print("Files for supervisor review:")
    print()
    for path in [
        "outputs/checkpoints/PHASE_05_MODELS.md",
        "outputs/checkpoints/phase_05_results_register.csv",
        "outputs/checkpoints/phase_05_interaction_contrasts.csv",
        "outputs/checkpoints/phase_05_model_diagnostics.csv",
        "outputs/checkpoints/phase_05_l2cu_within_variation.csv",
        "outputs/tables/table_16_kyrgyzstan_main_models.csv",
        "outputs/tables/table_17_kyrgyzstan_predicted_groups.csv",
        "outputs/tables/table_18_uzbekistan_main_models.csv",
        "outputs/tables/table_19_uzbekistan_predicted_groups.csv",
        "outputs/tables/table_21_standardized_country_comparison.csv",
        "outputs/tables/table_22_kazakhstan_benchmark_with_ci.csv",
        "outputs/tables/table_23_robustness_summary.csv",
        "outputs/figures/figure_19_kyrgyzstan_adjusted_four_groups.png",
        "outputs/figures/figure_20_uzbekistan_adjusted_four_groups.png",
        "outputs/figures/figure_23_standardized_interaction_comparison.png",
    ]:
        print(f"- {path}")
    print()
    print("Waiting for supervisor approval before Phase 6.")
