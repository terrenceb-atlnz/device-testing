# Campaign queue — tb470, x230v2-28GS as the DUT, 6 AWPTCM cases (AR4050S = link partner), from 2026-10-22 13:20 NZDT

The ask, Test Engineer 2026-10-22 13:1x (after `/orient-dt tb470`): *"Contact the peer session and execute these tests
T47209 T47228 T45543 T44179 T47119 T47121"*, then `/test-mode T47209 T47228 T45543 T44179 T47119 T47121 no reboots`.
Titles (ck.db `zephyr_cases`): AWPTCM-T47209 Fibre pluggable with supported speeds; AWPTCM-T47228 API-enable/disable
interafce, add/delete vlans; AWPTCM-T45543 TPM Support; AWPTCM-T44179 Jumbo Frames; AWPTCM-T47119 confirm secure mode
algorithm sets for SSH match other devices that support secure mode; AWPTCM-T47121 confirm the TLS algorithms match other
devices with crypto secure-mode.

**This file is the resume point.** A session that wakes up reads it top to bottom. It continues
from the first queue row that is not DONE or BLOCKED, and updates the row as soon as its state
changes.

## Session facts

Recorded 2026-10-22 13:20 NZDT (Test Engineer's answers to the setup questions):
Test Engineer: terrenceb@terrenceb-dl
Testbox: tb470
Consoles: u0,u1 (u0 = AR4050S swi_e, the link partner; u1 = x230v2-28GS swi_f, the DUT; both 115200), as recorded 2026-10-21 and confirmed by the 13:05 probe; taken by the sentinel and not disputed.
PDU: "10.36.150.14 u0=3 u1=4"
Constraints: "no reboots" (from the /test-mode arguments) + "None beyond no reboots". Host: VS Code.

Read together: the PDU outlets are declared, but "no reboots" means **no `reload`, no PDU cycle, no `write`-then-reload, on either unit**.
A framework run, if any case uses one, binds a run `.setup` with NO `[power]`/`[powerlink]` so the post-failure power cycle cannot fire.

Peer session `device-testing-c9` (Terrence's orient session, 13:1x): *"tb470 and u0/u1 are yours. I'm not using them and won't open them."*

## Rules carried with the queue

- Verdicts, working logs, the `RESULT` line, the results list: [logged-output.md](../../logged-output.md).
  The final log is made ONLY by `/create-logs`, on the Test Engineer's request.
- `STANDING-ORDERS.md` applies (§7 scapy for traffic, §8 health reads). Startup config: nothing written unless a case requires it, and under "no reboots" a written config is never reloaded.
- **Only u0 and u1 are touched.**
- Case texts: Ask-CK `ck.db` table `zephyr_cases`, key `AWPTCM-T<n>`, read-only. On the dev host the db is
  `/media/terrenceb/mnt/testbox_home/claude/Test-cases/ask-ck/db/ck.db` (`tools/ckcase.py`'s default `~/claude/...` path does not exist there; it does on tb470).
- MANUAL-ONLY.md (repo root): **T45543 step 3** (needs an idevid account + internet; steps 1–2 runnable, "TPM is instantiated" = "TPM is OK", Terrence 2026-10-13).
- Platform traps: [platforms/x230v2-28GS.md](../../platforms/x230v2-28GS.md).
- Prior evidence on this x230 (S/N A10783G262900002), method only, never the verdict: T47209 FAIL 2026-10-09 (`ports-2026-10-09T0845/`: SPSX accepts `speed 100`, passes no frames);
  T47228 FAIL 2026-10-13 and T45543 PARTIAL 2026-10-13 (`cli-2026-10-13T0949/`); `secure-2026-10-09T0845/`. T44179, T47119, T47121 never run here.
  Memory `awplus-restconf-api-reference` (no VLAN-database model; PATCH-on-leaf 204 is a no-op; client `tools/restconf.py`).

## Bench at queue creation (probe `2026-10-22T000539Z`, 13:05, u0/u1, **MISMATCH**; plus the peer's measurements 12:34–12:50)

- u0 AR4050S swi_e S/N A10401G214000005, awplus_main-20261008-57, boots `flash:/AR4050S-awplus_main-20261008-57.rel (file exists)` + `flash:/tb470-bench.cfg (file exists)`; flash 3.4 GB free; up 6 d 22 h.
- u1 x230v2-28GS swi_f S/N A10783G262900002, awplus_main-20261019-75 (built Mon Oct 19 08:39:33 UTC 2026), boots `flash:/x230v2_28GS-awplus_main-20261019-75.rel (file exists)` + `flash:/tb470-bench.cfg (file exists)`; flash 60.5 MB free; up 2 d 01 h.
- Terrence recabled ~12:40 and ran `apply` at 12:44 (`bench-setup/backups/2026-10-21T234445Z.*`); the deployed template predates the new cables. Spanning tree is DISABLED on both units (`no spanning-tree rstp enable`).
- Links (probe, LLDP both ends): 4050 port1.0.2 (access vlan10) <-> x230 port1.0.1 (trunk, native vlan1, `switchport atmf-link`); 4050 port1.0.3 (access vlan10, `static-channel-group 1` = sa1) <-> x230 port1.0.3 (access vlan103).
- Host NICs: eth1 (00:f0:4d:00:77:16) -> x230 port1.0.2 (access vlan1000); eth3 (…:18) -> 4050 port1.0.1 (vlan1);
  **eth2 (…:17) -> x230 port1.0.10 (SPTXc, vlan1)** per the peer and the x230's MAC table. **The probe's `tb-swi_e eth2-port1.0.2` is a MISATTRIBUTION** (eth2's frames cross the x230 trunk into 4050 vlan10 and the probe does not exclude inter-switch ports): **do not `apply` this probe's fence.**
- **Two self-loops on the x230 the probe does not see:** copper port1.0.15 <-> port1.0.16 (AT-SPTXa x2) and SX fibre port1.0.25 <-> port1.0.26 (AT-SPSX x2). All four untagged vlan1 with STP off made a live broadcast storm (CPU 68%); at 12:49, on Terrence's OK, the peer **shut port1.0.16 and port1.0.26 in RUNNING-CONFIG ONLY (not written)**; CPU fell to 1%.
  ⇒ these two shutdowns are the campaign's baseline: leave them shut after every case. Open 1.0.26 (or 1.0.16) only inside a case, with a VLAN/STP plan that prevents the storm, and re-shut before the case ends. A reload would bring the storm back (moot under "no reboots").

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| 1 | ports: T47209 (fibre pluggable speeds), T44179 (jumbo frames) | tb470/x230v2-28GS/ports-2026-10-22T1320/ | TRIAGE | T47209 on the SX self-loop 1.0.25<->1.0.26; T44179 per the peer needs `platform jumboframe` (write + reload) and root MTU 9000 on tb470 NICs: expect BLOCKED under "no reboots" |
| 2 | mgmt: T47228 (RESTCONF interface enable/disable, VLAN add/delete), T45543 (TPM) | tb470/x230v2-28GS/mgmt-2026-10-22T1320/ | TRIAGE | T45543 step 3 MANUAL-ONLY |
| 3 | secure: T47119 (secure-mode SSH algorithms), T47121 (secure-mode TLS algorithms) | tb470/x230v2-28GS/secure-2026-10-22T1320/ | TRIAGE | per the peer, secure mode needs write + reload each way on both units: expect BLOCKED under "no reboots" |

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |

## Issues

- 2026-10-22 13:20: `bench_probe.py` attributes a host NIC to an inter-switch port (eth2 -> 4050 port1.0.2, a port with an LLDP neighbour) and does not detect same-device self-loops. Not fixed in this campaign; the fence must not be applied as generated.
