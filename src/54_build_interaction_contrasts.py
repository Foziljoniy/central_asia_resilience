"""Build Phase 5 interaction contrasts."""
from phase5_common import build_predictions_and_contrasts, estimate_models, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); build_predictions_and_contrasts(estimate_models(read_data()))
