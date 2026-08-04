"""Phase 1I-J: build feasibility evidence and reports without analysis."""

from phase1_common import (
    test_topic_feasibility,
    validate_phase,
    write_main_report,
    write_research_documents,
    write_risk_report,
)


if __name__ == "__main__":
    test_topic_feasibility()
    write_research_documents()
    write_risk_report()
    write_main_report()
    validate_phase()
