# Group process review -- authmodes-2026-10-23T1304
tb277 / swi_d (AT-x960-56YSQ), five AWPTCM Authentication & Security cases, 2026-10-23
15:20-16:40 NZDT. All five PASS.

Reviewed 2026-10-28 by `/create-logs` from
`~/.claude/projects/-media-bidhanc-mnt-testbox-home-claude-device-testing/87016784-78a9-4107-8bc9-8db7a57a86ad/subagents/agent-a2b85027e32e3d1df.jsonl`
and the working files. The recommendations are the reviewer's; the findings cite the
transcript call or the working-file line they come from.

## Token usage

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T33369 | 4 | 8 | 14,683 | 903,812 | 64 | 4 | 162 s | 409 |
| T33374 | 1 | 2 | 2,017 | 146,190 | 24 | 1 | 0 s | 0 |
| T44277 | 5 | 10 | 14,893 | 926,644 | 80 | 5 | 171 s | 599 |
| T33362 | 3 | 6 | 15,160 | 797,183 | 48 | 3 | 161 s | 216 |
| T44279 | 7 | 14 | 21,593 | 2,180,492 | 68 | 8 | 281 s | 2,537 |
| **overhead** | **122** | **244** | **227,346** | **22,089,196** | **2,118** | **129** | **4,411 s** | **223,268** |
| **total** | **142** | **284** | **295,692** | **27,043,517** | **2,402** | **150** | **5,186 s** | **227,029** |

## 🔴 Read the table correctly: overhead is not overhead here

`case_tokens.py` opens a case segment at the first tool call that touches `<id>/` and closes it
at that case's `RESULT` line. **This group's tester did all its bench work first and wrote
`work/run1.log` last**, so for each case only the write-up, the commit and the `SendMessage`
fall inside the segment. Everything else — the console gate, the probe, the rig build, every
supplicant leg, every `show`, every health read — is pooled into `overhead`.

The proof is in the numbers. `overhead` holds **86% of the calls (122 of 142)**, **82% of the
cache read (22.1 M of 27.0 M)** and **98% of the tool output read back (223 kB of 227 kB)**.
T33374 shows **1 call and 0 s** for a case that occupied the bench for eighteen minutes.

**So no per-case row in this group may be read as a cost.** Two things follow:

1. **For the next tester:** write each case's `work/run1.log` *incrementally*, and emit the
   case's `RESULT` line before moving to the next case's first command. That alone makes the
   per-case numbers real, at no cost to the run.
2. **For the Test Engineer:** the group's true cost is the total row — about **27 M cache-read
   tokens over 150 tool calls and 86 minutes** for five cases, or roughly 5.4 M cache-read
   tokens a case.

## What actually sat in the overhead row

From the transcript's largest outputs in that segment:

| what | size | finding |
| --- | --- | --- |
| `sed -n '200,500p' CAMPAIGN-QUEUE-2026-10-23T1304.md` | 27,872 | the campaign queue was read in three slices totalling **57,920 characters** |
| `sed -n '500,760p' ...` | 15,725 | |
| `sed -n '1,200p' ...` | 14,323 | |
| `sed -n '694,760p;964,1010p;1034,1065p' tools/README.md` | 10,631 | `tools/README.md` was read in two passes totalling **20,583 characters** |
| `sed -n '20,110p' tools/README.md` + `sed -n '1546,1596p'` | 9,952 | |

**That is 78.5 kB of repository prose, about 35% of all tool output the whole group read back,
pulled in before the first command reached the DUT.** Both files were read in slices rather
than whole, which was the right instinct; the problem is that the dispatch did not say which
slices were needed, so the tester found them by reading around.

Two further costs that belong to the group and not to any case:
- The console gate and `bench_probe.py --read-only` run, plus the `git checkout --` that
  restored `bench-setup/tb277/bench-state.md` afterwards.
- 🔴 **The group's dispatch omitted the console baud rate.** The campaign queue's `## Issues`
  section records the same omission costing another group 85 seconds of apparent dead console.
  u2 is **115200**. A dispatch template that always carries box, console, **baud**, PDU and
  names removes this class of loss entirely.

**Recommendation.** The dispatch should carry, inline, the five or six facts a tester needs to
start: console and baud, the host NIC and the port it faces, the rig one-liner (the DUT is its
own RADIUS server, NAS 127.0.0.1, users `ckmulti1 ckmulti2 ckpeap cktls`), the named `tools/`
helpers with their exact arguments, and the pointer to `logged-output.md` §4 rather than the
whole queue. The queue stays the resume point; it does not have to be the briefing.

## Findings that recur across all five cases

Said once here rather than five times.

### 1. One rig, one `show system`, five cases, zero configuration drift
All five cases ran on one inherited rig: the DUT is both the 802.1X authenticator and the
RADIUS server (`radius-server local`, NAS 127.0.0.1, users `ckmulti1 ckmulti2 ckpeap cktls`),
the supplicant is tb277 on `eth4` facing `port1.0.48` in vlan 48, and no partner switch is used.
`show system` was taken once for the group at 02:18:41 UTC and the DUT did not reboot during the
group (every case's health read confirms it), so one capture is correct for all five.

Each case restored itself and captured `show running-config` as its own `swi_d.cfg`. **All five
captures are byte-identical below their per-case comment header** — the tester verified this
with an explicit `diff <(tail -n +6 ...) <(tail -n +5 ...)` at each hand-over. That is a strong
result: five cases that created and removed VLANs, L3 addresses, RADIUS groups, RADIUS users,
method lists, a web server address and nine port-level commands left the device exactly as
found. It is campaign bookkeeping, so it is recorded here and deliberately kept out of the final
logs.

### 2. 🔥 Four commands in this group silently discard a setting the operator entered
This is the group's most valuable product output, and no single case shows the pattern.

| command | what is silently lost | where measured |
| --- | --- | --- |
| `auth host-mode multi-supplicant` | `dot1x control-direction both` is rewritten to `in` | T33362 (and twice earlier in the campaign) |
| `auth-mac enable` | `dot1x control-direction both` is **deleted** from the running-config | T33369 |
| `auth supplicant-mac <MAC> <param>` | the previous per-MAC parameter is replaced | T44277 |
| `auth dynamic-vlan-creation rule ...` | `type multi` is replaced, and the port reverts to single dynamic VLAN | T33362 |

In every case there is no warning, no `% ` line and no log entry, and in every case the
replacement is a **weakening** — a narrower control direction, an unreachable parameter
combination, or a port that no longer does what the feature was enabled for. The same shape as
the known `spanning-tree mode` behaviour (memory `stp-mode-change-reenables-spanning-tree`).

T33369's instance is the sharpest, and is worth putting in front of a developer on its own: the
product **has** a correct, specific error message for the `auth-mac` / `control-direction`
conflict, and prints it only when the commands are given in the less natural order. Give them in
the natural order and the setting is deleted in silence.

🟢 **The contrast case is in the same group.** `auth-web enable` (T44279) adds
`auth forward arp`, `auth forward dhcp` and `auth forward dns` — what the feature needs — and
shows them in the running-config. So the product can do this well; four commands do not.

### 3. The method that made the group work
Three habits appear in all five cases and should be the default for the next authentication run:
- **`dot1x initialize interface port1.0.48` before every leg.** Inherited from the earlier
  group, where it removed a superseded-EAP-session anomaly. No leg in this group hit it.
- **A read-only `qmark` help probe before anything is sent.** In T44277 the help text revealed
  that the feature is a per-MAC parameter override and not a pre-authorisation, which is the
  case's whole result. In T33362 it revealed that the local RADIUS server carries a VLAN by
  group and not by user, which is the rig design. Both would have cost a wrong test otherwise.
- **An instrument control in the same configuration.** Every zero in these logs is licensed by
  the same instrument returning a non-zero somewhere else (memory
  `tcpdump-nfs-root-squash-capture`). T33362's fifth S0 leg does this for the whole case.

### 4. A probe that stops discriminating, and only one case noticed
Four cases probe the dataplane with a crafted ARP request. T44279 enables `auth-web`, which
auto-adds `auth forward arp`, and **an ARP probe then passes for unauthenticated clients too**.
The tester caught it and switched that case to ICMP echo. Had it not, the case would have
reported four false positives. **Rule for the next run: whenever `auth forward <protocol>` is in
force, the dataplane probe must use a protocol that is not in the forward list.**

### 5. Deliberate and identical gap in all five cases
None of the five proved that its configuration survives a reboot. Each log says so in its
CAVEAT. The reason is one group-level decision, and it was the right one: proving persistence
needs `write`, and the group's restore contract keeps `startup-config` at `flash:/default.cfg`
**so that a reload is itself a complete restore of the inherited rig** for the groups that
follow. Each case proved instead that its lines appear in and disappear from
`show running-config`.

**Recommendation.** Persistence across a reboot is a real part of "satisfactory level of
testing" (memory `satisfactory-level-of-testing`). Schedule it as **one** short case at the end
of a campaign, not per case: write the rig, reload, read back, restore. One reboot covers every
feature the campaign touched.

## The three biggest savings for the next run

1. **Brief the tester instead of making it read the campaign.** 78.5 kB of queue and
   `tools/README.md` prose — 35% of everything this group read back — was consumed before the
   first command reached the DUT. A dispatch carrying console **and baud**, the host NIC and
   port, the rig one-liner, the named helpers with their arguments, and a pointer to
   `logged-output.md` §4 would remove most of it.
2. **Build `tools/arpmatrix.py`.** Three cases hand-built the same thing: T44277 eight
   `arpleg.py` legs, T33362 eleven across two targets, T44279 six over ICMP. Proposed arguments:
   `--iface --targets <ip>[,...] --pairs <mac>:<sender-ip>[,...] --count N --icmp --gw-mac --tag`.
   It runs the cross product in one invocation and prints the reply-count matrix, which in
   T33362 *is* the result. One helper, three cases, and the matrix stops being assembled by
   hand.
3. **Emit each case's `RESULT` line before starting the next case**, and write `work/run1.log`
   as the case goes rather than at its end. Costs nothing, and it is the only way the per-case
   token measurement this review is built on becomes true. Until then, 82% of the cost of every
   authentication group will keep landing in one `overhead` row where nobody can act on it.
