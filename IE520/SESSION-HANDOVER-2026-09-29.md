# Session handover — 2026-09-29 campaign (wrapped 2026-09-30 ~08:55 NZDT)

Session `device-testing-61`, `/test-mode` shape A: this session was the sentinel, and
general-purpose subagents followed `.claude/agents/bench-runner.agent.md` as the tester. The
bench-runner agent type itself dispatched with no tools that day; fixed in `dd2b337`, effective
from the next session.

## TL;DR

- **The bench is WHOLE and restored.** The final probe, `2026-09-29T194906Z` (08:49 NZDT 09-30),
  reads **MISMATCH on ONE declared link only**: the new fibre link `swi_b-swi_d
  port1.0.26-port4.0.26` (stack member 4 ↔ IE520-sa, AT-SPSX 1G, LLDP both ends). Terrence cabled
  it at 13:3x on 09-29, and **its `apply` is Terrence's and is pending**. Nothing else differs.
- **33-case campaign, 10 with a verdict: 5 PASS · 3 PARTIAL · 1 FAIL · 1 UNSUPPORTED.**
  - The other **23** did not run: 14 can run on today's bench, 2 are blocked on topology, and 7
    are waiting on Terrence's decision.
- **Why it stopped:** the tester ran out of usage credits at 14:57 in the middle of the VLAN
  group. A bounded follow-up recorded T38409 and restored the bench at 17:16. The sentinel stood
  down at 17:20 because the 18:00 stand-down was close.
- **Resume point:** queue row 7 (VLAN): **T38408, T38407, T18302, T18303**. Redo the group setup
  first (recipe in [vlan-2026-09-29/README.md](vlan-2026-09-29/README.md)). Command:
  `/test-mode --resume` (queue file [CAMPAIGN-QUEUE-2026-09-29.md](CAMPAIGN-QUEUE-2026-09-29.md)).
- **The one action that unblocks T33235:** Terrence runs, on tb470,
  `cd ~/claude/device-testing/bench-setup && ./bench_probe.py apply`. Then re-run T33235 on
  Test-cases `3454bc0`.
- **Commits:** committed on device-testing main, **NOT pushed** (Claude cannot push). Last
  campaign commit `e55eb48`, plus this wrap's commit.

## 1. Bench state and how to verify it

Topology and measured state: [bench-setup/bench-state.md](../bench-setup/bench-state.md),
generated 2026-09-29T194906Z.

```
stack      members 1/3/4 Ready, Normal operation, member 3 (u5) Active Master, VMAC 0000.cd37.0d6f;
           member 2 still "Provisioned" (switch 2 provision ie520-28 in the running config)
builds     IE520s awplus_main-20260923-20 (same on all); 4050 awplus_main-20260924-26; x230 5.5.5_2-20260918-7
boot       every device: <platform>-tb470.rel (file exists) + flash:/tb470-bench.cfg (file exists)
flash      stack and SA: only tb470-bench.cfg, default.cfg, IE520-tb470.rel, the gui file (no framework cfg debris)
LAGs       sa1 stack 3.0.2/4.0.2 ↔ 4050 1.0.3/1.0.4; sa2 stack 1.0.2/1.0.9 ↔ x230 1.0.3/1.0.4; sa3 stack 1.0.13/4.0.9 ↔ SA 1.0.13/1.0.9
new link   stack port4.0.26 ↔ SA port1.0.26, 1000BASE-SX, access vlan 1, non-LAG (the pending apply)
host       eth1 → swi_c (stack) port3.0.13 · eth2 → swi_b (SA) port1.0.2 · eth3 → swi_f (x230) port1.0.1;
           carrier up on all three; /nfsHome mounted; no ethtool/IP/route changes by this session
consoles   all free at wrap (sudo fuser: none); no tmux, no sniffer, no sender, no sentinel/cron
```

Verify, ON tb470, with consoles free:

```bash
cd ~/claude/device-testing/bench-setup && ./bench_probe.py run
# expect MISMATCH (1): [portlink] swi_b-swi_d bench {port1.0.26-port4.0.26, port1.0.9-port4.0.9} vs template port1.0.9-port4.0.9
# after Terrence's `./bench_probe.py apply` it should read MATCH
```

**Reboots recorded on 09-29, all explained.** Every unit logged 7 `Unexpected System reboot`
entries. The IE520s and x230 log in UTC: 2026-09-28 19:53–19:59 and 23:34–23:57. The 4050 logs in
local time: 08:53–08:58 and 12:34–12:56 NZDT. **Each is one of the framework's PDU power cycles**
after a failed case: 2 in T33234 run 2 and 5 in the T33235 fibre cases. None is the fleet's silent
reboot. The x230's 2026-09-28 02:41 UTC entry predates the campaign (see the 09-28 handover).

## 2. What was accomplished

1. Orient, then `apply` (Terrence: "apply") of the 4050/x230 PDU powerlinks → MATCH (`93a7d5e`).
2. The T33234/T33235 Port campaign found three script defects. Test-cases fixed all three
   (`4ef0dc4`, `b734b40`, `d9a08dd`, `3454bc0`):
   - T33235 TestCase_33 used `reboot(None)`, which erases the startup config.
   - The scripts sent `no polarity`, which is invalid on both platforms; `polarity auto` is right.
   - The pluggable-port cases needed gating; they are now stripped or gated on probed properties.
3. **Terrence's ruling (T33234-specific):** MDI/MDI-X does not apply to pluggable ports. T33234
   is therefore UNSUPPORTED on the IE520-28GSX, which has no fixed copper port. A copper
   pluggable keeps its copper identity for every other test.
4. Standing orders and records, all committed:
   - STANDING-ORDERS §6: the framework's post-failure restart is accepted; no setup changes
     between cases; stop a run that fails systematically.
   - bench-runner gate 9: check the script's defaulting CLI before launch.
   - orient-dt §2/§4 rows.
   - Memories: `no-power-cycle-between-testcases`, `restate-topology-gaps-before-dispatch`.
5. Triage of the 31-case extension (queue rows 6–12), then groups A (T33234 re-run + Modbus) and
   B (VLAN, partial).
6. Ledger artifact updated to v4: https://claude.ai/artifact/WnvGxuUjUBHAEGojvryatP

## 3. Results (latest run of each case)

| case | title | verdict | log | label |
| --- | --- | --- | --- | --- |
| T33235 | (3) Port — Fixed port speed | PARTIAL | [port-2026-09-29/33235-partial.log](port-2026-09-29/33235-partial.log) | clean for 1–7; 8–12 **confounded** (no fibre link then, graded FAIL by the script); stopped at 12:57 |
| T33234 | Port — Auto MDI/MDI-X | UNSUPPORTED | [33234-skip.log](port-2026-09-29/33234-skip.log) | clean (marked before run, 0 cycles) |
| T22653 | modbus - read port information | PARTIAL | [modbus-2026-09-29/22653-partial.log](modbus-2026-09-29/22653-partial.log) | clean; PoE steps N/A (no PoE) |
| T22654 | modbus - write | PARTIAL | [22654-partial.log](modbus-2026-09-29/22654-partial.log) | clean; PoE write N/A |
| T22655 | modbus - dynamic changes | PASS | [22655.log](modbus-2026-09-29/22655.log) | clean |
| T22651 | modbus - read Sensor information | PASS | [22651.log](modbus-2026-09-29/22651.log) | clean |
| T22650 | modbus - read System information | FAIL | [22650-fail.log](modbus-2026-09-29/22650-fail.log) | clean; step 5 alarm count 124 vs 93 |
| T22652 | modbus - read alarm information | PASS | [22652.log](modbus-2026-09-29/22652.log) | clean |
| T18252 | vlan classifier and tag vlan | PASS | [vlan-2026-09-29/18252.log](vlan-2026-09-29/18252.log) | clean |
| T38409 | GVRP - basic functionality | PASS | [38409.log](vlan-2026-09-29/38409.log) | clean; log written afterwards from the evidence |

Group totals and every not-run case with its reason: [CAMPAIGN-QUEUE-2026-09-29.md](CAMPAIGN-QUEUE-2026-09-29.md)
rows 4–12 and the ledger artifact.

## 4. Findings

**Measured:**
- **22650:** Modbus register 0x0049 counts the provisioned-but-absent member 2 (+31 alarms). This
  is the first real consequence of the leftover `switch 2 provision ie520-28` (housekeeping I-27).
- **The IE520 serves Modbus Mapping Version 5.** AWPTCM texts for 22650/22652 carry Version 1
  addresses. The alarm-config bitmap is MSB-first, and alarm entries are 6 words. Now in orient-dt §2.
- **A linked IE520 copper-SFP port always reads `current polarity auto`.** Ruled not applicable.
- **`polarity` is refused on a LAG member and on `saN`.** Speed and duplex tests must free the
  link first (orient-dt §2).
- **The framework PDU-cycles every bound unit after any failed case,** and each cycle shows as
  *Unexpected System reboot* (orient-dt §4).
- **`service pdm` (PIM-DM) exists on this build.** The memory line has been corrected.

**Observed, cause not established:**
- **GVRP O-1:** a VLAN created after GVRP is running is not announced until the port's `gvrp` is
  bounced (38409.log).

## 5. OPEN — Terrence's decisions, carried forward

1. **Apply the SX fibre link?** `./bench_probe.py apply` on tb470. This unblocks the T33235
   re-run. At 1G the 10G-and-faster fibre steps only record "speed rejected"; a 10G measurement
   needs an SR module in stack port1.0.25.
2. **Fit a second host port on the stack?**
   - Fit a copper SFP in stack **port3.0.9** (the spare AT-SPTXc is in IE520-sa port1.0.1).
   - Cable **eth2 or eth3** to it, then probe and apply.
   - This unblocks **T24032** (the 5706 L2 suite binds two tb↔DUT links) and **T12067** (flow
     control needs two endpoints directly on the DUT).
3. **Decision-blocked cases:**
   - T45788 and T45789 (EPSR performance, an Ixia suite): is a hand-run two-node ring
     acceptable, and what is the pass criterion? 45789 also needs a working 10G link. The SA's SR
     module sits in the suspect cage 1.0.25; move it to a good SFP+ cage and cable it to x230
     1.0.10 (hands).
   - T28863 (MRP stack failover, no steps). Proposed reading: reload the master (member 3), then
     repeat with the master on a ring member.
   - T38410 (Voice VLAN): emulate LLDP-MED with scapy, or skip?
   - T5082 (DHCPv6 EUI-64): its steps defer to CR00036691/CR00036689, which are not in ck.db.
     Pass criteria are needed.
   - T12589 (actually a PBR case): run a probe for `set ip next-hop` support?
   - T27887: VLAN-based QinQ (`vlan-stacking`) is absent on both IE520s. Confirm UNSUPPORTED?
4. **Raise as defects?** 22650 (alarm count counts a provisioned member); GVRP O-1.
5. **Update the Modbus case texts** from Version 1 to Version 5 addresses.
6. **Housekeeping still open:** remove `switch 2 provision ie520-28` from the stack and the SA
   (I-27; it is now the cause of the 22650 FAIL). The older ledger rulings 1–19 are unchanged.
7. **Ignored evidence files:**
   - What: four `run.stdout` under `port-2026-09-29/framework-run*/` and four `18252-*.pcap`
     under `vlan-2026-09-29/evidence/`, 3.3 MB in total.
   - Status: gitignored and untracked, sitting on the share.
   - Question: keep them (`git add -f`) or delete them?

## 6. Next steps, in order

1. `/orient-dt`. Expect the one-link MISMATCH until Terrence applies.
2. `/test-mode --resume`, starting at **row 7**: T38408, T38407, T18302, T18303. Redo the group
   setup (below) once, and restore once at the end.
3. Row 9, MRP as a two-node ring with the IE520-sa: T38093, T38097, T38098, T38099.
   - Ring ports: stack 1.0.13 (member 1) + 4.0.26 (member 4) ↔ SA 1.0.13 + 1.0.26.
   - Take 1.0.13 out of sa3 on both ends and **shut** the other sa3 leg, 4.0.9↔1.0.9. STP is off,
     so a third parallel link loops.
4. Rows 10–12:
   - T5093 DHCPv6 relay (the 4050 serves over vlan10).
   - T8770 IPv6 neighbours (the 6057 responder method).
   - T3116 BGP at line rate (SA as peer, eth2 as receiver).
   - T11346 PIM-DM, T18948 VRRP, T10624 OSPF.
5. Once applied: re-run T33235 (row 4) on `3454bc0`. The same two-leg sa2 isolation is needed.

**The 14 runnable cases:** 38408 38407 18302 18303 · 38093 38097 38098 38099 · 5093 · 8770 3116 ·
11346 18948 10624.

## 7. Recipes

**VLAN group setup** (09-29 14:27–14:30), and **restore** (17:14–17:16).
- Full commands: [vlan-2026-09-29/README.md](vlan-2026-09-29/README.md) and
  `vlan-2026-09-29/evidence/group-restore.sh`.
- In short: shut each leg first, `no static-channel-group`, then `switchport access vlan
  <scratch>`, then `no shutdown`:
  - stack 1.0.2 → 3991, 1.0.9 → 3992, 1.0.13 → 3993, 4.0.9 → 3994
  - x230 1.0.3 → 3991, 1.0.4 → 3992
  - SA 1.0.13 → 3993, 1.0.9 → 3994
- `interface sa2`/`sa3` auto-delete. The restore recreates them from the pre-test copies, and
  sets the x230 ports back to access vlan 100.

**Framework run by hand** (TESTBOX-ACCESS §3):
- Copy the script, `library_9001.py`, and `ask-ck/tools/pt_media.py` as `ck_media.py` into a
  dated WORK directory under tb470 `/tmp/ck<case>/`.
- Symlink the framework into it.
- Run inside `tmux new -d -s t<case>`:
  `sudo -n env PYTHONPATH=/home/st-art python3 -u ./<script> -s /home/st-art/st-art/configs/tb470.setup -v --noupdate --nodefaultcfg`,
  piped to `run.stdout`.
- Afterwards: `boot config-file flash:/tb470-bench.cfg` on every bound device, then delete
  `*_9001_<case>*.cfg` and `TestCase_tear_down.cfg`.
- Single-case selection: `--include-test-cases <n>` (not yet exercised).

**Watching a framework run from the sentinel:** the kit's default globs do not see
`/tmp/ck*/run.stdout`. Add a Monitor:
`ssh tb470 'tail -F <WORK>/run.stdout' | stdbuf -oL tr -d '\000\r' | grep --line-buffered -E '!!FAIL|no longer reliable|Power cycle .*completed|y/n|Traceback|EXIT='`.

## 8. Pointers

- Queue and issues: [CAMPAIGN-QUEUE-2026-09-29.md](CAMPAIGN-QUEUE-2026-09-29.md), issues I-1 to I-10.
- Group records: [port-2026-09-29/README.md](port-2026-09-29/README.md),
  [modbus-2026-09-29/README.md](modbus-2026-09-29/README.md),
  [vlan-2026-09-29/README.md](vlan-2026-09-29/README.md).
- orient-dt edits this wrap: §2 rows for Modbus Mapping V5 and GVRP O-1; a §4 row for framework
  cycles showing as *Unexpected System reboot*. Snapshot: `SKILL.md.pre-20260930`.
- Memories updated this wrap: `awplus-service-gated-routing-daemons` (PIM-DM line superseded) and
  `sentinel-kit-in-orient-dt` (toolless agent type, usage death mid-group, watching a run dir).
- The sentinel stood down at 17:20 on 09-29: Monitor stopped, cron deleted, no strays. It was
  re-confirmed at this wrap.
