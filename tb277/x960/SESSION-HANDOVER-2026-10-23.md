# tb277 / x960 — session handover, 2026-10-23

Covers the campaign run on 2026-10-22 and wrapped in the early hours of 2026-10-23.

## Session facts
Test Engineer: bidhanc@bidhanc-dl
Testbox: tb277
Consoles: **u2 = swi_d (AT-x960-56YSQ, the DUT) — this session opened NO other console**
PDU: 10.36.230.212 outlet u2=1 (and **outlet 8**, see "swi_d has two PSUs" below)
Constraints: Window: partly attended. Sentinel ran "as long as it takes" and stood down at
             this wrap. 🔴 u3 and u5 were never opened — a credential guard, not a fault.

Copied from `CAMPAIGN-QUEUE-2026-10-22T1122.md`, which holds the Test Engineer's own answers.

## TL;DR

The four remaining x960 Management cases are **complete, logged and wrapped: 4 PASS**. All four
final logs and their `.cfg` files exist; **no `work/` folder remains**.

**The bench is whole.** swi_d read clean at the wrap: boot image `flash:/x960-tb277.rel (file
exists)`, boot config `flash:/default.cfg (file exists)`, autoboot disabled, standalone Ready
Active Master, and **every one of the four cases' configuration is gone** (verified by reading,
not by the absence of an error).

🔴 **One item is still the Test Engineer's: `vlan 60` is in swi_d's running- AND startup-config.**
It sits on `port1.0.2`, which is the RSTP **root port** — re-check spanning tree after removing it.

## Current bench state and how to verify it

```bash
cd ~/claude/device-testing
tools/tb precheck tb277 u2        # expect: u2 free; one FOUND item, ser2net pid 744 (standing)

# swi_d only — this session's console. NO credential is needed for u2 (factory password).
tools/tb probe tb277 --consoles u2 --no-prompt --pdu 10.36.230.212 --outlet u2=1 \
    --name u2=swi_d --baud 115200
tools/tb ckcon tb277 ckcheck u2 115200 "show boot" "show stack" "show reboot history"
```

🔴 **The probe rewrites `bench-setup/tb277/bench-state.md` as a swi_d-ONLY record** when you give
it one console, dropping swi_a and swi_b from the shared file. That happened four times on
2026-10-22 and was reverted every time. **At this wrap the Test Engineer chose to keep the
three-unit version** (`Generated 2026-10-21T201917Z`), which is still accurate because nothing on
the bench changed. If you probe one console, revert the file afterwards:
`git checkout -- bench-setup/tb277/bench-state.md`.

🔴 **To open u3 or u5 you need their console password**, which is NOT in this repo and must never
be put in it. See "The credential position" below.

### Per unit, as left

| unit | console | power | state |
| --- | --- | --- | --- |
| **swi_d** (DUT, AT-x960-56YSQ, S/N `A2WQS700B`) | u2 @115200 | on | standalone, Ready, Active Master, `Stacking hardware disabled`. Build `sin_x96056-20261019-27`. Boot image `flash:/x960-tb277.rel` **(file exists)**, boot config `flash:/default.cfg` **(file exists)**, autoboot disabled. Logged out at `awplus login:` |
| swi_b (AT-x960-28YSQ, S/N `A10737A261700021`) | u3 @9600 | on | **NOT OPENED this session.** Last read 2026-10-22 wrap: `awplus_main-20261020-78`, boot image `flash:/backup.rel` |
| swi_a (AT-x950 GEN2-52XSTQm, S/N `A10713A262600012`) | u5 @9600 | on | **NOT OPENED this session.** Last read 2026-10-22 wrap: `awplus_main-20261019-73`. **Boot image `Not set` — because it NETBOOTS**, which is correct for this unit |

Host NICs: `bootnet`, `eth2`, `eth3`, `eth4` all **carrier=1**. eth2 `10.38.22.1/27`,
eth3 `10.38.22.33/27`, eth4 `10.38.22.65/27`, each with a ULA IPv6. The bench **flash-boots**, so
no TFTP path is needed for a swi_d reload.

🔴 **`/tmp` on tb277 is 96 % full** (1.9 G of 2.0 G, 93 MB free). **1.8 G of it is
`wireshark_eth4*.pcapng` belonging to someone else — NOT ours to delete.** This session's own
scratch (`/tmp/ckq1122`, `/tmp/oper1022`, `/tmp/ntp61022`, 4.2 MB) was removed at the wrap.
**Bound and filter every capture.**

### swi_d's running-config, as left

| thing | state | whose |
| --- | --- | --- |
| L3 underlay: vlan10 `10.38.22.34/27` (port1.0.10 ↔ box eth3), vlan48 `10.38.22.66/27` (port1.0.48 ↔ box eth4) | in running- **and** startup-config | campaign infrastructure — **do not remove** |
| `vlan 60` `ckMGMT-A`, `interface vlan60 10.38.22.97/27`, port1.0.2 tagged | in running- **and** startup-config | 🔴 **the Test Engineer's to remove** |
| `log facility` | `Facility: default` | restored by T33401 |
| permanent log filter | `*1 Level warnings` | restored by T33402 |
| triggers | `% No triggers currently defined` | restored by T33403 |
| `show ntp status` | completely empty (unconfigured) | restored by T44299 |

## What was accomplished

The four cases dropped from the 2026-10-21 campaign, asked for on 2026-10-22 and run by
`bench-runner` subagents in two groups under a sentinel. Queue:
`CAMPAIGN-QUEUE-2026-10-22T1122.md`.

**All four had NO authored text** — `has_objective = 0`, one 53-character empty-JSON placeholder
step each, verified against `ck.db` before dispatch. Every step was designed from the title, the
X960 TPS row and the DUT's CLI surface, and written into the working log **before** being run.

🔴 **The bracketed number in each case title is offset +2 from the TPS row number.** Title
"(265)" is TPS row **263**; TPS row 265 is "Syslog stored in NVS", a different case. **Never look
one of these cases up by its bracketed number.**

## Results — all runs CLEAN, none confounded

**Final logs created**: `/create-logs` commits `c1df03b` (ntp6) and `6413940` (oper). No `work/`
folder remains.

| group | case | verdict |
| --- | --- | --- |
| [ntp6-2026-10-22T1122](ntp6-2026-10-22T1122/README.md) | T44299 IPv6 NTP Client | **PASS** |
| [oper-2026-10-22T1122](oper-2026-10-22T1122/README.md) | T33401 Syslog Facility Override | **PASS** |
| | T33402 Syslog stored in NVS | **PASS** (step 4 PARTIAL as designed) |
| | T33403 Scripting | **PASS** |

All three oper health-after reads were tool-reported **DIRTY** and each was adjudicated **CLEAN**
with the reasoning written out in full: in every case the single new reboot entry is that case's
own permitted `reload`, which the device itself classified `Expected CLI(user request)` within a
second of the command, and every flagged line is that boot's ordinary `kern.*` start-up text.
The DUT's `show reboot history` at the wrap shows **four** new entries for 2026-10-21/22, one per
case, all `Expected`. **No unexpected reboot, in any case.**

## Findings

### Measured

- 🔥 **`log host <ip> facility <f>` is a message-SELECTION filter, not a per-destination
  override.** Accepted, shown in running-config one line below `log facility`, reads exactly like
  an override, and **never rewrites the PRI byte**. Proved negatively twice and positively once.
  `show log config` is honest — it lists it under `Filters:`. The **global** `log facility`
  command does work (25/25 + 25/25 at two destinations, 387/387 after a cold boot), so T33401 is
  a PASS and this is a clarity/capability finding, not a defect. `platforms/x960.md` §7J.1.
- 🔬 **`log permanent level <lvl>` APPENDS a filter rather than replacing the default** — the same
  filter-builder mechanism. **One mechanism in two places, so assume it for the rest of the `log`
  family.** §7J.2.
- **NVS logging is real, named down to the media**: permanent = `/flash/log/messages` on
  `/dev/mmcblk0p1` (ext3, eMMC); volatile = `/var/log/messages` on a 10240k tmpfs. The permanent
  filter defaults to level `warnings`, so a notice is **not stored at all**. §7J.2.
- **Scripting is a `.scp` file run by `activate` or a trigger; there is no scripting language, and
  no `show script` command exists.** §7J.3. **This closes `platforms/x960.md` §7F.8**, which had
  recorded that running a real script "needs a root write to the box's `/tftproot`
  (STANDING-ORDERS §4) — still unmeasured". **It needs no write to the box at all.**
- **The DUT works as an IPv6 NTP client**: four captures, 8/11/13/13 requests all paired, a
  control at zero in every window it was armed for, two real clock steps (2.241471 s and
  50.914095 s) cross-checked against the DUT's own log, silence on removal with the link proven
  live, and cold-boot persistence proved by packets rather than a `show`.
- 🔴 **swi_d has TWO power supplies, so ONE outlet cannot power-cycle it.** The cycle completes,
  the outlet reports on, uptime does not reset and no reboot-history entry appears — and **both
  PSU bays still read `Ok`**, so the PSU read does not tell you the cut failed. **Check uptime.**
  §7J.7.

### Inferred, and what would prove it

- **Nothing in this campaign rests on an inference.** Every verdict is carried by frames on the
  wire or by a filesystem read, each with a control in the same run.

## OPEN questions

1. 🔴 **Will removing `vlan 60` disturb spanning tree?** It is tagged on `port1.0.2`, the RSTP
   **root port**. Evidence path: `show spanning-tree brief` before and after `no interface vlan60`
   / `no vlan 60`, then `write`.
2. **Is T33402's abrupt-power-cut limb worth a short re-run now that it is possible?** The
   outlets are known (below), so the stronger test is no longer blocked. It is a limb-only run 2,
   about a fifth the cost of a full case.
3. **Is swi_b's build train intended?** It runs `awplus_main-20261020-78` where swi_d runs
   `sin_x96056-*`. Open since 2026-10-21 and **not** re-checked this session, because u3 was never
   opened.
4. **`tb277.static` records `swi_c` (S/N `A2WQS7004`) on `/dev/u2`, outlet 1 — the same console
   and outlet as swi_d.** It looks like a predecessor that was never removed. Two units claiming
   one outlet could mislead a future campaign. Evidence path: read the serial on u2 (it is
   `A2WQS700B`) and ask whether `A2WQS7004` is still on this bench at all.

## ✅ ANSWERED this session — swi_d's two PSUs

**Test Engineer, 2026-10-22: `10.36.230.212`, outlets 1 and 8.** Recorded as a dated comment on
swi_d's line in `bench-setup/tb277/tb277.static`; the file's `serial = name, outlet[, pdu_ip]`
format holds one outlet, so the parsed field is unchanged and the second outlet is in the comment.

The address was first given as `10.36.230.121`, a digit transposition of the recorded `.212` that
had never appeared anywhere in the repo. **It was asked, not assumed**, because the two readings
differ in consequence: on `.121` the cycle would have gone to a **different PDU's outlet 1** and
the dual-PSU explanation would have been wrong — the DUT would simply never have been cut. Both
bays reading `Ok` fits either story, so the evidence could not settle it.

🔧 **Consequence: cycling outlets 1 and 8 TOGETHER gives a true abrupt power cut on swi_d.**

## The credential position — read this before opening u3 or u5

`CK_PASSWORD_U3` / `CK_PASSWORD_U5` were **not in this session's environment**, and `tools/tb`
forwards only what is in the environment. A probe that opens u3 or u5 without them **falls back to
trying three default passwords**. **AW+ locks an account at five failed logins and every further
failure re-arms the five-minute timer**, which is how swi_b was locked on 2026-10-21. Asked how to
deliver the password, the Test Engineer chose **"DUT only — don't open u3/u5"**, and the whole
campaign ran that way at no cost: tb277 itself played every partner role.

**To open them next time**, put the password in a file only you write — `~/.ckenv`, chmod 600,
**outside the repo** — holding `export CK_PASSWORD_U3=...` and `export CK_PASSWORD_U5=...`, then
`. ~/.ckenv && tools/tb ...`. The value then never appears in argv, in a transcript or in the
repo. **It must never go on a command line**: `ps` is readable by other users on this shared box.

## Ordered next steps

1. **Push.** This session committed locally and cannot push; see the end of this file for the
   count.
2. **Remove `vlan 60`** from swi_d (`no interface vlan60` / `no vlan 60`, then `write`), and
   **re-check `show spanning-tree brief`** because it sits on the root port.
3. Decide whether to re-run **T33402's power-cut limb** now that both outlets are known.
4. Settle OPEN 3 (swi_b's build train) and OPEN 4 (the stale `swi_c` line in `tb277.static`).
5. The process reviews propose three tooling fixes, in order of value — see
   [ntp6 REVIEW.md](ntp6-2026-10-22T1122/REVIEW.md) and
   [oper REVIEW.md](oper-2026-10-22T1122/REVIEW.md).

## Recipes

**A true abrupt power cut on swi_d** (now possible):

```bash
tools/tb pdu tb277 10.36.230.212 1 off
tools/tb pdu tb277 10.36.230.212 8 off
# confirm the unit is actually down before powering back on, then:
tools/tb pdu tb277 10.36.230.212 1 on
tools/tb pdu tb277 10.36.230.212 8 on
# after ANY restart: ping the leg to 4/4 BEFORE reading it. A login prompt is not readiness.
```

**Prove a log entry is absent** (never use `| include` for this):

```bash
tools/tb awshell tb277 <scratch> u2 115200 "grep -c CKPATTERN /flash/log/messages*"
```

`show log permanent | include <pattern>` **never returns a prompt when nothing matches** — the
wait is exactly the driver timeout, long enough for the console idle-timeout to log you out.

**Decode syslog by facility** (tool added this campaign):

```bash
tools/tb capture tb277 <scratch> eth3 <secs> syslog.pcap udp port 514
python3 -I tools/syslogwire.py <pcap> --expect-facility local4
```

**A syslog capture window must be ≥170 s.** With no UDP/514 listener on tb277 every datagram
draws an ICMP port-unreachable; the DUT's syslog-ng marks the destination broken and reopens it
after **exactly 60 s**, then flushes in one burst. Three shorter windows read ZERO while the
feature worked perfectly.

## Pointers

- Topology and measured bench state: [bench-setup/tb277/bench-state.md](../../bench-setup/tb277/bench-state.md)
  (three-unit record, `Generated 2026-10-21T201917Z`).
- Names, PDU outlets and the dual-PSU note: [bench-setup/tb277/tb277.static](../../bench-setup/tb277/tb277.static).
- Platform facts measured this campaign: [platforms/x960.md](../../platforms/x960.md) **§7J**,
  plus **§7F.8** which this campaign closed.
- The campaign's own record, including every finding and the full triage answer:
  [CAMPAIGN-QUEUE-2026-10-22T1122.md](CAMPAIGN-QUEUE-2026-10-22T1122.md).
- The previous session: [SESSION-HANDOVER-2026-10-22.md](SESSION-HANDOVER-2026-10-22.md).

## The sentinel stood down at this wrap

Monitor stopped, the 15-minute cron trigger deleted, no stray `sentinel.sh` processes, heartbeat
removed. Both `bench-runner` subagents had already handed back. Nothing of this session's is left
running on tb277.
