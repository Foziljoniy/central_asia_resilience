"""Phase 4K-P Uzbekistan descriptive entry point."""
from phase4_common import load_data, setup_logging, uzbekistan_outputs

if __name__ == "__main__":
    setup_logging()
    uzbekistan_outputs(load_data())
