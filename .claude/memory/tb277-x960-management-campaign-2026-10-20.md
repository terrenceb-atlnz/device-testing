---
name: tb277-x960-management-campaign-2026-10-20
description: "14 AWPTCM Management cases on the x960-56YSQ, 12 PASS / 1 FAIL / 1 NOT TESTED; keepers are T47199 (a device on the factory password warns nobody), T33413 (the hw-monitoring trap is sent with its enable command removed) and the AW+ chained `| exclude` that is silently swallowed"
metadata:
  node_type: memory
  type: project
---

2026-10-20 on tb277, DUT **AT-x960-56YSQ S/N `A2WQS700B`**, build `sin_x96056-20261012-24`.
Fourteen cases in four groups by `bench-runner` subagents under a sentinel, run **unattended**:
**12 PASS, 1 FAIL, 1 NOT TESTED**. Logs `tb277/x960/{aaa,snmpmon,mgmt,tacacs}-2026-10-20T0825/`,
handover `tb277/x960/SESSION-HANDOVER-2026-10-20.md`.

RADIUS T33407/T33408/T33409 · RMON T44308 · Trap-Temperature T33413 · Per-port link trap T44301 ·
sFlow T44309 · Telnet T33378 · Default-password warning T47199 · Triggers T33416 ·
TACACS+ T33411/T33410/T33412 · Flexera T33427 (dropped).

**The three findings worth a developer:**

- **T47199 FAIL — a device still on the factory password `friend` gives no warning, on any
  path.** 0 warnings in 6 logins, with a `banner exec` marker proving the instruments see a
  message at that exact position, plus a RestCONF cross-check. The cause looks like the stored
  hash being `$5$` (SHA-256) where the check expects MD5, read off the product's own engineering
  page. The unread `def_pwd_chg` limb is the one caveat.
- **T33413 — the hw-monitoring environment trap is sent with `snmp-server enable trap
  hw-monitoring` REMOVED and never re-added.** Two controlled 150 s captures: group removed, and
  the whole SNMP config rebuilt with community + host only. Both still delivered assert and
  clear. **Deliberately not claimed:** that the group gates nothing (only the temperature sensor
  was stimulated), nor that a reload would behave the same — the live alternative is that the
  state is read at daemon start, making this a delay rather than missing gating. Settling it
  needs a reload the campaign could not do.
- **AW+ silently swallows a chained `| exclude` after `| include`.** The whole string after
  `include` is taken as one alternation pattern, so ` exclude IMISH` becomes another alternative
  in the include regex. No `% ` error, the command succeeds, nothing is excluded — **the output
  looks filtered and is not.** It hits the STANDING-ORDERS §8 health read directly. Fix: save the
  output and filter it box-side. `platforms/x960.md` §7G.

**The method lesson is its own memory:** [[cli-surface-is-not-the-device-surface]]. T33413 was
first graded NOT MEASURABLE from an exhaustive CLI probe; the Test Engineer's `start-shell`
method produced the real trap. Run 2 superseded run 1.

**Also measured:** the DUT stores management secrets three ways and the **SNMP community is
plaintext**; TACACS+ has no port option (locked to TCP/49) where RADIUS has settable ports;
`local` at the end of a method list falls back on an **unreachable** server, never on an
authoritative Reject — which nearly caused a console lockout when I advised otherwise.

**Process, measured:** 147.9 M cache-read, **campaign overhead 20.9 %** (10-16 was 9 %, 10-15 was
46 %). One group hit **60.6 %** — 103 overhead calls against 59 case calls — because it read the
rules corpus in many small calls instead of one. Cost per call rises ~1.8x within a group, so
front-load every read. Two template problems surfaced: `show cpu` on the x960 **never prints an
idle percentage** although the `HEALTH:` template asks for one, and three partner `.cfg` files
were never captured because only the DUT's config was saved.

**Left open:** both partners (swi_b on u3, swi_a on u5) **refuse their console login** at wrap,
while swi_b is demonstrably alive and linked (swi_d sees its LLDP neighbour). Cause not
established, nothing tried, because guessing credentials risks a lockout. Also open: whether the
L3 underlay may be written to startup-config, which gates reboot persistence for the whole
campaign.

Related: [[tb277-x960-mcast-bfd-vrrp-campaign-2026-10-16]], [[scapy-for-traffic-tests]],
[[log-is-the-deliverable]], [[campaigns-measured-for-token-waste]],
[[sentinel-session-keeps-long-runs-moving]], [[grading-authority-tier-list]].
