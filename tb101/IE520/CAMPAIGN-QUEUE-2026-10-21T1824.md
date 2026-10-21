# Campaign queue — tb101, IE520 4-stack as the DUT, 1 AWPTCM case (T17509 12-hour longrun with IXIA traffic), from 2026-10-21 18:24 NZDT

The ask, Test Engineer 2026-10-21 (session device-testing-56, after `/orient-dt tb101`):
*"AWPTCM-T17509 (1.0) Longrun test: Normal operation with IXIA traffic. I have IXIA connections running on 10.36.10.82
card 10 ports 5 and 6. they are connected to u3 and u4 port 25. I want to know if you can drive the ixia itself, and
perform this test case"* — then *"take the ixia sessions by force. you are allowed to reconfigure whatever you need to
on the ixia and the devices in order to perform the test. is there anything else that would block you from running
that test?"* — then, after the plan below was put to him: *"ok. please start T17509 in a tmux session, because this one
will drop the ssh soon."*

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-21 18:24 NZDT (Test Engineer's facts, carried from the 10-21 tb101 sessions and confirmed today):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb101
Consoles: u0,u1,u2,u3 (= stack members 1,2,3,4; all 115200)
PDU: none (nothing is power-cycled; the framework's post-failure cycle silently does nothing)
Constraints: none stated. Run window: start now (evening 2026-10-21), 12-hour run, ends about 07:00-08:00 NZDT
2026-10-22. One whole-stack reboot at the start (the case's own step) and one at restore; no power cycles. Sentinel
stand-down: 2026-10-22 10:00 NZDT, or at completion (§8), whichever is first.
IXIA: chassis 82 (10.36.10.82), card 10 ports 5 and 6. Terrence 2026-10-21: "take the ixia sessions by force. you are
allowed to reconfigure whatever you need to on the ixia and the devices in order to perform the test."

**Pre-answered for this unattended start (Terrence, 2026-10-21 ~18:20, in session device-testing-56):**
- `/test-mode` §1 step 2 (setup questions) and the `--resume` one-line confirmation: **answered above. Do not ask.**
- §1 step 3 (multi-hour): **this session runs in tmux on the dev host** (`tmux attach -t t17509`). Do not ask.
- §5 the proceed question: **"Proceed"** — Terrence's *"ok. please start T17509"* after the plan below. Do not ask.
  If TRIAGE reports the case NOT runnable, that is the one reason to stop: put it under **NEEDS YOU:** and end.
- No AskUserQuestion anywhere in this campaign: nobody is watching the terminal overnight. Anything that would need
  Terrence goes under **NEEDS YOU:** in this session's output AND in `## Issues` below, and the run carries on where
  it can (STANDING-ORDERS §4).

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies (§7 crafted frames with a control flow; §8 health check twice per case).
  Whole-stack reloads are allowed within the test. No PDU exists.
- **Only u0-u3 are touched.** tb101 is the Test Engineer's own box (not shared); ser2net's `precheck` FOUND is normal.
- **No root on tb101 is needed** for this case (no bond, no host traffic). Anything as root → `NEEDS TEST ENGINEER`.
- **Unattended rules** (memory `unattended-session-stalls-on-permission-prompt`): commit results FIRST; anything that
  can raise a permission prompt (an rm of a file you did not create, anything root-owned or outside the repo) goes
  LAST or to Terrence as a line in the results post.
- Case text: Ask-CK `ck.db` table `zephyr_cases`, key `AWPTCM-T17509` (`tools/ckcase.py`, ON a testbox or with
  `--db /media/terrenceb/mnt/testbox_home/claude/Test-cases/ask-ck/db/ck.db` on the dev host). Title "Longrun test:
  Normal operation with IXIA traffic", folder `/VCS (Virtual Chassis Stacking)/VCS (Stacking)/Proj 1933 XS900MX
  Stacking over RJ-45 cable`, label Platform-Test. **Objective:** *"Longrun test with IXIA Traffic."*
  **Precondition:** `IXIA(port1)---XS916MXT(master)---XS916MXS(member)---IXIA(port2)`; streams: port1 SA
  00:00:00:00:00:01 DA 00:00:00:00:00:02 fixed, EthernetII/IPv4/UDP, 192.168.1.1 → 192.168.1.2; port2 the mirror.
  **Steps (two rows):** 1. Setup configuration on attachment files in switch and Ixia (attachments NOT in ck.db).
  2. Before and after the IXIA long run: `conf t / no spanning-tree rstp enable / line console 0 / exec-timeout 0 0 /
  end / wr / reboot`, then `show sys`, `show log`, `show cpu history`, `show stack detail`. **Expected:** "show sys"
  and "show stack detail" not changed before and after; VCS remains "Normal Operation"; CPU not high before and
  after in `show cpu history`; no error log in `show log`; run for 12 hours (a TeraTerm macro in the original);
  `show memory` every hour, no memory leak.
- MANUAL-ONLY.md (repo root) is read at triage (T17509 is not listed as of 18:24).
- Platform traps: [platforms/IE520.md](../../platforms/IE520.md) (a master reload drops the CLI session on every
  backup console; a refused stack command can land on backups → `remote-diff all show running-config`).
  Bench map: memory `tb101-ie520-bench-map`; IXIA: memory `ixia-chassis-82-tcl-access` (READ IT FIRST).

## Bench at queue creation (2026-10-21 18:24 NZDT, probe `2026-10-21T025503Z` 15:55, MATCH, advisories none)

- One 4-member stack `IE520`, Normal operation, 8/8 stackports learnt (ring), **all 8 stackports 10G**,
  VMAC 0000.cd37.0d6f, `stack 1 priority 1`, members 2-4 prio 128. Member 1 (u0, S/N 264A23061) Active Master.
  Build `awplus_main-20261019-75`, bootloader 9.2.0 on all four. Boot `flash:/IE520-awplus_main-20261019-75.rel` +
  `flash:/tb101-bench.cfg` (1771 B, Oct 20 20:33:07), both `(file exists)`.
- Running-config already has the case's pre-steps: `spanning-tree mode rstp` + `no spanning-tree rstp enable`,
  `line con 0 / exec-timeout 0 0`.
- **IXIA cabling, measured 17:47 by MAC learning:** chassis 82 card 10 **port 5 ↔ port3.0.25** (member 3, console
  u2, today access vlan3, vlan3 = 3.3.3.3/24) and **port 6 ↔ port4.0.25** (member 4, console u3, today access vlan2,
  vlan2 = 2.2.2.2/24). Both `connected`, a-full a-10G, 10GBASE-SR. A 100-frame burst from each IXIA port arrived as
  input packets 100 on each switch port; MAC 0000.0000.0001 learned on port3.0.25 vlan3, 0000.0000.0002 on
  port4.0.25 vlan2.
- **IXIA ownership:** taken by force at 17:45 (Terrence's ruling) from `IxNetwork/ixia-vm18-v10/terrenceb`; both
  ports now owned by login **`terrenceb-claude`**, which persists across connections. Streams currently loaded: the
  case's pair at 1% / 100 frames (stopStream), from the write test.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | T17509 Longrun test: Normal operation with IXIA traffic | tb101/IE520/longrun-2026-10-21T1824/ | RUNNING Phase A (18:40) | 3 phases (below): A = TRIAGE + setup + before-reads + start traffic and the detached sampler (bench-runner); B = 12 h unattended, sentinel watches the sampler's files; C = stop, after-reads, grade, restore (a fresh bench-runner dispatched by a one-shot cron at T0+12h) |

## The plan (agreed with Terrence 2026-10-21 ~18:00; the tester may refine mechanics, never weaken a check)

**Three phases, because a 12-hour wait does not fit inside one subagent turn.** IXIA traffic, once started, runs ON
THE CHASSIS with no process of ours involved; the hourly reads run in a detached sampler ON tb101 (`setsid nohup`),
which survives this session, a VPN drop and a usage cut. Claude only sets up, watches and grades.

- **Phase A (bench-runner, RUN dispatch after TRIAGE):** build the tools (below), set up, reboot, before-reads,
  start traffic, launch the sampler, record T0 and the sampler PID here, hand back with row state
  `RUNNING-DETACHED until <T0+12h>`. Then the sentinel arms a one-shot `CronCreate` at T0+12h+5 min for Phase C.
- **Phase B (sentinel only, no tester):** the 15-min cron backstop reads the sampler's progress file and the latest
  IXIA counter line (read-only ssh; never a console). Healthy → silent. Sampler dead, IXIA rx rate 0, a counter
  showing loss, or a stack event → dispatch a bench-runner for a bounded check/restart of the SAMPLER ONLY (never
  restart or reconfigure traffic mid-run without recording it as a run event), and surface it under NEEDS YOU.
- **Phase C (fresh bench-runner, RUN dispatch "Phase C"):** stop traffic, final counters, after-reads, control
  burst, health 2, grade, restore, release IXIA ports, probe MATCH, `RESULT`.

**Tester refinements (2026-10-21 18:40 NZDT, tester refinement; accepted by the sentinel at the RUN dispatch). Mechanics
only, each tightens a check:**
- R1 Per-stream counting. Each IXIA port received 85 non-test frames from the switch while idle (triage 18:28), so raw
  `framesReceived` is not graded. Each rx port gets a filter: UDS1 = SA1 & DA1 = the peer's test stream (port 6: SA ::01
  DA ::02; port 5: SA ::02 DA ::01), UDS2 = SA2 = the control SA ::03. Graded: `UDS1(rx) == framesSent(peer test
  stream)` after stop. Raw rx is kept in every sample, and the non-test count (rx - UDS1 - UDS2) is reported as its own figure.
- R2 The control burst has its own SA 00:00:00:00:00:03 (DA ::02, VLAN 3 tag, 1000 frames, port 5 -> port 6), counted
  on port 6 UDS2: expected 0, beside the untagged positive 1000/1000 each way.
- R3 Memory and CPU read per member (`show memory <1-4>`, `show cpu <1-4>`) at every sample, unless the bare form is
  proven to cover all four; `show memory history` and `show cpu history` in the before- and after-reads.
- R4 Each hourly sample saves the full `show log` to its file (never into context); before/after reads add `show log permanent`.
- R5 `tools/longrun.py --detach` (setsid + double fork, PID file `<out>/sampler.pid`), launched with `tools/tb tool tb101
  lr-1824 longrun ...`; stoppable with `tools/tb killmine tb101 <pid>`.
- R6 A held master console at sample time is retried every 60 s for up to 50 min, never a silent gap (a skipped sample
  is written as SKIPPED with its reason).
- R7 Phase A's first probe ran WITHOUT --read-only before the first device change: 2026-10-21T053443Z MATCH (18:34),
  so Phase C's restore probe compares like with like.
- R8 No `take --force`: the owner `terrenceb-claude` persists; every ixtcl call does `ixLogin terrenceb-claude`.

**Topology fidelity (case: IXIA → master → member → IXIA).** Make **member 3 the master** so IXIA port 5 enters the
master (port3.0.25) and leaves on a member (port4.0.25), crossing the 3↔4 stack link: `stack 3 priority 1` and
`stack 1 priority 128`; the case's own `wr` + `reboot` then elects member 3 (lowest priority wins an election).
Terrence authorised reconfiguring the devices; his 10-21 `stack 1 priority 1` is restored at the end.

**L2 path.** Both IXIA ports into one test VLAN: `vlan database / vlan 100 state enable`; `interface
port3.0.25,port4.0.25 / switchport access vlan 100` (check VID 100 is unused first). The case's streams are one
subnet, so this is switching, not routing.

**Traffic.** The case's two streams, continuous: port 5 SA 00:00:00:00:00:01 → DA 00:00:00:00:00:02, IPv4
192.168.1.1 → 192.168.1.2, UDP 5000→5000; port 6 the mirror. **512-byte frames, 50% line rate each way** (10G →
~1.17 Mpps each way), `stream config -dma contPacket`. Start both after the MACs are learned (send the 100-frame
pair first, confirm both MACs on the right ports in vlan 100, then clear stats and start continuous).

**Control flow (STANDING-ORDERS §7), at start and at end, beside the positive pair:** a 1000-frame burst from port 5
tagged VLAN 3 (or any VID ≠ 100) → expected **0** at port 6 (port3.0.25 is untagged access vlan 100), counted on
IXIA port 6 rx and the switch's port counters; the paired untagged 1000-frame burst → 1000/1000.

**Before-reads (after the reboot, member 3 master, before traffic) and after-reads (after traffic stops):** exactly
the case's `show system`, `show log`, `show cpu history`, `show stack detail`, plus `show memory`, `show stack`,
`show reboot history`, `show interface port3.0.25,port4.0.25`, `show mac address-table | include 0000.0000.000`,
`show running-config`; and the SO §8 health check (logged-output.md §2) as health 1 and health 2.

**Hourly, by the sampler (13 samples: T0, T0+1h … T0+12h):** on the master's console (u2 once member 3 is master;
confirm at T0) `show memory`, `show cpu`, `show stack | include Operational|Ready|Master|Backup`, `show log | count`
or the last 20 log lines, `show interface port3.0.25,port4.0.25 | include packets|dropped|error|CRC`; and IXIA
`stat get statAllStats` + `stat getRate allStats` on ports 5 and 6 (framesSent, framesReceived, fcsErrors, link,
rate). One timestamped file per sample under `<group dir>/17509/work/hourly/`, plus one line per sample appended to
`<group dir>/17509/work/progress.tsv`; a `DONE` marker file when the last sample is written. Between samples the
sampler holds no console open (the master console must stay free for a rescue read). Console transcript at the
box's `/tmp/lr-1824/console-u2.log`, so the sentinel's normal mode sees it.

**Grading (case Expected + logged-output.md):**
- `show system` and `show stack detail` unchanged before → after, apart from uptime, temperatures, fan speeds and
  voltages (diff them; list every other difference).
- VCS `Normal operation` at every sample, every member `Ready`, no new `show reboot history` entry after the
  start-of-test reboot.
- CPU not high: `show cpu history` before/after and the hourly `show cpu` (report the figures; flag a sustained
  rise).
- No error in `show log` across the run (list anything at error/crit or above, and anything new that is not the
  test's own config/link events).
- No memory leak: the 13 hourly `show memory` free/used figures, trend reported as a table. A monotonic decline
  that does not plateau is a FAIL candidate (this case IS a leak test, so the trend is graded here).
- Traffic (added, it makes "Normal operation" measurable): after stop, `framesReceived(port 6) == framesSent(port
  5)` and vice versa, FCS errors 0, the switch ports' dropped 0; the hourly rates steady. Any loss is reported with
  its size and the hours it appeared in.
- Control: 0 beside 1000/1000, start and end.

## Tools to build in Phase A (repo `tools/`, README entry each; generic, not tb101-specific)

1. **`tools/ixtcl.py`** — drives an IXIA chassis through the lab's IxOS Tcl client on a testbox (recipe and env in
   memory `ixia-chassis-82-tcl-access`: `/home/ixos-IxNetwork/bin/tclsh8.5`, `ixConnectToTclServer` FIRST, then
   `ixConnectToChassis`, `ixLogin terrenceb-claude`). Subcommands at least: `status` (owner, link, type), `take
   --force`, `stream` (port, sa, da, sip, dip, size, percent, continuous | count, optional vlan tag), `start`,
   `stop`, `clear`, `counters` (one TSV line per port, absolute + rate), `release`. Every call connects,
   acts, disconnects. Print the Tcl return codes; a non-zero is an error, never ignored.
2. **`tools/longrun.py`** — the detached sampler: `--hours 12 --every 3600 --console /dev/u2 --baud 115200
   --ixia 10.36.10.82 --ports 10/5,10/6 --out <dir>`, built on `console.py` (prompt-after-echo) and `ixtcl.py`;
   survives a console error by logging it and trying again at the next sample (never exits early on one bad read);
   writes `progress.tsv` and `DONE`. Launched on tb101 with `setsid nohup <PY> longrun.py … > <out>/sampler.out
   2>&1 < /dev/null &` from a copy of `tools/` in `/tmp/lr-1824/`; record the PID here. (A remote `pkill -f` is
   forbidden — kill by PID only.)
Both run with `python3.8` on tb101 (`tools/tb` picks it). Test each against the real chassis read-only first
(`ixtcl.py status`) and on one short sample before the 12 h launch.

## Group longrun-2026-10-21T1824 — bench setup and exact restore recipe

(The tester re-checks and completes this block BEFORE its first device change; a fresh tester restores from here.)

**Recipe check (tester, 2026-10-21 18:40):** setup and restore below re-read against the 18:34 capture: boot
`flash:/tb101-bench.cfg (file exists)`; `vlan 2-3` only (VID 100 free); port3.0.25 access vlan3, port4.0.25 access
vlan2; `stack 1 priority 1` the only priority line. Additions: restore step 1 also clears the UDS filters
(`ixtcl.py reset` = port factory defaults) before `release`; restore step 3 uses whichever `stack N priority` form the
config-mode qmark check accepts and the post-restore `show running-config` must again show only `stack 1 priority 1`.

**Setup, in this order** (consoles via `tools/tb … tb101`, scratch `lr-1824`; stop on any `% ` line):
1. Record pre-run state into `17509/work/`: master's `show running-config`, `show file flash:/tb101-bench.cfg`
   (the restore target, byte for byte), `show boot`, `show stack`, `show reboot history`, IXIA `ixtcl.py status`.
2. DUT (master console, `cfg`): `vlan database / vlan 100 state enable`; `interface port3.0.25,port4.0.25 /
   switchport access vlan 100`; `stack 3 priority 1`; `stack 1 priority 128` (check the accepted form with
   `tools/qmark.py`, never a raw `?` + CR); `end`. `remote-diff all show running-config`.
3. The case's own step: `write` (writes `flash:/tb101-bench.cfg`), then whole-stack `reload` (`ckreload`/`reloadc`).
   Wait for all four `Ready`, `Normal operation`; confirm **member 3 = Active Master** and which console now reaches
   it unrelayed (u2).
4. IXIA: `ixtcl.py status` (owner still `terrenceb-claude`; if not, `take --force` — Terrence's ruling), streams as
   in the plan, MAC-learn burst, control burst, clear, start continuous at 50%. T0 = the start time.

**Restore, whatever happened, in this order:**
1. IXIA: `ixtcl.py stop`; final `counters` saved; `release` (ports 5 and 6 back to no owner, so Terrence's IxNetwork
   can take them).
2. Sampler: if still running, kill by its recorded PID only; confirm with `tools/tb ps tb101 longrun`.
3. DUT (master console, `cfg`): `interface port3.0.25 / switchport access vlan 3`; `interface port4.0.25 /
   switchport access vlan 2`; `vlan database / no vlan 100`; `stack 1 priority 1`; `stack 3 priority 128` (or its
   `no` form, whichever leaves the running-config line absent as before); `end`; `write`.
4. Verify `show file flash:/tb101-bench.cfg` equals the step-1 copy (diff in the repo); if not, list the
   differences and fix by config + `write`, never by copying a file over it.
5. Whole-stack `reload` so member 1 (priority 1) is master again, as Terrence set the bench on 10-21. Wait for
   Normal operation, member 1 Active Master, boot pointers `(file exists)`.
6. `remote-diff all show running-config`; `tools/rcdiff.py` post vs pre running-config = no diff.
7. Consoles u0-u3: `end`, `terminal no monitor`, exec prompt. `/tmp/lr-1824/` may stay (tmpfs).
8. `tools/tb probe tb101 --consoles 0-3 --baud 115200 --no-prompt` = MATCH.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues

- 2026-10-21 18:24: the IXIA ports were taken from Terrence's IxNetwork session on ixia-vm18-v10. **If that session
  reconnects or reapplies its config to card 10 ports 5/6 during the run it can take them back and stop the
  traffic** — the sentinel's IXIA rx-rate check catches it; record it as a run event, re-take (`take --force`,
  Terrence's ruling) and resume, and report the gap.
