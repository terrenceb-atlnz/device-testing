# Session handover — 2026-10-08 (~13:1x): IE520 Modbus campaign TRIAGED, not launched

Session `d849bdea…` (VS Code). It oriented without a probe, set up and triaged the Modbus campaign,
and wrapped at the Test Engineer's instruction, relayed by his peer session `device-testing-8a`:
*"have the peer session /wrap-dt to update the memories it has, do not re-run the bench probe. please ask it to apply the results it has."*
**No case was run.** The x230v2 bootloader work of the same day is in the other handover,
[../x230v2-28GS/SESSION-HANDOVER-2026-10-08.md](../x230v2-28GS/SESSION-HANDOVER-2026-10-08.md).

## Session facts
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: "u0 + u2,u4,u5" (12:2x: "The DUT will be the IE520 stack" → DUT = u2,u4,u5; u0 = x230v2 passive link partner, 115200)
PDU: "10.36.150.14 per tb470.static" (u2/swi_a=6, u4/swi_d=4, u5/swi_c=5; u0/swi_f=1)
Constraints: "Run now, no power cycles" (a failing case must not PDU-cycle in office hours: stop and ask instead; only the listed consoles and outlets)

(From [CAMPAIGN-QUEUE-2026-10-08T1131.md](CAMPAIGN-QUEUE-2026-10-08T1131.md), which also has every later ruling verbatim.)

## TL;DR
- **Campaign ready, not launched.** AWPTCM-T22650–T22655 (Modbus, Proj 2166) on the IE520 stack: triage
  12:44 found **6 runnable, 0 blocked by topology**. They need only the master console (u5) and tb470 eth1.
  The Test Engineer ruled the probe's u2/u4 conflict "a win" (12:5x). The go was due from his peer
  session just after 13:00; instead came this wrap. Resume with `/test-mode --resume` (Next steps).
- **These six cases already ran on this stack on 2026-09-29** ([../../IE520/modbus-2026-09-29/README.md](../../IE520/modbus-2026-09-29/README.md),
  5 PASS / 1 FAIL). This campaign repeats them on the newer build with the same topology.
- **`apply` was NOT run.** The only fence available (capture `2026-10-07T234226Z`, u5 only) would cut
  `tb470.setup` from 6 devices to 1. Put to the Test Engineer via the peer: OPEN 1.
- **The bench is whole and idle.** It is not parked; nothing of this session is running.

## Bench state (NOT re-read at this wrap; the Test Engineer said no probe)
Last measured by this session's triage tester, 12:42–12:44, from the master console u5 at 115200, and by
the sentinel on u0 at 12:33–12:34:

| console | S/N | member / role | baud | notes |
| --- | --- | --- | --- | --- |
| u2 | 264A23061 | 1, Backup | 115200 | banner `IE520-stk-1`; probe login rejected (`Login incorrect`). Test Engineer, 12:5x: login prompts fine |
| u4 | 264A23052 | 4, Backup | 115200 (TE) | silent to the probe from 12:42. A peek printed `sysrq: HELP` at 12:41 (BREAK; no reboot). TE, 12:5x: login prompt fine |
| u5 | 264A23066 | 3, **Active Master** | 115200 | **left logged in at exec** by the probe |
| u0 | A10783G262900002 | x230v2-28GS, standalone | 115200 | **left logged in at `awplus#`** by the sentinel's ckcon (12:34) |

- Stack: Normal operation; member 2 still **Provisioned (absent)**; build `main-calanm` (Tue Oct 6 19:44:28 UTC
  2026) from `IE520-tb470.rel`; bootloader 9.2.0 ×3; boot `flash:/IE520-tb470.rel (file exists)`, boot config
  `flash:/tb470-bench.cfg`. The per-member build comparison was **not** done (`show stack detail` not captured).
  The stack rebooted at about 12:36 (Test Engineer's baud change).
- **Master flash: 176 KB free** (106.2 of 106.3 MB). Members 1 and 4: 27.9 MB.
- Cabling, set by the Test Engineer 12:1x–12:3x to the sentinel's topology:
  - **cable 1** tb470 eth1 ↔ stack port3.0.13: 1000/full, VLAN 1; ping 10.38.215.10 and link-local
    `fe80::200:cdff:fe37:d6f%eth1` 2/2.
  - **cable 2** stack port1.0.2 (member 1, copper SFP) ↔ x230 port1.0.2: linked, LLDP-confirmed. It was first put in
    the empty port1.0.1 cage (a known dead cage) and moved on request. **Stack port1.0.2 is in
    `static-channel-group 2` (sa2)**; its other leg port1.0.9 is notconnect.
  - tb470 eth2 and eth3: no carrier.
- **x230 (u0) running-config, changed by this session at the TE's request ("ensure the x230 has the required config"),
  NOT saved:** `no lacp global-passive-mode enable`, `lldp run`. The rest is the autoburnin's running-config:
  ports in VLANs 10–37 one each, RSTP off, `service test`. Boot config `flash:/default.cfg`. A reload reverts all of it.
- **x230 clock reads NZ local time, labelled UTC** (inferred: burnin.log shows "07:18–09:06 UTC" on 10-08, but those
  times in real UTC would be 20:18–22:06 NZDT, i.e. still in the future when it was copied at 09:53 NZDT). The autoburnin
  commit message `b25726a` therefore probably shows NZDT times.
- tb470: nothing changed by this session. Scratch only: `/tmp/ckmodbus/` (sentinel), `/tmp/modbus-1008/` (tester:
  tools copy + peek transcripts).

Verify, when a session may touch the bench:
```bash
sock=/run/user/$(id -u)/keyring/ssh
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb470 \
  'cd ~/claude/device-testing/bench-setup && python3 bench_probe.py --box tb470 precheck --consoles u0,u1,u2,u3,u4,u5'
# then the full probe (all six, so the fence is complete):
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb470 'cd ~/claude/device-testing/bench-setup && \
  python3 bench_probe.py --box tb470 run --consoles 0-5 --no-prompt --pdu 10.36.150.14 \
  --outlet u0=1,u1=7,u2=6,u3=8,u4=4,u5=5'
```

## What was done
1. Orient (11:2x, no probe at the TE's request): read the x230 records; found the overnight tmux sentinel
   stuck on a prompt (memory below); verified the then-uncommitted folder move byte-identical.
2. `/test-mode` (11:31): queue [CAMPAIGN-QUEUE-2026-10-08T1131.md](CAMPAIGN-QUEUE-2026-10-08T1131.md) (2e0b7c0);
   the cases are Draft, folder `/Modbus/Proj 2166 Modbus Support`, hand-driven (no framework script).
   Precheck 11:32 FOUND (TE's own minicom on u0). TE then: x230 115200; "tell me what ports to connect";
   DUT = IE520 stack. Topology chosen from the 09-29 run (19f413f).
3. Two rejected tool calls kept running on tb470: a ckcon read of u5 sat beside the TE's minicom for about 45 s
   and was killed by PID. A u0 `show log` had already exited.
4. x230 prep (above). Sentinel armed 12:36 (Monitor + 15-min cron); triage tester dispatched (report in the queue
   row, 6026cac); TE ruling recorded (42bbdba).
5. Wrap: sentinel stood down (Monitor stopped, cron deleted, no stray `sentinel.sh`); `render` compared with the
   deployed `.setup` and sent to the peer; partial bench-state.md **restored to the committed 10-06 version**
   (the partial one is reproducible: `bench_probe.py generate captures/2026-10-07T234226Z`); memories and
   platform file updated.

## Results
None. No case ran. **Final logs: none to create.**

## Findings
Measured:
- The Test Engineer changed the stack consoles from 9600 to 115200 (stack reboot about 12:36). The deployed
  `.setup` already says 115200 for them.
- `sysrq: HELP` on u4 at 12:41 from a peek: a BREAK reached member 4's kernel; no reboot (platforms/IE520.md row updated).
- Stack port1.0.2 is still a member of `sa2` (as on 09-29), so T22655's port write will be answered exception 4.

Inferred:
- u2's probe `login_failed` with the banner present is the login-timing trap (orient-dt §3), or a CR left over from
  the baud change. The Test Engineer sees a normal login prompt; not re-checked.

## OPEN
1. **`apply`: DECIDED (a), no apply** (Test Engineer, relayed by device-testing-8a ~13:2x: *"(a) no apply. Leave the
   deployed tb470.setup as it is."*). **For the next session: cable 1 is now eth1-port3.0.13, the stack consoles are
   at 115200, and a full u0–u5 probe, then `apply`, is needed** (command in "Bench state" above). The partial fence keeps only `swi_c = /dev/u5`, `stk_a = swi_c`, outlet 5, and
   `tb-swi_c = eth1-port3.0.13`. It drops swi_a/b/d/e/f, every inter-switch `[portlink]`, and 5 of 6 `[power]` lines.
   Real changes a full re-probe should carry: eth1 now lands on port3.0.13 (deployed: port3.0.10, plus eth3-port3.0.9);
   the x230's baud is now 115200 (deployed: 9600).
2. **Consoles left logged in:** u5 (exec, by the probe) and u0 (`awplus#`, by the sentinel). Not logged out, because
   the wrap opened no console. Log out (`exit`) at the next session, or the run's own gates will.
3. **x230 running-config:** keep `no lacp global-passive-mode enable` + `lldp run` while the Modbus run is pending
   (the sentinel's recommendation), or revert. Unsaved either way.
4. **Master flash 176 KB free** (member 3): something filled it. Anything that writes to master flash will fail.
5. The probe's u2/u4 read failures were not re-tested (TE: "taking it as a win").
6. Still owed from the x230 work (the other handover): the `sudo rm /tftproot/…` line.

## Next steps
1. Full u0–u5 probe, then `apply` (OPEN 1: decided no apply now, apply after a full probe).
2. Run the campaign: start a session in `claude/device-testing/`, then
   `/test-mode --resume tb470/IE520/CAMPAIGN-QUEUE-2026-10-08T1131.md`. Row 1 is triaged. Its precheck and the
   tester's gates re-run; then dispatch RUN for T22650 → T22655. **Estimate 45–60 min** (09-29: about 40 min for the
   six plus about 10 min of gates); no reloads, no PDU. Expected, as on 09-29: T22650 FAIL on 0x0049 (member 2
   provisioned); PoE steps of T22653/T22654 UNSUPPORTED; exception 4 on T22655's sa2-member write.
3. Afterwards: `/create-logs`, then `/wrap-dt` with the full probe and the apply decision.

## Recipes
- Modbus client + Version-5 register map: `tools/mb.py`, `IE520/modbus-2026-09-29/README.md`, platforms/IE520.md
  (Modbus row).
- Compare what `apply` would write, offline: `bench_probe.py --box tb470 render > /tmp/x.setup; diff bench-setup/tb470.setup.current /tmp/x.setup`.

## Pointers
- Queue / resume record: [CAMPAIGN-QUEUE-2026-10-08T1131.md](CAMPAIGN-QUEUE-2026-10-08T1131.md)
- Memories written or updated today: `unattended-session-stalls-on-permission-prompt` (new),
  `rejected-tool-calls-keep-running-remotely` (incident 5), `ie520-first-copper-port-is-x-0-2` (port1.0.1 mix-up).
- Sentinel: stood down at the wrap; nothing armed.
