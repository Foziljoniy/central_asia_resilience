"""Run Uzbekistan round-sensitive inference."""
from phase7_common import read_data, round_sensitive, setup_logging
if __name__ == "__main__":
    setup_logging(); round_sensitive(read_data())
