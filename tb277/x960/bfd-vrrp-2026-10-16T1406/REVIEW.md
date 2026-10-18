# bfd-vrrp-2026-10-16T1406 -- process review
Reviewed 2026-10-19 by /create-logs from `a0fe415a0d5fbb48a.output` and the working files.
Per-case reviews are in each case folder as `<id>-review.md`.

## Token usage

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T47201 | 97 | 194 | 140,408 | 16,869,029 | 1,986 | 114 | 40m 45s | 83,570 |
| T47873 | 66 | 132 | 417,709 | 18,660,280 | 560 | 67 | 40m 56s | 31,694 |
| **overhead** | 16 | 32 | 79,366 | 2,964,555 | 184 | 25 | 2m 28s | 133,391 |
| **total** | **179** | **358** | **637,483** | **38,493,864** | **2,730** | **206** | **1h 24m 09s** | **248,655** |

Campaign-wide: **10 cases, 599 calls, 126.0 M cache-read**, of which **9% is group overhead**.
That 9% is the headline number of the whole campaign: the 2026-10-15 run measured **46%**, so
the overhead share fell by a factor of five. Whatever was changed between those two campaigns is
the most valuable process change anyone has made here, and it should not be quietly undone.

**This group ran last and most expensively.** Two cases account for **30.5%** of the campaign's
cache-read (38.5 M of 126.0 M) and **30%** of its API calls, and T47873 (18.7 M) and T47201
(16.9 M) are the campaign's two most expensive cases. Almost none of that is this group's own
behaviour -- see finding 1.

### This group's own overhead
16 calls, 2.96 M cache-read, **2m 28s of wall**, and **133,391 characters of tool output -- 54%
of everything this group read back, in 12% of its tool calls.** The overhead segment here is
almost entirely the up-front read of the dispatch: the campaign queue in two ranged reads
(13,148 + 10,590 chars), `tools/README.md` in two more (12,837 + 11,057) and `platforms/x960.md`
(11,709). Averaged, an overhead call pulls **5,336 chars** against T47201's 733 and T47873's 473.

Two things follow:
- **Reading the dispatch is now the single densest block of text in a group**, and it is cheap
  only because it happens first, while the prefix is small. That is the right place for it. The
  improvement to make is not "read less" but "read each file once": `tools/README.md` and the
  campaign queue were each opened in **two separate ranged reads** (47.6 k chars across four
  calls). One merged range per file would cost the same tokens in half the calls and avoid the
  risk of a range that misses the section that mattered.
- The **9% overhead figure understates the true shared cost of this group**, because the group's
  shared preparation was done *inside* T47201 -- the VRRP guide WebFetch, six reads of its
  extract, and the `arpleg.py` extension (see finding 2).

## Findings that recur across this group (said once here)

1. **Cost in a group is positional before it is behavioural.** T47873 has the campaign's highest
   cache-read and simultaneously its **lowest read-back-per-call (473 chars) and near-lowest
   output (560 tokens)**. It is not an expensive case; it is a cheap case standing at the end of
   a long group, where every call carries the whole accumulated prefix. **Never judge a case
   against cases in other positions.** The corollary is operational: put the long, token-light
   observation limbs late and the reading and instrument-building early, which is exactly what
   this group did.

2. **An idle gap longer than the prompt cache's lifetime re-writes the entire context, and it is
   the most expensive single event in this group.** One call in T47873, at 06:33:21, has
   `cache_read = 0` and `cache_write = 327,405` -- a total miss, after a **339-second gap** with
   no API call. That one call is **78% of T47873's cache write and 51% of the group's**. It is
   not new material: it is ~327 k tokens being paid for a second time. The later in a group it
   happens, the worse it is. **Proposed fix, and the highest-value change this group suggests:
   a `tools/keepwarm.py` (or a ticking `tb waitfor`) that polls a long wait in sub-cache-lifetime
   chunks** so an API call lands every couple of minutes. This applies to every reload, every
   long capture and every convergence timer in every campaign.

   It also corrects a plausible but wrong reading of the same number. T47873's 417,709 cache
   write is 3-10x every other case, which looks like "the last case pulled in a lot of new
   context, including the VRRP Feature Overview guide". **The guide is not in T47873's segment.**
   The WebFetch is tool call **38, at 05:17:26**, which `case_tokens.py` bills to **T47201**.

3. **A group's shared preparation lands in whichever case is open, and distorts both.** T47201's
   four largest reads -- the VRRP guide extract (4,838 + 3,890 + 3,707 chars) and `tools/arpleg.py`
   (4,077) -- are T47873's authority and T47873's instrument. Front-loading them was the right
   call and is why T47873 ran so lean. But the measurement cannot see it, so **T47201 is
   over-charged, T47873 is under-charged, and the group's "overhead" row misses the group's real
   shared cost.** When a `/create-logs` reviewer compares two cases in one group, check what the
   first case was carrying for the second before concluding anything about either.

4. **Proving an absence costs more than proving a presence.** T47201 is UNSUPPORTED and it is the
   campaign's high-water mark for **output tokens (1,986) and tool calls (114)**. That inverts
   the natural expectation that a case with nothing to configure is cheap, and the next tester
   should plan for it. The method is what costs, and the method is the reusable part:
   **to call something UNSUPPORTED, enumerate the surface with the daemon up and produce a
   positive contrast on the same box.** In T47201 that meant five CLI probes taken with **both
   daemons already running** (bfdd pid 4391, ripd pid 4416, so it is neither the service gate nor
   a licence), a vendor guide with **0 occurrences of "bfd" in 1045 lines**, and
   **`ip ospf bfd` accepted on the same interface in the same minute** -- which proves the
   capability exists in the image and is simply not wired to RIP. An UNSUPPORTED verdict without
   the daemon-up precondition and the positive contrast is an untested assumption.

5. **A decoder's complaint is a hypothesis; the peer's own behaviour is the measurement.** This
   group's worst two readings both came from the sentinel and both had to be corrected mid-case.
   First it called `tcpdump`'s `bad vrrp cksum` an instrument artefact; the tester's own A/B --
   **one capture, one decoder, one window**, with `alternate-checksum-mode` on the DUT only --
   disproved it, because an artefact cannot be selective between two routers in the same capture.
   Then the sentinel over-corrected to "the default is non-conformant", which rests on the
   validator being right. **The tester's final F-17 wording is the accurate one**: two components
   of one firmware image disagree about the checksum of its own default VRRPv3 advertisement, and
   the vendor ships a command that makes them agree. **It does not say which mode is
   RFC-conformant, and nobody should read that in.**

6. **The sentinel's "NOT MEASURABLE on this bench" was also wrong, and the technique that
   disproved it is reusable.** The third-party-peer interop limb was declared unmeasurable for
   want of a conformant peer. Enabling `alternate-checksum-mode` on **one side only** produced a
   real dual-master: priority 100 displacing priority 150, both routers advertising for vrid 10
   from the same virtual MAC `00:00:5e:00:01:0a`, and **ten ARP replies to five requests**.
   **When a feature ships a compatibility mode, the mismatch between its two settings simulates a
   conformant and a non-conformant peer on one bench, for free.** Bounded by two controls:
   default-to-default is fine and alternate-to-alternate is fine, so it is the mismatch that
   breaks the pair, not either mode. What stays genuinely unmeasured is narrower than the claim:
   whether a *third-party* conformant router would reject the default frames.
   **Taken with finding 5: a verdict from the sentinel is a reading, not a result. Both of these
   were corrected by the tester at the bench, which is the authority order working as intended
   (memory `grading-authority-tier-list`) -- but only because the tester re-measured instead of
   accepting.**

7. **Three CLI traps in this group all have the same shape: a command that looks accepted and
   silently truncates the rest of a `cfg.py` batch.** Each is written up in the campaign queue
   with its reproduction.
   - **O-34** -- `no service bfd` **drops the console out of configuration mode** with nothing
     sent in between (`awplus(config)#` -> `awplus#`), so the following `end` fails with
     `% Invalid input detected at '^' marker.` Reproduced on both devices, twice each.
     **It must go LAST in any stop-on-error batch.**
   - **O-37** -- `circuit-failover` and `transition-mode` are **refused while the VRRP session is
     enabled**: `% You must disable this session first`. The guide does not mention the ordering.
     The **`disable` -> change -> `enable` wrapper is mandatory**; `priority`, `virtual-ip` and
     `preempt-mode` do not need it.
   - **O-40** -- `no interface vlanN` was **refused on swi_b** (`% Removal of interface not
     allowed`) although it had succeeded on swi_a earlier in the campaign. Once the SVI has no
     address and no member ports there is nothing to remove. **The reliable removal is
     `no ip address` on the SVI, then delete the VLAN from the vlan database
     (`vlan database` / `no vlan N`).** The tester hit this against its own committed restore
     recipe and corrected the recipe. A restore must **gate on the output**, not assume either
     behaviour.
   See also memory `bench-scripts-stop-on-cli-errors`.

8. **O-33 shapes how BFD can be measured at all: a BFD state change writes NOTHING to the device
   log.** `show log | include bfd` and `| include BFD` across four measured up/down transitions
   returned only IMISH command echoes. There is no audit trail of a BFD failure on this platform.
   The only instrument is **polling `show bfd peer`**, whose `Uptime:` / `Downtime:` field is
   1-second resolution and is **lost the moment the session re-establishes**. So the next tester
   must **arm the poll before the stimulus and take an epoch stamp immediately before it** (as
   T47201 did at call 89); a transition that is missed cannot be recovered afterwards. Every BFD
   timing in T47201 carries a `~` for that reason.

9. **Two generic `tools/arpleg.py` extensions shipped here, and both were self-tested in a live
   leg before any verdict rested on them.**
   - **`--udp DST[:PORT][@SRC]%L2DST`** -- a per-spec Ethernet destination. `--l2-dst` applies to
     every spec and therefore cannot carry a subject and a control that differ **only** in their
     link-layer address, which is exactly what a first-hop-redundancy case needs.
   - **`--show-ttl`** -- appends the received IPv4 TTL to each flow. The TTL is the only field on
     the wire that says **how many routers forwarded** a frame, so **when two routers answer from
     the same virtual MAC, the hop count is the only thing that attributes a forwarded frame to
     one of them.** It is what graded T47873's role transition, 63 -> 62 -> 63. Off by default.
   - Together they enable the pattern the whole VRRP case rests on: **subject, control and
     instrument as three flows to one IP destination, differing only in L2 destination, counted
     in one capture.** They were proven in STEP 0 of T47873, with the feature off, before a single
     verdict depended on them -- copy that ordering.

10. **What the final logs deliberately leave out, recorded here because the next reader will
    notice.** Per logged-output.md "Out":
    - **`swi_a` is dropped from both TOPOLOGY AS TESTED blocks.** It survives only in the session
      facts line (`u5 = swi_a`), because neither case carried traffic on it and it has no `.cfg`.
      A link a case never used is noise in the diagram.
    - **Teardown and the O-24 sticky-`no service` material are excluded** from both final logs.
      They are in `work/run1.log` and in the campaign queue (O-24 is group C's, re-confirmed by
      T47873's teardown producing both halves).
    - **Both `.cfg` pairs carry a PROVENANCE header, and the two differ.** T47873's was captured
      after the failover and reboot limbs with the configuration first returned to the setup
      state and `show vrrp brief` confirming the election. **T47201's is a reconstruction**: the
      capture point before step 1 was missed, so the setup was re-applied verbatim afterwards,
      with the BFD session confirmed `up` and both RIP routes installed at the moment of capture.
      **Fix for the next run: capture `show running-config` per device immediately after setup
      and before STEP 1, as its own numbered artefact.**

---
Recommendations are the reviewer's; findings cite the transcript call or working file they come from. A review never changes a verdict: a doubt about one goes to the Test Engineer.
