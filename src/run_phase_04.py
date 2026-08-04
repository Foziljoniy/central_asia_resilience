"""Run Phase 4 descriptive analysis from the project root."""
from phase4_common import run_all

if __name__ == "__main__":
    status = run_all()
    print("PHASE 4 COMPLETE")
    print()
    print("Administrative closeout:")
    print(status["administrative_closeout"])
    print()
    print("Input validation:")
    print(status["input_validation"])
    print()
    print("Kyrgyzstan descriptive sample:")
    print(status["kg_sample"])
    print()
    print("Uzbekistan descriptive sample:")
    print(status["uz_sample"])
    print()
    print("Kazakhstan benchmark sample:")
    print(status["kaz_sample"])
    print()
    print("Kyrgyzstan four-group cells:")
    print(status["kg_cells"])
    print()
    print("Uzbekistan four-group cells:")
    print(status["uz_cells"])
    print()
    print("FIES measurement quality:")
    print(status["fies_quality"])
    print()
    print("Kazakhstan annual benchmark:")
    print(status["kaz_benchmark"])
    print()
    print("Phase 5 main model readiness:")
    print()
    print(f"- Kyrgyzstan: {status['kg_ready']}")
    print(f"- Uzbekistan: {status['uz_ready']}")
    print()
    print("Critical findings requiring supervisor review:")
    for item in status["critical"]:
        print(f"- {item}")
    print()
    print("Recommended Phase 5 status:")
    print(status["recommended"])
    print()
    print("Files for supervisor review:")
    print()
    for path in [
        "outputs/checkpoints/PHASE_04_DESCRIPTIVE_ANALYSIS.md",
        "outputs/checkpoints/phase_04_sample_flow.csv",
        "outputs/checkpoints/phase_04_missingness.csv",
        "outputs/checkpoints/phase_04_fies_measurement_quality.csv",
        "outputs/checkpoints/phase_04_kyrgyzstan_four_groups.csv",
        "outputs/checkpoints/phase_04_uzbekistan_four_groups.csv",
        "outputs/checkpoints/phase_04_kazakhstan_annual_benchmark.csv",
        "outputs/checkpoints/phase_04_model_readiness.csv",
        "outputs/checkpoints/phase_04_descriptive_findings_register.csv",
        "outputs/tables/table_05_kyrgyzstan_four_groups.csv",
        "outputs/tables/table_10_uzbekistan_four_groups.csv",
        "outputs/tables/table_14_kazakhstan_annual_benchmark.csv",
    ]:
        print(f"- {path}")
    print()
    print("Waiting for supervisor approval before Phase 5.")
