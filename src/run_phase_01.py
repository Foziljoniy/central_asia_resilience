"""Run the reproducible Phase 1 pipeline and stop before Phase 2."""

from phase1_common import run_all


if __name__ == "__main__":
    path, status = run_all()
    print("PHASE 1 COMPLETE")
    print(f"Recommended research path: {path}")
    print("Primary research question status:")
    print(status)
    print("Files for supervisor review:")
    for item in [
        "outputs/checkpoints/PHASE_01_DATA_AUDIT.md",
        "outputs/checkpoints/phase_01_archive_inventory.csv",
        "outputs/checkpoints/phase_01_dataset_inventory.csv",
        "outputs/checkpoints/phase_01_variable_candidates.csv",
        "outputs/checkpoints/phase_01_country_compatibility_matrix.csv",
        "outputs/checkpoints/phase_01_topic_feasibility_matrix.csv",
        "outputs/checkpoints/phase_01_compatibility_risks.md",
        "literature/matrices/literature_matrix.csv",
        "research/main_analysis_plan.md",
    ]:
        print(f"- {item}")
    print("Waiting for supervisor review before Phase 2.")
