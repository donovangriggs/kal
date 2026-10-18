#!/usr/bin/env python3
"""The Workers' PreToolUse hook on Bash (kal-worker wires it into each Worker's settings; not a kal-* command).

Reads the hook's JSON on stdin and blocks (exit 2, one line on stderr) destructive git in worktrees that share
one .git: stash, reset --hard, clean, checkout … -- … (but --ours/--theirs, a Merger's conflict resolution, may),
checkout . / -f, restore (unless --staged only), switch -f/--discard-changes, branch -D, commit --amend,
push -f/--force…/+refspec. It drops heredoc bodies (a commit message's text is no command), splits the command
on && || ; | ( ) and newlines, and in each part skips VAR=value, an `rtk` / `rtk proxy` prefix and git's
global options (-c k=v, -C dir, --no-pager, --git-dir[=]…, …) to find the subcommand.
A guardrail against slips, not a sandbox: `sh -c '…'`, eval and backticks aren't looked into.
"""
import json
import re
import shlex
import sys

GLOBAL_WITH_VALUE = {"-c", "-C", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env",
                     "--attr-source"}  # their value may be the next word; every other global option is one word
SEP = set("&|;()\n")


def strip_heredocs(cmd):
    """The command without its heredoc bodies: after a line holding `<<WORD` (or `<<-`, quoted or not), every
    line up to and including the one that is WORD. An unclosed heredoc runs to the end, as in sh."""
    lines, out = cmd.split("\n"), []
    while lines:
        line = lines.pop(0)
        out.append(line)
        for dash, word in re.findall(r"(?<!<)<<(?!<)(-?)\s*['\"]?([A-Za-z_][\w.-]*)", line):
            while lines:
                body = lines.pop(0)
                if (body.lstrip("\t") if dash else body) == word:
                    break
    return "\n".join(out)


def words(cmd):
    """The command's words, with each run of separators as one word of separator characters."""
    lex = shlex.shlex(cmd, posix=True, punctuation_chars="();<>|&\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    try:
        return list(lex)
    except ValueError:  # unbalanced quotes (a heredoc's apostrophe): split plainly, never let it through unread
        return re.findall(r"[&|;()\n]+|[^\s&|;()]+", cmd)


def parts(cmd):
    part = []
    for w in words(cmd):
        if w and set(w) <= SEP:
            yield part
            part = []
        else:
            part.append(w)
    yield part


def why(part):
    """The reason this simple command is blocked, or None."""
    while part and re.fullmatch(r"\w+=.*", part[0]):
        part = part[1:]
    if part[:1] == ["rtk"]:
        part = part[2:] if part[1:2] == ["proxy"] else part[1:]
    if not part or part[0].rsplit("/", 1)[-1] != "git":
        return None
    i = 1
    while i < len(part) and part[i].startswith("-"):
        i += 2 if part[i] in GLOBAL_WITH_VALUE else 1
    sub, args = (part[i], part[i + 1:]) if i < len(part) else ("", [])
    if sub in ("stash", "clean"):
        return f"git {sub}"
    if sub == "reset" and "--hard" in args:
        return "git reset --hard"
    short = "".join(a[1:] for a in args if re.fullmatch(r"-[a-zA-Z]+", a))  # every short flag: -SW -> SW
    if sub == "checkout" and not {"--ours", "--theirs"} & set(args) and (
            "--" in args or "." in args or "f" in short or "--force" in args):
        return "git checkout -- / . / -f (discards changes)"
    if sub == "restore" and ("--worktree" in args or "W" in short or not ("--staged" in args or "S" in short)):
        return "git restore (of the working tree; --staged alone is fine)"
    if sub == "switch" and ("f" in short or "--force" in args or "--discard-changes" in args):
        return "git switch -f / --discard-changes"
    if sub == "branch" and ("D" in short or {"--delete", "--force"} <= set(args)):
        return "git branch -D"
    if sub == "commit" and any(a.startswith("--amend") for a in args):
        return "git commit --amend"
    if sub == "push" and any(a.startswith("--force") or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a)
                             or a.startswith("+") for a in args):
        return "git push --force"
    return None


cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
for part in parts(strip_heredocs(cmd)):
    reason = why(part)
    if reason:
        print(f"Blocked: {reason} is not allowed in a kal Worker (worktrees share one .git).", file=sys.stderr)
        sys.exit(2)
