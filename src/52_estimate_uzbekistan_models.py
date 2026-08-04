"""Estimate Uzbekistan Phase 5 models through the shared pipeline."""
from phase5_common import estimate_models, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); estimate_models(read_data())
