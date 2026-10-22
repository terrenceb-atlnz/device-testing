# Campaign queue — tb277 x960-56YSQ, the 4 remaining AWPTCM Management cases, from 2026-10-22 11:22 NZDT

The ask, verbatim: *"Lets execute these remaing sets now- the 4 test cases you were concerned
yesterday"*, with the AWPTCM "Not Executed" panel for x960-56YSQ showing exactly four cases.

These are the four the Test Engineer dropped from the 2026-10-21 campaign
(*"Ignore the last 4 ids - just run the 14 test case"*). Nothing else is in scope. Per the
Test Engineer's standing instruction, **this list is the whole requirement — it is never
reconciled against any other list of cases.**

**This file is the resume point.** `/test-mode --resume tb277/x960/CAMPAIGN-QUEUE-2026-10-22T1122.md`
picks up at the first row that is not DONE or BLOCKED.

## Session facts

Recorded 2026-10-22 11:0x–11:2x NZDT from the Test Engineer's own answers to `/test-mode` §1.

Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: **u2 = swi_d (AT-x960-56YSQ, the DUT) — THIS SESSION OPENS NO OTHER CONSOLE**
PDU: 10.36.230.212 outlet u2=1
Constraints: Window: **partly attended** — the Test Engineer is intermittently available, so a
             `NEEDS TEST ENGINEER:` may wait. The tester carries on with other runnable work.

The bench answer given was **"Same as 2026-10-21"**. It was then **narrowed by the Test
Engineer to the DUT only** when the credential position below came out. Both answers are
recorded; the narrowing is the operative one.

### 🔴 Why u3 and u5 are not opened — this is a lockout guard, not a bench fault

`CK_PASSWORD_U3` / `CK_PASSWORD_U5` are **not set in this session's environment**, and
`tools/tb` forwards only what is in the environment. A probe that opens u3 or u5 without them
falls back to trying three default passwords. **AW+ locks an account at five failed logins and
every further failure re-arms the five-minute timer**, so that fallback is what locked swi_b
mid-campaign on 2026-10-21 (memory `console-driver-retries-are-lockout-generators`).

Asked how to get the password to the tester, the Test Engineer chose **"DUT only — don't open
u3/u5"**. So:

- `--consoles u2` on every probe and every driver call. **u3 and u5 are not opened, not probed,
  not pinged over serial, and nothing is typed at their login prompts.**
- The partner roles all four cases might want (NTP server, syslog collector) are played by
  **tb277 itself**, as they were for T33399/T33400/T44298 yesterday.
- **If a case genuinely cannot be graded without a partner switch, it is reported BLOCKED with
  the exact reason** — never by guessing a credential. The unblock is one line: the Test
  Engineer puts the password in `~/.ckenv` (chmod 600, outside the repo) and the tester sources
  it.

### Constraints LIFTED and PERMISSIONS GRANTED for this campaign

- ✅ **The "do not reboot swi_a" constraint is LIFTED** (Test Engineer, 2026-10-22). It was
  offered on 2026-10-21 on the sentinel's reading of `Current boot image : Not set` as a
  missing boot pointer. That reading was **wrong**: swi_a **netboots**, so `Not set` is correct
  for it (`platforms/x960.md` §7I). Moot in practice this session, since swi_a is not opened.
- ✅ **swi_d may be written to startup-config and reloaded, as often as a case needs**
  (Test Engineer, 2026-10-22). This was asked because **T33402 (Syslog stored in NVS) cannot be
  graded without a reboot** — non-volatile storage that is never shown to survive a power
  interruption has not been measured. The tester removes its own configuration from BOTH
  running- and startup-config at the end of the case that added it, and proves the removal by
  re-reading, never by the absence of an error.

## Occupancy — checked before anything, 2026-10-22 11:2x NZDT

`tools/tb precheck tb277 u2`: **u2 free** (`/dev/u2 -> /dev/ttyUSB2`, no holder). One FOUND
item, `ser2net` (pid 744, root, up 41 days) — the box's own console daemon. It is **the
identical process the Test Engineer adjudicated "Proceed" for both the 2026-10-20 and the
2026-10-21 campaigns**, so it is treated as a standing adjudication and nothing was displaced.
It does not hold u2: `sudo -n fuser -v /dev/ttyUSB2` returns no holder, and `/etc/ser2net.conf`
has no `ttyUSB2` line. The Test Engineer's own login on pts/1 is information only.

**u3 and u5 were not checked, because this session does not open them.**

## Rules

- Verdicts, working logs, the `RESULT` line, the results list and the final log template:
  **[logged-output.md](../../logged-output.md)**. The final logs are made only by
  `/create-logs`, on the Test Engineer's request — the tester never writes one.
- `STANDING-ORDERS.md` in full. In particular **§7 (scapy, not ping)** and **§8 (a health read
  before step 1 and after the last step, every case)**. `/create-logs` refuses a case whose log
  has no sourced `HEALTH:` block, and that case keeps its `work/`.
- `platforms/x960.md` — the DUT family's measured quirks. §7G–§7I are from the last two
  campaigns.
- `MANUAL-ONLY.md` — a listed case or step is reported MANUAL-ONLY and never run unattended; a
  new person-needed step found here is added to it, dated.

## 🔴 All four cases have NO authored text — confirmed before dispatch

Read from `ck.db` on tb277, 2026-10-22 (`tools/ckcase.py`, which must run ON a testbox):

| case | title | `has_objective` | `num_steps` | steps column |
| --- | --- | --- | --- | --- |
| AWPTCM-T44299 | (265) Management_NTP - IPv6 NTP Client | **0** | 1 | 53-char placeholder |
| AWPTCM-T33401 | (266) Management_Operation - Syslog Facility Override | **0** | 1 | 53-char placeholder |
| AWPTCM-T33402 | (267) Management_Operation - Syslog stored in NVS | **0** | 1 | 53-char placeholder |
| AWPTCM-T33403 | (269) Management_Operation - Scripting | **0** | 1 | 53-char placeholder |

All four: folder `/New Platform Test (MASTER)/New Platform Template/Management`, status Draft,
`script_type STEP_BY_STEP`, label `New_Platform_Management`. The 53-character steps column is
the empty JSON placeholder, exactly as all fourteen were yesterday.

**So each test is designed from three sources, in this order:** the title, the **X960 TPS** row
for that feature, and the DUT's own CLI surface. Write the designed steps into the working log
before running them, so the final log can carry them.

**Fetch the TPS at triage** (last modified 2026-10-19 when fetched yesterday); readable from a
testbox, not from the dev host:

```
wiki.atlnz.lc/awpwiki/index.php?title=X960_platform_support_TPS&action=raw
```

Rows already read yesterday that bear on this campaign: **260 NTP Server(IPv4) · 261 NTP
Client(IPv4) · 262 IPv6 NTP Server = Yes**. **Triage must read the rows for 265 (IPv6 NTP
Client), 266, 267 and 269 itself** — a TPS "No" is the grounds for UNSUPPORTED, and a TPS "Yes"
against a DUT that lacks the feature is a **finding**, not a bench limit
(memory `review-feature-docs-before-testing`).

## 🔴 The CLI surface is not the device's surface

Before grading anything UNSUPPORTED or NOT MEASURABLE because no command exists, say *"no CLI
command exists"* in exactly those words, then ask whether the platform exposes it another way.
`start-shell` reaches a root Linux shell (`tools/awshell.py`); that is how T33413 went from NOT
MEASURABLE to PASS. This is live for **T33402** (where syslog is actually stored is a filesystem
question) and **T33403** (what a "script" is on this platform).

## Group A bench setup and RESTORE RECIPE — written 2026-10-22 ~11:05 UTC, BEFORE the first case

Written by the tester before touching the DUT, so a fresh tester can restore the bench if this
session dies mid-case. Group A is `ntp6-2026-10-22T1122`, one case, **AWPTCM-T44299**.

**Run `.setup`:** `tb277/x960/ntp6-2026-10-22T1122/tb277-u2.setup` — declares **swi_d and
nothing else**, so the framework's post-failure power cycle can never reach u3 or u5.
Probe `--consoles u2` against it: **exit 0 MATCH**.

**Gate record, 2026-10-22 ~11:00–11:05 UTC**
- `tools/tb precheck tb277 u2` → `/dev/u2` **free**, no holder. One FOUND item, `ser2net`
  pid 744 (root, up 41 d) — the box's own console daemon, the standing adjudication already
  given for the 2026-10-20, 2026-10-21 and today's triage. Nothing displaced. **u3/u5 untouched.**
- `tools/tb peek tb277 ntp61022 u2 115200` → `'awplus login:'`. **The console was NOT parked
  mid-state** — no `[root@… ~]#` shell, no `(config…)#` prompt.
- `tools/tb template tb277` → **no deployed `/home/st-art/configs/tb277.setup`**, as expected on
  this box. Never bind one.
- Probe capture: `bench-setup/tb277/captures/2026-10-21T230452Z`.
- 🔴 The probe regenerated `bench-setup/tb277/bench-state.md` as a **swi_d-only** record,
  dropping swi_a and swi_b (7 insertions, 25 deletions) because only u2 was opened. The
  tracked file was **reverted** to the committed three-unit version, whose
  `Generated 2026-10-21T201917Z` stamp honestly says when three units were last measured. The
  swi_d-only regeneration is kept in the tester's scratchpad. Nothing on the bench changed.
  (Same handling the sentinel applied at triage.)

**What the case ADDS to swi_d, and nothing else**

| what | where | why |
| --- | --- | --- |
| `ipv6 address fd32:b1f0:dff8:1603::34/64` | `interface vlan10` | the leg SVI has no IPv6 at all today; this is the DUT end of the box's eth3 ULA `/64` |
| `ntp server fd32:b1f0:dff8:1603::1` | global | tb277's own ntpd, the server under test |
| `ntp server fd32:b1f0:dff8:1603::99` | global | the **control** — an unused address on the same `/64` that must never be answered |
| a deliberately wrong `clock set` | runtime only | to produce a real correction to measure; the client puts it back |
| `write` + `reload` | startup-config | the reboot-persistence limb, explicitly permitted by the Test Engineer 2026-10-22 |

**Nothing else is touched.** In particular: `vlan 60` is the Test Engineer's and is left alone;
the vlan10 / vlan48 IPv4 L3 underlay is campaign infrastructure in startup-config and stays.

**RESTORE RECIPE — run this on u2 (115200) if the session dies mid-case**

```
configure terminal
 no ntp server fd32:b1f0:dff8:1603::1
 no ntp server fd32:b1f0:dff8:1603::99
 interface vlan10
  no ipv6 address fd32:b1f0:dff8:1603::34/64
 exit
exit
write
```
Then prove it, do not assume it:
```
show running-config | include ntp
show running-config interface vlan10
show startup-config | include ntp
show ipv6 interface brief
show ntp status            <- must be COMPLETELY EMPTY again (that is the unconfigured state)
show boot
show clock
```
Expected after restore: **no `ntp` line** in either running- or startup-config, **no IPv6
address on vlan10**, and `show boot` back at the baseline

```
Current boot image : flash:/x960-tb277.rel (file exists)
Current boot config: flash:/default.cfg (file exists)
Autoboot status    : disabled
```
build `sin_x96056-20261019-27`, standalone, Active Master.

If the clock was left wrong by an interrupted step 4, the IPv6 client itself corrects it once
`ntp server fd32:b1f0:dff8:1603::1` is re-applied; otherwise `clock set <hh:mm:ss> <d mon yyyy>`
in UTC, against the box's `date -u`. The DUT runs **UTC**; the box displays **NZDT (UTC+13)**.
Last: `end`, `terminal no monitor`, `exit` (shared box — log out of u2).


## Group B bench setup and RESTORE RECIPE — written 2026-10-22 ~12:5x UTC, BEFORE the first case

Written by the tester before touching the DUT, so a fresh tester can restore the bench if this
session dies mid-group. Group B is `oper-2026-10-22T1122`, three cases, in order:
**AWPTCM-T33401** (Syslog Facility Override) → **AWPTCM-T33402** (Syslog stored in NVS) →
**AWPTCM-T33403** (Scripting).

**Run `.setup`:** `tb277/x960/oper-2026-10-22T1122/tb277-u2.setup` — declares **swi_d and
nothing else**, so the framework's post-failure power cycle can never reach u3 or u5.
Probe `--consoles u2` against it: **exit 0 MATCH**.

**Gate record, 2026-10-22 ~12:4x–12:55 UTC**
- `tools/tb precheck tb277 u2` → `/dev/u2` **free**, no holder. One FOUND item, `ser2net`
  pid 744 (root, up 41 d) — the box's own console daemon, the standing adjudication already
  given for the 2026-10-20, 2026-10-21 and today's campaigns. Nothing displaced. **u3/u5 untouched.**
- `tools/tb peek tb277 oper1022 u2 115200` → `'awplus login:'`. The console was **NOT parked
  mid-state** — no `[root@… ~]#` shell, no `(config…)#` prompt.
- `tools/tb template tb277` → **no deployed `/home/st-art/configs/tb277.setup`**. Never bind one.
- Probe captures: `bench-setup/tb277/captures/2026-10-21T235239Z` (relative `--template` path
  was not resolved — the probe runs with the box's own checkout root, so the template must be
  given box-absolute) and `2026-10-21T235303Z` (**exit 0 MATCH** against the run `.setup`).
- 🔴 The probe again regenerated `bench-setup/tb277/bench-state.md` as a **swi_d-only** record.
  The tracked file was **reverted** (`git checkout --`) to the committed three-unit version;
  the regeneration is kept in the tester's scratchpad. Nothing on the bench changed.
- Boot baseline read from the DUT at 12:54 UTC, which **T33402's and any other reload must
  return to**:
  ```
  Current software   : x960-tb277.rel
  Current boot image : flash:/x960-tb277.rel (file exists)
  Default boot config: flash:/default.cfg
  Current boot config: flash:/default.cfg (file exists)
  Autoboot status    : disabled
  ```
  Build `sin_x96056-20261019-27`, uptime 0 days 00:23:48 (group A's reload), standalone.

**Baseline the three cases measure from, read before anything was changed**

| read | value |
| --- | --- |
| `show log config` → `Facility:` | **default** (the clean OFF for T33401) |
| Buffered log | enabled, 50kb, filter `*1 Level notices` |
| Console log | enabled, filter `*1 Level critical` |
| **Permanent log** | enabled, 50kb, filter `*1 Level **warnings**` (the T33402 trap) |
| Monitor / External log | monitor filter debugging; external **disabled** |
| `show running-config \| include log` | only `aaa authentication login default local` — **no `log` configuration of any kind** |
| `show startup-config \| include log` | the same one line |
| `show trigger` | `% No triggers currently defined` |
| `dir flash:` | no `.scp` file present |
| ports **down and unused** | port1.0.20, port1.0.21 (and 1.0.3, 1.0.5–1.0.7, 1.0.9, 1.0.11–1.0.13, 1.0.15, 1.0.17–1.0.19, 1.0.22–1.0.47, 1.0.49+) |
| ports **running** (never touched) | port1.0.2 (RSTP root port, carries the Test Engineer's vlan 60), 1.0.4, 1.0.8, 1.0.10 (box eth3), 1.0.14, 1.0.16, 1.0.48 (box eth4) |
| box legs | eth3 `10.38.22.33/27` ↔ DUT vlan10 `10.38.22.34/27`; eth4 `10.38.22.65/27` ↔ DUT vlan48 `10.38.22.66/27` |
| clock pair | DUT `UTC Wed, 21 Oct 2026 23:54:25 +0000` vs box 2026-10-22 12:54 NZDT — **13 h behind** |

🔑 **The log generator these cases use.** Every CLI command typed is logged by the DUT as
`user.notice awplus IMISH[<pid>]: [manager@ttyS0]<the command text>`, and a rejected one adds
`user.err awplus IMISH[<pid>]: Command [<text>] failed`. So typing a harmless command that
carries a unique marker (`show log | include CKT33401-A`) produces a syslog message with known
text, known facility (`user`, 1) and known severity (`notice`, 5) — PRI 13 — on demand. That is
the stimulus for T33401 and T33402, and it needs no port flap and no traffic.

**What group B ADDS to swi_d, and nothing else**

| what | case | why |
| --- | --- | --- |
| `log host 10.38.22.33` | T33401 | the collector leg (box eth3); the capture is the collector |
| `log host 10.38.22.65` | T33401 | a second REAL destination, to show which facility knob wins per destination |
| `log host 10.38.22.40` | T33401 | the **control** — an unused address on the same `/27` that must draw zero syslog packets |
| `log facility local5` | T33401 | the global override under test |
| `log host 10.38.22.33 facility local1` | T33401 | the per-destination override, measured against the global one |
| `log permanent level informational` | T33402 | the default filter is `warnings`, so a notice-level marker is NOT stored without this |
| `flash:/ckt33403.scp`, `flash:/ckt33403b.scp` | T33403 | the scripts, TFTP'd from the box's `/tftproot` (mode 1777, `tftpd-hpa` active — no root write) |
| `description CKT33403-*` on port1.0.20 | T33403 | the artefact that proves a script RAN, rather than was merely accepted |
| `trigger 1` (`type interface port1.0.20 down`, `script 1 ...`) | T33403 | the trigger-driven half of the scripting surface |
| `shutdown` / `no shutdown` on port1.0.20 | T33403 | the trigger stimulus; the port is **down and unused** |
| `write` + `reload` | all three | permitted by the Test Engineer 2026-10-22; T33402 cannot be graded without one |

**Nothing else is touched.** In particular: `vlan 60` and `port1.0.2` are the Test Engineer's
and are left alone; the vlan10 / vlan48 IPv4 L3 underlay is campaign infrastructure in
startup-config and stays; no port that is currently `running` is shut, flapped or reconfigured.

**RESTORE RECIPE — run this on u2 (115200) if the session dies mid-group**

```
configure terminal
 no log host 10.38.22.33
 no log host 10.38.22.65
 no log host 10.38.22.40
 no log facility
 no log permanent level informational
 no trigger 1
 interface port1.0.20
  no description
  no shutdown
 exit
 interface port1.0.21
  no description
  no shutdown
 exit
exit
delete force flash:/ckt33403.scp
delete force flash:/ckt33403b.scp
write
```
(`no log permanent level informational` must put the filter back to **`Level warnings`** —
check it in `show log config`, and if the negation leaves another level, set it explicitly.)

Then prove it, do not assume it:
```
show log config                            <- Facility: default; Permanent filter Level warnings
show running-config | include log          <- only `aaa authentication login default local`
show startup-config | include log          <- the same one line
show running-config | include trigger      <- nothing
show trigger                               <- % No triggers currently defined
show running-config interface port1.0.20   <- no description, no shutdown
show running-config interface port1.0.21   <- no description, no shutdown
dir flash:                                 <- no .scp file
show interface brief                       <- port1.0.20/21 admin up; the seven running ports unchanged
show boot                                  <- the baseline above
show clock
```
Last: `end`, `terminal no monitor`, `exit` (shared box — log out of u2).

🔴 **After ANY reload: ping the leg to 4/4 before reading anything.** A login prompt is not
readiness. And swi_d's out-of-band `eth0` link-local **changes across a reboot**, so never
cache it and expect the box's `ip -6 neigh` to hold a stale entry.

🔴 **/tmp on tb277 has ~90 MB free of 2.0 G**; 1.8 G is someone else's `wireshark_eth4*.pcapng`
and is **not ours to delete**. Every capture in this group is bounded (`-c` and a time limit)
and removed when its case is graded.

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T44299 IPv6 NTP Client | `ntp6-2026-10-22T1122` | **DONE — PASS** | Mirrors yesterday's T33400 (IPv4 client) with the family swapped. **The server must be reachable over IPv6 from the DUT.** First choice is tb277's own ntpd — **check it is listening on IPv6 and that the box↔DUT leg has IPv6 reachability before designing the case**; `ss -lun` on the box, then a counted leg. swi_a served IPv6 NTP yesterday but is **not available this session** (u5 not opened). 🔴 `show ntp status` and `show ntp counters` return **EMPTY output, not an error** — read them before and after configuring and report if they stay empty. 🔴 **The DUT clock is UTC, 13 h behind the box** — record the pair once. 🔴 tb277's ntpd has `limited kod` armed: a boot-time burst draws a **kiss-o'-death, refid RATE**, which cost 10 m 55 s to converge yesterday and nearly became a false defect report. Expect it; it is the bench, not the DUT |
| B | T33401 Syslog Facility Override; T33402 Syslog stored in NVS; T33403 Scripting | `oper-2026-10-22T1122` | **DONE — 3 PASS** | All three graded and committed (`1db87d2`, `96573fe`, `62e89d8`), bench restored, probe exit 0 MATCH, u2 logged out. New tool `tools/syslogwire.py` + README entry (`b9e657d`). Two findings for the Test Engineer: **F-1** `log host <ip> facility` is a message-selection FILTER, not a per-destination override; **B-1** swi_d has TWO PSUs and the session's single PDU outlet cannot power-cycle it (sent as `NEEDS TEST ENGINEER:`). T33403 closes the open item in `platforms/x960.md` §7F.8. |

Both groups run on the **same single console**, so they run **sequentially**, A then B. Nothing
runs on the bench between groups.

## 🔴 What the bench already carries, so it is not mistaken for this campaign's residue

Left by the 2026-10-21 campaign and **confirmed at its wrap probe (Advisories: none)**:

- **The layer-3 underlay on swi_d is in startup-config**, deliberately (Test Engineer's decision,
  2026-10-21). It is campaign infrastructure. **Do not remove it.**
- 🔴 **`vlan 60` is in swi_d's running- AND startup-config.** It is **the Test Engineer's to
  remove** (`no interface vlan60` / `no vlan 60`), still outstanding at the time this queue was
  written. **The tester does not remove it and does not report it as its own leftover.**
- swi_d: `sin_x96056-20261019-27`, boot image `flash:/x960-tb277.rel` **(file exists)**, boot
  config `flash:/default.cfg` (file exists), standalone, Ready, Active Master.
- RSTP, single instance, **root is swi_b**; the active tree is a line,
  swi_d —(1.0.2)— swi_b —(1.0.1)— swi_a. 2 of 6 inter-switch links forward. **There is no
  forwarding loop** — counted traffic legs are safe. Re-verify at triage; it was measured
  yesterday, not today.
- Host NICs eth2, eth3, eth4 all `carrier=1`. The bench **flash-boots**; no TFTP path is needed
  for a swi_d reload.
- 🔴 **`/tmp` on tb277 is 96 % full** (1.9 G of 2.0 G). 1.8 G of it is `wireshark_eth4*.pcapng`
  **belonging to someone else and NOT ours to delete**. **Bound every capture** (`-c`, or a
  time limit and a size check) and clean up your own files.

## 🔴 Method rules carried forward — each one has already cost a session

- **A LOGIN PROMPT IS NOT READINESS.** After any reload, ping every leg to **4/4** before
  reading it. Three sightings in one hour yesterday, and one of them would have **inverted a
  verdict**: a permitted host's first post-boot leg read as blocked, which looks exactly like a
  working filter. This campaign reboots the DUT at least once (T33402), so it applies directly.
- **A TIMEOUT IS NOT A MEASUREMENT.** When a wait ends without the thing you were waiting for,
  the window is a variable, not a result. If an earlier leg of the same case did it faster, the
  **inconsistency is the finding** — extend the window and decode what is actually on the wire
  before writing a defect against the product.
- **Never chain `| exclude` onto `| include`.** AW+ takes the whole string after `include` as one
  alternation pattern, so the second filter silently becomes another alternative. No error is
  printed and **the output looks filtered and is not** (`platforms/x960.md` §7G). Save the
  output and filter it box-side.
- **`show cpu` on the x960 never prints an idle percentage**, although the `HEALTH:` template
  asks for one. Record what it does print.
- **Two console calls in one tool block run sequentially** — a watcher issued beside a DUT
  change sees nothing. Start a capture with `run_in_background` FIRST, or drive both ends from
  one process.
- **Frame-level evidence or it did not happen** (STANDING-ORDERS §7). Every counted leg carries
  a **control flow that must NOT match**, sent in the same run. A verdict rests on the pair.

## 🔧 Tooling note — `tools/awlogin.py` was fixed this morning (commit `fdaded7`)

`login()` now submits a username+password **exactly once** (`cred_attempts=1`). `Login
incorrect` returns False immediately instead of looping, and the username is typed per character
below 19200 baud with its echo verified before the password is sent. The old `tries=5` loop was
a retry count exactly equal to the platform's lockout threshold. Verified on hardware (tb277 u2)
this morning. **If a login fails, it now fails once and tells you — do not re-run it in a loop
to "make sure".**

## ✅ TRIAGE ANSWER, 2026-10-22 11:39 NZDT — 4 runnable, 0 blocked. Test Engineer: **"go ahead"** (11:5x)

Measured on swi_d through u2 only. No device state changed, no case run.

**Both blockers this queue anticipated were DISPROVED by measurement:**

1. 🔴 **The scripting limb does NOT need a root write to the box.** This queue said an
   `activate <script>.scp` served from `/tftproot` would be a STANDING-ORDERS §4 item. It is
   not: **`/tftproot` is mode `1777`** (world-writable, sticky, symlinked from `/tftpboot`)
   with `tftpd-hpa` **active**, so a plain user stages the file and the DUT pulls it with
   `copy tftp://10.38.22.33/<f>.scp flash:/<f>.scp` — the method already endorsed in memory
   `file-to-unit-via-device-copy-tftp`. A second zero-box-write route is to write the `.scp`
   on the DUT through `start-shell` (`tools/awshell.py`). **T33403 has no blocking limb.**
2. 🔴 **No partner switch is needed for the IPv6 NTP case.** tb277's own ntpd listens on IPv6
   on every leg and is synced (`reach 377`), so losing swi_a costs this campaign nothing.

**Gates.** Occupancy: u2 free, one FOUND item (`ser2net` pid 744, the standing adjudication),
nothing displaced, u3/u5 never touched. Probe `--consoles u2`: **exit 1 MISMATCH, no
Advisories, no USER-CONFLICT** — all 15 lines are the expected artefact of probing one console
against a deployed template that describes **swi_a only**. Nothing to resolve, nothing to apply.

**Boot baseline T33402's reload must return to**, read from the DUT today:

```
Current software   : x960-tb277.rel
Current boot image : flash:/x960-tb277.rel (file exists)
Default boot config: flash:/default.cfg
Current boot config: flash:/default.cfg (file exists)
Autoboot status    : disabled
```
Build `sin_x96056-20261019-27`, standalone, Active Master.

**No forwarding loop — re-measured 11:32 NZDT today, not inherited.** RSTP converged, root
`8000:0000cd423029` (swi_b), **one** root port `port1.0.2` Forwarding, `port1.0.4` / `1.0.14` /
`1.0.16` Alternate/Discarding, and **both box legs Designated/Forwarding** (`port1.0.10` ← eth3,
`port1.0.48` ← eth4). Counted traffic legs are safe. *(This is the same state as 2026-10-21: the
"2 of 6 forwarding" recorded then counted the swi_a—swi_b link, which swi_d cannot see.)*

### TPS — all four rows say **Yes**, so no case has UNSUPPORTED grounds

| TPS No. | item | supported | case |
| --- | --- | --- | --- |
| 263 | NTP / IPv6 NTP Client | **Yes** | T44299 |
| 264 | Operation / Syslog facility override (Log) | **Yes** | T33401 |
| 265 | Syslog stored in NVS (Log) | **Yes** | T33402 |
| 267 | Scripting | **Yes** | T33403 |

🔴 **The bracketed number in each case title is offset +2 from the TPS row number**
(263→"(265)", 264→"(266)", 265→"(267)", 267→"(269)"). The TPS row *numbered* 265 is "Syslog
stored in NVS" = **T33402**, not the NTP case. **Never look these cases up by the bracketed
number.** Anchor: 260 NTP Server(IPv4), 261 NTP Client(IPv4), 262 IPv6 NTP Server.

Since every row is Yes, **a feature missing on the DUT would be a finding, not a bench limit.**

### Measured prerequisites, per group

**A / T44299 — IPv6 NTP source AVAILABLE.**
- tb277's ntpd listens on `[fd32:b1f0:dff8:1602::1]:123` (eth2), `[fd32:b1f0:dff8:1603::1]:123`
  (eth3), `[fd32:b1f0:dff8:1604::1]:123` (eth4) and `[::]:123`; service active, `ntpq -p` shows
  `*ntp.atlnz.lc st 4 reach 377`. chrony/chronyd/ntpsec inactive.
- Box has ULA IPv6 on all three legs; `net.ipv6.conf.all.forwarding = 1`.
- **IPv6 box↔DUT proven today: `ping -c 3 -I eth2 fe80::9c31:61ff:fef7:77e7` → 3/3, 0% loss,
  rtt 0.494/0.623/0.714 ms.**
- DUT surface: `ntp server ?` accepts `X:X::X:X`; `ntp source` takes an address, which is how
  the poll is pinned to a leg. `show ntp status` returns **completely empty output, no error**
  (unconfigured) — record it before and after.
- DUT IPv6 today: eth0 `fe80::9c31:61ff:fef7:77e7/64`, vlan1 link-local; **vlan10/48/60 have no
  IPv6**, so the case adds a ULA to the leg SVI and removes it afterwards.
- 🔴 **Budget for the kiss-o'-death.** `/etc/ntp.conf` carries
  `restrict -6 default kod notrap nomodify nopeer noquery limited` — identical to the IPv4 line
  that cost 10 m 55 s to converge on 2026-10-21. **Our bench's ntpd, not a DUT defect.**
- 🔴 Clock pair, once: DUT `UTC Wed, 21 Oct 2026 22:32:24 +0000` vs box 2026-10-22 11:32 NZDT —
  **13 h behind**.

**B1 / T33401 — the collector is a CAPTURE, and it is available.**
- **No UDP :514 listener on tb277.** `rsyslog` inactive with `imudp` commented out; `syslog-ng`
  running but binding no syslog UDP port. **Starting or reconfiguring either is a root change
  (§4) and is NOT needed.**
- Grade on the **received PRI** (`PRI = facility*8 + severity`) from a bounded
  `tcpdump … udp port 514` capture. `sudo -n` is passwordless and `tcpdump` is present.
- DUT surface: `log facility ?` offers all 20 RFC3164 facilities; `log host <ip> facility` also
  exists (per-destination); `log host ?` accepts `X:X::X:X`, so an **IPv6 syslog limb is free**
  if wanted. Baseline `show log config` → **`Facility: default`** — a clean OFF to measure from.
- 🔧 **`tools/` has NO syslog decoder** (60+ entries, none). A generic `tools/syslogwire.py`
  is needed: decode PRI/facility/severity/host/tag from a `tcpdump -w` pcap and count by
  facility, built on `snmpwire`'s classic-pcap reader the way `ntpwire.py` is. It goes in
  `tools/` **with its `tools/README.md` entry**, never loose in the lab tree.

**B2 / T33402 — the NVS mechanism is present and already on.**
```
Permanent log:
  Status ......... enabled
  Maximum size ... 50kb
  Filters:  *1  Level ...... warnings   Program .... any   Facility ... any
  Statistics ..... 11668 messages received, 36 accepted, 0 excluded
```
`show log permanent` exists; `log permanent ?` offers `size level program msgtext exclude
facility`. ⚠️ **The filter defaults to level `warnings`, so a notice-level event is NOT
stored.** The case must raise the filter (`log permanent level informational`) or generate a
warning-or-worse event — **and put the filter back**.

**B3 / T33403 — the scripting surface is `activate` + `trigger`.**
- exec `activate ?` → `SCRIPT  Script to activate` / `background`;
- config `trigger ?` → `<1-250>`, entering trigger-config mode;
- `show trigger` → `% No triggers currently defined` (present, nothing configured — clean
  baseline). ⚠️ **that line starts with `% ` and is informational**, so a stop-on-error driver
  will abort on it;
- 🔴 **`show script` → `% Unrecognized command`.** Write it in exactly those words: *no
  `show script` CLI command exists*. The surface is `activate` + `trigger`, and `dir flash:`
  lists the file. The CLI surface is not the device's surface.

### Bench facts learned at triage (the Test Engineer's to record, or not)

- **Box `eth2` is cabled to swi_d's out-of-band `eth0` management port**, not to a switchport.
  That is why its MAC is learned on no switch port, and it explains the probe's one NEEDS-CHECK
  `[portlink] tb-swi_a eth2 CHECK_CABLE` as a **stale template line, not a mis-cable**.
  Proven: `fe80::9c31:61ff:fef7:77e7` is swi_d eth0, and the box's `ip -6 neigh` holds it on
  `dev eth2` with lladdr `9e:31:61:f7:77:e7`.
- The DUT's L3 underlay as measured: vlan10 `ckUNDERLAY-eth3` port1.0.10 `10.38.22.34/27`;
  vlan48 `ckUNDERLAY-eth4` port1.0.48 `10.38.22.66/27`; vlan60 `ckMGMT-A` port1.0.2(t)
  `10.38.22.97/27`; eth0 IPv4 unassigned.
- 🔴 **vlan 60 sits on `port1.0.2`, which is the RSTP ROOT PORT.** If the Test Engineer removes
  it, re-check STP afterwards.

### Two triage claims the sentinel checked and CORRECTED

- The report said the branch was **"46 ahead / 39 behind origin"** and that it should be
  resolved before adding a tool. **It is not**: `git rev-list --left-right --count
  main...origin/main` read **2 ahead, 0 behind** with a clean tree. That line was the
  2026-10-22 handover's OPEN 1 text, not a current reading. Nothing is blocked. (The foreign
  stash is still present and still blocks nothing.)
- The probe **overwrote `bench-setup/tb277/bench-state.md` with a swi_d-only record**, dropping
  swi_a and swi_b from the shared bench file (25 lines removed). The regeneration was kept in
  the sentinel's scratchpad and the **tracked file reverted** to the three-unit version, whose
  `Generated 2026-10-21T201917Z` stamp honestly says when it was measured. Nothing on the bench
  changed, so no information was lost.

### MANUAL-ONLY

None of the four is listed, and triage found **nothing new needing a person**: no cable swap,
no LED, no GUI, no account, no removable media, no partner switch. Nothing was added.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| AWPTCM-T44299 | (265) Management_NTP - IPv6 NTP Client | ntp6-2026-10-22T1122 | **PASS** | Originates NTPv4 mode-3 over IPv6 and is answered — 8/11/13/13 requests in four captures, every one paired; Stratum 6 from a stratum-5 IPv6 source; real clock steps of 2.241471 s and 50.914095 s; the identically-configured unreachable IPv6 control drew **zero** packets in every window; silent on removal; survives a cold boot with nothing typed | `ntp6-2026-10-22T1122/T44299/work/run1.log` | tester, 2026-10-22 |
| AWPTCM-T33401 | (266) Management_Operation - Syslog Facility Override | oper-2026-10-22T1122 | **PASS** | The **global** `log facility` override is in force on the **received PRI byte**, never read off `show log config`: 25/25 + 25/25 `local4` at two destinations at once, severity untouched, an unreachable control at zero in every window, and **387/387 `local4` across four severities after a cold boot with nothing typed**; removal complete in running-config, startup-config and on the wire. TPS 264 satisfied by the global command. FINDING F-1: **`log host <ip> facility <f>` is a message-SELECTION FILTER, not a per-destination override** -- accepted, shown in running-config one line below `log facility`, reads exactly like an override, never rewrites the PRI. Proved negatively twice (with and without a global override in force) and positively once: a destination whose only filter was `facility user` took 7/7 user messages and ZERO syslog-facility ones while the other destination took five in the same window. **Bench mechanism that nearly became a false FAIL**: with no UDP/514 listener on tb277 every datagram draws an ICMP port-unreachable, the DUT's syslog-ng marks the destination broken and reopens after exactly 60 s (`time_reopen='60'`), flushing the backlog in a sub-millisecond burst -- **three capture windows read ZERO while the feature worked perfectly**; windows were 170 s thereafter. New tool `tools/syslogwire.py` (`b9e657d`). Health-after DIRTY, adjudicated CLEAN with full reasoning in section 11; run **clean, not confounded**. `rcdiff` pre vs post: no output, exit 0, across a reload. | oper-2026-10-22T1122/T33401/work/run1.log | tester |
| AWPTCM-T33402 | (267) Management_Operation - Syslog stored in NVS | oper-2026-10-22T1122 | **PASS** | Five entries written before a restart read back from `show log permanent` **with nothing typed**, while the identical entries are gone from `show log`; markers generated AFTER `write` survived too. **Storage named down to the media**, not inferred: permanent = `/flash/log/messages` on `/dev/mmcblk0p1`, **ext3 on the eMMC**; volatile = `/var/log/messages` on a **10240k tmpfs**. **STEP 4 is PARTIAL AS DESIGNED and the log says so in those words.** An abrupt power cut was ATTEMPTED FIRST -- non-volatile storage shown to survive only a graceful restart has not really been tested -- and could not be achieved: see bench finding **B-1** in this file, swi_d has two PSUs and one outlet. Graded on a `reload` instead, which is a real discriminator because the volatile log was **measured** to be on a tmpfs rather than assumed. The stronger test is declared **NOT MEASURABLE on this bench**, not quietly skipped. **MF-1, a method trap**: `show log permanent | include <pattern>` **NEVER returns a prompt when the pattern matches nothing** -- measured twice, each wait exactly the driver's timeout (180 s, then 600 s, long enough for the DUT's console idle-timeout to log the session out); with at least one match it returns in 4 s. **Prove an ABSENCE with `grep -c X /flash/log/messages*` in a start-shell.** **O-5**: `log permanent level <lvl>` **APPENDS** a filter rather than replacing the default -- the same filter-builder mechanism as F-1, so it is a **pattern across both cases**, not a one-off. There is no `show log buffered` on this platform; the buffered log is plain `show log`. A near-miss checked rather than assumed: `/var/log/messages.1` held 2 marker matches that looked like pre-restart content surviving in RAM and would have undermined the whole contrast -- `head -1` shows the file begins at this boot's own kernel line and the two matches are the post-restart read commands; the arithmetic closes at 5 pre-restart occurrences, flash only. Health-after DIRTY, adjudicated CLEAN in section 11; run **clean**. `clear log permanent` deliberately never run; nothing written inside the start-shell. | oper-2026-10-22T1122/T33402/work/run1.log | tester |
| AWPTCM-T33403 | (269) Management_Operation - Scripting | oper-2026-10-22T1122 | **PASS** | "Scripting" on this platform is a **`.scp` file of CLI commands on the device's flash**, run by `activate <file>` **or** by a trigger -- and **there is no `show script` command**, said in those words. A real script was executed **both ways** and proved by **an artefact only a running script could have made**, with ports the script does not name read in the same run and unchanged. The trigger's log-regular-expression condition was shown to be a **real regex** by a **one-character near-miss that it rejected in the same run as the string it accepted** -- the control and the positive in one window. The device's own **`[SCRIPT]` log prefix** shows the command came from the file, not from a console. Script, trigger and artefacts **survive a cold boot and the trigger still fires afterwards**. Everything removes cleanly, **proved by re-sending the stimulus and getting nothing** rather than by the absence of an error. The `.scp` reached flash with **no root write to the box** (`/tftproot` is mode 1777 with tftpd-hpa active), so the limb this queue flagged as a possible STANDING-ORDERS section 4 item needed nothing from the Test Engineer. **This case also closes the open item recorded in `platforms/x960.md` section 7F.8.** | oper-2026-10-22T1122/T33403/work/run1.log | tester |

## Issues

### F-1 (T33401) — there is no per-destination syslog facility override on the x960
`log host <ip> facility <f>` is accepted, appears in the running-config one line below
`log facility local4`, and reads exactly like a per-destination override of it. It is a
message-**SELECTION FILTER** on the facility a message was RAISED under, and it never
rewrites the PRI byte. Proved three ways in one case: with a global override in force it
changed nothing (25/25 still local4); with NO global override it changed nothing (a
byte-identical distribution to a destination without it); and used as a filter it selected
(a destination whose only filter was `facility user` received 7/7 user messages and ZERO
syslog-facility ones, while the other destination received five in the same window).
`show log config` is honest — it lists the setting under `Filters:` — but the CLI help
calls it "Specify a syslog facility". **TPS row 264 is still satisfied by the global
command, so T33401 is PASS.** This is a clarity-and-capability finding for the Test
Engineer, not a failure of the item under test.

### B-1 (T33402) — swi_d has TWO power supplies; one PDU outlet cannot power-cycle it
Sent as a `NEEDS TEST ENGINEER:` line during the run. `tools/tb pdu tb277 10.36.230.212 1
cycle` completed and the outlet reports on, but the DUT's uptime did not reset
(`0 days 00:18:31`, matching the earlier reload exactly) and `show reboot history` gained
no entry. `show system` lists PSU1 and PSU2, both AT-PWRSYS4, and afterwards
`show system environment` reads `PSU Power Input ... Ok` for BOTH bays. Nothing was harmed.
- T33402 is therefore graded on a `reload`, which still discriminates because the volatile
  log was MEASURED to be on a tmpfs; the stronger abrupt-interruption test is declared
  NOT MEASURABLE on this bench rather than quietly skipped.
- **The framework's own post-failure power cycle would not power-cycle swi_d either.**
- The second PSU's outlet was NOT hunted for: an outlet outside the session facts may
  belong to another unit (STANDING-ORDERS §4). **Open: which outlet feeds swi_d's PSU2?**

### MF-1 (T33402) — `show log permanent | include <pattern>` hangs when nothing matches
It prints no output and never returns a prompt; the console driver waits out its entire
per-command timeout. Measured twice, each wait exactly equal to the timeout (180 s, then
600 s — long enough for the DUT's own 10-minute console idle-timeout to fire and log the
session out). With at least one match it returns in four seconds. **Prove an ABSENCE with
`grep -c <pattern> /flash/log/messages*` in a `start-shell` instead**, which returns a
definite 0.

### O-3 (T33401) — a bench mechanism that produced three empty captures and would have been a false FAIL
tb277 runs no UDP/514 listener, so every syslog datagram the DUT sends draws an ICMP
port-unreachable. The DUT's syslog-ng reads that as `Error reading data` →
`Syslog connection broken`, stops sending, and reopens the destination exactly 60 s later
(`time_reopen='60'` in its own log), flushing everything buffered in one sub-millisecond
burst. **A capture window shorter than ~70 s can read ZERO while the feature works
perfectly.** Every measurement window in T33401 after that was 170 s.

### Closed by this group
`platforms/x960.md` §7F.8's open item — "Running a real script still needs a `.scp` on the
device's flash, which needs a root write to the box's `/tftproot` (STANDING-ORDERS §4) —
still unmeasured, as it was after T44181" — is **CLOSED by T33403**. A real script was run
by a trigger twice, before and after a reboot, and it needed no write to the testbox at
all: the `.scp` files were created on the DUT through `start-shell` and deleted again.


### 🔴 BENCH FACT, measured 2026-10-22 13:41 — swi_d has TWO PSUs, so ONE outlet cannot power-cycle it

`tools/tb pdu 10.36.230.212 1 cycle` completed and the outlet reported on, but **the DUT did not
reboot**: uptime stayed at `0 days 00:18:31` (matching the earlier reload exactly) with **no new
reboot-history entry**. `show system` lists **PSU1 and PSU2, both AT-PWRSYS4**, and after the cut
`show system environment` read `PSU Power Input ... Ok` for **both** bays. The second supply
carried the unit straight through. Nothing was harmed: Environment Status Normal, no reboot, no
log entry.

**Two consequences:**

1. **T33402 cannot be given a true AC-interruption test on this bench as configured.** It is
   graded on a `reload` — a full kernel restart, which still discriminates, because the tester
   established from `mount` inside `start-shell` that **`/var/log` is tmpfs (RAM)** and
   **`/flash/log` is ext3 on the eMMC**. The volatile/non-volatile split is proven at the
   filesystem level, not from `show` output. The working log states plainly that an abrupt power
   interruption was **attempted and could not be achieved with one outlet**.
2. 🔴 **The framework's post-failure power cycle would not power-cycle swi_d either** on this
   bench. True for any future campaign here, not just this one.

**NEEDS TEST ENGINEER (open):** the PDU outlet feeding swi_d's **second** PSU, if it is on
`10.36.230.212` and is theirs to give. The tester deliberately did **not** hunt for it: an outlet
outside the session facts may belong to another unit, which is STANDING-ORDERS §4.

