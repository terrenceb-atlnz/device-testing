# Campaign queue — tb277 x960-56YSQ, 13 AWPTCM routing + ARP cases, from 2026-10-15 17:47 NZDT

The ask (Test Engineer, 2026-10-15): *"Lets run the next set of test cases. I will be away so
won't be able to answer any prompts"*, with a screenshot of thirteen AWPTCM cases for
**x960-56YSQ** — seven `IPv4_UnicastRouting` and six `IPv4_ARP`.

⇒ **This campaign is exactly these thirteen.** Per the standing instruction from earlier the
same day — *"the list that I send you are the ones that you would be required to do. I won't
send you the list of test cases that have been manually done"* — there is **no reconciliation
against any other list**.

## 🔴 UNATTENDED RUN — no prompts, ever

The Test Engineer stated they are away and cannot answer prompts. For this campaign only:

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

**Session-survival risk, stated once:** in the one-session shape the tester lives inside this
session's process. If that process dies — a closed window, an editor reload, an xrdp or VPN drop
— the tester dies with it. This file and the per-case commits survive, and `/test-mode --resume`
picks up from the first row not DONE / BLOCKED, so the loss would be the case in flight. For a
future unattended run, starting inside `tmux` removes this risk.

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester.

**This file is the resume point.** A session that wakes up reads it top to bottom, continues from
the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state changes.

## Session facts

Recorded 2026-10-15 17:47 NZDT. **Not re-confirmed with the Test Engineer** — they are away by
their own instruction. Taken verbatim from the Session facts of the campaign that wrapped
fifteen minutes earlier (`CAMPAIGN-QUEUE-2026-10-15T1458.md` and
`SESSION-HANDOVER-2026-10-15.md`), which they did confirm:

Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None (full authority within tests; power cycles allowed). Unattended — see above.

Devices, measured by `bench_probe.py` 2026-10-15T041733Z (`bench-setup/tb277/bench-state.md`),
the post-restore probe of the previous campaign:

- **DUT — swi_d, /dev/u2 @115200, AT-x960-56YSQ, S/N `A2WQS700B`**, standalone Active Master,
  software **`sin_x96056-20261012-24`** (Mon Oct 12 2026), bootloader reads `Unknown`,
  **boots from FLASH** (`flash:/x960-tb277.rel`, file exists), boot config `flash:/default.cfg`
  (file exists). Its running-config is byte-identical to the start of the previous campaign.
- **partner — swi_b, /dev/u3 @9600, AT-x960-28YSQ**, S/N A10737A261700021,
  `sin_x96056-20260921-9`, boots `flash:/backup.rel` (file exists), hostname `x960-28YSQ`.
- **partner — swi_a, /dev/u5 @9600, AT-x950 GEN2-52XSTQm**, S/N A10713A262600012,
  `awplus_main-20261008-56`, **netboots**, boot image **Not set**,
  `flash:/default.cfg` **(file NOT found)** — see OPEN-1.

**🔥 This campaign is the first on tb277 to use swi_a and swi_b as live partners.** The previous
two campaigns opened only u2. Their consoles have not been driven in this bench's recorded
history, so the tester treats the first login to each as unproven: confirm the prompt, the baud
and the config state before relying on either.

Links (measured, `bench-state.md` 2026-10-15T041733Z):
```
tb eth3 (10.38.22.33/27) ── swi_d port1.0.10        swi_a 1.0.1  ── 1.0.1  swi_b
tb eth4 (10.38.22.65/27) ── swi_d port1.0.48        swi_a 1.0.11 ── 1.0.11 swi_b
tb eth2 (10.38.22.1/27)  ── (carrier up, unlearned) swi_a 1.0.4  ── 1.0.4  swi_d
                                                    swi_a 1.0.14 ── 1.0.14 swi_d
                                                    swi_b 1.0.2  ── 1.0.2  swi_d
                                                    swi_b 1.0.16 ── 1.0.16 swi_d
```
**This is a genuinely good routing bench**: the DUT has **two links to each of two partners**,
the partners are linked to each other (a triangle, so a route has a second path), and two host
NICs give a traffic source and sink. ECMP, IGP convergence and BGP all fit without a recable.

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **`logged-output.md`**. Final logs are made only by `/create-logs`, on request.
- `STANDING-ORDERS.md` applies in full. Constraints are "None", so the tester has full authority
  within the tests, including power-cycling all three units.
- **🔥 STANDING-ORDERS §7: traffic tests use scapy, not ping.** For routing this is sharper than
  usual, not softer: a successful `ping` across the DUT proves a path exists, never **which**
  path, never that the route came from the protocol under test, and never that a withdrawn route
  stopped being used. Craft the frame, send a known count, count at the far side, and send a
  **control** flow in the same run that must NOT be forwarded. `show ip route` is a read-back,
  not evidence — see `platforms/x960.md` §5, where `show mirror` read Enabled while the dataplane
  copied nothing.
  - **ECMP (T43861) in particular cannot be graded on `show ip route` or on ping.** It needs many
    flows with **varying** 5-tuples, counted per egress port, to show the hash spreading them.
    One flow proves nothing; a ping proves less.
  - **Proxy ARP (T43848/T43849) is an ARP-level question**: craft the ARP request, read who
    answers and with which MAC. A ping would hide the whole mechanism.
- **Satisfactory level of testing** (Test Engineer, 2026-10-08): the step text is the FLOOR —
  also prove removal (gone from running-config) and persistence across reboot; **baseline the
  feature OFF first**.
- **🔴 AW+ routing daemons are service-gated** (memory `awplus-service-gated-routing-daemons`):
  `% ... daemon is not running` means `service ospf` / `service rip` / `service bgp` was never
  run. `no service X` lingers until a reload. Check this BEFORE grading any protocol UNSUPPORTED.
- Nothing is written to startup-config unless a case requires it.
- Teardown verified by diffing `show running-config` against the pre-case copy, **on every device
  the case touched** — three devices now, not one.
- Gate each dependent step on proven state, never on an exit code alone; a benign `% ` advisory
  reads as failure to a stop-on-error driver (`platforms/x960.md` §5, §6.4).
- **`python3.8` for every tool on tb277.** `tools/tb` is broken there (the box's `python3` is 3.6).
- **Captures:** `sudo tcpdump -w /tmp/...` on the box, then copy and `chown`. Never
  `tcpdump -Z $(whoami)` to the NFS lab home — it yields header-only pcaps that read as
  *no traffic* (memory `tcpdump-nfs-root-squash-capture`).

## 🔴 Case steps: expect them to be absent — ground them in the feature docs

Five of the previous campaign's six cases had **no step text in AWPTCM or ck.db**, and ck.db keys
on `AWP-nnnn`, not `AWPTCM-T<id>` (memory `ckdb-case-lookup-by-title`). Assume the same here and
prove it per case rather than inventing steps. Where no step text exists, ground each step in,
and cite, these — the Test Engineer's 2026-10-08 rule (`review-feature-docs-before-testing`):

1. **Software TPS** — the X960 platform support TPS row for the feature. A row marked `Yes`
   whose command is absent on the DUT is a **finding**, not an UNSUPPORTED.
2. **The feature's TFS / functional spec**, quoted per step.
3. **The Feature Overview Guide** PDFs at the repo root in `Feature Overview Guides/`
   (gitignored, on the lab home).
4. The AW+ CLI wiki — **no x960 pages exist**; use the **x950** pages, same generation, and
   confirm anything silicon-adjacent on the DUT itself.

Read a spec **once per group**, not once per case: the previous campaign's reviews measured
re-reading as a top-three cost.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T33248 Static ARP · T33247 Clear ARP · T33249 ARP Logging · T33246 ARP Polling · T43848 Proxy ARP · T43849 Local Proxy ARP | arp-2026-10-15T1747 | QUEUED | DUT + both host NICs. Two L3 segments (eth3/VLAN 10, eth4/VLAN 48) give proxy ARP its two sides without a partner. Run first: it is the least topology-hungry and it proves the bench before the routing underlay goes in |
| B | T43855 IPv4 Static · T43861 ECMP Routing · T43862 Secondary IP Address | static-2026-10-15T1747 | QUEUED | Needs the routing underlay (below) and both partners. ECMP uses the DUT's **two** links to one partner, or one link to each — the triangle gives equal-cost paths either way |
| C | T43857 OSPFv2 · T43856 RIP v1/v2 | igp-2026-10-15T1747 | QUEUED | Same underlay as B. `service ospf` / `service rip` FIRST |
| D | T43858 BGPv4 · T43859 VRF-Lite | bgp-vrf-2026-10-15T1747 | QUEUED | Same underlay. `service bgp` first. VRF-Lite may need a feature the DUT lacks — that is UNSUPPORTED **with the refused command quoted**, after the service gate has been ruled out |

**Group order is deliberate.** A runs on a bench almost identical to the one just restored. B, C
and D then share **one L3 underlay** built once (STANDING-ORDERS §6: bench setup is set once per
TestSet), with each group layering only its own protocol on top and removing it afterwards. That
keeps three groups from rebuilding the same addressing three times.

**Triage has NOT run yet.** The tester triages all thirteen rows against the bench before
anything is configured, and the result is recorded here. Under the unattended rule the campaign
then proceeds with the runnable cases automatically instead of asking.

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |

## Issues

- **NOTICE (campaign) — session facts were not re-confirmed.** `/test-mode` §1 would normally
  ask the Test Engineer for the box, consoles, PDU and constraints before touching anything.
  They are away and cannot answer, so the facts above were taken verbatim from the campaign that
  wrapped at 17:46 the same day. *What was done instead:* proceeded with the recorded facts, and
  the first probe re-measures the bench against them — a disagreement becomes a USER-CONFLICT
  notice and BLOCKs only the cases that depend on the disputed fact.
- **NOTICE (campaign) — the multi-hour / tmux question was not asked.** `/test-mode` §1.3 would
  normally stop and ask before arming anything. *What was done instead:* the risk is stated at
  the top of this file and the campaign proceeds, since running while away is what was asked for.
- **OPEN-1 (carried from 2026-10-12 and 2026-10-15).** swi_a netboots and its
  `flash:/default.cfg` reads **(file not found)**. Any case that reloads or power-cycles swi_a
  must confirm it can boot first. Do not reload swi_a casually.
- **OPEN-5 (carried from 2026-10-15).** The DUT's `flash:/default.cfg` is not pristine: it
  carries `ip dhcp-client vendor-identifying-class` and `ip dhcp-client request
  vendor-identifying-specific` on `interface vlan1`. Harmless here, but it means "default config"
  on this unit is not the factory default — diff against the **recorded** pre-case copy, never
  against an assumed default.
