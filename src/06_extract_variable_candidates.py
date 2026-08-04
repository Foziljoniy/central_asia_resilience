"""Phase 1F-G: create provisional candidates and compatibility matrix."""

from phase1_common import build_country_compatibility_matrix, extract_variable_candidates


if __name__ == "__main__":
    extract_variable_candidates()
    build_country_compatibility_matrix()
