# tools/ — reusable helpers for AW+ bench testing (any testbox, any product)

Every helper a case can reuse lives here, catalogued in this file. The rules for using and
adding one are in [../logged-output.md](../logged-output.md) §2:
- **Look here first.** Use or extend the tool that already exists; do not write a second one.
- **Write it generic.** Testbox, consoles, NICs, ports, VLANs and addresses are arguments, never
  constants.
- **Commit it with its entry below.**
- **The working log names the tool and its exact arguments**, so the run can be repeated.

## How to run them

- **From a session, every step on a box goes through `tools/tb`** (below). Run it from the repo
  root on the dev host. It copies this directory to the box, sets the ssh agent itself, and runs
  each tool on the box.
- **By hand, copy the whole directory to the testbox's scratch** and run from there. For example:
  `scp -r tools <box>:/tmp/<campaign>/`, then `cd /tmp/<campaign>/tools`. The tools import each
  other from their own directory, so keep them together.

### `tb`
The one way a device-testing session reaches a testbox: `tools/tb <action> <box> [args...]`
(Ask-CK decision D6, 2026-10-09).
- **Why it exists:** every ssh step is one named action, so a settings file can allow each with
  one narrow rule (`Bash(tools/tb ckcon *)`). A hand-built `SSH_AUTH_SOCK=… ssh tbNNN '…'`
  line can never match a rule.
- **What it does for you:**
  - sets `SSH_AUTH_SOCK` (the keyring agent);
  - forwards a local `CKTO=<secs>` (the console drivers' per-command timeout) to the box for the
    console actions, since ssh carries no environment (2026-10-21; e.g. `CKTO=600 tools/tb ckcon …`
    for a long `copy`);
  - forwards every login secret — `CK_USER` / `CK_PASSWORD`, the per-console `CK_USER_U<N>` /
    `CK_PASSWORD_U<N>` that `tools/console.py` and `bench-setup/bench_probe.py` read, and any
    other `CK_PASSWORD*` / `CK_USER*` name a tool wants — to the box **over stdin**, exporting
    them there before the tool runs, never on the remote command line, which `ps` shows to every
    other user on a shared box (added 2026-10-21 for tb277, whose u3 and u5 are on a non-default
    password). 🔴 The secret lines come FIRST and **the caller's own piped stdin follows them**:
    an earlier version replaced stdin outright, which silently emptied the password a tool was
    reading from it and cost a bench account four failed logins the same day. A tool that needs
    a far-end password through this wrapper should still prefer an environment variable
    (`devclient --password-env`) over stdin;
  - picks the box's Python (tb105 and tb277: `python3.8`, because their `python3` is 3.6 and
    `bench_probe.py` dies on it with `TypeError: __init__() got an unexpected keyword argument
    'capture_output'`; or set `TB_PY`);
  - quotes every argument;
  - runs locally when the host IS the box.
- **Actions** (`tools/tb --help` gives the full list with arguments):
  - read-only: `hostname`, `precheck`, `probe` (`bench_probe.py run` only), `holders`, `ps`,
    `nics`, `template`, `tail`, `grep`, `waitfor`;
  - scratch: `scratch <name>` (a fresh copy of `tools/` into `/tmp/<name>/tools`), `put`;
  - consoles: `ckcon ckyn cfg qmark peek listen poll reloadc ckreload conlogin awshell health`
    (`<scratch> <uN> <baud> ...`; the transcript goes to `/tmp/<scratch>/console-<uN>.log`),
    `speedrow` (`<scratch> <dutU> <partnerU> <baud> ...`: two consoles from one process, both
    checked for holders; 2026-10-21), and `tftp_copy flash_copy bootmenu_escape bootmenu_park
    witness_log` (`<scratch> <uN> ...`);
  - other tools: `tool`, `sudotool` (the root traffic tools), `capture` (tcpdump), `ping`,
    `case` (a case script you `put` first), `pdu`;
  - framework runs: `fwprep`, `fw` (always `--noupdate --nodefaultcfg`; writes `run.log` and
    `run.exit`);
  - housekeeping: `killmine`.
- **Where:** the dev host (or the box itself); **needs:** Python 3.6+, ssh/scp with the keyring
  agent
- **Imports:** none (it runs the other tools on the box)
- **Guards:**
  - Every console action first runs `fuser` on the device node and refuses (exit 5), naming the
    holder, if any other process has it open.
  - `probe` refuses `apply`/`--force`.
  - `tail`/`grep`/`waitfor` read only under `/tmp/` and `/home/st-art/pytest-create/`.
  - `capture`/`ping` accept NIC names `eth*`, `enp*`, `ens*`, `eno*` and, since 2026-10-21, `bond*` (a host LAG
    built with `bondctl.py`).
  - `killmine` kills only this repo's tools, probes and framework runs, never a minicom, screen
    or tmux (the Test Engineer runs as the same Unix user).
  - There are no actions for `apply`, licences or root changes: those are STANDING-ORDERS §4.
- **Settings for Ask-CK-launched campaigns:** `.claude/ask-ck-campaign.settings.json`.
  - Ask-CK's launcher passes it with `claude --settings <it>`; Claude Code never loads it on its
    own.
  - It holds one allow rule per action (`case` deliberately has none), denies for
    `bench_probe.py apply`, and an `autoMode` block: the lab as trusted infrastructure, console
    configuration allowed, and the STANDING-ORDERS §4 items as `hard_deny`.
  - Approved by Terrence 2026-10-09.
- **Status:** verified 2026-10-09 on tb470:
  - `hostname`, `precheck`, `holders`, `ps`, `nics`, `template`, `scratch`, `put` + `case`,
    `waitfor`, `tail`;
  - `ckcon` on u0 (x230, `show clock`);
  - the held-console refusal, with `listen` holding u0;
  - the refusals for `probe apply`, `tail /etc/passwd`, a bad box name and `killmine 1`.

  `fwprep`, `fw`, `pdu`, `sudotool` and `capture` have not yet run: check their first use.
- **Console tools take `<tty> <baud> <transcript>` first.**
  - `<tty>` is the unit's console on the box, for example `/dev/u3`.
  - `<transcript>` is where every byte sent and received is written. Put it at
    `/tmp/<campaign>/console-<uN>.log`, the path the sentinel watches.
- **Login credentials** default to AW+'s `manager` / `friend`. Set `CK_USER` and `CK_PASSWORD`
  to change them for every tool at once.
- **Output goes only where the arguments say**, or to the current directory. A tool never
  writes into the repo, the deployed `.setup` or the framework.
- **Argument errors** print a usage line and exit 2. Run with `-h` for help.
- **Requirements:** Python 3.7 or later on Linux. Each entry names anything else it needs
  (pyserial, scapy, tcpreplay, pymodbus). "root" means run it with `sudo`.

**Status.** Every tool below, apart from the two i2c stress tools (see their entries), was moved
here and generalised on 2026-10-02 from tb470/IE520 campaign scripts. Bench facts became arguments and nothing else in its behaviour changed. The
read-only console tools and the offline pcap tools were re-run on tb470 the same day. **A tool
whose status still says "not re-verified on hardware" has not been run since it changed.** The
first run that uses one should change its status to `verified <date> on <box>/<product>`.

## Console driving

### `console.py`
AW+ console driver library. It logs in and treats a command as complete when a prompt appears
after its echo, so asynchronous log lines do not stall it. Every byte goes to the transcript as
it arrives. The framework's driver times out on about 17% of commands with `terminal monitor`
on; this one does not (orient-dt §3).
- **Run:** `import console; c = console.Console(tty, transcript, baud=115200); c.login(); c.cmd("show system"); c.close()` (library; running it directly prints usage)
- **Where:** testbox; **needs:** pyserial, `stty`
- **Imports:** none
- **Limits:**
  - The prompt regex expects AW+ `host#` / `host(mode)#`.
  - `stty -hupcl` is an IE520 DTR/BREAK workaround and is harmless elsewhere.
  - It raises at a forced password change rather than guessing.
- **Advisory `% ` lines (2026-10-09):** `console.ADVISORY` / `console.is_advisory(line)` is the
  ONE home for the AW+ `% ` lines that are advisories rather than rejections — currently
  `is currently configured as a mirror-port` and `This access-list is attached to an interface`.
  `cfg.py` and `qmark.py` both import it instead of keeping copies that could drift. A driver
  that treats an advisory as an error stops its batch and **silently skips every command after
  it**: that cost a run on tb277 2026-10-08 (T44992) and tripped `qmark.py` again on 2026-10-09
  (T44973). Add an entry only with a transcript showing the command took effect.
- **🔴 Prompt-splice recovery (2026-10-16, tb277 x960):** AW+ **switch-driver** messages are
  written straight to the console by the port driver, not through the logging subsystem, so
  **neither `terminal no monitor` nor `no log console` suppresses them**. One can land INSIDE
  the prompt rather than after it -- `awplus(config-ifswitch: port 14(port1.0.14) entered
  disabled state` then `)#` on the next line, and the same shape from
  `vlan61: entered allmulticast mode`. Neither half matched, so the command ran to its FULL
  timeout and `cfg.py` then silently abandoned the rest of its batch although the command HAD
  taken effect -- 90 s and a truncated batch per `shutdown`/`no shutdown`. Fixed two ways so an
  unseen message still works: `PROMPT_ANYWHERE_RE` also matches a line beginning `)#` (the tail
  a splice always leaves; no device output legitimately starts a line that way), and
  `SPLICE_RE` / `unsplice()` strip the known families from a COPY of the buffer and retry. The
  transcript and the returned output keep every byte. Same silent-truncation family as
  `console.ADVISORY`.
- **Exec sub-modes with square brackets (2026-10-21):** `PROMPT_RE` / `PROMPT_ANYWHERE_RE` also match
  `host[atmf-provision]#`, and `to_exec()` leaves such a mode with `exit` (a `(config…)` mode still with
  `end`). Before this, every command sent in `atmf provision node` mode ran to its full timeout.
- **Mode-aware terminal settings (2026-10-02):** `to_exec()`, `set_monitor(on)` and
  `monitor_off()`. `terminal monitor` / `terminal no monitor` / `terminal length` are exec-only
  and `terminal monitor` does not toggle, so these methods confirm a prompt first, `end` out of
  config, and then send the command. They send nothing more than one CR to a busy console and
  return False. `login()` and every driver here (`awlogin`, `ckcon`, `ckyn`, `cfg`, `poll`,
  `qmark`, `ckreload`; `i2c_stress` has its own `end` check) use them. Memory
  `terminal-monitor-exec-only`.
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only (through ckcon, cfg, qmark, poll, listen, witness_log); x230 at 9600 via ckcon. The mode-aware methods were verified the same day on u3 through `ckcon`: login at a parked `(config)#` prompt, a plain run, and a cleanup during a 30 s ping. None of them logged `Command [terminal no monitor] failed`. The other drivers' changed call sites compile but were not re-run on hardware.

### `awlogin.py`
Shared AW+ login and expect helpers for the console drivers. It waits for prompts, never for a
quiet gap, and refuses the forced password-change dialog.
- **Run:** `import console, awlogin as L; ok = L.login(c)` (library)
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Limits:** AW+ `login:` / `Password:` / `#` / `>` prompts only
- 🔴 **A credential is submitted ONCE** (`cred_attempts=1`). `tries` bounds prompt navigation
  only -- bare CRs, `enable`, an already-open session -- none of which costs an authentication
  attempt. **AW+ locks an account at five failed logins and every further failure re-arms the
  five-minute timer**, so a lock cannot expire while anything retries. Until 2026-10-22 this
  function looped `tries=5` re-sending a full credential on every rejection -- a retry count
  exactly equal to the lockout threshold -- and it locked a partner switch mid-campaign
  (tb277 swi_b, five attempts in forty seconds). `Login incorrect` now returns False at once:
  a rejection is an answer, not a reason to try again. Raise `cred_attempts` only with a reason.
- **It types the username slowly below 19200 baud.** At 9600 a single fast write truncates on
  the wire -- the device echoed `ma`, then `manag`, and went straight to `Password:`, so a
  CORRECT credential was evaluated against a mangled username and failed. If the echo still
  comes back truncated, it returns False rather than submit a password that would fail and
  count. A console with echo switched off is not mistaken for a truncation.
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only (through cfg, poll).
  Re-verified 2026-10-22 on tb277, x960-56YSQ (u2) after the single-attempt fix: a good
  credential logs in in 4.3 s; a bad one returns False after **exactly one** `Login incorrect`
  (the old loop produced five); an already-privileged console returns True having submitted
  nothing.

### `ckcon.py`
Runs a list of CLI commands on one console and prints each with its output. With
`--stop-on-error` it stops at the first `% ` line that is not a known advisory (`console.ADVISORY`, the list `cfg.py` uses; since 2026-10-22, when `remote-diff all show running-config` -- whose `% Comparing ...` / `% Results are identical` lines are its report -- stopped the T17509 restore read before its `show running-config`).
- **Run:** `ckcon.py <tty> <baud> <transcript> [--stop-on-error] [--verbatim] CMD [CMD ...]`. Env `CKTO` sets the per-command timeout in seconds (default 90)
- **`--verbatim` (2026-10-27):** prints each reply as the console showed it: `<prompt><command>`,
  then every output line with its leading spaces. Use it whenever a refusal is the evidence: the
  `^` under a `% Invalid input` keeps its column, so the final log can quote it from the saved
  output (T30403's carets were only in the box's tmpfs transcript). It sends one bare CR first
  to learn the prompt. Verified 2026-10-27 on tb470 u1 (x230v2-28GS): `show ip mroute` and
  `(config)#ip mroute ...` refusals with the caret under the first unknown word.
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Limits:**
  - It does not answer (y/n) prompts; use `ckyn.py` or `cfg.py` for those.
  - It is slow on a console flooded by `terminal monitor`; use `cfg.py` there.
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only; also x230-10GP (u0) at 9600
- **Directives (2026-10-09):** a CMD that starts with `@` is not sent. `@sleep <s>` pauses; `@poll <s> <regex> <cmd>`
  re-runs `<cmd>` until its output matches `<regex>` (no spaces; use `\s`) or `<s>` seconds pass, and prints
  `@poll MATCHED|TIMED OUT after <t> s` with the last output (a link-up timer, for example). With `--stop-on-error`
  a timeout stops the run (exit 3). Verified 2026-10-09 on tb470 (x230 u0, 4050 u1, IE520 stack u5; ports run 2).

### `ckyn.py`
Like `ckcon.py --stop-on-error`, but it answers expected (y/n) confirmations:
- `YN:CMD` must prompt;
- `YN?:CMD` may prompt;
- any unexpected prompt is answered `n` and the run stops.
- **Run:** `ckyn.py <tty> <baud> <transcript> [YN:|YN?:]CMD [[YN:|YN?:]CMD ...]`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Exit codes:**
  - 2: CLI error;
  - 3: unexpected (y/n);
  - 4: no prompt after `y`;
  - 5: no prompt within 60 s;
  - 6: an expected (y/n) did not appear.
- **Status:** verified 2026-10-02 on tb470 IE520 (u3): `YN:delete flash:/<file>` answered the real (y/n)[n] prompt

### `cfg.py`
Config and show driver for chatty consoles. Each command completes on the prompt after its echo,
so streams of port-state lines don't stall it. `YN:` commands are answered `y`. It always leaves
the console at exec with `terminal no monitor`.
- **Run:** `cfg.py <tty> <baud> <transcript> [YN:]CMD [[YN:]CMD ...]`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console, awlogin
- **Exit codes:**
  - 2: CLI error;
  - 3: unexpected (y/n);
  - 5: no prompt within 90 s;
  - 6: an expected (y/n) did not appear;
  - 7: no privileged prompt.
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only (`show clock`; the YN: path not exercised)

### `qmark.py`
Read-only CLI help probe. It types `PREFIX ?` with no CR, prints the completions offered, then
clears the line with Ctrl-U. A self-test first proves that nothing gets executed. Never send
`<cmd> ?` through a CR driver instead, because that executes the command (memory
`never-send-cli-help-through-a-cr-driver`).
- **Run:** `qmark.py <tty> <baud> <transcript> [--mode CMD ... --] PREFIX [PREFIX ...]`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Limits:**
  - It relies on AW+ Ctrl-U line-kill; the self-test aborts with exit 3 if that fails.
  - `--mode` commands are executed normally, to reach the mode being probed.
  - After the probes it clears the line with Ctrl-U and leaves the mode with `end`, so the
    console is back at exec; the transcript shows it (2026-10-21: a tester read the source to
    learn this; it is stated here now).
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only (self-test passed; line left clean, checked with peek)

### `health.py`
The STANDING-ORDERS §8 health sample of one unit in ONE call, summarised. It logs in, runs
`show reboot history`, `show exception log`, `show log | include kernel|exception|crash|restart|Unexpected`,
`show cpu` and `show memory` (plus `show log tail N` for the after sample), saves every command
with its full output to `<save>` in the `HH:MM:SS >>> cmd` format (quote that in the working
log), writes a `.json` summary, and prints only the summary: entry count and newest reboot,
exception log, filtered lines split into echoes of our own commands and others, CPU busy
averages, memory free. With `--before <the before sample's .json>` it prints a HEALTH-DIFF
block (new reboot entries, exception change, new non-echo lines, the tail's line signatures
with counts and one example each, CPU and memory before -> after) and a CLEAN / DIRTY verdict.
- **Run:** `health.py <tty> <baud> <transcript> [--before SUMMARY.json] [--save FILE] [--json FILE] [--tail N] [--label TEXT] [--raw]`;
  through the wrapper `tools/tb health <TB> <run> <uN> <baud> --label before`, then
  `... --before /tmp/<run>/health-<uN>-<stamp>.out.json --label after`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console, awlogin
- **Exit codes:** 0 clean; 4 DIRTY (a new reboot entry, an exception log that is not None and
  CHANGED since the before sample, or a new kernel / crash / restart line that is not an echo:
  `NEEDS TEST ENGINEER:` and label the run confounded); 7 no privileged prompt; 2 usage.
  An exception log that is not None but byte-identical to the before sample's is printed as
  "UNCHANGED since before (pre-existing entries)" and does NOT make the run DIRTY (T17509
  review, 2026-10-22: the 10-20 stack-merge snapshots sat in every member's exception log and
  were not that run's doing). A before sample alone still reports it, so the Test Engineer can
  `clear exception log` before a campaign if they want a None baseline.
  The same rule for log lines (2026-10-27): a `kernel|exception|crash|restart|Unexpected` line
  in the after sample's tail that the before sample already held (its filtered lines or tail)
  is listed as "pre-existing" and does NOT make the run DIRTY. Before this, the boot-time
  `HTTP: HTTP server restarted` line made two clean runs read DIRTY (T31866, T30403).
  Verified 2026-10-27 on tb470 u1 (x230v2-28GS): before + after samples 1 min apart, the boot's
  `HTTP server restarted` line listed as pre-existing, verdict CLEAN, exit 0.
- **Limits:**
  - `show cpu` on AW+ prints BUSY averages (1 s / 20 s / 60 s), never idle; the summary says so.
  - A memory difference across one case is printed as a number and never called a leak.
  - An "echo" is an `IMISH[...]: [user@tty]<cmd>` line (our own typing) or its suppression note.
  - It strips the terminal-size escape AW+ prints before `show log` output.
- **Status:** verified 2026-10-21 on tb470, x230v2-28GS (u1): before sample 17 s, after sample
  with `--before` 21 s, diff CLEAN; the tail's signatures named the snmpd `send_trap` lines (12)
  and the NSM port notifications (6 each) with one example line each

### `speedrow.py`
Speed/duplex rows on a DUT port and its link partner, BOTH consoles driven from ONE process, so
the partner is polled while the DUT changes. Two console tools issued in one tool block run one
after the other (memory `two-console-calls-in-one-block-run-sequentially`; T47208 lost 4 min
and a second pass to it on 2026-10-21). Per ROW it sets the DUT, sets the partner per `--match`,
polls both ends' `show interface <port> status` in parallel until each reads connected at the
expected speed and duplex (link-up time per end), optionally waits for the LLDP neighbour on
both ends (`--lldp`), decodes the DUT's MAC/PHY TLV at the partner (`--tlv`: auto-negotiation,
advertised set, operational MAU type, polled until the MAU expected for the DUT's mode appears;
plus the reverse read at the DUT), holds (`--hold S`) and flaps the link (`--flap N --flap-end
dut|partner|both`: shutdown / no shutdown with the down time, both ends' link-up times and the
LLDP re-learn times). One summary line per row and per flap; every command and output goes to
`<save>` as `[dut] HH:MM:SS >>> cmd` / `[partner] ...` for the working log.
- **Run:** `speedrow.py <dut-tty> <partner-tty> <baud> <dut-transcript> <partner-transcript> --dut-port P --partner-port P [--match forced|always|never] [--wait S] [--lldp] [--lldp-wait S] [--tlv] [--hold S] [--flap N] [--flap-end dut|partner|both] [--no-restore] [--save FILE] ROW...`;
  through the wrapper `tools/tb speedrow <TB> <run> <dutU> <partnerU> <baud> --dut-port P --partner-port P [opts] ROW...`
- **ROW grammar:** `auto` | `auto-<speed>` | `auto-<speed>-half` | `<speed>` (fixed, partner left at auto) |
  `<speed>-full` | `<speed>-half` (forced; the partner mirrors it with `--match forced`, the default,
  and returns to auto on every other row)
- **Where:** testbox; **needs:** pyserial
- **Imports:** console, awlogin
- **Exit codes:** 0 every row linked as expected; 3 a row or flap timed out or read another
  speed/duplex; 4 a row was refused (`% ...` printed verbatim as REFUSED, the next row runs);
  7 no privileged prompt; 2 usage
- **Limits:**
  - Restore is in a `finally:`: both ends `no speed` / `no duplex`, and with `--tlv`
    `no lldp tlv-select mac-phy-config` on both. `--no-restore` leaves the last row in place.
    A bench whose saved config carries `lldp tlv-select mac-phy-config` loses it with `--tlv`;
    re-apply it after.
  - Both consoles stay in config-if for the run (`do show ...`) and are left at exec with
    `terminal no monitor`.
  - Copper only so far; a fibre module refuses most rows (reported as REFUSED).
  - A bare `auto` row expects a-full at any speed; `<speed>` fixed rows expect `full <speed>`.
- **Status:** verified 2026-10-21 on tb470, x230v2-28GS port1.0.1 (DUT, u1, AT-SPTXa) <->
  AR4050S port1.0.2 (u0): rows auto-100, 100-full, auto-1000 each linked in 1.8-3.1 s on both
  ends with LLDP in 2-4 s, one flap per row from the partner (down 0.6 s, up 3.1-4.3 s), restore
  to a-full a-1000 both ends. `--tlv` run (auto-100, 100-half): the 4050 decoded the x230's TLV
  as `Supported, Enabled` / adv `100BaseTXFD, 100BaseTX` / MAU 100BaseTXFD (16), then
  `Supported, Disabled` / adv `[none]` / MAU 100BaseTXHD (15), each within 2 s of link-up; the
  reverse read agreed; `lldp tlv-select mac-phy-config` was gone from both ports afterwards

### `peek.py`
Pre-run console check. It sends one bare CR and reports the last line: `login:`, `>`, `#`, a
config mode, or nothing. It does not log in. Use it to find a console left in config mode or a
root shell before a run.
- **Run:** `peek.py <tty> <baud> <transcript>`
- **Where:** testbox; **needs:** pyserial, `stty`
- **Imports:** none
- **Limits:** it sends one CR, so it is not strictly passive
- **Status:** verified 2026-10-02 on tb470: IE520 (u3) and x230 (u0, 9600)

### `speedrow.py`
Speed/duplex rows on a DUT port and its link partner, BOTH ends driven from one process, so
the partner is watched while the DUT changes. Per row it sets the DUT, sets the partner per
`--match`, polls both ends' `show interface <port> status` in parallel until each reads
connected at the expected speed, and optionally: waits for the LLDP neighbour on both ends
(`--lldp`), selects the MAC/PHY TLV on both ports and decodes the DUT's TLV at the partner plus
the reverse direction (`--tlv`: auto-negotiation, advertised set, operational MAU type, polled
until the MAU matches the DUT's operational mode), holds the row (`--hold S`), and flaps the
link N times from one end with link-up and LLDP timing (`--flap N --flap-end dut|partner|both`).
One summary line per row and per flap; every command with its full output goes to `<save>`
(`[dut]` / `[partner]` prefixed, `HH:MM:SS >>> cmd` format) for the working log. Both ends are
restored to `no speed` / `no duplex` (and `no lldp tlv-select mac-phy-config` with `--tlv`) in a
`finally:`, even after an error, unless `--no-restore`.
- **Run:** `speedrow.py <dut-tty> <partner-tty> <baud> <dut-transcript> <partner-transcript> --dut-port P --partner-port P [--match forced|always|never] [--wait S] [--lldp] [--lldp-wait S] [--tlv] [--hold S] [--flap N] [--flap-end dut|partner|both] [--no-restore] [--save FILE] ROW...`;
  through the wrapper `tools/tb speedrow <TB> <run> <dutU> <partnerU> <baud> --dut-port P --partner-port P [opts] ROW...`.
  ROW: `auto` | `auto-<speed>` | `auto-<speed>-half` | `<speed>` | `<speed>-full` | `<speed>-half`
  (e.g. `auto-100 10-half 1000`). `--match forced` (default) mirrors the forced rows on the partner and
  returns it to auto on the others.
- **Where:** testbox; **needs:** pyserial
- **Imports:** console, awlogin
- **Exit codes:** 0 every row linked as expected; 3 a row or flap timed out, read another
  speed/duplex, or the expected MAU was not seen; 4 a row was REFUSED (`% …` quoted); 7 no
  privileged prompt; 2 usage
- **Limits:**
  - Copper rows only have been run; a fibre module refuses most rows (reported as REFUSED).
  - Both consoles stay in config-if for the run (`do show …`) and are left at exec with
    `terminal no monitor`; two console tools in one tool block would run one after the other
    (memory `two-console-calls-in-one-block-run-sequentially`), which is why this exists.
  - It counts nothing in the device log; read that with `health.py`'s after sample.
- **Status:** verified 2026-10-21 on tb470, x230v2-28GS port1.0.1 (u1, AT-SPTXa) <-> AR4050S
  port1.0.2 (u0): `auto-100`, `100-full`, `auto-1000` with `--lldp --flap 1 --flap-end partner`
  (link back in 1.8-4.3 s, LLDP 0.6-3.7 s, restore to a-full a-1000 both ends); `--tlv` run
  the same day (`auto-100`, `10-half`).

### `awshell.py`
Runs shell commands inside an AlliedWare Plus **`start-shell` root shell** on one console,
prints each command with its output, and leaves the console back at the AW+ exec prompt.
- **Run:** `awshell.py <tty> <baud> <transcript> [--member N] [--timeout S] [--keep-shell] CMD [CMD ...]`.
  Env `CKSHTO` sets the per-command timeout (default 30 s); `CK_USER` / `CK_PASSWORD` as usual.
  Through the wrapper: `tools/tb awshell <TB> <scratch> <uN> <baud> [opts] CMD ...`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Why it exists:** *the CLI surface is not the device's surface.* An AW+ switch is Linux, and
  what no CLI command exposes is often readable and writable in `/sys` or `/proc` -- the hwmon
  sensor tree above all. The other console drivers cannot reach it: `console.PROMPT_RE` matches
  `host#` / `host(mode)#` and never the shell's `[root@host flash]#`, so every shell command runs
  to its full timeout and the driver then abandons the rest of the batch. This one completes a
  command on the shell's own `]#` / `]$` prompt.
- **Exit codes:** 0 every command ran · 2 usage · 3 no shell (`start-shell` refused, or the unit
  lacks the `ACCESS`/`FULL` feature that `start-shell` needs) · 4 a command never returned the
  shell prompt (a lost quote leaves the shell at its `> ` continuation; it then sends Ctrl-C and
  carries on) · 5 the console did not come back to the AW+ exec prompt -- the serious one, and it
  is reported rather than hidden, because a console left in a root shell makes the NEXT run's
  `show` commands answer `ash: show: not found`.
- **🔴 It is root on the DEVICE UNDER TEST.** STANDING-ORDERS §1 puts device state in play; §4
  reserves root on the **testbox**, which is a different machine. But a sysfs write is **not in
  `show running-config`, so `rcdiff.py` cannot see it and cannot prove you put it back.** Read
  every value you are about to change first, record the exact bytes (`od -c` and `wc -c`, not
  just `cat`), and read them back after restoring. A `/sys` write is also volatile: it is gone
  at the next boot, which is a restore of last resort, never a plan.
- **Limits:**
  - one command per argument, no embedded newline; the shell's own quoting applies, so a
    stray `'` leaves the shell at `> ` (exit 4);
  - `--member N` gives a stack member's shell, which is **not root**, so it cannot write `/flash`
    or most of `/sys`;
  - `start-shell` is logged on the device (`IMISH[...]: [manager@ttyS0]start-shell`), so the
    shell session is auditable -- say in the log that you used it;
  - it does not answer (y/n) prompts and does not run CLI commands: it is the shell only.
- **Status:** verified 2026-10-20 on tb277, x960-56YSQ (T33413 run 2): enumerated
  `/sys/class/hwmon/hwmon0-5`, read and rewrote `hwmon1/temp1_max` four times, and returned the
  console to `awplus#` on every one of the five invocations.

### `conlogin.py`
Logs a console OUT and back IN as a named user, and reports what the login did. This is the
instrument an AAA case needs: `aaa authentication login` only runs when somebody really logs
in, so a case that configures RADIUS, TACACS+ or local authentication has to produce a real
login attempt and grade it -- no `show` command can. A refused login is a first-class result,
not an error.
- **Run:** `conlogin.py <tty> <baud> <transcript> --user U --password P [--logout]
  [--restore-user U --restore-password P] [--no-restore] [--settle S]
  [--expect fail|priv|user]`, or `tools/tb conlogin <TB> <scratch> <uN> <baud> ...`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Output:** one line, `LOGIN RESULT: PRIV|USER|FAIL|TIMEOUT  user=<u>  seconds=<s>
  prompt=<the last line seen>`
- **Exit:** 0 privileged `#`, 1 unprivileged `>`, 2 refused, 3 nothing recognisable,
  4 **the RESTORE login failed** (the serious one -- the console may need a human), 6 usage.
  With `--expect`, 0 means the outcome matched and 5 that it did not.
- **Always restores.** Unless `--no-restore`, it ends by logging in as a fallback user
  (default `manager`/`friend`, i.e. `CK_USER`/`CK_PASSWORD`), `enable`s if it lands at `>`,
  and leaves the console at exec with `terminal no monitor`. A case that deliberately breaks
  authentication therefore still hands the console back usable.
- **Limits and traps:**
  - **An AW+ console login lands at privilege 1 (`>`) even for a `privilege 15` username**, so
    a login test's success is `USER`, not `PRIV`. Expect `priv` only after an `enable`.
  - **`--settle` must exceed the method list's fallback delay.** On an x960 with
    `aaa authentication login default group radius local` and the server unreachable, the
    local fallback took **25.5 s** -- the 25 s default read it as a TIMEOUT while the login
    actually succeeded (measured 2026-10-20, `platforms/x960.md` §7E.1).
  - It counts against a device's failed-login lockout like any other login. AW+ locks an
    account at 5 failures with a timer that restarts on each further attempt: plan the number
    of negative attempts, and never retry in a loop.
- **Status:** verified 2026-10-20 on tb277, x960-56YSQ (T33408): local login, a refused login,
  a RADIUS-served login for a user with no local account, the local fallback with the server
  down, and two console recoveries after authentication was deliberately broken

### `netlogin.py`
Logs in to a device over **TELNET or SSH** and prints EVERY byte of the login exchange, banner
included, then runs commands. It is the network twin of `conlogin.py`: that one drives a serial
console, this one drives the network management paths.
- **Why it exists:** a case about a **login-time message** cannot be graded from a `show`
  command, because the message only exists in the bytes a real login receives -- and it differs
  per access path. The AW+ default-password warning, a MOTD, a login banner and a password
  expiry warning are all in that class. It is also how a telnet or SSH *server* case proves the
  server for real: authenticate, run a command, read the output back.
- **Run:** `netlogin.py --proto telnet|ssh --host H [--port N] --user U --password P
  [--transcript FILE] [--timeout S] [--login-timeout S] [--cmd CMD]... [--no-logout]
  [--expect priv|user|fail]`, or `tools/tb tool <TB> <scratch> netlogin ...`
- **Where:** testbox (it must reach the device's management address); **needs:** nothing beyond
  Python, and the system `ssh` client for `--proto ssh`
- **Imports:** none (telnet is a raw socket with minimal IAC handling -- every option is
  refused; ssh is the system client driven through a pty)
- **Output:** the bytes before the username prompt, between username and password, and **after
  the password was sent (the login banner)** as three labelled blocks, then
  `LOGIN RESULT: PRIV|USER|FAIL|TIMEOUT|EOF  proto=  user=  seconds=`, then one block per
  `--cmd`
- **Exit:** 0 privileged `#`, 1 unprivileged `>`, 2 refused, 3 nothing recognisable, 4 the
  transport failed (`[Errno 111] Connection refused` -- which is itself a first-class result
  for an "is the server off?" control), 6 usage. With `--expect`, 0 matched and 5 did not.
- **Limits and traps:**
  - **An AW+ login lands at privilege 1 (`>`)** even for a `privilege 15` username, so a login
    test's success is `USER`, not `PRIV` (`platforms/x960.md` §7E.6).
  - It writes **no** host trust: ssh runs with `UserKnownHostsFile=/dev/null`,
    `GlobalKnownHostsFile=/dev/null`, `StrictHostKeyChecking=no`, `PubkeyAuthentication=no`.
  - **A refusal is a re-prompt, and it differs per protocol.** A refused AW+ telnet login
    re-presents `<host> login:`; a refused **ssh** login re-presents
    `<user>@<host>'s password:`, because the ssh client retries up to three times. Both are
    graded FAIL (the ssh case was added 2026-10-20 in T33411, where the wrong-shared-key
    control had really failed and the tool reported `UNKNOWN`). A device that forces a
    password change also re-prompts, but with `Enter new password:`, which does not match.
  - It counts against the device's failed-login lockout like any other login. AW+ locks an
    account at 5 failures with a timer that restarts on each attempt, so for a *refusal*
    control prefer a **non-existent username** over a wrong password for an account you still
    need -- the DUT then logs `FAILED LOGIN n ... FOR (unknown)` and the real account is
    untouched.
  - `--login-timeout` must exceed the method list's fallback delay (25.5 s against an
    unreachable RADIUS server, `platforms/x960.md` §7E.1).
  - The password is an argv value, so it is visible in `ps` on the box. Use a worthless
    credential, as the standing orders require.
- **Status:** verified 2026-10-20 on tb277, x960-56YSQ (T33378): a telnet login as `manager`
  that authenticated, listed itself as `vty 0 ... 10.38.22.33` on the DUT and returned
  `show system`; a refused telnet login for a non-existent user; and three
  `Connection refused` results used as the OFF controls of an on/off arc. Fixed in that same
  case: a refused AW+ login re-presents `<host> login:`, so the failure pattern is now tested
  FIRST and a re-presented login prompt after the password grades FAIL. Extended 2026-10-20 on
  the same box (T33411): an **ssh** password re-prompt after the password was sent now grades
  FAIL too -- verified on a TACACS+ login refused because of a wrong shared key (was
  `UNKNOWN`), and against the three TACACS+-served ssh logins in the same case that still
  grade `USER`.

### `devclient.py`
Drives a device's **own telnet / SSH CLIENT outward** from its console, and grades what
happened. The outbound twin of `netlogin.py`.
- **Why it exists:** a "Telnet Client" or "SSH Client" case is about the device **originating**
  a session. No `show` command can grade that, `netlogin.py` drives the testbox's client INTO a
  device (the wrong direction) and `conlogin.py` drives a serial console. This one types the
  client command on the device's console, answers the far end's prompts, runs commands ON THE
  FAR END and reports the outcome.
- **Run:** `devclient.py <tty> <baud> <transcript> --proto telnet|ssh --target HOST [--port N]
  [--family ip|ipv6] [--user U] [--password P | --password-stdin] [--cmd CMD]... [--hold S]
  [--expect priv|user|fail|refused] [--no-logout] [--accept-hostkey] [--timeout S]
  [--login-timeout S]`, or `tools/tb devclient <TB> <scratch> <uN> <baud> ...`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Output:** labelled blocks for the bytes before the username prompt, between username and
  password, and after the password (the far end's login banner), then
  `CLIENT RESULT: PRIV|USER|FAIL|REFUSED|TIMEOUT  proto=  target=  user=  seconds=  prompt=`,
  then one block per `--cmd`
- **Exit:** 0 remote `#`, 1 remote `>`, 2 the credential was refused, 3 the connection was
  refused or unreachable (a first-class result -- it is the control leg of an on/off arc),
  4 nothing recognisable, 5 `--expect` did not match, 6 usage, 7 **the console could not be
  returned to its local prompt** (the serious one).
- **`--family` builds the AW+ address-family keyword** (`telnet ip <host>`,
  `ssh ipv6 user U <host>`), which is what an "(IPv4)" case should exercise rather than letting
  the client choose.
- **It always recovers the console.** After `exit` it re-checks the prompt and, if the session
  is still up, uses the application's own escape -- telnet `Ctrl-]` then `quit`, ssh `~.` --
  before giving up with exit 7. Verified on a deliberately refused login that left the console
  sitting at the far end's `awplus login:`.
- **Limits and traps:**
  - **Both ends of a bench are often called `awplus`**, so the prompt text cannot say which
    device you are on. The privilege character can: the console is at `#` and a fresh remote
    login at `>`. For proof rather than a heuristic, pass `--cmd "show system"` and compare
    serial numbers.
  - **An AW+ login lands at privilege 1 (`>`)** even for a `privilege 15` username, so a client
    session's success is `USER`, not `PRIV` (`platforms/x960.md` §7E.6).
  - `--password` is an argv value and is visible in `ps` on the box; use `--password-stdin`, or
    a worthless credential, as the standing orders require.
  - A failed login counts against the FAR END's lockout. AW+ locks an account at 5 failures and
    every further attempt re-arms the timer: prefer a non-existent username for a refusal
    control, and never retry in a loop.
- **Status:** verified 2026-10-21 on tb277, x960-56YSQ swi_d (u2) driving x960-28YSQ swi_b
  (T33379): a telnet session that authenticated and ran `show system` / `show users` /
  `show telnet` on the far end (which logged it as `vty 0 cktmp ... 10.38.22.97`), a refused
  connection with the far end's server off, a refused connection to a port with no listener, a
  refused credential for a non-existent user (with automatic console recovery), the
  `--family ip` form, `--port`, `--hold`, `--password-stdin` and all four `--expect` values

### `poll.py`
Runs commands every `interval_s` for `duration_s`, stamped with epoch times. It logs in again
when the session drops, for example when the master reloads, and touches `donefile` at the end.
- **Run:** `poll.py <tty> <baud> <transcript> <interval_s> <duration_s> <donefile> CMD [CMD ...]`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console, awlogin
- **Limits:** none known
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only (3 samples in 15 s; the first interval includes the login)

### `listen.py`
Passive console recorder. It prints every line the console emits with an epoch stamp for
`listen_s`, sends nothing, and touches `donefile` at the end.
- **Run:** `listen.py <tty> <baud> <transcript> <listen_s> <donefile>`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Limits:** it does not log in, so it records only what the console prints anyway (boot output, an existing `terminal monitor` session)
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only

### `witness_log.py`
Passive witness logger for a peer unit during a reproducer. It logs in once with `terminal
monitor` on, then only reads, stamping each line with the testbox's local time.
- **Run:** `witness_log.py <tty> [<outfile>] [<baud>]`. The default outfile is `./witness-<ttyname>.log`, with the raw transcript beside it. Stop it with Ctrl-C
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Limits:** the timezone and UTC offset in its header are read once, at start
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only (header computed NZDT = UTC+13:00; clean detach on SIGINT; leaves `terminal monitor` ON, so send `terminal no monitor` afterwards)

## Reload, flash and boot menu

### `reloadc.py`
Logs in, sends a command that asks (y/n) (for example `reload stack-member 3`), answers `y`,
prints an EVENT epoch, then records the console passively for `listen_s`.
- **Run:** `reloadc.py <tty> <baud> <transcript> <listen_s> <donefile> <command...>`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console, awlogin
- **Limits:** it only answers a `(y/n)` prompt, and exits 4 if none appears
- **Status:** verified on tb470 u3, 2026-10-02 (`reload`: `y` sent, login banner after 187 s, running-config unchanged)

### `ckreload.py`
From a console already at `#`, it sends `reload`. It answers `y` only to the reboot question and
`n` to any save-config question, then waits for `login:`.
- **Run:** `ckreload.py <tty> <baud> <transcript> [wait_s (default 720)]`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Limits:**
  - It does not log in; log in first, for example with `ckcon.py`.
  - The 720 s default boot wait was measured on IE520; other products may need another value.
- **Status:** verified on tb470 u3, 2026-10-02 (reboot question only, `y`; login after 189 s; running-config unchanged); also on tb470 u0, x230v2-28GS at 115200, 2026-10-09 (5 reloads, login after 163-168 s; no save-config question asked)
- **After a reload:** `startjobs.py` (below) summarises the boot's start jobs from the same transcript.

### `startjobs.py`
Summarises the systemd start jobs of every boot in a console transcript (console.py / ckcon
transcript, or a framework `swi_*.log`): per boot, each job's longest "A start job is running
for <job> (<elapsed> / <limit>)" sighting, its limit, how it ended (`OK Finished`, `OK Started`,
`FAILED ...`, `TIME ...`), and whether a login prompt followed. A name systemd truncated
("TPM2 Acc…ement Daemon", "…gement Daemon") is resolved against the "Starting <name>..." lines,
preferring the jobs still running; an unresolvable one is shown as printed with `(?)`.
- **Run:** `startjobs.py <console-log> [--from-line N] [--to-line M] [--boot REGEX] [--all]`;
  on a testbox `tools/tb tool <TB> <run> startjobs /tmp/<run>/console-uN.log`
- **Where:** anywhere the file is; **needs:** nothing beyond Python
- **Imports:** none
- **Why:** the 2026-10-27 group 1 tester rebuilt a grep/awk pipeline for each of four x230
  reloads (review `tb470/x230v2-28GS/platform-2026-10-27T0855/REVIEW.md`).
- **Limits:** a boot starts at `--boot` (default: `Bootloader N loaded`, `BootROM`, `U-Boot N`,
  `Starting kernel`, `Booting Linux`); a transcript with no such line is read as one boot.
- **Status:** verified 2026-10-27 on tb470 `/tmp/plat-1027/console-u1.log` (4 x230v2 reloads:
  poefw 54-58 s no limit, TPM2 Access Broker to 1 min 17-22 s of ~2 min 45 s, ATMF SSHD 739 ms,
  matching the hand-built tables) and on the 2026-10-06 framework log
  `tb470/x230v2-28GS/bootloader-6.2.40/5700_x230v2-28GS_6.2.40_run2/swi_a_2001.log` (3 boots)

### `atmf_provision.py`
Provisions a future AMF node on the AMF master and undoes it, in one call (the AWPTCM-T28218
sequence): `atmf provision node NAME [device TYPE]`, `create`, `locate`, copy and set the
release file and the config file, `exit`, `show atmf provision nodes`, `show atmf backup`,
`dir recursive` of the node's directory; then the restore: `delete` (answers `y` if asked),
`rmdir` of the node directory `delete` leaves behind (the node stays listed as Provisioned until
it goes), and a final `show atmf provision nodes`. Before the steps it prints any existing
`<media>/atmf/<net>/info/backup_<NAME>.info`: provisioning REWRITES that file (2026-10-27
review, 28218-review.md).
- **Run:** `atmf_provision.py <tty> <baud> <transcript> --node NAME [--device TYPE] [--rel FILE]
  [--cfg FILE] [--set-master] [--keep | --restore-only]`; on a testbox
  `CKTO=600 tools/tb atmf_provision <TB> <run> <uN> <baud> --node future_node --rel <x.rel> --cfg <x.cfg>`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console, awlogin
- **Options:** `--set-master` configures `atmf master` if needed and `no atmf master` at the end
  (only if it set it); `--keep` leaves the node provisioned; `--restore-only` removes a node a
  cut-short run left behind.
- **Exit codes:** 0 ok; 3 a `% ` CLI error (the restore still runs if the steps had started);
  4 not master / no backup media; 7 no privileged prompt; 2 usage.
- **Limits:**
  - It does not reload. After `no atmf master`, "Restricted login" stays Disabled until a reload
    (memory `atmf-recovery-residue-and-reboots`); use `ckreload.py` if the case needs it.
  - The `info/backup_<NAME>.info` file survives `delete` and `rmdir`; the tool shows it but does
    not delete it (it may predate the run).
- **Status:** NOT yet run on hardware (written 2026-10-27 from the T28218 run1 transcript of that
  day: same commands, prompts and outputs). Argument parsing and the `show atmf` /
  `show atmf provision nodes` field parsing were checked offline against that run's saved output.
  The first run that uses it should confirm it end to end and update this line.

### `flash_copy.py`
Copies a file from any AW+ path into flash, then checks with `dir` that it landed at the right
size. The source can be another stack member's flash (`<host>-<id>/flash:/`).
- **Run:** `flash_copy.py <tty> <source> <dest> [expected_bytes] [--baud 115200] [--timeout 1800] [--log PATH]`
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Limits:**
  - It refuses if the destination already exists.
  - **Pull only:** the destination is always the local unit's `flash:/`. A push to another member
    (`IE520-stk-1/flash:/…`) is not supported, and on IE520 a large push fails anyway: `nfs: server
    192.168.255.N not responding` → `% Input/Output error due to external media removal` (re-hit
    2026-10-02, 41 MB to member 1; memory `ie520-4stack-flashprep`).
  - The 1800 s timeout fits IE520 SPIFlash, where the console is silent for about 12 min per 41 MB.
- **Status:** verified 2026-10-02 on tb470 IE520 (u3), a 1.6 KB file; fixed that day: a copy that finishes inside the first read used to wait out the whole timeout

### `tftp_copy.py`
TFTPs a file into flash (`copy tftp://<server>/<file> flash:/<dest>`), then checks with `dir`
that it landed.
- **Run:** `tftp_copy.py <tty> <tftp_server_ip> <filename> [expected_bytes] [dest] [--baud 115200] [--timeout 1800] [--log PATH]`
- **Where:** testbox; **needs:** pyserial, and a TFTP server the unit can reach
- **Imports:** console
- **Limits:**
  - It refuses if the destination already exists.
  - `dest` can be given only after `expected_bytes`.
  - A size mismatch is reported, not failed.
  - The timeout is sized for IE520.
- **Status:** verified 2026-10-02 on tb470 IE520 stack master (u5), 41,104,007 bytes in 265 s, delta +0

### `bootmenu_escape.py`
Backs a console out of the bootloader Boot Menu and lets the unit boot. Nothing is saved. It reads
which menu is on screen and sends only the key that backs out of it:
- file list (`0 to cancel) and press Enter`): `0` + Enter;
- submenu (`0. Return to previous menu`): bare `0`;
- main menu (`9. Quit and continue booting`): bare `9`, then it waits for `login:`;
- CLI or `login:` prompt: nothing;
- anything else: nothing, exit 3.

It never sends `0` on the main menu (Restart) and never `9` in a submenu (in `Select device`, 9
SAVES the default boot source).
- **Run:** `bootmenu_escape.py <tty> [--baud 115200] [--boot-wait 360]`. Exit 0 booted (or
  already at a prompt), 3 unknown state, 4 no `login:` after `9`
- **Where:** testbox; **needs:** pyserial, `stty`
- **Imports:** none
- **Limits:** the menu strings are the IE520 Boot Menu's; on another product read a bootloader
  transcript first and confirm they match
- **Status:** rewritten and verified on tb470 u3, 2026-10-02: parked in `Select device`, it sent
  CR (re-prints the menu), `0`, `9`; booted to `login:` in 188 s; no `Saving settings`; `show
  boot` and running-config unchanged. The version before it read `Enter selection ==>` as a CLI
  prompt and sent `9\r` from any menu, which in `Select device` changes the boot source

### `bootmenu_park.py`
Catches a rebooting unit at `Press <Ctrl+B>`, then sets the bootloader's default boot source to
Flash + a named file: main menu `2`, the Flash digit, the file's number + Enter, `Saving
settings... Complete`. It leaves the unit **parked at the main menu**. Release it with
`bootmenu_escape.py`, so several units can be parked first and released together (memory
`ie520-image-update-procedure`).
- **Run:** `bootmenu_park.py <tty> <flash-file> [--baud 115200] [--transcript PATH] [--reload] [--watch 600]`
  - **A stack member:** start this first, then send `reload stack-member N` on the master.
  - **The master or a standalone:** pass `--reload`. The tool logs in on the same port, sends
    `reload`, answers `y`, then watches.
- **Where:** testbox; **needs:** pyserial, `stty`
- **Imports:** console, awlogin (only with `--reload`)
- **Exit codes:**
  - 0: parked;
  - 2: unexpected screen; the unit is left in the bootloader, so read it, then run `bootmenu_escape.py`;
  - 3: no Ctrl+B prompt;
  - 7: `--reload` could not log in.
- **Limits:**
  - The menu strings are the AW+ bootloader's: IE520 9.2.0 and AR4050S 5.2.8. Check them on any
    other product first.
  - It never sends `9`.
- **Status:**
  - The park sequence ran on tb470 on 2026-10-08 as session scratch: IE520 stack members 1, 3 and
    4 plus `IE520-sa`, bootloader 9.2.0, all parked and released. On 2026-10-09 the AR4050S
    (5.2.8) was then finished by hand after the first version misread queued Ctrl+B redraws.
  - **This consolidated version** (drain the redraws, re-draw with a bare CR, `--reload` built in)
    **has not yet run on hardware**: check its first run.

## Product-specific stress

### `i2c_stress.py`
**IE520 only.** It interleaves the two i2c-taxing commands, `show platform port` and `show system
pluggable diagnostics`, N times each, and watches for the i2c lock and watchdog-reset signature.
It stops at the first lock. It never power-cycles: the IE520 watchdog self-resets about 42 s
after a lock, and the tool waits that out passively. It sends read-only `show` commands only.
- **Run:** `setsid nohup ./i2c_stress.py /dev/uN [-n 300] [--baud 115200] [--user U] [--password P] > i2c-stress.stdout 2>&1 < /dev/null &`, from a fresh dated directory, because the logs land in the current directory
- **Where:** testbox; **needs:** pyserial
- **Imports:** none (it has its own console code)
- **Detection is IE520-specific:**
  - the kernel printk `i2c i2c-0: mv64xxx: I2C bus locked`, which appears only on the unit's own console, so drive that console;
  - a command that never returns a prompt;
  - a boot banner.
- **Limits:**
  - It expects a standalone unit, and warns if `show stack` disagrees.
  - On a stacked pair `show platform port` takes about 36 s per pass, so 300 pairs take about 3.1 h.
- **Exit codes:**
  - 0: clean;
  - 1: lock or reset detected (the evidence log has the iteration, the command in flight, the epoch and the reboot history);
  - 2: aborted or wedged.
- **Status:** smoke-tested clean on tb470 2026-08-26 (evidence `IE520/i2c-stress/runs/2026-08-26-tb470-smoke/`); moved here 2026-10-02 unchanged

### `i2c_stress_fw.py`
The same stress loop as `i2c_stress.py`, as a thin wrapper over the framework's
`ATSwitch.Switch(devicePath)`, with no `.setup`.
- **Run:** `PYTHONPATH=/home/st-art setsid nohup python3 ./i2c_stress_fw.py /dev/uN [-n 300] > stdout.log 2>&1 < /dev/null &`
- **Where:** testbox; **needs:** the AT framework at `/home/st-art/framework` (read-only)
- **Imports:** the framework's `ATSwitch`
- **Limits:**
  - IE520 only, as above.
  - It uses the framework's default baud only.
  - It drops an extra `swi_noname_N.log` at construction, which is cosmetic.
- **Status:** smoke-tested clean on tb470 2026-08-26; moved here 2026-10-02 unchanged

## Config and transcript analysis

### `hostsim.py`
A fake IPv4 host on one NIC: answers ARP who-has and ICMP echo for the addresses given,
from a fake MAC, installing nothing on the host and changing no host IP, route or interface.
The IPv4 counterpart of `nsresp.py` (which answers IPv6 Neighbor Solicitations).
- **Why it exists:** several cases need a reachable neighbour that the test can make
  UNREACHABLE on demand **while the link and the switch port stay UP** -- ping polling, a
  VRRP client, a tracked next hop, an ARP ageing or deauth timeout. Shutting a port or
  pulling an address also kills the measuring instrument and changes the thing under test,
  and dropping ICMP on the box needs an iptables rule, i.e. root (STANDING-ORDERS §4).
  Touching `--mutefile`, or reaching `--mute-at`, makes it stop answering ICMP echo within
  one packet; ARP keeps being answered (unless `--mute-arp`), so the DUT's neighbour entry
  stays valid and the loss the DUT sees is a pure echo-reply loss.
- **Run:** `sudo hostsim.py <iface> <ip[,ip...]> <stats.json> [--mac MAC] [--stopfile F] [--mutefile F] [--mute-at S] [--unmute-at S] [--mute-ip IPs] [--mute-arp] [--log-echo F] [--duration S] [--no-arp] [--no-icmp] [--quiet]`
- **Where:** testbox (root); **needs:** tcpdump (only to compile the BPF filter)
- **Imports:** none
- **`--mute-ip` keeps an instrument control in the same leg.** Give it two addresses, mute
  only one, and the address that keeps answering proves the capture is alive, so the
  silence of the other is a measurement rather than a dead instrument.
- **`--log-echo F`** appends `<epoch>\t<dst>\t<src>\t<id>\t<seq>\t<answered|muted>` per
  echo request. That file IS the wire record a poll-interval measurement is read from; it
  needs no pcap decoder.
- **Default MAC** is `02:87:71:<low 3 octets of the IPv4 address>`, so each address is
  distinguishable on the wire and in the DUT's ARP table. `--mac` forces one for all.
- **Limits:**
  - IPv4 only, untagged frames only (no 802.1Q); echo REQUESTS only, nothing else is answered.
  - The NIC is in promiscuous mode while it runs.
  - It answers for an address the host's own kernel does not own; if the kernel DOES own it,
    both will answer and the DUT sees duplicates.
- **Status:** verified 2026-10-16 on tb277, host eth3 -> x960-56YSQ port1.0.10 (T44181).
  Self-test: the DUT's `ping 10.38.22.44 repeat 4` went from "0 received, 100% packet loss"
  to "4 received, 0% packet loss" with it running, and `show arp` learned
  `10.38.22.44 0287.7126.162c vlan10 port1.0.10 dynamic`. In use: carried the whole
  ping-poll measurement -- 77 echo requests logged across a timed 50 s mute window, driving
  a clean Up -> Down -> Up transition pair that the DUT's own trigger log matched to within
  1 s, with a never-muted second address as the in-leg control.

### `filewin.py`
Reads a **window** of a growing text file: the bytes it gained since a byte offset the caller
recorded earlier. The instrument for grading a case against a file some **other** process keeps
appending to -- a TACACS+ accounting file, a syslog, a RADIUS detail file, a daemon log -- where
the whole file is history and only this case's own window is evidence.
- **Why an offset and not `tail -n`:** a tail of N lines is not a window. It silently drops
  evidence when the writer is busy and silently re-reads old records when it is idle, and
  neither failure is visible in the output. An offset recorded before the step bounds the window
  exactly, and the header says how many bytes arrived -- so **zero new bytes is a measurement**,
  not an absence of output.
- **Run:** `filewin.py <path> [--from OFFSET] [--grep REGEX] [--max-lines N] [--quiet]`, or
  `tools/tb tool <TB> <scratch> filewin /var/log/tac_plus.acct --from 1234`.
  To mark: `--quiet` with no `--from`, and record `size=` from the header.
- **Where:** anywhere (on the box for a server-side file); **needs:** nothing beyond Python
- **Imports:** none
- **Output:** one header line
  `FILEWIN <path> size= from= new-bytes= new-lines= matched=`, then the matching new lines
  unchanged
- **Exit:** 0 read; 3 absent or not readable (a first-class result: a server that never wrote
  anything, or a file the case may not read); 4 the file SHRANK below `--from` -- it was rotated
  or truncated, the window is not trustworthy, and everything from byte 0 is printed instead;
  6 usage
- **Limits:** text files only (bytes are decoded UTF-8 with replacement); it does not follow a
  rotation to the rotated-out file; a trailing partial line is printed, because a writer caught
  mid-append is still evidence. It reads only and writes nothing anywhere.
- **Status:** verified 2026-10-20 on tb277, x960-56YSQ (T33411/T33410/T33412): marking and
  windowing `/var/log/tac_plus.acct` across every accounting leg, the rotation guard and the
  unreadable-file exit tested offline

### `rcdiff.py`
Unified diff of the first FULL `show running-config` in two saved `ckcon.py` / `cfg.py` **stdouts** (not the
`<transcript>` argument, which has no `>>>` headers). This is the pre-case versus post-case teardown check
(STANDING-ORDERS §1).
- **Run:** `rcdiff.py [--last] <before.log> <after.log>`; exit 0 = no difference, 1 = difference printed, 2 = a file
  with no full dump (or unreadable)
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** none
- **Limits:**
  - it needs `HH:MM:SS >>> cmd` headers (an epoch prefix, as `cfg.py` prints, is accepted), and exits 2 on a
    file with no running-config. Only a header whose command is exactly `show running-config` counts.
    **Fixed 2026-10-21:** it used the first match of the text, so a `show running-config | include ...`
    earlier in the same capture gave a false diff (128 lines on T17584, tb101). `--last` uses the last full
    dump when a file has several.
  - ⚠ **an "empty" diff can still print one spurious `-HH:MM:SS` line** when the
    `show running-config` is immediately followed by the next command's timestamp header, which
    it mistakes for a config line (tb277, 2026-10-21, T33398). Read what the line IS before
    treating it as config drift; a direct `diff` of the extracted `show running-config` bodies
    is the tie-breaker.
- **Status:** verified 2026-10-02 on tb470 (two real IE520 captures, identical -> no output). 2026-10-21 on
  T17584's captures (tb101): the raw pre-run file now gives no diff, a changed `stack 1 priority` line is
  caught (exit 1), and a file with no dump exits 2. The spurious-line limit measured 2026-10-21 on tb277

### `rc2cfg.py`
Turns the first `show running-config` in a saved `ckcon.py` stdout into a loadable per-device
`<dev>.cfg` (logged-output.md §2): the given header lines first (each prefixed `! `), then the
config with the echoed command, bare prompts, pager remnants, CRs and blank lines removed.
- **Run:** `rc2cfg.py <ckcon-stdout> <out.cfg> <header-line> [<header-line> ...]`
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** none
- **Limits:** it reads the ckcon `HH:MM:SS >>> cmd` stdout format only (as `rcdiff.py` does)
- **Status:** verified 2026-10-08 on tb470, IE520 stack master (u5): T22650 `stk_a.cfg`, 186 config lines

### `bondctl.py`
Builds or removes a Linux bonding interface (`802.3ad` by default) from host NICs, for a LAG case
whose partner is the testbox itself, and restores the NICs' addresses exactly. `up` records
`ip -br addr` and each NIC's global addresses into a state file FIRST, then creates the bond,
flushes and enslaves the NICs; `down` releases them, deletes the bond, re-adds every recorded
address with `ip addr replace`, and diffs `ip -br addr` against the recording (`RESTORE DIFF:
empty`, else the diff and exit 1). Every `ip` command is printed before it runs and the first
failure stops it. `status` prints `/proc/net/bonding/<bond>`.
- **Run:** `sudo bondctl.py up <bond> <state.json> NIC [NIC ...] [--mode 802.3ad] [--miimon 100] [--lacp-rate fast] [--xmit-hash layer2]`;
  `sudo bondctl.py down <bond> <state.json>`; `bondctl.py status <bond>`
- **Where:** testbox (root; `tools/tb sudotool <box> <scratch> bondctl ...`); **needs:** iproute2, the bonding module
- **Imports:** none
- **Limits:**
  - It is a root CHANGE on the host, not test traffic: use it only when the Test Engineer has allowed the
    bond for the case (STANDING-ORDERS §4; tb101 2026-10-21, "sudo -n for the bond and its restore").
  - It stays in `tools/` and in `tools/tb`'s `SUDO_TOOLS` by the Test Engineer's decision, 2026-10-21: "yes, save it
    in tools". That makes it available to any case; it does not replace the per-case OK above.
  - It does not stop NetworkManager or systemd-networkd from re-applying addresses to a slave; check
    `ip -br addr` after `up` and report what the host did.
  - `up` refuses if the bond already exists; `down` only restores what `up` recorded.
- **Status:** added 2026-10-21 for tb101 T17584 (host bond0 = eth3 + eth4 as the LACP partner of an IE520 stack po1); see that run's working log for its verification

### `hostinfo.py`
Read-only inventory of a testbox HOST before a traffic or bonding case: which service manages
the NICs (NetworkManager, systemd-networkd, ifupdown, netplan), addresses and link details,
bonding interfaces already present, the bonding module, whether `sudo -n` is available, and the
tcpreplay / tcpdump / scapy versions. It changes nothing.
- **Run:** `hostinfo.py [NIC ...]` (per-NIC `ip -d link`, `ethtool`, routes for each NIC named);
  `hostinfo.py --stats NIC [NIC ...]` prints only each NIC's `ip -s -s link` and `ethtool -S` drop/miss/error/fifo
  counters (added 2026-10-21: tells a host-side receive loss from a DUT loss after a line-rate window)
- **Where:** testbox (no root); **needs:** nothing beyond Python; `nmcli`/`ethtool` optional
- **Imports:** none
- **Limits:** `sudo -n true` is the only privileged call, and it only reports yes/no
- **Status:** added 2026-10-21 for the tb101 T17584 triage (host bond for LACP); verified that day on tb101

### `ckcase.py`
Prints a test case's authored text (objective, precondition, steps) from the Ask-CK database.
Lookup order: `zephyr_cases` keyed on the AWPTCM id exactly as the Test Engineer writes it
(`AWPTCM-T43870`), then `testlink_cases` joined on `--title` for the legacy `AWP-nnnn` corpus.
- **Run:** `ckcase.py <KEY> [KEY ...] [--db PATH] [--title TEXT] [--columns] [--raw-steps]`
- **Where:** a testbox, or a dev host that mounts the lab home. With no `--db` it takes the
  first ck.db it finds: `$CK_DB`, the Test-cases checkout beside this repo (from the tool's own
  path), then `~/claude/Test-cases/ask-ck/db/ck.db` (2026-10-27: every dev-host campaign
  first failed without `--db`). **needs:** nothing beyond Python
- **Imports:** none
- **Limits:**
  - It opens the database read-only (`file:...?mode=ro`); never open it read-write while the CK
    server is running.
  - `steps` is usually HTML/JSON and is suppressed unless you pass `--raw-steps`; the readable
    procedure is normally in `precondition` or `steps_text`.
  - Exit 1 means the key matched nothing -- which is a real answer, not an error.
- **Why it matters:** memory `ckdb-case-lookup-by-title` says AWPTCM ids are absent from ck.db
  and that you must join on title. **That is out of date.** `zephyr_cases` (45k rows) is keyed
  on `AWPTCM-T<id>`, and five of the ten cases in the 2026-10-16 tb277 campaign had full
  authored procedures there. Check this before designing a case from scratch.
- **Status:** verified 2026-10-16 on tb277 (T43870: objective, the verbatim config block and a
  9-step procedure with exact OIDs)

### `case_tokens.py`
Per-case token usage and process metrics from a tester's Claude Code transcript, for
`/create-logs`' process review (logged-output.md §5). Splits the transcript at the tester's
`RESULT <id>` lines: a case runs from its first tool call into its own `<id>/` folder to its
`RESULT`; everything else is group overhead. Per segment: API calls, input / cache-write /
cache-read / output tokens, tool calls by name, wall time, characters of tool output read back,
the five largest outputs and the commands repeated verbatim.
- **Run:** `case_tokens.py --find ~/.claude/projects/<repo slug> --cases <id,id,...> [--json]`,
  or `--transcript <file.jsonl>` instead of `--find`
- **Where:** the dev host that ran the session (transcripts are local); **needs:** nothing beyond Python
- **Imports:** none
- **Limits:** needs the `RESULT` SendMessage lines (logged-output.md §2); a case that never
  touched `<id>/` before its RESULT counts from the RESULT call alone
- **Status:** verified 2026-10-08 on the modbus group (T22650–T22655, one bench-runner transcript); 2026-10-12 also matches `RESULT T<id>` and RESULT lines batched in one message (x230 campaign, 4 transcripts)

## Traffic, frames and protocol emulators

### `linerate.py`
Sends a UDP stream at a set rate, up to 1G line rate, from one host NIC and counts what arrives
on the others. It uses tcpreplay and tcpdump.
- **Run:** `sudo linerate.py --tx NIC --dst-mac MAC [--rx NIC,NIC] [--rate Mbps|top] [--secs 10] [--size 1500] [--dport 9] [--sport 5010] [--ttl 2] [--src-mac M] [--src-ip IP] [--dst-ip 192.0.2.1] [--pcap PATH] [--ipv6] [--src-macs N] [--mac-prefix 02:cc:00:00] [--rx-mac MAC|any] [--rx-len]`
- **Options added 2026-10-09:** `--rx-mac` counts frames arriving with that source MAC (a router's egress MAC: routed
  traffic is re-sourced, so the default sender-MAC filter counts 0) or `any`; `--rx-len` counts only frames of exactly the
  length sent (a lost or extra tag is then not counted); `--ipv6` builds IPv6/UDP (`--ttl` = hop limit; needs `--src-ip`
  and `--dst-ip`); `--src-macs N` rotates N source MACs (the sender's, then `--mac-prefix`:xx:xx, default 02:cc:00:00; give
  each direction its own prefix so two senders never share a MAC). The receive filter now
  always names `ip`/`ip6`.
- **Where:** testbox (root); **needs:** scapy, tcpreplay, tcpdump, iproute2
- **Imports:** none
- **Limits:**
  - About 984 Mbps of frame bytes measured on 1G NICs.
  - UDP only (IPv4 or, with `--ipv6`, IPv6).
  - The pcap is a temporary file unless `--pcap` is given.
- **Status:** verified on tb470 2026-10-02 at `--rate 10 --secs 5`: 4178 sent (10.2 Mbps on the wire), 4178 received on eth3, 0 kernel drops. Line rate itself not re-run. 2026-10-09 on tb470 (x230 T38294): line rate re-run, 822501 frames at 999.7 Mbps on the wire bridged; routed with
  `--rx-mac --rx-len` at 1500/1518/64 bytes, 100% counted (64-byte frames top out at ~274 kpps from this host)

### `l2flows.py`
Runs four sequence-numbered L2 flows between two host NICs, through the DUT, and records every
frame received. The flows are broadcast and unicast, in each direction. Use it for continuity
across a failover or a ring switch-over.
- **Run:** `sudo l2flows.py <duration_s> <pps_per_flow> <outdir> <nicA> <nicB> [--ethertype 0x88B5] [--per-link N]`
- **`--per-link N` (added 2026-10-21):** each flow becomes N sub-flows `<tag>.1`..`<tag>.N`, each with its own source
  MAC `02:4c:<nic MAC byte 5>:<byte 6>:<a0|b0>:<k>` and its own sequence numbers, at `pps_per_flow` each. A host bond or
  a DUT LAG hashes on the source MAC, so the sub-flows spread over the links and an event on ONE link shows as an
  outage on the sub-flows that sat on it. Without it every flow sits on one link (T17584 E2, tb101: the flows could not
  see a leg shutdown). Use N of at least twice the number of links. The sub-flow number travels in the first padding
  byte (0 = none), so N = 1 writes the old format exactly. The DUT learns 2 x N extra source MACs.
- **Where:** testbox (root); **needs:** Python only (AF_PACKET, Linux)
- **Imports:** none. It provides `flow_tags` to `flowstat.py` and `loopwin.py`
- **Limits:**
  - Exactly two NICs.
  - The flow tags come from the last character of each NIC name, or A/B if those match.
  - Pacing is Python sleep.
- **Status:** verified on tb470 2026-10-02: 10 s, 20 pps per flow, eth1 <-> eth3 through the stack; 4 x 200 frames, 0 lost.
  `--per-link` tested OFFLINE only, 2026-10-21 (a fake socket layer between two simulated NICs: 4 x 3 sub-flows, one
  sub-flow made to lose 10 frames showed a 500 ms outage and its siblings none; N = 1 output unchanged). Not yet run on
  hardware.

### `eventwin.py`
One traffic EVENT WINDOW in one call (built 2026-10-21 from T17584, where each of 6 events took 15-20
hand-made tool calls): starts `l2flows.py` (and optionally `linerate.py` both ways) with `sudo -n`, runs
timed console actions and reads through the console tools, polls until the DUT is ready, waits for the
traffic to end, then runs `flowstat.py` (with every action's event time) and `loopwin.py`, and writes
one `summary.txt`.
- **Run:** on the box, as the user: `tools/tb tool <TB> <scratch> eventwin --out /tmp/<scratch>/eN --nic-a NIC
  --nic-b NIC [--flows-secs 360] [--pps 100] [--per-link N] [--rate Mbps|top --rate-secs 300 --a-dst-mac MAC
  --b-dst-mac MAC [--a-src-ip IP] [--b-src-ip IP] [--src-macs 16]] [--act AT TOOL uN ARG ...]... [--read AT uN CMD
  ...]... [--bond BOND] [--poll uN SECS REGEX CMD] [--after uN CMD ...]... [--stats-nics a,b,c] [--baud 115200]
  [--save DIR] [--dry-run]`. TOOL is cfg, ckcon, ckyn, reloadc, ckreload or listen; every act except `listen` is
  an event (ev0, ev1 ... in flowstat), timed by the tool's own output (reloadc `EVENT y-sent`, else the header of
  the last command that is not `end`/`exit`/`configure terminal`). `--save` copies every text result into one
  folder per event (e.g. the case's `work/eN` on the NFS home) so the final log quotes the reads verbatim.
  Example (T17584 E3 shape): `--act 10 listen u0 330 /tmp/s/e3-u0.done --act 25 reloadc u1 240 /tmp/s/e3.done
  reload stack-member 1 --read 90 u2 "show stack" "show lacp sys-id" --poll u2 330 '1\s+-\s+84e3\.2787\.0ac0\s+1\s+Ready'
  'show stack' --after u2 "show etherchannel detail" --bond bond0`. Check the plan first with `--dry-run`.
- **Where:** testbox, from a `tools/tb scratch` copy (transcripts go to `/tmp/<scratch>/console-uN.log`, the path the
  sentinel watches); **needs:** `sudo -n` for the traffic tools, plus what those tools need
- **Imports:** none; runs `l2flows.py`, `linerate.py`, `flowstat.py`, `loopwin.py`, `hostinfo.py` and the console
  tools from its own directory
- **Limits:**
  - One console is used by one action at a time (a lock); an action waits while a `listen` holds its console.
  - A console another process holds (`fuser`) is not opened: the action is skipped and reported.
  - `--out` must not exist yet; the raw flow files stay there (they can be several MB) and are not copied by `--save`.
  - Exit 1 when any step failed: a held console, a tool's non-zero exit, a `!!!` line, or a `% ` line other than
    `remote-diff`'s own `% Comparing` / `% Results are identical`.
  - It runs for the whole flow time; call it from a backgrounded `tools/tb` command and wait on the summary.
- **Status:** tested OFFLINE only, 2026-10-21: `--dry-run` on an E3-shaped plan, the usage errors, and a full run
  through a harness with stub console and traffic tools (real `flowstat.py`/`loopwin.py`): event times taken from the
  tools' output, every read saved, a stubbed `% Invalid input` caught (exit 1). Not yet run on hardware.

### `flowstat.py`
For an `l2flows.py` run, reports per flow:
- the sent, received, lost and duplicate counts;
- outages of 2 or more frames, timed against event epochs;
- the longest outage and the latency.
- **Run:** `flowstat.py <outdir> <nicA> <nicB> [event_epoch ...]`
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** l2flows
- **Limits:**
  - Give it the same `nicA` and `nicB` as the run.
  - Single lost frames are counted but not listed. That was fixed 2026-10-02 to match the documentation; earlier output listed them.
  - A `--per-link` run (2026-10-21): each sub-flow is reported on its own, then one `<tag> ALL` line per flow with the
    totals, the longest outage of any sub-flow, and how many sub-flows had an outage of 5 frames or more.
- **Status:** verified on tb470 2026-10-02 on that `l2flows.py` run: 0 lost, 0 dups, median latency ~0.37 ms.
  2026-10-21 regression on tb101 (T17584's E3 flow files): output byte-identical to the original analysis.

### `loopwin.py`
Finds windows of loop evidence in an `l2flows.py` run: duplicates, and frames echoed back to
their sender. Windows are clustered with a 1 s gap.
- **Run:** `loopwin.py <flowsdir> <nicA> <nicB>`
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** l2flows
- **Limits:** give it the same `nicA` and `nicB` as the run. Reads `--per-link` sub-flow tags (2026-10-21).
- **Status:** ran on tb470 2026-10-02 on a loop-free `l2flows.py` run: 0 windows, as expected. 2026-10-21 on tb101
  (T17584 E3): found the one 30 ms window of 4 duplicated broadcast frames, the same as during the run

### `vsend.py`
Sends a burst of `CKVLAN`-marked frames of one kind: IPv4, IPv6, IPX, another EtherType, or ARP.
They can be 802.1Q or QinQ tagged.
- **Run:** `sudo vsend.py <iface> <count> <spec> [--src MAC] [--dst MAC] [--vlan V] [--outer O] [--tag TEXT] [--sip IP] [--dip IP] [--sport N] [--dport N]`
- **Where:** testbox (root); **needs:** scapy
- **Imports:** none
- **Limits:** the spec's default addresses are private 192.168.x test addresses; set `--sip`/`--dip` to match the DUT's config
- **Status:** verified on tb470 2026-10-02: 10 x ip10 + 10 x ipv6, eth1 -> stack VLAN 1 -> eth3, all 20 counted by `vcount.py`

### `vcount.py`
Counts captured `CKVLAN`-marked frames per burst, VLAN tags, EtherType, destination and source.
Unmarked frames are listed separately. It is the receiving side of `vsend.py`.
- **Run:** `vcount.py <pcap> [<pcap> ...]`
- **Where:** anywhere; **needs:** scapy
- **Imports:** none
- **Limits:** none known
- **Status:** verified 2026-10-02 on tb470 (scapy 2.6.1; unmarked frames counted)

### `lacpdu.py`
Decodes the LACPDUs in a tcpdump pcap (EtherType 0x8809, subtype 1) and prints, per sending MAC, the
count and the last PDU's actor and partner fields: system priority, system MAC, key, port, and the
state byte decoded (Act, Short, Agg, Sync, Coll, Dist, Def, Exp). The proof that a LAG partner
advertises a given system id (a VCStack's virtual MAC) and is Collecting/Distributing.
- **Run:** `lacpdu.py <pcap> [<pcap> ...]` (capture with `tools/tb capture <box> <scratch> <nic> <secs> <out> ether proto 0x8809`)
- **Where:** anywhere; **needs:** nothing beyond Python (its own pcap reader, link type 1 only)
- **Imports:** none
- **Limits:** classic pcap only (not pcapng); it reports the LAST PDU per sender, not every change
- **Status:** added 2026-10-21 for tb101 T17584 (IE520 stack po1 <-> host bond0); see that run's working log

### `mkpcap.py`
Writes a pcap of routed UDP frames, one per destination address, or all to one address with
`fixed`. Use it with tcpreplay for table-fill and line-rate tests.
- **Run:** `mkpcap.py <v4|v6> <src_mac> <dst_mac> <src_ip> <dst_base_ip> <first> <count> <frame_len> <out.pcap> [fixed] [--dport 9] [--sport-base 40000] [--ttl 64]`
- **Where:** anywhere; **needs:** scapy
- **Imports:** none
- **Limits:** UDP only; `frame_len` excludes the FCS
- **Status:** verified 2026-10-02 on tb470 (v4 and v6 pcaps, scapy 2.6.1)

### `mkmc.py`
Writes a pcap of sequence-numbered IPv4 multicast UDP frames from a fake source to a group.
- **Run:** `mkmc.py <src_mac> <src_ip> <group> <frame_len> <count> <out.pcap> [--sport 5000] [--dport 5001] [--ttl 16]`
- **Where:** anywhere; **needs:** scapy
- **Imports:** none
- **Limits:** IPv4 only
- **Status:** verified 2026-10-02 on tb470 (scapy 2.6.1)

### `igmp.py`
Sends IGMP joins (Membership Reports) or leaves from a fake receiver host, **v2 or v3**.
- **Run:** `sudo igmp.py <iface> <join|leave> <group> <src_ip> <src_mac> [count=2] [interval_s=0.5] [-2|-3] [--source A[,B]] [--record TYPE]`
- **Where:** testbox (root); **needs:** scapy (`contrib.igmp`, `contrib.igmpv3`)
- **Imports:** none
- **`-3` is what an SSM case needs.** PIM-SSM is *defined* by the (S,G) join, and IGMPv2 cannot
  carry a source list, so an SSM verdict cannot be reached with the v2 path. `--record` takes
  `is-include | is-exclude | to-include | to-exclude | allow | block`; the default is
  `to-include`, which is what a real host sends when it joins an SSM channel, and a `leave` with
  no `--record` becomes `to-include` with an EMPTY source list, which is how IGMPv3 leaves an
  include-mode group. An IGMPv3 report goes to 224.0.0.22, a v2 report to the group and a v2
  leave to 224.0.0.2; the tool picks the right destination and link-layer address for each.
  `--source` with `-2` is refused rather than silently ignored.
- **Limits:**
  - `src_ip` must be a real on-subnet address; AW+ drops reports from 0.0.0.0.
  - One group record per call.
  - 🔴 **The receiving ROUTER usually needs more than PIM.** On AW+ (x960, 2026-10-16) a report
    reaches the IGMP *snooping* table and shows up in `show ip igmp groups` even when
    router-side IGMP is disabled, and PIM then never sees the membership and nothing forwards.
    If a join "works" but no traffic arrives, check `show ip igmp interface <if>` for
    `IGMP Disabled, Active(Snoop Only)` before suspecting this tool (finding F-13).
- **Status:** v2 verified 2026-10-16 on tb277 (x960-56YSQ + x950 GEN2, joins and leaves driving
  real PIM-SM trees and a measured group-specific prune); **v3 added 2026-10-16** for T43865.

### `arpleg.py`
One **test leg** in one command: start `tcpdump` on every NIC named, send a known count of
crafted frames from one of them, stop, then decode the captures and print a grouped count of
everything seen — with the **Ethernet source and destination of every flow**, so the question
"who answered, and with which MAC?" is read off the wire instead of a `show arp` read-back
(STANDING-ORDERS §7). Written for the ARP cases (static ARP, clear ARP, ARP logging, proxy ARP,
local proxy ARP, web-auth ARP polling) but it is generic: any case that needs "send this, capture
there, tell me what came back".
It replaces the per-case `runleg.sh` heredocs that the 2026-10-15 process reviews named as the
campaign's single largest avoidable cost.
- **Run:** `sudo arpleg.py --tag NAME --out DIR --iface eth3 [--watch eth4 ...] [--show-ttl] [--arp TGT[,TGT]] [--probe DST[,DST]] [--icmp DST[,DST]] [--answer IP=MAC[,IP=MAC]] [--answer-iface eth3,eth4] [--announce] [--sender-ip IP] [--sender-mac MAC] [--gw-mac MAC] [--count N] [--vlan V] [--settle S] [--wait S] [--filter BPF] [--sniff-only] [--no-promisc] [--top N]`
- **Where:** testbox (root — raw sockets + tcpdump); **needs:** scapy, tcpdump
- **Imports:** none
- **`--answer IP=MAC` makes the DUT learn a DYNAMIC entry.** A background responder answers ARP
  requests for those addresses for the duration of the leg, one per `--answer-iface` (a comma
  list; they share one table and each only ever sees its own wire), and the leg prints how many
  replies it sent. **You need it**: measured on an x960-56YSQ 2026-10-15, this DUT does NOT create
  a dynamic ARP entry for a neighbour that merely sends it an ARP request — not even a request
  for the DUT's own address, which RFC 826 says should populate the table. Only a neighbour that
  ANSWERS the DUT's own request is learned. Ending the leg stops answering, which is how a poll,
  ageing or deauth timeout is driven. `--announce` sends the `--arp` specs as gratuitous ARP
  replies instead of requests.
- **Two independent counters:** it prints what it **sent** beside what the **capture** holds, and
  exits **7** when the sending NIC's capture holds fewer of its own marked frames than it sent.
  Marked frames carry `CKARPLEG-<tag>` in the payload and are flagged `[ours]` in the report, so
  the tool's traffic is never confused with the bench's.
- **`--udp DST[:PORT]` + `--l2-dst broadcast` is how you test a broadcast-forwarding feature.**
  `--probe` hardcodes dport 9 and sends to `--gw-mac`; a UDP-helper or directed-broadcast case
  needs a CHOSEN destination port and a true link-layer broadcast. `--l2-dst` applies to
  `--udp` only, so one leg can carry the broadcast flow AND a routed unicast `--icmp` control
  that must arrive. Pair a matched port with an unmatched one in the same leg (added 2026-10-16
  for T44378/T44182).
- **An IPv4 MULTICAST `--udp` destination derives its own link-layer address** (RFC 1112 §6.4,
  `01:00:5e` + the low 23 bits) when no `--l2-dst` is given, so ONE leg can carry the subject
  group and a never-joined control group each correctly addressed -- which is exactly what a
  multicast verdict needs and what a single `--l2-dst` could not give. An explicit `--l2-dst`
  still wins, so a deliberately MISMATCHED L2 address stays testable. Added 2026-10-16 for the
  tb277 PIM group; verified in-leg (239.1.1.1 -> 01:00:5e:01:01:01 beside
  239.9.9.9 -> 01:00:5e:09:09:09).
- **A PER-SPEC Ethernet destination: `--udp DST[:PORT][@SRC][%L2DST]`.** `--l2-dst` applies to
  **every** `--udp` spec, so it cannot carry a subject and a control that differ only in their
  link-layer address. `%L2DST` can: a first-hop-redundancy case sends one flow to the VRRP
  virtual MAC and, in the SAME capture, a control flow to a MAC nobody owns, which must be 0.
  `%broadcast` works too, and an explicit `%L2DST` beats both `--l2-dst` and the derived
  multicast address. Added 2026-10-16 for tb277 T47873.
- **`--show-ttl` appends the received IPv4 TTL to every flow in the report.** The TTL is the
  only field on the wire that says **how many routers forwarded** a frame, so when two routers
  share one virtual MAC (VRRP, or any first-hop redundancy) the hop count is what attributes a
  forwarded frame to ONE of them -- the Ethernet and IP headers are identical either way. It is
  equally the check for a TTL-rewriting or extra-hop defect. Off by default, so existing legs
  read exactly as before. Added 2026-10-16 for tb277 T47873.
- **`--tcp DST[:PORT][@SRC][%L2DST]` sends a crafted TCP SYN and reports the reply FLAGS.**
  Added 2026-10-21 for the management-ACL case T33386. A management filter has **three**
  possible answers and only the wire tells them apart: `SA` = the port is open, `R`/`RA` = the
  service refused it, and **no reply row at all** = the frame was silently dropped by a filter.
  `show access-list counters`, `show ssh server` and `show telnet` can distinguish none of them
  (`platforms/x960.md` §5 and §7F.2). The default port is 22; `@SRC` and `%L2DST` parse exactly
  as they do for `--udp`, so one leg carries the denied source and the permitted control
  together. The SYN carries the usual `CKARPLEG-<tag>` payload so `[ours]` and the two-counter
  guard apply to it — data on a SYN is legal and a Linux-based target answers it normally, but
  **always run the filter-OFF baseline leg first**: a `SA` there proves the instrument before
  any later silence is read as a filter.
- **🔴 scapy marker trap (measured on tb277 2026-10-16):** the tool marks its own frames with
  `CKARPLEG-<tag>` in the payload. scapy dissects well-known UDP ports into their OWN layer --
  69 becomes TFTP, 67/68 BOOTP, 53 DNS -- so for those ports there is **no `Raw` layer at all**
  and a check of `pkt[Raw].load` finds nothing: a `--udp ...:69` burst reported 0 of 5 frames
  as `[ours]` and the leg exited 7 with a false COUNTER DISAGREEMENT. Both the mark and the
  counter now scan `bytes(pkt)`, the whole frame. Same family as the `dhcp4.py` BOOTP trap;
  any other scapy tool that marks payloads needs the same treatment.
- **Limits:**
  - `--probe` / `--icmp` need `--gw-mac` (the L2 next hop, i.e. the DUT's SVI MAC); `--arp` does not.
  - Output goes to `--out`, which should be a **local `/tmp` path on the box**: tcpdump runs as
    root and cannot write the root-squashed NFS lab home (memory `tcpdump-nfs-root-squash-capture`).
    Pcaps are chowned back to `SUDO_UID` at the end, so copy them down afterwards.
  - It does not answer anything. For a leg that must respond, pair it with a responder
    (`nsresp.py`, `dhcp4.py`, `dnsresp.py`).
  - scapy on tb277 (2.4.4) imports matplotlib, which prints a `SyntaxWarning` on stderr. Harmless.
- **Status:** `--tcp` verified 2026-10-21 on tb277, x960-56YSQ (T33386) — see that case's log.
  Otherwise verified 2026-10-15 on tb277, host `eth3`/`eth4` → x960-56YSQ `port1.0.10`/`port1.0.48`.
  Self-test: 3 ARP requests sent, 3 in the capture, both MACs decoded. In use: T33248 proved a
  static ARP entry rewrites 5/5 routed frames to the configured MAC while a control address with
  no entry forwards 0/5 in the same leg; T33247 drove `--answer` to populate and re-populate the
  DUT's dynamic cache and told the three `clear arp-cache` forms apart on the wire. Used for
  every leg of the `arp-2026-10-15T1747` group.

### `ecmpflows.py`
Sends **many flows with different 5-tuples** through a router and reports what came back, for
load-sharing tests: ECMP, and equally a LAG or any "does it spread, and across which ports?"
question. A single flow can legitimately sit on one path, so one flow proves nothing; this is the
stimulus that makes the question answerable. It builds N flows differing in source IP,
destination IP, source port and destination port (**any subset, chosen with `--vary`** -- that
option is the whole point, see the trap below), sends M frames of each from one host NIC at L2
with an explicit next-hop MAC, and unless `--no-capture` runs tcpdump on the sending NIC and
groups what it caught.
- **Run:** `sudo ecmpflows.py --tag NAME --out DIR --iface eth3 --gw-mac MAC [--flows 64] [--per-flow 10] [--proto udp|tcp|icmp] [--vary src,dst,sport,dport] [--src-base IP] [--dst-base IP] [--src-span N] [--dst-span N] [--sport-base N] [--dport-base N] [--ttl N] [--size N] [--gap S] [--settle S] [--wait S] [--filter BPF] [--no-capture] [--top N]`
- **Where:** testbox (root -- raw sockets + tcpdump); **needs:** scapy, tcpdump
- **Imports:** none
- **It is the stimulus, NOT the counter.** The verdict comes from per-egress-port counters read
  on the devices (`show interface <port>` before and after, differenced). Measure the idle drift
  first -- on tb277 it was ~1.6 packets/s per port of STP/LLDP, symmetric across ports, which is
  2-3% of a 1280-frame leg and cannot manufacture a split.
- **`--vary` and the correlation trap (measured 2026-10-15, and it cost a leg).** Flows are built
  from one index `i`, so `--vary src,dst` moves BOTH addresses together. If the device hashes on
  the two addresses, lockstep inputs largely cancel and an even hash reads as a lopsided one --
  an x960-56YSQ gave 81/19 that way and 50/50 once the addresses were decorrelated with
  `--src-span 64 --dst-span 7`. **Vary one field per leg to characterise the hash; decorrelate
  the spans for a realistic mixed leg.**
- **Far-side attribution with no host behind the router:** point the flows at a prefix that is
  unrouted ON the far-side routers. Each router that receives a flow answers with an ICMP
  destination-unreachable **from its own address**, and the tool prints "ICMP unreachables by
  SOURCE", so the wire says which next hop got traffic. ICMP unreachable generation is
  rate-limited (2 per router per leg on an x960), so this is qualitative -- which routers --
  while the counters carry the quantity. The source address needs to be resolvable by the
  router, so prime its ARP first (`arpleg.py --answer`).
- **Two independent counters:** it prints what it sent beside what the capture holds, marks every
  payload `CKECMP-<tag>`, and exits **7** when the sending NIC's capture holds fewer marked
  frames than it sent, so a dead instrument can never be read as a result.
- **Limits:**
  - `--out` must be a **local `/tmp` path on the box**: tcpdump runs as root and cannot write the
    root-squashed NFS lab home (memory `tcpdump-nfs-root-squash-capture`).
  - IPv4 only.
  - It does not read device counters and does not answer anything.
  - It refuses to start if the chosen `--vary` fields cannot make `--flows` distinct flows.
  - scapy on tb277 (2.4.4) imports matplotlib, which prints a `SyntaxWarning` on stderr. Harmless.
- **Status:** verified 2026-10-15 on tb277, host `eth3` -> x960-56YSQ `port1.0.10`, in T43861.
  Self-test: 4 distinct flows x 2, 8 sent, 8 in the capture. In use: proved ECMP over two
  equal-cost static next hops (1920 frames 100% on one port with one route, split with two,
  collapsed back to 1280/0 by `maximum-paths 1`), and characterised the hash -- per-flow not
  per-packet, source and destination IPv4 addresses only, L4 ports not hash inputs.

### `nsresp.py`
IPv6 Neighbor Solicitation responder. It answers every NS for a target in a /64 with an NA from a
unique fake MAC (`02:87:70:xx:xx:xx`), so the DUT fills its ND table and FDB.
- **Run:** `sudo nsresp.py <iface> <prefix/64> <stats.json> [stopfile]`
- **Where:** testbox (root); **needs:** tcpdump (to compile the BPF filter)
- **Imports:** none
- **Limits:** /64 only; the NIC is in promiscuous mode while it runs
- **Status:** generalised 2026-10-02, not re-verified on hardware

### `dhcp4.py`
IPv4 DHCP/BOOTP test tool: a crafted client, a minimal pool server, and a pcap decoder. The
IPv4 counterpart to `dhc6.py`. Built for DHCP server, relay and client cases where the verdict
needs the exact bytes on the wire — option 51 lease time, option 61 client identifier, option 12
hostname, option 82 relay agent information, giaddr rewriting, and the ARP/ICMP probes a server
emits before it offers an address. It installs nothing on the host and changes no host IP, route
or interface: every frame is crafted and read at layer 2, so it needs only a raw socket.
- **Run:**
  - `sudo dhcp4.py client <iface> [--mac M] [--xid X] [--count N] [--client-id ID] [--hostname H] [--prl 1,3,6,51] [--option82 'circuit:<s>,remote:<s>'|hex:<b>] [--giaddr IP] [--hops N] [--server-ip IP] [--broadcast] [--arp-answer IP,...] [--icmp-answer IP,...] [--arp-watch CIDR] [--discover-only] [--wait S] [--pcap F] [--json F]`
  - `sudo dhcp4.py server <iface> --server-ip IP --pool-start IP --pool-end IP [--mask M] [--router IP] [--dns IP] [--lease S] [--arp-for IP,...] [--echo-option82] [--duration S] [--pcap F] [--json F]`
  - `dhcp4.py decode <pcap> [...] [--chaddr MAC] [--arp]`
- **Where:** testbox (root for client/server; decode anywhere); **needs:** scapy
- **Imports:** none
- **Limits:**
  - IPv4 only, IA_NA-style single address per client; the server is a test fixture, not a real
    server (it holds leases in memory for the life of the process and never writes a leases file).
  - `client` exits 2 when no OFFER arrives — which is a legitimate RESULT for a conflict test,
    not only an error.
  - `--arp-answer` / `--icmp-answer` simulate "this address is already in use", which is what a
    DHCP server's probe is looking for.
- **🔴 scapy option 82 trap (measured on tb277, scapy 2.4.4):** building option 82 by its
  INTEGER key is **silently dropped** — the frame serialises without the option and nothing is
  raised:
  ```python
  DHCP(options=[(82, raw)])                        # option ABSENT, no error
  DHCP(options=[("relay_agent_information", raw)]) # correct
  ```
  A test that used the integer key would read "the relay did not insert option 82" and grade a
  working device defective. The tool exports the correct spelling as `dhcp4.OPT82`; use it.
- **🔴 A relayed DHCP frame is INVISIBLE to scapy unless you bind on dport (measured on
  tb277, 2026-10-15):** scapy binds BOOTP to UDP only for the exact pairs (sport 68, dport 67)
  and (sport 67, dport 68). An AW+ DHCP relay forwards to the server from an **ephemeral source
  port** (`192.168.48.1.57304 > 192.168.48.2.67`), so the relayed frame is not dissected as
  BOOTP at all: it reads as `Raw`, `BOOTP in pkt` is False, and a scapy server or sniffer
  reports "nothing arrived" while tcpdump on the same NIC prints the packet plainly. That reads
  as a broken relay. This tool fixes it at import with `bind_layers(UDP, BOOTP, dport=67)` and
  `dport=68`; any other scapy tool that must see relayed DHCP needs the same two lines.
- **Option 82 can appear TWICE.** `ip dhcp-relay information policy append` puts the relay's
  own TLV after the client's, so `decode`/`summarize` report `option82_count` and, when there is
  more than one, `option82_all`. A tool that keeps only the first option of a given name reads an
  appended field as missing and grades `append` as not appending (measured on tb277).
- **Counting discipline:** use `--clients N`, not a shell loop of one-client runs. Each fresh
  process pays several seconds of scapy import, so a loop meant to send N clients a few seconds
  apart actually spreads them much further and silently under-fills a capture window, which
  looks exactly like packet loss.
- **Capture discipline (not this tool, but it bit the same case):** write tcpdump `-w` files to
  the box's LOCAL /tmp as root, then copy and chown. `-Z <user>` drops privilege before writing
  and cannot write to the root-squashed NFS lab home, leaving a header-only pcap that reads as
  "no traffic". And always `wait` for tcpdump to exit before reading its file.
- **Status:** verified 2026-10-15 on tb277, x960-56YSQ. `client` mode in T43851 (counted a
  3-packet ARP probe burst at 1000 ms spacing; drove an address conflict with `--arp-answer`
  and the ping-probe escalation with `--icmp-answer`) and T43853 (option 51 at 120 d / 1 d /
  1 h). `client` + `server` together in T43852 DHCP Relay: 5 distinct clients relayed end to
  end, giaddr rewrite and hops increment read off the server's own per-frame record, plus two
  zero-relay controls. `decode` mode is written but not yet exercised on hardware.

### `dhc6.py`
Minimal DHCPv6 client (SOLICIT/ADVERTISE/REQUEST/REPLY) that installs nothing on the host. Use it
for DHCPv6 server and relay cases.
- **Run:** `sudo dhc6.py <iface> <tag> [--tries 3] [--wait 4] [--duid-seed X] [--iaid 0x5093] [--pcap FILE]`
- **Where:** testbox (root); **needs:** scapy
- **Imports:** none
- **Limits:**
  - IA_NA only.
  - The interface needs a link-local address.
  - Exit 2 means either an argument error or "ADVERTISE, NO LEASE".
- **Status:** generalised 2026-10-02, not re-verified on hardware

### `dnsresp.py`
IPv4 DNS test tool: a crafted query client and a fake authoritative responder, for DNS relay /
`ip dns forwarding` cases. It counts the queries a device forwards upstream and the answers it
returns downstream, and lets a cache hit be proven by the ABSENCE of an upstream query. Both
modes answer ARP for the address they impersonate, so the device under test resolves them
without a static ARP entry. Nothing is installed on the host and no host IP, route or resolver
setting is changed.
- **Run:**
  - `sudo dnsresp.py respond <iface> --for <ip> [--zone name=ip ...] [--default-answer ip] [--ttl N] [--duration S] [--pcap F] [--json F]`
  - `sudo dnsresp.py query <iface> --server <ip> --server-mac <mac> --src-ip <ip> --name <qname> [--name ...] [--count N] [--gap S] [--base-id 0x..] [--wait S] [--pcap F] [--json F]`
- **Where:** testbox (root); **needs:** scapy
- **Imports:** none
- **Limits:**
  - A records only; one question per query.
  - `--server-mac` is the L2 next hop (the relay's SVI MAC), since nothing is resolved by the
    host stack.
  - `query` exits 2 when no answer arrives — a legitimate RESULT for a forwarding-disabled
    control, not only an error.
- **Two responders can run on one NIC** (each filters on its own `--for` address), which is how
  you discover WHICH upstream server a relay actually prefers — give them different
  `--default-answer` values and see which one is queried.
- **🔴 Settle time is part of the measurement.** On AW+, any DNS-relay configuration change —
  including the DHCP client learning a new server — restarts the relay process and clears its
  sessions (DNS Relay TFS, "Limitations"). Measured on tb277: a leg run ~3 s after such a change
  forwarded NOTHING and read as "the device cannot use a static DNS server"; the identical
  configuration after a 20 s settle forwarded every query. **Wait 20 s after any DNS or DHCP
  client change before counting.**
- **Counting discipline:** run tcpdump alongside and treat IT as authoritative for what was on
  the wire; this tool's counts are what it decoded. A scapy sniffer starts seconds after its
  process does. Use DISTINCT query names in a single round for any counted leg — repeated names
  let in-flight duplicate suppression swallow queries and corrupt the count.
- **Status:** verified 2026-10-15 on tb277, x960-56YSQ (T43854, DNS Relay): 5 queries forwarded
  and 5 answers returned, counted at both NICs and agreeing with tcpdump exactly; 0 forwarded in
  the forwarding-disabled control; and a two-responder run that identified which upstream server
  the relay preferred.

### `opt82dump.py`
Dumps the raw DHCP Option 82 (relay agent information) TLVs out of one or more pcap files, one
line per sub-option with its code, length and bytes. Written for Option 82 cases where the
question is what the relay actually put on the wire — an `append` that produced two option-82
blocks, a `replace` that produced one, a circuit-id or remote-id whose bytes must be read
literally rather than through a decoder's naming.
- **Run:** `opt82dump.py <pcap> [<pcap> ...]`
- **Where:** anywhere; **needs:** scapy
- **Imports:** none
- **It binds BOOTP on dport 67 AND 68 before reading.** Without that, scapy does not dissect a
  RELAYED DHCP frame at all, because an AW+ relay forwards from an ephemeral source port and
  scapy's default binding is on the source port. A tool that skips this reports an empty capture
  and reads as "the relay dropped everything".
- **Client-to-server frames only** (`BOOTP.op == 1`), and the FIRST such frame per file: it
  answers "what did this leg put on the wire", not "summarise the whole capture".
- **It does not merge options of the same name**, which is the point: a decoder that keeps only
  the first option 82 reports an appended second block as "append did not append".
- **Status:** verified 2026-10-15 on tb277, x960-56YSQ (T43850, Option 82): read both TLV blocks
  of an `append` leg and the single block of `keep` / `replace`.

### `snmpq.py`
Runs one net-snmp query against an agent and **classifies** the outcome, because a bench verdict
needs the difference between "the agent returned a value", "the OID is outside my MIB view",
"my credentials were rejected" and "nothing came back at all" -- and net-snmp returns exit 1 for
most of those, so a raw exit code cannot grade a step.
- **Run:** `snmpq.py get|getnext|walk|set <agent> <oid> [<oid>...]`
  - v3: `--v3 --user U --level noAuthNoPriv|authNoPriv|authPriv [--auth-proto MD5|SHA]
    [--auth-pass P] [--priv-proto DES|AES] [--priv-pass P] [--context C] [--engine-id E]`
  - v2c/v1: `--v2c|--v1 --community C`
  - set: `--set-type i|u|s|x|a|o|t|b --set-value V`
  - also: `--timeout S` `--retries N` `--port N` `--repeat N --interval S` `--quiet`
    `--expect VALUE|NOSUCH|DENIED|AUTHFAIL|TIMEOUT`
- **Where:** testbox; **needs:** net-snmp (`/usr/bin/snmpget` etc.)
- **Imports:** none
- **Classes and exit codes:** 0 VALUE, 1 NOSUCH, 2 DENIED, 3 AUTHFAIL, 4 TIMEOUT, 5 ERROR,
  6 `--expect` mismatch. With `--expect` it prints `GRADE PASS/FAIL`.
- **Limits:**
  - `--repeat` exists so a packet capture started in parallel is certain to catch the exchange;
    the grade is taken from the LAST repetition.
  - It calls the net-snmp binaries by absolute path; it is not a pure-Python SNMP stack.
- **Password handling.** It never prints a password. The `CMD` line shows
  `<PASS len=20 sha1=0eeef6a537>` instead, so two legs can be compared byte-for-byte without
  disclosing the secret. **That is a measurement, not decoration:** a password containing
  `!`, `$`, a backtick, `\`, `{}` or `~` can be mangled on its way through a local shell, ssh
  and a remote shell, and the agent then reports an authentication failure that reads exactly
  like the feature being broken. Compare the fingerprints before blaming the product. Passing
  the password through `tools/tb` (which quotes every argument) and letting this tool take it
  as argv is the safe path; net-snmp's `SNMPCONFPATH` + `defAuthPassphrase` file is the
  alternative if a password must never appear in an argument list at all.
- **Status:** verified 2026-10-16 on tb277, x960-56YSQ (T43870): all six classes produced,
  including the authored include/exclude pair and three distinct credential failures

### `snmpwire.py`
Decodes the SNMP messages in a libpcap file and says which ones are **encrypted on the wire**.
This answers the one question no `show` command on a device can: for SNMPv3, are the varbinds
really unreadable in flight? An SNMPv3 message carries `msgData` as either a plaintext
`scopedPDU` (ASN.1 tag 0x30) or an `encryptedPDU` (tag 0x04), and that tag with the msgFlags
auth/priv bits is the proof.
- **Run:** `snmpwire.py <file.pcap> [--port 161] [--port 162] [--limit N] [--oids] [--values] [--abs]`
- **Where:** anywhere; **needs:** nothing beyond Python (no scapy)
- **Imports:** none
- **Prints per message:** source and destination, SNMP version, and for v3 the msgID, the
  msgFlags as `a`/`p`/`r`, the USM user name, the authoritative engine ID, and
  `msgData=ENCRYPTED(n bytes)` or `msgData=PLAINTEXT scopedPDU pdu=<type>`. For v1/v2c it
  prints the community. With `--oids` it lists the varbind OIDs of every plaintext message --
  i.e. exactly what an eavesdropper could read. Ends with a `SUMMARY ... ENCRYPTED, ... PLAINTEXT`
  line.
- **It is also the trap decoder** (`--port 162`), and the two options below are what make it
  one. Added 2026-10-20 by T44308; no existing behaviour or default output changed.
  - **`--values`** prints each varbind as `OID = <type>: <value>` (INTEGER, STRING / Hex-STRING,
    OID, IpAddress, Counter32/64, Gauge32, TimeTicks, NULL, and the noSuchObject /
    noSuchInstance / endOfMibView exceptions), and annotates a known `snmpTrapOID.0` value with
    its name -- risingAlarm, fallingAlarm, linkUp, linkDown, coldStart, warmStart,
    authenticationFailure. It implies `--oids`.
    🔥 **A v2c/v3 notification is identified by the VALUE of `snmpTrapOID.0`, not by any OID in
    it**, so `--oids` alone cannot tell a risingAlarm from a fallingAlarm, and cannot tell
    linkDown from linkUp AT ALL -- those two carry byte-identical varbind OIDs and differ only
    in that value. Grading a link-state or alarm trap case without `--values` is not possible.
  - **`--abs`** prints each message's absolute local time instead of the offset from the first
    decoded message. Without it you can say one trap came before another but you cannot say a
    control window was silent, because the first trap always reads `+0.000s`. Pair it with the
    box-clock times of the stimulus; note the DUT's own log is on the DUT clock, which on tb277
    runs ~15 s behind the box.
  - The annotation is advisory: an unlisted notification OID is printed as-is and nothing is
    inferred from its absence from the list.
- **Limits:**
  - classic pcap only (`tcpdump -w`), Ethernet link type; it refuses pcapng with a clear message;
  - it walks 802.1Q/QinQ and IPv4/UDP only -- no IPv6 and no reassembly;
  - exit 1 means no SNMP message was decoded, 2 means the file could not be read.
- **Use it with a control.** A capture in which everything is encrypted proves little on its
  own: the decoder might simply be failing to find varbinds. Put a `noAuthNoPriv` or
  `authNoPriv` exchange in the same capture -- the decoder must show that one as PLAINTEXT with
  its OIDs legible. That pairing is what makes the encrypted result a measurement.
- **Status:** verified 2026-10-16 on tb277, x960-56YSQ (T43870): 18 messages, 6 encrypted
  authPriv and 12 plaintext (v3 discovery, v2c, and an authNoPriv control with its OID in the
  clear). `--values` and `--abs` verified 2026-10-20 on tb277, x960-56YSQ (T44308): four SNMPv2c
  RMON traps on udp/162 decoded to risingAlarm / fallingAlarm with alarmIndex, alarmVariable,
  alarmSampleType, alarmValue and the crossed threshold, each timestamped and matched to the
  burst that caused it, against an empty capture from the same stimulus after removal

### `httpq.py`
One HTTP/HTTPS request to a device's management interface, dependency free. It prints the
status line, the response headers and the (optionally truncated) body.
- **Why it exists:** HTTP is the third management access path a Management case has to grade
  alongside telnet and ssh, and `show http` cannot say what the web interface actually
  answers -- whether a GUI is installed, whether an API is reachable, or which error it
  returns. It is also how a device's REST/RestCONF surface is checked without adding a
  dependency to the box.
- **Run:** `httpq.py <url> [--method M] [--user U --password P] [--data STR]
  [--header 'K: V']... [--timeout S] [--max-body N] [--verify] [--head-only]`, or
  `tools/tb tool <TB> <scratch> httpq <url> ...`
- **Where:** testbox (it must reach the device's management address); **needs:** nothing
  beyond Python
- **Imports:** none (urllib from the standard library)
- **Exit:** 0 a response arrived, whatever its status; 4 the transport failed; 6 usage
- **Limits and traps:**
  - **TLS verification is OFF by default**, because device certificates are self-signed
    (`O = Allied-Telesis, CN = AlliedwarePlusDefault`). Pass `--verify` to turn it on.
  - 🔴 **An AW+ device answers plain `http://` with a 301 to `https://`.** urllib follows the
    redirect, so an SSL context attached only to an `https://` starting URL is not in play by
    then and the request dies on `CERTIFICATE_VERIFY_FAILED` -- which reads as a device or
    network fault. The context is therefore built unconditionally (measured on tb277
    2026-10-20, T47199).
  - `--user/--password` sends HTTP Basic only; it does not drive a form login or a session
    cookie.
  - The password is an argv value and is visible in `ps` on the box; use a worthless
    credential.
- **Status:** verified 2026-10-20 on tb277, x960-56YSQ (T47199): 404 from `/` and `/login`
  with no GUI file installed (`show http` -> `GUI file in use : -`), 501
  `ANT_CODE_UNIMPLEMENTED` from `/api/v1/system`, and **200 OK with 11848 B of
  `application/yang-data+json` from `/restconf/data`** -- the last being the measurement that
  the DUT was NOT in the documented "login-only mode" that a factory-default password would
  have put it in

### `tcpflow.py`
Summarises the **TCP conversations** in a `tcpdump -w` pcap, in pure Python. Every other decoder
here knows one application protocol; this one knows only TCP, which is what a case needs when
the question is *"did a session to this port actually happen, or was it refused?"*.
- **Why it exists:** a connection that was **refused** and a connection that was **never
  attempted** look identical in a `show` command and completely different on the wire. That
  discrimination is the whole of an off/on/removed arc, and `platforms/x960.md` §5 records this
  platform reporting a feature Enabled while the dataplane did nothing -- so the verdict has to
  come from the packets (STANDING-ORDERS §7).
- **Run:** `tcpflow.py <file.pcap> [--port N] [--ascii] [--max-bytes N] [--quiet]`, or
  `tools/tb tool <TB> <scratch> tcpflow /tmp/<scratch>/<out>.pcap --port 23 [--ascii]`
- **Where:** anywhere; **needs:** nothing beyond Python (no scapy; it reads the pcap format
  directly, classic and pcapng, either endianness, Ethernet / Linux SLL / SLL2 / RAW, and
  skips over VLAN tags)
- **Imports:** none
- **Output:** one block per flow with the endpoints, packet count, duration and a handshake
  verdict -- `ESTABLISHED+DATA`, `ESTABLISHED`, `REFUSED (SYN answered by RST)`,
  `NO-ANSWER (SYN, nothing back)` or `PARTIAL` -- then per direction the packet count, payload
  bytes and the set of TCP flag combinations seen. `--ascii` additionally prints the printable
  payload per direction, which for a cleartext protocol such as telnet is the login banner
  itself.
- **Limits:** IPv4 TCP only (no IPv6, no UDP); it does not reassemble out-of-order segments, so
  `--ascii` is a concatenation in capture order, which is right for an interactive session and
  wrong for a bulk transfer; a flow is keyed on the address/port pair, so a reused source port
  inside one capture merges into one flow.
- **Status:** verified 2026-10-20 on tb277, x960-56YSQ (T33378): four captures across one
  telnet on/off arc -- 4 packets / 2 REFUSED flows with the server disabled, 94 packets with it
  enabled (one ESTABLISHED+DATA flow carrying 2045 B of banner and command output, decoded with
  `--ascii`, plus a refused-credential flow of 94 B), a REFUSED flow while `show telnet` still
  read Enabled with Protocol IPv6, and 2 packets after removal

### `sflowwire.py`
Decodes the **sFlow v5** datagrams in a `tcpdump -w` pcap and prints what each sample says. It
exists because `sflowtool` is not installed on every testbox and installing it is root
(STANDING-ORDERS §4), while a verdict on sFlow needs the one thing no `show` command can give:
that a datagram really left the switch, that it names the configured agent, and that the
sampling rate and the sampled frame in it are the ones the case set up. `show sflow` saying
"Enabled" is not a measurement -- `platforms/x960.md` §5 records this exact platform reporting a
mirror Enabled while the dataplane copied nothing.
- **Run:** `sflowwire.py <file.pcap> [--port 6343] [--limit N] [--abs] [--quiet] [--find TEXT]`
- **Where:** anywhere; **needs:** nothing beyond Python (no scapy)
- **Imports:** snmpwire (for the classic-pcap reader and the Ethernet/802.1Q/IPv4/UDP walk --
  so it takes `tcpdump -w` output, NOT pcapng)
- **Prints per datagram:** agent address, sub-agent id, datagram sequence number, agent uptime
  and sample count. Per **flow** sample: the sampling rate as `1-in-N`, sample pool, drops,
  input and output ifIndex, and the sampled frame's own header decoded -- MACs, 802.1Q/QinQ
  tags, EtherType, IPv4 addresses, protocol and TCP/UDP ports. Per **counters** sample: the
  ifIndex and the generic interface counters (ifType, ifSpeed, direction, status, and the in/out
  octet, unicast, multicast, broadcast, discard and error counts). Ends with a `SUMMARY` line
  giving the datagram count, flow and counters sample totals, the agent address(es) and the
  sequence range.
- **Options:**
  - `--abs` absolute local time per datagram instead of the offset from the first one. Needed to
    claim a control window was silent, and to line a datagram up with the burst that caused it.
  - `--quiet` the SUMMARY line only -- the right form for counting in a control window.
  - **`--find TEXT`** counts the raw-header samples whose sampled bytes contain that ASCII text,
    and marks each one. 🔥 **This is how you prove WHICH burst a sample belongs to.** Send each
    burst with `vsend.py --tag <marker>`; the marker travels in the payload and the sampled
    header is the only place a decoder can see it. Without it two bursts of the same shape are
    indistinguishable in a decode -- and that distinction is exactly what settled T44309's
    finding (samples emitted after `no sflow enable` were of post-disable traffic, not a stale
    buffer).
- **Limits:**
  - sFlow **v5** only; a v4 datagram is skipped, not reported.
  - flow samples: the raw-packet-header record (format 1) is decoded; other record formats are
    listed by format and length only. Counters: the generic interface record (format 1) is
    decoded; the ethernet/dot3Stats record (format 2) that AW+ also sends is listed only.
  - expanded samples (formats 3 and 4) are parsed, including their split source and
    input/output fields.
  - IPv4/UDP transport only; it does not reassemble.
  - exit 1 means no sFlow datagram was decoded -- which for a control window is the expected
    grade, not an error; 2 means the file could not be read.
- **Status:** written and verified 2026-10-20 on tb277, x960-56YSQ (T44309). Self-tested first
  against a hand-built synthetic v5 datagram (one flow sample with a raw header of a known
  86-byte frame, one counters sample), then on hardware: 22 datagrams in which 2000 frames at a
  configured 1-in-50 gave exactly 40 flow samples, each reporting `sampling_rate=1-in-50`, with
  `sample_pool` stepping by exactly 50, 38 sampled headers decoding to the exact frame
  `vsend.py` was told to build, and 5 counters samples all for the one polled port

### `radius.py`
RADIUS (RFC 2865 / 2866) codec library -- the one home for the RADIUS wire format in this repo,
imported by `radsend.py`, `radsrv.py` and `radwire.py` so the encoding that SENDS a packet is
the code that DECODES it off the wire. It covers the header and attribute TLVs, PAP
User-Password hide/unhide, the Accounting-Request Request Authenticator, the Response
Authenticator (the check that proves a responder holds the shared secret -- no `show` command
on either end can prove that), and Message-Authenticator (RFC 3579, HMAC-MD5).
- **Run:** `import radius as R` (library). `python3 radius.py` runs a codec self-test, no network
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** none
- **Limits:** PAP and the standard attribute set; no CHAP, no EAP payload parsing, no
  vendor-specific (26) sub-attribute decoding
- **Status:** verified 2026-10-20 -- self-test OK on the dev host and on tb277 (`tools/tb tool
  tb277 <scratch> radius`), and end-to-end against a real AW+ RADIUS server (x960-56YSQ)

### `radsend.py`
A NAS in one command: sends an Access-Request (PAP) or an Accounting-Request and reports the
reply, **verifying the reply's Response Authenticator against the shared secret**. It is also
the control instrument -- `--secret` and `--password` can deliberately be wrong, and the exit
code tells the two outcomes apart. An ICMP port-unreachable is reported as such, which is a
stronger "nothing is listening" than silence.
- **Run:** `radsend.py <server-ip> --secret S --user NAME [--password PW] [--port N]
  [--acct start|stop|interim] [--bind IP] [--nas-ip IP] [--nas-id T] [--service-type N]
  [--msg-auth] [--count N] [--timeout S] [--retries N] [--id N] [--quiet]`
- **Where:** anywhere with a path to the server (on a testbox: `tools/tb tool <TB> <scratch>
  radsend ...`); **needs:** nothing beyond Python, and no root (unprivileged source port)
- **Imports:** radius
- **Exit codes:** 0 replied and the authenticator verified; 1 no reply (includes ICMP
  port-unreachable); 3 a reply whose Response Authenticator did NOT verify; 4 Access-Reject
  (a real answer -- a case that EXPECTS a reject treats 4 as success); 2 usage/socket error
- **Limits:** PAP only (no CHAP, no EAP), one outstanding request at a time
- **Status:** verified 2026-10-20 on tb277 against the x960-56YSQ Local RADIUS Server (T33407):
  Access-Accept, wrong-password Reject, unknown-user Reject, wrong-secret, unknown-NAS silence,
  and the ICMP-unreachable path with the feature off

### `radsrv.py`
A RADIUS authentication and accounting server in pure Python, on any UDP port. It exists
because a testbox's packaged freeradius keeps its clients and users under `/etc/`, which is
root to edit, and 1812/1813 are privileged ports (STANDING-ORDERS §4). This one runs as an
ordinary user on, say, 11812/11813 -- a DUT is pointed at it with `radius-server host <box>
auth-port <n> acct-port <n>` -- and every client, user and secret is on the command line, so
the whole server side of a case is visible in the working log. One log line per packet.
- **Run:** `radsrv.py --secret S --client IP --user NAME:PASSWORD [--auth-port N]
  [--acct-port N] [--bind IP] [--client-secret IP=S] [--user-file F] [--reply-attr N=V]
  [--reject-all] [--drop-all] [--log PATH] [--seconds N] [--stopfile PATH] [--pidfile PATH]`
- **Where:** a host the DUT can reach; **needs:** nothing beyond Python, and no root while the
  ports are >= 1024
- **Imports:** radius
- **Behaviour worth knowing:** a request from an unlisted client, or one whose
  Message-Authenticator does not verify, is DROPPED and logged -- so a wrong-secret control
  shows up as silence rather than a Reject, as a real server does. `--reject-all` and
  `--drop-all` give deliberate negative controls.
- **Limits:** PAP only (no CHAP, no EAP), no proxying of its own, no duplicate-request cache
- **Status:** verified 2026-10-20 on tb277 (T33408/T33409) and end-to-end against `radsend.py`

### `radwire.py`
Decodes and COUNTS the RADIUS packets in a `tcpdump -w` pcap, and, given the shared secret,
pairs each reply with its request and says whether the Response Authenticator verifies. This
is the wire half of a RADIUS case's evidence: RADIUS is UDP, so "the login worked" is not a
measurement (STANDING-ORDERS §7).
- **Run:** `radwire.py <file.pcap> [--port N ...] [--secret S] [--limit N] [--quiet]`
  (default ports 1812, 1813, 11812, 11813; any `--port` replaces the whole default list)
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** radius, snmpwire (for the classic-pcap reader and the Ethernet/802.1Q/IPv4/UDP
  walk -- so it takes `tcpdump -w` output, NOT pcapng)
- **Limits:** IPv4/UDP only; a reply can only be authenticator-checked when its request is in
  the same capture (reported as `unpaired` otherwise)
- **Status:** verified 2026-10-20 on tb277, x960-56YSQ (T33407): 10 packets, 5 Access-Request /
  2 Access-Accept / 3 Access-Reject, authenticator valid=5 invalid=0 unpaired=0

### `wpasup.py`
Drives `wpa_supplicant` as a WIRED 802.1X supplicant, captures the EAPOL exchange and grades it.
One process does all three, so the capture can never start after the exchange it was meant to
record (memory `two-console-calls-in-one-block-run-sequentially`). Use it where the EAP method
itself is the subject -- PEAP, TLS, TTLS -- and `eapol.py` where the case needs several
supplicant MACs on one wire.
- **Run:** `wpasup.py <iface> --method peap|peap-gtc|ttls|md5|tls --identity U
  [--password P | --password-env VAR] [--anonymous-identity A] [--ca-cert F] [--client-cert F]
  [--private-key F|.p12] [--private-key-passwd P] [--phase1 S] [--extra LINE]
  [--timeout S] [--settle S] [--pcap F] [--json F] [--label L] [--expect success|failure|timeout]`
- **Where:** testbox, as **root** (`tools/tb sudotool`); **needs:** `wpa_supplicant`, `tcpdump`,
  scapy (for the decode only)
- **Imports:** none from `tools/`
- **What it prints:** every `CTRL-EVENT-EAP-*` line, then one row per EAPOL frame
  (time, src, dst, EAPOL type, EAP code, id, EAP method), then the methods the authenticator
  offered, then `RESULT <label>: expected X, got Y -- MATCH|MISMATCH`. Exit 0 only on MATCH, so a
  **control leg that must not authenticate is `--expect failure`** and still exits 0 when it is
  correctly refused (STANDING-ORDERS §7).
- 🔴 **The capture is ALWAYS filtered `ether proto 0x888e`.** On a bench running loop-protection
  (tb277: 1 LDF/s across 57 instances) an unfiltered capture drowns.
- **Limits:**
  - with no `--ca-cert` the server certificate is accepted WITHOUT validation; the banner says so
    on every run, so a log can never imply the chain was checked when it was not;
  - do not add `tls_disable_tlsv1_3` or other post-2.6 network fields -- wpa_supplicant 2.6
    rejects the whole config file with "unknown network field";
  - ⚠️ **check the `--json` file against the printed RESULT.** On 2026-10-23 one run
    (T44270 control B) printed 22 frames and `got failure` while its own JSON recorded
    `"verdict": "timeout"` and `"eapol_frames": 2`. Nothing in the code can produce that -- both
    are final before the JSON is built -- and it did not recur on an unchanged re-run. Unexplained;
    grade on the printed RESULT plus the device's own log until it is understood.
- **Status:** verified 2026-10-23 on tb277, x960-56YSQ (T44270): EAP-PEAP success (24 EAPOL
  frames, EAP-Success), wrong-password control and unknown-identity control (22 frames each,
  EAP-Failure), all five legs matching `--expect`

### `eapol.py`
A scapy 802.1X supplicant that can be SEVERAL supplicants at once on one wire, each with its own
source MAC. `wpa_supplicant` is one supplicant per interface, so a multi-supplicant case
(`auth host-mode multi-supplicant`, multiple dynamic VLANs, two-step authentication,
`auth max-supplicant`) cannot be driven with it at all. Speaks EAP-Identity, EAP-MD5 (RFC 1994),
EAP-Notification (RFC 3748 §5.2) and Legacy-Nak -- enough for every authentication-MODE case,
which is about which supplicants the authenticator admits, not about the cipher.
- **Run:** `eapol.py <iface> --supplicant MAC:identity:password[:expect[:nak_type]] [--supplicant ...]
  [--timeout S] [--stagger S] [--no-start] [--logoff] [--settle S] [--pcap F] [--json F] [--label L]`
- **Where:** testbox, as **root** (`tools/tb sudotool`); **needs:** scapy
- **Imports:** none from `tools/`
- **Grading:** each supplicant carries its OWN expected outcome (`success`/`failure`, default
  `success`), so one run contains its own control. Exit 0 only if every supplicant matched.
- **Notes:**
  - `--stagger S` spaces the EAPOL-Starts, for a case about the ORDER two supplicants arrive in;
  - `--no-start` sends no EAPOL-Start and waits for the authenticator to ask, which is how you
    prove the authenticator initiates;
  - `nak_type` makes that supplicant Legacy-Nak to a chosen EAP type when offered something else;
  - EAP-Request/Notification payloads are captured per supplicant and printed, which is the hook
    an EAP-Notification case needs;
  - it listens with a BPF filter of `ether proto 0x888e`, for the loop-protection reason above.
- **Status:** written 2026-10-23 for tb277 group A/B; **not yet re-verified on hardware** -- first
  use should update this line

### `rs.py`
Sends ICMPv6 Router Solicitations to ff02::2, 2 s apart.
- **Run:** `sudo rs.py <iface> <count>`
- **Where:** testbox (root); **needs:** scapy
- **Imports:** none
- **Limits:** the interface needs a link-local address
- **Status:** generalised 2026-10-02, not re-verified on hardware

### `ra_decode.py`
Prints every Router Advertisement in a pcap, with its Prefix Information options.
- **Run:** `ra_decode.py <pcap>`
- **Where:** anywhere; **needs:** scapy
- **Imports:** none
- **Limits:** none known
- **Status:** verified 2026-10-02 on tb470 (scapy 2.6.1; a pcap with no RAs)

### `lldpmed_phone.py`
Emulates an LLDP-MED Class III IP phone. It sends LLDP-MED and decodes the switch's Network
Policy, then does tagged DHCP, ARP and ping in the voice VLAN.
- **Run:** `sudo lldpmed_phone.py <iface> <pcap-out> [--mac 00:00:5e:00:53:10] [--lldp-secs 8] [--vlan V] [--no-dhcp]`
- **Where:** testbox (root); **needs:** scapy
- **Imports:** none
- **Limits:**
  - `--mac` must be lower-case.
  - Exit 2 means either an argument error or "no OFFER".
- **Status:** verified 2026-10-21 on tb277, x960-56YSQ (T33398) -- its first hardware run.
  Six runs against a real switch: it sent its LLDP-MED Class III advertisements, the DUT
  learned it as `Endpoint Class III` / Telephone with the inventory string `CK-PHONE-EMU`, and
  it decoded the switch's Network Policy correctly every time, agreeing byte-for-byte with the
  independently written `lldpwire.py` on the 12-bit VLAN / 3-bit priority / 6-bit DSCP packing.
  It returned `voice network policy: None` correctly when the policy TLV was deselected and
  when the voice VLAN was removed. **`--mac` is more useful than it looks**: a different MAC is
  a NEW endpoint, which is what makes the LLDP-MED fast-start trigger testable on demand
  instead of waiting out a 120 s TTL. Use `--no-dhcp` on a bench with no DHCP server in the
  voice VLAN, or the run can only ever report "no OFFER"

### `lldpsend.py`
Advertises a **controllable LLDP neighbour** from a host NIC, with scapy. `lldpmed_phone.py`
beside it emulates an IP phone and always sends the LLDP-MED endpoint set plus DHCP, ARP and a
ping; this one sends a plain LLDPDU whose chassis ID, port ID, system name, capabilities,
management address and above all **TTL** are arguments, and which you start and stop on command.
- **Why it exists:** neighbour ageing is only measurable when you choose the TTL. With switch
  partners it is a 120 s wait with nothing to compare against; with this, two neighbours
  carrying different TTLs can sit on the same port at the same instant — one must go, the other
  must stay, and that pair is the measurement (STANDING-ORDERS §7: the exact frame plus a
  control that must NOT match). It is the sender half of `lldpwire.py`.
- **Run:** `sudo lldpsend.py <iface> [--count N] [--interval S] [--ttl S] [--chassis-mac MAC]
  [--src-mac MAC] [--port-id STR] [--port-desc STR] [--sys-name STR] [--sys-desc STR]
  [--mgmt-ip A.B.C.D] [--caps bridge,router,station] [--vlan V] [--med-class 1|2|3]
  [--med-policy voice:VLAN:PRIO:DSCP] [--shutdown] [--pcap FILE]`, or
  `tools/tb sudotool <TB> <scratch> lldpsend eth3 --count 3 --ttl 20 --port-id ckLLDP-eth3 ...`
- **Where:** testbox (root); **needs:** scapy
- **Imports:** none
- **`--shutdown`** sends a final TTL-0 LLDPDU (the IEEE 802.1AB shutdown frame), which asks the
  neighbour to delete the entry at once instead of waiting out the hold time. On AW+ that
  increments `Deleted Entries` **without** `Entry Age-outs`, which is how the two removal paths
  are told apart.
- **Limits:** IPv4 management address only; it sends, it does not listen (use `lldpwire.py` on a
  capture); a MED Network Policy is advertised but no MED Location or Extended Power TLV.
- **Status:** verified 2026-10-21 on tb277, x960-56YSQ (T44296): frames accepted field-for-field
  by the DUT (chassis, port ID, system name and capabilities all read back unchanged in
  `show lldp neighbors`), `In` counters moving frame-for-frame at every leg, a TTL-20 neighbour
  ageing out on schedule beside a TTL-120 one on the same port, and `--shutdown` deleting an
  entry with 110 s of hold time left

### `lldpwire.py`
Decodes the **LLDP frames** in a `tcpdump -w` pcap, in pure Python. Per source MAC it prints the
frame count, the inter-frame gaps (min/mean/max) and the decoded TLVs, and it checks the three
mandatory TLVs are present.
- **Why it exists:** a verdict on LLDP cannot come from `show lldp neighbors` — that is the
  device's answer about itself, and `platforms/x960.md` §5 records this platform reporting a
  feature Enabled while the dataplane did nothing. The gaps are how a Tx Timer change is graded
  and how LLDP-MED fast start is seen (three ~1 s frames where the steady state is 30 s); the
  TLV decode is how "the DUT advertises X" is graded.
- **Run:** `lldpwire.py <file.pcap> [--src MAC] [--tlv] [--quiet] [--expect-med] [--json]`, or
  `tools/tb tool <TB> <scratch> lldpwire /tmp/<scratch>/<f>.pcap --tlv`
- **Where:** anywhere; **needs:** nothing beyond Python (it reuses `tcpflow.py`'s pcap reader, so
  classic pcap and pcapng, either endianness)
- **Imports:** tcpflow
- **Knows:** the base TLVs (chassis/port ID with their subtypes, TTL, port and system
  description, capabilities, management address) and the organisationally-specific sets for
  IEEE 802.1 (port VLAN ID, VLAN name), IEEE 802.3 (max frame size, link aggregation) and TIA
  LLDP-MED (capabilities and device class, **Network Policy** with its 12-bit VLAN / 3-bit
  priority / 6-bit DSCP packing, inventory strings). An unknown OUI prints as hex rather than
  being dropped.
- **Limits:** Ethernet link-type only (LLDP is link-local, so that is the whole of it); it
  reports the outer 802.1Q tag and ignores inner tags.
- **Status:** verified 2026-10-21 on tb277, x960-56YSQ (T44296 and T33398): first against a
  synthetic frame built in-process, which round-tripped every field including the MED Network
  Policy bit-packing, then across thirteen real captures — 30.03 s / 10.01 s / 15.01 s gap
  measurements, TTLs of 120, 45 and 20, a 4-TLV default advertisement growing to 11 and back,
  and zero-frame captures whose zero was trustworthy because the same tool had just returned
  non-zero. T33398 added the LLDP-MED path: a Network Policy TLV decoded identically to
  `lldpmed_phone.py`'s independent parser, and 4 / 6 / 7-TLV advertisements told apart to grade
  two different MED removal routes

### `snmpwalk.py`
Walks an SNMP agent's MIB with SNMPv2c, stdlib only (tb470 has no snmpwalk tool in `tools/` and the wrapper has no free-form
exec). Every varbind goes to `<outfile>` (`<oid> = <TYPE>: <value>`); stdout gets a summary: varbinds, requests, retries,
elapsed, first/last OID, the subtrees seen, and why it stopped (`END` = endOfMibView or left `--root`; `NOT-INCREASING`,
`TIMEOUT`, `ERROR <status>`, `MAX`).
- **Run:** `snmpwalk.py <agent-ip> <community> <outfile> [--root 1.3.6.1] [--bulk 20] [--getnext] [--timeout 3] [--retries 3] [--max 200000] [--src <local-ip>]`
  (`tools/tb tool <TB> <scratch> snmpwalk ...`)
- **Where:** testbox (or anywhere with a route to the agent); **needs:** nothing beyond Python
- **Imports:** none
- **Limits:** SNMPv2c only (no v1, no v3); read-only GET-type PDUs; IPv4 transport. Exit 0 only on `END`.
- **Status:** verified 2026-10-09 on tb470 against the x230v2-28GS (T15255): GETBULK 12448 varbinds in 9.7 s, GETNEXT
  12469 in 26.6 s, both to endOfMibView

### `restconf.py`
Minimal RESTCONF (RFC 8040) client: one request per call, HTTPS with the certificate not
verified (bench units are self-signed), HTTP Basic auth, JSON bodies as
`application/yang-data+json`. Prints a status line (`HTTP <code> <reason>  <METHOD> <url>`), the
Content-Type / Location / Allow headers, and the body (pretty JSON).
- **Run:** `restconf.py <host> <METHOD> <path> [--data JSON|@file] [--user U] [--password P] [--port N] [--http] [--root R] [--out FILE] [--max-bytes N] [--grep REGEX] [--timeout S]`
  - `<path>` starting with `/` is sent as given; otherwise it is relative to the RESTCONF root, taken from
    `--root` or discovered from `/.well-known/host-meta`.
  - Credentials: `--user/--password`, else `CK_USER`/`CK_PASSWORD`, else `manager`/`friend`.
  - Through the wrapper: `tools/tb tool <TB> <scratch> restconf <host> GET data/... --root /restconf`.
- **Where:** anywhere that reaches the device (on tb470, the box itself over a host NIC); **needs:** Python 3.7+ stdlib only
- **Imports:** none
- **Exit codes:** 0 a 2xx answer; 1 any other HTTP status; 2 usage (including `--data` that is not JSON); 3 connection error.
- **AW+ facts it met (x230v2-28GS, awplus_main-20261008-57, 2026-10-13, T47228):** `/.well-known/host-meta` answers
  404, so pass `--root /restconf`; writes work only as **PUT on a leaf with an unqualified body**
  (`{"enabled":false}`), a module-qualified leaf body gets 400, PATCH on a container gets 404, and PATCH on a leaf
  answers 204 without changing anything. Details: memory `awplus-restconf-api-reference`.
- **Status:** verified 2026-10-13 on tb470 against the x230v2-28GS (u0) over eth3 (GET, PUT, PATCH, POST, DELETE, OPTIONS)

### `mb.py`
Modbus/TCP client with a raw-byte trace. It reads holding registers, writes a register, or
probes. Use it for AW+ SCADA Modbus gateway cases.
- **Run:** `mb.py --host H [--port 502] [--slave 0] [--timeout 3] [--retries 0] [--log mb.log] [--source IP] {read ADDR COUNT TYPE [DESC] | write ADDR VALUE [DESC] | probe}`
- **Where:** anywhere with a route to the DUT. The lab drops TCP from office PCs, so run it on the testbox; **needs:** pymodbus 3.x (3.8.6, the `slave=` API)
- **Imports:** none
- **Limits:**
  - The register decodings were written for the IE520 Modbus map (Mapping Version 5).
  - Exit 2 means either an argument error or "no connection".
  - An exception prints `EXCEPTION code=N (<name>) fc=0xNN`, the Modbus exception code itself
    (2026-10-08; before that it printed only `status=1`, and codes were inferred from the server's
    counters). pymodbus' own stderr line `Exception response 131 / 0` shows 0 for the code: ignore it.
- **Status:** verified 2026-10-08 on tb470/IE520 stack (main-calanm), T22650 reads over IPv4, units 0-4;
  exception codes verified 2026-10-08 against a pymodbus 3.8.6 server on tb470 loopback (code 2)

### `mbplan.py`
Runs a Modbus/TCP test **plan** and grades every line against its expected result, printing one
PASS / FAIL / INFO / ERROR row per line; the raw TX bytes and full CLI text go to `--log` /
`--out`. Plan actions: `step`, `read`, `write`, `probe <tcp-port> ok|refused`, `cli <cmd> [;;
<cmd>...] [=~ regex]` (through `ckcon.py`, one session), `log <regex>` (`show log | include`),
`sleep`, `port <tcp-port>`. Expectations: a value, `~` (record only), `>N`/`<N`, `exc`/`exc:N`,
`ok`. Port registers by name: `@1.0.2[+offset]` = unit 1, 0x5000 + 13*(port-1). Plans live per
bench and suite: `tb470/IE520/plans/modbus/` (T22650-T22655, with their README).
- **Run:** `mbplan.py --host H [--port 502] [--console /dev/uN --baud B --transcript F] [--log mb.log] [--out plan.out] [--var NAME=VALUE] PLAN`
- **Where:** the testbox (TCP to the DUT); **needs:** pymodbus 3.x; `mb.py`, `ckcon.py`, `console.py` beside it (copy `tools/` whole)
- **Imports:** `mb.py` (decode, exception text); runs `ckcon.py` for `cli`/`log` lines
- **Limits:** one TCP connection per line (the IE520 allows 1); per-member register maps beyond the
  port block are written as plain addresses in the plan; FLOAT values compare at 3 decimals
- **Status:** Modbus lines (read/write/exception/probe/port/@port) verified 2026-10-08 against a pymodbus
  3.8.6 server on tb470 loopback; `cli`/`log` lines NOT yet run against a console (first real use: check them)

### `ntpc.py`
Crafted **NTP client**: sends mode-3 (or any mode) NTP packets and decodes every field of the
reply. IPv4 and IPv6, no root.
- **Why it exists:** an NTP case is a traffic case (STANDING-ORDERS §7), and on the x960
  `show ntp associations` will list a peer no packet ever reached while `show ntp status` and
  `show ntp counters` print COMPLETELY EMPTY output -- indistinguishable from a hung command
  (`platforms/x960.md` §7H). The verdict has to come from the exchange.
- **Why a plain UDP socket and not scapy:** it needs no root, so it runs anywhere a case runs;
  and on a box whose own `ntpd` owns UDP/123 a raw responder would race the kernel, while an
  ordinary client socket just talks to the device under test. The 48-byte request is still
  built byte by byte here (LI/VN/mode, stratum, poll, precision, transmit timestamp are all
  arguments), so it is a crafted frame.
- **Run:** `ntpc.py <server> [--port N] [--count N] [--gap S] [--timeout S] [--version 1-4]
  [--mode 0-7] [--req-stratum N] [--poll N] [--precision N] [--bind IP] [--bind-port N]
  [-4|-6] [--json F]`, or `tools/tb tool <TB> <scratch> ntpc <server> --bind <src> --count N`
- **Where:** anywhere (the testbox, for a leg that must leave a particular NIC);
  **needs:** nothing beyond Python
- **Imports:** none
- **Output:** per packet, the request's transmit time and then the reply's LI, version, mode,
  stratum, poll, precision, root delay, root dispersion, refid, all four timestamps, and the
  computed offset and delay. It flags a stratum-0 **kiss-o'-death**, an **LI=3** "not
  synchronised" reply, and -- the important one -- **`origin_echo=yes/no`**, which says whether
  the reply's origin timestamp echoes the transmit timestamp of *this* request. A reply that
  does not echo it is reported, never counted as an answer.
- **`--bind <ip>` picks the leg**, which is how one box tests a server from two different
  client addresses (an `ntp restrict` case needs exactly that).
- **Exit codes:** 0 at least one reply; **2 no reply at all -- a legitimate control result**
  (server disabled, restricted, unreachable), not only an error; 3 usage/resolution error.
- **Limits:** client side only (it does not answer requests); no authentication (no MD5/SHA
  MAC is appended or checked); one server per run.
- 🔴 **Count a burst against the server's rate limiter, not against your expectations.** The
  x960 rate-limits NTP replies BY DEFAULT (burst 8, interval 8 s, leak 4), so 20 packets
  0.5 s apart legitimately return 11 answers. See `platforms/x960.md` §7H.
- **Status:** verified 2026-10-21 on tb277 -- against the box's own `ntpd` on 127.0.0.1
  (stratum 5, `origin_echo=yes`, offset < 1 ms) as the instrument control, then on
  x960-56YSQ (T33399 IPv4 server, T33400 IPv4 client, T44298 IPv6 server)

### `ntpwire.py`
Decodes and **counts** the NTP packets in a `tcpdump -w` pcap -- **IPv4 and IPv6**.
- **Why it exists:** the independent witness beside `ntpc.py`. It is what proves a request
  *left the box* when no reply came back, which is the entire content of a negative leg, and
  what counts a client's outbound polls when the device under test is the client and the far
  end is a real `ntpd` that reports nothing to the case.
- **Run:** `ntpwire.py <file.pcap> [--port N ...] [--from ADDR ...] [--to ADDR ...]
  [--limit N] [--quiet]`, or `tools/tb tool <TB> <scratch> ntpwire /tmp/<scratch>/<f>.pcap`
  (default port 123; any `--port` replaces the default list)
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** `snmpwire` (for the classic-pcap reader) -- so it takes `tcpdump -w` output,
  **not pcapng**. Its own IPv4/IPv6 + 802.1Q + UDP walk is local, because `snmpwire.udp_payload`
  is IPv4 only.
- **Output:** one line per packet (time, family, addresses and ports, mode, version, LI,
  stratum, refid, transmit timestamp, and `+MAC(auth)` when the packet carries an
  authenticator), then a summary by family, by mode and by address pair, and a
  **request/reply pairing** that matches each server reply to the request whose transmit
  timestamp it echoes in its origin field. It reports `paired`, `unpaired` and `unanswered`
  separately -- an unpaired reply is not evidence that a request was answered. Stratum-0
  kiss-o'-death replies and LI=3 replies are called out.
- **Exit codes:** 0 packets decoded; **2 no NTP packets at all** (for a control leg that is the
  measurement, not an error); 3 the file could not be read.
- **Limits:** Ethernet link type only; it walks hop-by-hop/routing/destination IPv6 extension
  headers but not fragments; no authenticator verification.
- **Status:** verified 2026-10-21 on tb277, x960-56YSQ -- across T33399's full off/on/
  restrict/removed arc (2 requests + 0 replies with the server off, 3+3 all paired with it on,
  3 requests + 0 replies while `ntp restrict ... serve deny` was in force) and on IPv6 in
  T44298

### `ixtcl.py`
Drives an IXIA chassis through the lab's IxOS Tcl client (IxTclHal 6.80 with its own `tclsh8.5` in
`/home/ixos-IxNetwork`, which proxies to the chassis's IxTclServer). Every call connects (`ixConnectToTclServer`
FIRST, then `ixConnectToChassis`, then `ixLogin <name>`), acts and disconnects. Each IxTclHal action's return code is
printed as `RC <label> <code>`; any non-zero code or Tcl error makes the call exit 1. Actions: `status` and
`counters` (read-only; one `TSV` line per port: link, transmitState, framesSent/Received, userDefinedStat1/2,
fcsErrors, bytes, undersize/oversize, then the rates of framesSent/framesReceived/UDS1; `--tsv FILE` appends them),
`take [--force]`, `release`, `reset` (port factory defaults, clears streams AND filters), `stream` (one
EthernetII/IPv4/UDP stream: `--sa --da --sip --dip --sport --dport --size --percent`, `--continuous` or
`--count N`, optional `--vlan VID`), `filter` (UDS1 = frames matching `--uds1-sa/--uds1-da`, UDS2 =
`--uds2-sa/--uds2-da`; an omitted address is "any"), `clear`, `start`, `stop`, `burst` (clear, start, wait for
`ixCheckTransmitDone`, counters), and `pair` (T17509 review, 2026-10-22: the STANDING-ORDERS §7 control + positive
pair in ONE call: `pair --ports A,B --sa1 MAC --sa2 MAC --control-sa MAC --control-vlan VID --count N [--size
--percent --sip --dip --control-sip]` = a tagged control burst A → B with the control SA, counters, then the untagged
test pair A ↔ B with N frames each, counters; prints the four `TSV` lines, `PAIR control/positive/RESULT` lines,
exit 5 when B's UDS2 is not 0 or either UDS1 is not N; needs the `filter`s already set. Replaces the five calls
Phase C built by hand twice; **not yet run on hardware** — check its first run). Also a library:
`ixtcl.counters(chassis, login, [(card, port), ...])`, `ixtcl.stream_body(...)`, `ixtcl.burst_body(ports)`.
- **Run:** `tools/tb tool <TB> <run> ixtcl <action> --chassis <ip> --login <name> --ports 10/5,10/6 [...]`
  (`--port 10/5` for `stream`/`filter`)
- **Where:** a testbox that mounts the lab `/home` (the client lives in `/home/ixos-IxNetwork`); **needs:** that
  client; nothing from pip
- **Imports:** none (stdlib)
- **Limits:**
  - Raw `framesReceived` includes frames the DUT itself sends (on tb101 ~1.4 per minute per port, ~68 B, while
    idle), so grade loss on a UDS filtered on the stream's SA/DA, never on raw rx.
  - The global error flag is `::ixtcl_bad`: IxTclHal itself uses a global `bad`, and a script that used it
    exited 3 with every RC 0 (2026-10-21).
  - Writing (`stream`, `filter`, `start` ...) needs port ownership under the same `--login` (memory
    `ixia-chassis-82-tcl-access`); a `take --force` steals ports from their owner, so it needs the Test Engineer's OK.
  - The framework's `ATDrivers/ATIxia.py` cannot do chassis 82; this does.
- **Status:** verified 2026-10-21 on tb101 -> chassis 82 (10.36.10.82, IxOS 9.20), card 10 ports 5/6: `status`,
  `counters` (read-only); the write actions are recorded in T17509's run1.log as they are first used.

### `longrun.py`
The detached long-run sampler (T17509, 2026-10-21). Every `--every` s for `--hours` (k = 0 .. hours*3600/every, so 13
samples for 12 h hourly, the first at the start) it reads an AW+ console and, optionally, IXIA counters, and writes
one file per sample (`<out>/hourly/sample-<kk>-<stamp>.txt`, every command with its full output, `HH:MM:SS >>> cmd`),
one line per sample to `<out>/progress.tsv` (stack state, Ready count, master, per-member memory free and CPU
1s/20s/60s, `show log` line count, `% ` line count, per-port IXIA link/sent/rcvd/UDS1/UDS2/FCS/rates), the IXIA rows
to `<out>/ixia.tsv`, and `<out>/DONE` after the last sample. Console reads: `show clock`, `show stack`, `show memory
<m>` and `show cpu <m>` per `--members`, `show interface <--dut-ports>`, each `--cmd`, then the full `show log`. It
opens the console only for the sample and closes it after (`terminal no monitor`, exec-safe). A console another
process holds is retried every 60 s for up to `--held-retry` s, then the sample is written as SKIPPED with the
reason. A failed read is written to the sample and its progress line, and the run goes on.
- **Run:** `tools/tb tool <TB> <run> longrun --detach --hours 12 --every 3600 --console /dev/u2 --baud 115200
  --transcript /tmp/<run>/console-u2.log --members 1,2,3,4 --dut-ports port3.0.25,port4.0.25 --ixia <ip>
  --ixia-login <name> --ports 10/5,10/6 --out <dir>`; prints `DETACHED pid=<pid>`. Stop it with
  `tools/tb killmine <TB> <pid>`, or create `<out>/STOP` (it then writes DONE as STOPPED).
  **Grading tables:** `python3 tools/longrun.py --report <out dir>` (offline, dev host or box; T17509 review,
  2026-10-22) prints markdown from `progress.tsv`: stack / Ready / master per sample, memory free per member per
  sample with min / max / range / least-squares slope (kB per hour) and a STEADY-FALL flag (slope negative, at
  least 75 % of hour-to-hour steps falling, total fall above 1 %), CPU 1 s / 20 s / 60 s per member, and per IXIA
  port link / tx fps / UDS1 fps / FCS per sample with the final sent / rcvd / UDS1. Verified 2026-10-22 on the
  T17509 table (13 samples, 4 members, 2 ports): no member flagged, CPU 60 s 2–5 %, FCS 0.
- **Where:** testbox; **needs:** pyserial, `fuser` (psmisc), the IXIA client for `--ixia`
- **Imports:** console, ixtcl
- **Limits:**
  - The `show stack` parser expects the AW+ VCS summary table; on another product the stack columns read `?`.
  - `--detach` uses setsid + a double fork; the process survives the ssh session, the dev host and a VPN drop, but
    not a reboot of the testbox.
- **Status:** first used 2026-10-21 on tb101 (IE520 4-stack, T17509): see that case's run1.log for the short test
  sample and the 12 h launch.

### `syslogwire.py`
Decodes and **counts** the syslog messages in a `tcpdump -w` pcap -- **IPv4 and IPv6** --
and reports every message's **PRI byte** split into its facility and severity.
- **Why it exists:** a syslog facility or severity case is graded on `PRI = facility*8 +
  severity` **as it arrived**, never on the device's own `show log config`. It is also the
  collector: on a bench with no UDP/514 listener (starting one is a root change on the testbox,
  STANDING-ORDERS §4) a bounded `tcpdump -w ... udp port 514` plus this decoder IS the syslog
  server, and it reads the one field a real syslog daemon usually throws away.
- **Run:** `syslogwire.py <file.pcap> [--port N ...] [--from ADDR ...] [--to ADDR ...]
  [--grep REGEX] [--limit N] [--quiet] [--abs] [--msg-width N]
  [--expect-facility NAME|N] [--expect-severity NAME|N]`, or
  `tools/tb tool <TB> <scratch> syslogwire /tmp/<scratch>/<f>.pcap ...`
  (default port 514; any `--port` replaces the default list)
- **Where:** anywhere; **needs:** nothing beyond Python (no scapy)
- **Imports:** `snmpwire` (the classic-pcap reader) and `ntpwire` (its IPv4/IPv6 + 802.1Q +
  UDP walk) -- so it takes `tcpdump -w` output, **not pcapng**.
- **Output:** one line per message -- time, family, addresses and ports, `PRI=<n>`, the decoded
  `<facility>.<severity>` with both numbers, the syslog tag and the message text -- then a
  summary by family, by facility, by severity, **by PRI** and by address pair. It flags a
  facility number that is in the RFC but is **not offered by AW+ `log facility ?`** (12-15),
  which from an AW+ device would itself be a finding.
- **`--expect-facility` / `--expect-severity`** turn the summary into a verdict: it prints how
  many of the decoded messages carry that facility or severity and **exits 4** if any do not.
  Both accept a number, the RFC short name (`local5`, `notice`) or AW+'s own word for the
  severity (`notices`, `informational`).
- **Exit codes:** 0 messages decoded; **2 no syslog message at all** (for a control leg that is
  the measurement, not an error); 3 the file could not be read; 4 an `--expect-...` was not met
  by every message.
- **Use it with a control.** One destination counted on its own proves little. Configure a
  second, unreachable destination on the same subnet in the same window and run `--to` against
  it: it must exit 2. Where two reachable destinations differ only in a per-host `facility`
  override, `--to` each one from the SAME capture window is what shows which knob wins.
- **Limits:** Ethernet link type only; it walks 802.1Q/QinQ and the IPv6 hop-by-hop/routing/
  destination extension headers, but not fragments; it decodes the RFC3164 and RFC5424 headers
  heuristically and keeps the raw remainder when neither matches; no TLS and no TCP syslog.
- **Status:** added 2026-10-22 for T33401 (Syslog Facility Override) on tb277, x960-56YSQ;
  self-tested offline against a hand-built pcap (PRI 13/141/171/173 decoded to
  user.notice / local1.notice / local5.err / local5.notice, `--to`, `--grep`, the exit-2 control
  path and the exit-4 `--expect-facility` path) before its first hardware use.
