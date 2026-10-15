---
name: tb277-x960-dhcp-campaign-2026-10-15
description: "6 AWPTCM DHCP cases on the x960-56YSQ, all PASS; five had no step text so each test was designed from the TFS + TPS + the DUT's own CLI surface; the one open item (the DNS forwarding cache) needs a developer, not a bench"
metadata:
  node_type: memory
  type: project
---

2026-10-15 on tb277, DUT **AT-x960-56YSQ S/N `A2WQS700B`**, build `sin_x96056-20261012-24`,
flash-booting. Six cases, **6 PASS / 0 FAIL**, final logs created
(`tb277/x960/dhcp-*-2026-10-15T1458/`), handover `tb277/x960/SESSION-HANDOVER-2026-10-15.md`.

T43851 ARP Probe · T43853 120-day lease · T43852 DHCP Relay · T43850 Option 82 ·
T35370 Extended ID · T43854 DNS Relay.

**What makes this campaign worth remembering is not the verdicts.**

1. **Five of six cases had no step text in AWPTCM or ck.db**, and T35370 had no functional spec
   for its title at all. Each test was designed from the TFS, the TPS row and — for T35370 — the
   DUT's own CLI surface enumerated by read-only help probe *before* the steps were drafted, then
   graded on all of it rather than on a guess at what the title meant. That is the pattern to
   repeat when a case id resolves to nothing: widen to the measurable surface, and say in the log
   that no authority exists.
2. **Every finding was an observation, none a defect.** The eight product observations are in
   **`platforms/x960.md` §6** — read that before the next x960 DHCP work. The ones that would
   otherwise produce a wrong verdict: a relayed DHCP frame is invisible to scapy without
   `bind_layers(UDP, BOOTP, dport=67/68)`; `agent-option checking` is a **response**-side check;
   `probe type ping` ARPs first so ARP does not discriminate the probe types; two near-identical
   `% …already…` messages mean *advisory* and *genuine rejection*; and all SVIs share one MAC so
   `client-id vlanN` emits byte-identical option 61 whichever interface is named.
3. **Three new generic tools, all hardware-verified:** `tools/dhcp4.py`, `tools/dnsresp.py`,
   `tools/opt82dump.py`. Each carries its traps in its `tools/README.md` entry.
4. **The one thing the bench cannot settle:** with the DNS forwarding cache enabled, two
   identical queries 5.3 s apart inside the TTL both went upstream. Recorded **UNMEASURED**, not
   FAIL, because the TFS separates a Name Resolver Process from a DNS Relay Process and
   S1570.1.03/.11 say "name *resolve result*" — which plausibly scopes the cache to the device's
   own lookups. **Needs a developer's answer.**

**Process lesson, measured:** cost per tool call rose **2.4×** across the campaign (183 k
cache-read per call in the first case, 431 k in the last), because every call carries the
accumulated context. Front-load specs, probes and driver-building into the cheap early part of a
session. Separately, **14% of everything the tester read all day was its own tool output read
back off disk** — extract what you need when the result first arrives.

Open afterwards: T35370 has no reboot-persistence evidence (the shared reload happened after its
removal step); T43850 proves removal for two of four `no` forms (the other two were sent only in
teardown); the DUT's `flash:/default.cfg` is **not pristine** — it carries two
`ip dhcp-client vendor-identifying-*` lines on `vlan1`, present before any testing.

Related: [[scapy-for-traffic-tests]], [[tcpdump-nfs-root-squash-capture]],
[[satisfactory-level-of-testing]], [[campaign-measurement-discipline]],
[[campaigns-measured-for-token-waste]], [[ckdb-case-lookup-by-title]].
