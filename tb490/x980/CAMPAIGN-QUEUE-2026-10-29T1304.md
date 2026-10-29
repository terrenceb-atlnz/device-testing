# Campaign queue — tb490 DUT + tb5 network, 4 AWPTCM Authentication & Security cases, from 2026-10-29 13:04 NZDT

The ask, verbatim: *"i want to run a campaign on TWO testboxes against a DUT located on TB490 the
rest of the network is on TB5"*, with the AWPTCM panel showing four cases (below).

**This file is the resume point.** `/test-mode --resume tb490/x980/CAMPAIGN-QUEUE-2026-10-29T1304.md`
picks up at the first row that is not DONE or BLOCKED.

> **Path note:** neither box had been probed when this file was written, so the DUT family was
> unknown and the file sits under `tb490/NO-FAMILY/`. Once TRIAGE measures the family it is moved
> (`git mv`) to `tb490/<FAMILY>/`, and that move is recorded here.
>
> **Moved 2026-10-29 (TRIAGE):** the DUT measured as an AT-x980-16CDQ, so the file is now
> `tb490/x980/CAMPAIGN-QUEUE-2026-10-29T1304.md`. There is no `platforms/x980.md` yet.

## Session facts

Recorded 2026-10-29 13:0x NZDT from the Test Engineer's own answers to `/test-mode` §1.

Test Engineer: jacobm@jacobm-dl
Testbox: tb490 (DUT, and the box that runs the cases) + tb5 (the rest of the network: "tb5 is for console access and logging")
Consoles: tb490 u2 = swi_dut (the DUT; names added 13:2x: "tb490 u2=swi_dut; tb5 u0=swi_x950, u1=swi_x530, u2=swi_ar"). tb5: "run the bench probe on tb5" — all its consoles, u0, u1, u2 (cleared by the Test Engineer 2026-10-29, see below)
PDU: "no pdus" (both boxes). The framework's post-failure power cycle therefore does nothing (STANDING-ORDERS §1).
Constraints: "no shared boxes all mine, run the test probe, u0 and u1 on tb490 are not to be touched"
             Both boxes are the Test Engineer's own ("tb5 is mine yes same with tb490 is mine").
             Cabling: "yes everything is cabled directly" (tb490 ↔ tb5).
             Driving: "the 490 runs it, tb5 is for console access and logging" — the cases are NOT
             driven from both boxes at once.
             .setup: asked whether one `.setup` describes both boxes' units, the answer was
             **"write them"** — the Test Engineer authorises writing the setup file(s).
Sentinel until: "When the campaign ends" (stands down at /wrap-dt).

### Occupancy check, 2026-10-29 13:0x NZDT (sentinel, no console opened)

- **tb490 u2** (`/dev/ttyUSB0`): free. **CLEAR**, exit 0.
- **tb5 u0, u1, u2** (`/dev/ttyUSB0-2`): all free. **FOUND**, exit 5, one item: `ser2net` (root, pid 593,
  up 10 days), whose `/etc/ser2net.conf` maps only `/dev/ttyS0` and `/dev/ttyS1`, so none of the
  session consoles. The Test Engineer answered **"Yes, probe u0-u2"**.
- **tb5's `python3` is 3.6**; use `python3.8` (pyserial 3.4): `TB_PY=python3.8 tools/tb …`, or add
  `tb5` to `BOX_PY` in `tools/tb`.
- **Neither box has a deployed `.setup`** (`/home/st-art/st-art/configs/<TB>.setup` missing) and
  neither has a `bench-setup/<TB>/` folder: this is the first probe of both, so expect "no template".
- Host NICs seen (information): tb490 `eth1` UP 10.38.235.1/27, eth2–eth7 DOWN (10.38.235.32/27
  steps); tb5 `eth2` 10.37.5.1/27, `eth4` 10.37.5.65/27, `eth6` 10.37.5.129/27 + 192.168.50.10/24, UP.
  Each box's lab segment and return path were not stated: ask before using anything outside them
  (STANDING-ORDERS §4).

## Rules

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **[logged-output.md](../../logged-output.md)**. Final logs are made only by `/create-logs`.
- `STANDING-ORDERS.md` in full: §7 (scapy, not ping) and §8 (a health read before step 1 and
  after the last step of every case).
- `platforms/<FAMILY>.md` for the DUT's family, once measured. If it is `x960`, its §7 holds the
  2026-10-23 tb277 auth & security findings (web-auth login is a plain POST to `/index.cgi`, T44279).
- `MANUAL-ONLY.md`: a listed case or step is reported MANUAL-ONLY and never run unattended; a new
  person-needed step found here is added to it, dated.
- **Two boxes:** tb490 runs the cases. tb5's consoles are for access and logging. The sentinel
  watches tb490 (`BOX=tb490`).
- **tb490 u0 and u1 are never touched.**

## The four cases

| case | title (from the AWPTCM panel; truncated there) | panel state |
| --- | --- | --- |
| AWPTCM-T33365 (1.0) | (205) Authentication&Security_WebAuthentication - Public … | not executed |
| AWPTCM-T33366 (1.0) | (206) Authentication&Security_WebAuthentication - Promis… | not executed |
| AWPTCM-T33357 (1.0) | (194) Authentication&Security_IEEE 802.1XEncryptionType … | not executed |
| AWPTCM-T33375 (1.0) | (219) Authentication&Security - MAC Auth/Web Auth | In Progress |

T33375 was run on IE520 before (`IE520/auth-2026-09-22/33375.log`).

## Triage — 2026-10-29 13:06–13:20 NZDT (bench-runner, TRIAGE)

### Bench, measured (probes exit 0; no template on either box, so no diff)

- **tb490 u2 = DUT**: AT-x980-16CDQ S/N A10732A263200035 + XEM3-12YS (bay 1) + XEM3-8CQ (bay 2),
  `awplus_main-20261029-90` (built 2026-10-28 20:43 UTC), boot image `flash:/x980-tb490.rel`,
  **boot config `flash:/x980-autoorder.cfg`** (the baseline, gate 7). Uptime 2 h 45 m at the probe.
  Capture `bench-setup/tb490/captures/2026-10-29T000558Z/`.
- **tb5**: u0 = AT-x950-52XTQm `x950-ptp` (`awplus_main-20261020-78`, boot cfg `flash:/x950-twostep.cfg`);
  u1 = AT-x530-18GHXm `awplus` (`awplus_main-20261028-87`, boot cfg `flash:/x530-twostep.cfg`,
  **boot image Not set**); u2 = AR4050S `wlg-ar4050s` (`awplus_main-20261027-86`, `flash:/default.cfg`).
  Capture `bench-setup/tb5/captures/2026-10-29T000612Z/`.
- The probe switched `lldp run` ON (running-config only) on the DUT, the x950 and the x530.
- **Topology** (LLDP both ends unless said):
  - DUT `port1.0.81` (100GBASE-CR4, the DUT's ONLY up switchport) ↔ tb5 x950 `port1.0.49`.
  - x950 `port1.0.39` ↔ x530 `port1.0.1`.
  - x530 `port1.0.16` ↔ **tb5 `eth6`** (MAC learned) — `00:90:0b:2a:11:c3`, 10.37.5.129/27 **and
    192.168.50.10/24**, plus macvlans `jm1`–`jm5@eth6` (192.168.50.11–15, all DOWN; jm2–jm5 MACs
    02:00:5e:00:01:02–05 are users in the DUT's RADIUS table).
  - tb5 `eth4` ↔ AR4050S `port1.0.8` (MAC learned). AR4050S has no other up port.
  - tb5 `eth2` (10.37.5.1/27) and x950 `port1.0.1`/`port1.0.2` are up, peer not proven.
  - tb490 `eth1` (10.38.235.1/27) reaches the DUT's **`eth0` management port** (10.38.235.3,
    ARP `e0:1a:ea:d5:04:55`) over a shared segment (other hosts .2, .5–.9). **tb490 has no NIC on
    any DUT switchport**: every client frame for these cases has to come from tb5 `eth6`.
- **DUT state found**: local RADIUS server (`radius-server local`, users `webuser`, `dot1xuser`,
  five MAC users, groups TWOSTEP / v10→VLAN 10); `aaa authentication dot1x|auth-mac|auth-web
  default group radius`; `auth-web-server ipaddress 192.168.50.1`; `port1.0.81`: `auth-web enable`,
  `auth host-mode multi-supplicant`, `auth forward arp|dhcp|dns`; vlan1 192.168.50.1/24; tb5
  eth6's MAC static-authorised on port1.0.81. x950 and x530 both carry `dot1x eap forward`.
  `show license brief`: Full (ATL-NZ internal), RADIUS-FULL present.

### Verdict per case

| case | full title (ck.db) | authored | triage |
| --- | --- | --- | --- |
| T33365 | (205) Authentication&Security_WebAuthentication - Public key encryption(X509) | objective + precondition + 7 steps | runnable after D1 (client = tb5 eth6 → https://192.168.50.1); the authored 1.1.1.1 / 8.8.8.8 routes on the testbox are root (D2) and NOT needed if the DUT's own web-auth address is used; the authored external freeradius is replaced by the DUT's local RADIUS (D3) |
| T33366 | (206) Authentication&Security_WebAuthentication - Promiscuous / Intercept web Authentication | none (empty) | from the title; after D1, and the intercept leg needs an off-subnet destination routed via the DUT from tb5 eth6 (D2, root) |
| T33357 | (194) Authentication&Security_IEEE 802.1XEncryptionType - EAP-TLS | none (empty) | from the title; after D1. `wpasup.py --method tls` on tb5 eth6 (TLS 1.2 supplicant, memory eap-tls-needs-tls12-supplicant) against the DUT's local RADIUS; `sudotool` works on tb5 |
| T33375 | (219) Authentication&Security - MAC Auth/Web Auth | none (empty) | from the title (as on IE520 2026-09-22); after D1 |
| T33365 | (205) Authentication&Security_WebAuthentication - Public key encryption(X509) | A | PASS | ck-web trustpoint bound to auth-web-server ssl; chain verified with exported CA (fails without); HTTPS login wrong 0/4, ckweb W 4/4; STEP 6 skipped (D3) | auth-2026-10-29T1304/T33365/work/run1.log | |

### Decisions for the Test Engineer

- **D1 — client host and segment.** The only path to the DUT's switchports is tb5 `eth6` on
  192.168.50.0/24 via x530 → x950. The session facts say "the 490 runs it, tb5 is for console
  access and logging", and neither box's lab segment was stated (STANDING-ORDERS §4). Confirm that
  tb5 `eth6` / 192.168.50.0/24 (and the jm1–jm5 macvlans) may carry the client traffic.
- **D2 — root on tb5** for an off-subnet destination routed via the DUT (T33366 intercept; T33365
  only if the authored 1.1.1.1 address is wanted): e.g. `sudo ip route add 8.8.8.0/24 via
  192.168.50.1 dev eth6`, and `ip link set jmN up` if the macvlans are to be used.
- **D3 — T33365's RADIUS server**: the authored case copies the CA to an external freeradius
  on the testbox; propose the DUT's local RADIUS (already staged) instead.
- **D4 — names**: none were given; the probes auto-named tb490's DUT `swi_a` AND tb5's AR4050S
  `swi_a`. Drafts in `bench-setup/tb490/tb490.setup.draft` and `bench-setup/tb5/tb5.setup.draft`,
  not applied.

### Test Engineer's answers — 2026-10-29 13:2x NZDT (AskUserQuestion, verbatim choices)

- **D1:** "Yes, use tb5 eth6 + run" — tb5 eth6 / 192.168.50.0/24 (and jm1–jm5) carry the client traffic; the run proceeds.
- **D2:** "Allow route + macvlans" — the tester may add the off-subnet route via the DUT (e.g. `sudo ip route add 8.8.8.0/24 via 192.168.50.1 dev eth6`) and bring jm1–jm5 up on tb5, and **removes both when the case is done**.
- **D3:** "Use the local RADIUS" — T33365 uses the DUT's local RADIUS instead of the authored external freeradius; the difference is noted in the working log.
- **D4:** "Let me name them" — given 2026-10-29 13:2x NZDT, verbatim: "tb490 u2=swi_dut; tb5 u0=swi_x950, u1=swi_x530, u2=swi_ar"

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T33365 Web Auth – Public…; T33366 Web Auth – Promis…; T33357 802.1X EncryptionType…; T33375 MAC Auth/Web Auth | `auth-2026-10-29T1304` | RUNNING (bench-runner 13:25): T33375 PASS; T33365 PASS; T33366 next | One group, one DUT console (tb490 u2); client NIC tb5 eth6. T33366 also waits on D2. See Triage. |

### Group A — bench setup and restore recipe (bench-runner RUN, written 2026-10-29 13:3x NZDT, before the first case)

**Bench (measured 2026-10-29 13:24–13:27 NZDT):** `.static` written for both boxes from D4, both
setups applied (`/home/st-art/configs/tb490.setup`, `/home/st-art/configs/tb5.setup`), re-probe
**MATCH** on both (commit a82c99e). Consoles used: tb490 u2 (swi_dut) only for config; tb5 u0/u1
(swi_x950/swi_x530) read-only if needed; tb5 u2 (swi_ar) not used. tb490 u0/u1 never.
Client: tb5 eth6 `00:90:0b:2a:11:c3` 192.168.50.10/24 -> swi_x530 port1.0.16 -> swi_x950
port1.0.49 -> swi_dut port1.0.81 (vlan1 192.168.50.1, MAC e0:1a:ea:d5:04:56).

**Baseline = the pre-run running-config, NOT the boot config.** Saved:
`auth-2026-10-29T1304/baseline/swi_dut-pre-run-1327.out` (show running-config, show boot, show auth,
supplicants, local-server users). `show boot`: image `flash:/x980-tb490.rel`, boot config
`flash:/x980-autoorder.cfg`. The running-config differs from that file (diff measured 13:3x):
users `00-90-0b-2a-11-c3`/`dot1xuser` in group TWOSTEP (file: v10); `lldp run` (the probe);
`auth-web-server ipaddress 192.168.50.1`; port1.0.81 has `auth-web enable` (file: `auth-mac enable`,
`dot1x port-control auto`, `auth dynamic-vlan-creation`, `auth two-step enable`); `interface vlan1`
(file: vlan10). **So a reload does NOT restore the baseline, and nothing is ever `write`n.**

**Inherited (not ours, left as found):** local RADIUS (`radius-server local`, server enable, nas
127.0.0.1, groups TWOSTEP/v10, users 00-90-0b-2a-11-c3, 02-00-5e-00-01-02..05, dot1xuser, webuser);
`radius-server host 127.0.0.1`; `aaa authentication dot1x|auth-mac|auth-web default group radius`;
`auth-web-server ipaddress 192.168.50.1`; port1.0.81 `auth-web enable`, `auth host-mode
multi-supplicant`, `auth forward arp|dhcp|dns`; `lldp run` (triage probe, unsaved); `service http`.
**Live state inherited:** eth6's MAC holds a WEB-auth session as `webuser` (Mode W, 192.168.50.10) —
triage called it "static-authorised"; it is not.

**Added by the cases (each removed by its own teardown):** local-server users prefixed `ck`
(and ck MAC users 02-00-5e-c0-ff-0N); port1.0.81 `auth-mac enable` / `dot1x port-control auto`
as a case needs; `auth-web-server mode ...`, `auth-web-server ssl`, a `crypto pki trustpoint
ck-web` and its RSA key `ck-web-key`; on tb5 (T33366, D2) the route `8.8.8.0/24 via 192.168.50.1
dev eth6` and jm links up.

**Restore recipe (anyone can run it):**
1. swi_dut: `configure terminal`; on port1.0.81 `no auth-mac enable`, `no dot1x port-control`,
   (re-)`auth-web enable`, `auth host-mode multi-supplicant`, `auth forward arp|dhcp|dns`;
   `no auth-web-server mode`/`no auth-web-server ssl` (back to what the baseline file shows);
   `radius-server local` -> `no user ck...`; `no crypto pki trustpoint ck-web`; `exit`;
   `crypto key zeroize rsa ck-web-key`; `end`.
2. `rcdiff.py` the new `show running-config` against `baseline/swi_dut-pre-run-1327.out`: must be
   identical (exit 0). `show boot` must still read `flash:/x980-autoorder.cfg`.
3. tb5: `ip route del 8.8.8.0/24 via 192.168.50.1 dev eth6`; `ip link set jm1..jm5 down`; prove
   with `tools/tb nics tb5` (jm DOWN, no 8.8.8.0/24 route).
4. eth6 web session: re-login as `webuser` needs its password (stored encrypted; asked of the
   Test Engineer 13:3x). Without it eth6 is re-authenticated with a ck user before that user is
   removed, and the log says so.
5. `end`, `terminal no monitor` on every console opened; re-probe both boxes: MATCH.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33375 | (219) Authentication&Security - MAC Auth/Web Auth | A | PASS | known MAC M 4/4 vs unknown 0/4; wrong web pw 0/4 vs ckweb W 4/4; M+W together | auth-2026-10-29T1304/T33375/work/run1.log | tester |

## Issues

### Test Engineer's answers — 2026-10-29 13:3x NZDT (to the RUN tester's NEEDS TEST ENGINEER)

- **eth6 restore:** tb5 eth6 held a live web-auth session as `webuser` (not static-authorised as triage said). Answer: "Test user, then delete it" — re-authenticate eth6 with a ck test user at restore, then remove that user.
- **Root helper for D2:** `tools/tb` refuses root route changes by design. Answer: "Yes, add the narrow helper" — only `ip route add/del 8.8.8.0/24 via 192.168.50.1 dev eth6` and `ip link set jm1-jm5 up/down`, under sudotool, for T33366, removal proved.
