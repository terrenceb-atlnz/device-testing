# tools/ — reusable helpers for AW+ bench testing (any testbox, any product)

Every helper a case can reuse lives here, catalogued in this file. The rules for using and
adding one are in [../logged-output.md](../logged-output.md) §2:
- **Look here first.** Use or extend the tool that already exists; do not write a second one.
- **Write it generic.** Testbox, consoles, NICs, ports, VLANs and addresses are arguments, never
  constants.
- **Commit it with its entry below.**
- **The working log names the tool and its exact arguments**, so the run can be repeated.

## How to run them

- **Copy the whole directory to the testbox's scratch** and run from there. For example:
  `scp -r tools <box>:/tmp/<campaign>/`, then `cd /tmp/<campaign>/tools`. The tools import each
  other from their own directory, so keep them together.
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
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only (through cfg, poll)

### `ckcon.py`
Runs a list of CLI commands on one console and prints each with its output. With
`--stop-on-error` it stops at the first `% ` line.
- **Run:** `ckcon.py <tty> <baud> <transcript> [--stop-on-error] CMD [CMD ...]`. Env `CKTO` sets the per-command timeout in seconds (default 90)
- **Where:** testbox; **needs:** pyserial
- **Imports:** console
- **Limits:**
  - It does not answer (y/n) prompts; use `ckyn.py` or `cfg.py` for those.
  - It is slow on a console flooded by `terminal monitor`; use `cfg.py` there.
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only; also x230-10GP (u0) at 9600

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
- **Status:** verified 2026-10-02 on tb470, IE520 standalone (u3), read-only (self-test passed; line left clean, checked with peek)

### `peek.py`
Pre-run console check. It sends one bare CR and reports the last line: `login:`, `>`, `#`, a
config mode, or nothing. It does not log in. Use it to find a console left in config mode or a
root shell before a run.
- **Run:** `peek.py <tty> <baud> <transcript>`
- **Where:** testbox; **needs:** pyserial, `stty`
- **Imports:** none
- **Limits:** it sends one CR, so it is not strictly passive
- **Status:** verified 2026-10-02 on tb470: IE520 (u3) and x230 (u0, 9600)

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
- **Status:** verified on tb470 u3, 2026-10-02 (reboot question only, `y`; login after 189 s; running-config unchanged)

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

### `rcdiff.py`
Unified diff of the first `show running-config` in two saved `ckcon.py` **stdouts** (not the `<transcript>` argument, which has no `HH:MM:SS >>>` headers). This is the
pre-case versus post-case teardown check (STANDING-ORDERS §1).
- **Run:** `rcdiff.py <before.log> <after.log>`
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** none
- **Limits:** it needs ckcon-style `HH:MM:SS >>> cmd` headers, and crashes if a file has no running-config
- **Status:** verified 2026-10-02 on tb470 (two real IE520 captures, identical -> no output)

### `rc2cfg.py`
Turns the first `show running-config` in a saved `ckcon.py` stdout into a loadable per-device
`<dev>.cfg` (logged-output.md §2): the given header lines first (each prefixed `! `), then the
config with the echoed command, bare prompts, pager remnants, CRs and blank lines removed.
- **Run:** `rc2cfg.py <ckcon-stdout> <out.cfg> <header-line> [<header-line> ...]`
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** none
- **Limits:** it reads the ckcon `HH:MM:SS >>> cmd` stdout format only (as `rcdiff.py` does)
- **Status:** verified 2026-10-08 on tb470, IE520 stack master (u5): T22650 `stk_a.cfg`, 186 config lines

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
- **Status:** verified 2026-10-08 on the modbus group (T22650–T22655, one bench-runner transcript)

## Traffic, frames and protocol emulators

### `linerate.py`
Sends a UDP stream at a set rate, up to 1G line rate, from one host NIC and counts what arrives
on the others. It uses tcpreplay and tcpdump.
- **Run:** `sudo linerate.py --tx NIC --dst-mac MAC [--rx NIC,NIC] [--rate Mbps|top] [--secs 10] [--size 1500] [--dport 9] [--sport 5010] [--ttl 2] [--src-mac M] [--src-ip IP] [--dst-ip 192.0.2.1] [--pcap PATH]`
- **Where:** testbox (root); **needs:** scapy, tcpreplay, tcpdump, iproute2
- **Imports:** none
- **Limits:**
  - About 984 Mbps of frame bytes measured on 1G NICs.
  - IPv4/UDP only.
  - The pcap is a temporary file unless `--pcap` is given.
- **Status:** verified on tb470 2026-10-02 at `--rate 10 --secs 5`: 4178 sent (10.2 Mbps on the wire), 4178 received on eth3, 0 kernel drops. Line rate itself not re-run

### `l2flows.py`
Runs four sequence-numbered L2 flows between two host NICs, through the DUT, and records every
frame received. The flows are broadcast and unicast, in each direction. Use it for continuity
across a failover or a ring switch-over.
- **Run:** `sudo l2flows.py <duration_s> <pps_per_flow> <outdir> <nicA> <nicB> [--ethertype 0x88B5]`
- **Where:** testbox (root); **needs:** Python only (AF_PACKET, Linux)
- **Imports:** none. It provides `flow_tags` to `flowstat.py` and `loopwin.py`
- **Limits:**
  - Exactly two NICs.
  - The flow tags come from the last character of each NIC name, or A/B if those match.
  - Pacing is Python sleep.
- **Status:** verified on tb470 2026-10-02: 10 s, 20 pps per flow, eth1 <-> eth3 through the stack; 4 x 200 frames, 0 lost

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
- **Status:** verified on tb470 2026-10-02 on that `l2flows.py` run: 0 lost, 0 dups, median latency ~0.37 ms

### `loopwin.py`
Finds windows of loop evidence in an `l2flows.py` run: duplicates, and frames echoed back to
their sender. Windows are clustered with a 1 s gap.
- **Run:** `loopwin.py <flowsdir> <nicA> <nicB>`
- **Where:** anywhere; **needs:** nothing beyond Python
- **Imports:** l2flows
- **Limits:** give it the same `nicA` and `nicB` as the run
- **Status:** ran on tb470 2026-10-02 on a loop-free `l2flows.py` run: 0 windows, as expected. Not yet run against a real loop

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
Sends IGMPv2 joins (Membership Reports) or leaves from a fake receiver host.
- **Run:** `sudo igmp.py <iface> <join|leave> <group> <src_ip> <src_mac> [count=2] [interval_s=0.5]`
- **Where:** testbox (root); **needs:** scapy (contrib.igmp)
- **Imports:** none
- **Limits:**
  - IGMPv2 only.
  - `src_ip` must be a real on-subnet address; AW+ drops reports from 0.0.0.0.
- **Status:** generalised 2026-10-02, not re-verified on hardware

### `nsresp.py`
IPv6 Neighbor Solicitation responder. It answers every NS for a target in a /64 with an NA from a
unique fake MAC (`02:87:70:xx:xx:xx`), so the DUT fills its ND table and FDB.
- **Run:** `sudo nsresp.py <iface> <prefix/64> <stats.json> [stopfile]`
- **Where:** testbox (root); **needs:** tcpdump (to compile the BPF filter)
- **Imports:** none
- **Limits:** /64 only; the NIC is in promiscuous mode while it runs
- **Status:** generalised 2026-10-02, not re-verified on hardware

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
- **Status:** generalised 2026-10-02, not re-verified on hardware

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
