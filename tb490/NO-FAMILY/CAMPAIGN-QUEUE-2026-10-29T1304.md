# Campaign queue — tb490 DUT + tb5 network, 4 AWPTCM Authentication & Security cases, from 2026-10-29 13:04 NZDT

The ask, verbatim: *"i want to run a campaign on TWO testboxes against a DUT located on TB490 the
rest of the network is on TB5"*, with the AWPTCM panel showing four cases (below).

**This file is the resume point.** `/test-mode --resume tb490/NO-FAMILY/CAMPAIGN-QUEUE-2026-10-29T1304.md`
picks up at the first row that is not DONE or BLOCKED.

> **Path note:** neither box had been probed when this file was written, so the DUT family was
> unknown and the file sits under `tb490/NO-FAMILY/`. Once TRIAGE measures the family it is moved
> (`git mv`) to `tb490/<FAMILY>/`, and that move is recorded here.

## Session facts

Recorded 2026-10-29 13:0x NZDT from the Test Engineer's own answers to `/test-mode` §1.

Test Engineer: jacobm@jacobm-dl
Testbox: tb490 (DUT, and the box that runs the cases) + tb5 (the rest of the network: "tb5 is for console access and logging")
Consoles: tb490 u2 = the DUT. tb5: "run the bench probe on tb5" — all its consoles, u0, u1, u2 (cleared by the Test Engineer 2026-10-29, see below)
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

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T33365 Web Auth – Public…; T33366 Web Auth – Promis…; T33357 802.1X EncryptionType…; T33375 MAC Auth/Web Auth | `auth-2026-10-29T1304` | TRIAGE | One group, one DUT console. TRIAGE may split it. |

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |

## Issues
