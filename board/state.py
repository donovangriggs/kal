"""The Board's state: every Run of a repo, as one JSON document, built from the files a Run keeps.

    python3 board/state.py <repo>      prints the state as JSON (what /state.json serves)

Sources, all read-only: .kal/runs/<feature>/ (run.md, Ticket mirrors, round folders), git (diff stats, commits),
tmux (which Worker panes are open) and Worker transcripts (each live Worker's latest action). The timeline comes
from file times, not log text: kal-worker writes a Worker's brief as it starts, and the Worker's report is written
as it ends.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
from _kal import REPORT, Ticket, field, report_field  # noqa: E402

ROLE_OF = {name: role for role, name in REPORT.items()} | {"standards": "reviewer"}
STALE = 900  # a heartbeat older than this (seconds) and no open pane: the Run isn't running


def sh(*cmd, cwd=None):
    try:
        return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def stamp(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t)) if t else None


def findings(text):
    """[{severity, text, blocking}] from a report's Blocking / Non-blocking sections."""
    out, blocking = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            head = line[3:].strip().lower()
            blocking = True if head.startswith("blocking") else False if head.startswith("non-blocking") else None
            continue
        m = re.match(r"^\s*[-*]\s*\[([A-Za-z]+)\]\s*(.*)", line)
        if m and blocking is not None:
            out.append({"severity": m[1].upper(), "text": m[2].strip(), "blocking": blocking})
    return out


def summary(text):
    """A report's one-sentence outcome: the first non-empty line after its title."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return next((l for l in lines[1:] if not l.startswith(("#", "Verdict:", "At:"))), "")


def filed(text):
    """The tickets a Run filed for later: its run.md `## Filed` lines, `- NN: title | status | ref` (ref: a tracker
    path or URL). Loose on purpose: a line without the separators is kept as a title."""
    body = text.split("\n## Filed", 1)[1].split("\n## ", 1)[0] if "\n## Filed" in text else ""
    out = []
    for line in body.splitlines():
        m = re.match(r"^\s*[-*]\s*(?:(\d+):\s*)?(.*)$", line)
        if not m or not m[2].strip():
            continue
        title, status, ref = (m[2].split(" | ") + ["", ""])[:3]
        out.append({"nn": m[1], "title": title.strip(), "status": status.strip() or None, "ref": ref.strip() or None})
    return out


def latest_action(pane):
    """A live Worker's newest tool call, from its transcript (its session id is in the pane's start command)."""
    m = re.search(r"--session-id (\S+)", sh("tmux", "display", "-p", "-t", pane, "#{pane_start_command}"))
    if not m:
        return None
    cfg = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    found = list(cfg.glob(f"projects/*/{m[1]}.jsonl"))
    if not found:
        return "starting"
    last = None
    with open(found[0]) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            for b in (rec.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    last = b
    if not last:
        return "thinking"
    i = last.get("input") or {}
    target = i.get("description") or i.get("file_path") or i.get("command") or i.get("pattern") or i.get("skill") or ""
    return f"{last.get('name')}: {str(target)[:120]}".rstrip(": ")


def pane_open(pane):
    return bool(pane) and sh("tmux", "display", "-p", "-t", pane, "#{pane_id}") == pane


def ticket_state(t, repo):
    steps, shots, verify = [], [], []
    for rd in sorted((t.run_dir / "reports" / t.nn).glob("round-*"), key=lambda d: int(d.name[6:] or 0)):
        k = int(rd.name[6:])
        for brief in sorted(rd.glob("*-brief.txt"), key=lambda p: p.stat().st_mtime):
            name = brief.name[:-len("-brief.txt")]
            report = rd / f"{REPORT.get(name, name)}.md"
            text = report.read_text() if report.is_file() else ""
            start = brief.stat().st_mtime
            end = report.stat().st_mtime if report.is_file() else None
            steps.append({"name": name, "role": ROLE_OF.get(REPORT.get(name, name), name), "round": k,
                          "verdict": report_field("Verdict", text), "at": (report_field("At", text) or "")[:7] or None,
                          "summary": summary(text), "started": stamp(start), "ended": stamp(end),
                          "seconds": round(end - start) if end else None,
                          "report": str(report.relative_to(repo)) if report.is_file() else None,
                          "findings": findings(text)})
        shots += [str(p.relative_to(repo)) for p in sorted(rd.glob("*.png"))]
        for log in sorted(rd.glob("verify-*.log"), key=lambda p: p.stat().st_mtime):
            last = (log.read_text().strip().splitlines() or [""])[-1]
            verify.append({"round": k, "sha": log.stem[7:], "passed": last == "kal-verify: exit 0",
                           "log": str(log.relative_to(repo))})

    diff = {"files": 0, "insertions": 0, "deletions": 0, "commits": []}
    wt = Path(t.worktree)
    if wt.is_dir() and t.base:
        rng, cwd = (f"{t.base}...HEAD", f"{t.base}..HEAD"), wt
    else:
        grep = f"Merge {t.feature}" if t.nn == "00" else f"Merge {t.nn}: "  # Ticket 00 lands as the whole feature
        merge = sh("git", "log", "--all", "--merges", "--format=%H%x09%s", "-F", f"--grep={grep}", cwd=repo)
        merge = next((l.split("\t")[0] for l in merge.splitlines() if l.split("\t", 1)[-1].startswith(grep)), "")
        rng, cwd = (f"{merge}^1...{merge}^2", f"{merge}^1..{merge}^2") if merge else (None, None), repo
    if rng[0]:
        stat = sh("git", "diff", "--shortstat", rng[0], cwd=cwd)
        for key, pat in (("files", r"(\d+) files? changed"), ("insertions", r"(\d+) insertion"),
                         ("deletions", r"(\d+) deletion")):
            m = re.search(pat, stat)
            diff[key] = int(m[1]) if m else 0
        diff["commits"] = [l.split(" ", 1) for l in sh("git", "log", "--no-merges", "--format=%h %s", rng[1], cwd=cwd).splitlines()]

    workers = [{"role": w[0], "model": w[1] if len(w) > 1 else None, "pane": w[2] if len(w) > 2 else None,
                "since": w[3] if len(w) > 3 else None,
                "action": latest_action(w[2]) if len(w) > 2 and pane_open(w[2]) else None,
                "open": len(w) > 2 and pane_open(w[2])} for w in t.workers]
    log = [l.strip() for l in t.text.split("## Log", 1)[-1].split("\n## ", 1)[0].splitlines()
           if re.match(r"^\d{4}-\d\d-\d\d \d\d:\d\d ", l.strip())] if "## Log" in t.text else []
    return {"nn": t.nn, "title": t.title, "status": t.status, "size": field("Size", t.text), "round": t.round,
            "blocked_by": t.blocked_by, "waits_on": t.waits_on, "discovered_from": field("Discovered from", t.text),
            "source": field("Source", t.text), "branch": t.branch, "steps": steps, "shots": shots, "verify": verify,
            "diff": diff, "workers": workers, "log": log,
            "reason": log[-1][17:] if t.status in ("needs-you", "parked") and log else None}


def run_state(run_dir, repo):
    text = (run_dir / "run.md").read_text()
    paths = sorted((run_dir / "tickets").glob("[0-9]*.md"))
    ts = [ticket_state(Ticket(p), repo) for p in paths]
    real = [t for t in ts if t["nn"] != "00"]
    live = [w for t in ts for w in t["workers"] if w["open"]]
    heartbeat = int(field("Heartbeat", text) or 0)
    if field("Finished", text):
        state = "finished"
    elif live or time.time() - heartbeat < STALE and not (run_dir / "pause").exists():
        state = "paused-finishing" if (run_dir / "pause").exists() else "active"
    elif (run_dir / "pause").exists():
        state = "paused"
    elif any(t["status"] == "needs-you" for t in real):
        state = "needs-you"
    else:
        state = "stopped"
    sev = {}
    for t in ts:
        for s in t["steps"]:
            for f in s["findings"]:
                sev[f["severity"]] = sev.get(f["severity"], 0) + 1
    runlog = [l.strip() for l in text.split("## Log", 1)[-1].splitlines() if re.match(r"^\d{4}-", l.strip())]
    feed = sorted([(l[:16], t["nn"], l[17:]) for t in ts for l in t["log"]] + [(l[:16], "", l[17:]) for l in runlog],
                  reverse=True)
    return {"feature": run_dir.name, "mode": field("Mode", text), "phase": field("Phase", text), "state": state,
            "base": field("Base branch", text), "target": field("Target branch", text),
            "started": field("Started", text), "finished": field("Finished", text),
            "heartbeat": stamp(heartbeat), "context": field("Context", text), "paused": (run_dir / "pause").exists(),
            "counts": {"total": len(real), "merged": sum(t["status"] in ("merged", "dropped") for t in real),
                       "needs_you": sum(t["status"] == "needs-you" for t in real), "live": len(live),
                       "developers": sum(w["role"] == "developer" for w in live), "slots": 3},
            "findings": sev, "tickets": ts, "filed": filed(text),
            "feed": [{"time": a, "ticket": b or None, "text": c} for a, b, c in feed[:200]]}


def state(repo):
    repo = Path(repo).resolve()
    runs_dir = repo / ".kal" / "runs"
    runs = [run_state(d, repo) for d in sorted(runs_dir.iterdir()) if (d / "run.md").is_file()] if runs_dir.is_dir() else []
    order = {"active": 0, "paused-finishing": 1, "needs-you": 2, "paused": 3, "stopped": 4, "finished": 5}
    runs.sort(key=lambda r: (order.get(r["state"], 9), r["started"] or ""), reverse=False)
    return {"repo": str(repo), "name": repo.name, "generated": stamp(time.time()), "runs": runs}


if __name__ == "__main__":
    print(json.dumps(state(sys.argv[1] if len(sys.argv) > 1 else "."), indent=1))
