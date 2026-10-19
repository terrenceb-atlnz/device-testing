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
| A-blocked | T33411 TACACS+ Authentication; T33410 TACACS+ Accounting; T33412 TACACS+ Logging | — | **BLOCKED** | TACACS+ needs a server on **TCP/49**, a privileged port, and the DUT exposes **no alternative**: `tacacs-server host <ip> ?` offers only `key \| vrf \| <cr>` (measured at triage). Binding it is root on the box = STANDING-ORDERS §4, never done unattended. See `## Issues` for the exact unblock |
| B | **T44308 RMON; T33413 Trap Temperature**; T44301 Per-port link trap; T44309 sFlow Agent | `snmpmon-2026-10-20T0825` | RUNNABLE | **Reordered at the tester's recommendation: RMON runs FIRST**, because T33413's only measurable trap limb is an RMON alarm bound to a temperature OID, so the alarm instrument is already proven when T33413 needs it. T33413's genuine over-temperature limb is **NOT MEASURABLE** — see `## Issues`. T44301 must flap **port1.0.2 or port1.0.16**, never port1.0.10/port1.0.48, which carry the path to the trap receiver |
| C | **T33378 Telnet Server (IPv4); T47199 default-password warning; T33416 Triggers - Interface** | `mgmt-2026-10-20T0825` | RUNNABLE | **Reordered at the tester's recommendation: Telnet FIRST**, because the console login shows no default-password warning (measured), so T47199 must look on telnet/SSH/HTTP — and T33378 is the case that turns telnet on. First action for T33416: `trigger 1` → `type ?`, the campaign's one unverified CLI surface |
| — | T33427 Flexera Licensing | — | **NOT TESTED** | Test Engineer's decision, 2026-10-19: *"Drop it — NOT TESTED"*. Its step 1 is *"Request Chris Robb to generate a Flexera License for a particular feature"*; installing a licence is the Test Engineer's (STANDING-ORDERS §4) and no licence file was available this session |

Setup and restore recipes are written into this file by the tester before each group's first
case, so a fresh tester can restore the bench from here.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33407 | (274) Management_RADIUS - Local RADIUS Server | aaa-2026-10-20T0825 | PASS | served real RADIUS on the wire (5 requests, 2 Accept / 3 Reject, every reply's authenticator verifying against the configured secret); rejected wrong password, unknown user and wrong secret; ignored a non-NAS host; removed cleanly (rcdiff byte-identical) | T33407/work/run1.log | tester |
| T33408 | (275) Management_RADIUS - Radius Client mode | aaa-2026-10-20T0825 | PASS | a user existing only on the RADIUS server logged in to the DUT, proven on the wire (24 packets: 7 Access-Request, 3 Accept, 1 Reject, 7 Accounting-Request, 6 Accounting-Response, 10/10 reply authenticators valid), paired Accounting Start/Stop, controls on wrong password / mismatched key / unreachable server, clean removal (rcdiff byte-identical) | T33408/work/run1.log | tester |
| T33409 | (276) Management_RADIUS - Radius Proxy | aaa-2026-10-20T0825 | PASS | the proxy re-originated each request (new id, Proxy-State carrying the original, added Message-Authenticator, realm stripped); the two legs are cryptographically independent — the same pcap gives authenticator valid=5/invalid=0 on the NAS leg under testing123 and valid=0/invalid=5 on the upstream leg under the same secret | T33409/work/run1.log | tester |
| T33427 | (300) Management - Flexera Licensing | — | NOT TESTED | needs a Flexera licence from Chris Robb; installing a licence is the Test Engineer's (STANDING-ORDERS §4). Dropped by the Test Engineer 2026-10-19 | — | Test Engineer |
| T33411 | (278) Management_TACACS+ - Authentication | — | NOT TESTED | BLOCKED: needs a TACACS+ server on TCP/49; binding a privileged port is root on the box (STANDING-ORDERS §4) and the DUT exposes no alternative port | — | sentinel |
| T33410 | (277) Management_TACACS+ - Accounting | — | NOT TESTED | BLOCKED: depends on T33411 | — | sentinel |
| T33412 | (279) Management_TACACS+ - Logging | — | NOT TESTED | BLOCKED: depends on T33411 | — | sentinel |

## Issues

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
- **DUT clock is UTC, exactly +13 behind the box, no skew.** Record once per group.
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
