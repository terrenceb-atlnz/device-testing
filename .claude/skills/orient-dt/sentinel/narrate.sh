#!/bin/bash
# The sentinel's narrator (orient-dt §10, 2026-10-13): one plain-English update per active tick,
# written by Haiku, so the session the Test Engineer talks to (Opus) is not woken to write it.
#
#   narrate.sh <tick lines file> <recent updates file>
#
# stdout: ONE JSON line {"text": "...", "attention": "..." | null, "cost_usd": n}; exit 1 on any
# failure (sentinel.sh then falls back to a plain summary). Nothing here touches the bench.
#
# Why (Ask-CK run 2026-10-13T0626-val-fbe9, $35.11 for one automated script): every line
# sentinel.sh printed woke the Opus session, which re-read its whole conversation (125k tokens
# at the start, 553k at the end) to write one line -- 331 times. Haiku now writes the line from
# a small, fixed-size context; Opus is woken only for ATTENTION and the alarms.
#
#   NARRATOR_MODEL   default haiku
#   NARRATOR_LINES   max log lines sent per tick (default 150)
#   NARRATOR_CHARS   max characters sent per tick (default 14000)
#   CLAUDE_BIN       default: `claude` on PATH, else ~/.local/bin/claude
set -u
TICKF=${1:?tick lines file}; MEMF=${2:-/dev/null}
MODEL=${NARRATOR_MODEL:-haiku}; MAXL=${NARRATOR_LINES:-150}; MAXC=${NARRATOR_CHARS:-14000}
BIN=${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}
[ -x "$BIN" ] || { echo "narrate: no claude CLI at $BIN" >&2; exit 1; }
[ -s "$TICKF" ] || exit 1

# One copy of each line: the framework writes every device log twice (swi_a.log and
# swi_a_<case>.log), and status polls repeat. Outlet-status dumps are pure noise.
uniq_lines() {
  awk '{ k = $0; sub(/^[0-9:]+ /, "", k); gsub(/_[0-9]+\]/, "]", k) } !seen[k]++' "$TICKF" \
    | command grep -v -e 'Current outlet status' -e '^[0-9:]* \[[^]]*\] *$'
}
SEL=$(mktemp); trap 'rm -f "$SEL" "$SEL.in"' EXIT
uniq_lines > "$SEL"
n=$(wc -l < "$SEL")
if [ "$n" -gt "$MAXL" ]; then   # the start, the end, and what matters in between
  k=$(( MAXL / 3 ))
  { head -n "$k" "$SEL"
    sed -n "$((k+1)),$((n-k))p" "$SEL" | command grep -E \
      'TestCase|TESTCASE|PASS|FAIL|ERROR|Error|error|Traceback|% |reboot|Reboot|login:|y/n|--More--|INFO|[a-zA-Z0-9_-]+(\([a-z-]+\))?#' \
      | head -n "$k"
    echo "... ($n lines this tick; middle trimmed)"
    tail -n "$k" "$SEL"; } > "$SEL.in"
else
  cp "$SEL" "$SEL.in"
fi

SYS='You write the running commentary on a live automated test run on an Allied Telesis AlliedWare Plus test bench, for the Test Engineer watching it.

Input: your last few updates, then the new log lines from the last ~30 seconds. Labels: [swi_a], [stk_a], [console-u5] ... are device console transcripts; [fw:...] are the test framework'"'"'s logs; [agent:...] is the tester agent'"'"'s own actions; [task:...] is its background output.

Write ONE short plain-English sentence (at most 30 words) saying what is happening now: which TestCase, what it is doing, what a device answered. Name TestCases and ports as the logs do. Do not repeat your previous update; if nothing new of note happened, say briefly what is still in progress. Tests often send values on purpose that a port rejects (for example "% Invalid input" or "Speed or duplex must be auto" during a check for rejection); that is expected, so say so rather than calling it a problem.

ATTENTION wakes the coordinating session, which is expensive, so use it rarely. Framework !!FAIL and ERROR lines, tracebacks and power cycles are already caught without you, and a separate alarm fires after 5 minutes with no activity. Add a second line starting "ATTENTION: " with a one-sentence reason ONLY for what those miss: a device rebooting when no test step asked for it; a console sitting at a prompt (login:, y/n, --More--) that nothing answers in this tick; one device silent for over 3 minutes while the others move on. These are NOT attention: a slow "boot conf", "copy" or stack config sync (30 to 90 seconds of silence is normal on a stack); a value the test expects the port to reject; the tester agent hitting a hook or permission refusal (it handles that itself); anything you are unsure about. Otherwise write no second line. Output nothing else.'

IN=$( { echo "Your recent updates (oldest first):"; tail -n 6 "$MEMF" 2>/dev/null || true
        echo; echo "New log lines:"; cat "$SEL.in"; } | head -c "$MAXC")

# A nested CLI must not inherit this session's identity (session id, messaging socket): strip
# every CLAUDE* variable. No tools, no settings, no hooks, no MCP, nothing persisted.
UNSET=(); while IFS='=' read -r k _; do [[ $k == CLAUDE* ]] && UNSET+=(-u "$k"); done < <(env)
cd "${TMPDIR:-/tmp}" || exit 1
OUT=$(printf '%s\n' "$IN" | timeout 90 env "${UNSET[@]}" "$BIN" -p --model "$MODEL" --tools "" \
        --setting-sources "" --strict-mcp-config --no-session-persistence --disable-slash-commands \
        --output-format json --system-prompt "$SYS" 2>/dev/null) || exit 1
printf '%s' "$OUT" | jq -ce '
  select(.is_error != true and (.result | type) == "string") |
  (.result | split("\n") | map(select(test("\\S")))) as $l |
  { text: ($l | map(select(startswith("ATTENTION:") | not)) | first // ""),
    attention: ($l | map(select(startswith("ATTENTION:"))) | first // null | if . then sub("^ATTENTION:\\s*"; "") else null end),
    cost_usd: (.total_cost_usd // 0) }' || exit 1
