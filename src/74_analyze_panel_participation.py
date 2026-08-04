"""Analyze Uzbekistan panel participation."""
from phase7_common import participation, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); participation(read_data())
