# mcast-2026-10-16T1406 -- process review
Reviewed 2026-10-19 by /create-logs from `a81d52aff45c3f339.output` (the group-C tester's
transcript) and the working files.
Per-case reviews are in each case folder as `<id>-review.md`.

## Token usage

| case | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T43863 | 73 | 146 | 111,702 | 13,395,700 | 789 | 78 | 41m 06s | 38,714 |
| T43864 | 37 | 74 | 41,131 | 9,864,930 | 414 | 37 | 20m 07s | 12,922 |
| T43865 | 29 | 58 | 34,337 | 8,970,149 | 275 | 29 | 21m 10s | 11,737 |
| T43866 | 39 | 78 | 42,417 | 14,110,604 | 367 | 39 | 29m 13s | 15,186 |
| **overhead** | 20 | 40 | 97,617 | 2,381,453 | 218 | 32 | 5m 35s | 146,863 |
| **total** | **198** | **396** | **327,204** | **48,722,836** | **2,063** | **215** | **1h 57m 11s** | **225,422** |

Campaign-wide: **599 calls, 126.0 M cache-read**, of which **9% is group overhead** rather than
case work. The 2026-10-15 campaign on this same bench ran **46%**, so the discipline added since
(one shared underlay per group, the setup recipe written once into the queue, per-section reads
instead of whole-file reads) is worth roughly a third of a campaign's context. This group is
**38.7% of the campaign's cache-read** in four of its ten cases, which is the right shape for the
group the queue called "the hardest".

### This group's own overhead
32 tool calls, 2.38 M cache-read -- **4.9% of this group's own total**, the lowest-overhead group
of the campaign. But it read back **146,863 characters of tool output, the most of any group**,
and that number is where the next saving is:

- **61,687 chars -- 42% of the whole overhead segment -- is four `sed` slices of
  `CAMPAIGN-QUEUE-2026-10-16T1406.md`** (lines 45-180, 287-560, 558-700, 700-900; 12.5k, 16.4k,
  12.4k and 20.4k chars). The queue is the right thing to read and the slicing was deliberate, but
  the fourth slice overlaps the third by three lines and the group read essentially the whole
  1,400-line file. **A queue should carry a `## Group <X>` section that a tester can read alone**;
  at this size the group brief is being reconstructed from a campaign-wide document every time.
- **22,201 chars is `tools/README.md`** in two slices (lines 20-200, then 393-445 + 497-600). The
  second slice was needed (it is the `arpleg.py` / `igmp.py` entries this group had to extend);
  the first is the catalogue, and `grep -n '^### ' tools/README.md` had already been run one call
  earlier. **Read the index, then only the entries named.**
- **12,664 chars is the previous group's T44182 working log + a directory listing of it**, read to
  learn the reload/boot-config recipe and the `tb` action names. That recipe is reusable and
  should not be recovered by reading someone else's case: see "proposed scripts" below.
- The rest is `logged-output.md` §1-2 (8.1k), `platforms/x960.md` §7.10 + §7B.6-7B.7 (7.8k),
  `STANDING-ORDERS.md` §7 (5.7k), `tools/tb --help` (5.6k) and the gate/probe output (4.4k).
  All of those are correctly scoped reads.

The overhead's 2.38 M cache-read against 146.9 kB read back is the cheap end of the session: 32
calls at ~74k cache-read each, against ~362k per call by T43866. **Everything that can be read
should be read here, not later.**

## Findings that recur across this group (said once here)

1. **Cost per call rises 2.1x through a group, and that is the single most actionable number in
   this review.** Cache-read per tool call: T43863 **171,740**, T43864 **266,620**, T43865
   **309,315**, T43866 **361,810**. **T43866 cost more cache-read than T43863 -- 14.1 M against
   13.4 M -- on half the tool calls, 39 against 78.** Nothing about T43866 is twice as expensive
   as T43863 in itself; it is simply later.
   *Stated so the comparison is honest:* a segment runs to its `RESULT` line, so the group's whole
   end-of-group teardown and hand-back (the clearing reload, the underlay restore for group D, the
   closing probe, the final three-device diffs, the logouts) falls inside T43866 -- about 12 of its
   39 calls. The per-call figure is unaffected, being a property of position rather than purpose,
   and the curve is monotonic across all four cases, so the finding holds.
   Consequences for the next campaign, in order of value:
   - **Front-load every read.** Specs, platform sections, `tools/README.md` entries, the queue and
     the CLI surface probes belong in the overhead segment or in case 1, where a call costs ~74k
     instead of ~362k.
   - **Order a group's cases cheapest-reading last.** A case whose work is mostly long observation
     legs (T43866: seven arpleg legs, one reload) costs tool *time*; a case that needs to read
     files costs *context*. Put the reading-heavy case first.
   - **Judge a case's cost against its position, never against another group's case.** T43863 is
     not "the expensive one" -- it is the one that paid for the bench.
2. **The first case of a group pays for the group, and here it also paid for the toolchain.**
   T43863's 78 tool calls include the whole two-router underlay build (calls 32-51: VLAN 61, the
   trunk, moving the receiver SVI to swi_a, STP priority, two shut ports, the static routes),
   the licence probe that chose the partner, **two `tools/console.py` fixes, one `tools/arpleg.py`
   extension and the creation of `tools/igmp.py` from nothing**. Only about half of that segment
   is T43863 the test case. The next three cases inherited a built bench and a working instrument
   and cost 37, 29 and 39 calls.
3. **Four generic tool improvements shipped from this group. Each one is a saving the next tester
   gets for free, and each should be checked for rather than rediscovered:**
   - **`tools/console.py` prompt-splice fix** (O-23). AW+ **switch-driver** port-state messages
     (`switch: port 14(port1.0.14) entered disabled state`, `vlan61: entered allmulticast mode`)
     are written straight to the console by the driver, so neither `terminal no monitor` nor
     `no log console` suppresses them, and one can land *inside* the prompt, leaving `)#` alone on
     a line. Before the fix every such command ran to its **full 25 s timeout** and `cfg.py` then
     abandoned the rest of the batch -- measured at **90 s per `shutdown`/`no shutdown`** plus a
     silently truncated batch. `PROMPT_ANYWHERE_RE` now also matches a bare `)#` (a general fix
     needing no message list) and `unsplice()` strips the known forms from a copy of the buffer.
     **Saves ~90 s and one silent truncation per port-state command; the group used eight.**
   - **Three `console.py` `ADVISORY` entries**: `All IP addresses configured on interface…`
     (the `ip vrf forwarding` / `no ip vrf forwarding` side effect, both wordings) and
     `Save the config and restart for this change to take effect` (`no service <proto>`,
     `no ip vrf <name>`). Without them `cfg.py` treats the `% ` line as a rejection and **abandons
     every command after it** -- which in T43866 is the entire VRF setup batch and the entire
     teardown batch. **Saves one silently-truncated batch per VRF move and per service removal.**
   - **`tools/arpleg.py` multicast link-layer derivation** (RFC 1112 §6.4): an IPv4 multicast
     `--udp` destination now derives `01:00:5e:` + its low 23 bits unless `--l2-dst` overrides.
     **This is what makes one leg able to carry the subject group AND a never-joined control
     group, each correctly addressed** -- the structure every count in all four logs rests on. A
     single `--l2-dst` cannot give it. An explicit `--l2-dst` still wins, so a deliberately
     mismatched L2 address stays testable.
   - **`tools/igmp.py` IGMPv3 mode** (`-3`, `--source A[,B]`, `--record {is-include|is-exclude|
     to-include|to-exclude|allow|block}`). PIM-SSM is *defined* by the (S,G) join and IGMPv2
     cannot carry a source list, so **T43865 could not have been graded at all without it**.
     Defaults are right for SSM work: `to-include` on join, and `to-include` with an empty source
     list on leave (how IGMPv3 leaves an include-mode group). Reports go to 224.0.0.22.
4. **The bench identity was re-typed into roughly 41 `arpleg` legs and 29 `igmp` calls.**
   `--icmp 10.38.22.65 --gw-mac e0:1a:ea:d4:70:43 --sender-ip 10.38.22.40 --sender-mac
   00:11:22:33:44:01` appears ~35 times verbatim; `10.38.22.70 00:11:22:33:44:77` ~29 times. That
   is ~6 kB of command text sent and echoed for no information. **Proposed: a bench profile** --
   `tools/arpleg.py --profile tb277-mcast` reading `bench-setup/tb277/profiles/mcast.json`
   (`gw_mac`, `sender_ip`, `sender_mac`, `icmp`, `iface`, `watch`), with any flag still
   overriding. Same `--profile` for `igmp.py` (`src_ip`, `src_mac`, `iface`). It also removes a
   real accuracy risk: one mistyped MAC in one leg is a false zero.
5. **The reload / persistence limb was rebuilt by hand four times** -- `copy running-config
   flash:/ck<id>.cfg` → `boot config-file flash:/ck<id>.cfg` → `show boot` → `ckreload … 480` →
   `show boot` → re-read STP until `port1.0.48` is Forwarding → measure → `boot config-file
   flash:/default.cfg` → `ckyn delete` → `show boot` + `dir flash:/*.cfg`. Eleven steps, four
   times, identical but for the filename, and the group spent one overhead call reading another
   group's working log to recover the recipe. **Proposed: `tools/bootcfgtest.py <box> <scratch>
   <uN> <baud> --tag ck43863 --wait-stp port1.0.48 --timeout 480`**, doing stage → reload → wait
   for login → poll `show spanning-tree brief` until the named port reads Forwarding → return →
   and a `--restore` mode for the pointer-back and delete. The STP poll is the part worth
   automating: **the 17-21 s post-reload Discarding window produced a near-miss in three of the
   four cases** and only the re-read saved them.
6. **Every zero in this group is backed by a non-zero from the same instrument in the same leg,
   and that discipline is why the group has no retracted findings.** Three different controls were
   used and all three are worth keeping: a **never-joined control group** in the same leg (proves
   the forwarding is selective), a **routed ICMP instrument control** that must always arrive
   (proves the capture and the two-router path are alive -- it arrived at full count in 9 legs of
   T43863, 11 of T43864, 10 of T43865), and, where VRF isolation makes an arriving flow impossible
   by construction, **the DUT's own PIM hello on the far segment** (T43866). The third is the
   interesting one: *an isolation case is a case whose result IS a zero*, and the tester found a
   liveness proof that survives the isolation instead of weakening the claim.
7. **F-13 and its addendum are a method trap, not only a product finding, and they belong in every
   future multicast run's setup order.** F-13: `ip pim sparse-mode` does NOT enable router-side
   IGMP; snooping holds the membership, `show ip igmp groups` lists it with a live timer, and
   `show ip pim sparse-mode local-members` is empty. The addendum (T43864) is the part that will
   catch the next tester: **a membership learned while the interface was snoop-only does not
   migrate when `ip igmp` is enabled later -- it must be re-sent.** T43864 applied F-13's lesson
   in its own setup and was *still* caught, because its baseline join preceded the `ip igmp` line
   by ~45 s. The ordering rule is therefore: **`ip igmp` on the receiver SVI before the first
   join, and after any `ip igmp` or VRF-membership change, re-join every group.** T43866 shows the
   same shape for a VRF move.
8. **O-26 -- the capture filter.** Any capture on a switched VLAN of this DUT competes with a 1 Hz
   loop-protection LDF stream (`loop-protection loop-detect ldf-interval 1 fast-block` is in the
   baseline). Those are 802.3/LLC `Null Unnumbered, test` frames with **no IP header**, so a short
   `-c` budget is consumed in under half a minute. It cost one capture in T43864. Use
   **`tcpdump -i vlanN -c 30 -nn ip`** -- a bare `ip` qualifier drops every LDF frame while keeping
   PIM, IGMP and the multicast data -- or `'proto 103 or net 239.0.0.0/8'` when only those matter.
   `proto 103` alone is wrong whenever the data flood is the subject.
9. **The sentinel is a source of accuracy risk as well as rescue, and this group has one of each.**
   The wrong diagnosis at 16:39:48 and its cost are written up in `T43863/T43863-review.md`; the
   LDF filter message at 17:06:57 is O-26 and saved a second retry. **Both are "a fact plus a
   suggestion" from a reader of a console feed, and the tester's own read is the authority**
   (grading authority tier list: sentinel outranks a sub-agent, but a device read outranks both).
   The standing rule the episode produces: *read the global group-to-RP mapping from
   `show ip pim sparse-mode rp mapping`, never from an (S,G,rpt) row's `RP:` field.*
10. **`platforms/x960.md` has no multicast section.** It has §7 (unicast), §7A (IGPs), §7B (BGP and
    VRF-Lite), §7C (BFD and VRRP) -- and every measured multicast fact from this group lives only
    in the queue's findings list and in these four logs. **A `§7D. IPv4 multicast -- PIM-SM,
    PIM-DM, PIM-SSM and multicast VRF-Lite, measured 2026-10-16` would save the next multicast
    tester the whole of T43863's design phase.** The expected-value tables in the four
    `<id>-review.md` files are its content.

## Next run: references (group-wide)
- **`platforms/x960.md` §7.10** -- single-instance RSTP. A root bridge never blocks its own ports,
  so the blocking decision moves to the partner and the DUT's own `show spanning-tree brief`
  cannot see it. **Read STP from both ends before measuring**, every time.
- **`platforms/x960.md` §7A.1 / §7A.2** -- the `service <proto>` gate and the sticky
  `no service <proto>` line. §7A.2's discriminator, confirmed twice here (O-24), is **the boot,
  not the daemon**: a unit that booted with the service keeps the `no service` line, a unit that
  never rebooted keeps nothing.
- **`platforms/x960.md` §7B.6-7B.7** -- VRF-Lite on the unicast path, which is the baseline
  T43866 tested the multicast path against. F-9 lives there; T43866 answers it for multicast.
- **`tools/README.md`** entries for `arpleg.py` (multicast L2 derivation, the `--udp DST:PORT@SRC`
  per-spec source override) and `igmp.py` (the `-3` section, and the 🔴 note pointing at F-13).
  Both were written by this group for the next one.
- **O-20 is the triage-method lesson of the whole campaign.** `service ?` lists `pim`, `pdm` and
  `pim6` **identically on a unit that cannot run any of them**, and the feature's own refusal
  (`% PIM-SM protocol daemon is not running or feature license is not available`) names two causes
  at once. **No read-only surface probe can settle licensing.** Only sending `service <x>` alone
  does: `% Service is not currently licensed on this platform`, one line, naming only the licence,
  leaving no config behind. It cost this group its partner-selection decision and two rounds of
  campaign-level reasoning. It is a **RUN-mode** action, not a TRIAGE one, because it is a device
  state change -- which is exactly why triage could not close it and the group had to.

---
Recommendations are the reviewer's; findings cite the transcript segment or working file they come from. A review never changes a verdict: a doubt about one goes to the Test Engineer.
