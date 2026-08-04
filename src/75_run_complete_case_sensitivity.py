"""Run complete-case sensitivity audit."""
from phase7_common import complete_case, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); complete_case(read_data())
