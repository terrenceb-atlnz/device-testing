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
  **Base licence: `OSPF-64`, `RIP`, no VRF-Lite.** Check its licence before planning any case
  that needs a feature on the partner side.
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
| A | T43870 IPv4_SNMP - SNMPv3 | snmp-2026-10-16T1406 | PENDING TRIAGE | DUT + host eth3 only. Cheapest and least topology-hungry: run it FIRST to prove the bench and the instrument before the expensive groups. SNMPv3 = USM users, auth/priv, engine ID, views. No SNMP helper exists in `tools/` — one will be needed (`snmpwalk`/`snmpget` on the box, or a scapy/pysnmp helper) |
| B | T44181 Ping Polling · T44378 UDP Broadcast Helper · T44182 Directed Broadcast Forwarding | ipv4svc-2026-10-16T1406 | PENDING TRIAGE | DUT + BOTH host NICs; two L3 segments (eth3/vlan10, eth4/vlan48). **Builds the shared L3 underlay** that groups C and D then inherit (STANDING-ORDERS §6: set once per TestSet) |
| C | T43863 PIM-SM · T43864 PIM-DM · T43865 PIM-SSM · T43866 MulticastRouting VRF-Lite | mcast-2026-10-16T1406 | PENDING TRIAGE | The big group. Needs `ip multicast-routing` + the PIM service gate, a source on one host NIC and a real IGMP receiver on the other. **Check the licence and the `service ?` surface for pim/pdm BEFORE grading anything UNSUPPORTED.** T43866 is multicast *inside a VRF* — different from the unicast VRF-Lite case already passed (T43859) |
| D | T47201 IPv4_BFD - With RIP v1/v2 · T47873 VRRP(v3) | bfd-vrrp-2026-10-16T1406 | PENDING TRIAGE | Both need a partner and the shared underlay. BFD needs `service bfd` + RIP on both ends; swi_b has the `RIP` licence. VRRP(v3) needs DUT and swi_b on one shared VLAN with a host as the client, and is graded on the virtual MAC on the wire |

**Group order is deliberate.** A is a single cheap case that proves console, instrument and
bench before anything expensive. B builds the **one** L3 underlay; C and D inherit it and layer
only their own protocol, removing it in their own teardown. That keeps three groups from
rebuilding the same addressing three times — the pattern that worked on 2026-10-15.

**Triage has NOT run yet.** The tester triages all ten rows against the bench before anything is
configured, and the result is recorded here. Under the unattended rule the campaign then proceeds
with the runnable cases automatically instead of asking.

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
