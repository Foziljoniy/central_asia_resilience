"""Phase 4Q-R Kazakhstan benchmark entry point."""
from phase4_common import kazakhstan_outputs, load_data, setup_logging

if __name__ == "__main__":
    setup_logging()
    kazakhstan_outputs(load_data())
