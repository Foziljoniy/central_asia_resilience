"""Run Phase 7 limited publication robustness from project root."""
from phase7_common import run_all

if __name__ == "__main__":
    s = run_all()
    print("PHASE 7 COMPLETE")
    print()
    print("Input validation:")
    print(s["input"])
    print()
    print("L2CU weight decision:")
    print(s["weight_decision"])
    print()
    print("Uzbekistan round-sensitive inference:")
    print(s["round"])
    print()
    print("Uzbekistan lagged sensitivity:")
    print(s["lagged"])
    print()
    print("Uzbekistan participation sensitivity:")
    print(s["participation"])
    print()
    print("Complete-case sensitivity:")
    print(s["complete_case"])
    print()
    print("Kyrgyzstan inference:")
    print(s["kg"])
    print()
    print("Literature verification:")
    print(s["literature"])
    print()
    print("Claims manuscript-ready:")
    print(s["claims_ready"])
    print()
    print("Publication readiness:")
    print(s["readiness"])
    print()
    print("Recommended next step:")
    print(s["next"])
    print()
    print("Files for supervisor review:")
    print()
    for p in [
        "outputs/checkpoints/PHASE_07_LIMITED_ROBUSTNESS.md",
        "outputs/checkpoints/phase_07_round_sensitive_inference.csv",
        "outputs/checkpoints/phase_07_lagged_models.csv",
        "outputs/checkpoints/phase_07_participation_sensitivity.csv",
        "outputs/checkpoints/phase_07_complete_case_sensitivity.csv",
        "outputs/checkpoints/phase_07_kyrgyzstan_inference_confirmation.csv",
        "outputs/checkpoints/phase_07_claim_citation_audit.csv",
        "outputs/checkpoints/phase_07_publication_readiness.csv",
        "research/l2cu_weight_decision.md",
        "literature/drafts/literature_review_v4_verified.md",
        "manuscript/final_evidence_hierarchy.md",
        "manuscript/manuscript_freeze_record.yaml",
    ]:
        print(f"- {p}")
    print()
    print("Waiting for supervisor approval before manuscript preparation.")
