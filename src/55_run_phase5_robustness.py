"""Run prespecified Phase 5 robustness checks."""
from phase5_common import estimate_models, read_data, robustness, setup_logging
if __name__ == "__main__":
    setup_logging(); data=read_data(); robustness(estimate_models(data), data)
