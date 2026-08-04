"""Phase 4D sample-flow validation entry point."""
from phase4_common import load_data, sample_flow, setup_logging

if __name__ == "__main__":
    setup_logging()
    sample_flow(load_data())
