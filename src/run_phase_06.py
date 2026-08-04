"""Run complete Phase 6 synthesis from project root."""
from phase6_common import run_all

if __name__ == "__main__":
    status = run_all()
    print("PHASE 6 COMPLETE")
    print()
    print("Result validation:")
    print(status["result_validation"])
    print()
    print("Kyrgyzstan evidence classification:")
    print("DIRECTIONAL BUT IMPRECISE")
    print()
    print("Uzbekistan evidence classification:")
    print("MODERATE CONDITIONAL ASSOCIATION")
    print()
    print("Uzbekistan fixed-effects qualification:")
    print("DIRECTIONALLY CONSISTENT BUT ATTENUATED AND IMPRECISE")
    print()
    print("Uzbekistan work-loss result:")
    print("SECONDARY EXPLORATORY")
    print()
    print("Cross-country synthesis:")
    print("DIRECTIONALLY CONSISTENT; DIFFERENT PRECISION AND ROBUSTNESS")
    print()
    print("Kazakhstan role:")
    print("FOOD-INSECURITY AND DEMOGRAPHIC BENCHMARK")
    print()
    print("Claims register:")
    print(status["claims"])
    print()
    print("Literature alignment:")
    print(status["literature"])
    print()
    print("Phase 7 required:")
    print(status["phase7"])
    print()
    print("Recommended next step:")
    print(status["next"])
    print()
    print("Files for supervisor review:")
    print()
    for p in [
        "outputs/checkpoints/PHASE_06_SYNTHESIS.md",
        "outputs/checkpoints/phase_06_result_validation.csv",
        "outputs/checkpoints/phase_06_claims_register.csv",
        "outputs/checkpoints/phase_06_results_consistency_matrix.csv",
        "outputs/checkpoints/phase_06_phase7_needs.csv",
        "manuscript/results_core.md",
        "manuscript/abstract_results_options.md",
        "manuscript/limitations_register.md",
        "manuscript/final_table_plan.csv",
        "manuscript/final_figure_plan.csv",
        "literature/drafts/literature_review_v3_aligned.md",
    ]:
        print(f"- {p}")
    print()
    print("Waiting for supervisor approval.")
