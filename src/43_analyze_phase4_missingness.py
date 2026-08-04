"""Phase 4E missingness assessment entry point."""
from phase4_common import load_data, missingness, setup_logging

if __name__ == "__main__":
    setup_logging()
    missingness(load_data())
