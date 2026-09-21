# Authentication group — IE520, tb470, 2026-09-22

7 cases. **1 PASS / 6 UNMEASURED — but read the split before reading the count.**

| case | title | verdict |
| --- | --- | --- |
| [33375](33375.log) | MAC Auth / Web Auth | **PASS** (both halves, end to end) |
| [38432](38432.log) | IEEE 802.1X - Authentication with TACACS+ | **UNMEASURED** — no TACACS+ server exists; **802.1X itself PROVEN** |
| [28126](guest-vlan-28126-28129.log) | L3 guest vlan IPv4, hw fwd disabled | **UNMEASURED** — needs 2 supplicants + line rate |
| [28127](guest-vlan-28126-28129.log) | L3 guest vlan IPv4, hw fwd enabled | **UNMEASURED** — same |
| [28128](guest-vlan-28126-28129.log) | L3 guest vlan IPv6, hw fwd disabled | **UNMEASURED** — same |
| [28129](guest-vlan-28126-28129.log) | L3 guest vlan IPv6, hw fwd enabled | **UNMEASURED** — same |
| [38435](38435.log) | Tri-auth / VCS - Master Failover | **UNMEASURED** — case has NO STEPS in ck.db |

## What was actually proven on the DUT

The UNMEASURED count is about what the *cases* ask for, not about the DUT's
authentication working. All three methods were driven end to end and passed:

| method | unauthenticated | authenticated | DUT evidence |
| --- | --- | --- | --- |
| MAC auth | 0/10 blocked | 9/10 forwarded | `macBasedAuthenticationSupplicantNum: 1` |
| Web auth | 0/10 blocked | 10/10 forwarded | `Supplicant name: testuser`, `webBased…: 1` |
| 802.1X | 0/10 blocked | 10/10 forwarded | `dot1xAuthenticationSupplicantNum: 1`, supplicant `EAP state=SUCCESS` |

Guest VLAN assignment also works: `auth guest-vlan 200` puts the unauthenticated
port into VLAN 200 untagged.

## Why the six are UNMEASURED

- **38432** — its subject is TACACS+, which does not exist on this bench (no
  binary at any absolute path, 0 dpkg matches, no TCP/49 listener). 802.1X was
  proven against RADIUS instead, and that is recorded as the substitute it is.
- **28126–28129** — all four need L3 traffic **between two supplicants** (this
  bench has one usable supplicant port) and their distinguishing claim is a
  **rate** claim (loss vs line rate) that scapy at ~10 pps cannot separate. The
  case text names ixia.
- **38435** — `num_steps = 0` in ck.db. No procedure, no expected result.

## Two non-obvious findings

- The DUT sends the MAC to RADIUS as **`00-f0-4d-00-77-17`** — lowercase,
  hyphen-separated. A `00f04d007717` user never matches, and this build has no
  `auth-mac username-format` command to change it.
- Default host-mode is **single-host**, so one *failed* supplicant occupies the
  port and a good MAC behind it never authenticates. `multi-supplicant` fixes it.

## Bench state at exit

Restored: `port2.0.2` plain access switchport, all auth disabled, local RADIUS
users and server removed, vlan 200 deleted, transit verified 10/10.
