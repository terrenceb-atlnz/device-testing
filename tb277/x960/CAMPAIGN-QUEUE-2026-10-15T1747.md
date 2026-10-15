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
| A | T33248 Static ARP · T33247 Clear ARP · T33249 ARP Logging · T33246 ARP Polling · T43848 Proxy ARP · T43849 Local Proxy ARP | arp-2026-10-15T1747 | **DONE 2026-10-15T2000 — 6 PASS, bench restored and re-probed (exit 0, all three configs identical to the pre-campaign capture)** | DUT + both host NICs. Two L3 segments (eth3/VLAN 10, eth4/VLAN 48) give proxy ARP its two sides without a partner. Run first: it is the least topology-hungry and it proves the bench before the routing underlay goes in |
| B | T43855 IPv4 Static · T43861 ECMP Routing · T43862 Secondary IP Address | static-2026-10-15T1747 | **DONE** 21:21 — 3 PASS (underlay + restore recipe below; underlay stays up for C and D) | Needs the routing underlay (below) and both partners. ECMP uses the DUT's **two** links to one partner, or one link to each — the triangle gives equal-cost paths either way |
| C | T43857 OSPFv2 · T43856 RIP v1/v2 | igp-2026-10-15T1747 | RUNNABLE (triaged 2026-10-15T1805) | Same underlay as B. `service ospf` / `service rip` FIRST |
| D | T43858 BGPv4 · T43859 VRF-Lite | bgp-vrf-2026-10-15T1747 | RUNNABLE (triaged 2026-10-15T1805) | Same underlay. `service bgp` first. VRF-Lite may need a feature the DUT lacks — that is UNSUPPORTED **with the refused command quoted**, after the service gate has been ruled out |

**Group order is deliberate.** A runs on a bench almost identical to the one just restored. B, C
and D then share **one L3 underlay** built once (STANDING-ORDERS §6: bench setup is set once per
TestSet), with each group layering only its own protocol on top and removing it afterwards. That
keeps three groups from rebuilding the same addressing three times.

**Triage ran 2026-10-15 18:05 NZDT — see `## Triage result` below. 13 runnable, 0 blocked.**

~~Triage has NOT run yet.~~ The tester triages all thirteen rows against the bench before
anything is configured, and the result is recorded here. Under the unattended rule the campaign
then proceeds with the runnable cases automatically instead of asking.

## Triage result — 2026-10-15 18:05 NZDT, by the bench-runner tester (TRIAGE dispatch)

**13 runnable now · 0 blocked by topology · 0 blocked by anything else.**
Nothing was changed on the bench: `bench_probe.py run` (exit 0), read-only `qmark.py` help probes
(no CR — `<cmd> ?` then Ctrl-U; self-test passed every time), and `cfg.py` `show` commands only.
`show running-config` on swi_d after all of it is **byte-identical** to the probe capture
(`captures/2026-10-15T045216Z/u2.show_running-config.txt`). All three consoles were left at the
exec prompt with `terminal no monitor`, verified from the transcripts
(`/tmp/rt1747/console-u{2,3,5}.log`), not from tool stdout.

### Gate record

| gate | result |
| --- | --- |
| 1 occupancy | `precheck` exit 5, **u2/u3/u5 all `free`**; the one FOUND item is `ser2net` pid 744 (root, up 34 d), the box's console-server daemon. Proceeded per dispatch |
| 2 consoles parked | none. All three logged in cleanly to an exec prompt at the recorded baud |
| 3 template path | **no `tb277.setup.current` exists** — tb277 has never had a `.setup` applied (`apply` needs `/nfsHome`, which is root ⇒ the Test Engineer's; still open from 10-15) |
| 4 probe | `python3.8 bench_probe.py --box tb277 run --consoles u2,u3,u5 --no-prompt --pdu 10.36.230.212 --outlet u2=1,u3=7,u5=3@10.36.230.35` → **exit 0**, Advisories: **none**, no USER-CONFLICT. `bench-state.md` regenerated at `2026-10-15T045216Z` |
| 5 the run's `.setup` | n/a — no template, so **no framework run is possible on tb277**. All 13 cases are manual console + scapy, as the 14:58 campaign was |
| 6 pt_preflight | n/a (no `.setup`, no generated script) |
| 7 boot baseline | swi_d `flash:/x960-tb277.rel` + `flash:/default.cfg`, **both exist** — the DUT is safe to reload. swi_b `flash:/backup.rel` exists. swi_a see RISK-1 |
| 8 Ask-CK server run path | n/a |
| 9 sentinel | `sentinel: parent`, nothing to arm |
| 10 CLI surface | every command all 13 cases need was confirmed present by read-only `?` probe — see the table below |

### TPS: all thirteen are priority 1 / Yes

`https://wiki.atlnz.lc/awpwiki/index.php?title=X960_platform_support_TPS&action=raw`, rows
17–24 (ARP) and 31–38 (Unicast Routing). Verbatim, every one `priority 1`, `Yes`, note column empty:

| TPS row | feature | case |
| --- | --- | --- |
| 18 | ARP Polling | T33246 |
| 19 | Clear ARP | T33247 |
| 20 | Static ARP | T33248 |
| 21 | ARP Logging | T33249 |
| 23 | Proxy-ARP | T43848 |
| 24 | Local Proxy-ARP | T43849 |
| 31 | IPv4 Static routing | T43855 |
| 32 | RIP v1/v2 | T43856 |
| 33 | OSPFv2 | T43857 |
| 34 | BGP-4 | T43858 |
| 35 | VRF-Lite | T43859 |
| 37 | ECMP (Equal-cost Multi-Path) routing | T43861 |
| 38 | Secondary IP Address (Multi homing) | T43862 |

⇒ **No case may be graded UNSUPPORTED without DUT evidence**, and none needs to be: every command
is present (next table).

### CLI surface, measured on swi_d by read-only `?` probe

| case | command(s) | present? |
| --- | --- | --- |
| T33248 Static ARP | `arp A.B.C.D` (config) | yes |
| T33247 Clear ARP | `clear arp-cache [A.B.C.D\|global\|vrf]` (exec) | yes — note it is `clear arp-cache`, **not** `clear arp` (that only takes `security`) |
| T33249 ARP Logging | `arp log` (config) | yes |
| T33246 ARP Polling | `auth-web-server ping-poll type arp` + `auth-web enable` (if) + `radius-server local` | yes — **see FINDING-A** |
| T43848 Proxy ARP | `ip proxy-arp` (if) | yes |
| T43849 Local Proxy ARP | `ip local-proxy-arp`, also `ip limited-local-proxy-arp` (if) | yes |
| T43855 IPv4 Static | `ip route A.B.C.D/M` | yes |
| T43861 ECMP | `maximum-paths <1-8>` (config) | yes |
| T43862 Secondary IP | `ip address A.B.C.D/M secondary` (if) | yes |
| T43857 OSPFv2 | `service ospf`, `router ospf`, `ip ospf` (if) | yes |
| T43856 RIP v1/v2 | `service rip`, `router rip`, `ip rip` (if) | yes |
| T43858 BGPv4 | `service bgp`, `router bgp` | yes |
| T43859 VRF-Lite | `ip vrf WORD`, `ip route vrf`, `show ip route vrf`, `arp vrf` | yes |

**The service gate is ruled out before any run:** `service ?` on swi_d lists `bgp`, `ospf`, `rip`
(and `ospf6`, `ripng`, `pim`, `bfd`, `vrrp`). Both partners list the same. Nothing here can be
called UNSUPPORTED for want of a `service` command.

### FINDING-A (resolved, record it) — "ARP Polling" is web-auth ARP polling, and the CLI is not what the TFS proposed

TPS row 18 "ARP Polling" is **Project 2561, "ARP-polling for Web Auth"**
(`https://wiki.atlnz.lc/awpwiki/index.php?title=ARP-polling_for_Web_Auth_TFS&action=raw`): the
device sends *directed* ARP requests to an authenticated web-auth supplicant and deauthenticates
it after `failcount` unanswered requests. It is **not** a generic ARP-cache refresh feature, and
there is no `arp polling` anywhere under `arp ?` (config), `arp ?` (interface) or `ip arp`.

The TFS's MRS text proposes `auth-web-server [arp-poll | ping-poll] enable`. **That syntax does
not exist on the DUT** — `auth-web-server arp-poll ?` → `% Unrecognized command`. The shipped
syntax is:

```
auth-web-server ping-poll type { arp | ping }     # "arp  Enable polling via ARP"
auth-web-server ping-poll { enable | interval | timeout | failcount | reauth-timer-refresh }
```

TFS revision 0.3 (28/Apr/2021) is logged as "Change configuration syntax", so the shipped CLI is
the intended one and **this is not a product defect** — but anyone grading T33246 against the TFS
text verbatim would wrongly call it absent. Defaults read off the CLI help: interval 30 s,
timeout 1 s, failcount 5.

### Licences — clear, nothing to request

| unit | licences | consequence |
| --- | --- | --- |
| swi_d (DUT) | Base + **`atlnz`** (ATL-NZ internal, Full) | has `VRF-LITE-FULL`, `VRF-LITE-63`, `VRF-LITE-8`, `BGP-FULL`, `OSPF-FULL`, `RIP-256`, `No-Tier-Check`. **Nothing in this campaign is licence-blocked on the DUT** |
| swi_a (u5) | Base + **`full`** (ATL-NZ internal) | same breadth |
| swi_b (u3) | **Base License only** | `BGP-64`, `OSPF-64`, `RIP`, `L3-FORWARDING`, **no VRF-Lite**. Fine as an IGP/BGP peer; keep swi_b-facing route counts **≤ 64**, and **do not make swi_b a VRF peer** |

Why this mattered: the TPS feature-licence matrix (§"Feature Licenses", X960-28YSQ) puts
**VRF-Lite <64 instances under `AT-FL-x960-01`, not under x960 Base** (OSPF/BGP ≤64 routes and
Static Routing 1024 routes *are* Base). The DUT's `atlnz` licence covers it, so T43859 is runnable
— but on a Base-only x960 it would not be.

### ck.db — one case has step text, twelve do not

Exact-title lookup against `/home/terrenceb/claude/Test-cases/ask-ck/db/ck.db` (read-only URI,
`python3.8` on the box; no `sqlite3` binary there) for all 13 queue titles:

- **T43849 "Local Proxy ARP: Functionality" → `AWP-4357` / internal_id 25060, unique, `steps_text`
  517 chars.** Use it. Quoted in full:
  > Configure DUT and BackupSW / Connect both SW via VLAN 23 / Configure DUT as follows: interface
  > VLAN23, iP address 23.1.1.1/24, ip local-proxy-arp / Configure BackupSW as follows: interface
  > VLAN23, ip address 23.1.1.2/16 / From BackupSW, ping 23.1.1.3 / Expect ping to fail, but with
  > ARP using DUT MAC address. DUT responds to ARPs on an interface for other IP hosts that would
  > be on the same interface. This is a "one armed router" situation eg when private vlans are
  > configured. DUT MAC address will be saved on BackupSW ARP table
- The other **twelve have no exact title** in ck.db. Ground them in the TPS row + the Feature
  Overview Guide + the TFS, per the queue's rule.
- Useful *reference* rows found by LIKE (same feature family, **not** these cases — do not present
  them as the case's steps): `AWP-4336/4337/4341/4342/4351` Static ARP, `AWP-4339` "ARP Commands:
  Clear ARP", `AWP-4353/4354/4355` Proxy ARP, `AWP-4356/4358` Local Proxy ARP,
  `AWP-8284/8285/8286` Secondary IP Address Assignment, `AWP-13667` "ECMP Default Maximum-Path
  Value", `AWP-22032` "IPv4 ECMP Test".

### Feature Overview Guides present at the repo root

`ip_feature_overview_guide.pdf` (covers static ARP, ARP aging, deleting ARP entries, Proxy ARP
p6, Local Proxy ARP p9, ARP logging p9, secondary addressing p3), `OSPF_…`, `RIP_…`,
`Route_Selection_…` (ECMP), `VRF_Lite_…`.
**There is no BGP Feature Overview Guide** — T43858 must be grounded in the TPS row plus the wiki
/ TFS instead. Note: the IP guide contains **no** mention of "polling"; T33246's grounding is the
Project 2561 TFS, not this guide.

### Bench facts the groups must carry

Host NICs (measured): `eth2` 10.38.22.1/27 carrier up, **nothing learned — not usable**;
`eth3` 10.38.22.33/27 → swi_d `port1.0.10`; `eth4` 10.38.22.65/27 → swi_d `port1.0.48`.
**Both usable NICs land on the DUT**, so there is no scapy host behind a partner: every far-side
count is either a hairpin back through the DUT to eth4, or a per-port interface counter on the
partner.

Clocks read 18:00 NZDT (box 05:00:09 UTC):

| unit | reads | offset |
| --- | --- | --- |
| swi_d u2 | 05:00:07 UTC | −2 s |
| swi_a u5 | 04:58:45 UTC | −1 m 24 s |
| **swi_b u3** | **17:59:46 "UTC"** | **+12 h 59 m 39 s** — it shows NZDT wall clock while labelled `Timezone: UTC` |

### RISKS — none blocks a case, all must be handled at group setup

- **RISK-1 (OPEN-1) swi_a must not be reloaded or power-cycled.** `Current boot image: Not set`,
  `Current boot config: flash:/default.cfg (file not found)`, autoboot disabled; it is running
  `x950GEN2-tb277.rel` from a netboot. **No case in this queue needs a partner reboot** — every
  reboot-persistence limb runs on the DUT, which flash-boots `flash:/x960-tb277.rel` with
  `flash:/default.cfg` present. ⇒ Use **swi_b as the primary routing partner**; use swi_a only as
  the second ECMP/IGP path. If swi_a must be touched, change config only, never power.
- **RISK-2 swi_b carries pre-existing config on a DUT link.** `vlan 100`, `port1.0.2` and
  `port1.0.4` in `static-channel-group 1` + `switchport access vlan 100`, `port1.0.8` in vlan 100,
  `interface sa1` in vlan 100, `eth0 169.254.42.42/16`. **`port1.0.2` is one of the two swi_b↔swi_d
  links.** ⇒ Prefer **swi_b `port1.0.16`** (clean both ends) for the swi_b leg and leave `sa1`
  untouched; take the pre-case `show running-config` of swi_b and diff it at teardown either way.
- **RISK-3 `lacp global-passive-mode enable` is set on all three units.** A port freed from an
  aggregator can auto-enrol, and the link then forwards where STP cannot block
  (memory `lacp-passive-hides-links-from-stp`). After any port change check
  `show static-channel-group` and `show etherchannel summary` on **all three**.
- **RISK-4 RSTP is on all three with six links in a doubled triangle**, so something is blocked
  today. Give every routed leg **its own VLAN** so each VLAN carries exactly one link; confirm
  with `show spanning-tree brief` before measuring, never after.
- **RISK-5 swi_b's clock is ~13 h ahead while both ends say `UTC`.** Correlating an ARP log,
  an OSPF adjacency or a BGP timer across swi_b and the DUT silently gives a wrong answer.
  ⇒ At group setup run `clock set <hh:mm:ss> 15 Oct 2026` on swi_b, record that it was done and
  the offset it replaced; or quote every swi_b timestamp with the offset applied. **State the
  offset in every working log.**
- **RISK-6 no `.setup` on tb277 ⇒ no framework.** All 13 are manual. There is therefore also no
  framework post-failure PDU cycle; a failed case leaves the bench exactly as the case left it,
  so each case's own teardown is the only restore.
- **RISK-7 `tools/tb` does not work on tb277** (box `python3` is 3.6). Every tool runs as
  `python3.8` over a hand-built ssh — the standing exception already in force on this box since
  10-08. One driver process per device, never two at once on the same `/dev/uN`: two readers give
  `device reports readiness to read but returned no data`, which reads exactly like a dead unit.

### Per-case verdict and what each needs

**Group A `arp-2026-10-15T1747` — 6 runnable. DUT + host NICs only; no partner, no reload of anything but the DUT.**

| case | runnable | bench it needs |
| --- | --- | --- |
| T33248 Static ARP | yes | VLAN 10 on `port1.0.10`, `interface vlan10 ip address 192.168.10.1/24`, eth3 192.168.10.2. `arp 192.168.10.9 <mac> port1.0.10`; prove the entry is Static in `show arp`, that a crafted frame to it egresses `port1.0.10` with that destination MAC, that `no arp …` removes it from running-config, and that it survives a DUT reload staged on a named boot config |
| T33247 Clear ARP | yes | same segment. Populate the cache with scapy, then `clear arp-cache`, `clear arp-cache 192.168.10.2`, `clear arp-cache global`. Grade on the cache **and** on the DUT re-ARPing on the wire, with a static entry present as the control that must survive |
| T33249 ARP Logging | yes | same segment + `arp log`. Grade on log lines produced by *crafted* ARP, with a baseline OFF leg first; `terminal monitor` is exec-only (memory `terminal-monitor-exec-only`) |
| T33246 ARP Polling | yes — **run it LAST in the group** | heaviest by far: `auth-web enable` on `port1.0.10`, `auth-web-server ipaddress`, a `radius-server local` user, a web-auth login driven from the box with `curl`, then `auth-web-server ping-poll type arp` + `enable` + a short `interval`/`failcount`. Measure the **directed** ARP requests on eth3 with tcpdump (the TFS requires dst-MAC = supplicant's, not broadcast), then stop answering and show the deauth after `failcount`. Control leg: `type ping` must produce ICMP, not ARP |
| T43848 Proxy ARP | yes | two segments: VLAN 10 (`port1.0.10`/eth3) and VLAN 48 (`port1.0.48`/eth4), DUT routing between them. eth3 given a deliberately wide mask so a VLAN-48 address looks on-link; scapy-craft the ARP request and read **who answers and with which MAC**. Baseline leg with `no ip proxy-arp` (default) must get no answer |
| T43849 Local Proxy ARP | yes — **has real step text (AWP-4357)** | one segment, two hosts: put **both** `port1.0.10` and `port1.0.48` in VLAN 23, `interface vlan23 ip address 23.1.1.1/24 ip local-proxy-arp`; eth3 `23.1.1.2/16` (wide mask, as the step says), eth4 `23.1.1.4/24`. scapy-ARP from eth3 for `23.1.1.3` → expect the DUT's MAC. Deviation from the step text, deliberate: the host NIC stands in for "BackupSW" so the ARP is crafted and counted rather than inferred from a ping (STANDING-ORDERS §7) |

**Groups B, C, D share ONE L3 underlay, built once (STANDING-ORDERS §6).** Proposed, each leg its own VLAN so RSTP blocks nothing:

```
DUT  vlan10  port1.0.10   192.168.10.1/24      (host eth3 = source)
DUT  vlan48  port1.0.48   192.168.48.1/24      (host eth4 = sink)
DUT  vlan41  port1.0.4    10.0.41.1/30   <-> swi_a port1.0.4   10.0.41.2/30
DUT  vlan42  port1.0.14   10.0.42.1/30   <-> swi_a port1.0.14  10.0.42.2/30
DUT  vlan61  port1.0.16   10.0.61.1/30   <-> swi_b port1.0.16  10.0.61.2/30
(swi_b port1.0.2 left alone — it is in static-channel-group 1, RISK-2)
```
**🔴 Restore, CORRECTED from T43849's measurement (2026-10-15 19:24) — the carried-over recipe was
wrong.** `no interface vlanN` is **refused on this build** with `% Removal of interface not
allowed` *even with the address removed AND every member port moved out*. What actually removes
the SVI is **`vlan database` / `no vlan N`**. The order that works:
```
interface port1.0.X / switchport access vlan 1      # every member port out of the VLAN first
interface vlanN / no ip address
vlan database / no vlan N                           # this removes the SVI too
```

| case | runnable | bench it needs |
| --- | --- | --- |
| T43855 IPv4 Static | yes | DUT + swi_b over vlan61. Static route on the DUT to a prefix that lives only on swi_b; prove forwarding with crafted frames plus a control flow to an unrouted prefix that must be dropped; prove `no ip route` removes it from both running-config and the FIB; prove persistence across a DUT reload |
| T43861 ECMP | yes | **use the swi_a pair** (`port1.0.4` + `port1.0.14`, clean at both ends) for the two equal-cost next-hops `10.0.41.2` and `10.0.42.2` to one prefix. `maximum-paths` is `<1-8>`. Grade by **varying the 5-tuple over many flows and counting per egress port** on the DUT's tx counters *and* swi_a's rx counters; hairpin the prefix back through swi_a to the DUT and out vlan48 so eth4 gives a scapy far-side count too. Control: `maximum-paths 1` must collapse everything onto one port. `show ip route` is a read-back, never the evidence |
| T43862 Secondary IP | yes | DUT + eth3 only. `interface vlan10 ip address 192.168.10.1/24` then `ip address 172.16.10.1/24 secondary`; eth3 given an address in each subnet; prove the DUT answers ARP and routes for **both**, that removing the primary is refused or drops the secondary as documented, and that `no ip address … secondary` removes it |
| T43857 OSPFv2 | yes | `service ospf` **first** on DUT and swi_b (and swi_a if a second neighbour is wanted). swi_b is `OSPF-64`, so keep advertised routes **≤ 64**. Prove adjacency Full, a route learned via OSPF (not static), forwarding on the wire, then **withdraw** the route and prove the traffic stops. `no service ospf` lingers until reload — do not grade on it |
| T43856 RIP v1/v2 | yes | `service rip` first. Both v1 and v2 behaviour (`version 1` / `version 2`), swi_b as neighbour. Same evidence shape as OSPF |
| T43858 BGPv4 | yes | `service bgp` first; `router bgp <asn>` on DUT and swi_b (eBGP across vlan61 is simplest). swi_b is `BGP-64` ⇒ keep ≤ 64 prefixes. **No Feature Overview Guide exists for BGP** — ground the steps in TPS row 34 and the wiki. Prove the session Established, a prefix learned via BGP, forwarding, then withdrawal stopping it |
| T43859 VRF-Lite | yes | **DUT + both host NICs only — do not make swi_b a VRF peer** (Base licence, no VRF-Lite). `ip vrf red` / `ip vrf blue`, `port1.0.10`/vlan10 into red, `port1.0.48`/vlan48 into blue. Prove isolation first (a crafted frame from eth3 to eth4's address must **not** cross, and `show ip route vrf red` must not hold blue's prefix), then add a route inside one VRF and prove it does forward. The DUT holds `VRF-LITE-FULL`, `VRF-LITE-63`, `VRF-LITE-8` |

### Recommended dispatch order

A → B → C → D, as the queue has it. Within A, run T33246 **last**: it is the only case needing
web auth + RADIUS + an HTTP login, and a problem there must not delay the five cheap ARP cases.
Build the B/C/D underlay once at the start of B and leave it up through D, removing only each
group's own protocol.

## Group A bench setup and restore — `arp-2026-10-15T1747` (written 2026-10-15 18:15 NZDT, before case 1)

**Per `/test-mode` §2 and STANDING-ORDERS §6: set ONCE before the group, restored ONCE after it.**
A fresh tester must be able to restore the bench from this section alone.

### What the group changes

Only **swi_d (the DUT, /dev/u2 @115200)**, except T43849, which also touches **swi_b
(/dev/u3 @9600)** and restores it inside its own case. **swi_a (/dev/u5) is never opened or
touched by group A** (RISK-1: it netboots with `flash:/default.cfg` not found).

Two routed segments, one per host NIC, each its own VLAN so RSTP blocks nothing (RISK-4):

```
tb eth3 00:0d:b9:55:77:0e (10.38.22.33/27)  ── swi_d port1.0.10  → VLAN 10, interface vlan10 192.168.10.1/24
tb eth4 00:0d:b9:55:77:0f (10.38.22.65/27)  ── swi_d port1.0.48  → VLAN 48, interface vlan48 192.168.48.1/24
```

The host NICs keep their own `10.38.22.x/27` addresses and **no host networking is changed at
any point** — every frame is crafted at L2 by `tools/arpleg.py`, so the kernel's addresses and
routes are bypassed entirely and the two private subnets stay quiet. That also means `192.168.10.2`
and `192.168.48.2` are **scapy fictions**, not host addresses.

### SETUP — swi_d, apply once before case 1

```
configure terminal
vlan database
 vlan 10,48
 exit
interface port1.0.10
 switchport access vlan 10
 exit
interface port1.0.48
 switchport access vlan 48
 exit
interface vlan10
 ip address 192.168.10.1/24
 exit
interface vlan48
 ip address 192.168.48.1/24
 exit
end
```

### RESTORE — swi_d, apply once after case 6 (and after any abort)

**🔴 CORRECTED 2026-10-15 19:24 from T43849.** `no interface vlanN` is refused on this build
(`% Removal of interface not allowed`) **even after the address is removed and every member port
is moved out**. `vlan database` / `no vlan N` is what removes the SVI. Ports out FIRST, then the
address, then the VLAN:

```
configure terminal
interface port1.0.10
 switchport access vlan 1
 exit
interface port1.0.48
 switchport access vlan 1
 exit
interface vlan10
 no ip address
 exit
interface vlan48
 no ip address
 exit
vlan database
 no vlan 10
 no vlan 48
 exit
vlan database
 no vlan 10,48
 exit
end
show boot                 ! must read Current boot config: flash:/default.cfg (file exists)
dir flash: | include ck   ! must list NO ck*.cfg -- delete any that a reboot limb staged
```

**Both ports MUST end as untagged VLAN 1.** `bench_probe.py`'s host-MAC discovery depends on
exactly `port1.0.10` and `port1.0.48` learning the host MACs, and the post-run probe will not
reproduce the recorded links otherwise (2026-10-15 handover).

Nothing in group A is written to `startup-config`. The reboot-persistence limbs stage a **named**
boot config instead and put the pointer back:

```
copy running-config flash:/ck<ID>.cfg
configure terminal / boot config-file flash:/ck<ID>.cfg / end
reload                                        ! answers (y/n) -- send `y\r`
# ... re-measure on the wire ...
configure terminal / boot config-file flash:/default.cfg / end
delete flash:/ck<ID>.cfg
```

### Per-case deviations from the group setup, each restored inside its own case

| case | deviation | restored by |
| --- | --- | --- |
| T43849 Local Proxy ARP | adds **VLAN 23** on swi_d `port1.0.10` + `port1.0.16`, `interface vlan23 23.1.1.1/24` + `ip local-proxy-arp`; on **swi_b** `port1.0.16` access VLAN 23 + `interface vlan23 23.1.1.2/16` (the /16 is the point of the case). `port1.0.10` leaves VLAN 10 for the case and returns to it | the case's own teardown, on **both** devices, each diffed against its pre-case `show running-config`. swi_b `sa1` / `port1.0.2` / `port1.0.4` / `vlan 100` are **not touched** (RISK-2) |
| T33246 ARP Polling | re-addresses `interface vlan10` to **10.38.22.34/27**, inside the box's existing `eth3` subnet, so `curl` can reach the DUT's web-auth server **with no host networking change**; adds `auth-web`, `auth-web-server`, `radius-server local` | the case's own teardown, which puts `192.168.10.1/24` back |

### The instrument

`tools/arpleg.py` (new this group, catalogued in `tools/README.md`) runs every leg: it starts
`tcpdump` on each NIC named, sends a known count of crafted frames, stops, and prints a grouped
count with the **Ethernet src/dst of every flow**. It exits 7 if its own send count and the
capture disagree. Captures live on the box at `/tmp/ck1747/<id>/`, never on the NFS home
(root-squash yields header-only pcaps).

### If the session dies mid-group

Apply the RESTORE block above on swi_d, and — only if T43849 was in flight — the swi_b half of
its row. Then re-run the probe:

```
ssh tb277 'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 run \
   --consoles u2,u3,u5 --no-prompt --pdu 10.36.230.212 --outlet u2=1,u3=7,u5=3@10.36.230.35'
```
and diff `captures/<new>/u2.show_running-config.txt` against
`captures/2026-10-15T051005Z/u2.show_running-config.txt` (the group's pre-run baseline, 70 lines).


## Group B/C/D shared L3 underlay and restore — built once at the start of `static-2026-10-15T1747` (written 2026-10-15 20:20 NZDT, before case 1 of group B)

**Per `/test-mode` §2 and STANDING-ORDERS §6: set ONCE before group B, left up through groups C
and D, restored ONCE after group D (or after any abort).** A fresh tester must be able to
restore the bench from this section alone.

### 🔴 The triage's RISK-4 remedy was WRONG, and this block replaces it

RISK-4 said "give every routed leg its own VLAN so each VLAN carries exactly one link — nothing
blocked". **RSTP on this bench is single-instance** (`spanning-tree mode rstp` on all three), so
it computes one tree over the *physical* topology: a port in Discarding is blocked for **every**
VLAN, and per-leg VLANs buy nothing. Measured on all three devices 2026-10-15 20:13–20:15 NZDT,
before anything was changed:

```
swi_b  Root Id 8000:0000cd423029 = itself.  sa1, port1.0.1, port1.0.11, port1.0.16 all Designated Forwarding
swi_a  Bridge 8000:889d98df2602.  port1.0.1 Rootport F · port1.0.11 Alternate D · port1.0.4 Designated F · port1.0.14 Designated F
swi_d  Bridge 8000:e01aead47043.  port1.0.2 Rootport F · port1.0.4 Alternate D · port1.0.14 Alternate D · port1.0.16 Alternate D
       (port1.0.8 and port1.0.40 are Designated Forwarding with NO LLDP neighbour — far ends unknown, left alone)
```

⇒ **Every one of the DUT's three candidate routed legs was Discarding.** On each DUT↔swi_a
segment the two bridges tie on root path cost and swi_a wins the tie on the lower bridge ID, so
no VLAN scheme can free them.

**The fix used instead — two lines, both on the DUT, both reverted at the end of group D:**

| change | why |
| --- | --- |
| `spanning-tree priority 0` on **swi_d** | makes the DUT the root bridge, so **every** DUT port becomes Designated and Forwarding. Blocking moves onto swi_a's and swi_b's spare ports, which no case uses |
| `interface port1.0.2 / shutdown` on **swi_d** | the second DUT↔swi_b link. swi_b's `sa1` (RISK-2) carries swi_b port1.0.2; with it live, swi_b would root through `sa1` and put **port1.0.16 — the leg group B needs — into Alternate/Discarding**. Shutting the DUT end (never swi_b's, RISK-2) removes the choice. Group A set the precedent |
| `interface port1.0.14 / shutdown` on **swi_d** | the second DUT↔swi_a link. With the DUT as root, swi_a must block one of its two DUT-facing ports; shutting 1.0.14 makes 1.0.4 swi_a's only DUT link, so the leg is deterministic instead of decided by a port-ID tie-break |

**swi_a and swi_b get no STP change at all, and no port on either is shut.** `sa1`, `vlan 100`,
swi_b `port1.0.2/1.0.4/1.0.8` are untouched (RISK-2). swi_a is config-only, never reloaded or
power-cycled (RISK-1).

**⇒ ECMP (T43861) therefore uses ONE link to EACH partner, not the swi_a pair.** The queue's own
group-B note sanctions this ("ECMP uses the DUT's **two** links to one partner, **or one link to
each**"). Two parallel links between the same pair of bridges are a loop that single-instance
RSTP must break at one end whichever bridge is root, so the swi_a pair is not available for ECMP
on this bench without disabling spanning tree — which is not worth the storm risk unattended,
with two DUT ports (1.0.8, 1.0.40) up to unknown far ends.

### Addressing — each routed leg its own VLAN (still worth doing: it keeps the L2 domains separate)

```
tb eth3 00:0d:b9:55:77:0e ── swi_d port1.0.10  vlan10  192.168.10.1/24     (source; scapy fictions only)
tb eth4 00:0d:b9:55:77:0f ── swi_d port1.0.48  vlan48  192.168.48.1/24     (sink)
swi_d port1.0.4  vlan41 10.0.41.1/30  ──  swi_a port1.0.4  vlan41 10.0.41.2/30
swi_d port1.0.16 vlan61 10.0.61.1/30  ──  swi_b port1.0.16 vlan61 10.0.61.2/30
swi_a interface lo  10.90.90.1/32      (a prefix that exists ONLY behind swi_a)
swi_b interface lo  10.70.70.1/32      (a prefix that exists ONLY behind swi_b)
```
**No host networking is changed at any point.** `192.168.10.x` and `192.168.48.x` are scapy
fictions; every frame is crafted at L2 with the DUT's SVI MAC as next hop.

### SETUP — apply once before group B case 1

**swi_d (/dev/u2 @115200)**
```
configure terminal
spanning-tree priority 0
interface port1.0.2
 shutdown
 exit
interface port1.0.14
 shutdown
 exit
vlan database
 vlan 10,41,48,61
 exit
interface port1.0.10
 switchport access vlan 10
 exit
interface port1.0.48
 switchport access vlan 48
 exit
interface port1.0.4
 switchport access vlan 41
 exit
interface port1.0.16
 switchport access vlan 61
 exit
interface vlan10
 ip address 192.168.10.1/24
 exit
interface vlan48
 ip address 192.168.48.1/24
 exit
interface vlan41
 ip address 10.0.41.1/30
 exit
interface vlan61
 ip address 10.0.61.1/30
 exit
end
```

**swi_a (/dev/u5 @9600) — config only, never reload or power-cycle (RISK-1)**
```
configure terminal
vlan database
 vlan 41
 exit
interface port1.0.4
 switchport access vlan 41
 exit
interface vlan41
 ip address 10.0.41.2/30
 exit
interface lo
 ip address 10.90.90.1/32
 exit
ip route 192.168.10.0/24 10.0.41.1
ip route 192.168.48.0/24 10.0.41.1
end
```

**swi_b (/dev/u3 @9600) — `sa1`, `vlan 100`, port1.0.2/1.0.4/1.0.8 untouched (RISK-2)**
```
configure terminal
vlan database
 vlan 61
 exit
interface port1.0.16
 switchport access vlan 61
 exit
interface vlan61
 ip address 10.0.61.2/30
 exit
interface lo
 ip address 10.70.70.1/32
 exit
ip route 192.168.10.0/24 10.0.61.1
ip route 192.168.48.0/24 10.0.61.1
end
```

### RESTORE — apply once after group D (and after any abort)

**🔴 `no interface vlanN` is REFUSED on this build** (`% Removal of interface not allowed`) even
with the address removed and every member port moved out. **Ports out of the VLAN → `no ip
address` → `vlan database` / `no vlan N`** (corrected from T43849, 2026-10-15 19:24).
**🔴 `cfg.py` stops at the first `% ` line and abandons the rest of its batch** — send the
restore in small batches and read every batch's output, never `>/dev/null`.

**swi_d**
```
configure terminal
interface port1.0.10
 switchport access vlan 1
 exit
interface port1.0.48
 switchport access vlan 1
 exit
interface port1.0.4
 switchport access vlan 1
 exit
interface port1.0.16
 switchport access vlan 1
 exit
interface vlan10
 no ip address
 exit
interface vlan48
 no ip address
 exit
interface vlan41
 no ip address
 exit
interface vlan61
 no ip address
 exit
vlan database
 no vlan 10,41,48,61
 exit
interface port1.0.2
 no shutdown
 exit
interface port1.0.14
 no shutdown
 exit
no spanning-tree priority            ! back to the default 32768
end
show boot                 ! must read Current boot config: flash:/default.cfg (file exists)
dir flash: | include ck   ! must list NO ck*.cfg -- delete any that a reboot limb staged
```
**swi_d `port1.0.10` and `port1.0.48` MUST end as untagged VLAN 1**, or `bench_probe.py`'s
host-MAC discovery will not reproduce the recorded links.

**swi_a**
```
configure terminal
no ip route 192.168.10.0/24 10.0.41.1
no ip route 192.168.48.0/24 10.0.41.1
interface lo
 no ip address 10.90.90.1/32
 exit
interface port1.0.4
 switchport access vlan 1
 exit
interface vlan41
 no ip address
 exit
vlan database
 no vlan 41
 exit
end
```

**swi_b**
```
configure terminal
no ip route 192.168.10.0/24 10.0.61.1
no ip route 192.168.48.0/24 10.0.61.1
interface lo
 no ip address 10.70.70.1/32
 exit
interface port1.0.16
 switchport access vlan 1
 exit
interface vlan61
 no ip address
 exit
vlan database
 no vlan 61
 exit
end
```

Then re-run the probe and diff every device against its pre-group capture:
```
ssh tb277 'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 run \
   --consoles u2,u3,u5 --no-prompt --pdu 10.36.230.212 --outlet u2=1,u3=7,u5=3@10.36.230.35'
python3.8 tools/rcdiff.py /tmp/ckB/dut-pre.out  <post>     # rcdiff PRINTS diffs but EXITS 0 -- read the output
python3.8 tools/rcdiff.py /tmp/ckB/swib-pre.out <post>
python3.8 tools/rcdiff.py /tmp/ckB/swia-pre.out <post>
```
Pre-group baselines are on the box at `/tmp/ckB/{dut,swib,swia}-pre.out`, captured
2026-10-15 20:13–20:15 NZDT, and `bench-setup/tb277/captures/2026-10-15T071248Z/` in the repo.

### Nothing is written to startup-config

The reboot-persistence limbs stage a **named** boot config and put the pointer back:
```
copy running-config flash:/ck<ID>.cfg
configure terminal / boot config-file flash:/ck<ID>.cfg / end
reload                                        ! answers (y/n) -- send `y\r`
# ... re-measure on the wire ...
configure terminal / boot config-file flash:/default.cfg / end
delete flash:/ck<ID>.cfg
```

### Clocks at group B start (RISK-5), measured 2026-10-15 20:13–20:18 NZDT

| unit | `show clock` | box at that moment | offset |
| --- | --- | --- | --- |
| swi_d | 07:13:27 UTC | 07:13:36 UTC | **−9 s** |
| swi_b | 07:15:05 UTC | 07:15:07 UTC | **−2 s** (group A's `clock set` holding) |
| swi_a | 07:13:50 UTC | 07:15:33 UTC | **−1 m 43 s** ⇒ `clock set` applied at group B setup, declared as a retained change |

### Per-case deviations from the underlay, each restored inside its own case

| case | deviation | restored by |
| --- | --- | --- |
| T43855 IPv4 Static | `ip route 10.70.70.0/24 10.0.61.2` on swi_d; a staged `flash:/ckT43855.cfg` for the reload limb | its own teardown |
| T43861 ECMP | `ip route 198.51.100.0/24 10.0.41.2` + `… 10.0.61.2` on swi_d; `maximum-paths 1` for the control leg | its own teardown |
| T43862 Secondary IP | `ip address 172.16.10.1/24 secondary` on swi_d `interface vlan10`; a staged `flash:/ckT43862.cfg` | its own teardown |

### If the session dies mid-group

Apply the three RESTORE blocks above, then re-probe and diff as above.


## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |
| T33248 | PASS | static ARP proven **on the wire**: 5/5 routed frames rewritten to the configured MAC and egressed on the configured port, the DUT's own ARP for that address suppressed; control address with no entry still ARPed and forwarded 0/5; removal returns config, table AND dataplane to baseline; survives a real reload. One instrument fault found and fixed first (`tools/arpleg.py` passed `-p` to tcpdump, so a frame carrying a next-hop MAC that was not the NIC's own was invisible and the leg read "0 forwarded") — both legs re-run after the fix | tester | arp-2026-10-15T1747/T33248/work/run1.log |
| T33247 | PASS | all three implemented `clear arp-cache` forms (single address, unqualified, global) proven **in the dataplane**, not in the table: a cleared address draws broadcast ARPs and forwards 0/5 while a surviving entry forwards 5/5 with no ARP; the static entry is explicitly protected and still forwarding after every clear. Single-address and unqualified clears are distinguishable **on the wire** — after the targeted clear the DUT sent 5 ICMP host-unreachables unicast to the OTHER dynamic entry's MAC, which it could only do because that entry survived. `vrf` form recorded NOT EXERCISED (no VRF on the DUT yet; that is T43859) rather than claimed | tester | arp-2026-10-15T1747/T33247/work/run1.log |
| T33249 | PASS | `arp log` emits one line per ARP cache event for crafted traffic that produces **zero** lines with the feature off; port, VLAN, MAC and IP in each line matched against the frames in the capture, and both directions appear (`del` from the clear, `add` from the re-learn). `mac-address-format ieee` changes only the MAC rendering (`0011.2233.4402` → `00-11-22-33-44-02`) and is held as its own running-config line. Both forms removable, each proven in running-config AND in the log output after it; survives a reboot and still logs | tester | arp-2026-10-15T1747/T33249/work/run1.log |
| T43848 | PASS | with `ip proxy-arp` on vlan10 the DUT answers ARP for a vlan48 address with its **own** MAC, where the identical request drew **nothing** with the feature off; silent for an unroutable address and for the ingress interface's own subnet; the proxied address is genuinely reachable; removal and reboot persistence both proven on the wire. One four-target ARP leg replayed OFF / ON / after reload, with the DUT's own address as an instrument control in **every** leg so each zero is a measurement, not a dead instrument. **No ping anywhere** — a ping crosses vlan10→vlan48 identically with proxy ARP on or off and would have proved nothing | tester | arp-2026-10-15T1747/T43848/work/run1.log |
| T43849 | PASS | the authored expected result of ck.db **AWP-4357** met in full on hardware: swi_b's `ping 23.1.1.3` fails 100% **and its ARP table holds `23.1.1.3 → e01a.ead4.7043`, the DUT's MAC**; underneath, the crafted ARP drew **0** replies with the feature off and **3** carrying the DUT's MAC with it on. **The ping fails in BOTH states and carries no verdict on its own** — what separates them is the SOURCE of the unreachable: `From 23.1.1.2` (swi_b itself, packets never left) vs `From 23.1.1.1` (the DUT, which resolved, forwarded, then ARPed for the target itself). Also measured: local proxy ARP is bounded by the DUT interface's own /24, not the neighbour's /16 idea of on-link. Removal and reboot persistence both proven | tester | arp-2026-10-15T1747/T43849/work/run1.log |
| T33246 | PASS | "ARP Polling" on this platform is **web-auth** ping-polling (Project 2561), not a generic ARP feature. Measured: **directed (unicast)** ARP polls to the supplicant's own MAC at the configured interval; **ICMP instead** under `type ping`; deauthentication after **exactly failcount** unanswered polls (3 directed ARPs, 0 replies, then polling stops — against 5 polls / 5 replies in the answering leg); removable; survives a reboot. The deauth is attributed by the DUT's own log naming the supplicant and MAC, **not** by `authorizedSupplicantNum`, which is quoted as context only. Stimulus was `ip link set eth3 arp off` on the box — link and port stay up, which is the condition the feature exists to detect | tester | arp-2026-10-15T1747/T33246/work/run1.log |
| T43855 | PASS | static route proven **on the wire**: 5/5 forwarded against **0/5** in the baseline and **0/5** after `no ip route`, with a control flow to an unrouted prefix dropped in every leg. Removal proven in the **FIB** (`% Network not in table`), not just running-config. Three syntax forms measured (next-hop, next-hop + distance, interface form); the floating-static egress move is attributed by **swi_a's own ICMP unreachables**, and the distance-255 RIB-not-FIB rule is confirmed. Survives a real reload; teardown diffed clean on swi_d and swi_b | tester | static-2026-10-15T1747/T43855/work/run1.log |
| T43861 | PASS | ECMP proven **per egress port on four counters across three devices**, never from `show ip route`: one route = 1920/1920 on a single port; two routes = a real split; **`maximum-paths 1` collapses the identical flow set to 1280/0**; removal returns all traffic to the survivor; survives a real reload. An instrument artefact was found and corrected mid-case — varying all four 5-tuple fields by the same index correlates the two addresses the hash actually uses and gave a misleading **81/19**; decorrelated spans gave **50/50**, and the verdict rests on the corrected legs. Three product findings recorded (F-1..F-3 below), none a failure of the feature | tester | static-2026-10-15T1747/T43861/work/run1.log |
| T43862 | PASS | the secondary address proven **serving traffic**, not merely displayed: ARP **0/4** off → **4/4** on → **0/4** removed, and forwarding into the secondary subnet **0/5** → **5/5** → **0/5**; the connected route appears and disappears with it; survives a real reload. Multiple secondaries coexist; `ip address … secondary` with no primary is refused (`% Configure primary first`); removing the primary while a secondary exists is **refused, not cascaded** (`% Must delete secondary before deleting primary`). One planned discriminator was **discarded at baseline because it did not discriminate** — a frame merely *sourced* in the secondary subnet crosses the DUT with the feature off too, since forwarding is destination-based and there is no uRPF | tester | static-2026-10-15T1747/T43862/work/run1.log |

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
- **NOTICE (campaign) — occupancy check returned FOUND (exit 5) and was not escalated.**
  `/test-mode` §3 would normally stop and hand the FOUND list to the Test Engineer. The single
  item is `process 744 (root, up 34-06:35): /usr/sbin/ser2net -c /etc/ser2net.conf` — the box's
  **console-server daemon**, which is what provides `/dev/uN` in the first place, not a session
  holding a console. **All three consoles report `free`.** *What was done instead:* proceeded.
  The same FOUND item was present throughout the 14:58 campaign, which ran three hours against
  it without contention. No person is being displaced.
- **🔴 FOR THE TEST ENGINEER (T33248, does not change its PASS) — `arp <ip> <mac> alias` installs but
  never answers.** The `alias` option is refused with `% Proxy Arp is not enabled in the interface`
  unless `ip proxy-arp` is on the interface owning that subnet (measured both ways: accepted on
  vlan10 with proxy-arp on, refused on vlan48 with it off). With the dependency satisfied it appears
  in running-config and in `show arp` — but produced **no ARP reply in any configuration reachable on
  this bench**. The instrument control rules out a measurement gap: the DUT answered 3/3 for its own
  address in the same leg. *What was done instead of asking:* recorded as an observation, the case
  graded on its own subject. **This wants a developer's answer on the intended semantics of `alias`,
  not another bench leg.**
- **PLATFORM FACT (T33247) — the command is `clear arp-cache`, NOT `clear arp`.** On this build
  `clear arp` takes only `security`; a script using `clear arp <ip>` gets a parser rejection.
- **🔴 PLATFORM FACT (T33247) — this DUT does NOT learn a dynamic ARP entry from a request it merely
  answers**, not even a request for its own address, which RFC 826 says should populate the table.
  Both pre-legs left `show arp` empty after the DUT had replied. **Only a neighbour that answers the
  DUT's OWN request is learned.** Any case that assumes "send it an ARP request, now it knows you"
  will measure an empty table and read it as a failure. `tools/arpleg.py` gained a background ARP
  responder (`--answer IP=MAC --answer-iface eth3,eth4`) to populate the table properly; the same
  responder drives T33246's web-auth poll timeout. For `platforms/x960.md` at wrap.
- **TRAP (T33249) — grep `ARP_LOG`, never `arp`, over `show log`.** An "arp" grep matches the IMISH
  command-audit echo of your own `clear arp-cache`, so the feature-OFF baseline reads non-zero and
  the feature looks already enabled. The log line is
  `HSL[936]: ARP_LOG port1.0.48 vlan48 add 0011.2233.4402 (192.168.48.2)`.
- **TECHNIQUE (T33249) — the emitting process id is a cheap reboot witness.** `HSL[936]` became
  `HSL[944]` across the reload, which is independent proof the reboot was real rather than a stale
  log buffer being re-read. Reusable in any persistence limb that reads a log.
- **🔴🔴 NEEDS TEST ENGINEER (T43848) — AN UNRECORDED DEVICE IS LIVE ON THE eth3 SEGMENT.**
  A capture holds `who-has 10.38.22.33 tell 10.38.22.41` from MAC `00:0c:25:2a:a5:53`, answered by
  the box. `10.38.22.33` is the box's own eth3 address; **`10.38.22.41` and that MAC are in no bench
  record**, and `eth3` is supposed to reach only swi_d `port1.0.10`.
  **The sentinel corroborated it against the capture history, and it is not a one-off:** MAC
  `000c.252a.a553` has been learned on swi_d **`port1.0.10`** in every probe since **2026-10-09**
  (`captures/2026-10-09T035251Z`, `2026-10-11T202947Z`, and all four of 2026-10-15), and the same
  MAC also appears on **swi_b `sa1` in vlan 100** — the pre-existing aggregation flagged as RISK-2.
  So a third party sits on, or is bridged onto, the host↔DUT link this campaign measures through.
  *Did it confound anything?* **No.** All T43848 measurement is in 192.168.x, every counted frame was
  matched by target and MAC plus a `CKARPLEG` payload marker, and the stray appeared once in ~25
  captures. *What was done instead of asking:* recorded; the tester will check for an address clash
  before T33246 uses `10.38.22.34`.
  **It bears on T33246**, which plans to put the DUT's vlan10 in the box's real eth3 subnet, and on
  any future case that uses bench addressing rather than private test subnets.
- **🔴 TOOL TRAP (T43849) — `cfg.py` stops at the first `% ` line and abandons the rest of its
  batch.** The `no interface vlanN` refusal above aborted a teardown batch twice, including a
  pending `no shutdown`, leaving residue the diff then caught. Do not put a command that may emit
  a benign `% ` in the middle of a batch whose later lines matter.
- **🔴 TOOL TRAP (T43849) — `rcdiff.py` PRINTS differences but EXITS 0.** So
  `rcdiff.py ... && echo clean` prints "clean" over a dirty diff. **Read its output, never its
  exit code.** This is the same class as the `% `-line trap: a gate that tests the wrong signal.
- **BENCH CHANGE RETAINED (T43849, declared).** swi_b's clock was `+12h59m39s` ahead while
  reporting `Timezone: UTC`; it was set with `clock set <HH:MM:SS> 15 Oct 2026` and both devices
  now agree with the box to within ~4 s. **This is deliberately NOT reverted** — restoring a
  13-hour error would be restoring a fault. It is the one thing group A leaves different from how
  it found the bench. (The time-only form `clock set HH:MM:SS` is refused as `% Incomplete
  command` despite being the only form `?` offers.)
- **🔴🔴 NEEDS TEST ENGINEER (T33246, confirming and extending the T43848 finding) — the box's eth3
  is NOT a point-to-point link to swi_d `port1.0.10`.** `10.38.22.41` / `00:0c:25:2a:a5:53` is live
  on that segment and **attempted web authentication on `port1.0.10`** during this case. An ARP
  sweep of the /27 after a cache flush found it to be **the only other live address** (the lladdrs
  seen on `.34` and `.49` were stale entries). The sentinel separately confirmed that MAC has been
  learned on swi_d `port1.0.10` in every probe since **2026-10-09** and also appears on swi_b `sa1`
  in vlan 100. *Not confounding:* every counted frame in group A is matched on BOTH MACs, the
  negative legs are **zero-frame** rather than low-frame (40 s, 0 frames, twice), and the deauth is
  attributed by log line. Section 9 of T33246's working log records the whole episode.
- **🔴 NEEDS TEST ENGINEER (T33246) — swi_d `port1.0.8` is connected at 1000BASE-T and
  STP-Forwarding, and is ABSENT from `bench-state.md`'s link table.** The probe does not know what
  is on the other end. Worth identifying before any case assumes the bench's link list is complete.
- **DELIVERABLE CAVEAT (T33246) — `swi_d.cfg` is NOT a true in-run capture.** The tester missed the
  in-run save, so the identical setup was re-applied afterwards, captured, and torn down again
  (bench re-verified after). The file's own header says so, and the tester declared it rather than
  letting it pass. Every other `.cfg` in group A was saved after setup and before step 1 as
  logged-output.md §2 requires. `/create-logs` should carry the caveat into T33246's final log
  rather than presenting the file as the state the case ran under.
- **🔴 TRIAGE CORRECTION (group B, measured) — RISK-4's remedy was WRONG.** Triage said "give every
  routed leg its own VLAN — one link per VLAN, nothing blocked". **RSTP on this bench is
  single-instance**, so a port in Discarding is blocked for *every* VLAN and a new VLAN frees
  nothing. All three of the DUT's routed legs were Discarding at group B's start. Resolved with two
  **DUT-only, reversible** changes: `spanning-tree priority 0` (DUT becomes root, its ports go
  Designated/Forwarding) plus `shutdown` on `port1.0.2` and `port1.0.14`.
  **Consequence for T43861 ECMP:** the two equal-cost next-hops are now **one link to EACH partner**
  (swi_a via vlan41, swi_b via vlan61) rather than the swi_a pair triage proposed. The queue's own
  group-B note sanctions either shape. Carry this into groups C and D — they share this underlay.
- **TRAP (T43855) — `dir flash: | include <x>` is `% Invalid input`**; `dir` takes no output
  modifiers on this build. Also: a `delete` whose `(y/n)` prompt is not answered returns
  `Deletion aborted` / `% Failed to delete`, which is easy to skim past — re-`dir` to confirm.
- **🔴🔴 F-1 (T43861) — DOCUMENTATION DEFECT: ECMP on this x960 is PER-FLOW, not per-packet.**
  400 packets of a single flow all took one path. **The Route Selection Feature Overview Guide
  states the opposite for AlliedWare Plus switches.** The behaviour is normal and desirable; the
  guide is wrong. Worth raising against the document, not the product.
- **🔴 F-2 (T43861) — the ECMP hash uses IPv4 SOURCE and DESTINATION ADDRESSES ONLY.** 64 distinct
  source ports gave **zero** spread; 64 distinct destination ports gave zero spread. Undocumented,
  and it matters for any deployment whose flows differ only in L4 port — they will all land on one
  path. For `platforms/x960.md`.
- **🔴 F-3 (T43861) — an ECMP next hop with UNRESOLVED ARP is silently absent from the dataplane
  while `show ip route database` still marks it `*>`.** Seen straight after the reboot: 100% of
  traffic took the one resolved path, and the route table looked **identical** either way, until
  the other next hop was pinged. **This is the sharpest illustration in the campaign of why
  `show ip route` is a read-back and not evidence** — it is the routing-table analogue of the
  `show mirror` defect in `platforms/x960.md` §5. For `platforms/x960.md`.
- **TOOL (T43861) — `tools/ecmpflows.py`** (new, generic, catalogued): many flows with chosen
  5-tuple fields varied, and far-side attribution from **ICMP unreachable source addresses** when
  there is no scapy host behind the router — which is this bench's binding constraint. Self-tested
  before use. **Its own trap, measured:** varying every 5-tuple field by the same index correlates
  the source and destination addresses, which are the only fields this hash uses, and manufactures
  a false imbalance.
- **🔴 F-4 (T43862) — the DUT answers ARP for an address on an interface ONLY when the ARP sender
  is inside THAT address's own subnet**, symmetrically for primary and secondary. The tester's
  first ARP leg sent from the primary subnet, got silence for the secondary, **and that looks
  exactly like a defect**. It is not. Any later ARP-based leg must source from the subnet of the
  address it is asking about. For `platforms/x960.md`, alongside the group-A ARP facts.
- **GROUP B COMPLETE — 3 of 3 PASS** (T43855, T43861, T43862). The shared B/C/D underlay stays up
  for groups C and D; the tester verified it intact at hand-back.
