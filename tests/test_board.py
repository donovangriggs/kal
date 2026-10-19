"""Tests for board/state.py: what the Board shows, built from a real Run's files."""
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "board"))
from state import findings, state, summary  # noqa: E402
from test_bin import Repo, kal  # noqa: E402

REPORT = """# reviewer report: ticket 01, round 1
One blocking finding: renewals ignore holds.
## Blocking findings
- [HIGH] loans.py:4: renew ignores holds. Failure: held book -> renewed. Fix: check holds first.
## Non-blocking findings
- [LOW] loans.py:1: magic number 2
## Assumptions
none
Verdict: CHANGES
At: abc1234def
"""


class Parsing(unittest.TestCase):
    def test_findings_know_blocking_from_non_blocking(self):
        self.assertEqual([(f["severity"], f["blocking"]) for f in findings(REPORT)], [("HIGH", True), ("LOW", False)])

    def test_summary_is_the_outcome_line(self):
        self.assertEqual(summary(REPORT), "One blocking finding: renewals ignore holds.")


class BoardState(Repo):
    def test_a_live_run_with_a_step_and_its_diff(self):
        kal("kal-start", str(self.run_dir), cwd=self.repo)
        t = self.ticket()
        kal("kal-begin", str(t), cwd=self.repo)
        self.commit(Path(self.text(t, "Worktree")), "renew.txt", "ok\n")
        rd = self.run_dir / "reports" / "01" / "round-1"
        rd.mkdir(parents=True)
        (rd / "reviewer-brief.txt").write_text("brief")
        time.sleep(0.05)
        (rd / "review.md").write_text(REPORT)

        run = state(self.repo)["runs"][0]
        self.assertEqual((run["feature"], run["state"]), ("loans", "active"))
        ticket = run["tickets"][0]
        step = ticket["steps"][0]
        self.assertEqual((step["name"], step["role"], step["verdict"], step["at"]), ("reviewer", "reviewer", "CHANGES", "abc1234"))
        self.assertEqual(ticket["diff"]["files"], 1)
        self.assertEqual(run["findings"], {"HIGH": 1, "LOW": 1})

    def test_no_runs_is_an_empty_board(self):
        self.assertEqual(state(self.repo)["runs"], [])


if __name__ == "__main__":
    unittest.main()


class Filed(unittest.TestCase):
    def test_filed_lines_parse(self):
        from state import filed
        text = "# Run\n\n## Log\n\nx\n\n## Filed\n\n- 14: Guard slugs | backlog | .scratch/s/issues/14-a.md\n- just a note\n"
        self.assertEqual(filed(text), [
            {"nn": "14", "title": "Guard slugs", "status": "backlog", "ref": ".scratch/s/issues/14-a.md"},
            {"nn": None, "title": "just a note", "status": None, "ref": None}])


class Decided(unittest.TestCase):
    def test_decided_lines_parse(self):
        from state import filed
        text = "# Run\n\n## Decided\n\n- 12: thumb 400w WebP | 446 KB measured, passes | reports/12/round-1/dev.md\n"
        self.assertEqual(filed(text, "Decided"), [{"nn": "12", "title": "thumb 400w WebP",
                                                   "status": "446 KB measured, passes", "ref": "reports/12/round-1/dev.md"}])
