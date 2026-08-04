"""Build Kazakhstan year-specific bootstrap uncertainty estimates."""
from phase5_common import kazakhstan_ci, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); kazakhstan_ci(read_data())
