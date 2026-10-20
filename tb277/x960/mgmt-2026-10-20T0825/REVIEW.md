# Group process review -- mgmt-2026-10-20T0825

Reviewed 2026-10-20 by /create-logs from the tester's transcript and the working files.

## Token usage

| segment | calls | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T33378 | 37 | 56,140 | 6,736,767 | 21,072 | 37 | 712 s | 21,477 |
| T47199 | 6 | 29,096 | 1,597,112 | 20,387 | 6 | 366 s | 5,179 |
| T33416 | 16 | 37,722 | 5,436,375 | 20,155 | 16 | 491 s | 11,548 |
| overhead | 103 | 210,610 | **21,161,018** | 16,136 | 115 | 2,395 s | 251,909 |
| **total** | **162** | **333,568** | **34,931,272** | **77,750** | **174** | **3,964 s** | **290,113** |

## 🔴 Group overhead: 60.6 % — this group spent more context outside its cases than inside them

21.2 M of 34.9 M cache-read went on overhead, against 7.7 % for `aaa`, 8.4 % for `snmpmon` and
12.1 % for `tacacs`. These are the three **cheapest** cases in the campaign (T47199 at 1.6 M is
the cheapest of all thirteen), so the cause is not hard cases.

**The cause is the call count, not any single read.** 103 overhead calls against 59 case calls.
Each call carries the whole accumulated context, so 103 cheap calls cost more than a handful of
large ones. The five largest overhead reads were the rules and reference corpus —
`TESTBOX-ACCESS.md` (16,236 chars), `tools/README.md` (14,252), `logged-output.md` (13,857),
the `orient-dt` skill (13,570) — plus one 20,654-character health-log read that landed in
overhead rather than in a case.

**What to do differently.** Read the rules corpus in **one** call with a combined `sed`
expression, not in a dozen. This group already used that form for some reads
(`sed -n '47,71p;72,280p' logged-output.md`); it needed to use it for all of them. The group
brief should also carry the facts the tester otherwise goes looking for, so `TESTBOX-ACCESS.md`
and the skill files do not have to be opened at all.

## Findings that apply to the whole group

1. **`show cpu` on this platform never prints an idle percentage.** The `HEALTH:` template asks
   for `idle <n>% before -> <n>% after`. The x960 prints load instead:
   `CPU averages: 1 second: 0%, 20 seconds: 0%, 60 seconds: 0%`. All three cases recorded the
   load and said so, which is right. **The template asks for a number this platform does not
   produce**, and every x960 case will hit it. The health-read instructions in
   `logged-output.md` §2 and the §4 template should accept load where idle is not printed.
2. **Two partner configs were never captured** — `T47199/swi_b.cfg` and `T33416/swi_b.cfg`.
   swi_b is in both topologies: the cross-unit control in T47199, and the far end of the
   flapped ports in T33416. `logged-output.md` §2 wants one `.cfg` per device the case uses.
3. **`tools/netlogin.py` was edited three times inside T33378's own segment.** Building a tool
   mid-case mixes instrument development with measurement. It also means the earlier steps of
   that case ran on a different instrument than the later ones.
4. **T47199 cost 6 tool calls and produced a FAIL.** A cheap case is not a shallow one: the
   verdict rests on 6 logins with 0 warnings, a `banner exec` marker proving the instruments
   see a message at that position, and a RestCONF cross-check. Worth remembering when a case
   looks too cheap to be trusted.

## Next run

- One combined read for the rules corpus, or put the facts in the brief.
- Capture a `.cfg` for every device named in the topology, not only the DUT.
- Finish instrument changes before step 1.
