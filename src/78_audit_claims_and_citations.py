"""Audit Phase 7 claims and citations."""
from phase7_common import claims_audit, literature_verify, setup_logging
if __name__ == "__main__":
    setup_logging(); claims_audit(literature_verify())
