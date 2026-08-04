"""Validate approved Phase 6 result sources."""
from phase6_common import read_sources, setup_logging, validate_results
if __name__ == "__main__":
    setup_logging(); validate_results(read_sources())
