"""Phase 4C input validation entry point."""
from phase4_common import input_validation, load_data, setup_logging

if __name__ == "__main__":
    setup_logging()
    input_validation(load_data())
