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

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T44299 IPv6 NTP Client | `ntp6-2026-10-22T1122` | **RUNNING** | Mirrors yesterday's T33400 (IPv4 client) with the family swapped. **The server must be reachable over IPv6 from the DUT.** First choice is tb277's own ntpd — **check it is listening on IPv6 and that the box↔DUT leg has IPv6 reachability before designing the case**; `ss -lun` on the box, then a counted leg. swi_a served IPv6 NTP yesterday but is **not available this session** (u5 not opened). 🔴 `show ntp status` and `show ntp counters` return **EMPTY output, not an error** — read them before and after configuring and report if they stay empty. 🔴 **The DUT clock is UTC, 13 h behind the box** — record the pair once. 🔴 tb277's ntpd has `limited kod` armed: a boot-time burst draws a **kiss-o'-death, refid RATE**, which cost 10 m 55 s to converge yesterday and nearly became a false defect report. Expect it; it is the bench, not the DUT |
| B | T33401 Syslog Facility Override; T33402 Syslog stored in NVS; T33403 Scripting | `oper-2026-10-22T1122` | QUEUED (after A) | Three Operation cases, all DUT-centric. **T33401** needs a syslog collector that records the facility byte — run one on tb277 and grade on the **received PRI**, not on `show log config`. **T33402 is the reboot case**: `write` + `reload` are permitted; prove storage survives a cold boot with nothing typed afterwards. **T33403**: establish what "scripting" means on this platform before designing — `.scp` activation, trigger scripts, or neither — and say which. 🔴 A file-driven `activate <script>.scp` from the box's `/tftproot` needs a **root write to the box** (STANDING-ORDERS §4) — that limb is `NEEDS TEST ENGINEER:`, not something to work around |

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

## Issues
