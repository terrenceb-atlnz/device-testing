#!/bin/bash
# Sentinel watch over a tester Claude session -- the 2026-09-22 campaign kit, generalised.
# Procedure, modes, arming rules and traps: orient-dt SKILL.md §10. Run it ONLY under Monitor, e.g.
#
#   Monitor(description: "sentinel: <tester-name>",
#           timeout_ms: 1800000,
#           command: "PEER_PID=… PEER_LOG=… SCRATCH=… UNTIL='2026-09-22 16:00' bash <repo>/.claude/skills/orient-dt/sentinel/sentinel.sh")
#
# Every stdout line becomes a Monitor event in the sentinel session (and wakes it), so stdout
# is mode-filtered and capped. The FULL feed always goes to $SCRATCH/sentinel.feed for a human
# `tail -f`. All state lives in $SCRATCH, never in the repo.
#
# MODES -- switch live, no re-arm:  echo verbose > $SCRATCH/sentinel.mode   (or normal)
#   normal   console CLI transcripts as they happen + the rescue alarms
#   verbose  + the tester's narration, commands and their output, bench-runner subagent
#            transcripts, the tester's background-task output, framework run logs
#
#   PEER_LOG  the tester's transcript .jsonl            (§10 setup step 2 says how to find it)
#   PEER_PID  pid of the tester's claude process        (same; OPTIONAL -- empty = no pid check)
#   SELF      1 = ONE-SESSION shape (/test-mode, 2026-09-28): the sentinel is the parent session
#             and the tester is its bench-runner SUBAGENT. PEER_LOG is then the parent's OWN
#             transcript: it is used only to locate <session>/subagents/*.jsonl and the tasks
#             dir, and is NEVER polled itself (each Monitor event lands in it, so polling it
#             would re-emit every event -- a feedback loop). PEER_PID is ignored.
#   SCRATCH   the sentinel session's scratchpad dir
#   UNTIL     hard stand-down, anything `date -d` reads  ("2026-09-22 16:00")
#   MODE      starting mode when $SCRATCH/sentinel.mode is absent   (default normal)
#   BOX       testbox                                   (default tb470)
#   CLI_GLOB  CLI transcripts on BOX, space-separated globs: console.py transcripts + the
#             framework's per-device console logs
#             (default /tmp/*/console-*.log /home/st-art/pytest-create/*/*/swi_*.log /home/st-art/pytest-create/*/*/stk_*.log)
#   FW_GLOB   other framework logs on BOX, verbose only (default /home/st-art/pytest-create/*/*/*.log;
#             a file matching both is CLI)
#   JOBS      ERE for a live job on BOX                 (default python3|tcpdump)
#   TICK      seconds between polls                     (default 30)
#   IDLE_ALARM seconds of no activity before an IDLE report   (default 300)
#   CAP       max stdout lines per source per tick      (default 40; the feed is never capped)
set -u
: "${PEER_LOG:?}" "${SCRATCH:?}" "${UNTIL:?}"
SELF=${SELF:-0}; PEER_PID=${PEER_PID:-}
[ "$SELF" = 1 ] && PEER_PID=""          # one-session: no separate process to watch
BOX=${BOX:-tb470}
RUNS=/home/st-art/pytest-create/*/*          # bench-runner's WORK dirs (TESTBOX-ACCESS.md §3)
CLI_GLOB=${CLI_GLOB:-/tmp/*/console-*.log $RUNS/swi_*.log $RUNS/stk_*.log}
FW_GLOB=${FW_GLOB:-/home/st-art/pytest-create/*/*/*.log}
JOBS=${JOBS:-python3|tcpdump}
TICK=${TICK:-30}; IDLE_ALARM=${IDLE_ALARM:-300}; CAP=${CAP:-40}
export SSH_AUTH_SOCK=${SSH_AUTH_SOCK_TB:-/run/user/1971/keyring/ssh}   # TESTBOX-ACCESS.md §0
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10 "$BOX")

SID=$(basename "$PEER_LOG" .jsonl); SLUG=$(basename "$(dirname "$PEER_LOG")")
SUBAGENTS="$(dirname "$PEER_LOG")/$SID/subagents"         # bench-runner transcripts
TASKS=${TASKS_DIR:-/tmp/claude-$(id -u)/$SLUG/$SID/tasks} # tester's background-task output
MODEFILE="$SCRATCH/sentinel.mode"; FEED="$SCRATCH/sentinel.feed"
LIFE="$SCRATCH/sentinel.life"; BEAT="$SCRATCH/sentinel.heartbeat"
LOFFS="$SCRATCH/sentinel.local-offsets"; ROFFS="$SCRATCH/sentinel.remote-offsets"
DEADLINE=$(date -d "$UNTIL" +%s) || { echo "bad UNTIL: $UNTIL"; exit 2; }
# Assembled at runtime so neither this script nor a grep for it can match itself -- the
# self-match is the bug this kit exists to catch (memory ssh-pgrep-watchers-self-match).
WATCHER="unt""il ! ssh"

# Lifecycle to a FILE: a killed Monitor loses its stdout (09-22: two silent SIGTERMs).
echo "$(date +%T) START pid=$$ ppid=$PPID peer=${PEER_PID:-none} self=$SELF" >> "$LIFE"
for sig in TERM INT HUP; do
  trap "echo \"\$(date +%T) SIG$sig pid=\$\$\" >> \"$LIFE\"; exit 0" "$sig"
done
: > "$BEAT"      # at START: a 60 s blind window once let a cron tick arm a second sentinel

# ---- read offsets: lines for .jsonl, bytes for everything else. A file first seen on the
# ---- very first pass starts at its END (no backlog flood); one that appears later starts at 0.
declare -A LOFF ROFF CNT
FIRST=1
[ -f "$LOFFS" ] && { FIRST=0; while IFS=$'\t' read -r k v; do LOFF[$k]=$v; done < "$LOFFS"; }
[ -f "$ROFFS" ] && while IFS=$'\t' read -r k v; do ROFF[$k]=$v; done < "$ROFFS"
save_offsets() {
  { for k in "${!LOFF[@]}"; do printf '%s\t%s\n' "$k" "${LOFF[$k]}"; done; } > "$LOFFS.tmp" && mv "$LOFFS.tmp" "$LOFFS"
  { for k in "${!ROFF[@]}"; do printf '%s\t%s\n' "$k" "${ROFF[$k]}"; done; } > "$ROFFS.tmp" && mv "$ROFFS.tmp" "$ROFFS"
}

# emit <show 0|1> <label> <line>: always to the feed; to stdout only if shown, capped per label.
emit() {
  printf '%s [%s] %s\n' "$T" "$2" "$3" >> "$FEED"
  [ "$1" = 1 ] || return 0
  CNT[$2]=$(( ${CNT[$2]:-0} + 1 ))
  [ "${CNT[$2]}" -le "$CAP" ] && printf '%s [%s] %s\n' "$T" "$2" "$3"
  return 0
}
flush_caps() {
  for k in "${!CNT[@]}"; do
    [ "${CNT[$k]}" -gt "$CAP" ] && printf '%s [%s] +%d more lines this tick -- tail -f %s\n' "$T" "$k" $(( CNT[$k] - CAP )) "$FEED"
  done
  CNT=()
}

# One line per transcript event: what the tester SAID, RAN, GOT BACK, and messages it received.
JQ='(select(.type=="user" and (.message.content|type)=="string") | "msg: " + (.message.content|gsub("\n";" ")|.[0:280])),
    (select(.type=="assistant" or .type=="user") | .message.content | select(type=="array") | .[] |
      if .type=="text" then "say: " + (.text|gsub("\n";" ")|.[0:280])
      elif .type=="tool_use" then "run: " + .name + " " + ((.input.command // .input.description // (.input|tostring))|gsub("\n";" | ")|.[0:280])
      elif .type=="tool_result" then "out: " + ((if (.content|type)=="string" then .content else ([.content[]?|.text? // empty]|join(" ")) end)|gsub("\n";" | ")|.[0:280])
      else empty end)'

poll_jsonl() {   # poll_jsonl <file> <label>
  local f=$1 cur off l
  cur=$(wc -l < "$f" 2>/dev/null) || return 0        # complete lines only; a half-written one waits
  if [ -n "${LOFF[$f]+x}" ]; then off=${LOFF[$f]}; elif [ "$FIRST" = 1 ]; then off=$cur; else off=0; fi
  [ "$cur" -lt "$off" ] && off=0
  LOFF[$f]=$cur
  [ "$cur" -gt "$off" ] || return 0
  ACTIVE=1
  while IFS= read -r l; do emit "$V" "$2" "$l"; done < <(tail -n +$((off+1)) "$f" | head -n $((cur-off)) | jq -r "$JQ" 2>/dev/null)
}

poll_bytes() {   # poll_bytes <file> <label> -- local append-only text file
  local f=$1 s b l
  s=$(stat -c %s "$f" 2>/dev/null) || return 0
  if [ -n "${LOFF[$f]+x}" ]; then b=${LOFF[$f]}; elif [ "$FIRST" = 1 ]; then b=$s; else b=0; fi
  [ "$s" -lt "$b" ] && b=0
  LOFF[$f]=$s
  [ "$s" -gt "$b" ] || return 0
  ACTIVE=1
  while IFS= read -r l; do [[ $l =~ [^[:space:]] ]] && emit "$V" "$2" "$l"; done \
    < <(tail -c +$((b+1)) "$f" | head -c $((s-b)) | tr -d '\000' | tr '\r' '\n')
}

is_cli() {       # is_cli <remote path>: does it match any CLI_GLOB pattern? (noglob: match, don't expand)
  local p rc=1; set -f
  for p in $CLI_GLOB; do [[ $1 == $p ]] && { rc=0; break; }; done
  set +f; return $rc
}

poll_remote() {  # ONE ssh per tick: new bytes of every console transcript and framework log
  local out="$SCRATCH/sentinel.remote-poll" offs line f s label show
  offs=$(for k in "${!ROFF[@]}"; do printf 'o[%q]=%s\n' "$k" "${ROFF[$k]}"; done)
  "${SSH[@]}" bash -s > "$out" 2>/dev/null <<EOF || return 0
declare -A o seen
$offs
for f in $CLI_GLOB $FW_GLOB; do
  [ -f "\$f" ] && [ -r "\$f" ] && [ -z "\${seen[\$f]+x}" ] || continue
  seen[\$f]=1
  s=\$(stat -c %s "\$f")
  if [ -n "\${o[\$f]+x}" ]; then b=\${o[\$f]}; elif [ $FIRST = 1 ]; then b=\$s; else b=0; fi
  [ "\$s" -lt "\$b" ] && b=0
  printf '::F::\t%s\t%s\n' "\$f" "\$s"
  [ "\$s" -gt "\$b" ] && tail -c +\$((b+1)) "\$f" | head -c \$((s-b)) | tr -d '\000' | tr '\r' '\n'
  echo
done
EOF
  while IFS= read -r line; do
    if [[ $line == ::F::$'\t'* ]]; then
      IFS=$'\t' read -r _ f s <<< "$line"; ROFF[$f]=$s
      if is_cli "$f"; then label=$(basename "$f" .log); show=1; else label="fw:$(basename "$f")"; show=$V; fi
    elif [[ $line =~ [^[:space:]] ]]; then
      ACTIVE=1; emit "$show" "$label" "$line"
    fi
  done < "$out"
}

MODE_NOW=""; last_act=$(date +%s); next_alarm=$(( last_act + IDLE_ALARM ))
declare -A SKIPF   # SELF: our own stdout lands in $TASKS/<id>.output -- reading it back is a loop
MARK="SENTINEL pid=$$"
ANYMARK="[0-9:]+ SENTINEL pid=[0-9]+ self="
while true; do
  T=$(date +%T); ACTIVE=0
  : > "$BEAT"
  [ -z "$MODE_NOW" ] && echo "$T $MARK self=$SELF"      # first tick: the marker that names our own task output
  m=$(cat "$MODEFILE" 2>/dev/null || echo "${MODE:-normal}"); [ "$m" = verbose ] || m=normal
  if [ "$m" != "$MODE_NOW" ]; then
    echo "$T MODE $m  (switch: echo verbose|normal > $MODEFILE; full feed: tail -f $FEED)"; MODE_NOW=$m
  fi
  V=0; [ "$m" = verbose ] && V=1

  if [ "$(date +%s)" -ge "$DEADLINE" ]; then echo "$T SENTINEL STAND-DOWN -- $UNTIL reached"; exit 0; fi
  if [ -n "$PEER_PID" ] && ! kill -0 "$PEER_PID" 2>/dev/null; then echo "$T PEER SESSION EXITED (pid $PEER_PID gone)"; exit 0; fi

  poll_remote                                        # CLI: shown in both modes
  [ "$SELF" = 1 ] || poll_jsonl "$PEER_LOG" tester   # the rest: shown in verbose only; never our own transcript
  for f in "$SUBAGENTS"/*.jsonl; do [ -f "$f" ] && poll_jsonl "$f" "agent:$(basename "$f" .jsonl | cut -c7-14)"; done
  for f in "$TASKS"/*.output; do
    [ -f "$f" ] || continue
    [ -n "${SKIPF[$f]+x}" ] && continue
    # ANY sentinel's output, not just ours: a re-arm otherwise replays the expired watcher's
    # whole output file (2026-10-01: 2158 lines in one tick after the first re-arm).
    if [ "$SELF" = 1 ] && command grep -qE -- "$ANYMARK" "$f" 2>/dev/null; then SKIPF[$f]=1; LOFF[$f]=$(stat -c %s "$f"); continue; fi
    poll_bytes "$f" "task:$(basename "$f" .output)"
  done
  flush_caps; save_offsets; FIRST=0

  now=$(date +%s)
  [ "$ACTIVE" = 1 ] && { last_act=$now; next_alarm=$(( now + IDLE_ALARM )); }
  if [ "$now" -ge "$next_alarm" ]; then
    # Snapshot ps to a file, then grep the file: grepping live ps output self-matches.
    ps -eo pid,etime,cmd --no-headers > "$SCRATCH/sentinel-ps.txt" 2>/dev/null
    stale=$(command grep -c -- "$WATCHER" "$SCRATCH/sentinel-ps.txt" 2>/dev/null); stale=${stale:-0}
    # Remote: plain ps, filtered LOCALLY -- never a remote pgrep (matches its own bash -c).
    remote=$("${SSH[@]}" 'ps -eo pid,etime,cmd --no-headers' 2>/dev/null \
             | command grep -v 'ps -eo' | command grep -Ec -- "$JOBS"); remote=${remote:-0}
    idle=$(( now - last_act )); [ "$idle" -ge 120 ] && idle="$(( idle / 60 ))m" || idle="${idle}s"
    echo "$T IDLE $idle -- stale watcher loops here: $stale; live jobs on $BOX: $remote"
    if [ "$stale" -gt 0 ] && [ "$remote" -eq 0 ]; then echo "  >>> STALL SIGNATURE: tester waits on a watcher that cannot fire -- message it"; fi
    if [ "$stale" -eq 0 ] && [ "$remote" -eq 0 ]; then
      if [ "$SELF" = 1 ]; then echo "  >>> nothing running anywhere -- if the queue has rows not DONE/BLOCKED, continue the bench-runner subagent or dispatch the next group (/test-mode)"
      else echo "  >>> tester idle, nothing running anywhere -- stalled, or NEEDS TERRENCE (read its last text)"; fi
    fi
    next_alarm=$(( now + IDLE_ALARM ))
  fi
  sleep "$TICK" & wait $!     # backgrounded so a signal trap fires at once, not after the sleep
done
