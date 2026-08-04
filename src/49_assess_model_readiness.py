"""Phase 4V model-readiness assessment entry point."""
from phase4_common import findings_and_readiness, kazakhstan_outputs, kyrgyzstan_outputs, load_data, setup_logging, uzbekistan_outputs

if __name__ == "__main__":
    setup_logging()
    data = load_data()
    kg = kyrgyzstan_outputs(data)
    uz = uzbekistan_outputs(data)
    kz = kazakhstan_outputs(data)
    findings_and_readiness(data, kg, uz, kz)
