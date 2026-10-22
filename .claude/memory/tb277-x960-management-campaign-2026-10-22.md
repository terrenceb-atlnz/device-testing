---
name: tb277-x960-management-campaign-2026-10-22
description: "The last 4 AWPTCM Management cases on the x960-56YSQ, all PASS, run DUT-only because the partner credentials were absent; keepers are a command that reads like an override and is a filter, a dual-PSU unit that one outlet cannot power-cycle, and a `| include` that never returns when nothing matches"
metadata:
  node_type: memory
  type: project
---

2026-10-22 on tb277, DUT **AT-x960-56YSQ S/N `A2WQS700B`**, build `sin_x96056-20261019-27`.
The four cases dropped from the 2026-10-21 campaign, run by `bench-runner` subagents in two
groups under a sentinel: **4 PASS**. Logs `tb277/x960/{ntp6,oper}-2026-10-22T1122/`, handover
`tb277/x960/SESSION-HANDOVER-2026-10-23.md`, queue `CAMPAIGN-QUEUE-2026-10-22T1122.md`.

T44299 IPv6 NTP Client · T33401 Syslog Facility Override · T33402 Syslog stored in NVS ·
T33403 Scripting. **All four had NO authored text** — that is now simply normal on this suite.

**The campaign ran DUT-ONLY, and that was the right call rather than a limitation.**
`CK_PASSWORD_U3`/`U5` were not in the session's environment, and the probe's fallback tries
three default passwords — the exact path that locked swi_b the day before. Asked, the Test
Engineer chose "DUT only". **It cost nothing**: tb277 itself played NTP server and syslog
collector for all four cases. **When a credential is missing, ask whether the partner is needed
at all before asking for the credential.**

**The three keepers:**

- 🔥 **A command can read exactly like a property setter and be a filter.** `log host <ip>
  facility <f>` is accepted, sits in running-config one line below `log facility local4`, and
  **never rewrites the PRI byte** — it selects which messages reach that destination. Only a
  **PRI-byte measurement** catches it; `show running-config` misleads and `show log config` is
  honest only because it lists the setting under `Filters:`. The same mechanism turned up again
  in the same campaign: `log permanent level <lvl>` **appends** a filter rather than replacing
  the default. **One mechanism, two commands — so assume it for the rest of the family.**
- 🔴 **A dual-PSU unit cannot be power-cycled from one outlet, and the PSU read will not tell
  you.** The cycle completes, the outlet reports on, **both bays still read `Ok`** — and the
  unit never rebooted. **Uptime is the check, not the PSU status.** The consequence is wider
  than one case: **the framework's own post-failure power cycle does not power-cycle such a
  unit** on a bench that records one outlet for it. The tester tried the abrupt cut FIRST,
  found it impossible, and declared that limb **NOT MEASURABLE in those words** rather than
  quietly grading the easier test — which is the behaviour to copy.
- 🔧 **`show log permanent | include <pattern>` never returns a prompt when nothing matches.**
  Measured twice; each wait was exactly the driver's timeout, the second long enough for the
  console idle-timeout to log the session out. With one match it returns in 4 s. **So a
  non-matching `| include` is indistinguishable from a hung console.** Prove an absence with
  `grep -c` in a `start-shell`.

**A trap in the case ids themselves:** the bracketed number in these titles is **offset +2 from
the TPS row number** (title "(265)" is TPS row 263, and row 265 is a different case). Looking a
case up by its bracketed number lands two rows away.

**Method worth copying — give a log-regex trigger a pattern that cannot match its own config
line.** The DUT logs every command typed, so a naive pattern fires the instant it is configured
and every later result is ambiguous. `CK[0-9]33403FIRE` works because the config line has `[`
where the regex needs a digit, and it hands you a one-character near-miss control for free.

**This campaign closed an open item**: `platforms/x960.md` §7F.8 said running a real trigger
script needed a root write to the box's `/tftproot` (STANDING-ORDERS §4) and was "still
unmeasured". It needs no write to the box at all — `/tftproot` is mode 1777, and `start-shell`
is a second route. **An item recorded as blocked is worth re-measuring before it is believed.**

**Process, measured:** ~81 M cache-read across both groups. The headline is not a token number
but a shape: **116 of one case's 241 tool calls (48 %) were pure waiting**, 104 of them an
identical `sleep 5; echo .`, roughly 20 M of 42 M spent on nothing. `Monitor` with an until-loop
was used three times, worked, and was then abandoned for sleep chains. Also found:
`tools/case_tokens.py` cannot split a `bench-runner` campaign, because its `RESULT` regex does
not allow the `AWPTCM-` prefix and a case segment starts at the first tool call naming the case
directory, which these testers write at the END.

Platform facts: `platforms/x960.md` §7J. Related:
[[tb277-x960-management-campaign-2026-10-21]], [[console-driver-retries-are-lockout-generators]],
[[cli-surface-is-not-the-device-surface]], [[log-is-the-deliverable]],
[[campaigns-measured-for-token-waste]], [[tcpdump-nfs-root-squash-capture]].
