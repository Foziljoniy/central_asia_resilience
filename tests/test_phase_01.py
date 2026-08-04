"""Safety and classification checks for the Phase 1 audit pipeline."""

import csv
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phase1_common import CHECKPOINTS, infer_year, safe_member  # noqa: E402


class PhaseOneTests(unittest.TestCase):
    """Check the invariants most likely to compromise a reproducible audit."""

    def test_archive_member_safety(self) -> None:
        self.assertTrue(safe_member("folder/file.dta")[0])
        self.assertFalse(safe_member("../escape.txt")[0])
        self.assertFalse(safe_member("C:/absolute.txt")[0])
        self.assertFalse(safe_member("/absolute.txt")[0])

    def test_lik_release_year_is_not_survey_year(self) -> None:
        self.assertEqual(infer_year("Version_2022/LiK19_Study_Description.pdf"), "2019")

    def test_required_csvs_have_headers(self) -> None:
        names = [
            "phase_01_archive_inventory.csv",
            "phase_01_dataset_inventory.csv",
            "phase_01_variable_candidates.csv",
            "phase_01_topic_feasibility_matrix.csv",
        ]
        for name in names:
            with self.subTest(name=name):
                with (CHECKPOINTS / name).open("r", encoding="utf-8-sig", newline="") as handle:
                    self.assertTrue(next(csv.reader(handle)))

    def test_requested_raw_directories_remain_empty(self) -> None:
        for country in ("kyrgyzstan", "uzbekistan"):
            self.assertFalse(any(p.is_file() for p in (ROOT / "data" / "raw" / country).rglob("*")))


if __name__ == "__main__":
    unittest.main()
