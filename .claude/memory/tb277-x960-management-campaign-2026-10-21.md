---
name: tb277-x960-management-campaign-2026-10-21
description: "14 AWPTCM Management cases on the x960-56YSQ, 10 PASS / 1 UNSUPPORTED / 2 NOT TESTED; seven reboot-persistence limbs measured at last; keepers are the numbered-ACL silent rule loss, a timeout that nearly became a false defect report, and 'a login prompt is not readiness'"
metadata:
  node_type: memory
  type: project
---

2026-10-21 on tb277, DUT **AT-x960-56YSQ S/N `A2WQS700B`**, build `sin_x96056-20261019-27`.
Fourteen cases in four groups by `bench-runner` subagents under a sentinel: **10 PASS,
1 UNSUPPORTED, 2 NOT TESTED, 1 deferred**. Logs
`tb277/x960/{access,mgmt,lldp,ntp}-2026-10-21T1159/`, handover
`tb277/x960/SESSION-HANDOVER-2026-10-22.md`.

Telnet/SSH client+server T33379/T33380/T33381 · Management ACL T33386 · Dynamic config T47192 ·
Management Stacking T33387 · LLDP T44296 · LLDP-MED T33398 · NTP T33399/T33400/T44298.

**Every one of the fourteen had NO authored text** — `has_objective = 0` on all of them, and the
thirteen "steps" were empty JSON placeholders. The X960 TPS was the only authority, so each test
was designed from the title, the TPS row and the DUT's own CLI surface. That is now the normal
case on this suite, not the exception.

**Reboot persistence was measured seven times — the first in three campaigns**, because the Test
Engineer allowed `write` mid-campaign once it became clear the limb was failing case after case
for a reason that was not the product's. Three of the seven were **retro-fitted to already-closed
cases as limb-only run 2s**, each about a fifth the cost of a full re-run. That is the cheap way
to close a measurement gap.

**The three keepers:**

- 🔥 **A NUMBERED hardware ACL holds exactly ONE rule, silently.** Each `access-list <n> <rule>`
  replaces the previous with no error and nothing in running-config. Every management filter is
  permit-then-deny, so the numbered form **collapses to the deny and locks the administrator
  out**. What makes it reportable is the pairing: the driver logs
  `exfx_cExt_dxch_rules_pclIdActionUpdate` at the instant of the loss, and the **named** form is
  unaffected. **That contrast spans two cases, so no single case log could carry it** — it lives
  in the campaign queue. `ntp rate-limit` behaves the same way, so assume more such surfaces.
- 🔥 **A timeout is not a measurement, and this one nearly became a false defect report.**
  T33400's post-reload NTP re-sync poll timed out at 180 s. Written up as it stood it reads *"NTP
  does not resume after a reboot"* — a defect against the product. The window was extended only
  because the same DUT had synced in ~45 s from configuration earlier **in the same case**, so
  the silence was not self-consistent. It converged at 10 min 55 s, and the decoder found why: a
  **kiss-o'-death, refid RATE** — the DUT's boot-time burst tripped **tb277's own ntpd
  `limited kod` restriction**. A property of our bench, not the DUT. **When a wait ends without
  the thing you were waiting for, the window is a variable; if an earlier leg did it faster, the
  inconsistency is the finding.**
- 🔴 **A login prompt is not readiness.** After any reload, ping every leg to 4/4 before reading
  it. Three sightings in one hour, and the third would have **inverted a verdict**: a permitted
  host's first post-boot leg read as blocked, which looks exactly like a working filter. With a
  TCP prober, *no reply row* means silently dropped.

**Also worth keeping:** replacing an unreachable partner with **the testbox itself** produced
*better* evidence than the partner would have — crafting LLDPDUs meant choosing the chassis ID,
port ID and TTL, so ageing was graded against a TTL we set rather than waiting out 120 s. Ask
whether a crafted partner is better before calling a case blocked.

**Both partner consoles were locked out mid-campaign by our own tooling** — see
[[console-driver-retries-are-lockout-generators]]. The campaign finished DUT-only and said so in
every affected log, as a console-lockout limitation rather than a bench gap.

**Process, measured:** 142.9 M cache-read, **27.6 % overhead**, 5 h 3 min of tester time.
T44296 alone was 25.8 M — 18 % of the campaign in one case — justified by zero authored steps,
twelve designed, two new tools and the first persistence measurement, but two thirds of it was
discovery that is now written down. A group's overhead *ratio* misleads when its cases are an
order of magnitude cheaper than another's: read the absolute number beside it.

Platform facts: `platforms/x960.md` §7H. Related:
[[tb277-x960-management-campaign-2026-10-20]], [[cli-surface-is-not-the-device-surface]],
[[scapy-for-traffic-tests]], [[log-is-the-deliverable]],
[[campaigns-measured-for-token-waste]], [[grading-authority-tier-list]].
