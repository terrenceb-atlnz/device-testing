# Campaign queue — tb277 x960-56YSQ, 14 AWPTCM Management cases, from 2026-10-20 08:25 NZDT

The ask (Test Engineer, 2026-10-19 16:52): *"Okay we will now run the next lot of test"*, with a
screenshot of the AWPTCM **Not Executed** panel for **x960-56YSQ**, showing fourteen
`Management` cases.

⇒ **This campaign is exactly these fourteen.** The panel header read "32 test cases"; the Test
Engineer was asked and chose **the 14 shown**. Per the standing instruction of 2026-10-15 —
*"the list that I send you are the ones that you would be required to do. I won't send you the
list of test cases that have been manually done"* — there is **no reconciliation against any
other list**.

**This file is the resume point.** `/test-mode --resume tb277/x960/CAMPAIGN-QUEUE-2026-10-20T0825.md`
starts at the first row that is not DONE / BLOCKED.

Shape: ONE session (orient-dt §10 A, `/test-mode`): this session is the sentinel, `bench-runner`
subagents are the tester, one per group.

## 🔴 UNATTENDED RUN — no prompts after this point

The Test Engineer answered the `/test-mode` §1 setup questions at 2026-10-19 ~16:55 and then
chose **"Unattended overnight"**. From the first dispatch onward:

- **AskUserQuestion is not used**, including a §5 USER-CONFLICT and the §5 "proceed with the N?"
  question.
- Every question that would have been asked is **recorded as a notice** in `## Issues`, carried
  in the final report, and the campaign **proceeds with the runnable cases**.
- **This does NOT loosen STANDING-ORDERS §4.** Root on the box, `bench_probe.py apply`, a
  recable or destack, a licence, resolving a USER-CONFLICT, and displacing a console holder
  remain the Test Engineer's and are **never** done unattended.
- This is a **user-driven** campaign, not `Driver: ask-ck`. `/create-logs` still waits for the
  Test Engineer; nothing is auto-logged.
- §1.3 was asked and answered: **"Here is fine"** — the run stays in this session's process, not
  tmux. If the process dies the tester dies with it; this file and the per-case commits survive,
  and the loss is the case in flight.

## Session facts

Recorded 2026-10-19 16:55 NZDT from the Test Engineer's own answers to `/test-mode` §1.

Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: u2 = swi_d (DUT), u3 = swi_b, u5 = swi_a
PDU: 10.36.230.212 outlets u2=1, u3=7; 10.36.230.35 outlet u5=3
Constraints: None beyond standing orders (full authority within tests; power cycles allowed).
             Unattended overnight — see above.

Answer given as **"Same as 2026-10-16"**, i.e. carried verbatim from
`CAMPAIGN-QUEUE-2026-10-16T1406.md`, and **confirmed by the Test Engineer** for this campaign.

Devices, as last measured by `bench_probe.py` (`bench-setup/tb277/bench-state.md`) — the tester
re-probes at TRIAGE and that probe, not this block, is authoritative:

- **DUT — swi_d, /dev/u2 @115200, AT-x960-56YSQ, S/N `A2WQS700B`**, standalone Active Master,
  software `sin_x96056-20261012-24`, boots FLASH (`flash:/x960-tb277.rel`), boot config
  `flash:/default.cfg`.
- **partner — swi_b, /dev/u3 @9600, AT-x960-28YSQ**, S/N A10737A261700021,
  `sin_x96056-20260921-9`. **Base licence** including `RADIUS-100`.
- **partner — swi_a, /dev/u5, AT-x950 GEN2-52XSTQm.**

## Occupancy — checked before anything, 2026-10-19 16:53 NZDT

`tools/tb precheck tb277 u2,u3,u5` → **exit 5 FOUND**, reported verbatim to the Test Engineer:

```
  - process 744 (root, up 38-05:41:17): /usr/sbin/ser2net -c /etc/ser2net.conf -P /run/ser2net.pid
  - process 10790 (root for bidhanc, up 3-06:05:17): minicom -D /dev/ttyUSB1
```

All three session consoles read **free**. Neither item is on them: `ser2net` is the box's console
daemon, and the minicom is the Test Engineer's own on **ttyUSB1 = u1**, which is not in this
session's list. The Test Engineer answered **"Proceed"**. **u1 is never touched.**

## Rules

Verdicts (PASS / FAIL / PARTIAL / UNSUPPORTED / NOT TESTED), the tester's working logs, the
`RESULT` line, the results list and the final per-case log template are all in
**[logged-output.md](../../logged-output.md)**. Standing answers are in
**[STANDING-ORDERS.md](../../STANDING-ORDERS.md)**. Platform facts are in
**[platforms/x960.md](../../platforms/x960.md)**.

Three that bear repeating for this campaign:

- **STANDING-ORDERS §7 — traffic tests use scapy, not ping.** Craft the exact frame, send a known
  count, count what arrives, and send a **control** flow that must NOT match. A verdict rests on
  the pair.
- **STANDING-ORDERS §8 — health-check the DUT in every case** (new, 2026-10-19). `show reboot
  history`, `show exception log`, a filtered `show log` + `show log tail 150`, `show cpu` and
  `show memory`, **twice**: with the setup reads before step 1, and again after the last step.
  Both samples in the working log. **This campaign is the first to run under §8.**
- **logged-output.md §2 — capture the DUT's `show system` verbatim** with the setup reads, or
  `/create-logs` cannot put it in the final log.

## 🔴 Thirteen of fourteen cases have NO authored step text

Read from `ck.db` (`zephyr_cases`) at 2026-10-19 17:0x. Every one of the 14 is
`script_type STEP_BY_STEP`, `num_steps 1`, `has_objective 0`, and for **13 of them** the single
step is `[{"description": "", "testData": "", "expected": ""}]` — completely empty.

**Only T33427 has authored text**, and it is the one case not being run (below).

⇒ Each case must be **designed** from the title, the TFS/TPS and the DUT's own CLI surface,
enumerated by read-only help probe before the steps are drafted — the pattern used for the
2026-10-15 DHCP campaign and half of 2026-10-16. **Every log must say that no authored step text
exists**, rather than implying the steps were authored.

## Bench capability, established read-only before dispatch (2026-10-19 17:0x)

| need | state on tb277 |
| --- | --- |
| RADIUS server | **`freeradius 3.0.16+dfsg-1ubuntu3.2` installed AND LISTENING** on UDP 1812/1813 (and 127.0.0.1:18120) |
| TACACS+ server | **`tacacs+ 4.0.4.27a-3` installed** (`/usr/sbin/tac_plus`), **not running** — the tester starts it |
| SNMP trap receiver | `snmptrapd` present (`/usr/sbin/snmptrapd`) |
| SNMP poller | `snmpwalk`, `snmptrap`, `python-netsnmp` present |
| telnet client | `/usr/bin/telnet` present |
| sFlow collector | 🟠 **`sflowtool` is ABSENT** — grade T44309 on the DUT emitting sFlow datagrams, captured and decoded by hand; say so in the log |
| scapy | 2.4.4 |
| 🔴 `/tmp` free space | **105 MB of 2.0 G — 95% full**, because of 1.8 GB of `wireshark_eth4*.pcapng` that **belong to someone else and are NOT ours to delete**. Captures must be short and copied out promptly (`tcpdump-nfs-root-squash-capture`) |

## Queue

| # | case(s) | group dir | state | note |
| --- | --- | --- | --- | --- |
| A | T33407 Local RADIUS Server; T33408 RADIUS Client mode; T33409 RADIUS Proxy | `aaa-2026-10-20T0825` | **DONE — 3 of 3 PASS** | RADIUS only. The tester runs a **second, user-owned freeradius** on unprivileged ports (e.g. 11812/11813) and points the DUT at them with `radius-server host <ip> auth-port/acct-port` — the running system instance needs root to reconfigure. All shared secrets are `testing123` |
| D | T33411 TACACS+ Authentication; T33410 TACACS+ Accounting; T33412 TACACS+ Logging | `tacacs-2026-10-20T0825` | **DONE -- 3 of 3 PASS** | **UNBLOCKED 2026-10-20 13:31 by the Test Engineer**, who started `tac_plus` on tb277 himself (STANDING-ORDERS §4 respected — the sentinel did not use its own passwordless sudo). Order puts **authentication first**: accounting has nothing to record until a login works |
| B | **T44308 RMON; T33413 Trap Temperature**; T44301 Per-port link trap; T44309 sFlow Agent | `snmpmon-2026-10-20T0825` | **DONE — 3 PASS, 1 PARTIAL** | **Reordered at the tester's recommendation: RMON runs FIRST**, because T33413's only measurable trap limb is an RMON alarm bound to a temperature OID, so the alarm instrument is already proven when T33413 needs it. T33413's genuine over-temperature limb is **NOT MEASURABLE** — see `## Issues`. T44301 must flap **port1.0.2 or port1.0.16**, never port1.0.10/port1.0.48, which carry the path to the trap receiver |
| C | **T33378 Telnet Server (IPv4); T47199 default-password warning; T33416 Triggers - Interface** | `mgmt-2026-10-20T0825` | **DONE — 2 PASS, 1 FAIL** | **Reordered at the tester's recommendation: Telnet FIRST**, because the console login shows no default-password warning (measured), so T47199 must look on telnet/SSH/HTTP — and T33378 is the case that turns telnet on. First action for T33416: `trigger 1` → `type ?`, the campaign's one unverified CLI surface |
| — | T33427 Flexera Licensing | — | **NOT TESTED** | Test Engineer's decision, 2026-10-19: *"Drop it — NOT TESTED"*. Its step 1 is *"Request Chris Robb to generate a Flexera License for a particular feature"*; installing a licence is the Test Engineer's (STANDING-ORDERS §4) and no licence file was available this session |

Setup and restore recipes are written into this file by the tester before each group's first
case, so a fresh tester can restore the bench from here.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33407 | (274) Management_RADIUS - Local RADIUS Server | aaa-2026-10-20T0825 | PASS | served real RADIUS on the wire (5 requests, 2 Accept / 3 Reject, every reply's authenticator verifying against the configured secret); rejected wrong password, unknown user and wrong secret; ignored a non-NAS host; removed cleanly (rcdiff byte-identical) | T33407/work/run1.log | tester |
| T33408 | (275) Management_RADIUS - Radius Client mode | aaa-2026-10-20T0825 | PASS | a user existing only on the RADIUS server logged in to the DUT, proven on the wire (24 packets: 7 Access-Request, 3 Accept, 1 Reject, 7 Accounting-Request, 6 Accounting-Response, 10/10 reply authenticators valid), paired Accounting Start/Stop, controls on wrong password / mismatched key / unreachable server, clean removal (rcdiff byte-identical) | T33408/work/run1.log | tester |
| T33409 | (276) Management_RADIUS - Radius Proxy | aaa-2026-10-20T0825 | PASS | the proxy re-originated each request (new id, Proxy-State carrying the original, added Message-Authenticator, realm stripped); the two legs are cryptographically independent — the same pcap gives authenticator valid=5/invalid=0 on the NAS leg under testing123 and valid=0/invalid=5 on the upstream leg under the same secret | T33409/work/run1.log | tester |
| T44308 | (296) Management - RMON | snmpmon-2026-10-20T0825 | PASS | statistics, history, event and alarm all measured against counted traffic (history bucket 2 = exactly 1000 packets / 86000 octets); four real SNMPv2c traps caught and decoded on udp/162; a control alarm stayed silent then fired with alarmValue exactly 50; removal proven on the CLI, in the MIB and on the wire | T44308/work/run1.log | tester |
| T33413 | (280) Management_Trap - Temperature | snmpmon-2026-10-20T0825 | PARTIAL | the over-temperature trap could not be produced on this bench (no settable threshold; coolest sensor 27 °C against a 61 °C hardware limit) AND the RMON-alarm substitute is refused by the product; everything else measurable passed — `hw-monitoring` arms, chains and removes per-group, the AT-ENVMONv2 table matches the CLI on all 14 sensors, and no fault trap fired in a 100 s window in which two known-good RMON traps proved the transport live. **Grade is the Test Engineer's to confirm — see Issues** | T33413/work/run1.log | tester |
| T44301 | (281) Management_Trap - Per-port link trap | snmpmon-2026-10-20T0825 | PASS | linkDown/linkUp emitted for the port carrying `snmp trap link-status` and for no other, proven on the wire by measured ifIndex (5002, read from ifDescr not assumed); a sibling port flapped in the same 220 s window was logged by the DUT but produced no trap; empty captures both before arming and after removal under identical stimulus | T44301/work/run1.log | tester |
| T44309 | (297) Management_SFlow - SFlow Agent | snmpmon-2026-10-20T0825 | PASS | v5 datagrams sent to the configured collector from the configured agent address; 2000 frames at 1-in-50 gave **exactly 40** flow samples, each reporting the configured rate and decoding to the exact frame sent; a tenfold rate change dropped the yield tenfold; counter samples only for the one polled port of 77; nothing before configuration, nothing after removal. **Two intermittent defects — see Issues; FAIL is defensible and is the Test Engineer's call** | T44309/work/run1.log | tester |
| T33378 | (229) Management - Telnet Server (IPv4) | mgmt-2026-10-20T0825 | PASS | proven on the wire across off / on / IPv6-only / removed: 4 pkts SYN→RST while disabled; 94 pkts with a real manager session carrying 2045 B of banner and output, the DUT logging telnetd from 10.38.22.33; a bad credential refused at the application on an ESTABLISHED connection; IPv4 refused while `show telnet` still read Enabled/IPv6; 2 pkts after removal; rcdiff byte-identical | T33378/work/run1.log | tester |
| T47199 | (273) Management_Operation - Show warning message when user continues to use default PW | mgmt-2026-10-20T0825 | **FAIL** | `% Default password needs to be changed.` absent from EVERY access path — 2 console logins on swi_d, telnet, SSH, and 2 console logins on swi_b (different model, 3-week-older build, also still on `friend`) — and absent from the log, while TPS row 271 says Yes at Priority 1 and the DUT still authenticates with the factory password. A `banner exec` marker proved the instruments can see a message in exactly that position | T47199/work/run1.log | tester |
| T33416 | (283) Management_Triggers - Interface | mgmt-2026-10-20T0825 | PASS | `type interface` exists; proven on three independent instruments — activation counters, the SNMPv2c trap on the wire (AT trigger OID `1.3.6.1.4.1.207.8.4.4.4.53.0.1`, trigger ID in varbind `…53.1.0`), and the DUT's own `TRIGGER[…] activated` log line — with three silent controls under identical stimulus (sibling port, `no active`, `no trigger`), 0 traps in 270 s from the instrument that had just recorded three | T33416/work/run1.log | tester |
| T33411 | (278) Management_TACACS+ - Authentication | tacacs-2026-10-20T0825 | PASS | a user existing ONLY on the TACACS+ server (`taclow`, no local entry) logged in over SSH, and `tacuser` -- deliberately given different local and server passwords -- was admitted with the server's and refused with the local one, so the server decided; 58 packets of TCP/49 against zero in both the OFF and the removed baselines under identical stimulus; every failure mode has its own measured signature (a Reject is one flow not two, a wrong key inverts the byte ratio and never puts the password on the wire, an unreachable server never gets past ARP); rcdiff byte-identical | T33411/work/run1.log | tester |
| T33410 | (277) Management_TACACS+ - Accounting | tacacs-2026-10-20T0825 | PASS | 23 TFS specs measured, **19 PASS**: paired START/STOP with matching sequential task_ids and an accurate `elapsed_time`, all three modes verified against measured zeros on two instruments, command accounting correct on privilege selection, abbreviation expansion, the `do` exception, `task_id` uniqueness and the trigger mutual exclusion both ways; removal leaves zero records and zero packets where 44 records were produced. **Three defects -- two need a developer, see Issues** | T33410/work/run1.log | tester |
| T33412 | (279) Management_TACACS+ - Logging | tacacs-2026-10-20T0825 | PASS | five of the seven TFS logging specs driven on hardware: login success, login failure (with the TACACS+ status code AND the session-level refusal), accounting-notification failure (distinguishing a lost START from a lost STOP, with the server index and the exhaustion line), no `debug tacacs+` and the `debug aaa` surface -- all satisfied. **Two gaps: S1599.1.080 and .081 produce no log message at all** (see Issues). S1599.1.084/.085 NOT MEASURED -- a rejected `enable` is unrecoverable without a reload | T33412/work/run1.log | tester |
| T33427 | (300) Management - Flexera Licensing | — | NOT TESTED | needs a Flexera licence from Chris Robb; installing a licence is the Test Engineer's (STANDING-ORDERS §4). Dropped by the Test Engineer 2026-10-19 | — | Test Engineer |

## Issues

### 🔴 CORRECTION 2026-10-20 15:40 — T33413 IS measurable. The Test Engineer supplied the method.

**The tester and the sentinel both concluded "the over-temperature trap is NOT MEASURABLE on
this bench". That conclusion was wrong**, and it was wrong for an instructive reason: both of us
reasoned from the **CLI surface only**. `temperature ?` and `environment ?` are
`% Unrecognized command`, and `snmp-server enable trap ?` has no `temperature` group — all true,
and all irrelevant, because **the threshold is settable underneath the CLI.**

**The Test Engineer's method**, demonstrated on an AT-x250-28XTm:

```
AT-x250-28XTm# start-shell
[root@AT-x250-28XTm flash]# echo 20000 > /sys/class/hwmon/hwmon0/temp1_max
[root@AT-x250-28XTm hwmon0]# exit
AT-x250-28XTm# 20:45:47 AT-x250-28XTm Platform: SENSOR Board Base - Temp: Remote 1:
              Alarm asserted. Reading:37 Threshold:20 (Degrees C)
```

Lower `temp*_max` below the live reading and the platform asserts the alarm, which is what
drives the `hw-monitoring` trap. **The sensor reading is real; only the threshold is moved.**

**Authority — this was never blocked.** `start-shell` is root **on the DUT**, not on the
testbox. STANDING-ORDERS **§4 reserves root on tb277**; **§1 explicitly puts the devices under
test in play** (*"You may reconfigure and deconfigure devices as required to perform a test"*).
No permission was needed and none should have been waited for. The gap was imagination, not
policy.

**The generalisable lesson, for `logged-output.md` and future triage:** *the CLI surface is not
the device's surface.* An AW+ switch is Linux underneath, and `start-shell` reaches sysfs,
`/proc` and the hwmon tree. Before declaring any limb NOT MEASURABLE on the grounds that "no CLI
command exists", check whether the underlying OS exposes it. This is the second time this
campaign that a stated impossibility turned out to be a missing idea rather than a missing
capability.

**T33413 is being re-run as `run2`** with this method. Its PARTIAL verdict and the
PARTIAL-vs-UNSUPPORTED grading question are both superseded by whatever run 2 measures.

### 🔎 CROSS-CASE (sentinel) — the DUT handles management secrets THREE different ways

Visible only across groups A, B and D; no single case could see it. Measured, same device, same
session:

| secret | stored in running-config as | in the device log |
| --- | --- | --- |
| **TACACS+** key (T33411/T33410) | **AES, type 9** — `key 9 kh3afe…=` | **masked**: `key ********` |
| **RADIUS** key (T33408) | **encrypted** — `key h+EeD…= encrypted` | not observed |
| **SNMP** community (T44308/T33413/T44301/T33416) | 🔴 **PLAINTEXT** — `snmp-server community testing123` | not observed |

**SNMP is the outlier.** TACACS+ gets the strongest treatment — encrypted at rest *and* redacted
in the audit trail, so an operator reading the log sees that a key was set without learning it.
RADIUS is encrypted at rest. The SNMP community is neither.

**Two consequences.** For this campaign, the throwaway-secret instruction was doing real work on
the SNMP cases and was merely belt-and-braces on the AAA ones — so a future campaign that
reuses a real community string leaks it into an uploadable `.cfg`. And as a product observation,
a consistent story across management protocols would be better than three; the SNMP community
is the one a reviewer would question.

Not a defect against any single spec, which is exactly why it needs recording here rather than
in a case log.

### 🔴🔥 NEEDS TEST ENGINEER — T33410 FINDING 2: command accounting records the CONSOLE only. **SSH commands are not audited at all.**

**The most consequential finding of the campaign so far, and it is a security one.**

A VTY (SSH) session ran six commands, including privilege-15 `configure terminal` and
`ip domain-lookup`, and produced **zero accounting records and zero packets on TCP/49** —
**measured twice**. In the *same file* and the *same configuration*: login accounting for those
same VTY sessions works perfectly, and command accounting **from the console** works perfectly.
So the feature is on, reachable and working — just not for VTY.

The tester probed `line vty` read-only: **there is no per-line command-accounting option**, so
nothing was left unbound. This is not a misconfiguration.

**Authority:** TFS **S1599.1.031** says command accounting is *"globally configured"*;
**S1599.1.065** explicitly dimensions *"33 concurrent command accounting sessions for vty
connections"* — the spec contemplates VTY command accounting in so many words. **TPS row 275 =
Supported: Yes, Priority 1.**

**Why it matters beyond a failed spec:** an administrator working **over SSH — the normal case**
— leaves **no command audit trail**, while the TACACS+ configuration gives every appearance of
recording one. A silently absent audit trail is worse than an obviously absent one: nobody goes
looking for records they believe they already have.

### 🔴 NEEDS TEST ENGINEER — T33410 FINDING 3: a VTY session's interim updates cannot be attributed to it

The periodic accounting update for a VTY session carries **`task_id` 45** where that session's
own START and STOP are **44**; `port` reads `pts/0` where its START/STOP read `ssh`; and
`rem_addr` is lost entirely.

Worse: **the next VTY session (START/STOP 46) emits updates carrying the same 45** — so two
consecutive administrators' interim records are **indistinguishable from each other**.

The console session, in the same file and the same minute, is **correct** (`task_id=4` matching
its START), which rules out a server-side or clock explanation. S1599.1.053's escape clause does
not apply: both sessions logged in after the configuration and had already sent their own START.
Against **S1599.1.052**.

### 🟠 T33410 FINDING 1 (low) — `end` leaves config mode unaccounted; `exit` is recorded

Confirmed in two separate runs, with consecutive `task_id`s either side, so nothing was lost in
transit. The audit trail shows an operator **entering** configuration mode and what they typed,
but not that they **left** it. `end` and `exit` are synonyms here; only one is accounted.

### 🔁 CORRECTION to `platforms/x960.md` §7E.4 — TACACS+ and RADIUS differ, and TACACS+ is right

A session that **predates** the accounting configuration correctly produces **no STOP record**
under TACACS+ (S1599.1.026). §7E.4 records the **opposite** behaviour for RADIUS on this same
DUT. **TACACS+ is the one that matches its own specification.** Fold the contrast into the
platform file at wrap — a reader of §7E.4 alone would generalise the wrong way.

### NOTICE (campaign) — S1599.1.105 deliberately NOT MEASURED, and the sentinel agrees

The spec covers CLI blocking when command accounting is on and the server disappears. Running it
would mean: command accounting on **from the console**, server removed — at which point **every
console command blocks, including the one that undoes it**, and the console is this bench's only
administrative path. **It needs its own case on a bench with a second administrative path.**

### 🟠 CORRECTION to `platforms/x960.md` §7E.2 — `Last login:` is keyed on a RECYCLED UID

Found by the group D tester, and it **qualifies a finding the sentinel reported with more
confidence than it had earned.**

§7E.2 says the `Last login:` banner line discriminates who authenticated a login — present for a
local account, absent for a server-authenticated one. **That is unsafe in exactly the pattern
our campaigns use.**

A freshly created `tacuser` reported `Last login: Mon Oct 19 23:00:48 UTC 2026 from 10.38.22.33`
**before it had ever logged in.** That record belongs to group C's **deleted `ckalt`** account
(T47199's telnet login, box time 12:01) — the UID was recycled and the lastlog entry came with
it.

⇒ **Any session that creates and deletes temporary accounts — which is what these campaigns do
every day — can see a `Last login:` line that belongs to a different, earlier user.** The
discriminator is still real for a stable account, but it must carry this caveat or it will be
read as evidence when it is an artefact. Fold into §7E.2 at wrap.

### 🔬 Three TACACS+ wire properties worth keeping (T33411)

1. **An accept and a reject are distinguishable WITHOUT the shared key.** An accepted login is
   **two** TCP/49 conversations — authentication, then an authorization exchange; a reject is
   the authentication flow alone. **The second flow's presence is the verdict**, which means a
   passive observer can grade TACACS+ outcomes without decrypting anything.
2. **A wrong key is distinguishable from a dead server on TACACS+** — where `platforms/x960.md`
   §7E.4 records it is **not** on RADIUS. `tac_authen_read_timeout: inconsistent reply body,
   incorrect key?` versus `tac_connect_single_vrf: connection failed … Transport endpoint is not
   connected`, plus an inverted wire ratio (41 B out / 72 B in), and the password never reaches
   the wire at all.
3. **The obfuscated body is not padded.** Five measurements fit `base + len(username) +
   len(password)` exactly, so **a passive capture leaks both lengths** even though no credential
   is readable. A protocol property, not a product defect — but measured here rather than
   asserted from the RFC.

### 🛠 NOTICE (tooling) — `tools/netlogin.py` could not report a failed SSH control

A refused **ssh** login re-prompts `<user>@<host>'s password:`, and the tool graded that
`UNKNOWN` — so a control that had genuinely failed could not say so, which would silently weaken
every negative leg that used it. Fixed to FAIL and regression-tested both ways in the same case.

### ✅ UNBLOCKED 2026-10-20 13:31 — the Test Engineer started a TACACS+ server

T33411 / T33410 / T33412 were BLOCKED because `tacacs-server host <ip>` takes **no port
argument**, so TACACS+ is locked to **TCP/49**, and binding a privileged port is root on the box.

**The Test Engineer ran the commands himself**, step by step in the session. The sentinel did
**not** use its own working passwordless sudo: §4 is about authority, not capability.

**Server facts for the group D dispatch — measured, not assumed:**

| fact | value |
| --- | --- |
| server address (as the DUT must address it) | **10.38.22.33** (tb277 `eth3`) |
| port | **49**, confirmed `LISTEN 0.0.0.0:49` and `[::]:49` |
| service | `tacacs_plus.service`, `systemctl is-active` = **active** |
| shared key | **`testing123`** |
| config | `/etc/tacacs+/tac_plus.conf`, parse-checked with `tac_plus -P` |
| user, priv 15 | **`tacuser`** / `testing123`, `service = exec { priv-lvl = 15 }` |
| user, priv 1 | **`taclow`** / `testing123`, `service = exec { priv-lvl = 1 }` |
| accounting file | **`/var/log/tac_plus.acct`**, pre-created `-rw-r--r--` so the tester can read it |

Two privilege levels on purpose: T33411 should prove the server's **authorisation** lands, not
merely that a login succeeds. The accounting file was pre-created 0644 because a root daemon
creating it later might have made it unreadable — which would have blocked T33410 and T33412 on
their own evidence mid-case.

🔴 **The server must be stopped when group D finishes** (`sudo systemctl stop tacacs_plus`) — it
is a service on a shared box and leaving it running is someone else's surprise later. That is
the Test Engineer's command, and the sentinel will remind him.

### 🔴🔥 NEEDS TEST ENGINEER — group D findings: two developer-grade accounting defects, two logging gaps

Found by the group D tester, 2026-10-20 14:1x–14:5x NZDT. Every one is measured on at least
two independent instruments, with the control in the same file.

**T33410 — FINDING 2 (developer): TACACS+ command accounting records CONSOLE commands only.**
A VTY (SSH) session running six commands, including privilege-15 `configure terminal` and
`ip domain-lookup`, produced **zero accounting records and zero packets on TCP/49** — measured
twice. In the same configuration and the same file, **login** accounting for those same VTY
sessions works, and **command** accounting from the console works. `line vty` was probed
read-only and offers `accounting login` only — there is no per-line command-accounting binding
to be missing. Against TFS **S1599.1.031** ("Command accounting will be globally configured")
and **S1599.1.065**, which dimensions VTY command accounting at 33 concurrent sessions.
TPS row 275 = Supported: Yes, Priority 1. ⇒ **An administrator working over SSH leaves no
command audit trail, while the TACACS+ configuration gives every appearance of recording one.**

**T33410 — FINDING 3 (developer): a VTY session's periodic update cannot be attributed to its
session.** Its `task_id` is 45 where the session's own START/STOP are 44; `port` reads `pts/0`
where the session's records read `ssh`; `rem_addr` is lost. The **next** VTY session
(START/STOP 46) then emits updates carrying **the same 45**, so successive administrators'
interim records are indistinguishable from each other. The console session, in the same file
and the same minute, is correct (`task_id=4` matching its START). S1599.1.053's escape clause
does not apply — both sessions logged in after the configuration and had already sent a START.
Against **S1599.1.052**.

**T33410 — FINDING 1 (low): `end` leaves configuration mode with no accounting record, while
`exit` — the synonym — is recorded.** Confirmed in two runs with consecutive task_ids either
side, so nothing was lost in transit. Not in the TFS's "will not be implemented" list.

**T33412 — FINDING 1 (🟠): S1599.1.080 is not implemented.** Two successful round trips to the
server, proven by the server's own accounting file, produced **no log message** about
communication being established — and neither did a server recovering from `Dead` to `Alive`.

**T33412 — FINDING 2 (🟠): S1599.1.081 is satisfied only by a `show` command.** The DUT detects
loss of communication well enough to move a server from `Alive` to `Dead` — a four-state column
(`Unknown`, `Alive`, `Error`, `Dead`) that even separates "never reached" from "was reachable"
— but emits no log line saying so. The loss case is logged **less** than the never-established
case, because the TCP-timeout path produces no `tac_connect_single_vrf` line.
**Why these two matter more than they look:** TFS **S1599.2.25** deliberately omits a
`debug tacacs+` command on the grounds that *"log messages are considered sufficient"* — the
tester confirmed its absence against a 47-entry `debug ?` list in which `radius`, `ldap` and
`dot1x` all have one. So for these two events there is no diagnostic at all except a `show`
nobody is watching.

### 🔴 NEEDS TEST ENGINEER (recorded, raised at the start of group D) — enable authentication via TACACS+ is NOT MEASURED

`aaa authentication enable default group tacacs+ ...` was deliberately never configured. Per
x960 §7E.1 — re-confirmed for TACACS+ in T33411 — a Reject is honoured and the fallback is not
consulted, and the server has no enable credential for these users. **A rejected `enable`
leaves the operator at `awplus>` with no route to configuration mode on any access path**
(console and every VTY share one enable method list), and AW+ offers no recovery except a
reload — which this session forbids, because the L3 underlay carrying the path to the server
exists in running-config only. This blocks TFS S1599.1.011–016 for T33411 and S1599.1.084/.085
for T33412, so **T33412 covers 5 of the 7 logging specifications**. The safe half was measured:
the method list falling back to `local` when every server is unreachable (T33411 STEP 12).
Running the full limb needs either the Test Engineer's acceptance of the risk or an enable
credential added to `tac_plus`.

### 🛠 ANSWERED — AW+ does NOT support a chained `| exclude` on this build

The §8 process notice above proposed
`show log | include kernel|exception|crash|restart|Unexpected | exclude IMISH` and asked that
chained-filter support be verified first. **It is not supported, and it fails silently.** No
`%` error is printed; AW+ takes the whole string after `include` as one alternation pattern, so
` exclude IMISH` simply becomes another alternative and the IMISH lines remain. The output
looks filtered and is not — the worst of the three possible outcomes. ⇒ the fix to
STANDING-ORDERS §8 / logged-output.md §2 should say **filter the echoes out on the box side
after the read** (`grep -v IMISH` over the saved output), which is what all three group D cases
did.

### ⚠️ `platforms/x960.md` §7E.2 — the `Last login:` discriminator now needs THREE caveats

It is not safe as written. Measured in group D:

1. **Absent** for a login with no local account — the original rule, confirmed for TACACS+ by
   `taclow` in T33411 STEP 13.
2. **Carries a DELETED user's timestamp when the UID is recycled.** A freshly created
   `username tacuser` reported `Last login: Mon Oct 19 23:00:48 UTC 2026 from 10.38.22.33`
   before it had ever logged in; that record belongs to group C's `ckalt`, whose telnet login
   from the box T47199 recorded at exactly that time. AW+ lastlog is keyed on the underlying
   UID.
3. **Duplicated when the login waited on an unreachable AAA server.** With the accounting
   server black-holed, one console login printed two `Last login:` lines ~7 s apart (4 logins
   in the window, 6 lines; every login outside it printed one). Correlation clear, mechanism
   not isolated.

Caveats 2 and 3 arise from exactly what campaigns do — create and delete temporary accounts,
and break a server on purpose — so anyone using the discriminator will meet them.

### NOTICE (product, for platforms/x960.md) — TACACS+ differs from RADIUS in three measured ways

All on the same DUT, same session, against §7E.4's RADIUS findings:

1. **A wrong shared key is distinguishable from a dead server.** RADIUS says `failed to
   respond` for both; TACACS+ prints `tac_authen_read_timeout: inconsistent reply body,
   incorrect key?` versus `tac_connect_single_vrf: connection failed ... Transport endpoint is
   not connected`. A consequence of TCP: a connect failure and a decode failure are at
   different layers.
2. **A session that predates the accounting configuration produces NO stop record**
   (S1599.1.026). RADIUS on this DUT still produces one. TACACS+ is the one matching its spec.
3. **The fallback delay is 3.6–3.9 s, not RADIUS's 25.5 s** — TACACS+ fails at ARP/TCP connect
   rather than waiting out a UDP retransmit schedule, so a console-login tool's settle timeout
   need not be as generous.

Plus, from the wire: **an ACCEPTED login is two TCP/49 conversations** (authentication, then
authorization) **and a REJECTED one is a single authentication flow** — a complete accept/reject
discriminator from a passive capture without the shared key. And the obfuscated body is **not
padded**: five measurements fit `base + len(username) + len(password)` exactly, so a capture
leaks both lengths.

### 🛠 NOTICE (tooling) — two repo tools changed in group D

* **`tools/filewin.py` (new, with its README entry)** — reads the window a growing file gained
  since a recorded byte offset. Written because grading against the Test Engineer's
  `/var/log/tac_plus.acct` needs **"zero new records" to be a measurement**, and a `tail -n` is
  not a window. Used on every leg of all three cases.
* **`tools/netlogin.py` fixed** — a refused **ssh** login re-prompts `<user>@<host>'s
  password:` and the tool graded that `UNKNOWN`, so a control that had genuinely failed could
  not report failure. Now FAIL, regression-tested both ways inside T33411.

### NOTICE (scope) — enumerated but NOT graded, across the campaign

Stated so `/create-logs` does not imply coverage these cases do not have:

- **IPv6 telnet** — the surface was walked (`service telnet ipv6`, `Protocol: IPv4,IPv6`,
  `Protocol: IPv6`) but the case is scoped IPv4 and no IPv6 session was driven or captured.
- **`type interface … any`** — the third interface-trigger direction, alongside the `down` and
  `up` that were measured.
- **A trigger's `day` / `time` / `test` options** — present in the sub-mode, not exercised.
- **A trigger script's CONTENT** — needs a root write to `/tftproot` (§4). The trigger was proven
  to *reach* the script (`Unable to activate script … (File not found)`), so the open limb is now
  "what does a script do when it runs", not "does the action list run".
- **HTTP login** — NOT MEASURABLE on this DUT: `show http` reads `GUI file in use : -`, no Web
  GUI is installed, and installing one is a bench change.

### ✅ TRIAGE POLICY — a future TRIAGE *can* read the trigger `type` surface

Measured in T33416: **entering `trigger N` and leaving without setting a `type` persists nothing**
— no `show trigger` row, no running-config line. So reading `type ?` is effectively read-only
and a future triage need not defer it. **This retires the "first action of the group's tester"
caveat** this campaign had to carry.

Contrast, from group A: entering **`group <name>`** in the RADIUS proxy sub-mode **DOES create
it**. The two sub-modes differ, so neither behaviour can be assumed from the other.

### 🛠 NOTICE (tooling) — `show trigger` with no triggers prints a `%` line from a SUCCESSFUL show

`% No triggers currently defined` stops `cfg.py`. The tester deliberately did **not** add it to
`console.ADVISORY`, which is for configuration commands, and ran shows through `ckcon.py`
instead. That is the right call and worth keeping: ADVISORY is not a dumping ground for every
benign `%`.

Related grep trap: **`show running-config | include trigger` prints only `trigger 1` / `trigger 2`**
— the sub-mode lines (`type`, `description`, `trap`, `repeat`) do not contain the word. That grep
tells you a trigger exists and **nothing about what it does**.

### NOTICE (campaign) — the trigger ACTION list is executed, but script CONTENT is NOT MEASURED

Pointing `script 1` at a deliberately absent file made the DUT log
`TRIGGER[1411]: Trigger 1 (ck down on port1.0.2) activated` immediately followed by
`Unable to activate script /flash/cktrig.scp (File not found)` — which proves the action list is
**executed, not merely counted**. What a script *does* when it runs still needs a root write to
the box's `/tftproot`: the same §4 limb T44181 left open, and item 5 on the 2026-10-19 handover's
OPEN list. **This case narrows that open item** from "does the trigger run its action?" to "what
does a script do when it runs?".

### 🔎 CROSS-CASE (sentinel) — triggers CAN threshold CPU, memory and temperature; RMON alarms cannot

Noticed by the sentinel at 12:13 while T33416 read `type ?`. **This qualifies group B's
T33413 finding and should travel with it**, because a developer reading that finding alone would
draw too strong a conclusion.

The full AW+ trigger type list on this build:

```
atmf  cpu  env-sensor  interface  linkmon-probe  log  main-pse  memory
periodic  ping-poll  pse-port  reboot  stack  time  usb
```

**`type cpu` ("Monitor CPU usage levels"), `type memory` ("Monitor memory usage levels") and
`type env-sensor` ("Monitor environment sensor") all exist.**

So the correct statement of the T33413/RMON finding is narrower than "no threshold on
temperature, CPU or memory can be expressed on this build". It is:

> **RMON's `alarmVariable` is restricted to the RMON tables, against RFC 2819** — so those
> thresholds cannot be expressed *through RMON*, and an SNMP manager expecting standard RMON
> behaviour will not find them. **AW+ provides the capability by a different, proprietary
> mechanism (triggers), which is not interoperable with an RMON-based manager.**

That is still a real finding — an RMON implementation that silently narrows a standard MIB is a
problem for anyone using a standards-based NMS — but it is an **interoperability** finding, not
a missing-capability one. `/create-logs` and `platforms/x960.md` should carry it in that form.

Also settled by the same read: **`type interface` EXISTS** ("Monitor the link status of an
interface"), so **T33416 is a genuine test, not UNSUPPORTED.** That was the campaign's one
unverified CLI surface.

### 🔴🔥 FAIL — T47199: the default-password warning is absent on every access path. **A developer finding.**

The campaign's first FAIL, and the best-evidenced thing in it.

**Measured absence.** `% Default password needs to be changed.` appears on **none** of: two
console logins on swi_d, a telnet login, an SSH login, two console logins on **swi_b** (an
x960-28YSQ on a three-week-older build, also still on `friend`, with no `security-password`
configuration at all). **Two models, two builds, one result.** No log line either, which
ER361.1.02 specifies when the feature is active.

**The absence is a measurement, not a blind spot.** `banner exec CKPROBE-EXEC-BANNER-MARKER`
appeared on console, telnet **and** SSH, in exactly the position the TFS example puts the
warning — the last thing before the first prompt. The instruments can see a message there.
There was none to see.

**Independent corroboration from a different subsystem.** The FDPC engineering page says a
device in the factory-default-password state is held in HTTP login-only mode, its APIs
answering 403 `API access requires admin password to be configured`.
**`GET /restconf/data` with `manager`/`friend` returned 200 OK and 11848 bytes of yang-data.**
The HTTP server agrees with the CLI that this device is not in the factory-default state —
although it literally is.

**Likely cause, from the product's own page, verbatim:** *"Currently, we only check that the
password has been encrypted with an MD5 hash, as the default-generated config contains this but
a user-generated config will not."* **Both units store the manager password as `$5$`
(SHA-256-crypt), not `$1$` (MD5).** Supporting detail: both units' manager hashes carry
**8-character salts** while a password set through the CLI got a **16-character salt** — different
generators, so the manager hashes were not produced by an ordinary CLI command.

**The authority for expecting it, precisely.** **X960 TPS row 271 = Yes**, and **TFS 2616.1**:
the warning is required *"at every login using the default account 'manager'"*, with
`Configuration Commands: None`, applicability *all platforms in 5.5.1-2*, and
**`Excluded Targets: None`**. There is no documented gate and no documented exclusion — which is
what makes the silence a defect rather than a configuration choice.

**Verdict confirmation needed.** The tester graded **FAIL**: the feature is declared supported
(TPS row 271 = Yes, Priority 1) and the behaviour is absent. If an unset `def_pwd_chg` boot
variable makes the silence correct, it becomes **UNSUPPORTED-by-configuration or PARTIAL**. The
evidence supports either reading. **Third grading call for the Test Engineer**, after T33413 and
T44309.

**The one open limb.** `def_pwd_chg` lives in the **U-Boot environment**; no CLI reports it and
reaching the bootloader needs a reboot, which this campaign forbids. *Against* it mattering:
TFS 2616 — the warn-only feature the TPS row and this case actually name — mentions no gate, and
its "will not be implemented" and "Excluded Targets" are both None. *For* it: 2616 may have been
built on FDPC's gated path.

**The experiment deliberately NOT run, and the sentinel agrees with the refusal.** Substituting a
`$1$` MD5-crypt of `friend` on the `manager` account would prove the theory on hardware. The
tester declined it unattended because it touches **the DUT's only admin account**;
`security-password history 1` may refuse the restoring command; and if the device then decides it
IS in the factory state, the behaviour is FORCE_CHANGE — an interactive dialogue `conlogin.py`
refuses by design. **swi_a is already lost to a lockout this campaign; a second lost unit would
be a bench incident.** The exact commands and the byte-exact restore string are in the working
log. **It needs an attended session.**

**Housekeeping:** HTTP *login* is NOT MEASURABLE on this DUT — `show http` reads
`GUI file in use : -`, no Web GUI is installed, and installing one is a bench change. The
manager password was **never changed**; the precondition was already true, and restoring
plaintext `friend` would have fought `security-password minimum-length 8`. The control came from
a second account (`ckalt`), now deleted. Adds `tools/httpq.py`.

### NOTICE (bench) — the Test Engineer's minicom on u1 is GONE as of 2026-10-20 ~11:44

`tools/tb precheck tb277 u2,u3` at the start of group C returned **exit 5 FOUND with exactly one
item**: `process 744 (root, up 39-00:20:06): /usr/sbin/ser2net` — the box's own console daemon.
**The `minicom -D /dev/ttyUSB1` that groups A and B ran alongside is no longer running.**

Both session consoles read free. The tester treated the Test Engineer's **"Proceed"** of
2026-10-19 16:53 as a standing answer rather than stalling an unattended queue on an
already-answered question, which the sentinel agrees with: the FOUND set is now strictly
*smaller* than the one that was approved. **u1 was not touched either way, by anyone, at any
point in this campaign.**

### 🔥 NOTICE (product fact, for platforms/x960.md) — how `service telnet` is stored, and a §5-shaped read-back

Measured in T33378, all four states walked:

| typed | stored in running-config | `show telnet` |
| --- | --- | --- |
| `service telnet ip` | `service telnet` **+** `no service telnet ipv6` | `Protocol: IPv4` |
| `service telnet ipv6` as well | `service telnet` alone | `Protocol: IPv4,IPv6` |
| `no service telnet ip` | `service telnet` **+** `no service telnet ip` | `Protocol: IPv6` |
| `no service telnet` | `no service telnet` | `Disabled`, `Protocol: None` |

**The command you type is not the command stored.** The IPv4-only state is defined by the
*presence of a negation*, not by the enabling command — so a config diff or a restore recipe has
to negate two lines, and a reader will never find the command that was issued.

And a **§5-shaped read-back**: `show telnet` can read **Enabled** while IPv4 TCP/23 is refused
(the IPv6-only state). Same shape as the mirroring trap in `platforms/x960.md` §5 — here it is
correct behaviour, but it is another instance of "a `show` command's headline does not settle
what the dataplane does".

### 🛠 NOTICE (tooling) — `service telnet ip` prints a `%` line AND SUCCEEDS

`% Warning: Telnet is insecure and deprecated. Please use SSH.` is emitted on success.
`tools/cfg.py` was abandoning the rest of the batch **at the very command that turns the feature
on**, because a `%` line reads as an error to a stop-on-error driver. Fixed by adding the text to
`tools/console.py`'s ADVISORY list, with the transcript console.py's own rule requires.

This is the inverse of memory `bench-scripts-stop-on-cli-errors`: there, a `%` line that looked
like success and was a failure; here, a `%` line that looks like a failure and is a success.
Both break a naive driver.

### 🛠 NOTICE (process) — the §8 `show log` filter MATCHES ITS OWN COMMAND, and the rule needs fixing

Found by the sentinel watching group C, 2026-10-20 11:39. **A defect in the rule written on
2026-10-19, not in any tester.**

STANDING-ORDERS §8 and logged-output.md §2 tell the tester to run:

```
show log | include kernel|exception|crash|restart|Unexpected
```

AW+ logs every command as `IMISH[pid]: [manager@ttyS0]<the command text>`. **That text contains
every keyword in the filter**, so each run of the health check matches every previous run of the
health check. By the eighth case of this campaign the output was mostly the tester's own
`show log | include …` and `show exception log` lines, with real device events a minority.

**Consequences:** the signal-to-noise ratio decays through a campaign; a genuine `restart` line
is easy to miss among the echoes; and each health read costs more context than the last.

**🔴 CORRECTED 2026-10-20 14:11 — the sentinel's proposed fix was WRONG, and wrong in a
dangerous way.** The group D tester tested it on hardware: **AW+ does not support a chained
`| exclude` on this build.** `show log | include <pat> | exclude IMISH` **prints no error** and
**silently swallows the second filter into the include pattern** — the output *looks* filtered
and is not. Had that gone into the rules unverified, every tester would have believed it was
excluding its own echoes while seeing them all.

**The correct fix for logged-output.md §2 and STANDING-ORDERS §8:** do the exclusion **on the
box side, after the read** — pipe the captured output through `grep -v IMISH` there — and keep
bounding the filter to the case's own time window. Do **not** recommend `| exclude`.

Credit to the tester for testing a proposed rule before it became one.

**Credit where due:** the rule still worked. It surfaced the `[SCRIPT]snmp restart isis` lines
and gave every case a clean reboot/exception/CPU/memory baseline. This is a refinement, not a
retraction.

### 🔴🔥 NEEDS TEST ENGINEER — T44309: sampled packet headers reached the collector AFTER sFlow was disabled

**The most serious thing this campaign has found, and the tester reported it rather than
burying it in a PASS.**

Once, after `no sflow enable` — with the CLI reporting `Admin Status Disabled` and
`Polling/sampling/Tx ....... Inactive` — the DUT sent **11 datagrams carrying 85 flow samples of
traffic that arrived *after* the disable**. 78 were positively identified by their payload
marker, the 85 sampler sequence numbers were consecutive, and `sample_pool` claimed 42,500
packets where only ~110 had actually passed.

**Why this matters beyond a failed check:** sFlow flow samples carry **real user traffic
headers**. This is packet header data leaving the device to a collector after monitoring was
switched off, while every management surface on the box said monitoring was off.

**Why the tester still graded PASS, and why FAIL is defensible:**
- For PASS — the feature itself was proven exact (exactly 40 samples from 2000 frames at 1-in-50,
  rate change scaling tenfold, correct per-port scoping), and the tester then ran **three further
  enable→disable cycles, the last mirroring the original sequence step for step including the
  mid-flight rate change, and all three were clean.** The anomaly is intermittent.
- For FAIL — **the removal check failed on its first execution.** A removal that does not reliably
  remove is a FAIL condition, and intermittency makes it worse to live with, not better.

The evidence for both readings is in the working log. **It is a one-line re-grade.**

**A second anomaly in the same case:** one fresh enable at 1-in-50 yielded **zero** flow samples
from the identical burst that had earlier given exactly 40.

### NOTICE (record) — the group B restore recipe was corrected mid-group

The tester wrote the recipe before reading the sFlow CLI surface and guessed
`sflow collector ip <addr>`, which the DUT rejects. The measured forms are
**`sflow collector id <1-5> ip <addr>`**, and the negations **`no sflow collector id 1`** /
**`no sflow agent ip`** take no address. Corrected in place. Worth noting as a process point:
a restore recipe written before the surface is read can be wrong in a way that only bites the
person trying to restore from it.

### 🟠 NEEDS TEST ENGINEER (recorded, not asked) — confirm T33413's grade: PARTIAL or UNSUPPORTED?

The tester graded **PARTIAL** and set out its reasoning rather than deciding quietly. The
sentinel did **not** re-grade: logged-output.md §1 makes this a genuine judgement call and
`grading-authority-tier-list` puts the Test Engineer above both of us.

**The case for PARTIAL (what the tester chose).** §1: *"It was unable to run fully, because of a
physical or other misconfiguration"*. The platform **does** have the `hw-monitoring` trap group
and it **does** arm. What is missing is any way for a bench to drive a sensor past a
hardware-fixed limit — the coolest sensor reads **27 °C against a 61 °C limit**. That is a bench
gap, and §1 puts a bench gap at PARTIAL.

**The case for UNSUPPORTED.** §1: *"The platform does not support what the case tests"*. If the
case is read as "the platform provides a settable temperature threshold and notifies on it",
then it does not: there is no settable threshold anywhere, and the RMON-alarm substitute is
**refused by the product**. On that reading the gap is the platform's, not the bench's.

**Either is defensible. It changes the filename** (`-partial.log` vs `-unsupported.log`) **and
the verdict block** the final log must carry (PARTIAL needs `NOT RUN:` + `UNBLOCK:`;
UNSUPPORTED needs `NEEDS:` + `ABSENT:`). Settle it before `/create-logs`.

### 🔥 Product finding — RMON alarmVariable is restricted to the RMON tables, against RFC 2819

The second developer-grade finding from group B. **Five attempts, four syntaxes, all refused,
none created** — including a plain `sysUpTime.0` control, so it is not a formatting mistake:

```
% OID number did not match 1.3.6.1.2.1.16.1.1.1. (etherStats) or 1.3.6.1.2.1.16.2.2.1. (etherHistory)
% OID field string did not match an acceptable etherHistory field
% Stats or history collection index was not correctly entered
```

**RFC 2819 places no such limit on `alarmVariable`** — it is any integer-valued MIB object, and
that generality is the entire point of the RMON alarm group. On this build **no threshold on
temperature, CPU, memory or any non-RMON counter can be expressed at all.**

Measured alongside it, and useful: the AT-ENVMONv2 temperature table is at
**`1.3.6.1.4.1.207.8.4.4.3.12.3.1`** — col 4 description, col 5 reading, col 6 upper limit,
col 7 status, indexed `.1.<resource>.<sensor>` — and all 14 sensors agree with
`show system environment` reading for reading. **So temperature CAN be thresholded by an
external manager polling that table; the device simply cannot notify on it itself.** That is the
crisp statement of the gap for a developer.

### ✅ RESOLVED 09:25 NZDT (was a live hazard 09:22–09:24) — the DUT rejected `manager` on the console

**Resolved by the tester, without a reload and without help.** `manager` authenticated at
09:24:48 — the RADIUS path stopped answering, so the `local` fallback engaged as designed on a
no-response — and the tester immediately restored local authentication:

```
aaa authentication login default local
no aaa accounting login default
```

**Peak exposure: 2 failed `manager` logins against a 5-failure lockout** (the sentinel first
wrote 3, miscounting the attempt that actually succeeded; the tester's count is correct).
Nothing was lost, the account was never locked, and no reload was needed.

**The recovery became a measurement.** The tester stopped its radsrv instance, so the server went
unreachable and the `local` fallback engaged on no-response. `manager` then authenticated locally
in **25.5 s**, against **0.4 s** when the method list is plain `local` — the DUT really did try
RADIUS first and waited out `timeout 5` × (1 + 3 retransmits) before falling through. That
timing difference is the proof that the method list was in force.

**🔥 Product fact, now recorded: `local` is NOT a fallback for an Access-Reject.** The server
rejected `manager` (`Access-Reject to 10.38.22.34 id=134 user='manager' (no such user)`) and the
DUT honoured it without trying `local`. The fallback fires on **no response**, never on an
authoritative reject. **The safe pattern is: the RADIUS server must know every account you still
need, or the server must be absent.** This belongs in `platforms/x960.md`.

**RESOLVED — and two sentinel hypotheses were settled against the server log, one wrong, one right:**
- **A `radclient1` lockout was NOT what happened.** The sentinel read the repeated 09:27–09:28
  rejects as a possible lockout poisoning the positive leg. Wrong: every attempt reached the
  server and the server's answers are on record — 09:27:17 was a deliberate **wrong-password**
  control (`Access-Reject`), and 09:27:55–09:28:10 was a deliberate **wrong-shared-key** control
  (four `DROP-bad-msg-auth` 5.003 s apart, then the local fallback). Designed negative legs, not
  accidents. The DUT's log never passed `FAILED LOGIN 2` against the 5 that lock an account.
- **The `Last login:` discriminator was CONFIRMED**, and is now `platforms/x960.md` §7E.2. Five
  local logins printed `Last login: … on ttyS0`; three RADIUS-served logins printed none; each
  cross-checked against the server's own Access-Accept lines, no exceptions. Mechanism: the line
  comes from the Linux lastlog of a **local** account, and a RADIUS session has no local account.
  (The sentinel had seen one counter-example and told the Test Engineer it probably would not
  survive — it did.)

**`Session setup problem, abort.` was NOT an authentication failure.** The server logged
`Access-Accept to 10.38.22.34 id=195 user='radclient1' (ok)` — the DUT received and accepted the
Accept and then failed to build the session, and no Accounting-Request followed. The Accept
carried only a Reply-Message: **no Service-Type and no privilege attribute**. That is an
instrument defect in the test server, **not a DUT defect**, and it is being treated as a step of
its own. Also measured: the DUT's Access-Request carries `NAS-Identifier='console'`,
`Service-Type=8 (Authenticate-Only)` and a Message-Authenticator.

---

**The hazard as it stood:**

**State:** T33408 configured the DUT as a RADIUS client:

```
radius-server host 10.38.22.33 auth-port 11812 acct-port 11813 key testing123
aaa authentication login default group radius local
aaa accounting login default start-stop group radius
```

The RADIUS server is a **user-owned freeradius instance the tester started on the box**, on
unprivileged ports 11812/11813. It does **not** know the user `manager`.

**What is happening:** `manager` now fails on the DUT console (`Login incorrect`, first seen
09:22:58, again 09:23:26). A `radclient1` login got as far as `Session setup problem, abort.`

**Why the `local` fallback did not save it — the sentinel got this wrong and says so.** The
sentinel advised `group radius local` on the grounds that it protects the console. It protects
against the server being **unreachable**: the fallback to `local` fires on no-response. It does
**not** fire when the server returns an **Access-Reject**, which is authoritative and which AW+
honours. freeradius rejects `manager` because it has no such user, so the DUT rejects it too.

🔴 **Do NOT retry `manager` in a loop.** AW+ locked swi_a at **5 failed logins** with a timer
that restarts on each further attempt. swi_a is already lost to exactly this. If the DUT's
`manager` reaches 5, the only console that matters is gone.

**Recovery, neither option needing a console login:**
1. **Stop the tester's freeradius instance on the box** (preferred). The server becomes
   unreachable, the `local` fallback genuinely engages, and `manager` authenticates locally as
   before. Instantly reversible by restarting it.
2. **Add `manager` to that freeradius instance's users file** and reload it.

Then remove the three AAA/radius lines and re-verify `manager` locally before anything else.

⚠️ **A reload is NOT a recovery here** and is the Test Engineer's call: the L3 underlay
(`vlan10 10.38.22.34/27`, `vlan48 10.38.22.66/27`) is **running-config only** and the boot config
is `flash:/default.cfg`, so a reload clears the AAA lines **and** destroys the server path that
groups B and C need.

**Two things to keep, because they are real measurements, not just damage:**
- `manager` being rejected is itself **evidence the DUT really is consulting RADIUS** rather
  than falling through to local — which is what T33408 set out to prove.
- `Session setup problem, abort.` for `radclient1` suggests RADIUS **authentication succeeded**
  and session establishment then failed, most likely a missing privilege / Service-Type
  attribute in the server's reply rather than a DUT defect. Confirm against the server-side
  `Successes` counter before grading it either way.

### 🟠 NEEDS TEST ENGINEER (recorded, not asked) — reboot persistence is NOT MEASURED for group A

Raised by the group A tester with T33407's RESULT, and its reasoning is correct, so the sentinel
did not overrule it.

**Group A performs no reload at all.** Two reasons, both sound:
1. The DUT's L3 underlay (`vlan10 10.38.22.34/27`, `vlan48 10.38.22.66/27`) exists in
   **running-config only**, and the boot config is `flash:/default.cfg`. **A reload destroys the
   server path** — which groups B and C also need.
2. `copy running-config startup-config` would change your standing bench configuration. That is
   bench-level, STANDING-ORDERS §4, and is not done unattended.

⇒ **T33407, T33408 and T33409 are graded without the reboot-persistence limb**, and each log must
say so explicitly rather than implying it was covered. This does not reduce their verdicts; it
bounds them.

**The cheap fix, one decision from you:** say once whether the underlay may be written to
startup-config. If yes, a **single reload covers all three cases** and the limb can be added on a
re-run. If no, the limb stays NOT MEASURED for every case in this campaign, which is the honest
outcome and should be stated in the group README.

### 🔴 NEEDS TEST ENGINEER (recorded, not asked — unattended run) — swi_a / u5 will not accept a login

Raised by the tester at 2026-10-20 08:3x NZDT, during the TRIAGE gate. **The campaign was NOT
held for it**: no case in this list needs swi_a, so triage and the run continue on u2 and u3.

**Probe exit 4 USER-CONFLICT**, Advisory verbatim:

```
  - the session gives facts for /dev/u5 (outlet 3@10.36.230.35, name swi_a), but no device
    was read on /dev/u5 this run
  Nothing recorded was changed. Ask the Test Engineer which is right.
```

**What is true.** u5 answers at 9600 with a clean `awplus login:` banner, so **the x950 is alive
and running** — this is a login problem, not a dead unit. `manager`/`friend` is refused. The
probe's own meta: `"login": "no prompt after login. tail='\r\nLogin incorrect\r\n\r\nawplus login: '"`.

**The username echo is TRUNCATED.** The console transcript shows `awplus login: maPassword:` —
the device took `ma` as the whole username and went straight to the password prompt. That is a
character-loss or console-state symptom, not evidence that the password changed. `u5 @9600` is
recorded in 27 places in this repo, and the regenerated `[baudrates]` section now carries
**swi_b 9600 and swi_d 115200 only, nothing for u5**.

**The tester locked the account, and said so.** The probe's attempts plus one `tools/tb ckcon`
diagnostic reached five failures: `The account is locked due to 5 failed logins. (5 minutes left
to unlock)`. It auto-unlocks. **The tester did not retry**, correctly: more attempts re-lock it,
and a password or console change on swi_a is bench-level (STANDING-ORDERS §4).

**Side effect on the record.** The probe regenerated `bench-setup/tb277/bench-state.md` from what
it could measure, so **swi_a's device row and its four LLDP-proven links to swi_b and swi_d have
dropped out of that file**. That is the probe working as designed — bench-state.md is measured
state only — not a deletion. The 2026-10-16 content is in git history. Nothing was hand-edited
and nothing was reverted. The next probe that can read u5 restores it.

🔴 **CORRECTION, 2026-10-20 12:02 — the truncated echo is NOT evidence of the cause.**
The group C tester's login to **swi_b on u3** (also 9600) shows the **identical signature** —
`x960-28YSQ login: maPassword:` — and **that login SUCCEEDED** (`Last login:` followed
immediately). So `ma`/`mana` is a harmless **echo/display race on a 9600 console**, where the
`Password:` prompt overwrites the tail of the echoed username; the device receives the full
string. It happens on a console where authentication works.

⇒ The sentinel's earlier reasoning — that the truncation pointed at baud or flow control and
therefore weakened the "the credential really changed" explanation — **does not hold**. The
progressive `ma`→`mana` difference was noise, not signal. **The cause of u5's refusal is open
again**, and a changed credential is back among the leading candidates.

**For the Test Engineer, when you are back — three candidates, in the order I would try them:**
1. **Console state.** Something may have left the port mid-dialog. One bare CR before the first
   username, then `manager`. Cheapest, and it costs nothing if wrong.
2. **Baud.** Force it: `bench_probe.py --box tb277 --baud 9600 run --consoles u5`. The probe
   never falls back from an explicit `--baud`, so a wrong auto-detection stops hiding the result.
3. **The credential really did change on swi_a**, by someone or something outside this campaign.
   That is yours to settle, not ours to guess at.

Nothing in `tb277.static` or the session facts was changed, and neither side of the
USER-CONFLICT was resolved (STANDING-ORDERS §4).

**Update 08:44:49 NZDT — u5 was attempted again and RE-LOCKED.** The sentinel's feed caught
`awplus login: manaPassword:` → `The account is locked due to 6 failed logins. (5 minutes left
to unlock)`. The tester had said at hand-back that it would not retry; something did. The
sentinel sent it one message to take u5 out of any further pass. **The truncation is
progressive, not random: `ma` at 08:33, `mana` at 08:44** — four characters through instead of
two. That strengthens the baud / flow-control reading and weakens the changed-password reading.
No further attempts should be made; the diagnosis is `--baud 9600` and it is not needed for this
campaign.

- **NOTICE (campaign) — `sflowtool` is absent from tb277.** T44309 will be graded on the DUT's
  emitted sFlow datagrams, decoded by hand, not on a collector's parse. Installing a package is
  root on the box and therefore the Test Engineer's (STANDING-ORDERS §4); it was not requested.
- **NOTICE (campaign) — `/tmp` on tb277 is 95% full** (105 MB free) because of 1.8 GB of
  `wireshark_eth4*.pcapng` belonging to someone else. Not ours to delete. If a case fails for
  want of capture space, that is the reason and the case is BLOCKED, not FAILED.

---

## Triage outcome, 2026-10-20 08:50 NZDT — 10 runnable, 3 BLOCKED, 1 NOT TESTED

Tester's report: **13 runnable, 0 blocked by topology, 0 blocked outright.** The sentinel then
blocked the three TACACS+ cases on a §4 decision the tester correctly surfaced rather than took.
No AskUserQuestion was used; this run is unattended.

### 🔴 NOTICE (campaign) — TACACS+ needs root, and there is no way round it

**Measured:** `tacacs-server host <ip> ?` offers `key | vrf | <cr>` — **no port option**. TACACS+
is locked to **TCP/49**, a privileged port, so the server must bind as root. The running box has
`tacacs+ 4.0.4.27a-3` installed at `/usr/sbin/tac_plus` but not running.

**The tester proposed** writing `tools/tacplus.py`, adding `tacplus` to `SUDO_TOOLS` in
`tools/tb`, and starting the daemon with `tools/tb sudotool`.

**The sentinel declined, unattended.** `SUDO_TOOLS` is a 14-name allowlist of **traffic
generators** (`linerate vsend igmp dhcp4 dnsresp hostsim arpleg …`), and `tools/tb` says so in
its own error text: *"sudotool is only for the root traffic tools"*. Those need raw sockets.
**Running a network service daemon as root on a privileged port is a different class of
privilege**, and widening a sudo allowlist to admit it is a security-relevant change to a shared
repo tool. STANDING-ORDERS §4 reserves root on the box for the Test Engineer and the queue says
§4 is never loosened unattended. The cases that do not depend on it run; these three do not.

⇒ **T33411, T33410 and T33412 are BLOCKED**, reason: *"TACACS+ requires a server on TCP/49;
binding a privileged port is root on the box (STANDING-ORDERS §4) and the DUT exposes no
alternative port."* Not a topology block; no recable fixes it.

**UNBLOCK, for the Test Engineer — one decision, then the three cases run unchanged:** approve
either (a) adding `tacplus` to `SUDO_TOOLS` with a `tools/tacplus.py` that writes its config into
the run workdir and only starts/stops `/usr/sbin/tac_plus`, or (b) starting `tac_plus` yourself
once before the run. Then `/test-mode --resume tb277/x960/CAMPAIGN-QUEUE-2026-10-20T0825.md`.

### NOTICE (campaign) — the running freeradius is not usable without root, and does not need to be

Its clients and users live under `/etc/freeradius/3.0/`, root to edit. Because the DUT accepts
`radius-server host <ip> auth-port <n> acct-port <n>`, group A runs a **second, user-owned
freeradius** (`freeradius -d <config tree in the run workdir> -X`) on unprivileged ports and
points the DUT at those. No root, full control of clients and users, system instance untouched.
**This is why RADIUS is runnable and TACACS+ is not** — RADIUS has a settable port, TACACS+ does
not.

### NOTICE (campaign) — T33413's true over-temperature limb is NOT MEASURABLE

`temperature ?` and `environment ?` are both `% Unrecognized command` in config mode, and
`snmp-server enable trap ?` has **no temperature group**. The limits are fixed in hardware:
Front Right reads **27 °C against a 61 °C limit**, every sensor `Ok`. Firing the real
AT-ENVMONv2 `hw-monitoring` fault trap needs the unit physically heated past its limit, and no
threshold can be moved down to meet the reading. **A bench cannot command that.**

The measurable route, which the case is graded on instead: (a) arm
`snmp-server enable trap hw-monitoring`, prove it armed, in running-config, removable and
reboot-persistent, with `snmptrapd` up as a negative control that no fault trap fires while all
sensors read Ok; **plus** (b) an **RMON alarm** bound to the temperature sensor's AT-ENVMONv2
OID with a rising threshold set **just below the current reading**, producing a real trap derived
from a real temperature value, and a control alarm set **above** the reading that must not fire.
The log must state plainly that the genuine over-temperature limb was NOT MEASURABLE, and why.

### NOTICE (campaign) — T44309 sFlow needs a decoder written

`sflowtool` is absent and installing it is root. `tools/` has no sFlow decoder. The tester writes
`tools/sflowwire.py` on the model of `tools/snmpwire.py` (pure Python, reads a `tcpdump -w` pcap,
no scapy), printing agent address, sub-agent id, sequence, sample type, sampling rate and the
sampled header. Captures stay short and are copied out at once — `/tmp` is 95% full.

### NOTICE (record) — tb277 has no deployed `.setup`

`/home/st-art/st-art/configs/tb277.setup` absent, `/nfsHome` not mounted, no local
`tb277.setup.current`. Irrelevant to 13 manual cases; it would block any framework run on this
box. Applying one is `bench_probe.py apply`, STANDING-ORDERS §4.

### NOTICE (process) — swi_a's manager account was locked by the tester

The probe's attempts plus two diagnostic logins reached **7 failures**; the five-minute timer was
last restarted at ~08:45. Stated plainly so it is never later read as a device fault. Blocks
nothing.

### Measured facts the group testers should not rediscover

- **The 2026-10-16 L3 underlay is still up and was NOT rebuilt**: `vlan10 10.38.22.34/27` on
  port1.0.10, `vlan48 10.38.22.66/27` on port1.0.48. Reachability measured **eth3→.34 3/3,
  eth4→.66 3/3**. That is the server path all cases need. The box is **10.38.22.33**.
- **DUT clock is UTC, +13 h behind the box — AND ~15 s SLOW on top of that.** 🔴 **CORRECTED
  2026-10-20 10:21 by the group B tester**; the triage block and the group A/B dispatches both
  said "no skew", which was wrong. Measured twice, 21 minutes apart, constant: box 10:17:25 NZDT
  ↔ DUT 21:17:10 UTC. The timezone offset was right; the extra ~15 s was not recorded anywhere.
  **It matters for correlating a DUT log line against a box-side capture** — it is how T44308's
  five RMON log lines were matched to its four traps. No clock was changed.
- **The DUT is still on the factory password** (`manager`/`friend` authenticated), so T47199's
  precondition is already true and no password change is needed to reach it. **A fresh console
  login shows NO warning** — only `Last login` and the version banner; `show banner login` is
  empty. T47199 must look at telnet, SSH and HTTP. If it appears nowhere and the TPS says the
  feature exists, that is a **FINDING, not UNSUPPORTED**.
- **T33416's surface is unverified**: `type ?` cannot be read without creating `trigger N`
  first, which TRIAGE may not do. First action of group C's tester. `type` must be set before
  `description`, and if `type interface` is absent the case is UNSUPPORTED with the `type ?`
  output as evidence.
- DUT licence is `atlnz` Full (RADIUS-FULL, RADIUS-100, RADIUS-3 present). **Nothing in this
  campaign is licence-gated.**

### §8 health-check instrument notes — first campaign under the new rule

All six reads work on the x960-56YSQ. Baseline at 08:46 NZDT:

- `show reboot history` — newest `2026-10-16 06:22:04 Expected CLI(user request)`. Diff the **top
  entry only**; the table carries year-2000 dates from before the clock was set.
- `show exception log` → **`None`**.
- `show cpu` — ⚠️ **`show cpu | include idle` does NOT give the summary.** It matches the
  per-process `idle` state column and returns a wall of kworker rows. Use plain `show cpu`.
- `show memory` → `RAM total: 8092132 kB; free: 7453840 kB; buffers: 1544 kB`.
- `show log | include kernel|…` — ⚠️ **noisy**: `kernel` matches the whole 2026-10-16 boot log
  (~40 lines) every time. **Two pre-existing `kern.err` lines are NOT a case finding**:
  `boardinfo-eeprom-i2c 1-0050: Failed to read eeprom data for board_index 0` and the same for
  `1-0052`, both at `2026 Oct 16 06:22:36`. Bound the filter to the case's own time window.

---

## Group A `aaa-2026-10-20T0825` — bench setup and the exact restore recipe

Written by the group's tester (bench-runner) before the group's first case, so a fresh tester
can restore the bench from this file alone if the session dies mid-group.

**Consoles used:** /dev/u2 (swi_d, the DUT) and /dev/u3 (swi_b) only. /dev/u5 and /dev/u1 are
never opened. Box scratch: `/tmp/ckaaa/` (`tools/tb scratch tb277 ckaaa`).

**Physical/bench setup this group needs: NONE beyond what is already standing.** No recable, no
VLAN change, no new SVI, no PDU action. The group uses the L3 underlay that was already up:

    tb277 eth3 10.38.22.33/27  <->  swi_d port1.0.10, DUT `interface vlan10` 10.38.22.34/27
    tb277 eth4 10.38.22.65/27  <->  swi_d port1.0.48, DUT `interface vlan48` 10.38.22.66/27

⛔ Do NOT shut port1.0.10 or port1.0.48 and do NOT rebuild these SVIs. They exist in
running-config only (boot config is `flash:/default.cfg`), so a DUT reload destroys them.
**This group deliberately performs no reload and writes nothing to startup-config.**

**What each case adds to the DUT, and the exact command that removes it:**

| case | added on swi_d (u2) | removed by |
| --- | --- | --- |
| T33407 | `radius-server local` block (`server enable`, `nas 10.38.22.33 key …`, `user …`), plus an auto-created `nas 127.0.0.1` entry the DUT makes itself | `configure terminal` / `no radius-server local` — removes the whole block including the auto-created NAS |
| T33408 | `radius-server host 10.38.22.33 auth-port 11812 acct-port 11813 key testing123`, `aaa authentication login default group radius local`, `aaa accounting …` | `no radius-server host 10.38.22.33 auth-port 11812 acct-port 11813`, then restore the baseline `aaa authentication login default local` and `no aaa accounting …` |
| T33409 | `radius-server proxy-server` block (+ whatever its own surface requires) | `configure terminal` / `no radius-server proxy-server` |

**The baseline the group must return to** (from `show running-config` at 2026-10-20 08:59 NZDT,
work/pre-u2.log of T33407). The AAA-relevant lines, and there is no `radius-server` line of any
kind at baseline:

    username manager privilege 15 password 8 $5$bJozIP4D$orvkW78S6QHN65L3EGGJpHS.QlHSjwuYbMynH5.Ifp2
    service ssh
    no service telnet
    service http
    aaa authentication enable default local
    aaa authentication login default local

🔴 **The restore that matters most:** `aaa authentication login default local`. If a case leaves
`aaa authentication login default group radius` behind and the RADIUS server on the box is gone,
console and SSH logins fall through to whatever the method list says next. Every case in this
group therefore configures the fallback form `group radius local`, never `group radius` alone,
and the restore command is:

    configure terminal
    aaa authentication login default local
    no aaa accounting login default
    no radius-server host 10.38.22.33 auth-port 11812 acct-port 11813
    no radius-server local
    no radius-server proxy-server
    end

(`no aaa authentication login default` also returns the list to its default; the explicit
`aaa authentication login default local` above is what the baseline actually shows, so it is
the form that makes `rcdiff.py` clean.)

**Verification after every case:** `python3 tools/rcdiff.py <pre>.log <post>.log` must print
nothing, and `show boot` must still read boot image `flash:/x960-tb277.rel`, boot config
`flash:/default.cfg`.

**The DUT's pre-existing global RADIUS secret is NOT ours.** `show radius` printed
`Secret Key : Byc98JqUNsCGeNIJ8uZhkYpbcbRZY+Fs5c3qCqhdvYw=` before this campaign touched
anything. It is left exactly as found. Every secret this group configures is `testing123`.

---

## Group B `snmpmon-2026-10-20T0825` — bench setup and the exact restore recipe

Written by the group's tester (bench-runner) before the group's first case, so a fresh tester
can restore the bench from this file alone if the session dies mid-group.

**Consoles used:** /dev/u2 (swi_d, the DUT) and /dev/u3 (swi_b) only. /dev/u5 and /dev/u1 are
never opened. Box scratch: `/tmp/cksnmpmon/` (`tools/tb scratch tb277 cksnmpmon`).

**Physical/bench setup this group needs: NONE beyond what is already standing.** No recable, no
VLAN change, no new SVI, no PDU action. The group uses the L3 underlay that was already up:

    tb277 eth3 10.38.22.33/27 (MAC 00:0d:b9:55:77:0e)  <->  swi_d port1.0.10, vlan10 10.38.22.34/27
    tb277 eth4 10.38.22.65/27 (MAC 00:0d:b9:55:77:0f)  <->  swi_d port1.0.48, vlan48 10.38.22.66/27
    swi_b port1.0.2  <-> swi_d port1.0.2    (LLDP both ends; RSTP root path)
    swi_b port1.0.16 <-> swi_d port1.0.16   (LLDP both ends; Alternate/Discarding under RSTP)

The DUT's vlan10/vlan48 MAC (both SVIs share one) is `e0:1a:ea:d4:70:43`.

⛔ Do NOT shut, flap or reconfigure port1.0.10 or port1.0.48. They carry the path to the trap
receiver and the sFlow collector; flapping one destroys the instrument meant to catch the trap.
The link-state case (T44301) flaps **port1.0.2** only.
⛔ These SVIs exist in running-config only (boot config is `flash:/default.cfg`), so a DUT reload
destroys them. **This group performs no reload and writes nothing to startup-config**, and
therefore does NOT measure reboot persistence — the same recorded NEEDS TEST ENGINEER item as
group A.

**Common setup every case in this group applies, and the exact command that removes it:**

| added on swi_d (u2) | removed by |
| --- | --- |
| `snmp-server community testing123 ro` | `no snmp-server community testing123` |
| `snmp-server host 10.38.22.33 version 2c testing123` | `no snmp-server host 10.38.22.33 version 2c testing123` |
| `snmp-server enable trap <group>` (rmon / nsm / hw-monitoring, per case) | `no snmp-server enable trap <group>` |

**What each case adds on top, and the exact command that removes it:**

| case | added on swi_d (u2) | removed by |
| --- | --- | --- |
| T44308 | `rmon event 11`, `rmon event 12`, `rmon alarm 11`, `rmon alarm 12`; on `interface port1.0.10`: `rmon collection stats 11`, `rmon collection history 11` | `no rmon alarm 11`, `no rmon alarm 12`, `no rmon event 11`, `no rmon event 12`; in `interface port1.0.10`: `no rmon collection stats 11`, `no rmon collection history 11` |
| T33413 | `snmp-server enable trap hw-monitoring`; an RMON event + alarm bound to a temperature variable **if the CLI accepts one** (`rmon alarm ?` says the variable must be `etherStatsEntry.n.n`, so this is expected to be rejected — that rejection is the case's measurement) | `no snmp-server enable trap hw-monitoring`; `no rmon alarm <n>`, `no rmon event <n>` |
| T44301 | `snmp-server enable trap nsm`; on `interface port1.0.2`: `snmp trap link-status`; the step itself does `shutdown` / `no shutdown` on port1.0.2 | `no snmp-server enable trap nsm`; in `interface port1.0.2`: `no snmp trap link-status`, and `no shutdown` so the link is left UP |
| T44309 | `sflow agent ip 10.38.22.34`, **`sflow collector id 1 ip 10.38.22.33`**, `sflow enable`; on `interface port1.0.10`: `sflow sampling-rate 50` (min is 50), `sflow polling-interval 20` | `no sflow enable`, **`no sflow collector id 1`**, **`no sflow agent ip`** (both negations take NO address -- the full form is rejected), then per interface `no sflow sampling-rate`, `no sflow polling-interval` |

**The baseline the group must return to** (from `show running-config` 2026-10-20 09:56:20 NZDT,
`T44308/work/pre-u2.log`). There is no `rmon`, no `sflow`, no `snmp-server community`, no
`snmp-server host` and no `snmp-server enable trap` line at baseline; the only SNMP line is the
bare `snmp-server`:

    snmp-server
    aaa authentication enable default local
    aaa authentication login default local
    interface port1.0.10
     switchport
     switchport mode access
     switchport access vlan 10
    interface vlan10
     ip address 10.38.22.34/27
    interface vlan48
     ip address 10.38.22.66/27

⚠️ **Corrected 2026-10-20 11:30 by the group's tester, measured not guessed:** the sFlow
collector is addressed by INDEX (`sflow collector id <1-5> ip <A.B.C.D>`); `sflow collector ip
<addr>` is `% Unrecognized command`. Both negations take no address. The forms above are the
measured ones and the forms originally written into this section were wrong.

🔴 **The restore that matters most:** `interface port1.0.2` must be left `no shutdown` after
T44301, and `port1.0.10`/`port1.0.48` must never be touched at all. The full group restore is:

    configure terminal
    no snmp-server enable trap rmon
    no snmp-server enable trap nsm
    no snmp-server enable trap hw-monitoring
    no snmp-server host 10.38.22.33 version 2c testing123
    no snmp-server community testing123
    no sflow enable
    no sflow collector id 1
    no sflow agent ip
    no rmon alarm 11
    no rmon alarm 12
    no rmon event 11
    no rmon event 12
    interface port1.0.10
     no rmon collection stats 11
     no rmon collection history 11
     no sflow sampling-rate
     no sflow polling-interval
    interface port1.0.2
     no snmp trap link-status
     no sflow sampling-rate
     no sflow polling-interval
     no shutdown
    end

**Verification after every case:** `python3 tools/rcdiff.py <pre>.log <post>.log` must print
nothing, and `show boot` must still read boot image `flash:/x960-tb277.rel`, boot config
`flash:/default.cfg` (both confirmed at 09:56:17 NZDT before the group's first command).

**Every secret this group configures is `testing123`** (community string and sFlow/trap
community alike). The DUT's pre-existing global RADIUS secret is left exactly as found.

---

## Group C `mgmt-2026-10-20T0825` — bench setup and the exact restore recipe

Written by the group's tester (bench-runner) before the group's first case, so a fresh tester
can restore the bench from this file alone if the session dies mid-group.
Cases, in dispatch order: **T33378** Telnet Server (IPv4) → **T47199** default-password warning
→ **T33416** Triggers - Interface.

**Consoles used:** /dev/u2 (swi_d, the DUT) only. /dev/u3 is opened by the gate probe and by
nothing else in this group; **/dev/u5 and /dev/u1 are never opened.** Box scratch:
`/tmp/ckmgmt/` (`tools/tb scratch tb277 ckmgmt`).

**Physical/bench setup this group needs: NONE beyond what is already standing.** No recable, no
VLAN change, no new SVI, no PDU action, no reload. The group uses the same L3 underlay as
groups A and B:

    tb277 eth3 10.38.22.33/27 (MAC 00:0d:b9:55:77:0e)  <->  swi_d port1.0.10, vlan10 10.38.22.34/27
    tb277 eth4 10.38.22.65/27 (MAC 00:0d:b9:55:77:0f)  <->  swi_d port1.0.48, vlan48 10.38.22.66/27
    swi_b port1.0.2  <-> swi_d port1.0.2     (LLDP both ends; RSTP root path)
    swi_b port1.0.16 <-> swi_d port1.0.16    (LLDP both ends; Alternate/Discarding under RSTP)

⛔ Do NOT shut, flap or reconfigure **port1.0.10** or **port1.0.48**: they carry the only IP path
from the box to the DUT, which IS this group's instrument (a telnet/SSH session and its capture).
T33416's interface trigger uses **port1.0.2** only.
⛔ The SVIs exist in running-config only (boot config `flash:/default.cfg`), so a reload destroys
them. **This group performs no reload and writes nothing to startup-config**, and therefore does
**NOT** measure reboot persistence — the same recorded NEEDS TEST ENGINEER item as groups A and B.

**The baseline the group must return to** (`show running-config` 2026-10-20 11:39:09 NZDT,
`T33378/work/pre-u2.log`; byte-identical to group B's restored baseline). The lines this group
can touch, at baseline:

    no banner motd
    username manager privilege 15 password 8 $5$bJozIP4D$orvk...     <- the FACTORY password 'friend'
    ssh server allow-users manager
    service ssh
    no service telnet
    service http
    aaa authentication enable default local
    aaa authentication login default local
    security-password minimum-length 8
    security-password history 1
    line con 0
    line vty 0 7

There is no `trigger`, no second `username`, no `banner login` and no `banner exec` at baseline.
`show telnet` reads `Telnet server : Disabled / Protocol : None / Port : 23`.
`show boot`: boot image `flash:/x960-tb277.rel`, boot config `flash:/default.cfg` — both
confirmed at 11:39:08 NZDT before the group's first command.

**What each case adds on swi_d (u2), and the exact command that removes it:**

| case | added on swi_d (u2) | removed by |
| --- | --- | --- |
| T33378 | `service telnet ip` (the IPv4-only form; `service telnet ?` offers `ip \| ipv6 \| <cr>`) | `no service telnet ip` — and the group's end state must be `no service telnet`, i.e. `show telnet` back to `Disabled / None / 23` |
| T47199 | `username ckalt privilege 15 password testing123` — a **second** account whose password is NOT the factory default, used as the control for the default-password warning. Telnet stays on from T33378 for this case | `no username ckalt` |
| T33416 | `trigger 1` with `type interface <port> <event>` and an action (`script`/`command`); on `interface port1.0.2` the step itself does `shutdown` / `no shutdown` | `no trigger 1`; in `interface port1.0.2`: `no shutdown` so the link is left UP |

🔴 **The manager password is NOT changed by this group.** T47199's precondition (the factory
password `friend` is still set) is already true, and the dispatch left the change to the tester's
judgement. It is **declined, deliberately**: `security-password minimum-length 8` is configured
and `friend` is 6 characters, so putting it back would need the length rule relaxed and restored
as well; and the product may not recognise a re-entered `friend` as the *factory* password again,
which would destroy the precondition for this case on this DUT permanently, unattended, with no
way to restore it. The control limb is obtained instead from a second account (`ckalt`) whose
password is not the default — same discrimination, fully reversible.

**Every secret this group configures is `testing123`.** No secret is sent down a console except
that one and the factory `friend`, which the DUT already holds.

**The full group restore is:**

    configure terminal
    no service telnet ip
    no service telnet
    no username ckalt
    no trigger 1
    interface port1.0.2
     no shutdown
    end

**Verification after every case:** `python3 tools/rcdiff.py <pre>.log <post>.log` must print
nothing, and `show boot` must still read boot image `flash:/x960-tb277.rel`, boot config
`flash:/default.cfg`.

**Authority consulted before the first command** (`review-feature-docs-before-testing`), so no
case in this group is graded against the DUT alone. The case numbers in the titles map to the
**X960 platform support TPS** rows with a constant **−2** offset (verified against group A:
case *(274)* Local RADIUS Server ↔ TPS row **272**):

| case | TPS row | TPS feature | Pri | Supported |
| --- | --- | --- | --- | --- |
| T33378 *(229)* | **227** | Management / Telnet Server(IPv4) | 1 | **Yes** |
| T47199 *(273)* | **271** | Management / Show warning message when user continue to use default PW | 1 | **Yes** |
| T33416 *(283)* | **281** | Triggers / Interface | 1 | **Yes** |

⇒ **All three are declared supported on this platform**, so an absent behaviour is a FINDING,
not a platform limit.

**T47199's behavioural authority** is the TFS *"Warning when using default password"*
(`https://wiki.atlnz.lc/awpwiki/index.php/Warning_when_using_default_password_TFS`, project 2616,
rev 0.3, approved 21/Oct/21), spec **2616.1**:

> The system will check **at every login using the default account 'manager'** if the factory
> default password 'friend' is set, if it is, the system will warn the user that the default
> password should be changed.

with this worked example, and `Initial Release Targets: all platforms in 5.5.1-2`,
`Excluded Targets: None`, `Logging specifications: None`:

    awplus login: manager
    Password:
    AlliedWare Plus (TM) 0.0.0 09/26/21 21:23:17
    % Default password needs to be changed.
    awplus>

⇒ the expected string is **`% Default password needs to be changed.`**, printed after the
version banner and before the first prompt, on **every** login as `manager` while the password is
`friend`. The TFS specifies no log line and no show command, so the login byte stream is the only
place it can be graded — which is why this group needed a network login driver
(`tools/netlogin.py`, new).


---

## Group D `tacacs-2026-10-20T0825` — bench setup and the exact restore recipe

Written by the group's tester (bench-runner) before the group's first case, so a fresh tester
can restore the bench from this file alone if the session dies mid-group.

**Consoles used:** /dev/u2 (swi_d, the DUT) only; /dev/u3 (swi_b) is opened only if a case needs
a second device, and no case in this group does. /dev/u5 and /dev/u1 are never opened.
Box scratch: `/tmp/cktac/` (`tools/tb scratch tb277 cktac`).

**Occupancy, 2026-10-20 13:3x NZDT:** `tools/tb precheck tb277 u2,u3` → exit 5 FOUND, the single
item being `process 744 (root) /usr/sbin/ser2net` — the box's own console daemon, the **same
item the Test Engineer already answered "Proceed" on at 2026-10-19 16:53** and that groups A, B
and C all ran under. Both session consoles read **free**. u2 was at a clean `awplus login:`
prompt (gate 2), i.e. logged out, not parked mid-state.

**Physical/bench setup this group needs: NONE beyond what is already standing.** No recable, no
VLAN change, no new SVI, no PDU action, and **no reload** (the L3 underlay is running-config
only; boot config is `flash:/default.cfg`). The group uses the standing L3 underlay:

    tb277 eth3 10.38.22.33/27  <->  swi_d port1.0.10, DUT `interface vlan10` 10.38.22.34/27
    tb277 eth4 10.38.22.65/27  <->  swi_d port1.0.48, DUT `interface vlan48` 10.38.22.66/27

⛔ Do NOT shut port1.0.10 or port1.0.48. **10.38.22.33 is the TACACS+ server address**, so
port1.0.10 IS the path under test.

**The server is the Test Engineer's, not the tester's.** `tac_plus -C /etc/tacacs+/tac_plus.conf`,
pid 3491, started 2026-10-20 13:29:56 NZDT. 🔴 The tester never restarts, reconfigures or stops
it, and never edits `/etc/tacacs+/tac_plus.conf` — both are root (STANDING-ORDERS §4). Stopping
it when the group finishes is the Test Engineer's command.
`/var/log/tac_plus.acct` measured **size 0** before the group's first command: a true empty
baseline for every accounting window.

**What each case adds to the DUT, and the exact command that removes it:**

| case | added on swi_d (u2) | removed by |
| --- | --- | --- |
| T33411 | `tacacs-server host 10.38.22.33 key testing123`, `aaa authentication login default group tacacs+ local`, a temporary local `username tacuser privilege 15 password …` (the escape route to config mode) | `no tacacs-server host 10.38.22.33`, `aaa authentication login default local`, `no username tacuser` |
| T33410 | the T33411 pair, plus `aaa accounting login default start-stop group tacacs+` / `stop-only`, `aaa accounting commands <N> default start-stop group tacacs+`, possibly `aaa accounting update` and a temporary `trigger` for the S1599.1.045/046 mutual-exclusion check | `no aaa accounting login default`, `no aaa accounting commands <N> default`, `no aaa accounting update`, `no trigger <N>`, then the T33411 removals |
| T33412 | the T33411 pair plus a second, deliberately unreachable `tacacs-server host 10.38.22.40` | `no tacacs-server host 10.38.22.40`, then the T33411 removals |

**The baseline the group must return to** (the AAA-relevant lines of `show running-config`; there
is no `tacacs-server` line of any kind at baseline, and group A left the box clean):

    username manager privilege 15 password 8 $5$bJozIP4D$orvkW78S6QHN65L3EGGJpHS.QlHSjwuYbMynH5.Ifp2
    service ssh
    no service telnet
    service http
    aaa authentication enable default local
    aaa authentication login default local

**🔴 The restore that matters most, and the lockout rule this group runs under.**
`platforms/x960.md` §7E.1: `local` at the end of a method list is a fallback for an
**UNREACHABLE** server, never for a Reject. The TACACS+ server does not know `manager`, so the
moment `aaa authentication login default group tacacs+ local` is applied, **`manager` cannot log
in to the console.** This group therefore never enters that state without a proven way back:

1. **Before** the method list is changed, a local `username tacuser privilege 15 password
   localonly1` is created and a console login as `tacuser` is proven to reach `>` and then `#`
   via `enable` (which stays on `aaa authentication enable default local`).
2. The method list is then changed. `tacuser` still authenticates — now by the TACACS+ server,
   with the *different* password `testing123` — and `enable` still reaches `#` from the local
   privilege-15 entry. **That is the escape route.**
3. Every `conlogin.py` call in this state uses `--restore-user tacuser --restore-password
   testing123`, never the default `manager`/`friend`, which would return exit 4.

**🔴 `aaa authentication enable default tacacs+` is NOT configured by this group, on purpose.**
A rejected `enable` leaves the operator at `awplus>` with no way to reach configuration mode,
and on this bench the only recovery is a reload — which this session forbids. See the Issues
entry; it is declared NOT MEASURED, not skipped silently.

**The restore command, in full:**

    configure terminal
    aaa authentication login default local
    no aaa accounting login default
    no aaa accounting commands 15 default
    no aaa accounting commands 1 default
    no aaa accounting update
    no tacacs-server host 10.38.22.33
    no tacacs-server host 10.38.22.40
    no tacacs-server timeout
    no username tacuser
    end

**Verification after every case:** `python3 tools/rcdiff.py <pre>.log <post>.log` must print
nothing, and `show boot` must still read boot image `flash:/x960-tb277.rel`, boot config
`flash:/default.cfg`.

**Authority consulted before the first command** (`review-feature-docs-before-testing`). The
case-title numbers map to **X960 platform support TPS** rows with the same constant −2 offset
group C verified:

| case | TPS row | TPS feature | Pri | Supported |
| --- | --- | --- | --- | --- |
| T33410 *(277)* | **275** | Management / TACACS+ / Accounting | 1 | **Yes** |
| T33411 *(278)* | **276** | Management / TACACS+ / Authentication | 1 | **Yes** |
| T33412 *(279)* | **277** | Management / TACACS+ / Logging | 1 | **Yes** |

⇒ **All three are declared supported on this platform**, so an absent behaviour is a FINDING,
not a platform limit.

**Behavioural authority: the "TACACS+ AAA" TFS** (`https://wiki.atlnz.lc/awpwiki/index.php/
TACACS%2B_AAA_TFS`, project 1599), fetched 2026-10-20. It is what each case is graded against,
because none of the three has any authored step text. The specs that carry this group:

- **T33411** — S1599.1.010 (authentication request format), S1599.1.004 (multiple servers tried
  sequentially), S1599.1.011–016 (enable authentication — NOT MEASURED, above).
- **T33410** — S1599.1.022 (no `tacacs+` option ⇒ no login accounting at all), .023 (START on
  login), .024 (STOP on logout), .027/.028 (`task_id` sequential, and identical in the STOP of a
  session), .025 (global, same on console and VTY), .030–.046 (command accounting: .034 no
  command output, .036 abbreviations expanded, .041 config-mode commands accounted at privilege
  15, .043 unique task_id per command, .045/.046 command accounting and triggers are mutually
  exclusive), S1599.2.06–2.09 (no record for `enable`, an incomplete command, `?`, an invalid
  command, or a command that did not execute).
- **T33412** — the seven logging specs **S1599.1.080–086**: a log message when communication with
  a server is established (.080) and lost (.081), when login authentication succeeds (.082) and
  fails (.083), when enable authentication succeeds (.084) and fails (.085), and when accounting
  notification fails after every configured server has been tried (.086). Note S1599.2.25: there
  is deliberately **no `debug TACACS+` command** — "log messages are considered sufficient" — so
  the log IS the specified interface, and a missing log line is a finding against a spec.

**Instruments, and which one proves what** (STANDING-ORDERS §7 — three independent instruments):

1. **The DUT**: `show tacacs+`, `show running-config`, and the DUT's own `show log`.
2. **The server's accounting file** `/var/log/tac_plus.acct`, read in a bounded window with the
   new `tools/filewin.py` (mark the byte offset before the step, read the delta after it), so a
   zero is a measurement and not an absence of output.
3. **The wire**: `tools/tb capture tb277 cktac eth3 <secs> <out>.pcap tcp port 49` decoded with
   `tools/tcpflow.py --port 49`. TACACS+ bodies are obfuscated with the shared key, but the TCP
   flow, packet count, direction, timing and handshake verdict are all measurable, and
   `tcpflow.py` tells `REFUSED` from `NO-ANSWER` from `ESTABLISHED+DATA` — which is exactly the
   off / on / wrong-key / unreachable discrimination this group needs.

🔴 `/tmp` on tb277 is 95% full. Every capture in this group is bounded in seconds and filtered
to `tcp port 49`.

**Clock.** The DUT is UTC, **+13 h behind the box and ~15 s slow** (measured by group B and
corrected in `## Issues`). Every correlation between a DUT log line and a server-side accounting
record or a capture timestamp in this group applies that offset explicitly.
