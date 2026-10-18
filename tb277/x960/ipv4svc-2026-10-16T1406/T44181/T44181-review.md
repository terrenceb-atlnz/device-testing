# T44181 process review -- ipv4svc-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `agent-a716404dd1611bc0d.jsonl` and the working files.

(51) IPv4 - Ping Polling, 11 authored steps, **PASS**. Case 1 of 3 in group B; it also built
the L3 underlay that T44378, T44182 and groups C/D inherited.

Findings true of the whole group are in `../REVIEW.md` and are not repeated here: **A1** the
working logs do not name every tool, **A2** the `arpleg.py` well-known-port marker defect,
**A3** the shared underlay, **A4** the stale box copy of `tools/`, **A5** the six-leg
skeleton, **A6** guide-authored cases.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 79 | 158 | 115,048 | 13,922,735 | 890 | 80 | 2,475 s (41 min) | 63,461 chars |

Transcript tool calls #26-#105. **This case alone is 48% of the group's cache-read and 2.7x
the tool output of T44378 and T44182 combined.** Three causes, only one of them the case
itself: 11 authored steps plus a 14-leg plan (unavoidable); `tools/hostsim.py` written from
scratch mid-case (~12 calls, #38-#53); and three framework-level defects found and fixed while
the case ran (~8 calls, #47-#50, #97-#98). See "scripts" below.

## Process taken

1. **#26-#30** pre-case capture: full `show running-config` + `show boot` + `show clock` +
   `show ip interface brief` into `work/pre-u2.log`; read back 130 lines (4,360 chars); port
   states and ARP pulled with a filtered `sed`+`grep`; `tools/tb probe`; the bench capture's
   clocks.
2. **#31-#35** wrote the shared B/C/D underlay + restore recipe into the campaign queue
   *before* configuring anything, then told the sentinel.
3. **#36-#37** applied the underlay (VLAN 10 / VLAN 48, two SVIs, two access ports) and
   verified it: DUT pings both host NICs, both ports Forwarding.
4. **#38-#53** built `tools/hostsim.py` -- read `nsresp.py` and `dhcp4.py` first to see whether
   an IPv4 ARP+ICMP responder already existed (it did not), wrote it, smoke-tested it against
   the DUT twice (#43-#46, #51-#52), then added per-echo timing and per-address muting.
   In the middle of this, **#47-#50** found and fixed `tools/tb`'s `SUDO_TOOLS` allowlist.
5. **#54-#55** post-setup `.cfg` via `rc2cfg.py`; opened `work/run1.log`.
6. **#56-#57** step 0, the read-only CLI surface probe with `qmark.py` (exec mode and config
   mode, no trailing CR).
7. **#58-#60** step 1, the limits step: 100 `ping-poll <n>` in one `cfg.py` batch, read back
   with `show ping-poll brief`, boundary-tested 0 and 101, then 98 `no ping-poll` to clean up.
8. **#61** step 0b, baseline OFF, both segments, 30 s.
9. **#62-#67** steps 2-6: `hostsim` up for 240 s, the polling instance configured and read
   back, the control instance, then the two triggers.
10. **#68-#70** the measured leg, three instruments at once: `hostsim` with
    `--mute-at 70 --unmute-at 120`, a host `tcpdump` on eth3, and `poll.py` sampling
    `show ping-poll brief` every 2 s for 180 s.
11. **#71-#74** reduced the three records in the scratchpad and cross-checked the two
    independent clocks.
12. **#75-#77** the DUT's own evidence: triggers, counters, `show log`, then `debug ping-poll`.
13. **#78-#80** steps 10 and 8 -- `clear ping-poll`, then `no active` graded on the wire with
    poll 2 as the in-leg control.
14. **#82-#86** step 12, persistence: staged `flash:/ck44181.cfg`, `ckreload`, re-read state,
    re-measured the dataplane.
15. **#87-#91** step 13, removal, proven in the dataplane and then in `rcdiff`.
16. **#92-#96** step 9's script limb, and **#97-#98** the `console.py` ADVISORY fix it exposed.
17. **#99-#105** wrote `work/run1.log` in four appends, updated `tools/README.md`, committed,
    sent `RESULT`.

## Wasted input

Little, for a case this size -- the expensive reads were instrument-building, not re-reading.
What there is:

- **#27, `sed -n '1,130p' work/pre-u2.log` (4,360 chars).** The file had just been written by
  the tester's own command; the next call (#28) already demonstrated the right technique, a
  filtered `grep -E 'port1\.0\.(2|4|8|10|14|16|40|48) '` over a line range (787 chars). The
  130-line read was a general look at a config the `.cfg` file already preserves. *Narrower:*
  `rc2cfg.py` writes the `.cfg`; read back only the lines the case depends on.
- **#39, the `dhcp4.py` grep (4,609 chars)** and **#38/#40 the `nsresp.py` reads (3,245 +
  2,919).** Justified -- they answered "does an IPv4 ARP+ICMP responder already exist?" before
  writing one, which is the right question. But 10.8 kB to establish an absence is the cost of
  `tools/README.md` not having a capability index (group finding 2, proposed script S2).
- **#75 `show trigger` + `show trigger 1` + `show trigger 2` + counters + state (4,160) and
  #77 the debug block (3,336).** Both earned: this is the DUT's own corroboration of the wire
  measurement, and the final log quotes from both.

## Repetition

- **`hostsim` was smoke-tested twice against the DUT (#43-#46, then #51-#52)** because the
  first run used a stale box copy of `tools/` (group finding A4). One `tools/tb scratch`
  before the first smoke test would have removed four calls.
- **`show running-config` was captured in full four times in this case** (#26 pre, #54
  post-setup, #91 post, plus the reload re-read at #85). Correct -- each is a different moment
  and each went to a file rather than into context. Not waste; noted so a reader does not
  count it as such.
- **The ping-poll state was read from the DUT in five separate `ckcon` calls** (#59, #63, #75,
  #79, #85). Each belongs to a different step. No merge available without confusing the
  evidence trail.

## Accuracy risks

1. **An unanchored read-back in the working log, dropped from the final log.**
   `work/run1.log:493` carries `(later) awplus#show ping-poll 1 -> Debugging : Disabled` with
   no timestamp and no command that produced it -- "(later)" is not an anchor. It was the
   proof that `no debug ping-poll 1` took effect, and the final log could not use it.
   *Fix:* every read-back in the working log is written as the command, its prompt and the
   time it was sent. If a value is quoted out of its capture order, cite the `work/` file and
   line it came from. **Closing evidence:** a `show ping-poll 1` taken immediately after the
   `no debug` in the same `ckcon` invocation, so the ordering is in the transcript itself.
2. **A detail the run summary had flattened, recovered from the work file.** The 2 s sampler
   recorded an intermediate **`Critical`** state on *both* transitions -- `t+78.23` (before
   Down at `t+86.24`) and `t+122.26` (before Up at `t+124.26`) -- and the run summary had
   collapsed the sequence to Up->Down->Up. The step's verdict depends on the state machine, so
   the collapse would have mis-stated it. It was recovered from `work/s4-pollstate.log` and is
   in the final log.
   *Fix:* **a run summary must not flatten sampler output that a verdict rests on.** When a
   step is graded on a state machine, the summary quotes every distinct state the sampler saw,
   with its timestamp, or it quotes nothing and points at the sampler file.
3. **Tools used but not named (group finding A1, in its sharpest form here).** The working log
   names `cfg.py`, `ckyn.py`, `qmark.py`, `poll.py`, `hostsim.py`, `rcdiff.py` and `arpleg`,
   `capture`, `sudotool` as `tb` subcommands -- but **`ckreload.py` and `rc2cfg.py` appear
   nowhere**, and `ckcon` appears once, bare, with no arguments. The reload limb and every
   `.cfg` in this folder were produced by tools the log does not mention.
4. **The sampler's first sample landed at t+9.03 with both instances already Up**, so the
   initial Up transition is *bounded* (<= t+9.03), not resolved. The log says so and resolves
   it from the wire instead (replies at t+0.00 and t+2.10, up-count 2 satisfied at t+2.10),
   which is the right handling. *Fix for next time:* start `poll.py` **before** the first
   `active`, so the sampler owns the initial transition too.
5. **An instrument died mid-run and nearly took a measurement with it.** `arpleg.py --out DIR`
   created a **root-owned** directory, so `poll.py` completed its 180 s of sampling and then
   died with `PermissionError: '/tmp/ckt1406b/T44181/poll.done'`. No data was lost -- the
   samples were already on disk -- but the donefile convention had silently broken, and a
   consumer waiting on the donefile would have hung or concluded "no samples". Fixed:
   `arpleg.py` now chowns its `--out` directory back to `SUDO_UID`. *Risk that remains:* any
   other tool that writes a donefile into a directory a sudo tool created first.
6. **A trigger-script warning is an ADVISORY, not a rejection**, and was nearly read as one:
   `script N <file>` for a non-existent file prints `does not exist. Please ensure it is
   created` but **stores the reference** (`show trigger 1 -> Number of scripts 1`).
   `console.ADVISORY` was extended so a prompt driver does not treat it as a failure.
7. **A genuinely unmeasurable limb, recorded as a CAVEAT and not as a failure.** See
   "references" below -- this is a standing bench limitation, not a one-off.

## Next run: expected outputs

| step | what this bench gave |
| --- | --- |
| 0 (surface) | `show ping-poll [<1-100>\|state {up\|down}] [brief]`, `clear ping-poll {<1-100>\|all}`, `debug ping-poll <1-100>` all exist. **There is no `show debugging ping-poll`.** |
| 1 (limits) | **100** is the maximum: 100 `ping-poll <n>` accepted in one batch with 0 CLI errors, all 100 listed by `show ping-poll brief`; both `ping-poll 0` and `ping-poll 101` -> `% Invalid input detected at '^' marker.` Matches the `<1-100>` range in the `?` probe and the authored text. |
| 1 (ART) | The authored ART run `1341_limits - 1341.1001.4991` is **not executable on this bench** -- there is no framework on tb277. Measure the limit directly; see "references". |
| 0b (baseline) | Feature OFF: **0 ICMP in 30 s** on both segments. Background on the eth3 segment was 1 ARP request + 1 reply; the foreign host emitted nothing. |
| 3 (defaults) | `show ping-poll <n>` straight after `ip <A.B.C.D>`: Critical interval **1**, Normal interval **30**, Fail count **5**, Up count **30**, Sample size **5**, Length **32**, Timeout **1**, Source IP address **Default**, Status **Down**, Enabled **Yes**. Only normal-interval 30 and critical-interval 1 are in the authored text; the rest are measured platform facts. |
| 5 (description) | **O-13 (process lesson).** `description` is **refused before `type` is set**: `% Please specify the trigger type first`. The authored step names `type` and `description` with no ordering constraint. A `show running-config` replay is safe (it emits `type` first); a hand-written batch in the authored order is not, and **`cfg.py` stops and abandons the rest of the batch**. Send `type` first. |
| 6 (intervals) | **O-14 (process lesson).** The poll **period is `timeout + interval`, not `interval`.** With `timeout 2 / normal-interval 5 / critical-interval 2`: **5.0-5.2 s while Up**, **3.7-4.6 s, mean 4.14 s, while Down** (timeout 2 + critical-interval 2), over 36 gaps, confirmed by the DUT's own debug lines. A tester who sets `critical-interval 2`, measures 4 s and expects 2 s will wrongly grade the command broken. Not a defect. |
| 4/7 (transitions) | Sampled every 2 s over 180 s, 89 samples: poll 1 Up (<= t+9.03) -> **Critical t+78.23** -> Down t+86.24 -> **Critical t+122.26** -> Up t+124.26. The control instance **never left Up**. Expect the intermediate `Critical`; a sampler that reports Up->Down->Up has been flattened. |
| 7 (DUT log) | **O-15 (process lesson).** `show log \| include PING` returns **nothing** across four transitions -- ping polling writes no log line of its own. The only record is `TRIGGER[...]: Trigger N (...) activated`, and only if a ping-poll trigger exists. Do not wait on a PING log line; it will never come. |
| 9 (script) | A `script N <file>` reference to a **non-existent** file is accepted and stored -- `show trigger 1 -> Number of scripts 1` -- after an advisory `does not exist. Please ensure it is created`. The warning is not a rejection. |
| 11 (debug) | **O-16 (process lesson).** `show debugging ping-poll` -> `% Invalid input detected at '^' marker.`, and the full `show debugging` has **no ping-poll section**. The debug state is readable **only** from the `Debugging :` field of `show ping-poll <n>`. `debug ping-poll 1` itself prints per-poll send/result lines at a 4 s period while Down. `no debug ping-poll 1` logs `Pingpolld has received SIGHUP`. |
| 12 (reload) | Login seen **68 s** after `reboot system? (y/n): y` (x960 §7.9 gives 60-68 s). All parameters, both triggers **and live polling** survived; 6 polls / 30 s measured after the reboot. Allow a further ~30 s for STP to leave Learning before grading the dataplane. |
| 13 (removal) | No instances, no triggers, and **not one frame** to .44 or .45, while the control flow was answered 5/5. |

## Next run: scripts

Existing, now proven for this case -- reuse, do not rebuild:

- **`tools/hostsim.py <iface> <ip[,ip...]> <stats.json>`** with
  `--duration S --mute-ip IP --mute-at S --unmute-at S --log-echo FILE [--quiet]`. Written for
  this case and already in `tools/README.md`. It is what makes a ping-poll transition
  measurable: a host that can be silenced **without taking the link down**, with a per-echo TSV
  whose clock is independent of the DUT's. Any up/down-detection feature (ping-poll, BFD-like
  polling, a trigger on reachability) should use it.
- **`tools/tb poll <box> <scratch> <console> <baud> <interval> <duration> <donefile> "<show>"`**
  -- the 2 s state sampler. Start it **before** the state change, not after (risk 4).
- **`tools/tb qmark ... --mode "configure terminal" -- "<prefix> "`** -- prove the command
  exists before the step relies on it. Cheap and it caught O-16.
- **`tools/cfg.py`** via `tools/tb cfg` for batched configuration; **`tools/tb ckyn`** when a
  `(y/n)` confirmation is in the batch (`YN?:copy running-config flash:/<name>.cfg`);
  **`tools/tb ckreload`**; **`tools/rc2cfg.py`** and **`tools/rcdiff.py`**.

Proposed (not built):

- **`tools/pollpoll.py --console u2 --instances 1,2 --mute-plan 70:120 --sample 2
  --duration 180 --out DIR`** -- one command that starts `hostsim`, the pcap and the sampler
  together, aligns their clocks and prints the transition table with the intermediate states
  (risk 2) and the per-gap periods (O-14) already reduced. This case spent six calls
  (#68-#74) assembling and reducing that by hand, and the reduction is where the flattening
  happened.
- **`tools/limits.py --console u2 --cmd "ping-poll {n}" --range 1-100 --probe-below 0
  --probe-above 101`** -- the limits step as one call: batch-create to the claimed maximum,
  read back the count, boundary-test either side. Replaces #58-#60 and is reusable for every
  "MAX supported X" ART step this campaign cannot run.
- **S3 `tools/toolsused.py`** (see `../REVIEW.md`) -- would have closed risk 3 mechanically.

## Next run: references

- **`STANDING-ORDERS.md` §4 -- the standing bench limitation behind this case's CAVEAT.** The
  **content** of a trigger script is **not measurable unattended on tb277**. Running a real
  `.scp` needs the file in the DUT's flash, the only transfer path to this DUT is
  `copy tftp://<box>/...` from the box's `/tftproot`, and writing there is a **root-level write
  on the box**, which an unattended run does not do. Do not rediscover this: either accept the
  limb as out of scope (it belongs to the Trigger feature, not to ping polling) or get the
  script staged by the Test Engineer **before** the run starts. What *is* measurable without it
  is the ping-poll side of the contract -- the `script` syntax, that a reference to a
  non-existent file is accepted and stored, and that `type ping-poll <n> {up|down}` fires at
  the right moment.
- **There is no test framework on tb277**, so any authored "Run ART ..." step is not executable
  here. Measure the limit or behaviour the ART case measures, directly, and say so in the
  CAVEAT with no results link. (Same handling will be needed by every ART step in this
  campaign.)
- `platforms/x960.md` **§7.9** -- the 60-68 s reload window; this case measured 68 s.
- `T44181.log` **TOPOLOGY AS TESTED** -- the underlay, both host NIC MACs and addresses, and
  the DUT clock offset. T44378 and T44182 cite it rather than re-capturing.
- Memory **`awplus-cli-confirmations-need-enter`** (why `ckyn` exists) and
  **`bench-scripts-stop-on-cli-errors`** (why O-13's ordering refusal abandons the rest of a
  `cfg.py` batch).
- `../REVIEW.md` **A1-A6** for the group-wide findings.
