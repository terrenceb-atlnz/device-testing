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

## Triage

(filled by bench-runner TRIAGE)

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T44274 Web Auth – Multip…; T44275 Web Auth – Proxy S…; T44276 Web Auth – DHCP S… | `webauth-2026-10-29T1528` | TRIAGE | |
| B | T33358, T44271, T44272 802.1X EncryptionType…; T33355 802.1X-2004…; T33354 EAP-Notification…; T44277 Supplicant MAC | `dot1x-2026-10-29T1528` | TRIAGE | |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues
