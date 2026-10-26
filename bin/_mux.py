"""The terminal multiplexer that holds the Worker panes, behind a few functions: kal-worker, kal-start and the Board
call these, never tmux or herdr itself. A pane is the multiplexer's pane id (tmux: `%12`, herdr: `w1:p3`); a function
given a pane tells the backend by the id's shape, the rest by the caller's env."""
import fcntl
import json
import os
import re
import shlex
import socket
import subprocess
import tempfile
import time
import types
from pathlib import Path

# The caller's multiplexer, innermost first: a tmux started inside herdr sets TMUX_PANE (and leaks HERDR_*), and
# herdr strips the TMUX vars from its panes.
BACKEND = "herdr" if not os.environ.get("TMUX_PANE") and os.environ.get("HERDR_ENV") == "1" else "tmux"
HERDR = os.environ.get("HERDR_BIN_PATH") or "herdr"
SOCK = os.environ.get("HERDR_SOCKET_PATH") or os.path.expanduser("~/.config/herdr/herdr.sock")
# Shell commands run in a Worker's pane. tmux: DONE signals the channel kal-done-<pane id> (tmux keeps a signal sent
# before anyone waits); the Stop hook also closes the pane. herdr: the pane closing, or its process exiting, is the
# signal, so DONE has nothing to add.
if BACKEND == "tmux":
    DONE = 'tmux wait-for -S "kal-done-$TMUX_PANE"'
    STOP_HOOK = f'{DONE}; tmux kill-pane -t "$TMUX_PANE"'
else:
    DONE = "exit"
    STOP_HOOK = '"$HERDR_BIN_PATH" pane close "$HERDR_PANE_ID"'


def _tmux(*args):
    return subprocess.run(["tmux", *args], check=True, capture_output=True, text=True).stdout.strip()


def _show(pane, fmt):
    """`fmt` expanded for a pane; empty once the pane is gone (or tmux isn't there), None if tmux didn't answer."""
    try:
        return subprocess.run(["tmux", "display", "-p", "-t", pane, fmt], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except OSError:
        return ""
    except subprocess.TimeoutExpired:
        return None


def _herdr(*args):
    """The CLI's stdout; empty on an error (pane_not_found, server_not_running, ...) or when herdr isn't there."""
    try:
        r = subprocess.run([HERDR, *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout if r.returncode == 0 else ""


def _result(*args):
    out = _herdr(*args)
    return json.loads(out)["result"] if out.strip() else {}


def _connect(method, params):
    """A socket to herdr that has sent one API request."""
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(10)
    try:
        s.connect(SOCK)
        s.sendall((json.dumps({"id": "kal", "method": method, "params": params}) + "\n").encode())
    except OSError:
        s.close()
        raise
    return s


def _rpc(method, **params):
    """One socket API call, for the methods the CLI lacks; its result ({} on an error)."""
    with _connect(method, params) as s:
        return json.loads(s.makefile().readline()).get("result") or {}


def is_herdr(pane):
    return bool(re.fullmatch(r"w\d+:p[0-9A-Za-z]+", pane or ""))


def inside():
    """The caller runs in a multiplexer pane."""
    return bool(os.environ.get("TMUX_PANE")) or os.environ.get("HERDR_ENV") == "1"


def caller():
    return os.environ["HERDR_PANE_ID" if BACKEND == "herdr" else "TMUX_PANE"]


def _panes(node):
    return [node["pane_id"]] if node["type"] == "pane" else _panes(node["first"]) + _panes(node["second"])


def _column(node, me, path=()):
    """(path, node) of the Workers' column in a herdr layout tree: the second side of the innermost `right` split
    whose first side holds the caller `me`; None before the first Worker. `path` leads from the root, True = second."""
    if node["type"] == "pane":
        return None
    inner = _column(node["first"], me, (*path, False)) or _column(node["second"], me, (*path, True))
    if inner or node["direction"] != "right" or me not in _panes(node["first"]):
        return inner
    return (*path, True), node["second"]


def rebalance(root, me):
    """[(path, ratio)] that give every pane in the Workers' column an equal height: the column is a chain of `down`
    splits (each new Worker splits the bottom one), and the k-th of n panes takes 1/(n-k) of what's left."""
    if not (found := _column(root, me)):
        return []
    path, node = found
    chain = []
    while node["type"] == "split" and node["direction"] == "down":
        chain.append(list(path))
        path, node = (*path, True), node["second"]
    return [(p, 1 / (len(chain) + 1 - k)) for k, p in enumerate(chain)]


def _layout():
    """The caller's tab as a tree; a lone pane if herdr won't say (no column: the next Worker splits the caller)."""
    root = _rpc("layout.export", tab_id=os.environ["HERDR_TAB_ID"]).get("layout", {}).get("root")
    return root or {"type": "pane", "pane_id": ""}


def split(cmd, env, cwd, title, color, mark=""):
    """Run the shell command `cmd` in a new pane beside the caller's, without focusing it; returns its pane id. The
    pane gets the multiplexer server's env, not ours: `env` is what it needs. `color` paints the pane's border, and
    its title through @kal_color (the orchestrator's pane has none, so it keeps tmux's default; herdr has no pane
    colors, so its label starts with `mark`, an emoji, instead). The Orchestrator's pane (the window's first) stays
    on the left, the Workers stacked on the right."""
    if BACKEND == "herdr":
        # Workers often start together (reviewer, QA, security): one split at a time per tab, or two would split the
        # same bottom pane and nest the column.
        lock = Path(tempfile.gettempdir(), "kal-split-" + re.sub(r"\W", "-", os.environ["HERDR_TAB_ID"]))
        with open(lock, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            return _herdr_split(cmd, env, cwd, f"{mark} {title}" if mark else title)
    pane = _tmux("split-window", "-d", "-P", "-F", "#{pane_id}", "-t", caller(), "-c", str(cwd),
                 *(x for k, v in env.items() for x in ("-e", f"{k}={v}")), "sh", "-c", cmd)
    _tmux("select-pane", "-t", pane, "-T", title)
    _tmux("set-option", "-p", "-t", pane, "@kal_color", color)
    _tmux("set-option", "-p", "-t", pane, "pane-border-style", f"fg={color}")
    _tmux("set-option", "-p", "-t", pane, "pane-active-border-style", f"fg={color},bold")
    _tmux("set-option", "-w", "-t", pane, "pane-border-format",
          "#{?@kal_color,#[fg=#{@kal_color}#,bold],} #{pane_title} #[default]")
    _tmux("set-option", "-w", "-t", pane, "pane-border-status", "top")
    _tmux("set-option", "-w", "-t", pane, "main-pane-width", "50%")
    _tmux("select-layout", "-t", pane, "main-vertical")
    return pane


def _herdr_split(cmd, env, cwd, title):
    me = caller()
    node = (_column(_layout(), me) or (None, None))[1]
    while node and node["type"] == "split":  # the column's bottom Worker
        node = node["second"]
    target, direction = (node["pane_id"], "down") if node else (me, "right")
    out = subprocess.run([HERDR, "pane", "split", target, "--direction", direction, "--ratio", "0.5", "--cwd",
                          str(cwd), *(x for k, v in env.items() for x in ("--env", f"{k}={v}")), "--no-focus"],
                         check=True, capture_output=True, text=True).stdout
    pane = json.loads(out)["result"]["pane"]["pane_id"]
    # herdr can't start a pane with a command: type one into its shell (typeahead waits for the shell's rc
    # files). A typed line must stay under the tty's 1024 bytes, so `cmd` goes in a script that removes itself.
    fd, script = tempfile.mkstemp(prefix="kal-pane-", suffix=".sh")
    with os.fdopen(fd, "w") as f:
        f.write(f'rm -f "$0"\n{cmd}\n')
    try:
        subprocess.run([HERDR, "pane", "run", pane, f"exec sh {shlex.quote(script)}"], check=True, capture_output=True)
        subprocess.run([HERDR, "pane", "rename", pane, title], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        kill(pane)  # not an empty shell left beside the orchestrator
        raise
    for path, ratio in rebalance(_layout(), me):
        _rpc("layout.set_split_ratio", tab_id=os.environ["HERDR_TAB_ID"], path=path, ratio=ratio)
    return pane


def _herdr_gone(pane):
    """herdr says the pane is gone (or herdr itself is). A slow or failed call isn't proof: the Worker counts as
    alive, and the watchdog's stall timeout still catches one that really hangs."""
    try:
        r = subprocess.run([HERDR, "pane", "get", pane], capture_output=True, text=True, timeout=10)
    except OSError:
        return True
    except subprocess.TimeoutExpired:
        return False
    if r.returncode == 0:
        return False
    try:
        code = json.loads(r.stderr)["error"]["code"]
    except (ValueError, KeyError, TypeError):
        return False
    return code in ("pane_not_found", "server_not_running")


def alive(pane, title=None):
    """The pane is still open. A title guards against a pane id reused by a restarted tmux (herdr never reuses one).
    A multiplexer that doesn't answer in time counts as alive: ending the wait early would start a second Worker."""
    if is_herdr(pane):
        return not _herdr_gone(pane)
    if title is not None:
        shown = _show(pane, "#{pane_id} #{pane_title}")
        return shown is None or shown == f"{pane} {title}"
    shown = _show(pane, "#{pane_id}")
    return bool(pane) and (shown is None or shown == pane)


def _unmark(label):
    """A herdr label without the Role's emoji in front, so it reads like the tmux title (`01 developer`)."""
    first, _, rest = label.partition(" ")
    return rest if rest and not first.isascii() else label


def title(pane):
    if is_herdr(pane):
        return _unmark(_result("pane", "get", pane).get("pane", {}).get("label") or "")
    return _show(pane, "#{pane_title}") or ""


def sid_in(command):
    m = re.search(r"--session-id[ =](\S+)", command)
    return m[1] if m else None


def session_id(pane):
    """The Worker's claude session id, from its pane's start command (herdr: its running processes); None if it has
    none."""
    if is_herdr(pane):
        procs = _result("pane", "process-info", "--pane", pane).get("process_info", {}).get("foreground_processes", [])
        return sid_in(" ".join(a for p in procs for a in p.get("argv", [])))
    return sid_in(_show(pane, "#{pane_start_command}") or "")


def screen(pane):
    """The pane's visible text."""
    if is_herdr(pane):
        return _herdr("pane", "read", pane, "--source", "visible")
    return subprocess.run(["tmux", "capture-pane", "-p", "-t", pane], capture_output=True, text=True).stdout


def status(pane):
    """herdr's read of the pane's agent: working, idle, blocked (waiting on a prompt), done or unknown; None without
    one, and always under tmux."""
    return _result("agent", "get", pane).get("agent", {}).get("agent_status") if is_herdr(pane) else None


def kill(pane):
    if is_herdr(pane):
        _herdr("pane", "close", pane)
    else:
        subprocess.run(["tmux", "kill-pane", "-t", pane], capture_output=True)


def siblings():
    """[(pane id, title)] for every pane in the caller's window (herdr: tab), the caller's own included."""
    if BACKEND == "herdr":
        panes = _result("pane", "list", "--workspace", os.environ["HERDR_WORKSPACE_ID"]).get("panes", [])
        return [(p["pane_id"], _unmark(p.get("label") or "")) for p in panes
                if p.get("tab_id") == os.environ["HERDR_TAB_ID"]]
    out = _tmux("list-panes", "-t", caller(), "-F", "#{pane_id} #{pane_title}")
    return [tuple(l.split(" ", 1)) for l in out.splitlines() if " " in l]


def waiter(pane):
    """Start waiting for the pane's done signal. kill() it when done waiting. tmux keeps a signal sent before this;
    herdr doesn't replay events, so check alive() after it."""
    if not is_herdr(pane):
        return subprocess.Popen(["tmux", "wait-for", f"kal-done-{pane}"])
    subs = [{"type": "pane.closed"}, {"type": "pane.exited", "pane_id": pane},
            {"type": "pane.agent_status_changed", "pane_id": pane}]
    s = _connect("events.subscribe", {"subscriptions": subs})
    w = types.SimpleNamespace(sock=s, pane=pane, buf=b"", kill=s.close)
    _line(w, time.time() + 10)  # subscription_started
    return w


def _line(w, end):
    """The subscription's next event, None if `end` passed first, {} if herdr went away."""
    while b"\n" not in w.buf:
        if end <= time.time():
            return None
        w.sock.settimeout(end - time.time())
        try:
            chunk = w.sock.recv(65536)
        except TimeoutError:
            return None
        if not chunk:
            return {}
        w.buf += chunk
    line, w.buf = w.buf.split(b"\n", 1)
    return json.loads(line)


def wait(w, timeout):
    """True once the done signal arrived, False if `timeout` seconds passed first. herdr also returns False as soon
    as the Worker turns blocked (sits at a prompt), so the caller can look at once."""
    if isinstance(w, subprocess.Popen):
        try:
            w.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            return False
    end = time.time() + timeout
    while (e := _line(w, end)) is not None:
        data = e.get("data", {})
        if not e or e.get("event") in ("pane_closed", "pane_exited") and data.get("pane_id") == w.pane:
            return True
        if data.get("agent_status") == "blocked":
            return False
    return False
