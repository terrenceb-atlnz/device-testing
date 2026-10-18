# T44378 process review -- ipv4svc-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `agent-a716404dd1611bc0d.jsonl` and the working files.

(52) IPv4 - UDP Broadcast Helper, **no authored step text**, **PASS**. Case 2 of 3 in group B;
it ran on the underlay and the tooling T44181 had already built.

Findings true of the whole group are in `../REVIEW.md` and are not repeated here: **A1** the
working logs do not name every tool, **A2** the `arpleg.py` well-known-port marker defect
(found in *this* case -- the detail is in A2), **A3** the shared underlay, **A4** the stale box
copy of `tools/`, **A5** the six-leg skeleton, **A6** guide-authored cases.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 40 | 31,548 | 5,227,485 | 216 | 20 | 716 s (12 min) | 13,554 chars |

Transcript tool calls #110-#129. **The cheapest full-depth case in the group**: six measured
legs, a reload, a removal proof and a teardown diff for 20 tool calls, because the underlay,
the `.cfg` pipeline and the wire instrument already existed. Its largest single read was
1,864 chars. This is the shape to aim for.

Note the accounting: the `arpleg.py --udp` / `--l2-dst` extension this case needed was built
at calls **#106-#109, which `case_tokens.py` charges to group overhead, not to this case**.
Add ~4 kB and four calls to the true cost of the first case that needs a new probe type.

## Process taken

1. **#110-#111** step 0, the read-only CLI surface probe with `qmark.py`: `ip forward-protocol`
   in global config, `ip helper-address` and `ip directed-broadcast` in interface config.
2. **#112** pre-case `show running-config` -> `work/pre-u2.log`, `.cfg` via `rc2cfg.py`,
   `rcdiff` against T44181's pre-group capture (only the 31 underlay lines differ).
3. **#113** extended `arpleg.py` so `--udp` could take an L2 destination.
4. **#114** leg 1, baseline OFF -- three UDP broadcast flows plus a routed unicast control.
   **This leg exposed the marker defect (A2)**: the `:69` flows reported as foreign and the
   leg exited 7 with a COUNTER DISAGREEMENT.
5. **#115-#117** fixed the marker generically (whole-frame scan in both `classify()` and
   `report()`), then re-ran the baseline leg: all four flows `[ours]`, exit 0.
6. **#118-#119** leg 2, helper ON: two forwarded ports plus an unhelped control port.
7. **#120** leg 3, port 37 removed -- the port list isolated from the helper address.
8. **#121** leg 4, a second helper address that is a connected subnet's broadcast address.
9. **#122-#124** leg 5, persistence: staged `flash:/ck44378.cfg`, `ckreload`, re-read
   `show boot` + STP, re-measured the dataplane.
10. **#125-#126** leg 6, removal, proven in the dataplane; boot pointer restored.
11. **#127-#129** wrote `work/run1.log`, updated `tools/README.md`, sent `RESULT`.

## Wasted input

**None found.** Every read in this segment was either a tool-source read needed to make the
fix (#116, 1,864 chars) or a leg's own output. The largest non-leg read was 1,847 chars.

## Repetition

- **`tools/tb scratch` was re-pushed at #110 and #114** because `arpleg.py` had just been
  edited -- the same stale-copy tax as group finding A4, here paid correctly and in advance.
- **Three separate `arpleg.py` edits in this case** (#113 `--l2-dst`, #115 and #117 the two
  halves of the marker fix), each needing its own push. #115 and #117 are one defect fixed in
  two places because `classify()` and `report()` each had their own copy of the marker test.
  *Fix:* a single `is_ours(pkt)` helper, so the next marker change is one edit. Across the
  group, `arpleg.py` was edited six times (#107, #109, #113, #115, #117, #134) -- see
  `../REVIEW.md` proposal S5.

## Accuracy risks

1. **The instrument's self-check was wrong while the measurement was right (A2).** This is the
   case that found it. The `:69` burst reported **0 of its own 5 frames** as `[ours]`, and the
   leg exited 7 claiming `sent 20 marked frame(s), capture on eth3 holds 15`. A tester who
   trusted the exit code would have recorded a bench fault that did not exist; a tester who
   trusted the count would have recorded 15 frames sent. The full statement, and what it means
   for older results, is in `../REVIEW.md` **A2**. **Closing evidence:** it was closed -- the
   fix was made and the leg re-run clean. The residual risk is historical, not forward.
2. **No authored step text, so the step boundaries are the tester's.** Each step is anchored to
   a sentence of the **IP Feature Overview Guide C613-22007-00 REV I, p.16**, which is what
   makes the verdict re-gradable by someone who disagrees with the decomposition. The risk is
   that a future reader treats these six steps as if they came from the case database. They did
   not. *Fix:* the guide page belongs in the STEP heading, not only in the preamble.
3. **Tools used but not named (A1).** This working log names `arpleg`, `qmark`, `rcdiff`,
   `ckcase` and `sudotool`. It does **not** name `cfg.py`, `ckcon.py`, `ckyn.py`,
   `ckreload.py` or `rc2cfg.py`, all of which were used -- the entire configuration, reload and
   `.cfg` path. The final log's tool line was written without them.
4. **The post-reload STP state was read once here, not twice.** T44182 found STP still at
   `Learning` immediately after a reload and took a confirming read; this case read it once
   (#123) before measuring. The measurement came out right and the control flow would have
   caught a blocked port, so the verdict stands -- but the next run should take the confirming
   read in every reload leg, not just when the first read looks wrong.

## Next run: expected outputs

Addresses: host eth3 **10.38.22.40** (sender, vlan10 side), DUT vlan10 **10.38.22.34/27**
(subnet broadcast **.63**), DUT vlan48 **10.38.22.66/27** (subnet broadcast **.95**), host eth4
**10.38.22.65** (the far host / helper target).

| step | what this bench gave |
| --- | --- |
| 0 (surface) | **O-17 (process lesson).** `ip forward-protocol` accepts only `udp`, and `ip forward-protocol udp` accepts only a **numeric PORT** -- there are **no named service keywords** on this platform. `ip helper-address` takes a bare `A.B.C.D`: **no interface form, no VRF form.** A test written against the named forms fails at its first command. |
| 1 (baseline OFF) | Nothing relayed. All 15 UDP broadcasts (`:69` to 255.255.255.255, `:37` to 10.38.22.63, `:7777` to 255.255.255.255, x5 each) were on the ingress wire; `s1-baseline-off-eth4.pcap` held **5 frames -- the ICMP control only**, with the DUT's MAC as L2 source. The DUT was routing and the far capture was live; it simply relayed nothing. |
| 2 (helper ON) | With `ip forward-protocol udp 69` + `udp 37` and `ip helper-address 10.38.22.65` on vlan10: eth4 holds **15** -- 5x `:69` and 5x `:37` both rewritten to `-> 10.38.22.65`, plus the 5 ICMP control. The unhelped `:7777` crossed **0** times. |
| 2 (semantics) | **O-18 (process lesson).** A relayed frame **keeps the original IP source address and BOTH UDP ports**; only the IP destination and the Ethernet header are rewritten. IP Helper is a plain forwarder -- **no giaddr, no option insertion** -- which is the opposite of `ip dhcp-relay` on the same box (`platforms/x960.md` §6). A tester looking for a giaddr rewrite will think the relay is broken. |
| 3 (port list) | `no ip forward-protocol udp 37` with the helper address untouched: port 37 goes **5/5 -> 0/5** between two otherwise identical legs; eth4 holds **10** (`:69` + control). The port list is the discriminator, independently of the helper address. |
| 4 (broadcast helper) | A **second** `ip helper-address 10.38.22.95` alongside the first: 10 helped ingress broadcasts produce **20 relayed frames, two per ingress frame** -- eth4 holds **25**. The two L2 treatments appear side by side in one capture: `-> 10.38.22.65` goes **unicast to the host's MAC**, `-> 10.38.22.95` goes to **`ff:ff:ff:ff:ff:ff`**, a true link-layer broadcast onto that directly connected subnet. The `:7777` control still relayed 0 times. |
| 5 (reload) | Login seen **61 s** after `reboot system? (y/n): y` (`platforms/x960.md` §7.9 gives 60-68 s). The dataplane after the reboot was **identical to leg 4**: 25 frames, same five flows. |
| 6 (removal) | `no ip helper-address <A.B.C.D>` x2 and `no ip forward-protocol udp <port>` x2: eth3 still carries all 20 ingress frames, eth4 holds **5 -- the ICMP control only**. Back to the baseline exactly. Teardown diff empty. |

## Next run: scripts

Existing -- reuse, do not rebuild:

- **`tools/arpleg.py`** via `tools/tb sudotool <box> <scratch> arpleg`, with
  `--tag <leg> --out DIR --iface eth3 --watch eth4 --udp DST[:PORT][@SRC][,...]
  --l2-dst ff:ff:ff:ff:ff:ff --icmp <control dst> --sender <src ip> --gw-mac <DUT SVI MAC>
  --count 5`. The `--udp` port/source form and `--l2-dst` were added in this group; the
  whole-frame marker scan (A2) is in. One invocation gives the ingress flows, the far-side
  capture, the `[ours]` marks and the per-flow counts -- which is the entire measurement for
  a relay feature.
- **`tools/tb cfg` / `tools/tb ckyn` / `tools/tb ckreload` / `tools/rc2cfg.py` /
  `tools/rcdiff.py`** -- the configure, confirm, reload and teardown-diff path. **Name them in
  the working log** (A1).
- **`tools/tb qmark ... --mode "configure terminal" -- "ip forward-protocol "`** -- how O-17 was
  found, in one read-only call, before anything depended on a named keyword.

Proposed (not built):

- **`tools/relayleg.py --ingress eth3 --egress eth4 --helped 69,37 --unhelped 7777
  --helper 10.38.22.65,10.38.22.95 --count 5 --expect <table>`** -- the relay-feature leg as one
  call: send the helped and unhelped flows plus a routed control, capture both sides, and print
  the sent/arrived matrix with a per-flow verdict. This case assembled that by hand six times
  with only the port list and helper set changing.
- **An `is_ours(pkt)` helper inside `arpleg.py`** so the marker test exists once rather than in
  both `classify()` and `report()` -- the reason A2 took two edits.
- **S3 `tools/toolsused.py`** (see `../REVIEW.md`) -- would have closed accuracy risk 3.

## Next run: references

- **IP Feature Overview Guide C613-22007-00 REV I, p.16 (IP Helper)** -- the source of every
  step in this case. Under `Feature Overview Guides/`; convert with `pdftotext -layout` into
  the scratchpad, grep, read the page. Do not re-derive the decomposition: the six legs above
  already cover every sentence of that section this bench can reach.
- `platforms/x960.md` **§6** -- `ip dhcp-relay` on the same box, for the contrast O-18 rests on;
  **§7.9** -- the 60-68 s reload window.
- `T44181.log` **TOPOLOGY AS TESTED** -- the underlay, both host NIC MACs and addresses, and the
  DUT clock offset. This case cites it rather than re-capturing, and so should the next one.
- `T44378.log` **CAVEAT** -- the scope actually proven (one ingress interface, one far subnet,
  two forwarded UDP ports). Anything outside it is unproven, not false.
- Memory **`scapy-for-traffic-tests`** and the documented `dhcp4.py` BOOTP trap -- A2 is the
  same family, and the next scapy-based tool will meet it again.
- `../REVIEW.md` **A1-A6**, and **A2** in full for what the marker defect means for older
  results.
