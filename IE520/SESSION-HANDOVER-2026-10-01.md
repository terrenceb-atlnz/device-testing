# Session handover — 2026-10-01 (wrapped ~11:40 NZDT)

Session `device-testing-67`: `/orient-dt`, a bench-state update after Terrence's pluggable swaps,
then `/test-mode verbose --resume` of [CAMPAIGN-QUEUE-2026-09-29.md](CAMPAIGN-QUEUE-2026-09-29.md)
in the one-session shape: this session was the sentinel, and `bench-runner` subagents did the
testing, one per queue row. Rows 12 → 16 → 17 ran. **The queue is now complete.**

## TL;DR

- **Campaign 2026-09-29 is COMPLETE.** 33 cases: **22 PASS / 5 FAIL / 2 UNSUPPORTED / 4 NOT
  TESTED** (the queue's row 6, still BLOCKED). The table is in §3, and it was built from the log
  NAMES (STANDING-ORDERS §2), not from memory.
- **Today's results:**
  - **T11346, T18948, T10624: PASS.**
  - **T12589: FAIL** (two real PBR defects, §4).
  - **T33235: PASS** (32 PASS / 1 UNSUPPORTED / 0 FAIL). This is the first time the fibre sweep
    was measured.
- **The bench is WHOLE and equals the template.** The final probe `2026-09-30T222718Z` (11:27
  NZDT) reads **MATCH** with no advisory. Every device's running-config is IDENTICAL to its
  pre-test capture, and all four boot from `flash:/tb470-bench.cfg (file exists)`.
- **Terrence's items, all his own:**
  - **Remove the tb470 iptables rule** `iptables -D FORWARD -s 192.168.10.0/24 -j DROP`. You
    added it during T12589, and it is still in place.
  - `git push origin main`.
  - Decide on row 6 (§6).
- **Sentinel stood down** at the wrap: the Monitor stopped, cron `5ebcaa8f` deleted, and the stray
  sweep found no `sentinel.sh` processes. No subagent is running.
- **Commits:** `2ab61f7` … `5067833` (tester) plus this wrap's commit on device-testing `main`.
  **Committed, NOT pushed.** Claude cannot push.

## 1. Bench state and how to verify it

For the topology, see [bench-setup/bench-state.md](../bench-setup/bench-state.md), generated
2026-09-30T222718Z. Read at the wrap, 11:21–11:30 NZDT:

```
stack      members 1/3/4 Ready, Normal operation, member 3 (u5) Active Master, VMAC 0000.cd37.0d6f
builds     stack + IE520-sa awplus_main-20260923-20 (build date Tue Sep 22 14:25:56 UTC, equal);
           x230 awplus_5.5.5_2-20260918-7; AR4050S awplus_main-20260924-26
boot       every device <platform>-tb470.rel (file exists) + flash:/tb470-bench.cfg (file exists);
           the framework's swi_*/stk_a_9001_33235*.cfg and TestCase_tear_down.cfg deleted on all four
reboots    since the 09-30 wrap, all explained (times UTC; NZDT = +13):
             19:09 / 19:50 / 20:41  reloads by the row-12/16 testers (clearing lingering daemons)
             21:44                  T33235 framework PDU cycle after TestCase_20 (10:42 NZDT)
             22:09                  T33235's own whole-stack `reload` step (11:09 NZDT)
             member 4 07:28 09-30   Unexpected System reboot (20:28 NZDT 09-30, nobody on the bench), OPEN §5
host       eth1 -> stack port3.0.10 (AT-SPTXc, autoneg), eth2 -> SA port1.0.2, eth3 -> x230 port1.0.1;
           all carrier up, autoneg on, advertising 10/100/1000 + 2500baseT (no pinning left)
iptables   FORWARD -s 192.168.10.0/24 -j DROP  <- Terrence's, still in place, his to remove
consoles   all free (sudo fuser: none); no sniffer, sender, framework run, Monitor or cron
scratch    tb470 /tmp/ck*/ dirs (tmpfs, dies with the box)
```

Verify, ON tb470, with the consoles free:

```bash
cd ~/claude/device-testing/bench-setup && ./bench_probe.py run
# expect: MATCH -- the bench equals the template. ~15 s, no advisory.
sudo iptables -S FORWARD | head -3     # the 192.168.10.0/24 DROP line is there until Terrence removes it
```

## 2. What was accomplished

1. `/orient-dt`. Then, after **Terrence's deliberate pluggable swaps**, `bench_probe.py
   run` → `apply` → MATCH (`2ab61f7`). The only template change is `tb-swi_c = eth1-port3.0.10`
   (it was port3.0.13, now an empty cage). The apply's snapshot pair is
   `backups/2026-09-30T185542Z.*`, and this wrap commits it with `bench-state.current.md`.
2. **Row 12 (routing group):**
   - T11346 was written up from the 2026-09-30 evidence and then restored, on Terrence's
     "Write up, then restore": no re-run.
   - T18948 and T10624 were run by hand.
   - At the group close, the stack and SA were reloaded to clear the lingering vrrpd/ospfd/pdm
     daemons. Configs were then IDENTICAL, and the probe read MATCH (`9468f10`).
3. **Row 16:** the T12589 full PBR build (RIPv2/v1, two next-hop VLANs, traffic) was a **FAIL**
   (`180f983`). During the run the stack **leaked** matched traffic out to tb470. Terrence
   contained it with the iptables rule above ("did (b), continue"): 10,161 packets had leaked
   before the rule, and none after it (30,480 dropped).
4. **Row 17:** T33235 re-run 4, on Test-cases `3454bc0`, **PASS** (`daf6313`, `5067833`).
   - The sa2 legs were isolated into VLANs 3998/3999 once, before the TestSet, and restored once
     after it (STANDING-ORDERS §6).
   - There was one framework PDU cycle, at 10:42, and it succeeded.
5. **The sentinel kit was fixed.** `sentinel.sh` now skips *any* sentinel's output file, not just
   its own. Before, the first re-arm replayed the expired watcher's whole output (2158 lines in
   one tick). All four later re-arms were clean.
6. **Records:**
   - Memory `awplus-service-gated-routing-daemons`: the old claim that "PIM-DM has no service
     command" is corrected to `service pdm`. Added: `no service X` lingers until a reload, and
     `router rip` can be refused right after `service rip`. The stale "reboot not an option" line
     now points to flash boot.
   - orient-dt §2: two dated rows (snapshot `SKILL.md.pre-20261001`). One is the AT-SPTXc
     autoneg counter-observation. The other refines the media-blind row: speeds are offered but
     refused when run.

## 3. Results — campaign 2026-09-29, complete

Every row is *clean* unless it says otherwise. Logs are under `IE520/<group>/`.

| group | case | outcome | log | commit |
| --- | --- | --- | --- | --- |
| port | T33234 Auto MDI/MDI-X | UNSUPPORTED | port-2026-09-29/33234-unsupported.log | 5161b71 |
| port | T33235 Fixed port speed | **PASS (today)** | port-2026-09-29/33235.log | 5067833 |
| vlan | T18252 vlan classifier and tag vlan | PASS | vlan-2026-09-29/18252.log | 09bba4f |
| vlan | T18302 Private VLAN, send from uplink | PASS | vlan-2026-09-29/18302.log | 589fefd |
| vlan | T18303 Private VLAN, send from private | PASS | vlan-2026-09-29/18303.log | ce1bee9 |
| vlan | T27887 vlan-based QinQ interop + translation | UNSUPPORTED | vlan-2026-09-29/27887-unsupported.log | c0304bb |
| vlan | T38407 VLAN translation basic | PASS | vlan-2026-09-29/38407.log | a629849 |
| vlan | T38408 QinQ basic | PASS | vlan-2026-09-29/38408.log | 424db54 |
| vlan | T38409 GVRP basic | PASS | vlan-2026-09-29/38409.log | e55eb48 |
| vlan | T38410 Voice VLAN basic | PASS | vlan-2026-09-29/38410.log | 6f9ec7d |
| modbus | T22650 read System | FAIL | modbus-2026-09-29/22650-fail.log | 47d861d |
| modbus | T22651 read Sensor | PASS | modbus-2026-09-29/22651.log | 4d18b85 |
| modbus | T22652 read alarm | PASS | modbus-2026-09-29/22652.log | c3eb4df |
| modbus | T22653 read port information | PASS | modbus-2026-09-29/22653.log | 5161b71 |
| modbus | T22654 write | PASS | modbus-2026-09-29/22654.log | 5161b71 |
| modbus | T22655 dynamic changes | PASS | modbus-2026-09-29/22655.log | 0c9c08d |
| mrp | T28863 MRP stack failover | PASS | mrp-2026-09-29/28863.log | 61fd69c |
| mrp | T38093 DUT as MRM | FAIL | mrp-2026-09-29/38093-fail.log | 61fd69c |
| mrp | T38097 DUT as MRC | PASS | mrp-2026-09-29/38097.log | 9fdc3ca |
| mrp | T38098 ring switch-over 200 ms | PASS | mrp-2026-09-29/38098.log | 61fd69c |
| mrp | T38099 ring switch-over 500 ms | PASS | mrp-2026-09-29/38099.log | 73c9092 |
| dhcpv6 | T5082 EUI-64 + /64–/128 advertised prefix | FAIL | dhcpv6-2026-09-29/5082-fail.log | 9b680aa |
| dhcpv6 | T5093 DHCPv6 Relay basic | PASS | dhcpv6-2026-09-29/5093.log | d9fc885 |
| ipv6-bgp | T3116 BGPv4 unicast traffic | PASS | ipv6-bgp-2026-09-29/3116.log | ab88928 |
| ipv6-bgp | T8770 IPv6 Neighbors in silicon | FAIL | ipv6-bgp-2026-09-29/8770-fail.log | b9c1c7e |
| routing | T10624 OSPF silicon tables synced | **PASS (today)** | routing-2026-09-29/10624.log | 5e65e8b |
| routing | T11346 PIM-DM end-to-end | **PASS (today)** ¹ | routing-2026-09-29/11346.log | 650da90 |
| routing | T12589 Interop RIPv1/v2 (PBR) | **FAIL (today)** | routing-2026-09-29/12589-fail.log | 180f983 |
| routing | T18948 VRRP routes near wirespeed | **PASS (today)** | routing-2026-09-29/18948.log | 034f4c7 |
| epsr-l2 | T45788, T45789 EPSR performance SFP / SFP+ | NOT TESTED | — (Terrence runs these by hand) | — |
| epsr-l2 | T24032 5706 L2 platform; T12067 flow control with MDI | NOT TESTED | — (BLOCKED, §6) | — |

¹ The run was on 2026-09-30, 18:27–19:12, and its session ended before it wrote a log or
restored the bench. The log was written today from that run's own evidence, on Terrence's
instruction, and the restore was done today.

## 4. Defects and observations — the summary Terrence asked for at the end

Terrence, 2026-09-30: *"raise them all at the end, as a summary for the next session"*. The
wording in the case logs is authoritative, and each item names its log. This list covers today.
The earlier ones are in [SESSION-HANDOVER-2026-09-29.md](SESSION-HANDOVER-2026-09-29.md), the
2026-09-30 handover, and the queue's `## Issues` list.

**Product (IE520, awplus_main-20260923-20), measured:**

1. **T12589 D-1: PBR misdirects traffic when its next hop is unusable.** The stack neither falls
   back to the routing table nor drops. It sends the matched traffic back out the ingress port,
   untagged in vlan1, to the first MAC in its ARP table (tb470 eth1). This is what leaked to tb470.
   Proof: the FORWARD DROP counter rose by 5080 per misrouting run, and a capture on the live
   uplink saw 0 frames from 192.168.10.0/24. See `routing-2026-09-29/12589-fail.log`.
2. **T12589 D-2:** after the next-hop VLAN comes back up, PBR never re-resolves its next hop's ARP.
3. **PIM-DM counter (T11346):** after PIM-DM is removed, `show ip pim dense-mode interface` reads
   "Total configured interfaces: -1".
4. **T11346 observations:**
   - A PIM assert "Loser" was seen once.
   - Loss was 0.008–0.014 % at a full 100 % line-rate offer, and none at 95 %.
5. **`no service pdm|vrrp|ospf|rip` needs a reload.** The daemon lingers otherwise. The CLI says
   so ("Save the config and restart"); this is a usability note, not a failure.
6. **Stack member 4 Unexpected System reboot** at 2026-09-30 07:28 UTC (20:28 NZDT), with nobody
   on the bench. It fits the known fleet pattern (orient-dt §1). It is reported because it happened
   on a quiet bench.
7. **SA port1.0.2 cage failed to set up an AT-SPTXc** (`PluggableSetup rc=1`) after an SP10TM was
   hot-swapped out, during Terrence's swaps before the campaign resumed. He swapped the modules
   back and it linked.
8. **T33235 O-1/O-2, platform facts, not defects:**
   - On the AT-SPTXc, only `speed 100`/`1000` can be fixed (`speed 10` gives `% Unsupported
     speed/duplex combination`), and the x230's RJ45 rejects ≥2500.
   - On the AT-SPSX, only `speed 1000` is accepted on both IE520s, although the CLI offers every
     speed.

**Test-cases scripts (for the Ask-CK side):**

9. **T33235 D-1 = the I-8 pattern again.** A step the script already knows is not applicable is
   reported through `self.supported=False` **plus** `self.failed()`. The framework grades it
   UNSUPPORTED but still power-cycles the whole six-unit bench (TestCase_20; about 4 minutes). The
   same guard exists in other generated cases. Fix: use the `3454bc0` pre-marking pattern, or log
   and return without `failed()`.
10. **T33235 D-2:** under `--nodefaultcfg`, the TestSet tear_down's startup-config restore is
    refused (`% Cannot overwrite flash:/stk_a_9001_33235.cfg as it is configured as the boot
    config file`). The script ignores the result and deletes the backup, so the log shows a
    restore that never happened. It is harmless on tb470, because the tester restores the boot
    pointer itself.

**Bench / infrastructure:**

11. **PDU outlet 5 reads status '2' after power-on.** The framework's three-attempt check fails,
    and a fourth call succeeds. This is the second time (the first was 2026-09-29 12:55). The unit
    boots normally.

## 4b. After the wrap (12:35–12:55 NZDT): row 6's second NIC fitted

On Terrence's request, "Which eth do you want moved into the stack, and where": **eth3 was moved
from x230 port1.0.1 to stack port3.0.9** (member 3, u5).
- The module in 3.0.9 is the AT-SP10TM taken from SA port1.0.2. The "spare AT-SPTXc in SA
  port1.0.1" named in the 09-29 notes did not exist any more: SA 1.0.1 read `not present` in
  every probe today.
- Terrence then put eth2 back on SA port1.0.2 (10GBASE-TM, 1000/full).
- `bench_probe.py apply` ran on his "run apply" (snapshots `backups/2026-09-30T235326Z.*`). The
  re-probe reads **MATCH**.
- New template: `tb-swi_b = eth2-port1.0.2`, `tb-swi_c = eth1-port3.0.10, eth3-port3.0.9`.
  **There is no `tb-swi_f` now**, so the x230 has no host link.
- Row 6's T24032 and T12067 are UNBLOCKED; re-triage them before running.

## 5. OPEN questions

- **Member 4's 07:28 UTC unexpected reboot:** is it a new signature, or the fleet pattern?
  Evidence: `show reboot history` on u2 (member 4 section), read at the wrap.
- **Which copper-SFP / cage / host-NIC combinations need forcing?** Is the 09-09 "copper SFP facing
  a host NIC only links when forced" rule tied to a module lot, a cage or a NIC? Today's AT-SPTXc in
  3.0.10 linked on autoneg. See orient-dt §2 (2026-10-01 counter-observation).
- ~~Should the framework `run.stdout` files be kept?~~ **Resolved 2026-10-01:** Terrence said "delete the misc run files if the log is built". All five were deleted; the case logs are complete.

## 6. Ordered next steps

1. **Terrence:** remove the iptables FORWARD DROP rule. (`git push`: done, Terrence 2026-10-01.)
2. **Row 6, if wanted:**
   - T24032 and T12067 need a **second tb470 NIC on the stack**. Put a copper SFP in stack
     port3.0.9 (the spare AT-SPTXc is in SA port1.0.1), cable eth2 or eth3 to it, then run
     `bench_probe.py run` + `apply` (Terrence's). Re-triage with `/test-mode --resume`.
   - T45788 and T45789 are Terrence's to run by hand.
3. **Ask-CK side:** fix the not-applicable → `failed()` guard (defect 9) across the generated cases,
   and check the tear_down result (defect 10).
4. **Raise the product defects** (1–3, and 6 if it recurs) wherever Terrence files them.

## 7. Recipes

- **Resume a campaign in the one-session shape:** from the repo root, `/test-mode --resume
  [queue]` (§2–§5 of that skill). Arm the sentinel with `SELF=1` and your own transcript as
  `PEER_LOG`. On every Monitor expiry, sweep for strays first: `ps -eo pid,args >
  <scratch>/ps.snap`, grep it for the assembled pattern `"sentin""el.sh"`, kill those PIDs, then
  `rm <scratch>/sentinel.heartbeat` and re-arm.
- **Two-leg sa2 isolation for T33235-style cases (stack ↔ x230):**
  - Stack, on port1.0.2 and port1.0.9: shut, `no static-channel-group`, `switchport access vlan
    3998` or `3999`, then no shutdown.
  - x230, on port1.0.3 and port1.0.4: the same.
  - Restore: shut; stack `no switchport access vlan`, x230 `switchport access vlan 100`;
    `static-channel-group 2`; sa2 `switchport mode access` (x230 also `switchport access vlan
    100`); `no vlan 3998/3999`; no shutdown.
- **After any framework run with `--nodefaultcfg`,** on every device:
  - `boot config-file flash:/tb470-bench.cfg`.
  - `delete force flash:/<swi>_<suite>_<case>*.cfg` and `TestCase_tear_down.cfg`.
  - Then diff running-config against the pre-test capture and run the probe.

## 8. Pointers

- Queue / resume record: [CAMPAIGN-QUEUE-2026-09-29.md](CAMPAIGN-QUEUE-2026-09-29.md) (all rows DONE, SUPERSEDED or BLOCKED)
- Verdict rules: [../STANDING-ORDERS.md](../STANDING-ORDERS.md) §2
- Previous handovers: [SESSION-HANDOVER-2026-09-30.md](SESSION-HANDOVER-2026-09-30.md), [SESSION-HANDOVER-2026-09-29.md](SESSION-HANDOVER-2026-09-29.md)
- Sentinel kit: `.claude/skills/orient-dt/sentinel/` (orient-dt §10)
