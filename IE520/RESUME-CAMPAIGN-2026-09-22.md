# IE520 campaign — RESUME RECORD

**Written 2026-09-22 ~10:30 NZST, mid-campaign, so the run can be picked up if
this session stops.** This is a resume record, NOT an end-of-session wrap. The
bench is left live and mid-flight on purpose; nothing has been torn down.

**`bench-setup/bench-state.md` has deliberately NOT been updated** (Terrence's
instruction). The bench deltas are recorded *here* instead — see §4.

---

## 1. Where we are — 37 of 72 cases graded

| group | result | commit |
| --- | --- | --- |
| ACL (13) | **11 PASS / 2 UNMEASURED** | `237fb09`, `c243c8e` |
| Authentication (7) | **1 PASS / 6 UNMEASURED** | `6ebdbda` |
| MRP (5) | **0 / 5 UNMEASURED** | `fb4771d` |
| QoS (12) | **9 PASS / 3 UNMEASURED** | `a5485f5` |
| STP & storm control (8) | **2 of 8 recorded, group IN PROGRESS** | `c1a5a9a` |
| switching (11) | not started | — |
| IPv6 routing & protocol (16) | not started | — |

**Read the UNMEASURED counts with their reasons — most are "the case's subject
does not exist on this bench", not work skipped.** Authentication in particular:
MAC-auth, web-auth and 802.1X were each driven end to end and passed; the cases
are UNMEASURED because their subject is TACACS+ (absent) or they need two
supplicants. Each group README leads with that split.

## 2. Exact next action

**Finish the STP & storm control group**, then switching, then IPv6 routing.

Done in STP: `16452` (UNMEASURED), `16453` (UNMEASURED). Still to do:
`38487` MSTP instance limit · `16388` storm-control on a static channel group ·
`6005` MAC movement/thrash · `38151` MSTP basic · `38152` RSTP basic ·
`38153` STP basic.

Confirmed syntax already paid for:
```
interface <port>
 loop-protection action {learn-disable|link-down|log-only|none|port-disable|vlan-disable}
```
Not `loop-protection loop-detect action ...` (unrecognised). Loop detection
cannot be configured on an aggregator **member** port.

**To actually close T16453** you must first remove `channel-group 1` from the
**x230's** `port1.0.2` — it is in an unformed LACP group so that leg does not
forward, which is why no loop formed. Doing so creates a genuine loop with
RSTP off on all three devices; `loop-protection action link-down` on the stack
is the only safeguard. Deliberate and watched, please.

## 3. Harness — committed, not scratch

`IE520/test-harness/{bench.py,qosbench.py,README.md}`. It was living only in
the session scratchpad and would have died with the session. `bench.py` gives
the DUT console + transit traffic; `qosbench.py` decodes DSCP/CoS/802.1p at
egress. The README documents the two grading rules (baseline-first; traffic
must TRANSIT) and the safe `?`-without-CR syntax probe.

## 4. BENCH DELTAS NOT IN bench-state.md — read before touching anything

1. **The x230/4050/stack triangle is broken ON PURPOSE.** The AR4050S's
   `port1.0.2` is `shutdown` and removed from `channel-group 1` (done 08:57 to
   break the loop before ATMF was stripped). It was never restored, because MRP
   turned out unrunnable. **RSTP is disabled on all three devices**, so closing
   that leg without a working loop protocol storms the bench.
2. `po1` is therefore a **single link**: stack `port4.0.2` ↔ 4050 `port1.0.4`.
3. **QoS**: enabled during the QoS group, then disabled again with `no mls qos`
   (`mls qos disable` and `no mls qos enable` are both invalid).
4. **`no lacp global-passive-mode enable`** on the stack, left off deliberately
   since 2026-09-21 — it auto-rejoins freed ports into new aggregations and
   fights explicit port config.
5. Stack priorities are back to baseline (1=128, 2=2, 3=128, 4=128); member 3
   is Active Master and holds the **USB stick**.
6. The x230 runs its own restored `default.cfg` — all ports vlan 100,
   `channel-group 1` on ports 2 and 4, SVI `10.38.215.2/27`, console **9600**.
7. ATMF is fully removed from all three nodes.

**Verified good at the time of writing:** stack `Normal operation`, 4/4 Ready;
all three TB paths 0% loss (eth1→10.38.215.10 via x230, eth2→.40 direct,
eth3→.70 to the 4050).

## 5. Standing blockers for Terrence (none gate the remaining groups)

- **One recable** — a second cabled port, ideally straddling stack members —
  unblocks ACL `881/885/890/889`, QoS `13604`'s straddling half, the guest-VLAN
  four, `38435`'s failover half, and the mirror-destination checks in `943`/`830`.
- **A line-rate source (ixia)** — unblocks QoS `13549`/`13553` and the
  guest-VLAN rate claims.
- **Two MRP-capable switches** — unblocks the whole MRP group.
- **Case definitions missing**: `38435` and `38148` both have `num_steps = 0`.
- **TACACS+ server** — unblocks `38432` as written.

## 6. Traps paid for today (also in the memory store)

- `mls qos enable` **and** `no mls qos` prompt `(y/n)`; a driver that feeds the
  prompt `end` gets `% Command aborted.` **and logs the console out.**
- `policy-map`/`class-map` do not parse until QoS is enabled globally.
- MAC-auth usernames arrive at RADIUS as **`00-f0-4d-00-77-17`** (lowercase,
  hyphenated); there is no `auth-mac username-format` on this build.
- Default auth host-mode is single-host: one FAILED supplicant occupies the
  port so a good one behind it never authenticates.
- `ssh tbNNN 'command -v X'` misses `/usr/sbin` and `/sbin` — proves presence
  only, never absence.
- A rejected/interrupted tool call does **not** kill an already-dispatched ssh
  command; it keeps running and holding consoles.

## 7. Git

All work is committed. **Claude cannot push — Terrence pushes.**
Campaign commits: `237fb09`, `c243c8e`, `6ebdbda`, `fb4771d`, `a5485f5`, `c1a5a9a`.
