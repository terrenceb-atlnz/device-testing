# Session handover — 2026-10-02 (wrapped ~09:00 NZDT)

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1,u2,u3,u4,u5 (u6 absent)
PDU: 10.36.150.14; outlets per bench-setup/tb470.static
Constraints: none


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
