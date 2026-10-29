# IE520 session handover — 2026-09-09

**Campaign:** AWPTCM **T5648** (EPSR stack **master** failure — L2) and **T5649** (EPSR stack
**slave** failure — L2). Prove L2 traffic continues across a stack member failover, with
**≥9000 FDB entries on EPSR ports** and **link aggregation in the ring**.

Authoritative bench topology + PDU map: **`~/claude/IE520-testing/bench-setup/bench-state.md`**,
"Current state — 2026-09-09" section (updated this session). Don't trust that file's ```setup
fences yet — they still describe the Sep-3 tree and are flagged stale (see step 7).

---

## TL;DR — where we are

- Bench recabled into an **EPSR ring**: DUT stack (u2/u3 = S/N …061/…068) = EPSR **master**;
  **u4** (…052) and **u5** (…066) = standalone **transit** nodes. (The old record's "stack on
  u4/u5" was stale — whole device population moved.)
- The two **structural requirements are MET**: ≥9000 FDB on EPSR ports (u5 held **9497/9243**
  unique test MACs), and cross-member link aggregation in the ring (stack `sa1`/`sa2`).
- The **failover runs are NOT clean results yet** — see "Test results". And the bench is
  currently **degraded/parked** — see below.
- **BENCH IS PARKED:** member 2 (u3/…068) **powered OFF**; member 1 (u2/…061) standalone Active
  Master; EPSR `ring1` = **Failed**, L2 down; **`tb eth3` is link-down** (which is why member 2
  can't netboot).

## Current bench state — verify first thing

```
member 1  u2  S/N 264A23061  MAC …0ac0  outlet 6 (F)  = Active Master (standalone)   ON
member 2  u3  S/N 264A23068  MAC …0780  outlet 8 (H)  = POWERED OFF (was boot-looping) OFF
transit   u4  S/N 264A23052  MAC …09c0  outlet 4 (D)                                  ON
transit   u5  S/N 264A23066  MAC …0740  outlet 5 (E)                                  ON
x230 u0 / 4050 u1 = still cabled, powered OFF; PDU outlets TBD (Terrence to reconcile)
```
Check with: host carriers `cat /sys/class/net/eth{1,2,3}/carrier` (expect eth1=1, eth2=1,
eth3=0); `show stack` / `show epsr summary` via u2 (member 1). `fuser /dev/u{2,3,4,5}` BEFORE
driving any console.

## What was accomplished this session

- Diagnosed and fixed the **copper-SFP edge links** (they only link **forced 1000/full**, not
  autoneg). eth1↔stack member 1 `port1.0.2` and eth2↔u4 `port1.0.2` are up in **vlan10**.
  Terrence physically swapped SFPs/cables; the fault was traced to a **dead switch cage**
  (relocated eth1's link to `port1.0.2` on member 1; eth3's edge never recovered).
- Removed a leftover unsynced LACP group (`po5`) off the stack edge ports; set edges to
  `access vlan10`.
- **Demonstrated the FDB scale requirement:** 9497/9243 unique MACs learned on **u5's EPSR
  ports** (≥9000 ✓). (The DUT stack read ~half — VCStack distributes the hardware FDB across
  members; a display artifact, logical total is ~full.)
- Re-established the **true device/console/serial/member/PDU mapping** (the old record was
  stale) and recorded it in bench-state.md prose + the PDU outlet map.
- Powered off the boot-looping member 2 at Terrence's request.

## Test results so far — NOT clean, do not cite as pass/fail

- **T5649 attempt (accidental):** outlet F (member 1) was cut. Invalid as a slave-failure
  continuity test because the traffic *source* (eth1) sits on member 1 — the very member that
  failed — so the flow just died with the source. Confirmed the F↔member-1 mapping, nothing else.
- **T5648 (master cut, outlet H / member 2):** member 1 correctly took over as Active Master
  and its `sa1`/`sa2` legs stayed up — but **EPSR `ring1` went `Failed` and ALL L2 traffic
  stopped and did NOT recover.** Then member 2 **could not reboot** (TFTP boot-loop, below), so
  the outage was open-ended. Result is confounded — needs a clean re-run.

## Key findings / learnings

1. **Copper-SFP ↔ Intel-igc edge links need forced 1000/full** on BOTH ends; autoneg leaves
   them `notconnect`.
2. **IE520 members NETBOOT via TFTP over eth3** (`tftp://10.38.215.65/IE520-tb470.rel`;
   `in.tftpd` serves `/tftproot` on the host). **A hard power-cut strands the member if
   eth3/TFTP is down** — it boot-loops on "Failed to load tftp://…". ⇒ Prefer
   **`reload stack-member <id>`** for failover, or make eth3/TFTP bulletproof first. And **never
   leave eth3 pinned to 1000-only** (`advertise 0x20`) — the bootloader's ASIX USB dongle is
   10/100-class; restore `advertise 0x2f` / autoneg or you kill the TFTP boot (bit us earlier).
3. **OPEN QUESTION (the crux of T5648):** after the master-member cut, EPSR did **not**
   reconverge on the surviving member (ring stayed `Failed`, L2 down) even though member 1's
   `sa1`/`sa2` legs were up. Real EPSR-over-VCStack defect **vs.** a ring-cabling gap (ring not
   truly cross-member-cabled) is **unresolved** — but note it was confounded by member 2 never
   rebooting. Re-test with a clean `reload`-based failover where the member returns.
4. **Mastership is not priority-pinned now** (both members priority 128) — no preemption, so
   after a failover the master role stays on the survivor and **the master's PDU outlet
   changes**. Always `show stack` and confirm which member is master before cutting/reloading.
5. **Measurement harness needs a rebuild** (see recipe): scapy `sendp` only sustained ~26 pps;
   and per-frame timestamps weren't persisted, so cut timings couldn't be reported.

## NEXT STEPS (ordered)

1. **Restore eth3** — physical SFP/cable (flaky copper link + the TFTP boot path). Bring the
   link up (force 1000/full switch side; host `ethtool -s eth3 autoneg on advertise 0x2f`),
   confirm `10.38.215.65` is up and `in.tftpd` reachable.
2. **Power member 2 back** (outlet 8, `ons.cgi` — recipe below). Confirm it TFTP-boots
   `IE520-tb470.rel` and rejoins: both members `Ready`, `ring1` `Complete`.
3. **Re-verify** stack whole + ring `Complete` + FDB, then rebuild the continuity harness.
4. **T5648 (master fail):** `show stack` → find current master; source the continuity flow on
   the **surviving** member's edge; **`reload stack-member <master-id>`** (preferred over a PDU
   cut); measure outage + FDB survival + confirm failover + ring returns `Complete`. Write
   **`T5648.log`**.
5. **T5649 (slave fail):** source the flow on the **surviving (master)** member's side — needs a
   member-2-side edge (eth3 up) or a restructure; reload/cut the slave. Write **`T5649.log`**.
6. **Resolve finding #3** — if the ring still won't reconverge on the survivor with its `sa`
   legs up (clean reload, member returns), it's a real defect; otherwise map the **port-level
   ring cabling** to find the gap.
7. **Rewrite bench-state.md ```setup fences** once the bench is whole and characterised:
   device model incl. the transit nodes, `[powerlink]`, ring `[portlink]`, and TFTP boot
   replacing `[boot_from_flash]`. **First confirm the framework `.setup` schema tolerates
   transit-node `swi_` entries / a multi-node ring** (unknown — don't guess into the source of
   truth). Deliverables per house rule are the **`.log` files**, not an after-action.

## Recipes (scratchpad scripts are session-ephemeral — rebuild from these)

**Console driver** (use this, NOT minicom — closing a port sends BREAK and can park the
bootloader; and `fuser /dev/uN` first, collisions happened this session):
```python
import sys; sys.path.insert(0,'/home/terrenceb/old test runs/IE520/stack-tests/2026-09-02-driver-test')
from console import Console
c = Console('/dev/u2','/tmp/ckprobe/x.log',baud=115200); c.login(monitor=False)
c.cmd('end',timeout=8); c.cmd('terminal length 0',timeout=8)      # drain config-mode; u5 was left in it
print(c.cmd_fast('show stack',timeout=25))
```
u2 & u3 both relay to the master CLI. If a console reads "% Invalid input at ^" for plain
`show` cmds, it's stuck in config mode — send `end`/`disable`/`enable` (raw) to drain it.

**PDU** (`10.36.150.14`, `manager`/`friend`; framework `PduPower` hit a symlink-loop import, so
POST directly, mirroring `ATPower._pdu_cmd`):
```python
import requests; from requests.auth import HTTPBasicAuth
A=HTTPBasicAuth('manager','friend'); IP='10.36.150.14'
st=requests.post(f'http://{IP}/status.xml',auth=A,timeout=8).text.split('<pot0>')[1].split(',')[10:35]  # states, index=outlet-1
led=lambda n: ''.join('1' if i==n-1 else '0' for i in range(24))
requests.post(f'http://{IP}/ons.cgi?led={led(8)}',auth=A,timeout=8)   # power ON outlet 8 (member 2)
# offs.cgi to power off. Outlets: 6=u2/m1, 8=u3/m2, 4=u4, 5=u5.
```

**Copper edge link up:** switch `interface portX.0.Y ; speed 1000 ; duplex full ; shutdown ; no
shutdown`; host `sudo ethtool -s ethN autoneg on advertise 0x20` (0x20 = 1000baseT/Full); wait
~15-20 s; `show interface portX.0.Y status` should read `connected full/1000`.

**FDB populate + count:** scapy from eth2 — N unique srcs `02:00:00:00:%02x:%02x`, dst
broadcast, paced (chunks of 500, `inter=0.0008` — unpaced storm-control drops ~half); count on
a node via `show mac address-table | include 0200.0000`.

**Continuity harness (REBUILD):** raw `AF_PACKET` socket (scapy `sendp` only did ~26 pps) for
steady ≥200 pps; **write per-frame send+recv timestamps to a FILE** (Terrence wants cut timings
in the log); use **BROADCAST** (survives the ring's forwarding-direction flip at failover — a
unidirectional unicast flow breaks); outage = longest recv inter-arrival gap + longest
consecutive-lost run.

## Pointers

- Topology + PDU map (authoritative): `~/claude/IE520-testing/bench-setup/bench-state.md`
  ("Current state — 2026-09-09"). Prior record archived at
  `bench-setup/backups/2026-09-08T192551Z.bench-state.md`.
- Applier: `bench-setup/bench_setup.py {render|check|apply}` — box is currently IN SYNC (fences
  unchanged this session; only prose was updated).
- Session working scripts were under `/tmp/ckprobe/` on tb470 and the session scratchpad
  (ephemeral): `topology_truth.py`, `t5648_preflight*.py`, `fdb_populate.py`, `failover_run.py`,
  `recovery_monitor.py`, `agg_resilience_diag.py`, `pdu_off_looper.py`. Rebuild from the recipes
  above if gone.
- SSH from the dev host needs `export SSH_AUTH_SOCK=/run/user/1971/keyring/ssh`.
