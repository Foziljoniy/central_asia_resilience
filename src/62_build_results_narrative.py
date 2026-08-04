"""Build manuscript results narrative."""
from phase6_common import read_sources, results_core, setup_logging
if __name__ == "__main__":
    setup_logging(); results_core(read_sources())
