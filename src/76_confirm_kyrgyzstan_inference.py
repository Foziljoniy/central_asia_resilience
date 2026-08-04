"""Confirm Kyrgyzstan inference."""
from phase7_common import kyrgyzstan_confirm, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); kyrgyzstan_confirm(read_data())
