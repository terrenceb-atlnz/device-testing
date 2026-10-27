---
name: tb277-x960-auth-security-campaign-2026-10-23
description: "tb277 x960 Authentication & Security campaign — 11 cases, 11 PASS, run 2026-10-23 and finished 2026-10-28; keepers are the silent discards and secure mode"
metadata: 
  node_type: memory
  type: project
  originSessionId: e1b6a525-1ced-44a8-bded-4e12b6b39c08
  modified: 2026-10-27T22:33:59.339Z
---

Campaign `tb277/x960/CAMPAIGN-QUEUE-2026-10-23T1304.md`, build `sin_x96056-20261019-27`, DUT
swi_d on u2 only. **11 cases, 11 PASS.** Final logs created 2026-10-28 (`e20ee8b`, `fefaeee`,
`5c34210`, `3db9288`).

Two cases stood at PARTIAL after 2026-10-23 and were re-run on 2026-10-28, both becoming PASS:
- **T9032 EAP-TLS** — the DUT was never at fault. See [[eap-tls-needs-tls12-supplicant]].
- **T44287 Crypt Secure-mode** — run 1 measured the safe half read-only and stopped; the enable
  limb needs an **attended window**, and got one.

**The keepers, all in `platforms/x960.md` §7K:**
- 🔥 **Four auth commands silently discard a setting the operator entered**, each a weakening,
  none with a warning or a log entry. `auth host-mode multi-supplicant` rewrites
  `dot1x control-direction both` to `in` and `no auth host-mode` never restores it.
- 🔥 **Secure mode deviates from its documentation in four ways** — the telnet *client* still
  runs (CR-84010 not implemented), SHA-1 is refused for SNMPv3 beyond what the docs say (a
  conforming `auth sha` user is silently deleted at the next restart), the CLI help surface
  shows no restriction at all while the parser rejects what it offered, and neither route to the
  cryptographic self-test exists.
- 🔴 **Secure mode's PKI move is reversible**, but a PKI inventory read *inside* secure mode
  describes the secure-mode store and **looks exactly like catastrophic key loss**. Read both
  sides of the round trip. This produced a false alarm on 2026-10-28.
- 🔥 **`mail smtpserver authentication oauth2` is silently inert** — accepted, never written to
  running-config, previous mechanism still in force.
- 🔴 **An authored objective of `Not Support` can be wrong**: T33354's was, and the TPS row said
  Yes. Check the TPS before grading UNSUPPORTED off the objective.

**Still open after the wrap** (detail in `tb277/x960/SESSION-HANDOVER-2026-10-28.md`):
- 🔴 **`tools/snmpq.py` can report `RESULT VALUE` exit 0 for a net-snmp *usage error*** — it
  parses a line out of the usage dump. Any case passing an unsupported `--auth-proto` records a
  **false PASS**. The one open item that can change a future verdict.
- `tools/case_tokens.py` does not match the `AWPTCM-` prefix testers write, so `--find` returns
  empty per-case rows. One regex.
- tb277 cannot drive SNMPv3 against a secure-mode DUT at all (net-snmp 5.7.3 takes only MD5|SHA;
  pysnmp's hlapi will not load). Root to fix.

Related: [[tb277-x960-management-campaign-2026-10-22]], [[satisfactory-level-of-testing]],
[[grading-authority-tier-list]].
