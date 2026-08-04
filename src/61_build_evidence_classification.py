"""Build Phase 6 evidence classification."""
from phase6_common import evidence_classification, read_sources, setup_logging
if __name__ == "__main__":
    setup_logging(); evidence_classification(read_sources())
