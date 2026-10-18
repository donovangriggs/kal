"""Tests for bin/: the git guard, kal-set, kal-verify, kal-start, kal-begin and kal-merge, against throwaway git
repos. Run: python3 -m unittest discover -s tests"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "bin"
CONFIG = Path(tempfile.mkdtemp(prefix="kal-test-config-"))  # a Claude config that trusts every folder
(CONFIG / ".claude.json").write_text(json.dumps({"projects": {"/": {"hasTrustDialogAccepted": True}}}))
ENV = {**os.environ, "CLAUDE_CONFIG_DIR": str(CONFIG), "TMUX_PANE": "%0", "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "RTK_DISABLED": "1"}


def sh(*cmd, cwd, check=True, env=ENV):
    r = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)
    if check and r.returncode:
        raise AssertionError(f"{cmd} failed ({r.returncode}): {r.stdout}{r.stderr}")
    return r


def kal(name, *args, cwd, env=ENV):
    return subprocess.run([str(BIN / name), *args], cwd=cwd, env=env, text=True, capture_output=True)


def guard(command):
    return subprocess.run([str(BIN / "_kal_guard.py")], input=json.dumps({"tool_input": {"command": command}}),
                          text=True, capture_output=True).returncode


class Guard(unittest.TestCase):
    def test_blocks_destructive_git(self):
        for c in ["git stash", "git reset --hard HEAD~1", "git clean -fd", "git checkout -- src/a.ts", "git checkout .",
                  "git restore src/a.ts", "git switch -f main", "git branch -D x", "git commit --amend",
                  "git push --force", "git push -f origin x", "git push origin +x",
                  "rtk git reset --hard", "rtk proxy git stash", "cd x && git -C /tmp/w clean -n",
                  "FOO=1 git stash pop"]:
            self.assertEqual(guard(c), 2, c)

    def test_allows_safe_git_and_message_text(self):
        for c in ["git status", "git commit -m 'Remove the stash button'", "git checkout --ours -- a.ts",
                  "git restore --staged a.ts", "git branch -d done", "git push origin x", "npm test",
                  "git commit -F - <<'EOF'\ngit reset --hard is mentioned here\nEOF"]:
            self.assertEqual(guard(c), 0, c)


class Repo(unittest.TestCase):
    """A main checkout on `main` with kal's setup done: docs/agents/, a Commands block, .kal/ ignored."""
    verify = "true"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="kal-test-"))
        self.repo = self.tmp / "app"
        self.repo.mkdir()
        sh("git", "init", "-q", "-b", "main", cwd=self.repo)
        (self.repo / "docs" / "agents").mkdir(parents=True)
        (self.repo / "docs" / "agents" / "issue-tracker.md").write_text("local\n")
        (self.repo / ".gitignore").write_text(".kal/\n")
        (self.repo / "CLAUDE.md").write_text(
            f"# app\n\n## Commands\n\n- Verify: `{self.verify}`\n- Dev server: `none`\n- Teardown: `none`\n"
            "- Worktree setup: `none`\n")
        (self.repo / "loans.txt").write_text("renew\n")
        sh("git", "add", "-A", cwd=self.repo)
        sh("git", "commit", "-qm", "init", cwd=self.repo)
        self.run_dir = self.repo / ".kal" / "runs" / "loans"

    def tearDown(self):
        sh("rm", "-rf", str(self.tmp), cwd="/")

    def ticket(self, nn="01", status="ready"):
        path = self.run_dir / "tickets" / f"{nn}-renew.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {nn}: Renew a loan\n\nStatus: {status}\nSize: small\n\n## Acceptance criteria\n\n"
                        "- [ ] a member can renew\n\n## Log\n")
        return path

    def report(self, t, role_file, verdict, at, k=1):
        d = self.run_dir / "reports" / t.name[:2] / f"round-{k}"
        d.mkdir(parents=True, exist_ok=True)
        (d / role_file).write_text(f"# report\n\nVerdict: {verdict}\nAt: {at}\n")

    def started(self):
        r = kal("kal-start", str(self.run_dir), cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stdout)
        t = self.ticket()
        r = kal("kal-begin", str(t), cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stdout)
        return t, Path(self.text(t, "Worktree"))

    @staticmethod
    def text(path, key):
        return next(l.split(":", 1)[1].strip() for l in path.read_text().splitlines() if l.startswith(f"{key}:"))

    def commit(self, wt, name, body):
        (wt / name).write_text(body)
        sh("git", "add", name, cwd=wt)
        sh("git", "commit", "-qm", f"add {name}", cwd=wt)
        return sh("git", "rev-parse", "HEAD", cwd=wt).stdout.strip()


class Set(Repo):
    def test_header_log_and_workers(self):
        t = self.ticket()
        kal("kal-set", str(t), "Status=in-dev", "Round=1", "--log", "started", cwd=self.repo)
        kal("kal-set", str(t), "--worker", "reviewer sonnet %3 10:00", "--worker", "qa sonnet %4 10:00", cwd=self.repo)
        kal("kal-set", str(t), "--no-worker", "reviewer", cwd=self.repo)
        text = t.read_text()
        self.assertIn("Status: in-dev", text)
        self.assertIn("Round: 1", text)
        self.assertIn("Workers: qa sonnet %4 10:00", text)
        self.assertRegex(text, r"## Log\n\n?\d{4}-\d\d-\d\d \d\d:\d\d started")


class Verify(Repo):
    def test_pass_then_reuse_at_same_commit(self):
        logs = self.tmp / "logs"
        self.assertEqual(kal("kal-verify", str(self.repo), str(logs), cwd=self.repo).returncode, 0)
        r = kal("kal-verify", str(self.repo), str(logs), cwd=self.repo)
        self.assertEqual(r.returncode, 0)
        self.assertIn("reused", r.stdout)

    def test_reuse_ignores_kal_and_scratch_changes(self):
        logs = self.tmp / "logs"
        kal("kal-verify", str(self.repo), str(logs), cwd=self.repo)
        (self.repo / ".scratch").mkdir()
        self.commit(self.repo, ".scratch/t.md", "ticket\n")
        self.assertIn("reused", kal("kal-verify", str(self.repo), str(logs), cwd=self.repo).stdout)


class VerifyRed(Repo):
    verify = "false"

    def test_red_exits_nonzero(self):
        r = kal("kal-verify", str(self.repo), str(self.tmp / "logs"), cwd=self.repo)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("FAIL", r.stdout)

    def test_start_refuses_a_red_base(self):
        r = kal("kal-start", str(self.run_dir), cwd=self.repo)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Verify is red", r.stdout)


class Start(Repo):
    def test_needs_tmux(self):
        env = {k: v for k, v in ENV.items() if k != "TMUX_PANE"}
        r = kal("kal-start", str(self.run_dir), cwd=self.repo, env=env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("tmux new", r.stdout)

    def test_needs_folder_trust(self):
        config = self.tmp / "config"
        config.mkdir()
        (config / ".claude.json").write_text(json.dumps({"projects": {}}))
        r = kal("kal-start", str(self.run_dir), cwd=self.repo, env={**ENV, "CLAUDE_CONFIG_DIR": str(config)})
        self.assertEqual(r.returncode, 1)
        self.assertIn("trusted", r.stdout)

    def test_needs_setup(self):
        sh("rm", "-rf", "docs", cwd=self.repo)
        self.assertEqual(kal("kal-start", str(self.run_dir), cwd=self.repo).returncode, 3)

    def test_first_start_then_resume_while_a_ticket_is_live(self):
        r = kal("kal-start", str(self.run_dir), cwd=self.repo)
        self.assertIn("first start: base branch main", r.stdout)
        self.ticket(status="in-review")
        self.assertIn("resume", kal("kal-start", str(self.run_dir), cwd=self.repo).stdout)

    def test_reuses_an_idle_single_ticket_run(self):
        kal("kal-start", str(self.run_dir), cwd=self.repo)
        self.ticket(status="merged")
        self.assertIn("Run folder reused", kal("kal-start", str(self.run_dir), cwd=self.repo).stdout)


class Begin(Repo):
    def test_cuts_branch_and_worktree(self):
        t, wt = self.started()
        self.assertTrue(wt.is_dir())
        self.assertEqual(sh("git", "branch", "--show-current", cwd=wt).stdout.strip(), "kal/loans-01")
        self.assertEqual(self.text(t, "Status"), "in-dev")
        self.assertIn("resume", kal("kal-begin", str(t), cwd=self.repo).stdout)

    def test_clones_node_modules_when_lockfile_matches(self):
        (self.repo / "package-lock.json").write_text("{}\n")
        (self.repo / ".gitignore").write_text(".kal/\nnode_modules/\n")
        sh("git", "add", "package-lock.json", ".gitignore", cwd=self.repo)
        sh("git", "commit", "-qm", "lock", cwd=self.repo)
        (self.repo / "node_modules" / "left-pad").mkdir(parents=True)
        (self.repo / "node_modules" / "left-pad" / "index.js").write_text("x\n")
        t, wt = self.started()
        self.assertTrue((wt / "node_modules" / "left-pad" / "index.js").is_file())


class Merge(Repo):
    def test_refuses_without_a_reviewer_pass(self):
        t, wt = self.started()
        self.assertEqual(kal("kal-merge", str(t), cwd=self.repo).returncode, 3)
        head = self.commit(wt, "renew.txt", "ok\n")
        self.report(t, "review.md", "CHANGES", head)
        self.assertEqual(kal("kal-merge", str(t), cwd=self.repo).returncode, 3)

    def test_merges_on_pass_and_cleans_up(self):
        t, wt = self.started()
        head = self.commit(wt, "renew.txt", "ok\n")
        self.report(t, "review.md", "PASS", head)
        self.report(t, "qa.md", "PASS", head)
        r = kal("kal-merge", str(t), cwd=self.repo)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertTrue((self.repo / "renew.txt").is_file())
        self.assertFalse(wt.exists())
        self.assertEqual(self.text(t, "Status"), "merged")

    def test_an_earlier_pass_stands_after_a_fix_round(self):
        t, wt = self.started()
        first = self.commit(wt, "renew.txt", "v1\n")
        self.report(t, "review.md", "PASS", first)
        self.report(t, "qa.md", "CHANGES", first)
        fixed = self.commit(wt, "renew.txt", "v2\n")
        self.report(t, "qa.md", "PASS", fixed, k=2)
        self.assertEqual(kal("kal-merge", str(t), cwd=self.repo).returncode, 0)

    def test_conflict_with_base_aborts(self):
        t, wt = self.started()
        head = self.commit(wt, "loans.txt", "branch\n")
        self.report(t, "review.md", "PASS", head)
        self.commit(self.repo, "loans.txt", "main\n")
        r = kal("kal-merge", str(t), cwd=self.repo)
        self.assertEqual(r.returncode, 4, r.stdout)
        self.assertEqual(sh("git", "status", "--porcelain", cwd=wt).stdout, "")


class MergeRed(Repo):
    verify = "test ! -f broken.txt"

    def test_red_verify_blocks_merge(self):
        t, wt = self.started()
        head = self.commit(wt, "broken.txt", "x\n")
        self.report(t, "review.md", "PASS", head)
        r = kal("kal-merge", str(t), cwd=self.repo)
        self.assertEqual(r.returncode, 5, r.stdout)
        self.assertFalse((self.repo / "broken.txt").exists())


if __name__ == "__main__":
    unittest.main()
