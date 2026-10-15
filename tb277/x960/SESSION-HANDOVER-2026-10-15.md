# Session handover — tb277 / x960-56YSQ — 2026-10-15

## Session facts
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 (swi_d, DUT), u3 (swi_b), u5 (swi_a) — **only u2 was ever opened**
PDU: 10.36.230.212; outlets u2=1, u3=7 · 10.36.230.35; outlet u5=3
Constraints: none. Full authority within tests; power cycles allowed.

Bench chosen by rule 1: this session's own bench (the campaign's Session facts).
Campaign: `CAMPAIGN-QUEUE-2026-10-15T1458.md`, 6 AWPTCM DHCP cases, 2026-10-15 15:20 → 17:19.

## TL;DR
**The bench is WHOLE.** All 6 cases ran: **6 PASS, 0 FAIL**. Final logs, per-device `.cfg` files
and process reviews exist for every case, so nothing is left to produce.

The restore is proven, not asserted: **all three switches' `show running-config` is byte-identical
between the pre-campaign probe (`captures/2026-10-15T012929Z/`) and the post-restore probe
(`captures/2026-10-15T041733Z/`).** No unit was left powered off, nothing is `shutdown`, and no
host NIC was pinned.

The campaign's headline is not a defect — it is that **five of the six cases had no step text and
no functional spec to match the case title**, so each test was designed from the TFS, the TPS row
and the DUT's own CLI surface, and every verdict rests on crafted frames with a control, never on
a `show` read-back. The one thing that genuinely needs an answer is **OPEN-2**, the DNS forwarding
cache, and it needs a developer, not another bench run.

## Current bench state, and how to verify it
Read from the hardware's own capture at 2026-10-15T041733Z (17:17 NZDT), taken after the restore,
and from a live occupancy check and NIC read at 17:50. Not from memory.

| unit | console | power | role | boot source | boot pointer | state |
| --- | --- | --- | --- | --- | --- | --- |
| swi_d (DUT) AT-x960-56YSQ S/N A2WQS700B | u2 @115200 | on | standalone Active Master, Ready | **flash** `x960-tb277.rel` | `flash:/default.cfg` **(file exists)** | clean, config identical to pre-campaign |
| swi_b AT-x960-28YSQ | u3 @9600 | on | standalone Active Master | `flash:/backup.rel` (file exists) | `flash:/default.cfg` (file exists) | untouched — console never opened |
| swi_a AT-x950 GEN2-52XSTQm | u5 @9600 | on | standalone Active Master | netboots | boot image **Not set**, `flash:/default.cfg` **(file NOT found)** | pre-existing, OPEN-1 |

Host NICs, read live: `eth2` 10.38.22.1/27, `eth3` 10.38.22.33/27, `eth4` 10.38.22.65/27 — all
carrier up, **all advertising the full 10/100/1000 set** (no `ethtool` pinning was ever made, and
none is left). `eth3 → swi_d port1.0.10` and `eth4 → swi_d port1.0.48` both learning again;
`eth2` carrier up with no MAC learned, as it has been all along.

Consoles u2, u3, u5 all **free**. The only `precheck` FOUND item is `ser2net` (root, up 34 days),
which is the box's console-server daemon — infrastructure, not a holder. No tcpdump, `dhcp4.py`,
`dnsresp.py` or `ckcon.py` process of ours is left running.

```bash
sock=/run/user/$(id -u)/keyring/ssh
# occupancy, opening NO console
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 \
  'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 precheck --consoles u2,u3,u5'
# regenerate bench-state.md from the hardware
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 \
  'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 run \
     --consoles u2,u3,u5 --no-prompt --pdu 10.36.230.212 --outlet u2=1,u3=7'
```
**tb277 runs python3.6 as `python3`, and `bench_probe.py` dies on it (`capture_output`). Use
`python3.8` for every tool on that box, and do not use `tools/tb` there.**

`/tmp/dhcp-2026-10-15T1458/` on the box (2.4 MB) holds the campaign's cached TFS/wiki pages and
the box-side tool copies. It is tmpfs scratch and dies with the box; losing it is correct.

## What was accomplished
- Six AWPTCM DHCP cases run to completion on a DUT that had been swapped that morning
  (`A2WQS7004` → `A2WQS700B`, a build three weeks newer, now flash-booting instead of netbooting).
- Three bench setups built and torn down in sequence, because the DUT cannot be DHCP server,
  relay and client at once. The campaign was re-cut from 2 groups to 3 at triage for that reason.
- Two new generic tools written, hardware-verified and catalogued: **`tools/dhcp4.py`**
  (DHCP client / server / decode) and **`tools/dnsresp.py`** (DNS query client and fake
  authoritative responder). A third, **`tools/opt82dump.py`**, was lifted out of a case's `work/`
  at log time.
- `bench_probe.py` gained **per-unit PDU support** (`--outlet uN=OUTLET[@PDU_IP]`, a third field
  in `<TB>.static`), because tb277's three units span two PDUs. Backward-compatible: tb470's
  two-field `.static` renders byte-identical.
- **STANDING-ORDERS §7** added, on the Test Engineer's instruction: every traffic test uses
  scapy-crafted frames with a control flow and per-frame counts.

## Results
From the queue's `## Results` table. All graded by the tester; none re-graded.

| case | title | verdict |
| --- | --- | --- |
| T43851 | IPv4_DHCPServer - DHCP ARP Probe | **PASS** |
| T43853 | IPv4_DHCPServer - DHCP 120-day lease | **PASS** |
| T43852 | IPv4_DHCPServer - DHCP Relay | **PASS** |
| T43850 | IPv4_DHCPServer - Option 82 | **PASS** |
| T35370 | IPv4_DHCPClient - DHCP Extended ID | **PASS** |
| T43854 | IPv4_DHCPClient - DNS Relay | **PASS** |

**Final logs created** — `/create-logs` commits `85479cb` (dhcp-server), `a655eb2` (dhcp-relay),
`e47d053` (dhcp-client). No `work/` folder remains in git.

Run quality, per group:
- **dhcp-server (T43851, T43853): clean.**
- **dhcp-relay (T43852): clean for every graded measurement, but the route to them was not.**
  Four faults in the tester's own scapy harness were found and fixed first, each of which
  initially presented as *the relay is dropping packets*. No graded measurement predates the
  fixes. **T43850: clean.**
- **dhcp-client (T35370): clean. T43854: clean for the graded limbs**; the forwarding-cache limb
  is **UNMEASURED** with its reason (OPEN-2), which does not affect the PASS.

One number is unreconciled and is recorded rather than smoothed: on three of T43852's zero-legs
the client tool reports `sent: 5` while the eth3 capture counted 4. The graded quantity on those
legs is `eth4 = 0 relayed`, on which both counters agree, so the verdict does not rest on it.

### What each PASS actually proves
Every verdict rests on crafted frames and a control, never a status read-back:
- **T43851** — 3 ARP probes at the configured 1000 ms spacing (measured 0.995 / 1.001 s); **0**
  probes when disabled and at `probe packets 0`; an answered probe withholds the address and
  records a conflict binding with an empty ClientId; `no` forms restore the TFS defaults;
  survives a reboot.
- **T43853** — option 51 = **10,368,000 s** in OFFER and ACK, binding expiring exactly 120 days
  out; the parser accepts 120 and refuses 121 and 999 (that boundary *is* the 30→120 day
  feature); 1-day and 1-hour controls measured in the same run; `no lease` restores 86,400;
  survives a reboot.
- **T43852** — 5/5 DISCOVERs and REQUESTs relayed 1:1 in ~0.76 ms, giaddr rewritten, hops
  incremented; every reply returned to the right client; both zero-relay controls clean;
  hop threshold enforced at the default 10.
- **T43850** — circuit-id `vlan10` and remote-id = switch MAC on the wire; ASCII override and its
  revert proven in captured frames; remote-id correctly refused while agent-option is disabled;
  **all four** information-policy actions correct; option 82 stripped from replies per RFC 3046;
  survives a reboot.
- **T35370** — options **61** (type byte + SVI MAC), **12**, **124** (IANA enterprise 207) and
  **125** in the PRL, each absent in the baseline and each removed cleanly by its `no` form.
  No TFS exists for "Extended ID", so the build's identity surface was enumerated by read-only
  help probe and all four measured rather than one being guessed.
- **T43854** — 5/5 queries forwarded and 5/5 answers returned, counted at both NICs and agreeing
  with tcpdump exactly; **0** forwarded in the disabled control with the same queries
  demonstrably on the wire; a DHCP-learned server imported and genuinely used; survives a reboot.

## Findings

### Measured — product behaviour
All eight are **observations, not defects**. None stopped a case passing. The durable ones are now
in `platforms/x960.md` §6, which is the place to read them before the next x960 DHCP work.

1. **`ip dhcp-relay agent-option checking` validates SERVER RESPONSES, not client ingress.** The
   name reads like an untrusted-ingress check; it is not. A case designed around "the relay
   should drop a client frame that already carries option 82" tests the wrong direction. Ingress
   behaviour is `information policy` (replace / keep / drop / append).
2. **`probe type ping` ARPs first and escalates**, so the presence or absence of ARP cannot
   discriminate the two DHCP-server probe types. Related: under `probe type ping` an ARP reply
   alone does not withhold the address — only the ICMP echo reply does — which is narrower than
   the literal "or" in ARP Probe TFS S1566.1.01.
3. **Conflict recovery is per-DISCOVER, not automatic.** S1566.1.04's "repeat … for the next
   available address" does not roll on within the same transaction.
4. **Two near-identical `% …already…` messages mean opposite things.** `% DHCP Relay is already
   globally enabled` is an advisory and the state holds; `% DHCP client is already running on
   this interface.` is a genuine rejection (exit 2, state unchanged). Measuring past the second
   captures the *default* client and reports it as configured.
5. **All SVIs share one MAC** (`vlan1`, `vlan10`, `vlan48` all `e01a.ead4.7043`), so
   `client-id vlan10` and `client-id vlan48` emit **byte-identical** option 61. Grade on
   presence, type byte and length — a content comparison proves nothing.
6. **The client's parameter request list is [1,3,15,6,43].** Option 43 is additional to what the
   wiki DHCP page documents.
7. **A DHCP-learned DNS server is queried in preference to a statically configured one** — the
   relay queried the learned `.2` and never ARPed for the static `.9`; a control proves `.9` is
   reachable and used. S1570.1.12's "added last" describes list position, and a resolver need not
   walk its list in order, so this is preference, not a spec violation. `show ip name-server`
   cannot settle it: its display is type-grouped.
8. **The TPS files Option 82 under "DHCP server"**, but the TFS states it is a DHCP **relay**
   feature. The case was run as a relay case.

### Measured — instrument faults, all ours, all fixed
Recorded because each one first looked like a product defect.

1. **scapy does not dissect a relayed DHCP frame** — an AW+ relay forwards from an ephemeral
   source port, so `bind_layers(UDP, BOOTP, dport=67)` and `dport=68` are required before reading
   any relayed capture. Without them a server receives 0 frames and the run reads as total loss.
   Fixed in `tools/dhcp4.py` and `tools/opt82dump.py`.
2. **`dhcp4.py` kept only the FIRST option of a name**, so an appended option 82 read as
   "append did not append". Fixed; `tools/opt82dump.py` exists precisely so the raw TLVs can be
   read without trusting a decoder's option list.
3. **Four harness faults in T43852**, all of which mimicked a dropping relay.
4. **A DNS or DHCP-client change restarts the relay process and clears sessions** (DNS Relay TFS
   "Limitations"). A leg run ~3 s after such a change forwarded nothing and read as *the DUT
   cannot use a statically configured DNS server*; after a 20 s settle the identical config
   forwarded every query. The rule is in `tools/dnsresp.py`'s README entry.

### Inferred, not measured
- The one-frame gap between T43852's two counters is **most likely** the scapy sniffer missing
  the first frame — the same shape as T35370's 7-on-the-wire / 4-decoded gap, which was proven.
  It was not proven here. What would prove it: timestamp the sniffer's start against the first
  frame's capture time.

### Infrastructure
1. **`tools/tb` is broken on tb277** — it invokes the box's `python3` (3.6) and `bench_probe.py`
   dies with `TypeError: __init__() got an unexpected keyword argument 'capture_output'`. Use
   `python3.8` explicitly.
2. **Case steps are not available from AWPTCM or ck.db** for five of the six cases. ck.db keys on
   `AWP-nnnn`, not `AWPTCM-T<id>`, so cross-referencing is by **title** in `testlink_cases`.
3. **The sentinel's first arm replayed ~11 MB of stale logs**, including another box's, because
   `sentinel.sh` reads `/home/st-art/pytest-create/*/*/` on the **shared NFS home**. The fix was
   to let one pass baseline every remote offset at EOF, then re-arm.
4. **🔥 `tcpdump -Z $(whoami)` BREAKS CAPTURES on the NFS lab home.** Dropping privilege means
   tcpdump cannot write to the root-squashed share, so the pcaps are header-only and read as
   *no traffic* — indistinguishable from a dropping relay. **Capture to the box's local `/tmp`
   as root, then copy and `chown`.** This corrects advice given earlier in the same session.

## OPEN questions

**OPEN-1 (carried from 2026-10-12). swi_a netboots and its `flash:/default.cfg` reads
"(file not found)".** Not touched this session — swi_a's console was never opened. Any case that
needs swi_a must confirm it can boot first.
*Evidence path:* `captures/2026-10-15T041733Z/u5.show_boot.txt`.

**OPEN-2. Is the DNS forwarding cache meant to cover RELAYED queries at all?** With the cache
enabled (`DNS Cache: enabled, Size 100, Max-TTL 60`), two identical queries 5.3 s apart inside
the TTL **both** went upstream. This is recorded UNMEASURED rather than FAIL because the TFS
separates a *Name Resolver Process* from a *DNS Relay Process*, and S1570.1.03/.11 both say "name
**resolve result**", which plausibly scopes the cache to the device's own lookups rather than to
relayed third-party queries. **Nothing on this bench can separate "not cached by design" from
"cache broken" — this one wants a developer's answer, not another bench run.**
*Evidence path:* `dhcp-client-2026-10-15T1458/T43854/T43854.log`, the second CAVEAT.

**OPEN-3. T35370 has no reboot-persistence evidence, in either direction.** The group's shared
reload saved `ckclient.cfg` at 17:11, *after* T35370's removal step had taken all four identity
options out, so none of them were in the saved config. Closing this needs a re-run, or a group
reboot check staged before any removal step.

**OPEN-4. T43850 proves removal for two of its four `no` forms.** `no ip dhcp-relay information
policy` and `no ip dhcp-relay agent-option` were sent only in the teardown, with no `show` after
them, and teardown proof is excluded from a final log. Send every `no` form inside the removal
step with a `show` after it.

**OPEN-5. The DUT's "default config" is not pristine.** `interface vlan1` carries
`ip dhcp-client vendor-identifying-class` and `ip dhcp-client request vendor-identifying-specific`
in `flash:/default.cfg`. They were present in the **first** probe of the day, before any testing,
so they are not campaign residue and they did not confound T35370 (which measured on vlan48 and
showed both options absent in its baseline). Worth knowing before the next client case.
*Evidence path:* `diff captures/2026-10-15T012929Z/u2.show_running-config.txt
captures/2026-10-15T041733Z/u2.show_running-config.txt` — identical.

## Ordered next steps
1. **Push.** Claude cannot; the branch is committed and not pushed.
2. **Attach the six logs and their `.cfg` files in Zephyr** from
   `tb277/x960/dhcp-*-2026-10-15T1458/<id>/`.
3. **Take OPEN-2 to a developer.** It is the only item in the campaign that a bench cannot settle.
4. **Build `tools/leg.py`** before the next campaign — the single highest-value item in the
   process reviews. Twelve hand-built leg drivers were written this session, one set per case.
   Proposed: `--leg NAME --nics eth3,eth4 --config F --client '<args>' --out DIR`, applying the
   config, capturing both NICs, running the client, and **failing loudly when the tool's count
   and the capture's count disagree**.
5. **Re-run T35370's persistence limb** (OPEN-3) and **T43850's two unproven `no` forms**
   (OPEN-4) if either matters for sign-off.
6. Decide whether `bench_probe.py apply` should ever write a `.setup` on tb277. It needs
   `/nfsHome` mounted, which is root and therefore the Test Engineer's call. Still open from the
   start of the campaign.

## Recipes

**Set the three group bench states on the DUT.** All three use `tb eth3 → port1.0.10` and
`tb eth4 → port1.0.48`, and all three must end by returning both ports to untagged VLAN 1 or the
post-run probe will not MATCH (its host-MAC discovery depends on exactly those ports).

```
# DHCP SERVER group (T43851, T43853): DUT serves VLAN 10, host eth3 is the client
vlan database / vlan 10 / exit
interface port1.0.10 / switchport access vlan 10 / exit
interface vlan10 / ip address 192.168.10.1/24 / exit
service dhcp-server
ip dhcp pool CKPOOL / network 192.168.10.0 255.255.255.0 / range 192.168.10.50 192.168.10.60

# DHCP RELAY group (T43852, T43850): eth3 client side, eth4 is a scapy DHCP server
interface vlan10 / ip address 192.168.10.1/24 / ip dhcp-relay server-address 192.168.48.2
interface port1.0.48 / switchport access vlan 48 / exit
interface vlan48 / ip address 192.168.48.1/24
arp 192.168.48.2 000d.b955.770f port1.0.48     # pre-resolve, so no measured DISCOVER is spent on ARP

# DHCP CLIENT group (T35370, T43854): DUT is the client on VLAN 48, eth4 the scapy server
interface vlan48 / ip address dhcp

# RESTORE, all groups
interface port1.0.10 / switchport access vlan 1 / exit
interface port1.0.48 / switchport access vlan 1 / exit
no interface vlan10        # NOTE: `no interface vlanN` answers `% Removal of interface not allowed`
                           # while an address is still on it — remove the address first
```

**Reboot persistence, without writing startup-config.** Stage a named boot config, reload, verify
on the wire, then restore the pointer and delete the file:
```
copy running-config flash:/ckNAME.cfg
configure terminal / boot config-file flash:/ckNAME.cfg / end
reload                      # answers (y/n) — send `y\r`
# ... re-measure on the wire ...
configure terminal / boot config-file flash:/default.cfg / end
delete flash:/ckNAME.cfg
```

**Capture without producing root-owned files on the NFS share.** Do **not** use
`tcpdump -Z $(whoami)` — see Findings/Infrastructure 4.
```
sudo tcpdump -i ethN -w /tmp/leg.pcap ...      # local tmpfs, as root
cp /tmp/leg.pcap <case>/work/ && sudo chown $(id -u):$(id -g) <case>/work/leg.pcap
```

**Read a relayed DHCP capture in scapy.** Before anything else:
```python
bind_layers(UDP, BOOTP, dport=67); bind_layers(UDP, BOOTP, dport=68)
```

## Pointers
- Topology: `bench-setup/tb277/bench-state.md` (generated 2026-10-15T041733Z — do not hand-edit).
- Names, PDU outlets, per-unit PDU IPs: `bench-setup/tb277/tb277.static`. It is append-only, so
  it still carries a stale `swi_c` line for the previous physical DUT (`A2WQS7004`).
- The campaign and every finding in full: `tb277/x960/CAMPAIGN-QUEUE-2026-10-15T1458.md`.
- Platform facts for the next x960 DHCP work: **`platforms/x960.md` §6**.
- Process reviews and the token tables: `tb277/x960/dhcp-*-2026-10-15T1458/REVIEW.md` and each
  case's `<id>-review.md`.
- Logging rules: `logged-output.md`. Standing rules for campaigns: `STANDING-ORDERS.md`
  (§7 is the scapy rule added this session).
- Tools: `tools/README.md` — `dhcp4.py`, `dnsresp.py` and `opt82dump.py` are new this session and
  each carries its traps in its entry.

## Sentinel
Armed at 14:58 as a one-session sentinel (`SELF=1`), re-armed five times, and **stood down at
17:46**: the Monitor was not re-armed after its last expiry, the 15-minute cron backstop was
deleted, and a process sweep confirmed no `sentinel.sh` remains. It was stood down about 15
minutes before its 18:00 deadline because the campaign was complete and the bench idle.
