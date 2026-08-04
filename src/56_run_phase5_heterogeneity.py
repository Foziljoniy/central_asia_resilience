"""Run limited prespecified Phase 5 heterogeneity checks."""
from phase5_common import estimate_models, heterogeneity, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); data=read_data(); heterogeneity(estimate_models(data), data)
