# Campaign queue — tb277 x960-56YSQ, 6 AWPTCM DHCP cases, from 2026-10-15 14:58 NZDT

The ask (Test Engineer, 2026-10-15): *"Please do the test cases that I give you"*, with a
screenshot of six AWPTCM cases for **x960-56YSQ**. Earlier in the same session: *"Don't worry
about the test cases that you have done — that is done and dusted. Don't worry about the number
that you saw on the screenshot … Some of the test cases will be done manually by me"*, then:
*"the list that I send you are the ones that you would be required to do. I won't send you the
list of test cases that have been manually done."*
⇒ **This campaign is exactly these six. No reconciliation against any earlier list.**

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom, continues from
the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state changes.

## Session facts

Recorded 2026-10-15 14:58 NZDT. The Test Engineer's answers, confirmed verbatim:
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None

Devices, measured by `bench_probe.py` 2026-10-15T012929Z (`bench-setup/tb277/bench-state.md`):
- **DUT — swi_d, /dev/u2 @115200, AT-x960-56YSQ, S/N `A2WQS700B`**, standalone Active Master,
  software **`sin_x96056-20261012-24`** (Mon Oct 12 2026), bootloader reads `Unknown`,
  **boots from FLASH** (`flash:/x960-tb277.rel`, file exists), flash 166 MB used of 14.3 GB,
  hostname `awplus` — **the DUT is at default config**.
- partner — swi_b, /dev/u3 @9600, AT-x960-28YSQ, S/N A10737A261700021,
  `sin_x96056-20260921-9`, boots `flash:/backup.rel`, hostname `x960-28YSQ`.
- partner — swi_a, /dev/u5 @9600, AT-x950 GEN2-52XSTQm, S/N A10713A262600012,
  `awplus_main-20261008-56`, netboots, boot image **Not set**, hostname `awplus`.

**🔥 The DUT is a DIFFERENT PHYSICAL UNIT from the 2026-10-08 campaign** (`A2WQS700B`, was
`A2WQS7004` = `swi_c`) on a build three weeks newer, and it now boots from flash instead of
netbooting. Confirmed by the Test Engineer: *"The DUT is the same, just a different unit. Boots
from flash now."* `tb277.static` is append-only, so it still carries the stale `swi_c` line.

Links (measured, richer than the 10-08 campaign's):
```
tb eth3 ──── swi_d port1.0.10        swi_a 1.0.1  ── 1.0.1  swi_b
tb eth4 ──── swi_d port1.0.48        swi_a 1.0.11 ── 1.0.11 swi_b
tb eth2 ──── (carrier up, unlearned) swi_a 1.0.4  ── 1.0.4  swi_d
                                     swi_a 1.0.14 ── 1.0.14 swi_d
                                     swi_b 1.0.2  ── 1.0.2  swi_d
                                     swi_b 1.0.16 ── 1.0.16 swi_d
```
Two host NICs reach DUT **switch ports**, so inject-and-observe across the DUT is available
without recabling.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **`logged-output.md`**. Final logs are made only by `/create-logs`, on request.
- `STANDING-ORDERS.md` applies in full. Constraints are "None", so the tester has full authority
  within the tests, including power-cycling the three units.
- **🔥 STANDING-ORDERS §7 (Test Engineer, 2026-10-15): traffic tests use scapy, not ping.** Craft
  the exact frame the rule matches, send a known count, count arrivals, and send a **control**
  flow in the same run that must NOT match. These six are DHCP cases — DISCOVER/OFFER/REQUEST/ACK,
  Option 82 insertion and stripping, relay rewriting, ARP probing — none of which a ping can
  express. Use `tools/` first; anything new is generic and lands in `tools/` with its README entry.
- **Satisfactory level of testing** (Test Engineer, 2026-10-08): the step text is the FLOOR —
  also prove removal (gone from running-config) and persistence across reboot; baseline OFF first.
- Nothing is written to startup-config unless a case requires it.
- Teardown verified by diffing `show running-config` against the pre-case copy.
- Gate each dependent step on proven state, never on an exit code alone; a benign `% ` advisory
  reads as failure to a stop-on-error driver (`platforms/x960.md` §5).

## 🔴 Case steps: NOT in ck.db — ground them in the feature docs

`ck.db` does **not** contain these six. Proven three ways on 2026-10-15: no title anywhere in
`testlink_cases` contains `IPv4_`; `atp_tests` has no `IPv4_DHCP` rows (its DHCP suites are
IxANVL, a different thing); and the AWPTCM-T numbering is absent from the database entirely.
Title `LIKE` searches return many plausible-but-different cases (five "ARP Probe", six
"Option 82"), so **no ck.db case may be mapped to one of these six** — that would be fabricating
a source. See memory `ckdb-case-lookup-by-title`.

⇒ Per the Test Engineer's 2026-10-08 rule (memory `review-feature-docs-before-testing`), steps
are grounded in, and cite, these three — NOT reconstructed from the title alone:
1. **Software TPS** — `https://wiki.atlnz.lc/awpwiki/index.php?title=X960_platform_support_TPS&action=raw`
   (confirmed reachable from tb277, 200, 70,440 B). Quote the DHCP support row per case. A row
   saying **No** is UNSUPPORTED with the TPS as evidence; a row saying **Yes** whose command is
   absent on the DUT is a **finding**, not a limit.
2. **Feature Overview and Configuration Guide** — the public guide for each feature.
3. **Test Strategy** for the x960-56YSQ.
Fetch on the box with `curl -sk` (`lab-wiki-reachable-from-a-testbox`); the dev host cannot reach
the wiki and neither can WebFetch.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | T43850 Option 82 · T43851 ARP Probe · T43852 DHCP Relay · T43853 120-day lease | dhcp-server-2026-10-15T1458 | PENDING TRIAGE | DUT as DHCP server/relay; needs a crafted-DHCP client and a capture point |
| 2 | T43854 DNS Relay · T35370 DHCP Extended ID | dhcp-client-2026-10-15T1458 | PENDING TRIAGE | DUT as DHCP client; needs a server to answer it |

Grouping is provisional — triage may re-cut it (T43852 and T43850 are relay-shaped, which is a
different setup from a server pool).

## Known bench notes

- **The DUT is at default config**, so every group builds its own setup from scratch.
- **swi_a holds no config across a reboot** (`show boot` → `default.cfg (file not found)`, empty
  flash, netboots). Carried from the 2026-10-12 handover as OPEN-1. Any case using swi_a must
  reconfigure it after any reload.
- **The DUT's clock reads year 2000** (`Sat Mar 25 2000` at probe). Same RTC fault the previous
  unit had, so it looks like a model trait. Repair it with `clock set` (exec-only, no
  running-config footprint) before the first case and record the pre-change value.
- **`tools/tb` does not work on tb277**: it invokes the box's `python3` (3.6) and
  `bench_probe.py` dies with `TypeError: __init__() got an unexpected keyword argument
  'capture_output'`. Use `python3.8` explicitly for every tool on this box. Logged as I-1.
- Occupancy 2026-10-15 14:58: u2, u3, u5 all **free**; the only FOUND item is the box-wide
  `ser2net` (pid 744), which maps only `ttyS0`/`ttyS1` and holds no USB console — cleared by the
  Test Engineer on 2026-10-07 and run over by 13 cases since.

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |

## Issues

Status: OPEN (waiting on the Test Engineer), CHOSEN (a blocker; recommendation applied for
review), NOTED (no decision needed now), CLOSED (decided or answered).

- **I-1 `tools/tb` is broken on tb277** — runs the box's python3.6. NOTED; use `python3.8`.
  Worth fixing in the wrapper so the next session does not rediscover it.
- **I-2 Case steps are not available from AWPTCM or ck.db.** Grounded in the TPS, the Feature
  Overview guide and the Test Strategy instead (above). Every verdict must say so, and cite the
  TPS row it rests on. NOTED.
- **I-3 The sentinel watches every testbox, not just this one.** `sentinel.sh` reads the
  framework's per-device logs under `/home/st-art/pytest-create/*/*/`, which is on the SHARED
  lab home (`10.36.250.11:/home`), so a watch on tb277 also replays tb470's runs. On the first
  arm (2026-10-15 15:00) that dumped ~11 MB of 2026-10-08→13 backlog — stale tb470 IE520 and
  x230v2 framework logs and week-old tb277 console transcripts — straight into the sentinel's
  context before a single case had run, and the harness suppressed events for rate. Fixed for
  this session by stopping the watch, letting the pass baseline 415 remote offsets at EOF, and
  re-arming. **The kit should scope the remote glob to this box's own runs, or baseline silently
  on a first arm.** NOTED — worth fixing in `.claude/skills/orient-dt/sentinel/sentinel.sh`.
