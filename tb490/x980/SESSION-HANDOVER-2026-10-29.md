# tb490 + tb5 / x980 — session handover, 2026-10-29

The first campaign across two testboxes: the DUT on tb490, the rest of the network on tb5.

## Session facts

Test Engineer: jacobm@jacobm-dl
Testbox: tb490 (DUT, and the box that runs the cases) + tb5 (the rest of the network: "tb5 is for console access and logging")
Consoles: tb490 u2 = swi_dut (AT-x980-16CDQ, the DUT). tb5 u0 = swi_x950, u1 = swi_x530, u2 = swi_ar
          (names verbatim: "tb490 u2=swi_dut; tb5 u0=swi_x950, u1=swi_x530, u2=swi_ar")
PDU: none ("no pdus", both boxes)
Constraints: "no shared boxes all mine, run the test probe, u0 and u1 on tb490 are not to be touched"

Copied from [CAMPAIGN-QUEUE-2026-10-29T1304.md](CAMPAIGN-QUEUE-2026-10-29T1304.md).

## TL;DR

**The campaign is complete: 4 of 4 PASS. Final logs created and committed. The bench is whole.**
swi_dut is standalone, Ready Active Master, boot image `flash:/x980-tb490.rel (file exists)`, boot config
`flash:/x980-autoorder.cfg (file exists)`, no new reboot since the session started. `lldp run`, which the
first probe turned on, is off again on swi_dut, swi_x950 and swi_x530. Nothing is running on either box.
The sentinel stood down at this wrap.

🔴 **About 23 commits are local and NOT pushed.** `git push origin main` is yours.

🔴 **The AW+ default password list changed** (framework, 2026-10-19). It is not just `friend` any more:
five passwords, which equals the lockout threshold. See memory `awplus-default-password-list`.

## Current bench state and how to verify it

```bash
cd ~/claude/device-testing      # or the repo root on your dev host
tools/tb precheck tb490 u2      # never u0/u1 on tb490
tools/tb precheck tb5 0-2       # ser2net (pid 593, ttyS0/S1 only) is always FOUND; it is not a holder
tools/tb probe tb490 --consoles u2 --no-prompt --baud 115200       # NOTE: the probe turns `lldp run` ON
tools/tb sudotool tb5 <scratch> hostnet show                     # route 8.8.8.0/24 absent, jm1-jm5 DOWN
```

Bench topology: [bench-setup/tb490/bench-state.md](../../bench-setup/tb490/bench-state.md) (Generated
2026-10-29T020348Z, **MATCH**) and [bench-setup/tb5/bench-state.md](../../bench-setup/tb5/bench-state.md)
(Generated 2026-10-29T020449Z, **MISMATCH only because u1 was left out**, see below). Both files still say
`lldp run` was "switched on and left on" for swi_dut and swi_x950. That note is stale: it was reverted after
the probe.

### Per unit, as left (read at the wrap, 15:03–15:08 NZDT)

| unit | power | state | boot | running vs startup | console |
| --- | --- | --- | --- | --- | --- |
| swi_dut (tb490 u2) | on | standalone, Ready Active Master, uptime 4 h 42 m; no new reboot | `x980-tb490.rel (file exists)`, `x980-autoorder.cfg (file exists)`; autoboot disabled | running = the group A baseline (auth rig on port1.0.81, vlan1 192.168.50.1/24); differs from startup, which has the two-step rig. A reload restores startup, NOT today's running-config | logged out |
| swi_x950 (tb5 u0) | on | — | `x950-5.5.5-2.1.rel (file exists)`, `x950-twostep.cfg (file exists)` | running = startup | logged out |
| swi_x530 (tb5 u1) | on | not read at the wrap (see OPEN) | not read | `no lldp run` done by the Test Engineer | at `awplus login:` |
| swi_ar (tb5 u2) | on | — | `AR4050S-awplus_main-20251103-998.rel (file exists)`, `default.cfg (file exists)` | running-only: `security-password minimum-length 8`, `security-password history 1`, `lldp run` (found so; not this session's); startup-only: `service password-encryption`, `shutdown` on port1.0.1 | logged out |

- **eth6 on swi_dut port1.0.81** is web-authenticated as `ckrestore`, a user that was then deleted. That was
  the Test Engineer's choice ("Test user, then delete it"). It was `webuser` before the session; the
  `webuser` password is stored encrypted, so it could not be restored.
- **tb5 host:** eth6 UP (10.37.5.129/27, 192.168.50.10/24, MAC 00:90:0b:2a:11:c3); jm1–jm5 DOWN; no 8.8.8.0/24 route.
- Nothing is shut down or powered off by this session. No `write` on any unit.

## What was accomplished

- First probes of tb490 and tb5. Both now have `bench-setup/<TB>/` with `.static` (the Test Engineer's names)
  and a deployed `.setup` (`/home/st-art/configs/<TB>.setup`). The DUT ↔ x950 link crosses the boxes, so it is a
  comment in both `.setup` files, not a `[portlink]`.
- `tools/tb`: tb5 uses python3.8 (`BOX_PY`). New `tools/hostnet.py`: the narrow, approved root helper on tb5.
  `tools/httpq.py`: `--cafile`, `--no-hostname-check`, `--peer-cert`.
- New [platforms/x980.md](../../platforms/x980.md) from this run's measurements.
- Four cases run, graded and logged; `/create-logs` done.

## Results — 4 of 4 PASS. Final logs CREATED (`0149091`)

From the queue's `## Results` table, all graded by the tester, all runs *clean*:

| case | verdict | log |
| --- | --- | --- |
| T33375 MAC Auth/Web Auth | PASS | [auth-2026-10-29T1304/T33375/T33375.log](auth-2026-10-29T1304/T33375/T33375.log) |
| T33365 Web Auth X.509 | PASS | [auth-2026-10-29T1304/T33365/T33365.log](auth-2026-10-29T1304/T33365/T33365.log) |
| T33366 Promiscuous/Intercept Web Auth | PASS | [auth-2026-10-29T1304/T33366/T33366.log](auth-2026-10-29T1304/T33366/T33366.log) |
| T33357 EAP-TLS | PASS | [auth-2026-10-29T1304/T33357/T33357.log](auth-2026-10-29T1304/T33357/T33357.log) |

Group README and process review: [auth-2026-10-29T1304/README.md](auth-2026-10-29T1304/README.md),
[auth-2026-10-29T1304/REVIEW.md](auth-2026-10-29T1304/REVIEW.md).

## Findings

### Measured
- **x980 build awplus_main-20261029-90:** no `clear auth` (use `dot1x initialize interface <port>`);
  `auth-mac enable` ends existing web sessions; no `auth-web-server mode`, and interception is always on
  (extra ports via `intercept-port`); entering `crypto pki trustpoint <n>`, even from a help probe, creates it;
  `crypto key zeroize <name>` (no `rsa` keyword). All in `platforms/x980.md` §1.
- TFTP from the DUT to a client behind an Unauthorized dot1x port fails (`% Network is unreachable`).
- tb5's wpa_supplicant 2.6 cannot finish EAP-TLS over TLS 1.3; TLS 1.2 works (same as the x960).
- `bench_probe.py` always turns `lldp run` ON unless read-only. There is no option to skip it.
- The framework's default password list is five passwords (`ATDrivers/ATSwitch.py`, dated 2026-10-19).
  `bench_probe.py` and `tools/console.py` still carry the old list (see OPEN).

### Inferred, not measured
- swi_x530's password is not one of the defaults it was tried with, because it was logged in all day and one
  open made 5 failed logins. Which password it actually uses is not known here.

## OPEN

1. **swi_x530 (tb5 u1) may be locked** after 5 failed logins at 14:51:12–14:51:51 NZDT. The Test Engineer then
   logged in by hand and reverted `lldp run`, so the lock has cleared. Its wrap reads (`show boot`,
   running vs startup) were not taken. It is also missing from tb5's bench-state, so tb5 reads MISMATCH until
   it is probed with its password (`CK_PASSWORD_U1` in `~/.ckenv`).
2. **Code still on the old password list:** `bench-setup/bench_probe.py` `PASSWORDS = ["friend", "P@ssw0rd",
   "awplus"]` and `tools/console.py` (`friend`, plus CRs at `Password:`). `tools/README.md` line 92 and
   `tools/atmf_provision.py` / `tools/awshell.py` docstrings say "manager / friend". Whether to change them is
   the Test Engineer's call. Walking all five defaults would hit the lockout threshold.
3. `tb5:/tftpboot/cktls.p12` (a client certificate signed by swi_dut's local CA): the Test Engineer removes it
   (root on tb5).
4. eth6 is logged in under the deleted user `ckrestore`, not `webuser`. Restoring `webuser` needs its password.

## Ordered next steps

1. `git push origin main`.
2. Delete `tb5:/tftpboot/cktls.p12`.
3. Decide OPEN 2 (the password lists in the code).
4. Probe tb5 with swi_x530's password to get tb5 back to MATCH.

## Recipes

```bash
# Client legs run from tb5 eth6 (192.168.50.10) through swi_x530 -> swi_x950 -> swi_dut port1.0.81.
# tb490 has no NIC on any DUT switchport (eth1 reaches only the DUT's eth0 management port).
# Before every auth leg on port1.0.81:
#   x980-CDQ(config)# do dot1x initialize interface port1.0.81
# EAP-TLS: hold the supplicant at TLS 1.2 (memory eap-tls-needs-tls12-supplicant).
# Export a PKCS#12 BEFORE `dot1x port-control auto`, or the TFTP to eth6 fails.
# tb5 route for an off-subnet web-auth test (approved helper only):
tools/tb sudotool tb5 <scratch> hostnet route-add    # ... then route-del, then `show` to prove it
```

## Pointers

- Queue and Results: [CAMPAIGN-QUEUE-2026-10-29T1304.md](CAMPAIGN-QUEUE-2026-10-29T1304.md)
- Platform: [platforms/x980.md](../../platforms/x980.md)
- Memories written: `two-box-campaign-dut-and-client-on-different-testboxes`, `awplus-default-password-list`;
  updated `campaigns-measured-for-token-waste`, `console-driver-retries-are-lockout-generators`,
  `testbox-console-access`.
- orient-dt trap 2 (framework credentials) updated for the new password list.
