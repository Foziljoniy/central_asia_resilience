"""Phase 4F FIES measurement validation entry point."""
from phase4_common import fies_quality, load_data, setup_logging

if __name__ == "__main__":
    setup_logging()
    fies_quality(load_data())
