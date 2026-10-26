"""Helpers shared by the Python kal-* commands. A script imports it from its own folder (`from _kal import ...`):
Python puts a script's folder first on sys.path. The leading underscore keeps it off the kal-* command space."""
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # the plugin root (CLAUDE_PLUGIN_ROOT isn't set on the Bash PATH)

# Role -> its report's file name (without .md) in the round folder.
REPORT = {"developer": "dev", "reviewer": "review", "qa": "qa", "security": "security",
          "bug-fixer": "fix", "merger": "merge"}
CHECKS = ("reviewer", "qa", "security")

# Each Role's dev-server port as an offset in the Ticket's block, so Roles running side by side never collide.
PORT_OFFSET = {"developer": 0, "bug-fixer": 0, "qa": 1, "reviewer": 2, "security": 3, "merger": 3}
QA_BASELINE = 4
# Each Role's color, the Board's dark-mode palette (board/index.html --dev, --rev, ...: change both together).
# kal-worker paints each Worker's tmux pane border and title with it.
ROLE_COLOR = {"developer": "#8b85ff", "reviewer": "#3cc2c2", "qa": "#f0a43c", "security": "#ef6a8a",
              "bug-fixer": "#a88bef", "merger": "#3fbf6a"}  # QA's spare: a baseline server from the base branch's checkout
# herdr has no pane colors: a Worker's pane label starts with its Role's nearest colored emoji instead.
ROLE_MARK = {"developer": "🟣", "reviewer": "🔵", "qa": "🟠", "security": "🔴", "bug-fixer": "🟪", "merger": "🟢"}
COMMAND_KEYS = ("Verify", "Quick check", "Dev server", "Teardown", "Worktree setup")


def run(*cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def git(*args, cwd):
    return run("git", *args, cwd=cwd).stdout.strip()


def stop(code, msg):
    print(msg)
    sys.exit(code)


def _lines(key, text):
    return re.findall(rf"^(?:\*\*)?{re.escape(key)}:(?:\*\*)?[ \t]*(.*?)[ \t]*$", text, re.M)


def field(key, text):
    """A header line `Key: value` (plain or bold) of a Ticket or Run file; None if absent. Only the header counts
    (the text before the first `## ` heading), and the first match wins."""
    found = _lines(key, re.split(r"^## ", text, maxsplit=1, flags=re.M)[0])
    return found[0] if found else None


def report_field(key, text):
    """A report's last `Key: value` line (`Verdict:`, `At:`), anywhere in it; None if absent."""
    found = _lines(key, text)
    return found[-1] if found else None


def commands(checkout):
    """The `## Commands` block as {key: command}; `none`, `TODO` or missing -> None. Always read from the MAIN
    checkout's CLAUDE.md, whichever worktree is asked about, so a change to the repo's commands applies at once,
    mid-Run (a worktree cut earlier still has the old block)."""
    main = repo_of(checkout) if Path(checkout).is_dir() else None
    md = (main or Path(checkout)) / "CLAUDE.md"
    text = md.read_text() if md.is_file() else ""
    out = {}
    for key in COMMAND_KEYS:
        m = re.search(rf"^- {re.escape(key)}[^`\n]*`([^`]+)`", text, re.M)
        cmd = m[1].strip() if m else ""
        out[key] = None if cmd.lower() in ("", "none", "todo") else cmd
    return out


def kal_loaded(repo):
    """kal is installed for this repo (user scope, or project/local scope for this path) and not disabled in the
    user, project or local settings: a `claude` started in the repo loads it. Enabled-but-not-installed (a fresh
    clone before `claude plugin install`) doesn't count."""
    cfg = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        installed = json.loads((cfg / "plugins" / "installed_plugins.json").read_text()).get("plugins", {})
    except (OSError, ValueError):
        installed = {}
    found = any(key.split("@")[0] == "kal" and (e.get("scope") == "user" or e.get("projectPath") == str(repo))
                for key, entries in installed.items() for e in entries)
    enabled = None
    for f in (cfg / "settings.json", repo / ".claude" / "settings.json", repo / ".claude" / "settings.local.json"):
        try:
            for key, on in json.loads(f.read_text()).get("enabledPlugins", {}).items():
                if key.split("@")[0] == "kal":
                    enabled = bool(on)
        except (OSError, ValueError):
            pass
    return found and enabled is not False


def repo_of(path):
    """The main checkout that owns `path` (works from any worktree)."""
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=path)
    return Path(common).parent if common else None


def numbers(line):
    """Ticket numbers in a `Blocked by:` / `Waits on:` line: every standalone number ("01, 03" -> ["01", "03"]);
    "none" or an empty line -> []."""
    return [f"{int(n):02d}" for n in re.findall(r"\b(\d+)\b", line or "")]


def tickets(run_dir):
    """Every Ticket mirror of a Run except the end-of-spec Ticket 00, lowest number first."""
    return [Ticket(p) for p in sorted((Path(run_dir) / "tickets").glob("[0-9]*.md")) if not p.name.startswith("00-")]


class Ticket:
    """A Ticket mirror at <repo>/.kal/runs/<feature>/tickets/NN-<slug>.md and everything derived from it."""

    def __init__(self, path):
        self.path = Path(path).resolve()
        self.text = self.path.read_text()
        self.nn = self.path.name.split("-")[0]
        self.run_dir = self.path.parent.parent
        self.feature = self.run_dir.name
        self.repo = self.run_dir.parent.parent.parent
        self.run_md = self.run_dir / "run.md"
        title = re.search(r"^# (?:\d+:\s*)?(.*)$", self.text, re.M)
        self.title = title[1].strip() if title else self.nn
        self.round = int(field("Round", self.text) or 0) or 1
        self.branch = field("Branch", self.text) or f"kal/{self.feature}-{self.nn}"
        self.worktree = field("Worktree", self.text) or str(self.repo.parent / f"{self.repo.name}-kal" /
                                                            f"{self.feature}-{self.nn}")
        run_text = self.run_md.read_text() if self.run_md.exists() else ""
        # A Ticket's own `Base branch:` wins: the end-of-spec Ticket 00 builds on the integration branch and
        # merges into the target, while every other Ticket merges into the Run's base (the integration branch).
        self.base = field("Base branch", self.text) or field("Base branch", run_text)
        self.status = field("Status", self.text) or "ready"
        self.blocked_by = numbers(field("Blocked by", self.text))
        self.waits_on = numbers(field("Waits on", self.text))
        self.workers = [w.split() for w in (field("Workers", self.text) or "").split(",") if w.strip()]
        self.block = 5100 + 10 * int(self.nn)

    def round_dir(self, k=None):
        return self.run_dir / "reports" / self.nn / f"round-{k or self.round}"

    def reports(self, role):
        """Every report this Role wrote for the Ticket, oldest round first: [(round, path)]."""
        name = REPORT[role] + ".md"
        found = []
        for d in (self.run_dir / "reports" / self.nn).glob("round-*"):
            if (d / name).is_file() and d.name[6:].isdigit():
                found.append((int(d.name[6:]), d / name))
        return sorted(found)


def worktrees(repo):
    """{branch: worktree path} for every worktree of the repo, from git (the truth, not the Ticket's lines)."""
    out = {}
    for block in git("worktree", "list", "--porcelain", cwd=repo).split("\n\n"):
        wt = re.search(r"^worktree (.*)$", block, re.M)
        ref = re.search(r"^branch refs/heads/(.*)$", block, re.M)
        if wt and ref:
            out[ref[1]] = wt[1]
    return out


def dirty(checkout):
    """Uncommitted paths in a checkout, ignoring kal's run folder and the local tracker's folder."""
    out = run("git", "status", "--porcelain", "--", ".", ":(exclude).kal", ":(exclude).scratch", cwd=checkout)
    return [l[3:] for l in out.stdout.splitlines()]


def covers(at, head, base, cwd):
    """A PASS at `at` still holds for `head`: it is the head, or every commit after it that `base` lacks is a
    clean automatic merge (its tree is exactly what `git merge-tree` makes of its two parents, no conflict).
    A hand-resolved merge, or any other commit, brings in content nobody checked."""
    at = git("rev-parse", "--verify", "-q", f"{at}^{{commit}}", cwd=cwd)
    if not at or run("git", "merge-base", "--is-ancestor", at, head, cwd=cwd).returncode:
        return False
    for line in git("rev-list", "--parents", f"{at}..{head}", f"^{base}", cwd=cwd).splitlines():
        sha, *parents = line.split()
        merged = run("git", "merge-tree", "--write-tree", *parents, cwd=cwd) if len(parents) == 2 else None
        if not merged or merged.returncode or merged.stdout.split()[0] != git("rev-parse", f"{sha}^{{tree}}", cwd=cwd):
            return False
    return True


LOCKS = ("pnpm-lock.yaml", "package-lock.json", "yarn.lock", "bun.lock", "bun.lockb")


def prepare(repo, wt):
    """Ready a fresh worktree's dependencies. node_modules is cloned from the main checkout (APFS copy-on-write:
    instant, no extra disk) when both trees hold the same lockfile; otherwise the Commands block's `Worktree
    setup` runs there. Returns what it did; raises RuntimeError when Worktree setup fails or times out."""
    import filecmp
    repo, wt = Path(repo), Path(wt)
    lock = next((l for l in LOCKS if (repo / l).is_file()), None)
    src = repo / "node_modules"
    # ponytail: root node_modules only; per-package node_modules in a monorepo fall back to Worktree setup.
    if lock and src.is_dir() and (wt / lock).is_file() and filecmp.cmp(repo / lock, wt / lock, False) \
            and run("cp", "-cR", str(src), str(wt / "node_modules"), cwd=repo).returncode == 0:
        return "cloned node_modules"
    setup = commands(wt)["Worktree setup"]
    if not setup:
        return "none"
    try:
        s = subprocess.run(["sh", "-c", setup], cwd=wt, timeout=900, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Worktree setup timed out after 15 minutes in {wt}")
    if s.returncode:
        raise RuntimeError(f"Worktree setup failed in {wt}: {(s.stderr or s.stdout).strip().splitlines()[-1:] or '?'}")
    return "Worktree setup"


def settle(ticket_file, timeout=300):
    """Wait until no kal-worker process for this Ticket is alive. A Worker's pane closes before its kal-worker
    finishes: it still runs Teardown and sweeps the Ticket's port block, which would kill servers a Verify
    started meanwhile (a merge right after the last check). True once settled, False on timeout."""
    pattern = f"kal-worker .*{re.escape(Path(ticket_file).name)}"
    end = time.time() + timeout
    while time.time() < end:
        if subprocess.run(["pgrep", "-f", pattern], capture_output=True).returncode:
            return True
        time.sleep(1)
    return False


def teardown(worktree, port):
    """Run the Commands block's Teardown in the worktree, once per Role port when it names {port}, then kill
    whatever still listens on the port block (port to port+9)."""
    cmd = commands(worktree)["Teardown"] if Path(worktree).is_dir() else None
    if cmd:
        offsets = sorted({*PORT_OFFSET.values(), QA_BASELINE}) if "{port}" in cmd else [0]
        for off in offsets:
            try:
                subprocess.run(["sh", "-c", cmd.replace("{port}", str(port + off))], cwd=worktree, timeout=300,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                pass
    for sig in (signal.SIGTERM, signal.SIGKILL):  # KILL only what ignored TERM for 2s
        for pid in listeners(port):
            try:
                os.kill(int(pid), sig)
            except ProcessLookupError:
                pass
        for _ in range(20):
            if not listeners(port):
                return
            time.sleep(0.1)


def listeners(port):
    """Pids listening on the port block, on any address (a dev server may bind *, ::1 or 127.0.0.1)."""
    return subprocess.run(["lsof", "-t", "-n", "-P", f"-iTCP:{port}-{port + 9}", "-sTCP:LISTEN"],
                          capture_output=True, text=True).stdout.split()
