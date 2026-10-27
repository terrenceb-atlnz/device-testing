# CR draft — <case> → <CR key>

Source: <case log path>. Build: <build>. Fields grouped by Jira tab, in Jira's order; paste each
fenced block as-is (Jira wiki markup). **Do not fill RCA.**

Rules below are from the wiki (read 2026-10-27 via tb470, `curl …&action=raw`):
**G** = [Jira CR Creation and Verifying Guidelines](https://wiki.atlnz.lc/awpwiki/index.php/Jira_CR_Creation_and_Verifying_Guidelines) §2.5–2.7,
**S** = [CR severity definitions](https://wiki.atlnz.lc/awpwiki/index.php/CR_severity_definitions),
**M** = [Must Fix Decision Process](https://wiki.atlnz.lc/awpwiki/index.php/Must_Fix_Decision_Process).

## Decisions before filing
Open questions for the Test Engineer (priority, regression/new-platform answers, split or not,
duplicate search result). Not pasted anywhere.

## Before creating (G §2.1)
Duplicate check: search [Bug Search](http://bugsearch.atlnz.lc/) (all Jira + ClearQuest CRs) or
Jira `project = CR AND text ~ "..."`. List the search terms used and the hits.

---
## Main tab

### Summary
`[<release> MF][<platform>] <nature of the issue> when|if|during <context>` (G). It is the search
key for duplicates, so name the symptom in the words someone would search for. The MF tag only
if it is on a must-fix list; **no `[SVT]` tag** (another department's, Terrence 2026-10-27).

### Priority (S)
| | AW+ definition (short) |
| --- | --- |
| 1 - Blocker | device non-operational: firmware can't load/boot, all features down. **Not** "blocks a test" |
| 2 - Critical | crash/reboot of a core module, lock-up, data loss, leak; affects the overall system |
| 3 - Major | loss of function in one area (STP, VLAN, RIP, QoS ...), device not locked up; protocol crash with data loss; security risk; hard-to-debug-in-field |
| 4 - Minor | simple workaround, or unrealistic/limited conditions; also "a Sev 3 with a workaround" |
| 5 - Trivial | display only |
Sev 2/3 may drop to 4 if non-customer-affecting. Give the line of S the choice rests on.

### Basic Analysis (G, M)
Keep the proforma exactly — no lines added or deleted; clarifying text after an item is allowed.
Replace every `Y / N` with **`Y` or `N`** (never `Y/N N`). Every `N` on the degradation/regression
and binary-search lines needs a reason, e.g. `N - Issue is specific to a new platform and/or
feature so degradation check is not required` (that does NOT excuse the regression check) or
`N - Analysis not performed as I believe this CR will not be a must fix because ...`.
- **Repeatable** = seen more than once. **frequency** = actual reproductions out of actual tests,
  never reduced or a %; several runs listed separately plus a total
  (`Run 1: 1 out of 87 / Run 2: ... / Total: 3 out of 432`).
- **Regression** = not present in the latest GA; **degradation** = not present in the last two
  major releases (users' view). Binary search only if very likely Must Fix.
- **Blocks testing** = blocks test cases OTHER than the one that raised it, and actually stops them.
- **New feature/platform**: `Y` + name it. On a new platform it counts only if the issue is shown
  NOT to occur on an existing platform (M "New Feature").
```
# Repeatable: Y / N
#- frequency: x out of y
# Degradation or regression keyword set: Y / N
#- Regression/Degradation process followed: Y / N
#- All builds tested that contain this issue:
#- All builds tested that do not contain this issue:
# Binary search performed: Y / N
#- All mainline builds tested that contain this issue:
#- All mainline builds tested that do not contain this issue:
#- Changelog link:
# Blocks Testing keyword set: Y / N
#- number of tests blocked:
# New feature/platform: Y / N
```

### Keywords (G)
`regression` / `degradation` / `blocks_testing` only when Basic Analysis says so (each pushes to Must Fix).

### Issue Description (G)
- **Description**: what, when, how (why if known); state the **expected** behaviour; state the
  network impact (or that none was seen).
- **Consequences**: how it affects the network and whether it recovers — e.g. "unexpected traffic
  flow ... never recovers, a reboot is required".
- **Reproduction Method**: steps someone else can follow. **No console output here** (that is Debug Output).
```
h4. +Description:+

h4. +Consequences:+

h4. +Reproduction Method:+
```

### Network Configuration / Device Configuration
`DUT : peer` then `port : port` lines (as CR-92097). Device config reduced to what reproduces it
(G §2.3: simplify units and config; say what removing parts did, if tested).

### Linked Issues
Related CRs if known.

### Attachment (G)
Core files, tech-support, network diagram, logs, scripts, configs, IXIA streams, **pcap files**
(`tcpdump -w`: console tcpdump text lacks bytes). Meaningful names: which reproduction each is from.

---
## Debug Output tab

### Debug Output (G)
Output with the issue **NOT** seen, then the same output with it seen; mark the lines that show
the fault with `<=====`. Pick the counters that prove it. Tech-support is attached, not pasted.
```
{noformat}
...
{noformat}
```

### Core File Output
`-`, or the core run through http://awpbuild.atlnz.lc/core_interpreter/.

---
## Found On tab
- **Found Stage**: blank (ATLNZ).
- **Affects Version/s**: the versions seen on; `Mainline` if it happens on main.
- **Component/s**: best guess, at least one; IPv4/IPv6/CLI combine with a protocol component;
  `zFeature Not In This List` if nothing fits.
- **Show System**: required — the DUT's real `show system`, verbatim (never reconstructed).

---
## Not ours
RCA (company AI), Mitigation (written in the Must Fix process if not MF; see Mitigation_Definitions),
Resolution Details, Verification, ISSU, RED *, Decision, Risk, Release Notes.
