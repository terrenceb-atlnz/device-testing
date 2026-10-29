# Campaign queue — tb490 DUT + tb5 network, 9 AWPTCM Authentication & Security cases, from 2026-10-29 15:28 NZDT

The ask, verbatim: *"can we run all of these on x980 dut"*, with the AWPTCM panel ("Not Executed",
9 test cases) showing the cases below.

**This file is the resume point.** `/test-mode --resume tb490/x980/CAMPAIGN-QUEUE-2026-10-29T1528.md`
picks up at the first row that is not DONE or BLOCKED.

## Session facts

Recorded 2026-10-29 15:2x NZDT from the Test Engineer's own answers to `/test-mode` §1.

Test Engineer: jacobm@jacobm-dl
Testbox: tb490 (DUT, and the box that runs the cases) + tb5 (the rest of the network) — "Same as 10-29"
Consoles: "Same as 10-29": tb490 u2 = swi_dut; tb5 u0 = swi_x950, u1 = swi_x530, u2 = swi_ar
PDU: "Same as 10-29": no PDUs on either box. The framework's post-failure power cycle therefore does nothing (STANDING-ORDERS §1).
Constraints: "Same as 10-29": "no shared boxes all mine, run the test probe, u0 and u1 on tb490 are not to be touched";
             plus the 2026-10-29 wrap ruling that `lldp run` stays off, so every probe runs `--read-only`.
             tb490 runs the cases; tb5's consoles are for access and logging (10-29).
Session: run in the editor (Test Engineer accepted the risk of a cut; `--resume` covers it).
Added 15:3x: "just heads up, the python3 scripts running on the tb490 are my scripts and does not touch u0 at all so the x980-dut is safe from that"
             (python3 processes on tb490 in a precheck are the Test Engineer's own: not a stop, never touched; an fuser holder of /dev/u2 still is.)
Added 15:3x: "okay yes so if anything touvhes u2 please stop, i'll make sure here it doesn't n my end"
             (any other process, output, login, reload or build change on tb490 u2 = the tester STOPS and reports; no retry, no grading of the case in flight.)
Sentinel until: when the campaign ends (stands down at /wrap-dt).

### Occupancy check, 2026-10-29 15:21 NZDT (sentinel, no console opened)

- **tb490 u2** (`/dev/ttyUSB0`): free, CLEAR (exit 0). The precheck missed a live
  `python3 -m x980nos load-release -u u2` (PID 144141, the Test Engineer's pts/1, started 15:16); the
  Test Engineer answered "Finished / safe now" and PID 144141 was gone at 15:27. **The DUT may now run a
  different build from the -90 that `platforms/x980.md` was measured on**: read `show version` first.
- **tb5 u0, u1, u2**: free; FOUND only `ser2net` (pid 593, ttyS0/S1 only, not a holder; 10-29 ruling).
- tb5 read-only probe 15:22 (2026-10-29T022219Z): MISMATCH 3 + NEEDS-CHECK 1, all from read-only mode
  (no LLDP to prove x530↔x950; eth6 learned on both switches; no traffic on eth4). The deployed
  `tb5.setup` is correct (handover 2026-10-29, update block).

## Rules

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **[logged-output.md](../../logged-output.md)**. Final logs are made only by `/create-logs`.
- `STANDING-ORDERS.md` in full: §7 (scapy, not ping) and §8 (a health read before step 1 and
  after the last step of every case).
- **[platforms/x980.md](../../platforms/x980.md)** — the x980 auth surface measured 10-29 (no `clear auth`,
  no `auth-web-server mode`, `auth-mac enable` ends web sessions, grade web-auth on `show auth supplicant
  brief`, never the HTTP body). Re-check anything a new build could change.
- The previous campaign's group A recipe (client = tb5 eth6 → swi_x530 → swi_x950 → swi_dut port1.0.81,
  DUT local RADIUS, EAP-TLS supplicant at TLS 1.2, `tools/tb sudotool tb5 <scratch> hostnet ...` for the
  approved tb5 root helper): [CAMPAIGN-QUEUE-2026-10-29T1304.md](CAMPAIGN-QUEUE-2026-10-29T1304.md) §Group A.
- `MANUAL-ONLY.md`: a listed case or step is reported MANUAL-ONLY and never run unattended; a new
  person-needed step found here is added to it, dated.
- **tb490 u0 and u1 are never touched.** Probes are `--read-only`.

## The nine cases

| case | title (from the AWPTCM panel; truncated there) | panel state |
| --- | --- | --- |
| AWPTCM-T44274 (1.0) | (204) Authentication&Security_WebAuthentication - Multip… | not executed |
| AWPTCM-T44275 (1.0) | (207) Authentication&Security_WebAuthentication - Proxy S… | not executed |
| AWPTCM-T44276 (1.0) | (208) Authentication&Security_WebAuthentication - DHCP S… | not executed |
| AWPTCM-T33358 (1.0) | (195) Authentication&Security_IEEE 802.1XEncryptionType - … | not executed |
| AWPTCM-T44271 (1.0) | (197) Authentication&Security_IEEE 802.1XEncryptionType … | not executed |
| AWPTCM-T44272 (1.0) | (198) Authentication&Security_IEEE 802.1XEncryptionType … | not executed |
| AWPTCM-T33355 (1.0) | (192) Authentication&Security_IEEE 802.1X - IEEE 802.1X-2004… | not executed |
| AWPTCM-T33354 (1.0) | (191) Authentication&Security_IEEE 802.1X - EAP-Notification… | not executed |
| AWPTCM-T44277 (1.0) | (214) Authentication&Security - Supplicant MAC | not executed |

## Triage — 2026-10-29 15:29–15:41 NZDT (bench-runner, TRIAGE)

### Gate

- Precheck 15:29: tb490 u2 CLEAR (exit 0); tb5 u0-u2 free, FOUND only `ser2net` pid 593 (known, not a holder).
- Probes, `--read-only --baud 115200`, names from the session facts:
  - **tb490 u2: MATCH** (exit 0), capture `bench-setup/tb490/captures/2026-10-29T023114Z/`.
  - **tb5 u0-u2: MISMATCH 3 + NEEDS-CHECK 1** (exit 1), capture `bench-setup/tb5/captures/2026-10-29T023125Z/`.
    The same four lines as the 15:22 probe, all read-only artefacts: no LLDP to prove
    x530 port1.0.1 - x950 port1.0.39; eth6 placed on swi_x950 port1.0.39 instead of swi_x530 port1.0.16;
    eth4 - swi_ar port1.0.8 has no learned MAC. Nothing moved. The deployed `tb5.setup` was not changed.
- No template under `/nfsHome` on either box (not mounted); the deployed `/home/st-art/configs/<TB>.setup` is the template.
- Every console opened was logged out (`login:` in each transcript `/tmp/tri1528/console-uN.log`); no holder left on either box.
  tb490 u0/u1 never opened. No device state changed (help probes `qmark` only; the line was erased each time).
- Gate 6 (pt_preflight) does not apply: no case has a script; all nine are title-only manual-CLI cases.

### swi_dut after the Test Engineer's 15:16 `x980nos load-release -u u2` — NOTHING changed

Measured 15:32 NZDT. **The release load left no trace on swi_dut:**
- `show version`: `x980-awplus_main-20261029-90.rel` (the build `platforms/x980.md` was measured on);
  `show system`: build date Wed Oct 28 20:43:01 UTC 2026, **uptime 5 h 10 m** (no reload since before the 10-29 campaign).
- `show boot`: image `flash:/x980-tb490.rel` (file exists), config `flash:/x980-autoorder.cfg` (file exists), backup
  image/config Not set, autoboot disabled — identical to the wrap capture `2026-10-29T020348Z`.
- `dir flash:/*.rel`: `x980-tb490.rel` dated **Oct 28 2026 21:19:40 (UTC)**, i.e. before today's 13:04 campaign;
  no new .rel. No new .cfg (newest `x980-macweb-90.cfg`, Oct 28 21:42 UTC).
- `show running-config` vs the wrap capture: identical except `lldp run`, which the wrap reverted after that probe.
- `show auth supplicant brief`: eth6 (`0090.0b2a.11c3`) still web-authenticated (Mode W, 192.168.50.10, user `ckres...`),
  as the handover left it. Local RADIUS users unchanged (00-90-0b-2a-11-c3, 02-00-5e-00-01-02..05, dot1xuser, webuser).
- DUT clock UTC, ~35 s behind tb5 (`show clock` 02:32:04 vs `date -u` 02:32:39).
- **For the Test Engineer:** you confirmed the load-release targeted u2, but swi_dut's flash and boot show no new
  image. Either it did not complete, or it wrote somewhere this read cannot see. Re-read `show version` before group A's
  first case and stop if it moves (campaign rule: anything else touching u2 = stop).

### Platform reads that decide the verdicts (measured, help only)

- `show license brief`: Full (ATL-NZ internal), RADIUS-FULL present.
- **`show radius local-server statistics`: Available methods `MAC EAP-MD5 EAP-TLS EAP-PEAP`** (Enabled: the same).
  The AW+ command reference and Local RADIUS guide document the same four. **No EAP-TTLS, LEAP or OTP on the DUT's
  local RADIUS server.**
- config: `auth-web-server dhcp ?` -> `ipaddress | lease | wpad-option`; `auth-web-server intercept-port ?` ->
  `<1-65535> | any`.
- config-if port1.0.81: `dot1x eapol-version ?` -> `<1-2>` (default 1); `auth supplicant-mac ?` -> MAC (HHHH.HHHH.HHHH);
  `auth ?` includes `priority`, `max-supplicant`, `host-mode`, `two-step`, `supplicant-mac`, `profile`.

### Verdict per case (ck.db `zephyr_cases`, read on tb490 from `/home/terrenceb/claude/Test-cases/ask-ck/db/ck.db`)

**Authored content: none of the nine has steps.** Each `steps` column is one empty step
(`[{"description": "", "testData": "", "expected": ""}]`); none has a precondition; only T33354 has an objective,
and it is the two words **"Not Support"**. All are Status Draft, folder New Platform Template / Authentication & Security.
Every runnable case is therefore run from its title (as T33366/T33357/T33375 were on 10-29).

| case | full title (ck.db) | authored | triage |
| --- | --- | --- | --- |
| T44274 | (204) Authentication&Security_WebAuthentication - Multiple Authentication | none | **RUNNABLE now** (group A). Read as several auth methods and supplicants on one port: port1.0.81 multi-supplicant with auth-web + auth-mac + dot1x (and `auth priority` if wanted); eth6 web-auth with a ck user, eth6 dot1x via `wpasup --method md5/peap`, and MAC-auth of the existing RADIUS MAC users 02-00-5e-00-01-02..05 from fake-MAC frames (`vsend`/`hostsim`, sudotool, no host change). Grade on `show auth supplicant brief` (Mode W/M/D per MAC). Interpretation note in D1 |
| T44275 | (207) Authentication&Security_WebAuthentication - Proxy Server for Web Authentication | none | **RUNNABLE now** (group A). Unauthenticated eth6 (after `dot1x initialize interface port1.0.81`) sends an HTTP proxy request (absolute-URI GET) to 8.8.8.8:8080 via the approved `hostnet route-add`; `auth-web-server intercept-port 8080` must return the DUT's login page from the DUT's MAC, and NOT without it (control). Login, then restore with a ck user and delete it (10-29 pattern); `hostnet route-del`, proved |
| T44276 | (208) Authentication&Security_WebAuthentication - DHCP Server for Web Authentication | none | **RUNNABLE now** (group A). `auth-web-server dhcp ipaddress <net>` + `lease`; unauthenticated client = `sudotool dhcp4 client eth6 --mac <eth6 MAC>` (crafted at L2, changes no host IP): grade the OFFER/ACK address, lease (opt 51) and server; login from eth6's own MAC (web-auth binds the MAC). A second client on a jm MAC (02-00-5e-00-01-0N) via `dhcp4 --mac` covers multi-supplicant DHCP. The full "client then browses with the leased address" leg from a second MAC needs D2 |
| T33358 | (195) Authentication&Security_IEEE 802.1XEncryptionType - EAP-TTLS | none | **BLOCKED (decision D3)**: the DUT's local RADIUS has no EAP-TTLS (measured). The authenticator part is method-agnostic, so the case needs an EXTERNAL RADIUS server that speaks TTLS. `wpasup --method ttls` exists |
| T44271 | (197) Authentication&Security_IEEE 802.1XEncryptionType - EAP-LEAP | none | **BLOCKED (D3)**: no LEAP on the local RADIUS. Needs an external server with LEAP (FreeRADIUS has it); `wpasup.py` needs a `leap` method added (a tools change, mine to make) |
| T44272 | (198) Authentication&Security_IEEE 802.1XEncryptionType - EAP-OTP | none | **BLOCKED (D3)**: no OTP on the local RADIUS, and stock FreeRADIUS has no EAP-OTP module either (it has GTC, which is NOT a substitute). Needs a server that speaks EAP-OTP (type 5); `wpasup.py` needs an `otp` method |
| T33355 | (192) Authentication&Security_IEEE 802.1X - IEEE 802.1X-2004 | none | **RUNNABLE now** (group B). `dot1x eapol-version 2` on port1.0.81 vs default 1; supplicant `wpasup --eapol-version 1|2 --method md5` (and peap) on eth6 against the local RADIUS with a ck user; grade the EAPOL protocol-version byte in both directions from the pcap and the outcome; restore eth6's web session |
| T33354 | (191) Authentication&Security_IEEE 802.1X - EAP-Notification | objective: **"Not Support"** | **BLOCKED (decision D4)**: the author records it as not supported. It can be measured: `radeap.py --notify` (no root, port >= 1024) on **tb490 eth1 10.38.235.1**, which reaches the DUT's eth0 (10.38.235.3) without crossing the controlled port; DUT `radius-server host 10.38.235.1 auth-port <N> key ...` in a ck server group for dot1x; supplicant `wpasup --method md5` on eth6; grade whether the EAP-Request/Notification reaches eth6 |
| T44277 | (214) Authentication&Security - Supplicant MAC | none | **RUNNABLE now** (group B). `auth supplicant-mac <mac>` per-MAC overrides on port1.0.81 (e.g. `port-control force-authorized` / `force-unauthorized` / `auto` for eth6 `0090.0b2a.11c3` and a fake jm MAC); grade `show auth supplicant` and the dataplane (ICMP from eth6 / fake-MAC frames), with the port's own control as the contrast; `no auth supplicant-mac` restores |

**Summary: 5 runnable now, 0 blocked by topology, 4 blocked otherwise.**
- Runnable, in queue order: T44274, T44275, T44276, T33355, T44277.
- Blocked by topology: none. Every client leg runs from tb5 eth6 -> swi_x530 port1.0.16 -> swi_x950 -> swi_dut
  port1.0.81, as on 10-29; RADIUS for T33354 from tb490 eth1 -> swi_dut eth0.
- Blocked otherwise: T33358, T44271, T44272 (D3: an external RADIUS server), T33354 (D4: authored "Not Support").
- MANUAL-ONLY: none of the nine is listed, and none needs a person (web login by `httpq`, no browser). Nothing added.

### Regrouping (the full titles split differently from the panel's two groups)

| group | cases | dir | state |
| --- | --- | --- | --- |
| A — web auth, local RADIUS | T44274, T44275, T44276 | `webauth-2026-10-29T1528` | runnable |
| B — 802.1X / port auth, local RADIUS | T33355, T44277 | `dot1x-2026-10-29T1528` | runnable |
| C — needs a decision | T33358, T44271, T44272 (external RADIUS); T33354 ("Not Support") | `eap-2026-10-29T1528` | blocked |

T44277 (Supplicant MAC) is port-auth, not an EAP type, so it stays with T33355 in B; the three EAP types move to C
because none can run on the local RADIUS server.

### Decisions for the Test Engineer

- **D1 — T44274 "Multiple Authentication"**: proposed reading = several methods (web + MAC + 802.1X) and several
  supplicants on one port. If it means several WEB-auth logins from different MACs, it needs D2.
- **D2 — a web login from a MAC other than eth6's** (T44274 alt. reading, T44276's second-client browse leg): the
  macvlans jm1-jm5 share 192.168.50.0/24 with eth6, so the kernel sends their HTTP out of eth6 with eth6's MAC. It
  needs either a new root tool (an HTTP login over a crafted TCP stack from a fake MAC, added to `tools/tb` SUDO_TOOLS),
  or root policy routing on tb5. Both are root on tb5: yours.
- **D3 — T33358 / T44271 / T44272**: an external RADIUS server with EAP-TTLS, LEAP and EAP-OTP. Installing or configuring
  FreeRADIUS on a box is root (STANDING-ORDERS §4). FreeRADIUS covers TTLS and LEAP, but not EAP-OTP. Options: provide or
  approve a server (which box, which port; tb490 eth1 10.38.235.1 reaches the DUT's eth0 without the controlled port),
  or leave the three blocked. Whether FreeRADIUS is installed on tb490/tb5 was NOT checked (no wrapper action reads it).
- **D4 — T33354**: the authored objective is "Not Support". Record it so (UNSUPPORTED from the author, nothing run), or
  measure it with `radeap.py --notify` on tb490 as above (adds a temporary `radius-server host 10.38.235.1` + a ck server
  group on the DUT, removed by the teardown).
- **Info — load-release**: see "swi_dut after ... load-release" above: no change to build, boot or flash.

### Test Engineer's answers to the triage — 2026-10-29 15:4x NZDT

- Proceed: **"Proceed with the 5 (Recommended)"**: run A then B; C waits BLOCKED.
- D1 (T44274): **"Several methods, one port (Recommended)"**: web + MAC + 802.1X and several supplicants on port1.0.81, graded per MAC. D2 is not needed for T44274.
- D3 (T33358, T44271, T44272): **"don't test these right now"**: BLOCKED, NOT TESTED.
- D4 (T33354): **"i'll deal with it "**: BLOCKED, NOT TESTED; the Test Engineer handles it.
- T44276's second-MAC browse leg (needs D2, root on tb5) was not asked; that leg is out of scope unless the Test Engineer opens D2.

- **15:5x — already tested and finished (Test Engineer, verbatim): "T33355 Pass, T44271 Not Supported, T44272 Not Supported, T33354 Pass".**
  Not run in this campaign; recorded in Results as the Test Engineer's verdicts, with no working log here. T33355 removed from group B,
  so B = T44277 only. T33358 (EAP-TTLS) stays NOT TESTED (D3).

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T44274 (204) Multiple Authentication; T44275 (207) Proxy Server for Web Auth; T44276 (208) DHCP Server for Web Auth | `webauth-2026-10-29T1528` | RUNNING | 16:0x bench-runner RUN started; triage 15:41: all three runnable now; T44274 reading = D1 |
| B | T44277 (214) Supplicant MAC | `dot1x-2026-10-29T1528` | RUNNABLE | regrouped at triage; T33355 removed 15:5x (already PASS, Test Engineer) |
| C | T33358 (195) EAP-TTLS; T44271 (197) EAP-LEAP; T44272 (198) EAP-OTP; T33354 (191) EAP-Notification | `eap-2026-10-29T1528` | BLOCKED | D3 "don't test these right now" (needs an external RADIUS with TTLS/LEAP/OTP; local RADIUS has MAC/MD5/TLS/PEAP only); D4 T33354 "i'll deal with it " (Test Engineer) |

### Group A — bench setup and restore recipe (bench-runner RUN, written 2026-10-29 16:0x NZDT, before the first case)

**Gate (15:50–15:58 NZDT):** precheck tb490 u2 CLEAR; tb5 u0-u2 free, FOUND only `ser2net` pid 593 (known).
Probes `--read-only --baud 115200`: tb490 u2 **MATCH** (`captures/2026-10-29T025037Z`); tb5 the same
3 MISMATCH + 1 NEEDS-CHECK read-only artefacts as at triage (`captures/2026-10-29T025049Z`). Run setups:
`webauth-2026-10-29T1528/tb490-u2.setup` (swi_dut) and `tb5-u0u1.setup` (swi_x950, swi_x530; swi_ar dropped).
No framework script, so no preflight. Consoles used for config: tb490 u2 only. tb5 u0/u1/u2 opened by the
probe only and logged out (tb5's ckcon kept running after `exit` on u1 and u2, as at triage; killmine'd).

**Baseline = the pre-run running-config**, `webauth-2026-10-29T1528/baseline/swi_dut-pre-run.out` (15:51):
build `x980-awplus_main-20261029-90.rel`, uptime 5 h 30 m (no reload since 15:32: campaign rule OK);
`show boot` image `flash:/x980-tb490.rel`, config `flash:/x980-autoorder.cfg`. Nothing is ever `write`n.
eth6 (`0090.0b2a.11c3`) holds a web session as the deleted user `ckrestore` (Mode W).

**Client:** tb5 eth6 `00:90:0b:2a:11:c3` 192.168.50.10/24 -> swi_x530 port1.0.16 -> swi_x950 -> swi_dut
port1.0.81 (vlan1 192.168.50.1, MAC e0:1a:ea:d5:04:56). Fake supplicants from eth6 by scapy
(`arpleg --sender-mac`, `eapol.py`, `dhcp4.py --mac`), MACs `02:00:5e:c0:ff:xx`.

**Added by the cases (each removed by its own teardown):** local-server users prefixed `ck` (and ck MAC
users `02-00-5e-c0-ff-xx`); on port1.0.81 `auth-mac enable`, `dot1x port-control auto` (T44274);
`auth-web-server intercept-port 8080` (T44275); `auth-web-server dhcp ipaddress|lease` (T44276).
T44274 removes the inherited MAC user `00-90-0b-2a-11-c3` (so eth6 falls through to web) and re-adds it
from its encrypted line (as T33375 did 10-29). On tb5: route `8.8.8.0/24 via 192.168.50.1 dev eth6`
(T44275, `hostnet route-add`, removed by `route-del`).

**Restore recipe (anyone can run it):**
1. swi_dut `configure terminal`: `interface port1.0.81` -> `no auth-mac enable`, `no dot1x port-control`,
   (re-)`auth-web enable`, `auth host-mode multi-supplicant`, `auth forward arp|dhcp|dns`; `exit`;
   `no auth-web-server intercept-port 8080`; `no auth-web-server dhcp ipaddress`, `no auth-web-server dhcp lease`;
   `radius-server local` -> `no user ck...`, `no user 02-00-5e-c0-ff-..`; if missing,
   `user 00-90-0b-2a-11-c3 encrypted password mssv+c7URUgtfltKy46Rt1ydpHKUTY8WiQr1zgQjGbY= group TWOSTEP`; `end`.
2. `rcdiff.py` the new `show running-config` against `baseline/swi_dut-pre-run.out`: identical (exit 0).
   `show boot` still `flash:/x980-autoorder.cfg`.
3. tb5: `tools/tb sudotool tb5 wa1528 hostnet route-del`, then `hostnet show`: no 8.8.8.0/24 route.
4. eth6 web session: re-authenticate eth6 with a ck user (`ckrestore`), then delete that user (10-29 answer).
5. `end`, `terminal no monitor`, `exit` on every console opened; re-probe both boxes read-only.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33355 | (192) Authentication&Security_IEEE 802.1X - IEEE 802.1X-2004 | B | PASS | "Pass" — already tested and finished, stated by the Test Engineer 2026-10-29 15:5x; not run in this campaign | — | Test Engineer |
| T33358 | (195) Authentication&Security_IEEE 802.1XEncryptionType - EAP-TTLS | C | NOT TESTED | BLOCKED D3: needs an external RADIUS with EAP-TTLS (the DUT's local RADIUS offers MAC/MD5/TLS/PEAP only); Test Engineer: "don't test these right now" | — | Test Engineer |
| T44271 | (197) Authentication&Security_IEEE 802.1XEncryptionType - EAP-LEAP | C | UNSUPPORTED | "Not Supported" — already tested and finished, stated by the Test Engineer 2026-10-29 15:5x; not run in this campaign (the DUT's local RADIUS offers MAC/MD5/TLS/PEAP only, measured at triage) | — | Test Engineer |
| T44272 | (198) Authentication&Security_IEEE 802.1XEncryptionType - EAP-OTP | C | UNSUPPORTED | "Not Supported" — already tested and finished, stated by the Test Engineer 2026-10-29 15:5x; not run in this campaign (no EAP-OTP on the local RADIUS, measured at triage) | — | Test Engineer |
| T33354 | (191) Authentication&Security_IEEE 802.1X - EAP-Notification | C | PASS | "Pass" — already tested and finished, stated by the Test Engineer 2026-10-29 15:5x; not run in this campaign | — | Test Engineer |
| T44274 | (204) Authentication&Security_WebAuthentication - Multiple Authentication | A | PASS | web (W ckweb), MAC (M ff01) and 802.1X (D ckdot1x) authenticated together on port1.0.81, 4/4 ICMP each; wrong-password and unknown-MAC controls 0/4; health CLEAN | webauth-2026-10-29T1528/T44274/work/run1.log | tester |
| T44275 | (207) Authentication&Security_WebAuthentication - Proxy Server for Web Authentication | A | PASS | with intercept-port 8080 a proxied request (8.8.8.8:8080) got the login page from the DUT's MAC, not without it (4 SYNs unanswered) nor on 8081; direct login wrong 0/4, right 4/4; routed after login. Info: a login POST sent THROUGH the proxy got no response (Tips&Tricks: login network must be No Proxy) | webauth-2026-10-29T1528/T44275/work/run1.log | tester |
| T44276 | (208) Authentication&Security_WebAuthentication - DHCP Server for Web Authentication | A | FAIL | web-auth DHCP service accepted and shown "DHCP server: enabled" but never OFFERed: 0 offers to DISCOVERs the DUT counted on port1.0.81 (+5 in, 0 out), in 5 configs (.254 same subnet, 192.168.60.1/24, +/- auth forward dhcp, vlan1 unaddressed); lease/login/2nd-client legs skipped. **Open (sentinel 16:26):** running-config had `no service dhcp-server`; run1.log does not show it was tried, so a missing enable step is not ruled out | webauth-2026-10-29T1528/T44276/work/run1.log | tester |

## Issues
