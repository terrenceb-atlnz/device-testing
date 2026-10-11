# Session handover — tb277 / x960-56YSQ — 2026-10-12

## Session facts
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 (swi_c, DUT), u3 (swi_b), u5 (swi_a)
PDU: 10.36.230.212; outlets u2=1, u3=7 · 10.36.230.35; outlet u5=3
Constraints: none stated. Power cycles allowed (Test Engineer, 2026-10-08).

Bench chosen by rule 1: this session's own bench (the campaign's Session facts).
Campaign: `CAMPAIGN-QUEUE-2026-10-08T1637.md`, 13 AWPTCM cases, 2026-10-08 → 2026-10-12.

## TL;DR
**The bench is WHOLE and restored.** All 13 cases ran: **12 PASS, 1 FAIL**. Final logs and
per-device `.cfg` files exist for every case, so nothing is left to produce. Running-config and
startup-config on the DUT are identical, so a reload changes nothing.

The campaign's headline is **three mirroring defects**, one of which is the single FAIL, and they
share a theme worth acting on: **`show mirror` on this platform does not reliably describe what
the dataplane is doing.** Five mirroring cases would have passed on a status read-back alone.

## Current bench state, and how to verify it
Verified by reading the hardware on 2026-10-11/12, not from memory.

| unit | console | power | role | boot source | boot pointer | state |
| --- | --- | --- | --- | --- | --- | --- |
| swi_c (DUT) AT-x960-56YSQ | u2 @115200 | on | standalone Active Master, Ready | **netboots** `x960-tb277.rel` | `flash:/default.cfg` **(file exists)** | clean |
| swi_b AT-x960-28YSQ | u3 @9600 | on | standalone Active Master, Ready | `flash:/backup.rel` (file exists) | `flash:/default.cfg` (file exists) | clean |
| swi_a AT-x950 GEN2-52XSTQm | u5 @9600 | on | standalone Active Master, Ready | netboots `x950GEN2-tb277.rel` | `flash:/default.cfg` **(file NOT found)** | pre-existing, see OPEN-1 |

Nothing is left `shutdown`. No unit was left powered off. The DUT's uptime (2 d) reflects the
last D3 reload of the campaign, not a fault.

```bash
sock=/run/user/$(id -u)/keyring/ssh
# occupancy, opening NO console
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 \
  'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 precheck --consoles u2,u3,u5'
# regenerate bench-state.md from the hardware
SSH_AUTH_SOCK=$sock ssh -o BatchMode=yes tb277 \
  'cd ~/claude/device-testing/bench-setup && python3.8 bench_probe.py --box tb277 run \
     --consoles u2,u3,u5 --no-prompt --pdu 10.36.230.212 --outlet u2=1,u3=7'
```
**tb277 runs python3.6 as `python3`, and `bench_probe.py` dies on it (`capture_output`). Use
`python3.8` for every tool on that box.**

Topology: `bench-setup/tb277/bench-state.md` (regenerated 2026-10-11T202947Z; device and link
rows identical to the campaign's start, Advisories: none).

## What was accomplished
- Triaged all 13 cases, confirming every drafted command family on the DUT with `?` and no CR.
- Ran all 13 across four groups, each with its bench setup and exact restore recipe committed
  **before** its first case.
- Built the final `.log` + `.cfg` deliverables for all four groups.
- Restored the bench after every group and verified each restore by config diff and re-probe.

## Results
From the queue's `## Results` table. **Final logs created for all four groups** — nothing is
pending `/create-logs`, and no `work/` folder remains anywhere under `tb277/`.

| group | cases | verdicts | final logs |
| --- | --- | --- | --- |
| `mirror-2026-10-08T1637` | T44967, T44968, T44969, T44973, T44974 | 4 PASS, **1 FAIL** | `21be3bb` |
| `acl-num-2026-10-08T1637` | T44987, T44988, T44986 | 3 PASS | `d4c9b89` |
| `acl-named-2026-10-08T1637` | T44979, T44991, T44989, T44990 | 4 PASS | `67713ee` |
| `acl-lag-2026-10-08T1637` | T44992 | 1 PASS | `affaef1` |

Every run is labelled **clean**. No run was confounded: each verdict rests on frame-level or
counter evidence with its own control, and the two reloads were both deliberate persistence
tests, not recoveries.

## Findings

### MEASURED — the three mirroring defects (the campaign's main output)
1. **`mirror interface <src> direction both` copies NO frames.** Accepted, reported correctly by
   `show mirror`, `show mirror interface <src>` and the running-config, and it survives a save
   and reload — but nothing is copied. **This is the single FAIL (T44969).** Proven against the
   product and not the method: it was saved to flash and the DUT reloaded, so on that pristine
   boot there was no re-application history to blame, and it still copied nothing while
   `transmit` and `receive` applied on that same boot each delivered their 6 frames. Reproduced
   five times. Ruled out first: settle time, a second destination bounce, link state both ends,
   host capture (`0 packets received by filter` on an unfiltered run), and a wedged mirror engine.
2. **A re-applied mirror copies nothing until the destination port is bounced** (`shutdown` /
   `no shutdown`). Only the first-ever mirror on a port takes effect immediately. `show mirror`
   reports it Enabled and correct throughout.
3. **An in-place `direction` change is silently ignored** — no error, and `show mirror` keeps
   reporting the OLD direction, which the dataplane also keeps using. `no mirror interface <src>`
   must come first.

   **Consequence for anyone testing mirroring here: `show mirror` is not evidence.** Use a frame
   capture, and bounce the destination port before measuring.

### MEASURED — ACL behaviour
- **An UNBOUND access-list consumes NO classifier entry.** Six lists defined with one bound reads
  `ACL 1`. The Falcon rule budget is spent per **binding**, not per definition.
- **The ingress classifier pool reports 1024 entries**, not the 2.5K–3K the TPS and
  `platforms/x960.md` §2 describe. Each bound rule costs exactly one.
- **The same rule costs 1 entry via `access-group` but 3 via `service-policy input`** — a 3x
  multiplier for the identical logical rule.
- **`show access-list counters` stays at 0 on the service-policy path** while the rule is
  demonstrably enforcing. A working QoS-bound ACL reads as dead.
- **A bound NUMBERED list cannot be edited** (`% ...is currently attached...cannot be edited`,
  entry silently dropped) while **a bound NAMED list can** (advisory, edit applies on `end`).
  The two messages differ by one word and mean opposite things.
- **`access-group <1-99>` returns `% Access-list does not exist`** for a standard list that
  `show access-list` prints in full. The real constraint is that `access-group` takes only
  3000–3699, 4000–4699 or a named hardware list; the binding point for a standard list is the
  global **`vty access-class`**, not the Cisco-style line-mode `access-class`, which does not exist.
- Software ACLs implicitly DENY; hardware ACLs implicitly PERMIT.
- `proto 1` / `proto 6` are stored and displayed as `icmp` / `tcp`.
- The MAC mask is a **wildcard** (1 = don't care), proven from both the traffic side and the
  rule side.
- **`copy-to-cpu` lands on CPU receive-queue 0 and still forwards; `send-to-cpu` does not forward
  and does not touch queue 0.** Same hit count, opposite forwarding outcome.
- **`copy-to-mirror` terminates ACL processing at the first match** — proven by an order-only
  pair.
- `no mls qos enable` is rejected; the negation is **`no mls qos`**, which does not prompt
  (whereas `mls qos enable` does).

### MEASURED — two regressions did NOT reproduce
- **CR30477** (STP interference from send-to-cpu): spanning tree byte-for-byte unchanged.
- **CR56263** (NSM crash on `mirror interface none`): NSM stayed at the same pid throughout.

### NOT MEASURABLE on this bench
- **CPU receive-queue 6** is clear-on-read and carries this bench's continuous control traffic
  (RSTP, LLDP, loop-detect at 1/s — about 40 counts in 8 s idle). A handful of test packets is
  not separable from that floor, so **queue 6 cannot evidence send-to-cpu here, and its silence
  must not be read as a negative result.** Queue 0 is clean.

## OPEN questions
- **OPEN-1 — swi_a holds no config across a reboot.** `show boot` reads
  `Current boot config: flash:/default.cfg (file not found)`; it netboots with empty flash.
  Pre-existing, not caused by this session, and it cost nothing here because swi_a was isolated
  throughout. **A later campaign that needs swi_a must reconfigure it after any reload.**
  Evidence: `show boot` on u5.
- **OPEN-2 — is a 1024-entry ingress classifier pool expected on `sin_x96056-20260921-9`?** The
  TPS and `platforms/x960.md` §2 describe 2.5K–3K for Falcon. If 1024 is correct, the project's
  rule budget needs restating; if not, it is a defect. Evidence:
  `show platform classifier statistics utilization brief`.
- **OPEN-3 — `send-to-mirror` and `deny-and-not-cpu` are absent** from the numbered hardware
  forms, though `platforms/x960.md` §5 lists both among the actions a verdict is graded against.
  No case needed them. Evidence: `access-list 3000 ?` and `access-list 4000 ?`.
- **OPEN-4 — the three mirroring defects and the diagnostic defects need CR wording.** That is
  the Test Engineer's call; the logs hold the measurements.
- **OPEN-5 — `work-box/` folders** remain in `mirror-2026-10-08T1637/` (49 files) and
  `acl-named-2026-10-08T1637/` (10 files): raw captures and console transcripts preserved off the
  box mid-campaign. They are group-level, so `/create-logs` does not remove them. Nothing in the
  final logs depends on them. **Keep or delete as you prefer.**
- **OPEN-6 — `flash:/precampaign.cfg` (1703 B) is deliberately left on the DUT** as the only
  byte-exact copy of the pre-campaign startup config. A direct copy back onto `default.cfg` is
  **refused** by the platform (`% Cannot overwrite flash:/default.cfg as it is the default config
  file`), so the restore re-saved the running-config instead; `default.cfg` is now 1714 B, the
  11-byte difference being `lldp run`, which `bench_probe` enables by design. Delete
  `precampaign.cfg` only when the baseline is no longer wanted.

## Ordered next steps
1. **Push.** Everything is committed locally and **not pushed** (Claude cannot push here).
2. Decide OPEN-2 and OPEN-4; raise CRs if wanted.
3. Fold the findings above into `platforms/x960.md` — §2 (the 1024 pool), §5 (the absent actions,
   the numbered-vs-named edit rule, the `vty access-class` binding point, `no mls qos`).
4. Decide OPEN-5 and OPEN-6 (delete or keep).
5. The AWPTCM "Not Executed" list for x960-56YSQ held 47 cases; 13 are now done. The next
   campaign picks up from the remainder.

## Recipes

**Re-create the campaign's deterministic L2 path** (used by groups 1–4; full setup/restore with
step ids is in the queue file):
```
swi_b: port1.0.16 shutdown; port1.0.4 no static-channel-group;
       port1.0.16 switchport access vlan 100 + static-channel-group 1;
       port1.0.1, port1.0.8, port1.0.11 shutdown; interface vlan100 ip address 10.38.22.70/27
swi_c: port1.0.16 shutdown; port1.0.4 no static-channel-group + switchport access vlan 1 + shutdown;
       port1.0.14 shutdown; port1.0.8 shutdown;
       port1.0.16 switchport access vlan 100 + static-channel-group 1;
       port1.0.48 switchport access vlan 100
both:  port1.0.16 no shutdown
host:  ip addr add 10.38.22.66/27 dev eth4      # the non-matching control source
gate:  sa1 = port1.0.2 + port1.0.16 on BOTH units; ping 10.38.22.65 and .66 -> 10.38.22.70 both 0% loss
```
Shut the LAG member on both ends **before** editing it: every port runs
`loop-protection loop-detect ldf-interval 1 fast-block`, whose action is `vlan-dis` for 7 s.

**Measure a mirror honestly** (never trust `show mirror`):
```
1. no mirror interface <src>        # remove any existing mirror first
2. interface <dest> ; mirror interface <src> direction <dir>
3. interface <dest> ; shutdown ; no shutdown        # REQUIRED, or nothing is copied
4. tcpdump -i <host NIC on dest> -n 'icmp'  while pinging across the monitored port
5. count echo REQUESTS (ingress on the monitored port) against REPLIES (egress)
```

**Set both device clocks to box local time** before any capture correlation — the DUT logs in UTC
and the two switches' clocks drifted ~12 h apart. `clock set <HH:MM:SS> <DD MMM YYYY>` is
exec-only and leaves no running-config footprint, so it needs no restore.

## Pointers
- Topology and measured bench facts: `bench-setup/tb277/bench-state.md` (generated — never edit).
- Names and PDU outlets: `bench-setup/tb277/tb277.static`.
- The campaign, its setup/restore recipes per group, Results and Issues:
  `tb277/x960/CAMPAIGN-QUEUE-2026-10-08T1637.md`.
- Platform facts for this family: `platforms/x960.md`.
- Deliverables: `tb277/x960/<group>-2026-10-08T1637/<id>/` — one `.log` plus `swi_c.cfg` and
  `swi_b.cfg` per case, and a `README.md` verdict table per group.
- Logging rules and the final-log template: `logged-output.md`.
