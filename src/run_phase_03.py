"""Run Phase 3 analytical dataset construction and QA."""

from phase3_common import run_all, stop_message


if __name__ == "__main__":
    result = run_all()
    print(stop_message(result))
