# T47873 process review -- bfd-vrrp-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `a0fe415a0d5fbb48a.output` and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 66 | 132 | 417,709 | 18,660,280 | 560 | 67 | 40m 56s | 31,694 |

**The most expensive case of the campaign to read, and the leanest one to run.** 18.7 M
cache-read is the highest of all ten cases, but 560 output tokens and 31,694 chars of tool
output read back are both near the bottom, and 67 tool calls produced a nine-step PASS with
every claim graded on the wire. The cost is **positional, not behavioural**: this ran last, so
every one of its 66 API calls carried the whole accumulated prefix of the group. Judged per
unit of work it is the cheapest case here.

### The 417,709 cache write -- what it actually was
It is 3-10x every other case in the campaign, which invites the reading that the case pulled in
a lot of genuinely new material. **It did not.** Measured per call:

- **327,405 of the 417,709 (78%) is ONE call**, at 06:33:21, whose `cache_read` was **0**. A
  total cache miss: the entire accumulated prefix had to be re-written.
- It follows a **339-second gap** with no API call at all (the previous message is 06:27:42).
  That is past the prompt cache's lifetime, so the cache expired and the next call paid full
  freight on ~327 k tokens of context that had already been paid for once.
- **The VRRP Feature Overview guide is not the cause.** The WebFetch of it is tool call 38 at
  05:17:26, which `case_tokens.py` bills to **T47201's** segment, along with the six reads of
  its extract and the `arpleg.py` extension. All of T47873's preparation was front-loaded into
  the previous case and is already paid for there.

So the lesson is not "this case read a lot". It is: **a pause longer than the cache lifetime
re-writes the whole context, and the later in a group it happens the more it costs.** By the
end of a group the prefix is ~327 k tokens, so one idle gap there is worth more than every
other cache write in the group combined. Mitigation in "scripts" below.

## Process taken
1. Call 134 -- case folder, and the group's already-built topology inherited from T47201. No
   re-probe, no re-read of the case text (fetched at T47201's call 32), no guide re-read.
2. Call 135 -- **STEP 0 baseline with the feature OFF**, and in the same leg the **self-test of
   the two new `arpleg` features**: three flows emitted to three different Ethernet destinations
   from one spec list, and the TTL column printed. The instrument is proven before any verdict
   rests on it.
3. Calls 136-139 -- `service vrrp`, gated on `show process`, then two `tb qmark` probes of the
   router-vrrp command surface (the 14-command list, and the absence of `version`).
4. Calls 140-144 -- STEP 1/2: VRRP configured on both units, `show vrrp brief` from both,
   a `tcpdump` of the advertisement, and the `V1-dut-master` leg.
5. Calls 145-153 -- STEP 4: `alternate-checksum-mode` on the DUT only, the `V3-split-master`
   leg, the `config-router` probe for the command, and the matched-mode A/B.
6. Calls 154-164 -- STEP 5: `circuit-failover vlan61 120` as the stimulus, `V4-swib-master`,
   then recovery, with `show vrrp brief` read from both ends at each transition.
7. Calls 165-173 -- STEP 7: `ckyn` for the save prompt, `ckreload`, two STP reads after boot,
   the `V6-after-reboot` leg, and the boot-source restore.
8. Calls 174-190 -- `.cfg` capture, STEP 8 removal, restore on both units, a second reload, a
   final `tb probe`, and the `V8-final-sanity` leg.
9. Calls 191-200 -- `work/run1.log` assembled, consoles logged out, queue updated,
   `RESULT T47873 PASS` to the sentinel at 06:36:57.

## Wasted input
- **Almost none, and this case is the campaign's model for it.** 31,694 chars over 67 tool calls
  is **473 chars per call** -- the lowest ratio in the group. Of 67 tool calls, only **three**
  read a file: the scratchpad VRRP extract (call 151), the case's own working log (call 171) and
  the group-C restore recipe from the campaign queue (call 180). Every other call is a device
  action whose output was either small by construction or redirected into `work/`.
- The largest single read is 2,469 chars (the `V1-dut-master` `arpleg` report, call 144) --
  i.e. the biggest thing pulled into context is a verdict-bearing measurement, which is what the
  context is for.
- The one avoidable cost is the idle gap at 06:27:42-06:33:21 described above. That is 327 k
  tokens of re-write for no new information.

## Repetition
- **No command was issued verbatim twice** (`case_tokens.py` reports no repeats).
- Calls 178-182 are a restore iteration rather than a repetition: the committed group-C recipe
  was read at call 180, applied, **refused**, and corrected. See O-40 under Accuracy risks.
- The case text and the VRRP guide were each read exactly once, in the previous case's segment.
  That is the pattern to copy: **read a group's shared authority in the first case, not in each
  one.**

## Accuracy risks
This case is where the campaign's two worst readings were produced and corrected, and both are
worth recording as method rather than as incident.

- **A decoder's complaint is a hypothesis; the peer's own behaviour is the measurement.**
  `tcpdump` on the DUT flagged its own default VRRPv3 advertisement `(bad vrrp cksum ...)`. The
  dispatching sentinel first read that as an **instrument artefact** and told the tester so. The
  tester disproved it with its own A/B: **one capture, one decoder, one window**, with
  `alternate-checksum-mode` set on the DUT only -- `10.38.22.34` (alternate) decodes with no
  complaint while `10.38.22.35` (default) decodes `(bad vrrp cksum 4a46)`; confirmed a third way
  by the transition-mode capture, where the same daemon's **v2** frame validates clean and its
  **v3** frame 26 us later does not. An artefact cannot be selective across one capture and one
  decoder.
- **Then the sentinel over-corrected**, to "the default is non-conformant". That claim rests on
  the validator being right, which was never independently verified. **The tester's final F-17
  wording is the accurate one and must not be loosened**: *two components of one firmware image
  disagree about the checksum of its own default VRRPv3 advertisement, and the vendor ships a
  command that makes them agree.* Which mode is RFC 5798 5.2.8-conformant is **NOT ESTABLISHED**.
  Closing evidence would be an independent VRRPv3 checksum implementation, or a third-party
  conformant peer.
- **The sentinel also called the third-party-peer interop limb NOT MEASURABLE on this bench, and
  that was wrong too.** Setting `alternate-checksum-mode` on one side only produced a **real dual
  master**: swi_b stopped accepting the DUT's advertisements and took over at **priority 100
  against the DUT's 150**, both routers then advertising for vrid 10 from the same virtual MAC
  `00:00:5e:00:01:0a`, with **ten ARP replies to five requests** for the virtual IP. **The
  vendor's own two checksum modes simulate a conformant and a non-conformant peer on one bench.**
  That is a reusable technique: when a feature has a compatibility mode, the mismatch between its
  two settings is a free interop partner. It is bounded by two measured controls, so it is not
  over-claimed -- default-to-default is fine (swi_b stayed Backup *and* reported
  `Master address: 10.38.22.34`, which it can only learn by accepting the frames) and
  alternate-to-alternate is fine (the pair re-converged immediately). **It is the mismatch that
  breaks the pair, not either mode.** What remains genuinely NOT MEASURED is narrower than the
  sentinel's claim: whether a *third-party* conformant router would reject the default frames.
- **O-37 -- `circuit-failover` and `transition-mode` are REFUSED while the VRRP session is
  enabled**: `% You must disable this session first`. The guide's procedures do not mention the
  ordering. The working order is **`disable` -> the command -> `enable`**, and it is mandatory;
  `priority`, `virtual-ip` and `preempt-mode` do **not** need it. A driver that sends
  `circuit-failover` into an enabled session gets a `% ` line that `cfg.py` stops at.
- **O-40 -- `no interface vlanN` was REFUSED on swi_b** (`% Removal of interface not allowed`)
  although the same command had succeeded on swi_a earlier in the campaign, for group C. Once
  the SVI has no address and no member ports there is nothing left to remove. **The reliable
  removal is: `no ip address` on the SVI, then delete the VLAN from the vlan database
  (`vlan database` / `no vlan N`).** The tester hit this against its own committed restore
  recipe and corrected the recipe in the campaign queue. A restore must **gate on the output**
  rather than assume either behaviour, because `cfg.py` stops at the `% ` and the teardown
  silently half-completes.
- **O-38 -- "v3" cannot be read back from the configuration.** There is no `version` command
  (`version ?` -> `% Unrecognized command`). The title's claim is graded from the
  advertisement's own version field on the wire. A tester who looks for a config line will
  wrongly report the feature missing.
- **Not a risk, but the reason the verdict holds:** every positive leg carries an unowned-MAC
  control at 0 and an instrument flow to the DUT's real SVI MAC at 5/5 **in the same capture**,
  and STEP 8 reproduces STEP 0 byte for byte. Each zero in this case is therefore a measurement
  and not a dead instrument.

## Next run: expected outputs
| step | value / CLI line this bench gave |
| --- | --- |
| topology | vrid 10 on vlan10; virtual IP **10.38.22.36**, owned by neither router; DUT vlan10 10.38.22.34/27 priority 150; swi_b vlan10 10.38.22.35/27 priority 100 (default, so not rendered in running-config) |
| instrument | three UDP flows to one destination 10.38.22.65 differing only in L2 destination -- `:9999%00:00:5e:00:01:0a` SUBJECT, `:9998%02:00:00:00:00:99` CONTROL (unowned MAC), `:9997%e0:1a:ea:d4:70:43` INSTRUMENT (DUT SVI MAC) |
| 0 | virtual IP unanswered, virtual MAC carrying nothing, instrument flow 5/5 |
| 1 | virtual MAC **`00:00:5e:00:01:0a`** as the Ethernet source of the advertisement; version field reads **3**; `show vrrp` -> `Accept mode: TRUE`, `VMAC enabled` |
| 1 | router-vrrp offers exactly **14 commands**: `advertisement-interval, alternate-checksum-mode, circuit-failover, disable, do, enable, exit, help, no, preempt-mode, priority, show, transition-mode, virtual-ip`. **No `accept-mode`, no `version`** (O-38, O-39); `vrrp vmac` is a **global** command |
| 2 | the ARP reply for 10.38.22.36 carries `00:00:5e:00:01:0a` in **both** the ARP payload and the Ethernet source; every SVI on this DUT otherwise shares `e0:1a:ea:d4:70:43` |
| 3 | backup loses its connection -> swi_b goes **Initialize** on its own admission; client 5/5 at an **unchanged one-hop TTL**; control 0 |
| 4 | default VRRPv3 frame decodes `(bad vrrp cksum ...)` on the device's own `tcpdump`; with `alternate-checksum-mode` it decodes clean. Mismatched modes -> **two masters**, priority 100 displacing 150, **ten ARP replies to five requests** |
| 5 | role transition read in the dataplane as **ttl 63 -> 62 -> 63** with the instrument held at 63 and the unowned-MAC control at 0; client 5/5 throughout |
| 5 | stimulus: `circuit-failover vlan61 120` -- VRRP's own mechanism, on an interface **NOT on the measurement path**, so the stimulus does not also destroy the instrument |
| 6 | `transition-mode true` -> paired v2 and v3 advertisements **26 us apart** from one virtual MAC to one group. With it off the DUT sends v3 and only v3 |
| 7 | reload to `login:` measured at **60 s and 62 s** (x960.md 7.9 gives 60-68 s); tracking re-arms by itself, reading `Monitored circuit: vlan61, Priority Delta: 120, Status: UP` |
| 7 | **x960.md 7B.8 bites here**: `port1.0.48` read `Designated Discarding` on the first post-reload STP read and `Forwarding` on the second. **Read STP twice after a reload** -- the persistence leg reads as a failure in that window |
| 8 | removal returns byte for byte to the STEP 0 baseline, instrument still 5/5 |
| ordering | `disable` -> `circuit-failover` / `transition-mode` -> `enable` (O-37) |
| guide | C613-22049-00 REV E has **zero** occurrences of "alternate" or "checksum" |

## Next run: scripts
- **Already shipped by this case, both generic and both in `tools/README.md`:**
  - **`tools/arpleg.py --udp DST[:PORT][@SRC]%L2DST`** -- a **per-spec Ethernet destination**.
    `--l2-dst` applies to every `--udp` spec and so cannot carry a subject and a control that
    differ only in their link-layer address, which is exactly what a first-hop-redundancy case
    needs: one flow to the virtual MAC and, in the same capture, a control to a MAC nobody owns.
  - **`tools/arpleg.py --show-ttl`** -- appends the received IPv4 TTL to each flow in the report.
    The TTL is the only field on the wire that says **how many routers forwarded** a frame, so
    when two routers share one virtual MAC the hop count is what attributes a forwarded frame to
    one of them. It is what graded the role transition (63 -> 62 -> 63). Off by default.
  - Both were **self-tested inside a real leg with a known-good instrument control before any
    verdict rested on them** (STEP 0, call 135). Copy that ordering.
- **Proposed -- `tools/keepwarm.py` (or a `tb` subcommand).** Nothing to do with the device: a
  wrapper for any step that will idle longer than the prompt cache lives (a reload, a long
  capture, a convergence timer). `keepwarm.py --until <file-on-box> --timeout 600 --tick 120`
  would poll in sub-cache-lifetime chunks so there is an API call every couple of minutes,
  instead of one call that returns after 339 s and costs a 327 k-token re-write. `tb waitfor`
  already does the waiting; what is missing is the ticking. **Highest-value single change in this
  group**, and it applies to every campaign.
- **Proposed -- `tools/vrrpwire.py --pcap FILE` (or a `--decode vrrp` mode on an existing
  helper).** Parse the VRRP advertisement independently of `tcpdump`: version, vrid, priority,
  advertisement interval, source MAC, and **the checksum recomputed by our own code**. That is
  precisely the evidence F-17 is missing, and it would have settled in one call the question the
  sentinel got wrong twice.

## Next run: references
- `Feature Overview Guides/VRRP Feature Overview and Configuration Guide` (C613-22049-00 REV E)
  -- **now in the repo**, fetched from the URL the authored step text names. Do not re-fetch.
- `platforms/x960.md` 7.9 (reload to `login:` 60-68 s) and **7B.8** (read STP twice after a
  reload).
- `tb277/x960/CAMPAIGN-QUEUE-2026-10-16T1406.md`, entries **F-17** and **O-37 to O-40** -- the
  checksum finding with its two bounding controls and its explicit NOT-ESTABLISHED clause, and
  every CLI trap, each with its reproduction. The group-D restore recipe in that file carries the
  O-40 correction.
- Memory `bench-scripts-stop-on-cli-errors` -- why O-37 and O-40 truncate a `cfg.py` batch.
- Memory `tcpdump-nfs-root-squash-capture` -- the general rule this case re-proved from the other
  side: an instrument's complaint, like an instrument's zero, is only a measurement once the same
  instrument has been shown to behave differently under a known-different input.

---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript call or working-file line they come from. A review never changes a verdict: a doubt about one goes to the Test Engineer.
