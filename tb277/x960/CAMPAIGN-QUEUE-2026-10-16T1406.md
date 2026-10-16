# Campaign queue — tb277 x960-56YSQ, 10 AWPTCM cases, from 2026-10-16 14:06 NZDT

The ask (Test Engineer, 2026-10-16): *"I will be away so please do these test"*, with a
screenshot of ten AWPTCM cases for **x960-56YSQ** — four `IPv4_MulticastRouting`, three plain
`IPv4` helper features, one `IPv4_SNMP`, one `IPv4_BFD` and one `VRRP(v3)`.

⇒ **This campaign is exactly these ten.** Per the standing instruction of 2026-10-15 — *"the
list that I send you are the ones that you would be required to do. I won't send you the list of
test cases that have been manually done"* — there is **no reconciliation against any other
list**.

## 🔴 UNATTENDED RUN — no prompts, ever

The Test Engineer stated they are away. For this campaign only:

- **AskUserQuestion is not used at any point**, including the `/test-mode` §1 setup questions,
  a §3 FOUND, a §5 USER-CONFLICT, and the §5 "proceed with the N?" question.
- Every question that would have been asked is **recorded as a notice** in `## Issues` below,
  carried in the final report, and the campaign **proceeds with the runnable cases**.
- **This does NOT loosen STANDING-ORDERS §4.** Root on the box, `bench_probe.py apply`, a
  recable or destack, a licence, resolving a USER-CONFLICT, and displacing a console holder
  remain the Test Engineer's and are **never** done unattended. Working past one of those means
  running every case that does not depend on it, and marking the rest BLOCKED.
- This is a **user-driven** campaign, not `Driver: ask-ck`. `/create-logs` still waits for the
  Test Engineer; nothing is auto-logged.

**NOTICE (campaign) — the §1 setup questions were not asked.** The session facts below are taken
verbatim from `SESSION-HANDOVER-2026-10-16.md`, written at the wrap of the previous campaign
three hours earlier and confirmed by the Test Engineer when that campaign began. They are **not
re-confirmed**. If any has changed, the campaign is wrong about it and the queue says so here.

**NOTICE (campaign) — the §1.3 multi-hour / tmux question was not asked.** Ten cases including
multicast routing and reload-persistence limbs is a multi-hour run. In this one-session shape the
tester lives inside this session's process: if the process dies, the tester dies with it. This
file and the per-case commits survive, and `/test-mode --resume` picks up from the first row not
DONE / BLOCKED, so the loss would be the case in flight. **For a future unattended run, starting
inside `tmux` removes this risk.**

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom, continues from
the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state changes.

## Session facts

Recorded 2026-10-16 14:06 NZDT, carried verbatim from `SESSION-HANDOVER-2026-10-16.md`.

Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None (full authority within tests; power cycles allowed). Unattended — see above.

Devices, measured by `bench_probe.py` at **2026-10-15T200610Z** (`bench-setup/tb277/bench-state.md`,
Advisories: none) — the post-campaign probe taken at this morning's wrap:

- **DUT — swi_d, /dev/u2 @115200, AT-x960-56YSQ, S/N `A2WQS700B`**, standalone Active Master,
  software **`sin_x96056-20261012-24`**, bootloader `Unknown`, **boots FLASH**
  (`flash:/x960-tb277.rel`, file exists), boot config `flash:/default.cfg` (file exists).
- **partner — swi_b, /dev/u3 @9600, AT-x960-28YSQ**, S/N A10737A261700021,
  `sin_x96056-20260921-9`, boots `flash:/backup.rel`, hostname `x960-28YSQ`.
  **Base licence, read in full at triage 2026-10-16 14:15** — `10G_SFP+, AMF-GUEST, AMF-Starter,
  BASE-AW+, BGP-64, BW-UNLIMITED, CFM, EPSR-MASTER, G8032, IPv6Basic, L3-FORWARDING,
  **L3-MC-ROUTE**, LAG-FULL, MLDSnoop, MRP, No-License-Lock, OSPF-64, RADIUS-100, RIP, UDLD,
  UFO, VCStack, **VRRP**`. No VRF-Lite.
  🔴 **CORRECTION to this queue's first draft**, which said only "OSPF-64, RIP, no VRF-Lite":
  swi_b **does** hold `L3-MC-ROUTE` and `VRRP`, so it CAN be a real PIM neighbour (group C) and a
  real VRRP peer (group D). Its refusals at triage — `% BFD protocol daemon is not running`,
  `% VRRPD protocol daemon is not running or feature license is not available`, `% PIM-SM
  protocol daemon is not running or feature license is not available` — are the **daemon gate**,
  not a licence wall; the "or feature license" clause is a catch-all.
- **partner — swi_a, /dev/u5 @9600, AT-x950 GEN2-52XSTQm**, S/N A10713A262600012,
  `awplus_main-20261008-56`, **netboots**, boot image **Not set**,
  `flash:/default.cfg` **(file NOT found)** — RISK-1 below.

Links (measured, bench-state.md 2026-10-15T200610Z — all six inter-switch links are up again
after the previous campaign's restore):
```
tb eth3 (10.38.22.33/27) ── swi_d port1.0.10        swi_a 1.0.1  ── 1.0.1  swi_b
tb eth4 (10.38.22.65/27) ── swi_d port1.0.48        swi_a 1.0.11 ── 1.0.11 swi_b
tb eth2 (10.38.22.1/27)  ── (carrier up, unlearned) swi_a 1.0.4  ── 1.0.4  swi_d
                                                    swi_a 1.0.14 ── 1.0.14 swi_d
                                                    swi_b 1.0.2  ── 1.0.2  swi_d
                                                    swi_b 1.0.16 ── 1.0.16 swi_d
```

**🔴 Only TWO usable host NICs, and both land on the DUT.** `eth3` and `eth4` are the only
scapy-capable endpoints; `eth2` has carrier but nothing learned. There is **no host behind a
partner**. Every far-side count is therefore one of: a hairpin back through the DUT to the other
NIC, a per-port interface counter on the partner, or **the DUT's own `tcpdump` at privileged
exec** (see the techniques block). This shapes every multicast case in group C.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **`logged-output.md`**. Final logs are made only by `/create-logs`, on request.
- `STANDING-ORDERS.md` applies in full. Constraints are "None", so the tester has full authority
  within the tests, including power-cycling swi_d and swi_b (**not swi_a** — RISK-1).
- **🔥 STANDING-ORDERS §7: traffic tests use scapy, not ping.** For this list it is sharper than
  usual:
  - **Multicast (T43863/64/65/66) cannot be graded on `show ip mroute` or on a ping.** It needs a
    crafted group stream from one host NIC, a real IGMP join from the other, and a **counted**
    far-side result, with a control group that was never joined and must NOT arrive.
  - **PIM-SSM is defined by the (S,G) join.** An IGMPv3 include-source join is the subject; an
    IGMPv2 (*,G) join on an SSM range must be *rejected*, and proving that rejection is part of
    the case.
  - **Directed broadcast (T44182) and UDP broadcast helper (T44378)** are about *which* frames
    the DUT translates and forwards. Craft the exact destination (subnet broadcast, a helper
    UDP port) and send a control the rule must not match (a different UDP port, a different
    subnet).
  - **VRRP (T47873) is graded on which router answers for the virtual IP**, read from the ARP
    reply's source MAC (the VRRP virtual MAC `0000.5e00.01<vrid>`) and from the advertisement
    packets on the wire — not from `show vrrp`.
  - **BFD (T47201)** is graded on the measured failure-detection interval versus RIP's own
    timers, not on `show bfd peer` alone.
  - **Ping polling (T44181)** is the one case where `ping` is the subject; say so in the log.
- **Satisfactory level of testing** (Test Engineer, 2026-10-08): the step text is the FLOOR —
  also prove removal (gone from running-config AND from the dataplane) and persistence across a
  reboot; **baseline the feature OFF first**.
- **🔴 AW+ routing/service daemons are gated, but the gating set differs per protocol** (memory
  `awplus-service-gated-routing-daemons`, updated 2026-10-16 from this bench):
  - OSPF and RIP **are** gated; the start is **asynchronous**, so `service <proto>` and
    `router <proto>` must NOT share a console batch — send the service line alone, wait ~10 s.
  - **BGP is NOT gated** on this build. Do not assume; probe `service ?` first.
  - **PIM-SM is `service pim`, PIM-DM is `service pdm`, PIM6 is `service pim6`, BFD is
    `service bfd`** — on IE520. **Verify each on this x960 with a read-only `?` probe before
    concluding anything is UNSUPPORTED.**
  - `ip pim sparse-mode` additionally needs **`ip multicast-routing`** ("IP Multicast Routing
    not activated").
  - `no service <proto>` writes a **sticky config line** that configuration cannot remove; only
    a reload onto a config that never contained it clears it. Plan one reload at the end.
- Nothing is written to startup-config unless a case requires it.
- Teardown verified by diffing `show running-config` against the pre-case copy, **on every device
  the case touched**.
- Gate each dependent step on proven state, never on an exit code alone.
- **`python3.8` for every tool on tb277.** `tools/tb` is broken there (the box's `python3` is 3.6).
- **Captures:** `sudo tcpdump -w /tmp/...` on the box, then copy and `chown`. Never
  `tcpdump -Z $(whoami)` to the NFS lab home. **And confirm the capture process has EXITED before
  reading the file's size** — a size read while the buffer is unflushed reads 0 and nearly
  produced a false product finding on 2026-10-15 (memory `tcpdump-nfs-root-squash-capture`).
- **🔴 tb277 `/tmp` is 95% full** with 1.8 GB of someone else's `wireshark_eth4*.pcapng`, which is
  **not ours to delete**. Check free space before every capture; keep captures small and copy
  them off.

## 🔴 Case steps: expect them to be absent — ground them in the feature docs

Eleven of the previous nineteen cases on this bench had **no step text in AWPTCM or ck.db**, and
ck.db keys on `AWP-nnnn`, not `AWPTCM-T<id>` (memory `ckdb-case-lookup-by-title`) — join on
**title**, and read `summary` when `steps_text` is empty. Assume the same here. Where no
authority exists: design from the TFS, the product's TPS row and the DUT's own CLI surface
(read-only `?` probe), **say in the working log that no authored step text exists**, and grade on
what was actually exercised. Do not invent a quotation.

Feature Overview Guides live at `Feature Overview Guides/` in the repo root (gitignored). Read
the relevant guide **and** the TPS support matrix before drafting steps
(memory `review-feature-docs-before-testing`).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T43870 IPv4_SNMP - SNMPv3 | snmp-2026-10-16T1406 | **RUNNABLE** (triaged 14:24) | 🟢 Instrument confirmed: net-snmp 5.7.3 (`snmpwalk/snmpget/snmpset/snmptrap`, `snmptrapd`) + `python3-pysnmp4`, all on the box — **no helper needs writing**. `snmp-server view/group/user/host` all present on the DUT. **ck.db `zephyr_cases` holds a full 9-step authored procedure with exact OIDs** (see Triage result). DUT + host eth3 only. Cheapest and least topology-hungry: run it FIRST to prove the bench and the instrument before the expensive groups. SNMPv3 = USM users, auth/priv, engine ID, views. No SNMP helper exists in `tools/` — one will be needed (`snmpwalk`/`snmpget` on the box, or a scapy/pysnmp helper) |
| B | T44181 Ping Polling · T44378 UDP Broadcast Helper · T44182 Directed Broadcast Forwarding | ipv4svc-2026-10-16T1406 | **RUNNABLE** (triaged 14:24) | 🟢 `ping-poll <1-100>`, `ip forward-protocol udp`, `ip helper-address`, `ip directed-broadcast [acl]` all confirmed present. T44181 has **11 authored steps**; the other two have none (design from the IP Feature Overview Guide, which we hold). No partner and no STP work needed. DUT + BOTH host NICs; two L3 segments (eth3/vlan10, eth4/vlan48). **Builds the shared L3 underlay** that groups C and D then inherit (STANDING-ORDERS §6: set once per TestSet) |
| C | T43863 PIM-SM · T43864 PIM-DM · T43865 PIM-SSM · T43866 MulticastRouting VRF-Lite | mcast-2026-10-16T1406 | **RUNNABLE** (triaged 14:24) | 🟢 DUT holds `PIM/PIM-100/PIM-1024/PIM6` + `VRF-LITE-FULL`; `service pim`/`service pdm`/`service pim6` all exist; `ip multicast-routing [vrf]`, `ip pim ssm {default|range}`, `ip pim vrf`, `show ip mroute vrf` all present. **A TWO-ROUTER topology IS achievable** despite both NICs being on the DUT — trunk eth4's VLAN to the partner and give the partner the SVI (see Triage result). **FIRST ACTION: `service pim` on swi_b, alone, wait 10 s** — swi_b's Base licence lacks the `PIM` bit, so if it refuses, fall back to swi_a (has `PIM`, RISK-1 care) or single-router. **T43865 needs `tools/igmp.py` extended to IGMPv3** (SSM is defined by the (S,G) join; current tool is v2-only). Needs the NEW-RISK-8 STP remedy. Carry **F-9** into T43866. The big group. Needs `ip multicast-routing` + the PIM service gate, a source on one host NIC and a real IGMP receiver on the other. **Check the licence and the `service ?` surface for pim/pdm BEFORE grading anything UNSUPPORTED.** T43866 is multicast *inside a VRF* — different from the unicast VRF-Lite case already passed (T43859) |
| D | T47201 IPv4_BFD - With RIP v1/v2 · T47873 VRRP(v3) | bfd-vrrp-2026-10-16T1406 | **RUNNABLE** (triaged 14:24) | 🟠 **T47201 expect UNSUPPORTED, and that is the finding**: BFD is present and NOT licence-gated on all three units, but AW+ has **no RIP↔BFD binding** — `bfd all-interfaces` is OSPF-only, and the DUT's `ip rip ?` offers no `bfd`. Rule the service gate out, quote the refusals, and pair with a working `bfd peer` session so the verdict is "BFD works, no RIP binding". 🟢 **T47873 runnable**: `VRRP` is in swi_b's Base licence so it is a legitimate peer; `service vrrp` is the gate. AW+ has **no `version {2|3}` command** — grade v3 from the advertisement's version field on the wire; `transition-mode`/`alternate-checksum-mode` prove VRRPv3-for-IPv4 exists. Needs the NEW-RISK-8 STP remedy. Both need a partner and the shared underlay. BFD needs `service bfd` + RIP on both ends; swi_b has the `RIP` licence. VRRP(v3) needs DUT and swi_b on one shared VLAN with a host as the client, and is graded on the virtual MAC on the wire |

**Group order is deliberate.** A is a single cheap case that proves console, instrument and
bench before anything expensive. B builds the **one** L3 underlay; C and D inherit it and layer
only their own protocol, removing it in their own teardown. That keeps three groups from
rebuilding the same addressing three times — the pattern that worked on 2026-10-15.

**🟢 Triage RAN 2026-10-16 14:09–14:24 NZDT — see `## Triage result` at the end of this file.**
**10 runnable / 0 blocked by topology / 0 blocked otherwise.** Nothing needs a recable, a
destack, a licence or a Test Engineer decision. Two caveats, both resolved inside their own
group: **NEW-RISK-8** (the DUT is not the STP root and both swi_a legs are Discarding — remedy in
the Triage result) and the **group-C partner probe** (`service pim` on swi_b, ~2 minutes).

## Known risks, carried from the previous campaign on this bench

- **🔴 RISK-1: swi_a must NOT be reloaded or power-cycled.** `Current boot image: Not set`,
  `flash:/default.cfg` **not found**, autoboot disabled; it runs `x950GEN2-tb277.rel` from a
  netboot and would not come back. Config changes only. ⇒ Prefer **swi_b** as the partner for
  every case that needs one.
- **🔴 RISK-2: swi_b carries pre-existing config on a DUT link.** `vlan 100`, `port1.0.2` and
  `port1.0.4` in `static-channel-group 1`, `port1.0.8` in vlan 100, `interface sa1`, `eth0
  169.254.42.42/16`. **`port1.0.2` is one of the two swi_b↔swi_d links.** ⇒ Use swi_b
  **`port1.0.16`** (clean both ends) and leave `sa1` alone; diff swi_b at every teardown.
- **🔴 RISK-3: single-instance RSTP on all three devices.** It computes ONE tree over the
  physical topology, so a Discarding port is blocked for **every** VLAN and "a VLAN per leg"
  unblocks nothing. Two parallel links between the same bridge pair can never both forward.
  The previous campaign's remedy: `spanning-tree priority 0` on the DUT plus `shutdown` on
  `port1.0.2` and `port1.0.14`. Confirm `show spanning-tree brief` **before** measuring, never
  after. (`platforms/x960.md` §7.10)
- **RISK-4: `lacp global-passive-mode enable` is set on all three.** A port freed from an
  aggregator can auto-enrol and then forwards where STP cannot block. After any port change
  check `show static-channel-group` and `show etherchannel summary` on all three.
- **🔴 RISK-5: swi_b's clock ran ~13 h ahead of the DUT's** while both labelled themselves UTC.
  The previous campaign corrected swi_a and left swi_b near the box. **Re-read all three clocks
  at group setup and state the offsets in every working log** — correlating a BFD failure, a
  VRRP transition or a PIM join across devices with uncorrected clocks silently gives a wrong
  answer.
- **RISK-6: no `.setup` on tb277 ⇒ no framework.** All ten cases are manual, and there is no
  framework post-failure PDU cycle; each case's own teardown is the only restore.
- **RISK-7: `tools/tb` does not work on tb277** (box `python3` is 3.6). Everything runs as
  `python3.8`. **One driver process per device, never two at once on the same `/dev/uN`** — two
  readers give `device reports readiness to read but returned no data`, which reads exactly like
  a dead unit.

## Techniques proven on this bench — use them, do not rediscover them

- **The DUT's own `tcpdump` at privileged exec** is the instrument for anything that never
  reaches a host NIC (a routed-only segment, a control-plane protocol between two router
  addresses). `awplus# tcpdump -i vlan61 -c 20 -nn -v tcp port 179`. BPF note: `greater N` counts
  the 14-byte Ethernet header.
- **An instrument control in EVERY counted leg** — a flow that must arrive, usually to the DUT's
  own address — so a zero is a measurement and not a dead instrument. This caught two instrument
  faults and one false finding on 2026-10-15.
- **`tools/` already has** `mkmc.py` (multicast pcaps), `igmp.py`, `arpleg.py` (counted legs with
  `--icmp`), `vsend.py`/`vcount.py`, `linerate.py`, `ckcon.py`/`cfg.py` (console drivers),
  `ckreload.py`, `rcdiff.py`, `poll.py`. **Look there before writing anything**; a new helper is
  generic, goes in `tools/` with its `README.md` entry, and is never left in a case's `work/`.
- **Tool traps:** `cfg.py` stops at the first `% ` line and abandons the rest of its batch;
  `rcdiff.py` prints differences but **exits 0** — gate on output, never on the exit code.
- **Reboot-persistence without touching startup-config:** stage a named boot config
  (`copy running-config flash:/ck<ID>.cfg`, `boot config-file flash:/ck<ID>.cfg`), reload,
  re-measure, then put the pointer back and `delete` the file — the `delete` prompts `(y/n)[n]`
  and **aborts if unanswered**.
- **Re-read STP after every reboot, before measuring.** A port reads Designated *Discarding* for
  ~17-21 s after `login:` and Forwarding ~15 s later. A leg measured in that window reads as a
  feature failure.

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |

## Issues

- **NOTICE (campaign) — session facts not re-confirmed.** See the UNATTENDED block above.
- **NOTICE (campaign) — the multi-hour / tmux question was not asked.** See above.
- **NOTICE (campaign) — the §3 occupancy check returned FOUND (exit 5) and was NOT escalated.**
  Run 2026-10-16 14:09 NZDT. **All three of this session's consoles are free** (u2/ttyUSB2,
  u3/ttyUSB3, u5/ttyUSB5). The two FOUND items are outside this session's console list and
  neither is touched:
  - `process 744 (root, up 35-02:54:05): /usr/sbin/ser2net` — the box's own serial daemon,
    infrastructure, not a holder of any of our consoles;
  - **`process 10790 (root for bidhanc, up 03:18:05): minicom -D /dev/ttyUSB1`** — a minicom on
    **u1**, which this session does not use. It is the Test Engineer's own session, left open.
    **Not displaced, not touched.**
  `/test-mode` §3 would normally stop and hand this back; under the unattended rule it is a
  notice and the campaign proceeds. **If u1 was meant to be part of this campaign, say so and it
  will be re-triaged** — nothing has been run against it.
- **🔴 CARRIED, STILL OPEN FOR THE TEST ENGINEER** (none blocked a case on 2026-10-15, and none
  is expected to block one here):
  - an unrecorded device `10.38.22.41` / `00:0c:25:2a:a5:53` is live on the box's eth3 segment,
    present since at least 2026-10-09; it is **on the segment every host-NIC case uses**, so
    match counts on both MACs and say so in the log;
  - swi_d `port1.0.8` and `port1.0.40` up and Forwarding with no LLDP neighbour, absent from
    bench-state.md's link table;
  - tb277 `/tmp` 95% full with 1.8 GB of someone else's captures — **not ours to delete**;
  - `arp <ip> <mac> alias` installs but never answers (T33248, UNMEASURED);
  - **F-9**: a removed inter-VRF static route leaves the dataplane forwarding across the VRF
    boundary until the VRF's ARP cache is cleared. **T43866 is multicast VRF-Lite and runs on the
    same mechanism — watch for it there.**
  - **F-7**: `show running-config` disagrees with the saved file and the wire about
    `bgp graceful-restart`.

## Triage result

Run 2026-10-16 14:09–14:24 NZDT (box UTC 01:09–01:24) by the `bench-runner` tester in **TRIAGE
mode**: read-only apart from `bench_probe.py run`. **No device state was changed.** Every
`configure terminal` entry below was a `tools/qmark.py` read-only `?` probe (no CR, Ctrl-U
line-kill, self-test passed) and was left with `end` → `terminal no monitor` → exec, verified
from the transcripts `/tmp/ckt1406/console-u{2,3,5}.log`.

### Headline: 10 runnable / 0 blocked by topology / 0 blocked otherwise

Nothing needs a recable, a destack, a licence or a Test Engineer decision. Two caveats ride
along and both are resolved inside the first few minutes of their group (NEW-RISK-8 and the
group-C partner probe, below).

### Gate results

| gate | result |
| --- | --- |
| §3 occupancy, `precheck --consoles u2,u3,u5` | **u2, u3, u5 all free.** FOUND (exit 5) = the same 2 items as 14:09, neither ours and neither touched: `ser2net` (pid 744, box infrastructure) and `minicom -D /dev/ttyUSB1` (pid 10790, the Test Engineer's own session on **u1**) |
| probe `run --consoles u2,u3,u5 --pdu 10.36.230.212 --outlet u2=1,u3=7` | **exit 0.** `no template at tb277.setup.current -- diff skipped`, as expected. **Advisories: none.** Capture `2026-10-16T011135Z`; all six inter-switch links and both host-NIC links re-measured unchanged |
| swi_a outlet | recorded, not exercised: **10.36.230.35 outlet 3**. Never power-cycled (RISK-1) |
| consoles left | all three at exec, `terminal no monitor`, closed cleanly |

### Device baseline measured at triage

- **DUT (swi_d, u2) is at a clean baseline**: `show ip interface brief` = `eth0/lo/vlan1 all
  unassigned`; one VLAN (`vlan1`, every port untagged); `show vrf` → `% Invalid input` (the
  command is `show ip vrf`; no VRFs configured). The previous campaign's restore was complete.
- **🟢 RISK-5 is RESOLVED.** All three clocks are UTC and agree with the box within ~7 s:
  box `01:23:06`, swi_b `01:23:08`, swi_a `01:23:20`, DUT `01:17:13` vs box `01:17:18`.
  **swi_b's ~13 h offset is gone.** Re-read at each group setup anyway, but do not budget for it.
- Host NICs: `eth2 10.38.22.1/27`, `eth3 10.38.22.33/27` (`00:0d:b9:55:77:0e`),
  `eth4 10.38.22.65/27` (`00:0d:b9:55:77:0f`), all UP. Record once per group (§"Keep the context small").
- tb277 `/tmp`: **108 MB free of 2.0 GB** — still 95% full with the other user's captures. Scratch
  for this campaign is `/tmp/ckt1406/` (456 KB).

### 🔴 NEW-RISK-8 — the DUT is NOT the root bridge, and BOTH swi_a links are Discarding

Not covered by the queue's RISK list, and it blocks every case that needs a partner.
`show spanning-tree brief` on the DUT, 14:17:

```
Root Id 8000:0000cd423029      Bridge Id 8000:e01aead47043   Root Port 5002
port1.0.2    Rootport     Forwarding   <- to swi_b
port1.0.16   Alternate    Discarding   <- to swi_b  (the RISK-2-clean link)
port1.0.4    Alternate    Discarding   <- to swi_a
port1.0.14   Alternate    Discarding   <- to swi_a
port1.0.10   Designated   Forwarding   <- host eth3
port1.0.48   Designated   Forwarding   <- host eth4
port1.0.8, port1.0.40  Designated Forwarding, no LLDP neighbour  (the carried open issue, still present)
```

⇒ **Right now there is no forwarding path at all between the DUT and swi_a**, and the only live
DUT↔partner path is `port1.0.2`, the one RISK-2 says to avoid.

**Remedy (within a test, §7.10 of `platforms/x960.md`), for every group that uses a partner:**
1. On the DUT: `spanning-tree priority 0` — the DUT becomes root and all its ports go Designated
   Forwarding; the blocking moves onto the partners' spare ports.
2. On the DUT: `shutdown` `port1.0.14` (redundant swi_a leg) and `port1.0.2` (the RISK-2 swi_b
   leg), forcing the partners' root-port choice onto `port1.0.4` (swi_a) and `port1.0.16` (swi_b)
   instead of a bridge-ID tie-break.
3. **Confirm with `show spanning-tree brief` BEFORE measuring**, and allow the settle the queue's
   technique block gives (Discarding for ~17–21 s, Forwarding ~15 s later).
Groups A and B need none of this — both host NICs are already Forwarding on the DUT.

### Feature presence, measured per device

`show license`, 14:12–14:16:

| | DUT swi_d (u2) | swi_b (u3) | swi_a (u5) |
| --- | --- | --- | --- |
| licences | Base + **`atlnz` (ATL-NZ internal)** | **Base only** | Base + **`full` (ATL-NZ internal)** |
| `PIM`, `PIM-100`, `PIM-1024`, `PIM6` | **YES** (atlnz) | **NO** | **YES** (full) |
| `VRRP` | YES (Base) | **YES (Base)** | YES (Base) |
| `RIP` | YES (Base) | **YES (Base)** | YES (Base) |
| `L3-MC-ROUTE` | YES (Base) | YES (Base) | YES (Base) |
| `VRF-LITE-FULL/63/8` | **YES** (atlnz) | **NO** | YES (full) |
| BFD | no feature bit exists — service-gated only | same | same |

**The service gate, read with a read-only `?` in config mode on the DUT** — the full list is
`advanced-vty, atmf-application-proxy, bfd, bgp, cloud-client, dcbx, dhcp-relay, dhcp-server,
dhcp-snooping, epsr, http, isis, linkmon, mlag, mrp, netconf, onm, openflow, ospf, ospf6, pdm,
pfc, pim, pim6, power-inline, rip, ripng, snmp-discovery, ssh, statistics, stoat, telnet,
terminal-length, test, vrrp, wireless`.
⇒ The IE520 gating set carries over and extends: **`service pim` (PIM-SM), `service pdm`
(PIM-DM), `service pim6`, `service bfd`, and also `service vrrp`** — VRRP is service-gated on
this platform too, which is why `show vrrp` refused on all three units.

**Baseline refusals before any service was started** (all three units, so they are the gate, not
a fault): `% PIM-SM protocol daemon is not running or feature license is not available`,
`% VRRPD protocol daemon is not running or feature license is not available`, and on swi_b/swi_a
`% BFD protocol daemon is not running` — note the BFD message carries **no licence clause**,
confirming BFD is service-gated only. `show ip pim sparse-mode interface` "after" was not taken:
`service pim` is a device-state change and TRIAGE changes none.

⚠️ `show bfd session` is **not** a command — it answers `% Invalid input detected`. The verb is
**`show bfd peer`** (also `show bfd peer brief`, `show bfd peer <addr> counters`, `show bfd vrf`).

**CLI surface confirmed present on the DUT** (read-only `?`): `ip multicast-routing
[border|ssm-only-hw|vrf]`; `ip pim rp-address|ssm {default|range}|bsr-candidate|rp-candidate|
spt-threshold|register-*|vrf` (global) and `ip pim sparse-mode|dense-mode|dr-priority|
hello-interval|neighbor-filter|state-refresh` (interface); `show ip pim {sparse-mode|dense-mode|
vrf}`; `show ip mroute [sparse|dense|static|count|summary|vrf]`; `router vrrp <1-255>`;
`ping-poll <1-100>`; `ip forward-protocol udp`; `ip helper-address A.B.C.D`;
`ip directed-broadcast [<1-99>|<1300-1999>|WORD]` (optional standard ACL);
`ip igmp version <1-3>` (default 3); `snmp-server view|group|host|user`.

### 🟢 Answer to the campaign's single most important triage question: YES, this bench can test multicast — and with TWO routers

The queue reasoned that because both usable host NICs land on the DUT there is "no host behind a
partner". **That does not force a single-router test.** A host NIC's *physical* port and its
*routing* router are independent:

> Put the DUT port that carries `eth4` (`port1.0.48`) into a VLAN for which **the DUT has no
> SVI**, and trunk that VLAN over the DUT↔partner link. The **partner** owns the SVI. `eth4` is
> then logically a host **behind the partner**, while still being cabled to the DUT.

That yields the authored topology of T43864 (`IXIA -- DUT -- sw1(running PIM-DM) -- IXIA`), with
the two host NICs standing in for the two IXIA ports:

```
host eth3 ──(DUT port1.0.10, vlan S, SVI on DUT)── DUT ══ transit vlan T (SVIs both ends, PIM adjacency) ══ partner
                                                    ╚═ vlan R trunked, NO SVI on DUT ═╝        SVI for vlan R
host eth4 ──(DUT port1.0.48, vlan R access) ────────────────────────────────────────────────────┘
```
Source = scapy on `eth3`; receiver = IGMP join + counted capture on `eth4`; the DUT is the
upstream PIM router and the partner is the downstream one, so Hello, Join/Prune, Register and
DR election all cross a real wire and are capturable.

**Which partner.**
- **swi_a is the only unit PROVEN to hold the `PIM` bit** (its `full` ATL-NZ licence lists
  `PIM, PIM-100, PIM-1024, PIM6`). swi_b's Base licence does **not** list `PIM`.
- 🔴 **The queue's current Session-facts note is an inference, not a measurement.** It says swi_b
  "CAN be a real PIM neighbour" because it holds `L3-MC-ROUTE`. `L3-MC-ROUTE` is held by all
  three units including those whose PIM comes from a separate `PIM` bit, so it is not the PIM
  gate; and `platforms/x960.md` §7A.1 warns the "or feature license" half of the refusal is a red
  herring **in both directions** — it cannot confirm a licence either. This was not settled at
  triage because settling it needs `service pim`, a device-state change.
- ⇒ **First action of group C (about 2 minutes):** on swi_b send `service pim` **alone**, wait
  ~10 s (§7A.1: the start is asynchronous and `service`/`router` must not share a batch), then
  `show ip pim sparse-mode interface`. Daemon up ⇒ use **swi_b on `port1.0.16`** (rebootable via
  PDU outlet 7, clean both ends per RISK-2). Refused for licence ⇒ fall back to swi_a.
- **swi_a as the PIM partner is permitted but handle under RISK-1.** Config-only changes are
  fine, and §7A.2's sticky `no service` line does **not** apply to it: that residue appears only
  on a unit that **booted** with the service, and swi_a netbooted with no config file — so its
  teardown comes back clean and needs no reload. The hazard is only that swi_a must never be
  reloaded, so if PIM destabilises it, it will not come back. Prefer swi_b.
- **Fallback if neither partner runs PIM:** single-router PIM with the DUT as its own static RP
  (`ip pim rp-address <DUT loopback>`), source on `eth3`, IGMP receiver on `eth4`. This still
  measures mroute creation, IGMP→OIF, dataplane forwarding, prune-on-leave and SSM (S,G). It
  cannot measure neighbour adjacency, Register/Register-Stop, Join/Prune on the wire, Assert or
  DR election — those limbs become NOT MEASURABLE and the ceiling for an inter-router subject
  drops to PARTIAL. Say which topology was used in every multicast working log.

### 🟢 Case step text EXISTS — and the `ckdb-case-lookup-by-title` memory is WRONG

The memory says AWPTCM numbers "do NOT exist in ck.db" and to join on title. **That is out of
date.** ck.db has a **`zephyr_cases`** table (45,427 rows) keyed on exactly `AWPTCM-T<id>`:
`key, title, folder, objective, precondition, steps, steps_text, num_steps, labels, status`.
All ten cases were found instantly by key. Nine sit in
`/New Platform Test (MASTER)/New Platform Template/IPv4`; T47873 sits in
`/5.5.6-0/Singularity/x950 Gen2`. All ten are status **Draft**.

| case | authored content in `zephyr_cases` |
| --- | --- |
| **T43870 SNMPv3** | 🟢 **the best-defined of the ten** — no `steps_text`, but `precondition` carries the **full config block and a 9-step procedure in Japanese and English**, with exact OIDs. Objective: *verify `snmp-server view` filtering under SNMPv3*. Steps: get `1.3.6.1.2.1.1.5` (sysName) → must succeed; get `1.3.6.1.2.1.2.1` (ifNumber) → must fail; add that OID as `exclude`; re-get → must fail; get another `1.3.6.1.2.1.1.x` → must succeed. Config given verbatim incl. `snmp-server view system 1.3.6.1.2.1.1 included`, a `priv` group, an `auth md5` + `priv des` user and `interface vlan1 / ip address 192.168.1.1/24`, manager at `192.168.1.100` |
| **T44181 Ping Polling** | 🟢 **11 steps**, full `ping-poll` + trigger + script recipe, every sub-command named (`ip`, `active`, `length`, `timeout`, `normal-interval`, `critical-interval`, `sample-size`, `fail-count`, `up-count`, `show ping-poll`, `show counter ping-poll`, `clear ping-poll`, `debug ping-poll`, `type ping-poll <1-100> {up\|down}`) |
| **T43865 PIM-SSM** | 🟢 **3 steps**: forwarding + table state on join; prune + table state on leave; state on interface down/up. Names the read-backs (`show ip mroute`, `show ip pim sparse-mode mroute`, `show ip igmp group`) |
| **T43864 PIM-DM** | 🟢 objective + **topology precondition `IXIA -- DUT -- sw1(running PIM-DM) -- IXIA`** + "Setup a PIM-DM network / Multicast client able to get multicast stream" |
| **T47873 VRRP(v3)** | 🟢 short but real: *"configure a basic VRRP and ensure end device(s) can be reached when either the master or the backup router loses connection… Role transitioning works correctly"*, + a link to the public VRRP Feature Overview Guide |
| T44378, T44182, T43863, T43866, T47201 | ⚪ **no objective, no precondition, no steps** (`num_steps` 1, `steps_text` empty). Design from the guides + the DUT's CLI surface and **say so in the working log** |

⇒ **5 of 10 have usable authored text** — the queue's "expect them to be absent" is too
pessimistic. Read `zephyr_cases` by key before drafting any case.

### Docs available, and a gap

`Feature Overview Guides/` holds **8** guides: ACL, DHCP, **IP Addressing and Protocols**,
Mirroring, OSPF, **RIP**, Route Selection, **VRF-lite**. The IP guide covers group B's three
subjects (ping polling, UDP broadcast helper, directed broadcast) and RIP + VRF-lite cover group
D's and T43866's halves. **There is no SNMP, multicast/PIM, BFD or VRRP guide locally** — for
those use (a) ck.db's `cli_commands` table, which carries per-command `Overview / Mode / Default
/ Usage notes / Related commands / Command changes` and was the decisive source for the two
findings below, and (b) the lab wiki, reachable from tb277 (memory
`lab-wiki-reachable-from-a-testbox`). T47873 links the public VRRP FOG itself.

⚠️ **The `cli_commands` corpus has NO x960 pages.** Its product list is `x950, x950gen2, x930,
x980, x908gen2, x908gen3` (plus the AR/IE/GS families) — the same trap as the IE520
(`awplus-cli-wiki-on-the-share`). Treat it as family-general and **confirm every command on the
DUT**. swi_a, an x950 Gen2, *is* covered. No product TPS was found in the repo; the support
matrix a TPS would give was substituted by `show license` + the `?` probes above.

### Per-case verdict

**All 10 runnable.** In queue order:

| # | case | needs | this bench provides it? |
| --- | --- | --- | --- |
| A | **T43870 SNMPv3** | DUT + an SNMP manager on `eth3`; `snmp-server view/group/user/host`; an SNMPv3 USM client doing `auth md5` + `priv des` | 🟢 **YES, and it is the cleanest case of the ten.** CLI all present. Instrument fully installed on the box: net-snmp **5.7.3** — `/usr/bin/snmpwalk`, `snmpget`, `snmpset`, `snmptrap`, plus `snmptrapd`, `snmp-mibs-downloader` and `python3-pysnmp4` (imports under `python3.8`). No partner, no STP work, no service gate. Authored 9-step procedure. **Run it first exactly as the queue plans.** Note the case's literal passwords contain shell metacharacters (`!#$%&'()*+,-./[\]^_\`` and `:;<=@{}~0123456789ab`) — quote them carefully and treat them as the one case where exact secrets go down the console (the case *is* that test) |
| B | **T44181 Ping Polling** | `ping-poll` + triggers + scripts; a pollable host that can be made unreachable | 🟢 YES. `ping-poll <1-100>` present; 11 authored steps. Poll the box's `eth3` address and drive unreachability by stopping the responder or shutting `port1.0.10`. This is the one case where `ping` IS the subject (queue rule) — say so in the log. The trigger/script limb writes a small script to the DUT's flash: within a test, delete it at teardown (the `delete` prompt is `(y/n)[n]` and **aborts if unanswered**) |
| B | **T44378 UDP Broadcast Helper** | two L3 segments on the DUT; `ip forward-protocol udp <port>` + `ip helper-address` | 🟢 YES, DUT + both host NICs, no partner. No authored steps — design from the IP guide. Grade on the wire: a crafted UDP broadcast on a helped port must be relayed to the helper address, and a **control on a non-helped port must not be** |
| B | **T44182 Directed Broadcast Forwarding** | two L3 segments; `ip directed-broadcast` on the egress SVI | 🟢 YES, DUT + both NICs. The optional standard-ACL form (`<1-99>`/`<1300-1999>`/`WORD`) gives a free second limb: permitted source forwarded, denied source dropped. Baseline OFF first — the default is no directed broadcast |
| C | **T43863 PIM-SM** | `service pim`, `ip multicast-routing`, an RP, a source and an IGMP receiver | 🟢 YES. Two-router per the design above (partner probe first), else single-router with the DUT as its own static RP. `ip pim rp-address` and `ip pim rp-candidate`/`bsr-candidate` all present |
| C | **T43864 PIM-DM** | `service pdm`; flood-and-prune | 🟢 YES. `service pdm` exists and `ip pim dense-mode` is an interface command. Its authored precondition explicitly wants a second PIM router, so run it on the two-router topology if the partner probe succeeds |
| C | **T43865 PIM-SSM** | `ip pim ssm {default\|range}` + an **IGMPv3 include-source** join | 🟡 YES, **but it needs a tool extension.** `ip pim ssm default` (232/8) and `ip pim ssm range <acl>` are both present and `ip igmp version <1-3>` defaults to 3. **`tools/igmp.py` is IGMPv2-only** — PIM-SSM is *defined* by the (S,G) join, so the group needs an IGMPv3 membership report with an `ALLOW_NEW_SOURCES`/`MODE_IS_INCLUDE` record. scapy 2.4.4 on the box has `scapy.contrib.igmpv3` (`IGMPv3`, `IGMPv3mr`, `IGMPv3gr`), so this is ~30 lines. **Extend `tools/igmp.py` with a `v3` mode and add its `tools/README.md` entry** — generic, not a case-local script. The authored steps also want the IGMPv2-(*,G)-on-an-SSM-range rejection limb, which the existing v2 path already covers |
| C | **T43866 Multicast VRF-Lite** | `ip multicast-routing vrf`, `ip pim vrf`, `show ip mroute vrf`; the `VRF-LITE` licence | 🟢 YES on the DUT (`VRF-LITE-FULL/63/8` from `atlnz`; all three `vrf` keywords confirmed present by `?`). No authored steps. 🔴 **Carry F-9 into this case**: a removed inter-VRF static route kept forwarding until the VRF's ARP cache was cleared — the same mechanism, so check it explicitly. Note swi_b has **no** VRF-Lite licence, so any second-router limb must use swi_a (RISK-1) or stay DUT-local |
| D | **T47201 BFD with RIP v1/v2** | `service bfd` + `service rip` both ends, and a **RIP↔BFD binding** | 🟠 **Runnable, but expect UNSUPPORTED — and that is the finding.** BFD itself is fully present on all three units (`service bfd`, `bfd profile`, `bfd peer`, `show bfd peer`) and is **not** licence-gated. **But AlliedWare Plus appears to have no RIP↔BFD binding at all.** Every BFD integration point in the CLI reference is OSPF, BGP or static: `ip ospf bfd`, `area … virtual-link fall-over bfd`, `neighbor <id> fall-over bfd` (BGP), `ip route bfd` / `ip route bfd all-interfaces`. **`bfd all-interfaces` is OSPF-only** — its Overview reads *"enable BFD fall-over detection on all interfaces **under an OSPF process**"*, Mode `Router Configuration`. And the DUT's own interface-mode `ip rip ?` offers only `authentication, receive, receive-packet, send, send-packet, split-horizon` — **no `bfd`**; interface-mode `bfd ?` answers `% Unrecognized command`. **Procedure:** rule the service gate out first (`service bfd`, then separately `service rip`, ~10 s apart per §7A.1), then probe `router rip` mode and interface mode with `qmark.py` and **quote the refusals** (STANDING-ORDERS §1). Pair it with a positive control that keeps the case valuable: bring a real BFD session up between the DUT and swi_b with `bfd peer` / `ip route bfd` and show BFD works, so the verdict is precisely *"BFD present and functional; no RIP binding exists on this platform"* and not *"BFD missing"* |
| D | **T47873 VRRP(v3)** | `service vrrp` on two routers sharing one VLAN, plus a host client | 🟢 YES. **swi_b is a legitimate peer — `VRRP` is in its Base licence**, so no licence question. Segment: one VLAN over DUT `port1.0.16` ↔ swi_b `port1.0.16` (RISK-2-clean) with host `eth3` on DUT `port1.0.10` in the same VLAN as the client. Needs the NEW-RISK-8 STP remedy. **On "v3": AW+ has NO `version {2\|3}` command.** The VRRP command set is `router vrrp <vrid> <if>` (IPv4), `router ipv6 vrrp` (VRRPv3 for IPv6), plus `priority`, `virtual-ip`, `preempt-mode`, `advertisement-interval [csec]`, `circuit-failover`, `accept-mode`, `enable/disable`, `vrrp vmac`. VRRPv3-for-IPv4 is nevertheless supported, proven by two commands that exist only for it: **`transition-mode {true\|false}`** — *"allows you to upgrade from VRRPv2 to VRRPv3 and gives interoperability between VRRPv2 and VRRPv3"* — and **`alternate-checksum-mode`** — *"the IPv4 checksum for VRRPv3 advertisements will then use a pseudo header"*. ⇒ **Grade "v3" from the wire**: capture the advertisement and read its **version field = 3**, plus the virtual MAC `0000.5e00.01<vrid>` in the ARP reply for the virtual IP, exactly as the queue demands; then set `transition-mode true` and show v2 advertisements appear alongside. Failover by `priority` change or by shutting the master's VRRP interface, graded on which MAC answers |

### Notices for the Test Engineer (none blocks a case)

- **NEEDS TEST ENGINEER (informational, carried):** the §3 occupancy check is still FOUND (exit 5)
  because of `ser2net` and the **minicom on u1**. Our three consoles are free and u1 was not
  touched. **If u1 was meant to be part of this campaign, say so and group C gains a third
  partner** — nothing has been run against it.
- **Memory correction to make at wrap:** `ckdb-case-lookup-by-title` should record the
  **`zephyr_cases` table keyed on `AWPTCM-T<id>`** as the first lookup, with `testlink_cases`
  (join on title) as the fallback for `AWP-nnnn` material. The current memory sends a reader down
  the title-join path unnecessarily and states the AWPTCM ids are absent, which is false.
- **New platform facts earned at triage**, for `platforms/x960.md` at wrap: `service vrrp` exists
  (VRRP is service-gated); the full 36-entry `service` list; `show bfd session` is invalid and the
  verb is `show bfd peer`; BFD has no RIP binding (OSPF/BGP/static only); VRRP has no `version`
  command but `transition-mode`/`alternate-checksum-mode` prove VRRPv3-for-IPv4; the DUT is not
  the STP root at baseline and both swi_a legs are Discarding.
