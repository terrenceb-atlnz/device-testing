# Session handover — 2026-10-02 (wrapped ~09:00 NZDT; re-wrapped ~10:30 NZDT)

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1,u2,u3,u4,u5 (u6 absent)
PDU: 10.36.150.14; outlets per bench-setup/tb470.static
Constraints: none


## Shareable-repo session, wrapped ~10:30 NZDT. Its own section; the side mission below is a different session

### Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0, u3 (driven); u5 (read-only, 09:41); precheck over u0–u5
PDU: none used
Constraints: AI writes only in the three repos; Terrence pushes; only this session's consoles,
precheck first; no stray .py in the lab tree; framework and ck.db read-only; never hand-edit
bench-state.md or the deployed .setup; root on the box through the Test Engineer (`sudo -n` for
the traffic senders was approved: "Traffic senders (root)"); console transcripts stay in the
box's /tmp (u3's hold a password hash)

### TL;DR

- **The repo is now testbox- and product-agnostic, and logging changed.** The rules are in
  [logged-output.md](../logged-output.md). The tester writes `work/run<N>.log` plus one `.cfg` per
  device and sends `RESULT` lines; the sentinel keeps a `## Results` table. The final
  `<id><suffix>.log` is made ONLY by `/create-logs`, on request. Helpers are in [tools/](../tools/),
  product facts in [platforms/IE520.md](../platforms/IE520.md), and the default box is in
  `bench-setup/default-boxes`.
- **None of the new logging flow has been run end to end yet.** That is next step 1.
- **Tool verification on tb470:** 25 of 33 tools are now verified (6 need DUT feature config; the 2 i2c tools are unchanged since their 08-26 smoke test); statuses are in
  [tools/README.md](../tools/README.md).
- **One dangerous bug was found and fixed** (`2df1fc0`). The old `bootmenu_escape.py` sent `9` from
  any Boot Menu screen. In `Select device`, `9` saves "Boot from default", which would undo the
  units' flash-boot default.
- **Bench, as far as this session can see:**
  - u0 and u3: exec prompt, monitor off, running-config = startup-config, boot pointers valid.
  - u2, u4, u5: held by the Test Engineer's minicom, not read.
  - **bench-state.md NOT regenerated** (stamp `2026-10-01T195349Z`), because the probe needs those
    consoles.
- **eth1 and eth3 (to stack member 3) had no carrier at 10:24**, after this session's last
  traffic test at 09:42. Detail under Findings.

### What was accomplished (commits, all by this session unless marked)

| commit | what |
| --- | --- |
| `7b96295` | logged-output.md: logging rules moved out of STANDING-ORDERS §2; template from 38472.log (structure) + 30142.log (per-step proof, topology) |
| `6209742`, `33139b0` | tools/: one repo-root home, duplicates deleted, renames (ck15lib→awlogin, ckyn3→ckyn, flows→l2flows, ra→ra_decode, phone→lldpmed_phone, recover_u5→bootmenu_escape); i2c stress tooling moved in |
| `6b48b5d`, `4c9ec2e`, `ad0e4be` | `/create-logs` skill; test-mode Results table and the closing line; bench-runner working log + `.cfg` + `RESULT`, never the final log |
| `1b5fa6a`, `a591943`, `1bda08b` | testbox-agnostic docs; `default-boxes` read by bench_probe, sentinel.sh and orient-dt; README for new engineers; wiki rewritten |
| `e37c8b4`, `788a9fa` | `platforms/IE520.md` (product facts out of orient-dt); a leftover bench fact removed |
| `877271c`, `3b10dbb`, `2df1fc0`, `7bdf2b7` | hardware verification of the tools; flash_copy/tftp_copy small-file fix; Boot Menu escape rewrite |
| `616b828`, `6617d6c`, `18423ec` | **not this session**: the rollback-image side mission and the terminal-monitor fix |

### Results: tool verification on tb470 (all clean runs)

| tool | console / path | result |
| --- | --- | --- |
| peek, ckcon, rcdiff, qmark, cfg, poll, listen, witness_log, ckyn | u3, u0 | pass (`877271c`) |
| mkpcap, mkmc, vcount, ra_decode | host | pass (scapy 2.6.1) |
| flash_copy | u3 | **hung 600 s on a 1.6 KB file** (the prompt came back inside the first read; an old bug). Fixed in `3b10dbb`; then 8 s, +0 bytes |
| ckreload | u3 | reboot question only, `y`; login after 189 s; running-config unchanged |
| reloadc `reload` | u3 | `y` 09:30:14; login banner after 187 s; running-config unchanged |
| bootmenu_escape (rewritten) | u3, parked in `Select device` | CR (re-prints the menu), `0`, `9`; login after 188 s; no `Saving settings`; `show boot` and running-config unchanged |
| vsend → vcount | eth1 → stack VLAN 1 → eth3 | 10 × ip10 + 10 × ipv6, all 20 counted |
| l2flows → flowstat, loopwin | eth1 ↔ eth3, 10 s, 20 pps per flow | 4 × 200 frames, 0 lost, 0 dups, median latency 0.37 ms; loopwin 0 windows |
| linerate | eth1 → eth3, 10 Mbps, 5 s | 4178 sent / 4178 received, 0 kernel drops |

**u3's reboot history:** the entries at 2026-10-01 20:26, 20:31 and 20:36 UTC (09:26–09:36 NZDT)
are this session's three reloads, all `Expected CLI(user request)`. The side-mission section
below calls the 09:36 reload "someone else's ckreload.py, PID 393877"; that was this session.
The `Unexpected` entries before 19:40 UTC are not this session's.

**Final logs:** this session ran no campaign cases, so there is nothing for `/create-logs`.

### Findings

**Measured:**
- The IE520 Boot Menu prompt `Enter selection ==> ` ends in `>`. In `Select device`, `9` is a
  saving selection. On the main menu, `0` is Restart. A bare CR at a menu re-prints it.
  Recorded in `platforms/IE520.md` §2.
- `flash_copy`/`tftp_copy`: a copy that finishes inside the first read used to wait out the whole
  timeout.

**Observed, cause inferred:**
- tb470 eth1 and eth3 went down together at 10:06:30, up at 10:09:39–48 (eth3 first at 2500,
  then 1000), and down together again at 10:21:27. Still down at 10:24 (from tb470's kernel log).
- Both go to stack member 3 (port3.0.10, port3.0.9). Inferred: member 3 was restarting during the
  Test Engineer's rollback work. Not confirmed, because u5 is held by their minicom.
- Proof would be `show reboot history` and `show stack` on u5.

### OPEN

1. Are eth1/eth3 back up, and did stack member 3 rejoin? Read `cat /sys/class/net/eth{1,3}/carrier`
   and `show stack` once the minicoms on u2/u4/u5 are closed.
2. bench-state.md is not regenerated. The next probe will also show the side mission's
   `coro-IE520-tb470.rel` boot image (expected, not drift).
3. Not verified yet:
   - `mb`, `igmp`, `nsresp`, `dhc6`, `rs`, `lldpmed_phone`: each needs DUT feature config;
   - `loopwin` against a real loop;
   - `linerate --rate top`;
   - the i2c tools (unchanged; the full 300 run is still deferred);
   - minor: `vsend.py --help` exits 2.

### Next steps, in order

1. **Trial the new logging flow:** `/test-mode` with one or two quick cases, then `/create-logs`
   on the queue. Check the RESULT lines, the Results table, the closing line, the final log
   against logged-output.md §4, the `.cfg` files, and the `git rm` of `work/`.
2. Probe the bench (`bench_probe.py --box tb470 run --consoles u0,u1,u2,u3,u4,u5`) when no one
   holds a console.
3. Verify the six feature tools inside the campaign cases that need them.

### Recipes (the session scratch is gone; these are complete)

```bash
sock=/run/user/$(id -u)/keyring/ssh; S="ssh -o BatchMode=yes tb470"
scp -r tools tb470:/tmp/cktools/            # then run from /tmp/cktools/tools
# reload tools (u3 = standalone, 115200)
SSH_AUTH_SOCK=$sock $S 'cd /tmp/cktools/tools && python3 ckcon.py /dev/u3 115200 /tmp/cktools/console-u3.log "show running-config" > /tmp/cktools/rc-before.txt'
SSH_AUTH_SOCK=$sock $S 'cd /tmp/cktools/tools && python3 ckreload.py /dev/u3 115200 /tmp/cktools/console-u3.log 900'
SSH_AUTH_SOCK=$sock $S 'cd /tmp/cktools/tools && python3 reloadc.py /dev/u3 115200 /tmp/cktools/console-u3.log 300 /tmp/cktools/reloadc.done reload'
#   after each: ckcon "show boot" "show running-config" > rc-after.txt; rcdiff.py rc-before.txt rc-after.txt  (empty = unchanged)
#   ckcon's STDOUT is what rcdiff reads; its 3rd argument is the raw transcript
# traffic, eth1 and eth3 both on stack VLAN 1 untagged; unicast to eth3's MAC so nothing floods
SSH_AUTH_SOCK=$sock $S 'cd /tmp/cktools/tools && sudo -n python3 vsend.py eth1 10 ip10 --src <eth1 MAC> --dst <eth3 MAC>'   # capture: sudo tcpdump -i eth3 -U -w vs.pcap; vcount.py vs.pcap
SSH_AUTH_SOCK=$sock $S 'cd /tmp/cktools/tools && sudo -n python3 l2flows.py 10 20 /tmp/cktools/flows eth1 eth3 && python3 flowstat.py /tmp/cktools/flows eth1 eth3 && python3 loopwin.py /tmp/cktools/flows eth1 eth3'
SSH_AUTH_SOCK=$sock $S 'cd /tmp/cktools/tools && sudo -n python3 linerate.py --tx eth1 --dst-mac <eth3 MAC> --rx eth3 --rate 10 --secs 5'
```

**Parking an IE520 in the Boot Menu to test an escape.** No repo tool does this; it was session
scratch.
1. Log in with `console.Console` (it applies `stty -hupcl`).
2. Send `reload`. Answer a save question `n\r` and the reboot question `y\r`.
3. Wait for `Press <Ctrl+B>`, then send `\x02` every 0.1 s **until `Boot Menu` or `Enter selection`
   appears, then stop**.
4. Read 4 s, then send a bare `2` to enter `Select device`.

Recover with `tools/bootmenu_escape.py /dev/uN` (it sends CR, then a bare `0`, then a bare `9`).
By hand: a bare `0` in a submenu, a bare `9` on the main menu, `0` + Enter in a file list.

### Pointers

- [logged-output.md](../logged-output.md), [.claude/skills/create-logs/SKILL.md](../.claude/skills/create-logs/SKILL.md),
  [tools/README.md](../tools/README.md), [platforms/IE520.md](../platforms/IE520.md),
  [README.md](../README.md)
- Memories touched: `log-is-the-deliverable`, `i2c-stress-tooling`,
  `product-dirs-archive-to-old-test-runs` (new), `ie520-bootloader-console-driving` (pointer moved
  to platforms/IE520.md §2), `sentinel-kit-in-orient-dt`, `sentinel-session-keeps-long-runs-moving`,
  `tb470-topology-and-setup`, `ie520-silent-reboot-watch-2026-09-02`

---


## Re-wrap ~10:30 NZDT — READ THIS FIRST: the stack is SPLIT on the old build

**State read at 10:25–10:26 NZDT (read-only, this session):**

| console | unit (MAC) | stack ID / role | build | boot image |
| --- | --- | --- | --- | --- |
| u2 | 84e3.2787.0ac0 (was member 1) | ID 1, Active Master, **Standalone unit** | `tomahawk_ie520-20260825-42` | `coro-IE520-tb470.rel` |
| u5 | 84e3.2787.0740 (was member 3, master) | ID 1, Active Master, **Standalone unit** | `tomahawk_ie520-20260825-42` | `coro-IE520-tb470.rel` (file exists) |
| u4 | 84e3.2787.09c0 (was member 4) | ID 1, Active Master, **Standalone unit** | `tomahawk_ie520-20260825-42` | `coro-IE520-tb470.rel` |
| u3 | IE520-sa | standalone, unchanged | `awplus_main-20260923-20` | `flash:/IE520-tb470.rel` (file exists) |

- **Three masters, one virtual MAC:** all three former members read the same
  `0000.cd37.0d6f`, and each lists only ID 1 plus a `Provisioned` ID 2. They boot the same
  config, so the stack's addresses (e.g. interface vlan10) may now be live on three units at
  once. Observed, not tested.
- **Who reloaded:** reboot history on all three reads "Expected User Request" at 21:07:16 and
  21:22:12 UTC (10:07 and 10:22 NZDT). **This session sent no reload.** A `minicom --wrap -D
  /dev/u2` (terrenceb) was running from ~10:00 and had gone by 10:25. This is the Test Engineer's
  rollback test ("verify a fault has been repaired").
- **Cause of the split: ESTABLISHED (permanent logs, read 2026-10-05).** The old build rejects
  member IDs above 2 on every boot: u5 `filesysd: VCS member-ID 3 is invalid (max is 2)`, u4 `…
  member-ID 4 is invalid (max is 2)`. Each unit then logs `No neighboring members found` and becomes
  `Member 1 … Active Master`. u2's log shows that the first reload (21:07 UTC) did briefly form a
  1/3/4 stack (21:09:16, with "booted from non-default location, SW version auto synchronization
  cannot be supported"). The split dates from the 21:22 reload.
- **Corosync / CMSG check (Test Engineer's ask, 2026-10-05):** the buffered and permanent logs of
  all three units have **no `corosync` or `totem` line at all**. The only `CMSG` lines are two on
  u2's permanent log, at 2026-10-01 19:32:50 UTC (08:32 NZDT 10-02, T24032 run 3, build
  `20260923-20`, before the rollback):
  `IE520-stk-1 VCS[4955]: CMSG(519).tport.host.req.tcp[192.168.255.3:9600]: Receive took 61 seconds`
  and the same from `IE520-stk-4` (60 s). These are members 1 and 4 waiting on the master. The
  search was verified with a positive control (`include VCS` returns 31–41 lines per unit). Since
  21:22 UTC 10-01 the units have not been stacked, so the absence of CMSG errors since then says
  nothing about the stack.
- **Unexpected reboots on the old build, standalone (to 2026-10-04, UTC):**
  - u2: 10-02 09:56, 22:12, 23:02; 10-04 11:54.
  - u5: 10-02 02:12, 05:06, 10:49; 10-03 13:49; 10-04 07:14.
  - u4: 10-01 23:36; 10-02 06:44, 14:54, 23:28; 10-03 06:13, 06:23; 10-04 09:40.
  - That is 16 in about 2.5 days.
- The "Unexpected System reboot" entries 18:15–19:40 UTC on 2026-10-01 (07:15–08:40 NZDT
  2026-10-02) are T24032's framework power cycles.
- **Final probe SKIPPED at this wrap.** The bench is mid-test by the Test Engineer, and a probe
  opens every console and switches LLDP on where it is off. bench-state.md is still the 08:53 MATCH
  (`2026-10-01T195349Z`), which describes the stack **before** the rollback. Do not `apply`
  from the split bench.
- **To restore the stack on the current build** (Test Engineer's call): on each unit
  `boot system flash:/IE520-tb470.rel` (that file is still in every unit's flash), then reload
  all three. Check that `show stack` lists IDs 1/3/4 Ready, then re-probe → MATCH.

**Also since the first wrap (commits 616b828, 6617d6c, 18423ec, all pushed by the Test Engineer):**
- The rollback image was staged (below).
- `terminal (no) monitor` was measured on u3. It is exec-only and **does not toggle**. Every
  `tools/` console driver now goes through `console.py` `monitor_off()`, which sends `end` first
  and sends nothing to a busy console. The tester's and wrap-dt's order is now `end` first (memory
  `terminal-monitor-exec-only`). u3 was left at exec with monitor off.
- No process of this session is running on tb470; precheck CLEAR on u0–u5 at 10:25. Scratch is
  `/tmp/ckflash/` on tb470 (tmpfs).
- Superseded below: the side-mission line "nothing has been reloaded yet" was true at 09:55.

## Side mission ~09:30–09:55 NZDT — rollback image staged on the stack. READ THIS FIRST

**The stack's boot pointer now names an OLD build.** The next stack reload boots
`tomahawk_ie520-20260825-42`. That is intentional (Test Engineer: "we are rolling the stack back
to an old build to verify a fault has been repaired"), and nothing has been reloaded yet.

- Source: tb470 `/tftproot/IE520-tb470.rel`, dropped there 09:24, 41,104,007 bytes, sha256
  `09bbe149…f0c5` (matches its `.sha256sum`); `.info` = `IE520-tomahawk_ie520-20260825-42.rel`.
- Staged as **`flash:/coro-IE520-tb470.rel`** (the Test Engineer's name), because AW+ refuses to
  overwrite the current boot image. It is on members 1, 3 and 4, each 41,104,007 bytes.
- How it got there:
  1. `tools/tftp_copy.py` onto the master (member 3, u5) from `10.38.215.1`: 265 s.
  2. A push from the master to member 1 (`copy flash:/… IE520-stk-1/flash:/…`) **failed** as on
     09-14 and 09-23: `nfs: server 192.168.255.1 not responding` → `% Input/Output error due to
     external media removal`. No partial file was left.
  3. **`boot system flash:/coro-IE520-tb470.rel` on the master synced it to both members in about
     5 min**: "File synchronization with stack member 4 / 1 successfully completed", on the
     console only.
- `show boot` on the master: `Current boot image : flash:/coro-IE520-tb470.rel (file exists)`.
  `Current software` is still `IE520-tb470.rel` (`awplus_main-20260923-20`), which also stays in
  flash on every member.
- **cmsg check (Test Engineer's ask): none.** The stack log has no hits for `cmsg|CMSG|Cmsg`. The
  master's console during the sync, and the consoles of members 1 and 4, printed none either
  (passive `listen.py` on u2/u4/u5 from 09:49:24). The only error logged is
  `Command [terminal no monitor] failed`, a line queued during the sync that ran in config mode.
  The console was then returned to exec with `end`.
- Stack after: 1/3/4 Ready, member 3 master. The SA links (port1.0.13, port4.0.9, port4.0.26,
  `sa3`) read down at 09:36–09:37, during a reload of the SA (u3) by someone else's
  `ckreload.py`, PID 393877, which this session left alone. All four read running at 09:55.
- **Before reloading onto the old build:** builds before `awplus_main-20260913-1734` limited the
  stack to member IDs 1–2 (memory `ie520-4stack-flashprep`). This stack is IDs 1/3/4, so check
  that members 3 and 4 rejoin. To go back: `boot system flash:/IE520-tb470.rel`.
- The bench template is unaffected (`[boot_from_flash]`). bench-state.md's "boot image" column
  will read `coro-IE520-tb470.rel` at the next probe; that is this change, not drift.

As recorded in `CAMPAIGN-QUEUE-2026-09-29.md` → Session facts (the 2026-10-02 resume: "cable
re-seated", stand down when row 6 is done).

This file stays at the legacy path (`IE520/`), because the campaign predates the 2026-10-01 layout.

## TL;DR

- **Row 6 is DONE. The campaign queue `IE520/CAMPAIGN-QUEUE-2026-09-29.md` has no runnable rows
  left in this session's scope.**
  - T24032 → **FAIL**, in [24032-fail.log](epsr-l2-2026-09-29/24032-fail.log).
  - T12067 → **UNSUPPORTED**, in [12067-unsupported.log](epsr-l2-2026-09-29/12067-unsupported.log).
  - T45788/T45789 remain the Test Engineer's to run by hand.
  - Both logs were moved with `git mv` from `switching-2026-09-22/`.
- **The bench is whole and at the template.**
  - Final probe `2026-10-01T195349Z` (08:53 NZDT): **MATCH**.
  - The tester's probe at 08:50 (`2026-10-01T195034Z`) read MATCH with no Advisories.
- **The sentinel stood down.** No subagent is running, the Monitor was already stopped, cron
  29751465 is deleted, and no stray `sentinel.sh` processes were found.

## Current bench state and how to verify it

```bash
sock=/run/user/$(id -u)/keyring/ssh
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb470 \
  'cd ~/claude/device-testing/bench-setup && python3 bench_probe.py --box tb470 precheck --consoles u0-u5 \
   && python3 bench_probe.py --box tb470 run --consoles u0-u5 --no-prompt'
```

Recorded by the tester at 08:50, with re-probe MATCH at 08:53:

| What | State |
| --- | --- |
| Running config, u0–u3 | IDENTICAL to `epsr-l2-2026-09-29/pre-test-configs/2026-10-02-24032/` |
| Stack members | agree with each other (`remote-diff`) |
| Boot config | every device boots `flash:/tb470-bench.cfg` |
| Framework cfgs | `stk_a_5706_1001.cfg`, `swi_b_5706_1001.cfg` and `TestCase_tear_down.cfg` deleted |
| Older files left | members 1 and 4 still hold `stk_a_9001_33234*/33235*.cfg` copies from the 09-28 to 09-30 runs. They are not this row's, so they were left. |
| Loop protection | baseline `loop-protection loop-detect ldf-interval 1 fast-block` restored |
| PDU | outlets 1–8 all ON. The x230 (1) and AR4050S (7) were switched off by the legacy suite on every run and switched back on each time. |
| Host | NIC pause settings never changed; no process of this session left running; precheck CLEAR at 08:53 |

**Not read at this wrap:** a per-unit `show reboot history`. This row had framework power cycles,
including 07:17 and 07:41:48, so new `Unexpected System reboot` entries are expected from them.

## What was accomplished

1. **Resumed `/test-mode --resume` on row 6.**
   - Precheck CLEAR, then triage: 2 runnable / 0 / 0. Probe `2026-10-01T171936Z` MATCH (the sa2
     leg was healthy again after the re-seat).
   - The Test Engineer chose "Proceed with both" and "TC120: Use sa4/sa5".
2. **T24032, the legacy suite `raw-data/test_scripts/5706_Platform_L2` (19 TestCases, DUT stk_a):**
   three framework runs from a staged copy with two approved patches:
   - TC120 sa1/sa2 → sa4/sa5;
   - suite VLAN 10 → 3910 (Test Engineer, relayed: "Yes, use 3910").
   - Original md5 `2ba740d6…`, staged `2242f89f…`; the diffs are in `epsr-l2-2026-09-29/evidence/`.
3. **T12067 was run by hand.** Feature-off baselines were measured first, then step 1 was refused
   by the platform. Steps 2–3 (polarity on an SFP cage) are UNSUPPORTED per the 2026-09-29 ruling.
4. **Records:**
   - three dated framework traps in orient-dt §4 (snapshot `SKILL.md.pre-20261002`);
   - memory `stack-refused-command-lands-on-backups`;
   - `bench_probe.py`'s `--consoles` now accepts the `uN` form the skills write. `u0-u5` used to
     crash it with `ValueError`.

## Results

**T24032 — FAIL.** 12 of 19 TestCases passed in the framework: 10–50, 70, 80, 90, 100, 110, 120
and 190. The other seven:

| TestCase | Graded as | Why | Clean? |
| --- | --- | --- | --- |
| TC60, TC130–160 (5) | DUT correct; FAIL is a **harness artefact** | the 80-column console wrap splits the matched strings. The DUT's own log lines prove the MAC add/age-out and every thrash action with its timeout. The suite's "timed out correctly" PASS lines are vacuous (`all()` over an empty list), so the timeouts were graded from the raw log. | clean as DUT evidence |
| TC170 | **check-timing race** | the status check at +10 s equals the LDF interval. By +15 s VLAN 1 was dropped while VLAN 3910 flowed: vlan-disable working. | clean |
| TC180 | **the one unexplained FAIL** | loop-protection action port-disable: status Normal at +10 s, traffic still flowing at +15 s. The same LDF reflector blocked in TC170 and TC190. | clean (run 3) |

Confounds that were found and removed:
- **Run 1:** the suite's VLAN 10 is the bench's own VLAN, and its tear_downs delete it. TC70 FAILed
  on that, with a full power cycle at 07:17.
- **Run 2:** TC70 was confounded by the T12067 leftover (O-1 below). It passed cleanly in run 3.
- **Ingress filtering:** the bench baseline `loop-protection … fast-block` blocks `ingress-filter
  disable`. For run 3 it was removed once before the TestSet and restored once after
  (STANDING-ORDERS §6).
- **SIGINT timing:** twice the SIGINT landed after the next TestCase's configure step had run (TC90
  in run 1, TC160 in run 2). Both were undone with their own tear_down steps.

**T12067 — UNSUPPORTED.** Baselines first, with the feature off:
- tcpreplay eth1 → eth3 ran at 976.10 Mbps (wire rate);
- with PAUSE frames sent from eth3 (195 frames, quanta 0xFFFF), the DUT counted all 195 (RX
  FlowCtrlFrms +195) and ignored them.
- So igc does send software-built PAUSE frames, and the AT-SP10TM module does not absorb them.

Then `flowcontrol receive|send on` was refused on every port tried on both IE520s (`% Error setting
flow control`; DUT log `exfx_port_flowControlSet 1979: … not supported on this product`).

## Findings

**Measured:**
- The IE520 refuses 802.3x flow control, though the command parses.
- A legacy TestSet powers off every device it did not initialise.
- The console's 80-column wrap breaks single-line log matches.
- **O-1:** the stack master refused `flowcontrol`, yet the backup members' running config got
  `flowcontrol both`.

**Inferred, not established:**
- O-1 is a product defect, not a CLI-sync quirk of the refused path.
- TC180 points at loop-protection port-disable not acting within 15 s. A hand repro would prove or
  clear it.

## OPEN questions for the Test Engineer

1. **T12067:** is the IE520 meant to support 802.3x flow control? If yes, UNSUPPORTED should become
   FAIL (`12067-unsupported.log`).
2. **TC180 / TC170:** allow a script change (a settle longer than one LDF interval before the status
   check), or a hand repro polling `show loop-protection interface port3.0.10` for 30 s?
3. **O-1:** raise it as a defect? The evidence is in `12067-unsupported.log` (O-1 section).
4. **The wrap artefacts:** a wider framework console or a wrap-tolerant match is Test-cases' (or
   your) call. Ask-CK note: `pt_preflight.py` gives a false UN-RUNNABLE on `self.`-attribute
   bindings. That has not been sent to Ask-CK.
5. **The old `stk_a_9001_33234*/33235*.cfg` files** on stack members 1 and 4: delete them?

## Ordered next steps

1. Answer the OPEN questions above; each one changes at most one log's grade or adds one repro.
2. Queue rows still open in `CAMPAIGN-QUEUE-2026-09-29.md`:
   - row 2 (33235 partial: re-run after the fibre cabling);
   - row 4 (UNBLOCKED 09-30, re-triage);
   - row 6's T45788/T45789 (yours, by hand).
3. The next session starts with `/orient-dt`. Its §0b finds tb470 from this file's Session facts.

## Recipes

- **Re-run a subset of a legacy suite, from its staged copy** (in its WORK dir on tb470, as root):
  `PYTHONPATH=/home/st-art python3 test-5706.1001.py -s /home/st-art/st-art/configs/tb470.setup -v
  --noupdate --nodefaultcfg --include-test-cases <ids>`.
  - Afterwards, switch PDU outlets 1 and 7 back on.
- **Progress of a framework run:**
  `tr -d "\000\r" < test-5706.1001.log | grep -a -E "^(<<|>>) test-|Power cycle|!!FAIL"`.

## Pointers

- Group: [epsr-l2-2026-09-29/README.md](epsr-l2-2026-09-29/README.md), plus `evidence/`,
  `pre-test-configs/` and `post-test-configs/`.
- Framework workdirs on tb470 (scratch, not ours to keep):
  `/home/st-art/pytest-create/24032/run-2026-10-02T0635`, `…T0737-rerun` and `…T0818-run3`.
- Bench: [../bench-setup/bench-state.md](../bench-setup/bench-state.md) (Generated `2026-10-01T195349Z`).
- The previous handover: [SESSION-HANDOVER-2026-10-01.md](SESSION-HANDOVER-2026-10-01.md).
