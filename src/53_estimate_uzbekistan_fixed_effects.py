"""Estimate Uzbekistan household fixed-effects robustness when feasible."""
from phase5_common import fixed_effects_uz, read_data, setup_logging
if __name__ == "__main__":
    setup_logging(); fixed_effects_uz(read_data())
