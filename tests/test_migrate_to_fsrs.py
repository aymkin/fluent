#!/usr/bin/env python3
"""Run: python3 tests/test_migrate_to_fsrs.py"""
import json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude" / "hooks"))
import migrate_to_fsrs as m

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".claude" / "hooks" / "migrate_to_fsrs.py"


class TestSeed(unittest.TestCase):
    def test_reviewed_card_seeded_from_interval(self):
        card = {"interval_days": 48, "easiness_factor": 2.5, "repetitions": 3}
        s, d = m.seed(card)
        self.assertAlmostEqual(s, 48.0, delta=0.5)
        self.assertGreaterEqual(d, 1.0)
        self.assertLessEqual(d, 10.0)

    def test_never_reviewed_card_stays_null(self):
        card = {"interval_days": 1, "easiness_factor": 2.5, "repetitions": 0}
        s, d = m.seed(card)
        self.assertIsNone(s)
        self.assertIsNone(d)


class TestMainStampsMetadata(unittest.TestCase):
    """Runs main() out-of-process (subprocess) so fluent_paths' cached data_dir()
    can't leak into / be leaked from the real ~/.claude/fluent-data."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fluent-test-"))
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "spaced-repetition.json").write_text(json.dumps({
            "metadata": {"algorithm": "SM-2", "total_items_tracked": 1},
            "items": {"vocab_dag": {"interval_days": 6, "easiness_factor": 2.4,
                                     "repetitions": 2, "stability": None,
                                     "fsrs_difficulty": None}},
        }))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self):
        # FLUENT_DATA_DIR pins the target explicitly (rung 1 of fluent_paths'
        # resolution order) so a missing/incomplete fixture can never silently
        # fall through to the real ~/.claude/fluent-data.
        env = {**os.environ, "FLUENT_DATA_DIR": str(self.tmp / "data")}
        proc = subprocess.run(["python3", str(SCRIPT)], cwd=str(self.tmp),
                              env=env, capture_output=True)
        self.assertEqual(proc.returncode, 0, msg=f"stderr={proc.stderr!r}")
        return json.loads((self.tmp / "data" / "spaced-repetition.json").read_text())

    def test_stamps_algorithm_and_scheduler(self):
        sr = self._run()
        self.assertEqual(sr["metadata"]["algorithm"], "FSRS-6")
        self.assertEqual(sr["metadata"]["scheduler"], "fsrs-6")

    def test_rerun_is_idempotent_and_keeps_label(self):
        self._run()
        sr = self._run()
        self.assertEqual(sr["metadata"]["algorithm"], "FSRS-6")
        self.assertEqual(sr["items"]["vocab_dag"]["stability"], 6.0)


if __name__ == "__main__":
    unittest.main()
