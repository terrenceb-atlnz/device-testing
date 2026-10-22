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
| 1 | ports: T47209 (fibre pluggable speeds), T44179 (jumbo frames) | tb470/x230v2-28GS/ports-2026-10-22T1320/ | T47209 DONE run1 FAIL 14:22 (SPSX accepts `speed 100`/`speed auto 100`, link "connected 100", 0/100 frames; 10/2500/10000/half refused; auto, 1000, 1000+full both ends pass 100/100). First tester died ~14:00 after R6; resumed 14:04 by a new bench-runner (sentinel device-testing-c9). Restored per the Group 1 recipe 14:19, NO DRIFT vs 13:46, 1.0.16 + 1.0.26 shut, nothing written, health CLEAN; working log `ports-2026-10-22T1320/47209/work/run1.log`; T44179 BLOCKED (not run, Test Engineer 13:4x) | T47209: setup/restore "Group 1" below (u1 only). T44179 BLOCKED (K): see Triage 2026-10-22 13:30 |
| 2 | mgmt: T47228 (RESTCONF interface enable/disable, VLAN add/delete), T45543 (TPM) | tb470/x230v2-28GS/mgmt-2026-10-22T1320/ | RUNNABLE (go 13:4x) | setup/restore "Group 2" below. T45543 step 3 MANUAL-ONLY, so the expected verdict is PARTIAL |
| 3 | secure: T47119 (secure-mode SSH algorithms), T47121 (secure-mode TLS algorithms) | tb470/x230v2-28GS/secure-2026-10-22T1320/ | BLOCKED (Test Engineer 13:4x: "ignore them for this run") | (K): 2 reloads each under "no reboots", AND no reference unit with secure mode on the bench. See Triage 2026-10-22 13:30 |

## Triage 2026-10-22 13:30 (bench-runner, read-only)

Gate: precheck CLEAR (u0, u1 free). `tools/tb template tb470` resolves (`/nfsHome` mounted). Peek: u0 `4050-5g#`, u1 `x230-28GSv2#`.
Probe `2026-10-22T002207Z` exit 1 MISMATCH, the same two lines as at 13:05: `[portlink] swi_e-swi_f` (bench adds port1.0.3-port1.0.3)
and `[portlink] tb-swi_e eth2-port1.0.2` (the known misattribution). No Advisories, no USER-CONFLICT. Neither runnable case depends on either line.
Boot baseline (gate 7): both units `Current boot config: flash:/tb470-bench.cfg (file exists)`. The x230 is on awplus_main-20261019-75 and the 4050 on -20261008-57.
No case has a script: all are manual-CLI (ck.db steps empty, except T45543 steps 1–3 and T44179's precondition), so preflight (gate 6) and the
defaulting-CLI check (gate 10) do not apply, and no run `.setup` is bound. If a framework run is ever added: cut it from `bench-setup/tb470.setup.current`
with u1 only (Group 1) or u0+u1 (Group 2), and no `[power]`/`[powerlink]`.

Read-only measurements taken at triage (u1 = x230, u0 = 4050; transcripts `/tmp/x230tri1022/console-u{0,1}.log` on tb470):
- x230 `show platform`: `Jumboframe support off`. `show interface port1.0.10` / `port1.0.25`: `mru 1500`. In config-if, `mru ?` and `mru jumbo ?` give
  `% Unrecognized command`, so there is **no per-port MRU on this build**. In config, `platform jumboframe ?` offers only `<cr>`.
  The help probes were typed with no CR and cleared with Ctrl-U. The device log shows only `configure terminal` / `interface port1.0.10`, and `show running-config | include jumbo|mru|secure|crypto` is empty afterwards.
- x230 `show secure-mode`: `Secure mode is disabled`; `no service ssh`; `service http`. **4050 `show secure-mode`: `% Invalid input detected`** (this build has no
  secure-mode CLI, although the CLI wiki lists AR4050). The 4050 has `service ssh` and `service http` on, with vlan1 10.38.215.70/27 reached through tb470 eth3.
- `show ssh server`: Ciphers/KEX/MAC/hostkeys are **identical** on the x230 and the 4050 in normal mode (chacha20/aes-gcm/aes-ctr; mlkem768x25519/sntrup761/curve25519/ecdh-nistp*; umac/hmac-etm/hmac-sha2; ed25519/ecdsa/rsa-sha2 + certs).
- tb470 eth1/eth2/eth3: mtu 1500, maxmtu 9216; `sudo -n` OK (scapy through `tools/tb sudotool`).
- x230 pluggables: 1.0.25 AT-SPSX A03240R192701902, 1.0.26 AT-SPSX A03240R111800014 (both 1000BASE-SX); 1.0.15/1.0.16 AT-SPTXa. 1.0.25 is admin up / link down; 1.0.26 is admin down (the baseline).
- Before the case, x230 running-config for the ports and VLAN the cases touch: port1.0.2 `switchport access vlan 1000`; port1.0.3 `switchport access vlan 103`; port1.0.10, 1.0.15 and 1.0.25 are
  `switchport mode access` (vlan1); port1.0.16 and 1.0.26 also `shutdown`; interface vlan1 `ip address 192.168.1.1/24`; vlan105 exists (member port1.0.5, no IP); STP disabled.

### Group 1 — T47209 setup and exact restore (u1 only; T44179 not run)

Path: tb470 eth2 → x230 port1.0.10 → **port1.0.25 =SX fibre= port1.0.26** → port1.0.2 → tb470 eth1. Two VLANs so the self-loop cannot close:
- **Setup (in this order; 1.0.26 stays shut until the VLANs are proven):**
  1. `vlan database` / `vlan 3901 name T47209A`;
  2. `interface port1.0.10,port1.0.25` / `switchport access vlan 3901`;
  3. `interface port1.0.26` / `switchport access vlan 1000` (it joins port1.0.2's VLAN);
  4. prove it with `show vlan brief`: 3901 = {1.0.10, 1.0.25} and 1000 = {1.0.2, 1.0.26}. Nothing else may be in either VLAN;
  5. then `interface port1.0.26` / `no shutdown`.

  Traffic: scapy frames from eth2 to eth1's MAC (00:f0:4d:00:77:16) with a counted control flow (STANDING-ORDERS §7). Each speed row goes on port1.0.25 (port1.0.26 stays auto), and the 2026-10-09 expected-output table in `ports-2026-10-09T0845/47209/47209-review.md` applies.
- **Restore (exact, in this order):**
  1. `interface port1.0.26` / `shutdown` FIRST;
  2. `interface port1.0.25,port1.0.26` / `speed auto` / `duplex auto`;
  3. `interface port1.0.26` / `no switchport access vlan` (→ vlan1);
  4. `interface port1.0.10,port1.0.25` / `no switchport access vlan` (→ vlan1);
  5. `no vlan 3901` (in `vlan database`).

  Then prove it: `show running-config interface port1.0.2,port1.0.10,port1.0.25-1.0.26` must equal the block above (1.0.26 `shutdown`), and `show vlan brief` must have no 3901. Nothing is written.

### Group 2 — T47228 and T45543 setup and exact restore (u0 read-only, u1 changed)

- **T47228 setup:** RESTCONF from tb470 eth2 (10.38.215.33/27).
  1. x230: `interface port1.0.10` / `switchport access vlan 105`;
  2. x230: `interface vlan105` / `ip address 10.38.215.35/27`;
  3. `tools/tb ping tb470 eth2 10.38.215.35 3`.

  `service http` is already on. Use `tools/restconf.py --root /restconf` with user manager. The interface under test is **x230 port1.0.3** (↔ 4050 port1.0.3, read at u0: link down/up seen at both ends); never port1.0.1 (atmf-link, the flap audit) or port1.0.10 (the management path). The test VLAN is 3999 (absent now). The 2026-10-13 expected table is in `cli-2026-10-13T0949/47228/47228-review.md`.
- **T47228 restore:**
  1. port1.0.3 `no shutdown` (PUT enabled=true, or CLI), proven `running`;
  2. `no vlan 3999` if the CLI created it;
  3. `interface vlan105` / `no ip address`;
  4. `interface port1.0.10` / `no switchport access vlan` (→ vlan1);
  5. `show running-config interface port1.0.3,port1.0.10,vlan105` must equal the pre-case capture.

  Nothing is written.
- **T45543:** steps 1–2 are reads only (`show platform full-debug | grep tpm` with `CKTO=180`, `show system tpm`), so there is nothing to restore. Step 3 is MANUAL-ONLY.

### Blocked (K) — what would unblock them, and what is measurable without a reload

- **T44179 Jumbo Frames.**
  - The x230 has no per-port `mru`; jumbo is only `platform jumboframe`, which the wiki (x230) says needs *"save the configuration and restart"*. That means `write` + reload to turn it on, and again to restore it: **2 x230 reloads (~165 s each), excluded by "no reboots"**.
  - It also needs **root on tb470** (the Test Engineer's): `ip link set eth2 mtu 9216` and `ip link set eth1 mtu 9216` (maxmtu 9216), restored to 1500 afterwards. At MTU 1500 the host cannot even send the jumbo-OFF baseline frame (>1518 B).
  - The case says Ixia; no Ixia port is recorded on tb470. With host NICs the largest frame testable is ~9216 B, not the x230's 16335-byte payload limit.
  - Measurable without a reload: only the CLI reads already taken (jumbo off, mru 1500, no per-port mru). Entering `platform jumboframe` in running-config only would prove nothing.
- **T47119 / T47121 secure-mode SSH / TLS algorithm sets.**
  - Secure mode on the x230 is `crypto secure-mode` + `write` + reload (~265 s), and the restore is `no crypto secure-mode` + `write` + reload: **2 reloads, excluded**.
  - Independently of reboots, **there is no reference device on this bench**: the AR4050S (u0, -20261008-57) rejects `show secure-mode`. The Test Engineer must name the "other device with crypto secure-mode" (a unit or box) or a documented reference list.
  - (`Feature Overview Guides/` is not present at the repo root on 2026-10-22, so the secure-mode guide could not be read here.)
  - Measurable now without a reload, as baseline only and not a verdict:
    - the normal-mode SSH sets (taken above, x230 = 4050);
    - the normal-mode TLS sets of both HTTPS servers, from tb470 (x230 through the Group 2 temporary IP; 4050 at 10.38.215.70 through eth3);
    - optionally, whether `crypto secure-mode` in running-config ONLY (no `write`, then `no crypto secure-mode`) changes `show ssh server` before a reload.
  - For reference only, the x230's secure-mode SSH set measured 2026-10-09 on -20261008-57 is in `secure-2026-10-09T0845/47114/47114-review.md`.

## Results

| case | verdict | reason | graded by | working log |
| --- | --- | --- | --- | --- |
| T44179 Jumbo Frames | NOT TESTED | BLOCKED: `platform jumboframe` needs write + 2 x230 reloads (excluded by "no reboots") and root MTU 9216 on tb470 eth1/eth2 (Test Engineer's); nothing measurable at MTU 1500. Test Engineer 2026-10-22 13:4x: "Proceed with the 3", the other three ignored for this run | sentinel (triage) | — (triage section above) |
| T47119 secure-mode SSH algorithm sets | NOT TESTED | BLOCKED: secure mode needs write + 2 x230 reloads ("no reboots"), and no reference device with secure mode on the bench (the 4050 rejects `show secure-mode`). Test Engineer 2026-10-22: "ignore them for this run" | sentinel (triage) | — (triage section above) |
| T47121 secure-mode TLS algorithms | NOT TESTED | BLOCKED: as T47119 (reloads + no secure-mode reference device). Test Engineer 2026-10-22: "ignore them for this run" | sentinel (triage) | — (triage section above) |

## Issues

- 2026-10-22 13:20: `bench_probe.py` attributes a host NIC to an inter-switch port (eth2 -> 4050 port1.0.2, a port with an LLDP neighbour) and does not detect same-device self-loops. Not fixed in this campaign; the fence must not be applied as generated.
