# T44182 process review -- ipv4svc-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `agent-a716404dd1611bc0d.jsonl` and the working files.

(53) IPv4 - Directed Broadcast Forwarding, **no authored step text**, **PASS**. Case 3 of 3 in
group B; it ran on the underlay and the tooling the first two cases had already built.

Findings true of the whole group are in `../REVIEW.md` and are not repeated here: **A1** the
working logs do not name every tool, **A2** the `arpleg.py` well-known-port marker defect,
**A3** the shared underlay, **A4** the stale box copy of `tools/`, **A5** the six-leg
skeleton, **A6** guide-authored cases.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 21 | 42 | 30,664 | 6,240,989 | 207 | 21 | 727 s (12 min) | 9,670 chars |

Transcript tool calls #130-#150 (the last two are the commit and the `RESULT` line). **The
least tool output of the three cases -- 9,670 chars for seven measured legs** -- and its
largest single read was 984 chars, a leg's own result table. Every leg was read at the size it
printed; nothing was re-read from disk. This is the cheapest case in the group and the one to
copy.

## Process taken

1. **#130** pre-case `show running-config` -> `work/pre-u2.log`, `.cfg` via `rc2cfg.py`,
   `rcdiff` against T44181's pre-group capture (only the 31 underlay lines differ). Step 0,
   the `qmark.py` surface probe for `ip directed-broadcast`, was folded into the T44378
   interface-mode probe at #111 rather than repeated.
2. **#131** leg 1, baseline OFF: 10 directed broadcasts to 10.38.22.95 plus a routed unicast
   control, counted on both segments.
3. **#132** leg 2, the direction discriminator -- `ip directed-broadcast` on the **ingress**
   interface (vlan10), which the guide says is the wrong one.
4. **#133** leg 3, the same command moved to the **destination subnet's** interface (vlan48),
   with nothing else changed.
5. **#134** extended `arpleg.py --udp` with a per-spec source address, so the ACL leg could
   carry a permitted and a denied source in **one** capture.
6. **#135-#136** leg 4, the optional standard ACL: `access-list 1 permit 10.38.22.40 0.0.0.0`
   bound as `ip directed-broadcast 1`, both sources sent together.
7. **#137** leg 5, the ACL inverted to permit the other source -- is it consulted per packet,
   or merely present?
8. **#138-#140** leg 6, persistence: staged boot config, `ckreload`, `show boot` + STP, and a
   **confirming** STP read when the first one caught a Learning port.
9. **#141-#142** leg 7, removal proven in the dataplane; boot pointer restored; teardown diff.
10. **#143** wrote `work/run1.log`.
11. **#146-#148** the queue results rows -- then removed its own duplicates when it found the
    sentinel had already added them from the `RESULT` lines (charged to group overhead).
12. **#149-#150** committed and sent `RESULT`.

## Wasted input

**None found.** The largest reads in the segment are leg result tables (984, 959, 943, 713,
708 chars), all of which the final log quotes. No file was read in full, nothing was re-read
from disk, and no `show running-config` was pulled into context -- all four captures went to
files and were compared with `rcdiff.py`.

One near-miss worth naming as *good* practice rather than waste: **#140 is a second
`show spanning-tree brief` taken deliberately** (455 chars) because the first read caught a
port still Learning. Spending a call to stop a measurement resting on a doubtful instrument is
the correct trade; see accuracy risk 1.

## Repetition

- **Step 0 was not repeated.** The `ip directed-broadcast` surface probe was folded into
  T44378's interface-mode `qmark` call (#111) and cited from there. This is exactly the
  "once per group, not once per case" saving `logged-output.md` §5 asks for, and it should be
  the default for any probe that covers more than one case's commands.
- **The pre-case `rcdiff` baseline was T44181's pre-group capture, not a fresh one** -- one
  capture serving three cases.
- **A fourth `arpleg.py` edit** (#134, the per-spec source). Four edits across the group in
  four separate calls, each needing a `tools/tb scratch` push (A4). The three capabilities
  added (`--udp PORT`, `--l2-dst`, `--udp @SRC`) were all foreseeable from the two cases'
  requirements and could have been one change; see `../REVIEW.md` proposal S5.

## Accuracy risks

1. **An instrument in a transient state immediately after a reload -- caught and closed.** The
   first `show spanning-tree brief` after the reboot read `port1.0.48 Designated Learning`,
   inside the settle window. A measurement taken against a Learning port would have produced a
   false "not forwarded". The tester took a **confirming read** (`work/s6-stp-confirm.log`)
   showing `port1.0.10 Designated Forwarding / port1.0.48 Designated Forwarding`, identical to
   the pre-case baseline, before grading. *Fix, for every reload leg:* read STP **twice** --
   once on login and once before the dataplane leg -- and grade only against the second.
   T44378's reload leg read it once (see that case's review, risk 4).
2. **Tools used but not named (A1).** This working log names `arpleg`, `qmark`, `rcdiff`,
   `ckcase` and `sudotool`. It does **not** name `cfg.py`, `ckcon.py`, `ckyn.py`,
   `ckreload.py` or `rc2cfg.py` -- the whole configure, confirm, reload and `.cfg` path. The
   final log's tool line was written without them.
3. **No authored step text, so the step boundaries are the tester's**, anchored to the **IP
   Feature Overview Guide C613-22007-00 REV I, p.17**. Same risk and same fix as T44378: put
   the guide page in the STEP heading, not only in the preamble, so a re-grader can check the
   decomposition against its source.
4. **The marker defect (A2) did not reach this case** -- every flow here used high ports
   (7777, 7778), which scapy leaves as `Raw`. Worth stating explicitly so nobody re-opens
   these counts: they were never at risk.
5. **The ACL claim rests on an inversion, not on a single leg** -- which is the strong form.
   Leg 4 alone would have been consistent with "the ACL is present but not consulted"; leg 5
   inverting the permit and seeing the forwarded source swap is what rules that out. Keep this
   pattern for any filter-bound feature: **a bound filter is only proven by changing it.**

## Next run: expected outputs

Addresses: host eth3 **10.38.22.40** and **10.38.22.42** (the two sources), DUT vlan10
**10.38.22.34/27** (ingress SVI), DUT vlan48 **10.38.22.66/27**, destination subnet broadcast
**10.38.22.95**, host eth4 **10.38.22.65** (control target). DUT SVI MAC `e0:1a:ea:d4:70:43`.

| step | what this bench gave |
| --- | --- |
| 0 (surface) | `ip directed-broadcast [<1-99>\|<1300-1999>\|WORD]` exists in **interface** configuration mode. The optional argument is a standard or named ACL. |
| 1 (baseline OFF) | Off by default: all 10 directed broadcasts were **delivered to the DUT** -- in the eth3 capture, addressed to its SVI MAC, so the DUT had them and chose not to forward -- and **none** reached the destination subnet. The routed ICMP control arrived **5/5** in the same capture, proving the DUT was routing and the eth4 instrument was alive. |
| 2 (wrong interface) | **O-19 (process lesson).** `ip directed-broadcast` on the **INGRESS** interface (vlan10) is **completely inert**: byte-identical frames **0/10** forwarded. Nothing in `show running-config` says so, there is no warning and no `show` command reveals it. This is the single easiest thing to get wrong in this feature and a wrong configuration reads as a product failure. Configure it on the interface facing the **destination** subnet. |
| 3 (right interface) | The same command on **vlan48**, nothing else changed: **10/10 forwarded**, and -- the point of the case -- **flooded as a link-layer broadcast**. eth4 holds 15 frames; egress Ethernet destination is `ff:ff:ff:ff:ff:ff` while the **IP destination is still 10.38.22.95** and the IP source and both UDP ports are unchanged. **The translation is in the Ethernet header alone. A tester looking for a rewritten IP destination will not find one.** |
| 4 (ACL) | `access-list 1 permit 10.38.22.40 0.0.0.0` + `ip directed-broadcast 1` on vlan48. Both sources sent in **one** capture: the permitted source (.40:7777) forwarded **5/5** as a link-layer broadcast; the denied source (.42:7778) **0/5** -- the standard ACL's implicit deny. The ACL filters on the packet's **SOURCE** address. `show access-list 1` reads back `4 permit 10.38.22.40`. |
| 5 (invert) | `no access-list 1` + `access-list 1 permit 10.38.22.42 0.0.0.0`, same frames: the result **follows the ACL and not the source** -- .42 now forwarded 5/5, .40 now 0/5. The ACL is consulted **per packet**, not merely present at bind time. |
| 6 (reload) | Login seen **60 s** after `reboot system? (y/n): y` (`platforms/x960.md` §7.9 gives 60-68 s). **Expect `port1.0.48 Designated Learning` on the first STP read** -- take a confirming read. The interface command, the ACL binding **and** the ACL contents all survived, and the dataplane behaviour with them. |
| 7 (removal) | **`no ip directed-broadcast` removes the ACL-bound form `ip directed-broadcast 1` without needing the argument** -- the negation need not mirror the positive form. With the command and the ACL removed, the destination subnet sees nothing again. Teardown diff empty. |

## Next run: scripts

Existing -- reuse, do not rebuild:

- **`tools/arpleg.py`** via `tools/tb sudotool <box> <scratch> arpleg`, with
  `--tag <leg> --out DIR --iface eth3 --watch eth4 --udp "10.38.22.95:7777@10.38.22.40,
  10.38.22.95:7778@10.38.22.42" --icmp 10.38.22.65 --sender 10.38.22.40
  --gw-mac e0:1a:ea:d4:70:43 --count 5`. The **`@SRC`** form was added in this case and is what
  lets a permitted and a denied source share one capture -- the single most useful thing for
  grading any source-filtered feature, because it removes the "were the two legs really
  identical?" doubt entirely.
- **`tools/tb cfg` / `tools/tb ckyn` / `tools/tb ckreload` / `tools/rc2cfg.py` /
  `tools/rcdiff.py`** -- the configure, confirm, reload and teardown-diff path. **Name them in
  the working log** (A1).
- **`tools/tb ckcon ... "show spanning-tree brief"`** as a confirming read after every reload.

Proposed (not built):

- **`tools/aclleg.py --iface vlan48 --acl 1 --permit <src> --sources <srcA,srcB>
  --dst 10.38.22.95 --count 5 --invert`** -- run the permitted/denied pair in one capture, then
  invert the ACL and re-run, printing the 2x2 matrix that is the whole proof. This case did it
  in three calls (#135-#137) and the pattern applies to every ACL-bound feature in the
  campaign.
- **`tools/tb postreload --console u2 --expect-stp-forwarding port1.0.10,port1.0.48`** -- wait
  for login, then poll STP until the named ports are Forwarding (or time out), so no reload leg
  ever measures against a Learning port. Closes accuracy risk 1 for the whole campaign.
- **S3 `tools/toolsused.py`** (see `../REVIEW.md`) -- would have closed accuracy risk 2.

## Next run: references

- **IP Feature Overview Guide C613-22007-00 REV I, p.17 (IP Directed Broadcast)** -- the source
  of every step here. Under `Feature Overview Guides/`; convert with `pdftotext -layout` into
  the scratchpad, grep, read the page. The guide's phrase that matters is "the interface via
  which the switch connects to that destination subnet" -- that one clause is O-19.
- `platforms/x960.md` **§7** for the IPv4-services material and **§7.9** for the reload window;
  the three measured platform facts in this case's working log (egress IP destination
  unchanged, ACL filters on source and is consulted per packet, `no ip directed-broadcast`
  needs no argument) are §7 material.
- `T44181.log` **TOPOLOGY AS TESTED** -- the underlay, both host NIC MACs and addresses, and the
  DUT clock offset. This case cites it rather than re-capturing.
- `T44182.log` **CAVEAT** -- the scope actually proven (one ingress subnet, one directly
  connected destination subnet). Anything outside it is unproven, not false.
- `T44378-review.md` -- the sibling relay case; its `--udp` arguments and leg shape are the
  same instrument.
- `../REVIEW.md` **A1-A6**.
