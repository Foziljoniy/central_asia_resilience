"""Run Uzbekistan lagged sensitivity."""
from phase7_common import lagged_sensitivity, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); lagged_sensitivity(read_data())
