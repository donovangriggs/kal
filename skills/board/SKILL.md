---
name: board
description: Open the repo's kal Board, the live read-only dashboard of every build Run (status lanes, dependency graph, timeline, live worker panes, findings, decisions made while away, tickets filed for later). Starts its server if it isn't running, or replaces one left over from an older kal version. Use when the user asks for the board, the dashboard, or how a build is going.
---

Run `kal-board` in the repo. It prints the Board's URL: the repo's server if it's already up, or a fresh one it started (one per repo, from port 4100, kept in `.kal/board-port`).

Then open the URL for the user (`open <url>` on macOS), and tell them:

- It refreshes every 2 seconds by itself, and keeps the run, tab and ticket they're on.
- It's read-only: the build is steered from tmux or herdr.
- To stop the server: `lsof -ti tcp:<port> -sTCP:LISTEN | xargs kill`. The next build or `/kal:board` starts it again on the same URL.
