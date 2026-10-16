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
  swi_b **does** hold `L3-MC-ROUTE` and `VRRP`, so it is a legitimate **VRRP** peer (group D) and
  a legitimate RIP peer.
  🔴🔴 **AND A CORRECTION TO THAT CORRECTION — the sentinel's, caught by triage.** The first
  version of this note went on to say swi_b "CAN be a real PIM neighbour". **That was an
  inference stated as a measurement, and it is withdrawn.** swi_b's feature list has **no `PIM`
  bit**; `L3-MC-ROUTE` is held by all three units *including* ones whose PIM comes from a
  separate licence bit, so it is **not** the PIM gate. Only **swi_d (atlnz)** and **swi_a
  (ATL-NZ full)** are proven to hold `PIM`/`PIM6`.
  Whether swi_b can still run PIM is **genuinely unsettled** and needs a state change to answer:
  group C's first action is `service pim` on swi_b alone, wait ~10 s, then
  `show ip pim sparse-mode interface`. If refused, the PIM partner is **swi_a** — permitted under
  RISK-1, which forbids reloading and power-cycling it, not configuring it.
  Its triage refusals (`% BFD protocol daemon is not running`, `% VRRPD … not running or feature
  license is not available`, `% PIM-SM … not running or feature license is not available`) are
  the **daemon gate** for BFD and VRRP, where the licence bits are present. For PIM the "or
  feature license" clause may be the operative half — that is exactly why it must be measured,
  not inferred, in **either** direction (`platforms/x960.md` §7A.1).
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
| A | T43870 IPv4_SNMP - SNMPv3 | snmp-2026-10-16T1406 | **DONE -- PASS** (14:33-14:53) | 🟢 Instrument confirmed: net-snmp 5.7.3 (`snmpwalk/snmpget/snmpset/snmptrap`, `snmptrapd`) + `python3-pysnmp4`, all on the box — **no helper needs writing**. `snmp-server view/group/user/host` all present on the DUT. **ck.db `zephyr_cases` holds a full 9-step authored procedure with exact OIDs** (see Triage result). DUT + host eth3 only. Cheapest and least topology-hungry: run it FIRST to prove the bench and the instrument before the expensive groups. SNMPv3 = USM users, auth/priv, engine ID, views. No SNMP helper exists in `tools/` — one will be needed (`snmpwalk`/`snmpget` on the box, or a scapy/pysnmp helper) |
| B | T44181 Ping Polling · T44378 UDP Broadcast Helper · T44182 Directed Broadcast Forwarding | ipv4svc-2026-10-16T1406 | **DONE -- 3/3 PASS** (15:04-16:12) | 🟢 `ping-poll <1-100>`, `ip forward-protocol udp`, `ip helper-address`, `ip directed-broadcast [acl]` all confirmed present. T44181 has **11 authored steps**; the other two have none (design from the IP Feature Overview Guide, which we hold). No partner and no STP work needed. DUT + BOTH host NICs; two L3 segments (eth3/vlan10, eth4/vlan48). **Builds the shared L3 underlay** that groups C and D then inherit (STANDING-ORDERS §6: set once per TestSet) |
| C | T43863 PIM-SM · T43864 PIM-DM · T43865 PIM-SSM · T43866 MulticastRouting VRF-Lite | mcast-2026-10-16T1406 | **IN PROGRESS** (from 16:10) — partner settled 16:19: **swi_a**, swi_b licence-refuses `service pim` AND `service pdm` (O-20) | 🟢 DUT holds `PIM/PIM-100/PIM-1024/PIM6` + `VRF-LITE-FULL`; `service pim`/`service pdm`/`service pim6` all exist; `ip multicast-routing [vrf]`, `ip pim ssm {default|range}`, `ip pim vrf`, `show ip mroute vrf` all present. **A TWO-ROUTER topology IS achievable** despite both NICs being on the DUT — trunk eth4's VLAN to the partner and give the partner the SVI (see Triage result). **FIRST ACTION: `service pim` on swi_b, alone, wait 10 s** — swi_b's Base licence lacks the `PIM` bit, so if it refuses, fall back to swi_a (has `PIM`, RISK-1 care) or single-router. **T43865 needs `tools/igmp.py` extended to IGMPv3** (SSM is defined by the (S,G) join; current tool is v2-only). Needs the NEW-RISK-8 STP remedy. Carry **F-9** into T43866. The big group. Needs `ip multicast-routing` + the PIM service gate, a source on one host NIC and a real IGMP receiver on the other. **Check the licence and the `service ?` surface for pim/pdm BEFORE grading anything UNSUPPORTED.** T43866 is multicast *inside a VRF* — different from the unicast VRF-Lite case already passed (T43859) |
| D | T47201 IPv4_BFD - With RIP v1/v2 · T47873 VRRP(v3) | bfd-vrrp-2026-10-16T1406 | **RUNNABLE** (triaged 14:24) | 🟠 **T47201 expect UNSUPPORTED, and that is the finding**: BFD is present and NOT licence-gated on all three units, but AW+ has **no RIP↔BFD binding** — `bfd all-interfaces` is OSPF-only, and the DUT's `ip rip ?` offers no `bfd`. Rule the service gate out, quote the refusals, and pair with a working `bfd peer` session so the verdict is "BFD works, no RIP binding". 🟢 **T47873 runnable**: `VRRP` is in swi_b's Base licence so it is a legitimate peer; `service vrrp` is the gate. AW+ has **no `version {2|3}` command** — grade v3 from the advertisement's version field on the wire; `transition-mode`/`alternate-checksum-mode` prove VRRPv3-for-IPv4 exists. Needs the NEW-RISK-8 STP remedy. Both need a partner and the shared underlay. BFD needs `service bfd` + RIP on both ends; swi_b has the `RIP` licence. VRRP(v3) needs DUT and swi_b on one shared VLAN with a host as the client, and is graded on the virtual MAC on the wire |

**Group order is deliberate.** A is a single cheap case that proves console, instrument and
bench before anything expensive. B builds the **one** L3 underlay; C and D inherit it and layer
only their own protocol, removing it in their own teardown. That keeps three groups from
rebuilding the same addressing three times — the pattern that worked on 2026-10-15.

**🟢 Triage RAN 2026-10-16 14:09–14:24 NZDT — see `### New from group B (T44181, T44378, T44182, 2026-10-16). Next free numbers were F-13 and O-13.

**No F-level defect was found in any of the three cases** -- F-13 is still free. Everything
the IP Feature Overview Guide claims for these three features, this platform does. Seven
observations, and three tool defects fixed generically.

- **O-13 (T44181) — a trigger's `description` is REFUSED before its `type` is set.**
  `% Please specify the trigger type first`. The authored step 2 names `type ping-poll
  <1-100> {up|down}` and `description` with no ordering constraint. A replay of
  `show running-config` is safe (it emits `type` first); a hand-written batch in the
  authored order is not, and `cfg.py` stops at the `% ` and abandons the rest of it.
  Evidence: `T44181/work/s5-s6-config.log`.
- **🔴 O-14 (T44181) — the ping-poll PERIOD is `timeout + interval`, not `interval`.**
  With `timeout 2`, `normal-interval 5`, `critical-interval 2`: **5.0-5.2 s while Up** and
  **3.7-4.6 s, mean 4.14 s, while Down** (= timeout 2 + critical-interval 2), over 36 gaps
  on the host's own packet record, confirmed by the DUT's own debug lines ("Sending ping"
  at 02:31:38/42/46/50/54, "unsuccessful" exactly 2 s after each). The authored text says
  the critical interval is "set to send a packet every one second" by default -- with the
  default `timeout 1` that is an actual 2 s period. **A tester who configures
  `critical-interval 2`, measures 4 s and grades the command broken is wrong.** Not a
  defect; carry it into any future ping-poll or poll-timer case.
- **O-15 (T44181) — ping polling writes NO log line of its own for a state change.**
  `show log | include PING` returned nothing across four measured transitions; the only
  record is `TRIGGER[...]: Trigger N (...) activated`, which exists only if a ping-poll
  trigger is configured. A deployment using ping polling without a trigger leaves no audit
  trail. Evidence: `T44181/work/s4-dutlog.log`.
- **O-16 (T44181) — there is no `show debugging ping-poll`** (`% Invalid input detected`)
  and the full `show debugging` output has no ping-poll section. The debug state is
  readable only from the `Debugging` field of `show ping-poll <n>`.
- **O-17 (T44378) — `ip forward-protocol` accepts only `udp`, and `ip forward-protocol udp`
  only a NUMERIC port.** No named service keywords (`tftp`, `domain`, `netbios-ns`, ...)
  exist on this platform, and `ip helper-address` takes a bare `A.B.C.D` with no interface
  or VRF form. A case written against the Cisco-style named forms fails at its first
  command. Evidence: `T44378/work/s0-qmark-global.log`.
- **O-18 (T44378) — a relayed frame keeps the ORIGINAL IP source and BOTH UDP ports**; only
  the IP destination and the Ethernet header are rewritten. IP Helper is a plain forwarder
  with no relay-agent semantics -- no giaddr rewrite, no option insertion -- which is the
  OPPOSITE of `ip dhcp-relay` on the same box (`platforms/x960.md` §6). A server behind the
  helper sees the client's real address, and a tester looking for a giaddr rewrite will
  wrongly think the relay is broken. Evidence: `T44378/work/s2-helper-on.log`.
- **🔴 O-19 (T44182) — `ip directed-broadcast` on the INGRESS interface is completely
  inert, and nothing says so.** Byte-identical frames to the far subnet's broadcast address
  were dropped 0/10 with the command on `vlan10` and forwarded 10/10 with it on `vlan48`,
  nothing else changed. The guide does say "the interface via which the switch connects to
  that destination subnet", but this is the easiest thing to get wrong in the feature, a
  wrong configuration reads as a product failure, and there is no warning and no `show`
  command that reveals it. Evidence: `T44182/work/s2-wrong-if.log` vs `s3-right-if.log`.

**🔴 Three tool defects found and fixed generically (not worked around). These would have
cost groups C and D time:**
- **`tools/tb`'s `SUDO_TOOLS` allowlist was STALE.** It listed 8 root tools and was missing
  `arpleg`, `ecmpflows`, `dhcp4` and `dnsresp` -- all added 2026-10-15 -- so none of them
  could be run through the wrapper at all. All four added, plus the new `hostsim`. (Group A
  never hit this because `tools/tb` did not work on tb277 until group A fixed `BOX_PY`.)
- **🔴 `arpleg.py` mis-marked its own frames on well-known UDP ports.** It looked for its
  `CKARPLEG` tag in `pkt[Raw].load`, but **scapy dissects well-known UDP ports into their
  OWN layer** -- 69 becomes TFTP, 67/68 BOOTP, 53 DNS -- so for those ports there is no
  `Raw` layer and the tag is invisible: a `--udp ...:69` burst reported **0 of 5 of its own
  frames as `[ours]`** and raised a false `COUNTER DISAGREEMENT` (exit 7). The measurement
  was unaffected but the self-check was lying, which is worse. Both the mark and the
  counter now scan `bytes(pkt)`. Same family as the documented `dhcp4.py` BOOTP trap --
  **any other scapy tool that marks payloads has the same hole.**
- **`arpleg.py --out DIR` left a ROOT-OWNED directory**, so a later non-root tool could not
  write into it: `poll.py` completed 180 s of sampling and then died with
  `PermissionError: '/tmp/ckt1406b/T44181/poll.done'`. It now chowns the directory back to
  `SUDO_UID` as it already did the pcaps.

**🟢 New and extended generic tooling, all with `tools/README.md` entries:**
- **`tools/hostsim.py` (NEW)** -- the IPv4 counterpart of `nsresp.py`: a fake host that
  answers ARP who-has and ICMP echo for a list of addresses from a fake MAC, installs
  nothing and changes no host IP/route/interface, and **can be silenced on a timer
  (`--mute-at`/`--unmute-at`) or by a file, for SELECTED addresses only (`--mute-ip`),
  while still answering ARP** -- so a polled neighbour can go away with the link and the
  switch port still up, and a never-muted second address is the in-leg instrument control.
  `--log-echo` writes the per-request wire record an interval measurement reads from.
  Groups C and D: this is the cheap way to make any neighbour reachable or unreachable on
  demand (a VRRP client, a tracked next hop, an ARP ageing timeout).
- **`tools/arpleg.py` extended** with `--udp DST[:PORT][@SRC]` (a CHOSEN destination port
  and an optional per-spec source -- an ACL-filtered forwarding case needs two sources in
  ONE capture), `--l2-dst MAC|broadcast` (scoped to `--udp` ONLY, so one leg can carry a
  link-layer broadcast flow AND a routed unicast control), `--sport` and `--ttl`.
- **`console.ADVISORY`** gained `does not exist\. Please ensure it is created` -- the
  trigger `script N <file>` warning is an ADVISORY, not a rejection: the reference IS
  stored (`show trigger 1 -> Number of scripts 1`). Added with the transcript that
  `console.py`'s own rule requires (`T44181/work/s9-script-file.log`).

**🟢 Useful for groups C and D:**
- **`ckcase.py` confirmed again**: T44181 had 11 authored steps; **T44378 and T44182 had
  NONE** (no objective, no precondition, empty `steps`), exactly as triage predicted. Both
  logs say so explicitly and name the guide section used instead. Run `ckcase.py` first.
- **Reload to `login:` measured three times on this build: 68 s, 61 s, 60 s** -- the x960
  §7.9 range (60-68 s) holds. **Re-read STP after EVERY reload**: the T44182 post-reload
  read caught `port1.0.48 Designated Learning` and needed a confirming read before the
  measurement could be trusted.
- **The reboot-persistence recipe works cleanly here**: `copy running-config
  flash:/ck<ID>.cfg` -> `boot config-file flash:/ck<ID>.cfg` -> reload -> restore the
  pointer -> `delete` with `ckyn.py`'s `YN:` form. Three times, no residue. startup-config
  and `flash:/default.cfg` were never written.
- ⚠️ **The shared underlay lives in running-config ONLY.** `flash:/default.cfg` is the
  pristine campaign baseline and was never written, so **any reload by group C or D comes
  up WITHOUT the underlay** and it must be re-applied (the recipe is in the section above).

## Triage result` at the end of this file.**
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

## Group A (snmp-2026-10-16T1406) — bench setup and its EXACT restore recipe

Written **before** the first configuration command (bench-runner, 2026-10-16 14:40 NZDT), so a
fresh tester can restore the bench if this one dies mid-group.

**Devices touched: swi_d (DUT, /dev/u2 @115200) ONLY.** swi_b and swi_a are not configured, not
reloaded and not power-cycled by this group. Host side: box `eth3` (10.38.22.33/27,
`00:0d:b9:55:77:0e`) is the SNMP manager; no host NIC addressing is changed.

**Pre-case DUT running-config is saved at**
`tb277/x960/snmp-2026-10-16T1406/T43870/work/pre-u2.log` (a `ckcon.py` stdout, usable directly
with `tools/rcdiff.py`). **That file is the restore target.**

### What this group changes on the DUT

1. `interface vlan1` — the baseline is **`ip address dhcp`** plus
   `ipv6 enable`, `ipv6 address dhcp`, `ip dhcp-client vendor-identifying-class`,
   `ip dhcp-client request vendor-identifying-specific`. The case replaces the address with a
   **static `10.38.22.34/27`** (substituted for the authored `192.168.1.1/24`, so the box's
   existing `eth3` segment can be the manager without a root-level host addressing change —
   STANDING-ORDERS §4).
2. SNMPv3 objects from the authored precondition: `snmp-server view`, `snmp-server group`,
   `snmp-server user`, `snmp-server host`. The bare `snmp-server` line is **already present at
   baseline** and must be LEFT IN PLACE.
3. One named boot config for the persistence limb: `flash:/ck43870.cfg`, with
   `boot config-file flash:/ck43870.cfg`, then **one reload of swi_d**.

### Restore recipe (run on /dev/u2 @115200, in this order)

```
configure terminal
 no snmp-server host 10.38.22.33 version 3 auth TESTtestTESTtestTEST
 no snmp-server user TESTtestTESTtestTEST ADMINadminADMINadmin
 no snmp-server group ADMINadminADMINadmin priv read MOSTmostMOSTmostMOST write MOSTmostMOSTmostMOST notify MOSTmostMOSTmostMOST
 no snmp-server view MOSTmostMOSTmostMOST 1.3.6.1.2.1.1
 no snmp-server view MOSTmostMOSTmostMOST 1.3.6.1.2.1.1.5
 no snmp-server view system 1.3.6.1.2.1.1
 no boot config-file                      <- only if a `boot config-file` line is left behind
 interface vlan1
  no ip address 10.38.22.34/27
  ip address dhcp
  ipv6 enable
  ipv6 address dhcp
  ip dhcp-client vendor-identifying-class
  ip dhcp-client request vendor-identifying-specific
 end
delete flash:/ck43870.cfg                 <- prompts (y/n)[n]; use ckyn.py `YN:`, it ABORTS if unanswered
```

Then confirm `show boot` reads `Current boot config: flash:/default.cfg` and
`tools/rcdiff.py work/pre-u2.log work/post-u2.log` prints nothing. **`rcdiff.py` exits 0 even
when it prints differences — gate on the OUTPUT.** Keep the bare `snmp-server` line.

**Nothing is written to startup-config.** `flash:/default.cfg` is never overwritten; the
persistence limb uses a separate file and puts the pointer back.

## Group B/C/D shared L3 underlay and restore

Written by the group-B tester (bench-runner) at **2026-10-16 15:10 NZDT / 02:10 UTC**, **before
the first configuration command of group B**, so a fresh tester can restore the bench if this
one dies mid-group. STANDING-ORDERS §6: bench setup is set ONCE per TestSet, not per case.

**Groups C and D inherit this.** Group B takes down only each *case's* own additions at each
case teardown; **the underlay itself is left UP** at the end of group B.

### Devices touched by the underlay

**swi_d (DUT, /dev/u2 @115200) ONLY.** swi_b and swi_a are not configured, not reloaded and not
power-cycled by group B. No host-NIC addressing is changed (STANDING-ORDERS §4), and no
startup-config is written.

**The restore target is the pre-group DUT running-config**, saved before anything was sent, at
`tb277/x960/ipv4svc-2026-10-16T1406/T44181/work/pre-u2.log` (a `ckcon.py` stdout, usable
directly with `tools/rcdiff.py`). It is byte-identical in substance to the campaign baseline:
`vlan1 ip address dhcp`, all 57 ports untagged in vlan1, `spanning-tree mode rstp`,
`lacp global-passive-mode enable`, `no ip multicast-routing`, boot config `flash:/default.cfg`.

### 🔴 The addressing differs from the shape the dispatch proposed, and here is why

The dispatch proposed `vlan10 192.168.10.1/24` and `vlan48 192.168.48.1/24`. **Measured against
the hardware, those cannot carry group B**, so they were not used:

- The box's two usable NICs already own `eth3 10.38.22.33/27` and `eth4 10.38.22.65/27`. A DUT
  SVI in `192.168.10.0/24` shares no subnet with either, so the box's kernel would neither ARP
  for it nor answer it.
- **T44181 Ping Polling needs the DUT to ping a REAL responder** — the poll is generated by the
  DUT's own IP stack, not by scapy, so a crafted source address cannot stand in for the host.
- **T44378's helper destination must ARP-resolve** on the egress segment for the relayed unicast
  to leave the DUT at all.
- Putting the host on `192.168.x` would need `ip addr add` on the box = a root-level host
  addressing change = **STANDING-ORDERS §4, never done unattended**. Group A hit the same wall
  and solved it the same way (it substituted `10.38.22.34/27` for the authored `192.168.1.1/24`).

⇒ The underlay uses the box's own two segments. Crafted scapy traffic still uses whatever source
addresses a case needs; only the DUT's SVI addresses are pinned to the real subnets.

### The underlay, as sent (DUT, /dev/u2)

```
configure terminal
 vlan database
  vlan 10 name ckUNDERLAY-eth3
  vlan 48 name ckUNDERLAY-eth4
  exit
 interface port1.0.10
  switchport access vlan 10
 interface port1.0.48
  switchport access vlan 48
 interface vlan10
  ip address 10.38.22.34/27
 interface vlan48
  ip address 10.38.22.66/27
 end
```

Resulting topology (all three segments measured at 15:06 NZDT, STP roles from
`show spanning-tree brief`):

| segment | DUT side | host side | STP role of the DUT port |
| --- | --- | --- | --- |
| A | `vlan10` = `10.38.22.34/27`, member `port1.0.10` | `eth3 10.38.22.33/27`, MAC `00:0d:b9:55:77:0e` | **Designated Forwarding** |
| B | `vlan48` = `10.38.22.66/27`, member `port1.0.48` | `eth4 10.38.22.65/27`, MAC `00:0d:b9:55:77:0f` | **Designated Forwarding** |

- Subnet A = `10.38.22.32/27`, broadcast **`10.38.22.63`**. Subnet B = `10.38.22.64/27`,
  broadcast **`10.38.22.95`**. Those two broadcast addresses are the subjects of T44182.
- **All DUT SVIs share one MAC, `e0:1a:ea:d4:70:43`** (x960 §6.5) — that is the `--gw-mac` for
  every crafted leg, and the DUT's bridge id is `8000:e01aead47043`.
- ⚠️ The carried open issue **`10.38.22.41` / `00:0c:25:2a:a5:53`** lives on the `eth3`
  segment. It receives every broadcast group B sends on segment A. Every count is attributed by
  MAC so its traffic is never confused with the DUT's.

### 🟢 What group B did NOT build, and what C and D must add themselves

- **No partner leg.** None of B's three cases needs swi_b or swi_a, so no transit VLAN was
  created and **NEW-RISK-8 was never triggered**: `port1.0.10` and `port1.0.48` were already
  Designated Forwarding at 15:06 and stayed so. `port1.0.2` Rootport Forwarding,
  `port1.0.4` / `port1.0.14` / `port1.0.16` Alternate Discarding — **unchanged from triage**.
- ⇒ **Group C and group D each own the NEW-RISK-8 remedy** (`spanning-tree priority 0` on the
  DUT, `shutdown port1.0.14` and `port1.0.2`, then confirm `show spanning-tree brief` BEFORE
  measuring), plus their own transit VLAN, e.g. `vlan 61` on `port1.0.16` ↔ swi_b `port1.0.16`
  with `10.0.61.1/30` ↔ `10.0.61.2/30` and swi_b return routes for `10.38.22.32/27` and
  `10.38.22.64/27` via `10.0.61.1`. **None of that exists yet.**
- 🔴 **Group C's two-router multicast design conflicts with `vlan48`'s SVI.** Triage's design
  wants `port1.0.48` in a VLAN for which the **DUT has no SVI**, trunked to the partner which
  owns the SVI. Group C must therefore remove `interface vlan48` (or move `port1.0.48`) as its
  own first setup step, and restore it afterwards. `vlan10` is unaffected and is group C's
  source segment.

### 🔴 Restore recipe — the EXACT sequence (DUT, /dev/u2 @115200)

Run this, in this order, to put the bench back to the campaign baseline. It is the **whole**
restore: group B changed nothing on swi_b or swi_a, nothing on the host, and nothing in
startup-config or the boot pointers.

```
configure terminal
 interface vlan10
  no ip address
 interface vlan48
  no ip address
 exit
 no interface vlan10
 no interface vlan48
 interface port1.0.10
  switchport access vlan 1
 interface port1.0.48
  switchport access vlan 1
 exit
 vlan database
  no vlan 10
  no vlan 48
  exit
 end
```

Then verify with, and only with, a diff against the saved pre-group config:

```
tools/tb ckcon tb277 <scratch> u2 115200 "show running-config" > /tmp/post.log
tools/tb tool tb277 <scratch> rcdiff ...   # or locally: python3 tools/rcdiff.py pre-u2.log post.log
```

⚠️ **`rcdiff.py` prints differences but exits 0** — gate on its OUTPUT, never on its exit code.

**Per-case additions, each removed by that case's own teardown and NOT part of the underlay:**

| case | what it adds on top of the underlay | removed by |
| --- | --- | --- |
| T44181 | `ping-poll <n>` instances, two `trigger` instances, two `.scp` scripts in `flash:`, `debug ping-poll` | its own teardown (`no ping-poll`, `no trigger`, `delete` each `.scp` — the `delete` prompt is `(y/n)[n]` and **aborts if unanswered**, so use `ckyn.py`/`cfg.py` `YN:`) |
| T44378 | `ip forward-protocol udp <port>` (global), `ip helper-address <a>` on `interface vlan10` | its own teardown |
| T44182 | `ip directed-broadcast [acl]` on `interface vlan48`, one standard `access-list` | its own teardown |

**Reboot-persistence limbs** stage a named boot config (`copy running-config flash:/ck<ID>.cfg`,
`boot config-file flash:/ck<ID>.cfg`), reload swi_d, re-measure, then put the pointer back to
`flash:/default.cfg` and `delete` the file. **Baseline to return to: `Current boot config:
flash:/default.cfg`, `Current boot image: flash:/x960-tb277.rel`, `Autoboot status: disabled`.**
Re-read `show spanning-tree brief` after every reload before measuring (Discarding ~17-21 s).

### Group B gate results, 2026-10-16 15:04-15:07 NZDT (02:04-02:07 UTC)

| gate | result |
| --- | --- |
| §3 occupancy `precheck u2,u3,u5` | **u2, u3, u5 all free.** FOUND (exit 5) = the same two non-ours items as triage: `ser2net` pid 744 and `minicom -D /dev/ttyUSB1` pid 10790 (the Test Engineer's own u1 session). **Neither touched.** Re-sent to the sentinel as a one-line informational `NEEDS TEST ENGINEER:`; not blocked on (unattended rule) |
| consoles parked mid-state? | **No.** `peek` gave `awplus login:` (u2), `x960-28YSQ login:` (u3), `awplus login:` (u5) — all at the login prompt, nothing in config mode and no root shell |
| template | **none** — `no deployed tb277.setup`, as expected (RISK-6). All cases manual; no framework, so no preflight and no post-failure PDU cycle |
| probe `run --consoles u2,u3,u5 --pdu 10.36.230.212 --outlet u2=1,u3=7 --name u2=swi_d,u3=swi_b,u5=swi_a` | **exit 0**, `diff skipped` (no template), **no advisories**. Capture `bench-setup/tb277/captures/2026-10-16T020647Z` |
| boot baseline (gate 7) | DUT `Current boot image: flash:/x960-tb277.rel (file exists)`, `Current boot config: flash:/default.cfg (file exists)`, `Autoboot status: disabled` |
| clocks (RISK-5) | DUT `02:06:04 UTC` against box `02:06:13 UTC` — **DUT ~9 s behind the box**, same as triage. swi_b and swi_a were measured in sync at triage 45 min earlier and are not touched by group B |
| sentinel | `sentinel: parent` (one-session `/test-mode` shape) — nothing to arm |
| scratch | `/tmp/ckt1406b/` on the box (48 tools). ⚠️ tb277 `/tmp` is still ~95% full with another user's 1.8 GB of captures — **not ours to delete**; every group-B capture is BPF-filtered, under 1 MB, and deleted after it is read |

## Group C (mcast-2026-10-16T1406) — bench setup and its EXACT restore recipe

Written by the group-C tester (bench-runner) at **2026-10-16 16:25 NZDT / 03:25 UTC**, **before
the first configuration command of group C**, so a fresh tester can restore the bench if this
one dies mid-group.

### 🔴 SETTLED IN THE FIRST FIVE MINUTES: the PIM partner is **swi_a**, not swi_b

The queue left this genuinely open and told group C to measure it. It is now measured, and the
answer is unambiguous — **O-20** below:

```
x960-28YSQ(config)#service pim
% Service is not currently licensed on this platform
x960-28YSQ(config)#service pdm
% Service is not currently licensed on this platform
```

Both sent alone, on swi_b (/dev/u3), 2026-10-16 16:18:48 and 16:19:25 NZDT. Neither was
accepted, so **nothing was applied to swi_b and its running-config is unchanged** (verified:
only `service password-encryption` and `service ssh` are present). swi_b's `service ?` list
*does* offer `pdm`, `pim` and `pim6` — the CLI surface is identical on all three units — so the
surface probe triage ran could never have settled this. The licence is the gate, and the
message is a **different and much clearer one** than the `% PIM-SM protocol daemon is not
running or feature license is not available` that `show ip pim …` gives: it names the licence
with no daemon ambiguity at all.

⇒ **Partner for all of group C's two-router work: swi_a (/dev/u5 @9600, x950 GEN2, `full`
ATL-NZ licence, holds `PIM/PIM-100/PIM-1024/PIM6`).** Handled under **RISK-1**: configured
freely, **never reloaded and never power-cycled**. swi_a netbooted with no config file, so
`no service pim` leaves no sticky line on it (x960.md §7A.2 applies only to a unit that BOOTED
with the service) and its teardown comes back clean without a reload.

### Devices touched by group C

| device | console | touched how |
| --- | --- | --- |
| **swi_d (DUT)** | /dev/u2 @115200 | STP priority, two ports shut, vlan 61, the vlan48 SVI REMOVED, port1.0.4 trunked, `service pim`/`pdm`, `ip multicast-routing`, PIM, a static route, VRFs (T43866). **One reload at the very END of the group** |
| **swi_a (partner)** | /dev/u5 @9600 | vlan 48 + vlan 61, port1.0.4 trunked, two SVIs, `service pim`/`pdm`, `ip multicast-routing`, PIM, a static route. **NEVER reloaded or power-cycled (RISK-1)** |
| **swi_b** | /dev/u3 @9600 | **two refused `service` commands and one read-only `?` probe — nothing applied.** Not configured, not reloaded, not power-cycled |

Host side: box `eth3` (10.38.22.33/27, `00:0d:b9:55:77:0e`) = the multicast **source** segment;
box `eth4` (10.38.22.65/27, `00:0d:b9:55:77:0f`) = the **receiver** segment. **No host NIC
addressing is changed** (STANDING-ORDERS §4).

**Restore targets, captured before anything was sent:**
- DUT: `tb277/x960/mcast-2026-10-16T1406/T43863/work/pre-u2.log`
- swi_a: `tb277/x960/mcast-2026-10-16T1406/T43863/work/pre-u5.log`
- swi_b: `tb277/x960/mcast-2026-10-16T1406/T43863/work/pre-u3.log`

All three are `ckcon.py` stdouts, usable directly with `tools/rcdiff.py`. The DUT capture is the
shared B/C/D underlay exactly as group B left it; swi_a is a bare netboot config (every port
access vlan1, `no ip multicast-routing`, `spanning-tree mode rstp`, `lacp global-passive-mode
enable`, no VLANs but 1).

### The two-router topology group C builds

Triage's design, with swi_a substituted for swi_b as the partner. `port1.0.4` is the DUT↔swi_a
link that survives the NEW-RISK-8 remedy.

```
host eth3 10.38.22.33/27 ──(DUT port1.0.10 access vlan 10, SVI 10.38.22.34/27 on the DUT)── swi_d
                                                                                             ║
                                     port1.0.4 TRUNK, tagged vlan 48 + vlan 61               ║
                                                                                             ║
host eth4 10.38.22.65/27 ──(DUT port1.0.48 access vlan 48, NO SVI on the DUT)════════════════╝
                                                                                             ║
                                                                                           swi_a
                                                        vlan 48 SVI 10.38.22.66/27  (receiver's router)
                                                        vlan 61 SVI 10.0.61.2/30    (transit, PIM adjacency)
```

- **DUT = the source's first-hop router** (DR on vlan 10) and the upstream PIM router.
- **swi_a = the receiver's last-hop router** (DR on vlan 48) and, for T43863, **the RP**.
- `vlan 61` `10.0.61.0/30` carries the PIM adjacency, the Register path and the SPT. It has no
  host NIC, so it is read with **the DUT's own `tcpdump` at privileged exec** (the queue's
  techniques block) — that is the instrument for every Hello / Join-Prune / Register claim.
- `eth4` is **logically behind swi_a while still cabled to the DUT**, which is the whole point:
  the DUT's vlan 48 is pure L2 and the DUT has no SVI on it.

🔴 **This means the shared underlay's `interface vlan48 / ip address 10.38.22.66/27` is REMOVED
for the whole of group C** and the address moves to swi_a. `vlan 48` itself, and
`port1.0.48 switchport access vlan 48`, stay. Group D inherits whatever the group-end restore
below leaves — see "What group C leaves for group D".

### Setup, as sent

**NEW-RISK-8 remedy first (DUT, /dev/u2), and confirmed with `show spanning-tree brief` BEFORE
any measurement:**
```
configure terminal
 spanning-tree priority 0
 interface port1.0.2
  shutdown
 interface port1.0.14
  shutdown
 end
```
(DUT becomes root ⇒ every DUT port Designated Forwarding; shutting the redundant swi_a leg
`port1.0.14` and the RISK-2 swi_b leg `port1.0.2` forces swi_a's root-port choice onto its
`port1.0.4` and swi_b's onto its `port1.0.16`, rather than a bridge-ID tie-break.)

**DUT L2/L3:**
```
configure terminal
 vlan database
  vlan 61 name ckTRANSIT
  exit
 no interface vlan48
 interface port1.0.4
  switchport mode trunk
  switchport trunk allowed vlan add 48,61
 interface vlan61
  ip address 10.0.61.1/30
 exit
 ip route 10.38.22.64/27 10.0.61.2
 end
```

**swi_a L2/L3 (/dev/u5 @9600):**
```
configure terminal
 vlan database
  vlan 48 name ckRECEIVER
  vlan 61 name ckTRANSIT
  exit
 interface port1.0.4
  switchport mode trunk
  switchport trunk allowed vlan add 48,61
 interface vlan48
  ip address 10.38.22.66/27
 interface vlan61
  ip address 10.0.61.2/30
 exit
 ip route 10.38.22.32/27 10.0.61.1
 end
```

**The service gate — `service <proto>` ALONE, then ~10 s, then everything else** (x960.md
§7A.1). Per case: `service pim` for T43863/T43865, `service pdm` for T43864. `ip
multicast-routing` is global and is additionally required before `ip pim sparse-mode` is
accepted ("IP Multicast Routing not activated").

### 🔴 Restore recipe — the EXACT sequence

Run this to put the bench back to the state group B left (the shared underlay), which is what
group D expects.

**1. swi_a (/dev/u5 @9600) — config only, NEVER a reload (RISK-1):**
```
configure terminal
 no ip route 10.38.22.32/27 10.0.61.1
 no ip pim rp-address 10.0.61.2
 no ip multicast-routing
 no interface vlan48
 no interface vlan61
 interface port1.0.4
  switchport mode access
 exit
 vlan database
  no vlan 48
  no vlan 61
  exit
 no service pim
 no service pdm
 end
```
Then `python3 tools/rcdiff.py T43863/work/pre-u5.log <post-u5 capture>` must print **nothing**.
`rcdiff.py` exits 0 even when it prints differences — **gate on the OUTPUT**.

**2. DUT (/dev/u2 @115200) — configuration, then ONE reload:**
```
configure terminal
 no ip route 10.38.22.64/27 10.0.61.2
 no ip pim rp-address 10.0.61.2
 no ip multicast-routing
 no interface vlan61
 interface port1.0.4
  switchport mode access
 exit
 vlan database
  no vlan 61
  exit
 interface port1.0.2
  no shutdown
 interface port1.0.14
  no shutdown
 no spanning-tree priority
 no service pim
 no service pdm
 end
```
**Then reload the DUT onto `flash:/default.cfg`.** Two reasons, and the second is the one that
makes the reload non-optional:
- it is the only way to clear a **sticky `no service pim` / `no service pdm` line** if any
  reboot-persistence limb in this group staged a boot config that contained the service
  (x960.md §7A.2: the line appears on a unit that BOOTED with the service and configuration
  cannot remove it);
- it returns the DUT to the campaign baseline `Current boot config: flash:/default.cfg`,
  `Current boot image: flash:/x960-tb277.rel`, `Autoboot status: disabled`.

**3. 🔴 The reload loses the shared underlay — re-apply it immediately afterwards.**
`flash:/default.cfg` is the pristine baseline and has never been written, so the DUT comes back
with no vlan 10, no vlan 48 and no SVIs. Re-send group B's underlay verbatim:
```
configure terminal
 vlan database
  vlan 10 name ckUNDERLAY-eth3
  vlan 48 name ckUNDERLAY-eth4
  exit
 interface port1.0.10
  switchport access vlan 10
 interface port1.0.48
  switchport access vlan 48
 interface vlan10
  ip address 10.38.22.34/27
 interface vlan48
  ip address 10.38.22.66/27
 end
```
Then **re-read `show spanning-tree brief` before anything is measured** — a port reads
Discarding for ~17–21 s after `login:` — and diff the DUT against
`T43863/work/pre-u2.log`, which must come back empty.

**4. swi_b:** nothing to restore. Two `service` commands were refused and one `?` probe was
read-only; its running-config was captured before and is unchanged.

### What group C leaves for group D

Recorded here as the group runs; the final state is restated in `## Results` when group C ends.
**Intended** end state = exactly the group-B shared underlay on the DUT, a bare swi_a, an
untouched swi_b, and the DUT back on `flash:/default.cfg` after one reload.


## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |
| T43870 | **PASS** | All 9 authored steps passed, plus baseline-off, auth/priv enforcement, on-the-wire encryption with an in-capture plaintext control, removal and reboot persistence. The authored precondition omits the group's read view (O-9) and was run with that one line supplied. Also produced F-12. | tester | snmp-2026-10-16T1406/T43870/work/run1.log |
| T44181 | **PASS** | All 11 authored steps (step 1's ART run substituted by a direct measurement of the limit it measures: 100 instances accepted, 0 and 101 rejected), plus baseline-off, wire-measured normal and critical intervals, fail-count/up-count transitions corroborated by the DUT's own trigger log to within 1 s, per-instance `clear`, removal and reboot persistence in the dataplane. Produced O-13..O-16 and the new `tools/hostsim.py`. Trigger-SCRIPT-CONTENT limb not measurable unattended (needs a root write to the box's /tftproot, §4). | tester | ipv4svc-2026-10-16T1406/T44181/work/run1.log |
| T44378 | **PASS** | **No authored step text exists** -- designed from the IP Feature Overview Guide C613-22007-00 REV I p.16 and the DUT's CLI surface, and said so in the log. Nothing relayed by default; both all-ones and subnet-directed broadcasts relayed on helped ports while an unhelped control port never was; the forward-protocol port list and the helper address proven independent; multiple helper addresses each produce a copy; a helper address that is a connected subnet's broadcast is forwarded as a true link-layer broadcast; removal and reboot persistence in the dataplane. Teardown diff EMPTY. Produced O-17, O-18 and a real `arpleg.py` marker defect. | tester | ipv4svc-2026-10-16T1406/T44378/work/run1.log |
| T43863 | **PASS** | **No authored step text exists** -- designed from RFC 4601 and the DUT's CLI surface, and said so in the log. Two-router topology (DUT = source DR, swi_a = last-hop DR and RP) built after O-20 settled that swi_b cannot run PIM. Baseline off with a JOINED receiver 0/10; forwarding 5/5 with a never-joined control group 0/5 and an instrument control in all 9 legs; Register / RP Join-Prune / Register-Stop / SPT decoded on the transit wire with the DUT's own tcpdump; prune-on-leave proven group-specific (left group 0/5, still-joined group 5/5, same leg); the RP isolated by A/B on one group (0/10 -> 8/10); removal and reboot persistence both proven in the dataplane. Produced F-13, O-20..O-24 and two generic tool fixes. | tester | mcast-2026-10-16T1406/T43863/work/run1.log |
| T43864 | **PASS** | Authored objective and authored topology both satisfied -- the group-C two-router bench IS `IXIA -- DUT -- sw1(running PIM-DM) -- IXIA` with swi_a as a real PIM-DM sw1 -- and the authored step measured 10/10 then 30/30. Plus baseline off with `pdmd` already running (0/10), a branch with no receiver pruned (0/40, 0/50, 0/25, empty OIF), the PIM-DM-specific State Refresh and Join/Prune decoded on the transit wire, a Graft/Graft-Ack handshake 206 us apart turning the SAME group from 0/50 to 20/20, group-specific prune on leave, removal and reboot persistence in the dataplane. Initial flood declared NOT MEASURED (O-25). Produced O-25, O-26 and the F-13 addendum. | tester | mcast-2026-10-16T1406/T43864/work/run1.log |
| T43865 | **PASS** | All THREE authored steps pass, including step 1's "Check IGMP Host Joined the correct multicast source" -- measurable only because `tools/igmp.py` gained an IGMPv3 source-list mode for this case. The defining SSM property proven on the wire: the joined channel forwards 9-10/10 while the SAME group from a DIFFERENT source is 0/10 in the same leg, discriminated at layer 3 with both flows sharing one link-layer address. IGMPv2 (*,G) on the SSM range rejected; table state pure SSM (zero (*,G), one (S,G), SPT bit 1, no RP configured at all); prune on leave clears both tables; interface down/up correct with the two readings distinguished (O-28); source filtering still enforced after a cold boot. Teardown diff EMPTY on BOTH devices. Produced F-14, O-27, O-28. Two authored read-backs do not exist (`show ip pim spare-mode mroute` is a typo, `show ip igmp group` is `groups`) and the substitutions are declared. | tester | mcast-2026-10-16T1406/T43865/work/run1.log |
| T44182 | **PASS** | **No authored step text exists** -- designed from the same guide, p.17. Off by default and dropped; enabled on the DESTINATION subnet's interface the identical frames are forwarded and translated to a link-layer broadcast; enabled on the INGRESS interface it is inert (O-19); the optional standard ACL filters on source and is consulted per packet, proven by INVERTING it; removal and reboot persistence in the dataplane. Teardown diff EMPTY. | tester | ipv4svc-2026-10-16T1406/T44182/work/run1.log |

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
- **🟠 NEEDS YOU (T44181, informational — did not block the case).** The one limb that could not
  be measured unattended is the **content of a trigger script**: putting an `.scp` on the DUT's
  flash needs a root-level write to the box's `/tftproot`, which is STANDING-ORDERS §4 and is
  never done unattended. The **ping-poll side of the trigger contract was measured in full**
  (both transitions, timestamped, with an in-leg control). If you want the script-execution limb
  covered, stage an `.scp` on tb277 and the case can be re-run for that step alone.
- **🟠 O-14 (T44181, carry this one) — the ping-poll PERIOD is `timeout + interval`, not
  `interval`.** With `timeout 2`, `normal-interval 5`, `critical-interval 2` the measured period
  was **5.0-5.2 s while Up** and **3.7-4.6 s, mean 4.14 s, while Down** (= timeout 2 +
  critical-interval 2), over 36 gaps on the host's own packet record and confirmed by the DUT's
  debug lines. **A tester expecting the bare `critical-interval` would read this as a broken
  timer.**
- **🔴 TOOL DEFECT FOUND AND FIXED (T44378) — it produced a FALSE counter disagreement, and any
  payload-marking scapy tool has the same hole.** `tools/arpleg.py` looked for its payload marker
  in `pkt[Raw].load`, but **scapy dissects well-known UDP ports into their own layer** — 69 into
  `TFTP`, 67/68 into `BOOTP`, 53 into `DNS` — so a burst to `:69` has **no `Raw` layer at all**.
  The tool reported **0 of its own 5 frames** and flagged them as foreign, which reads exactly
  like the DUT failing to relay. Fixed to scan the whole frame rather than `Raw`; README updated.
  **Check every other scapy helper that tags payloads for the same assumption** before trusting a
  zero from it. This is the third instrument fault this bench has caught before it reached a
  verdict, and the reason every leg carries an instrument control.
- **O-17 (T44378)** `ip forward-protocol udp` takes a **numeric port only** — no named service
  keywords.
- **O-18 (T44378)** the relay **preserves the original IP source and both UDP ports** — no
  `giaddr`, no relay-agent option — unlike `ip dhcp-relay` on the same box.
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

### New from group C (2026-10-16). Next free numbers were F-13 and O-20.

- **🔴 F-13 (T43863, and it will bite every multicast case) — `ip pim sparse-mode` does NOT
  enable router-side IGMP on an interface, and IGMP SNOOPING hides the fact.** With
  `ip multicast-routing`, `ip pim sparse-mode` on the receiver SVI, the PIM adjacency up, the
  group-to-RP mapping present on both routers and the RPF route present, a joined receiver got
  **0 of 5** frames. The receiver interface read:
  `IGMP Disabled, Active(Snoop Only), Non-Querier, Version 3 (default)` /
  `IGMP querying router is 0.0.0.0`, while at the same instant
  `show ip igmp groups` listed `239.1.1.1 vlan48 uptime 00:00:39 Expires 00:03:41` and
  `show ip pim sparse-mode local-members` listed **nothing** under vlan48 — the membership was
  held by snooping, which does not feed PIM. The report itself was confirmed well-formed on the
  wire first (`IP p2 10.38.22.70 -> 239.1.1.1`, correct on-subnet source), so the host was
  exonerated before the platform was blamed. A single `ip igmp` on the interface fixed it:
  `IGMP Enabled, Active, Querier` and `(*, 239.1.1.1) : Include`, and the same leg then
  forwarded. ⇒ **a receiver interface needs BOTH `ip pim sparse-mode` and an explicit
  `ip igmp`.** Two read-backs disagree at the same instant and the dataplane follows the
  pessimistic one — the same family as the x960 mirroring trap (`platforms/x960.md` §5) where
  `show mirror` read Enabled while nothing was copied. **Worth a developer's eye**: whether
  enabling PIM on an interface should imply router-side IGMP, and whether `show ip igmp groups`
  should distinguish a snooped membership from a routed one.
  Evidence: `mcast-2026-10-16T1406/T43863/work/run1.log` legs 2 and 3.
- **O-21 (T43863)** `show ip igmp groups` reports **`Last Reporter 0.0.0.0`** on this build even
  though the report on the wire carries a correct on-subnet source (10.38.22.70, confirmed by
  capture), both before and after `ip igmp` was enabled. Cosmetic, but it reads like a malformed
  report and cost diagnosis time inside F-13.
- **O-22 (T43863)** `no interface vlanN` is **refused** on AW+: `% Removal of interface not
  allowed`. An SVI is retired with `no ip address` (the VLAN stays, L2 bridging continues),
  and the VLAN itself with `no vlan N` in `vlan database`. Group C needed this to move the
  receiver subnet's SVI from the DUT to the partner.
- **🔴 O-23 (T43863) — TOOL DEFECT FOUND AND FIXED in `tools/console.py`.** AW+ **switch-driver**
  port-state messages are written straight to the console by the driver, not through the logging
  subsystem, so **neither `terminal no monitor` nor `no log console` suppresses them** (both
  measured). One can land INSIDE the prompt rather than after it:
  `awplus(config-ifswitch: port 14(port1.0.14) entered disabled state` / `)#`, and a second
  family does the same on `ip pim sparse-mode`: `awplus(config-ifvlan61: entered allmulticast
  mode` / `)#`. Neither half is a prompt, so the command ran to its FULL 90 s timeout and
  `cfg.py` then **silently abandoned every command after it** although the command itself had
  taken effect — the same silent-truncation family as the advisory trap already in
  `console.ADVISORY`. Fixed generically and twice over, so an unseen message still works:
  `PROMPT_ANYWHERE_RE` now also matches a line beginning `)#` (the tail a splice always leaves,
  and something no device output legitimately produces), and `SPLICE_RE`/`unsplice()` strip the
  known families from a COPY of the buffer and retry. Self-tested on 6 buffers before being
  pushed. **Any campaign that shuts or unshuts ports through `cfg.py` was losing the rest of its
  batch to this.**
- **🔴 F-14 (T43865) — the IGMPv2 any-source-join rejection is bound to the hardcoded IANA
  232/8 range ONLY, and is not applied to a range configured with `ip pim ssm range <acl>`.**
  Measured on one router, one interface, two groups, in a single `show ip igmp groups`: with
  `access-list 20 permit 239.20.20.20 0.0.0.0` + `ip pim ssm range 20` active on both routers,
  an IGMPv2 (*,G) join on **239.20.20.20 was ACCEPTED** (`00:00:07  00:04:14`), while the same
  v2 join on **232.7.7.7 was REJECTED** (absent from the table) 40 s later. The 232/8 rejection
  also persists with **no SSM configuration at all**, so `ip pim ssm default` is not what
  enforces it. RFC 4607 §4.2 expects SSM semantics on the configured range too.
  **Impact measured, and it is limited**: the accepted (*,G) membership is inert — traffic from
  an arbitrary source to 239.20.20.20 was **0 of 10** in the dataplane (no RP is configured),
  so nothing leaks. It is a spec-conformance gap that makes `ip pim ssm range` weaker than
  `ip pim ssm default`, not a forwarding hole. **Worth a developer's eye.**
  Evidence: `mcast-2026-10-16T1406/T43865/work/run1.log` leg 6.
- **O-27 (T43865)** `ip pim ssm` has an **asymmetric negation**: the positive form takes
  `default` or `range <acl>`, the negation takes **neither** — `no ip pim ssm default` is
  `% Invalid input detected`, and the working form is bare `no ip pim ssm` (settled with a
  read-only `no ip pim ssm ?` probe). Same family as group A's O-10. A teardown that mirrors
  its setup line-for-line fails.
- **O-28 (T43865) — "interface down" has two readings and only one updates the multicast
  table.** Shutting the RECEIVER'S L2 access port on the DUT left swi_a's IGMP group and its
  mroute entry fully populated, because the multicast router is swi_a and its `vlan48` SVI is
  still up over the trunk — it cannot see a host unplug two switches away, and the membership
  is soft state that must time out. Shutting swi_a's own `interface vlan48` cleared both tables
  immediately and dropped the interface from `show ip pim sparse-mode interface`
  (`Total active interfaces: 1`). T43865's authored step 3 expects "the multicast routing table
  updates accordingly", which is **only true for the router-interface reading** — a tester who
  shuts the host's port and expects the table to clear will record a false failure.
- **O-25 (T43864) — the FLOOD half of PIM-DM flood-and-prune was NOT observable at 4-5
  frames/s.** Three never-joined groups were streamed (40, 50, 25 frames) with a capture armed
  on the transit VLAN before two of them; **not one data frame of any reached the transit
  segment or the receiver**. The prune itself is unambiguous (empty OIF in `show ip mroute`,
  swi_a's `Join / Prune` on the wire) and **State Refresh is active** on this build
  (`PIMv2, Prune Refresh` from the DUT every ~60 s), which is precisely the feature that
  suppresses the periodic re-flood. The first-packet flood converges faster than a 0.2 s
  inter-frame gap can sample. **To measure it:** a line-rate stimulus (`tools/linerate.py` or
  tcpreplay) with a capture on the transit VLAN and per-frame timestamps, so the flood/prune
  boundary is located in time rather than counted. Not a platform fault; a stimulus limit.
- **⚠️ O-26 (T43864) — a capture on any switched VLAN of this DUT competes with a 1 Hz
  loop-detect LDF stream.** `loop-protection loop-detect ldf-interval 1 fast-block` is in the
  baseline config, so `tcpdump -i vlanN -c 24` unfiltered is consumed by 802.3/LLC
  `Null Unnumbered, test` frames in under half a minute before much protocol traffic lands —
  it wasted one capture here. Those frames carry **no IP header**, so a bare `ip` qualifier
  drops every one of them while keeping PIM, IGMP and the multicast data:
  `tcpdump -i vlanN -c 30 -nn ip`. Use `proto 103 or net 239.0.0.0/8` when the data matters too.
- **🔴 F-13 ADDENDUM (T43864) — a membership learned while the interface was snoop-only does
  NOT migrate when router-side IGMP is later enabled.** It must be re-sent. T43864 applied
  F-13's lesson in its setup and was still caught, because the baseline join preceded the
  `ip igmp` line by ~45 s; the first forwarding leg read 0/10 for a group that looked joined,
  and an identical leg after a re-join read 10/10 with nothing else changed. A tester enabling
  `ip igmp` on a live bench must re-join every group.
- **🟢 O-24 (T43863) — the sticky `no service <proto>` rule (x960.md §7A.2) reproduced side by
  side on the x960, and it is narrower than a reader might fear.** The same teardown commands
  were sent to both units within one minute. The **DUT** keeps `no service pim` in
  running-config, because it had BOOTED from `flash:/ck43863.cfg` (which contained
  `service pim`) during the reboot-persistence limb. **swi_a keeps nothing at all** — its
  post-teardown running-config holds only `service password-encryption, service ssh,
  no service telnet, service http, no service dhcp-server`, exactly as before the group — because
  it never rebooted. ⇒ the discriminator is **the boot, not the daemon**, confirmed on a second
  platform. Note both units answer `% Save the config and restart for this change to take
  effect.` to `no service pim`, which is an **advisory, not a rejection** — `cfg.py` stops at
  it, so never put commands after it in one batch.

- **🟢 O-20 (group C setup) — `service <proto>` gives a CLEAN licence verdict; `show ip pim …`
  does not.** The campaign spent two rounds of reasoning on whether swi_b's Base licence can run
  PIM, because every read-only instrument available to TRIAGE is ambiguous: the `service ?` list
  offers `pim`, `pdm` and `pim6` **identically on all three units** regardless of licence, and
  the refusal `% PIM-SM protocol daemon is not running or feature license is not available`
  names both causes at once (x960.md §7A.1 warns it is a red herring in both directions).
  **`service pim` itself answers in one line and names only the licence:**
  `% Service is not currently licensed on this platform`. Same for `service pdm`. Measured on
  swi_b 2026-10-16 16:18:48 and 16:19:25 NZDT; **nothing was applied** (a refused `service` line
  leaves no config). ⇒ **To settle "does this unit hold feature X" on AW+, send `service <x>`
  alone and read its answer — never the feature's own `show`.** It is a one-line, zero-residue
  probe, but it IS a device-state change, so it is a RUN-mode action, not a TRIAGE one.
  Consequence for this campaign: **swi_b cannot be a PIM neighbour and swi_a is group C's
  partner**, under RISK-1 (config only, never reloaded).

### New from group A (T43870, 2026-10-16). Next free numbers were F-12 and O-9.

- **F-12 (T43870) — an SNMPv3 GetNext at a MIB-view boundary gets NO response at all.** RFC 3416
  §4.2.2 requires the varbind back with `endOfMibView`. Measured on
  `sin_x96056-20261012-24` with a 5 s timeout and 3 retries, between two in-view GetNexts
  answered in milliseconds and permitted GETs answered before and after, so it is not slowness
  or a dead agent. A **GET** of an out-of-view OID is handled correctly (`noSuchObject`); only
  **GetNext** is silent. ⇒ `snmpwalk` against any view-restricted SNMPv3 user cannot terminate
  cleanly — it stalls at the view boundary and ends in a client timeout. **Worth a developer's
  eye.** Evidence: `T43870/work/s6-outofview-getnext.log`.
- **O-9 (T43870) — the AUTHORED CASE is defective, not the platform.** T43870's precondition
  configures `snmp-server group ADMINadminADMINadmin priv read MOSTmostMOSTmostMOST …` but the
  only view it defines is `system`; `MOSTmostMOSTmostMOST` is never created. Applied verbatim,
  the DUT accepts it silently and then denies **every** read, so authored step 4 FAILS and the
  case can demonstrate nothing. Supplying the one missing line
  `snmp-server view MOSTmostMOSTmostMOST 1.3.6.1.2.1.1 included` makes all nine steps behave
  exactly as authored. Secondary: step 6's OID is typed `1.3.6.1.1.2.1.1.5`, which is not
  sysName. **Recommended fix to the case:** rename the view in the config block, correct the
  step-6 OID. Evidence: `T43870/work/s3-legA-verbatim.log`.
- **O-10 (T43870) — `no snmp-server view <name>` deletes the WHOLE view.** The positive form is
  per-OID (`snmp-server view NAME OID included|excluded`) but the negation takes only the name;
  `no snmp-server view NAME OID` is `% Invalid input`. There is no way to withdraw one OID entry
  from a view. Same shape for `no snmp-server user <name>` and `no snmp-server group <name>`.
  A teardown that mirrors its setup line-for-line will fail. Evidence: `work/s20-removal.log`
  (the rejections) and `work/s21-qmark-no.log` (the `?` probe that settled the syntax).
- **O-11 (T43870) — `show snmp-server user` has no column separator at maximum name length.**
  20-character names run together: `TESTtestTESTtestTESTADMINadminADMINadminmd5          des`.
  Cosmetic, but not parseable by whitespace.
- **O-12 (T43870) — a message that fails DES decryption gets no response.** RFC 3414 §3.2(8)
  expects `usmStatsDecryptionErrors` and a report PDU. The access outcome is correct (denied)
  and silence is a common implementation choice, so this is an observation, not a defect. Same
  silence family as F-12.

- **🟢 RISK-7 CAN BE CLOSED.** `tools/tb` did not work on tb277 because the box's `python3` is
  3.6 (`bench_probe.py` dies with `TypeError: __init__() got an unexpected keyword argument
  'capture_output'`). Fixed generically instead of worked around: `tb277` was added to the
  wrapper's `BOX_PY` map so it selects `python3.8`, exactly as `tb105` already did. **Every gate
  and every console step of group A then went through `tools/tb`** (Ask-CK decision D6). Groups
  B, C and D should use it too — no hand-built `SSH_AUTH_SOCK=… ssh` lines are needed on tb277
  any more.
- **🟢 Three new generic tools are in `tools/` with README entries**, for groups B-D and future
  campaigns: `ckcase.py` (authored case text from ck.db `zephyr_cases` in one command),
  `snmpq.py` (classifying net-snmp wrapper with `--expect` grading), `snmpwire.py`
  (dependency-free pcap SNMP decoder: ENCRYPTED vs PLAINTEXT `msgData`).
- **🔴 PLATFORM TRAP for any later SNMP work:** `show snmp-server` reports **SNMPv3
  Authentication Max Fail 5 / Lockout Time 300 Seconds**. Every credential-failure probe must be
  **one attempt** (`--retries 0`); a careless `-r 3` locks the user out for five minutes and
  every later leg then reads as a product failure.

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
