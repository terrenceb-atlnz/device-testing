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
| A | T33407 Local RADIUS Server; T33408 RADIUS Client mode; T33409 RADIUS Proxy; T33411 TACACS+ Authentication; T33410 TACACS+ Accounting; T33412 TACACS+ Logging | `aaa-2026-10-20T0825` | TRIAGE | one AAA setup serves all six: freeradius is already up, tac_plus is started by the tester. Order deliberately puts **authentication before accounting/logging** — accounting has nothing to record until a login works |
| B | T33413 Trap Temperature; T44301 Per-port link trap; T44308 RMON; T44309 sFlow Agent | `snmpmon-2026-10-20T0825` | TRIAGE | one monitoring setup: SNMP community + trap host pointing at the box, `snmptrapd` receiving, tcpdump for sFlow. T33413 may not be forceable — a temperature threshold crossing is not something a bench can command |
| C | T47199 default-password warning; T33416 Triggers - Interface; T33378 Telnet Server (IPv4) | `mgmt-2026-10-20T0825` | TRIAGE | DUT-local, or the box acting as a plain client. Cheapest group; run last |
| — | T33427 Flexera Licensing | — | **NOT TESTED** | Test Engineer's decision, 2026-10-19: *"Drop it — NOT TESTED"*. Its step 1 is *"Request Chris Robb to generate a Flexera License for a particular feature"*; installing a licence is the Test Engineer's (STANDING-ORDERS §4) and no licence file was available this session |

Setup and restore recipes are written into this file by the tester before each group's first
case, so a fresh tester can restore the bench from here.

## Results

| case | title | group | verdict | reason | working log | graded |
| --- | --- | --- | --- | --- | --- | --- |
| T33427 | (300) Management - Flexera Licensing | — | NOT TESTED | needs a Flexera licence from Chris Robb; installing a licence is the Test Engineer's (STANDING-ORDERS §4). Dropped by the Test Engineer 2026-10-19 | — | Test Engineer |

## Issues

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
