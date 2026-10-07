---
name: shared-testbox-console-occupancy
description: "Before bench_probe.py (or any console driver) touches a SHARED testbox, run a no-console occupancy check over ssh: who/w, /run/lock/LCK..uN, ps for minicom/screen/picocom/python, `sudo -n fuser -v` on the resolved ttyUSB targets. `sudo minicom` holders are INVISIBLE to fuser without sudo — so no sudo = UNKNOWN, never free. Verified tb105 2026-10-01."
metadata:
  type: project
  modified: 2026-10-01T00:00:00.000Z
---

**Terrence, 2026-10-01:** "there is a large likelihood we will use this on shared test boxes" —
before probing another box, find which `/dev/uN` other people are on "so we can not interrupt
them". Method verified the same day on **tb105** (shared; x950 stack), read-only, no console opened.

**The check** — one `ssh -o BatchMode=yes tbNNN 'bash -s' <<'EOF' … EOF` (SSH_AUTH_SOCK =
the keyring socket, [[testbox-console-access]]); sends NOTHING to any console, not even `\r`:
1. `who; w -h` — humans logged in, their pts, idle time.
2. `for d in /dev/u[0-9]*; do readlink -f $d; done` — the uN → ttyUSBn map (numbering has gaps:
   tb105 has no u24, 42 consoles).
3. Lock files: `/run/lock/LCK..uN` (content = holder PID). `/var/lock` is a symlink to
   `/run/lock`, so globbing both lists every lock twice.
4. `ps -eo user,pid,ppid,tty,etime,args | grep -E '[m]inicom|[s]creen|[p]icocom|[A]TTestSet|[p]ython'`
   — the `[x]` bracket stops grep matching itself ([[ssh-pgrep-watchers-self-match]]).
5. `sudo -n /bin/fuser -v <every resolved ttyUSB>` — the authoritative holder list, catches
   pyserial/framework holders the ps pattern misses. `fuser` is `/bin/fuser`; check absolute paths
   ([[ssh-path-has-no-sbin]]). `sudo -n true` first: tb105 has passwordless sudo.

**What tb105 showed (2026-10-01 13:44 NZDT):** `u0` (ttyUSB1) and `u5` (ttyUSB19) held by
`sudo minicom -D /dev/uN`, user **samh** (pts/0 and pts/1, sessions since 09-28, idle 4 h+); the
other 40 had no holder. Lock file and fuser both say **root** — the human is found by walking the
PPID to the login shell (`ps -o user -p <ppid>` → samh).

**The trap — and a gap in bench_probe.py:** `/bin/fuser -v /dev/u0` WITHOUT sudo returned rc=1,
no output, for samh's root-owned minicom — exactly what a free console looks like.
`bench_probe.py console_holder()` (~line 387) uses `sudo -n` only when `_sudo_ok()`; on a box
without passwordless sudo it would call those consoles free and log in on top of the occupant
(the probe's login also sends `\r`/`quit`, which can log a user out). Until the code is changed:
no sudo → also check the lock files and `ps` args, and report anything unverifiable as UNKNOWN.

**Running the probe there — `--read-only` (added 2026-10-01, first used on tb105 u2/u4/u22):**
`capture --consoles 2,4,22 --read-only --no-prompt` = logins and `show` commands ONLY: no `lldp
run` on a device that has it off (its cabling then reads unproven), no MAC-learning pings out of
the host NICs. Default tb470 behaviour unchanged (offline regenerate byte-identical).
- **Copy the script to the box's `/tmp/ckprobe/` and run it there.** Run from the repo path on the
  NFS home, its captures land in `bench-setup/captures/` beside tb470's, and tb470's next run takes
  the newest one as its "previous capture" (baud/LLDP hints).
- **tb105's `python3` is 3.6 — too old** (`subprocess.run(capture_output=...)` needs 3.7); use
  `python3.8` (has pyserial 3.4). Consoles are `crw-rw---- root grp_everyone`: no sudo needed to open.
- Pull the capture back (`scp -r`) and `generate <dir> --out <scratchpad>/…` offline; NEVER the
  default `--out` (that is tb470's bench-state.md). The output still says "tb470" in its headings
  and names units swi_g… from an empty static file — cosmetic, but don't paste it as a .setup.
- One console of a stack reads the WHOLE stack (backup consoles relay to the master): u2 gave all
  4 SBx908 GEN2 members, u4 both x330s.
- `close()` sends only `end`: the probe LEAVES each console logged in as manager. On a shared box
  that is someone else's console afterwards — log out, or rely on the device's exec-timeout.

**Why:** two writers on one console is the classic failure ([[sentinel-kit-in-orient-dt]]), and
on a shared box the other writer is a colleague, not our own stray process.

**UPDATE 2026-10-01 (later the same day): the check is now a probe subcommand, and the probe is
box-agnostic.** `bench_probe.py --box tbNNN precheck --consoles <list>` does steps 1–5 above
without opening a console: it resolves uN to ttyUSB, uses `/bin/fuser` via `sudo -n` where that
works, checks `/run/lock/LCK..` under both names, lists screen/tmux/minicom-type processes and
python scripts box-wide (walking PPIDs to find the human behind a root `sudo minicom`), and runs
`w -h`. No sudo makes every console with no other evidence read **UNKNOWN**. Exit 0 = CLEAR,
5 = FOUND. `--box` puts a non-tb470 box's files under `bench-setup/<box>/` (captures, static,
backups, bench-state.md) and its template at `/home/st-art/st-art/configs/<box>.setup`. That
removes the two cautions below ("captures land beside tb470's", "apply would overwrite
tb470.setup"), but only when `--box` is passed. `/test-mode` runs the precheck before every
probe and returns to the Test Engineer on FOUND.

**How to apply:**
- On any box but tb470: run this check first, then pass bench_probe `--consoles` listing only
  the free ones. Idle ≠ free — an open minicom idle for hours is still someone's console.
- It sees who has a console open NOW, not who owns the bench: an ST-ART/framework run between
  steps, or a user who closed minicom mid-task, looks free. Ask the box's users or Terrence.
- bench_probe.py is still tb470-wired (`BOX`, `REMOTE`, `tb470.static`): on another box never
  `apply` (it would overwrite tb470.setup), and its LLDP switch-on is a device change that needs
  the box owner's consent. See [[bench-probe-one-tool]].

**Gate on the precheck's exit code — never `;`-chain a driver after it (2026-10-08, tb470 u0).**
A wrap ran `bench_probe.py precheck --consoles u0; ckcon.py /dev/u0 …` in one ssh. Precheck
said FOUND (the Test Engineer's minicom, opened ~2 h after the last CLEAR, for a modbus
campaign), but `;` ran ckcon anyway: it sent one bare CR into his live console, then died on
"multiple access on port". Use `precheck … && driver …`, or read the result before the next call.
A CLEAR from earlier in the session is stale.
