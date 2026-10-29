# auth-2026-10-29T1304 process review — group A (tb490 swi_dut x980 + tb5 client side)
Reviewed 2026-10-29 by /create-logs from `agent-aa136ab5396975428.jsonl` (the RUN tester), the four
working logs and the four case reviews. This is for the next tester and the Test Engineer; it is not a
deliverable and is never attached in Zephyr.

## Token usage

`tools/case_tokens.py --find ~/.claude/projects/-media-jacobm-mnt-testbox-home-claude-device-testing --cases T33375,T33365,T33366,T33357`

| segment | calls | input | cache write | cache read | output | tool calls | wall s | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T33375 | 14 | 28 | 26,630 | 1,894,840 | 18,097 | 14 | 430 | 11,752 |
| T33365 | 9 | 18 | 16,610 | 1,556,955 | 13,067 | 9 | 247 | 5,541 |
| T33366 | 21 | 46 | 28,780 | 4,348,053 | 16,865 | 23 | 463 | 10,640 |
| T33357 | 17 | 36 | 27,753 | 4,172,199 | 18,163 | 17 | 615 | 16,801 |
| overhead | 78 | 164 | 174,256 | 11,224,767 | 52,858 | 80 | 1,246 | 177,773 |
| **total** | **139** | **292** | **274,029** | **23,196,814** | **119,050** | **143** | **3,001** | **222,507** |

**The per-case split is skewed; read the rows with that in mind.**
- `case_tokens.py` starts a case at its first tool call into `<group>/<id>/`. The T33365 tester
  created `T33365/work/` only after its STEP 5. So about 15 calls of real T33365 work (STEP 0, STEPs
  7/2/3/4/5, the health-before read, 15,671 chars of output) were counted under T33375 or overhead.
  The other cases are likely skewed the same way.
- With bare ids (`--cases 33375,...`) the tool put every call under overhead, because this campaign's
  case folders carry the `T` prefix. Pass the ids as the folder names.
- The transcript stores each tool call twice (a second copy prefixed `cd <repo> &&`).
  `case_tokens.py` already de-duplicates; any ad-hoc segment script must count unique tool_use ids.

**Cache read is 97 % of all tokens.** Tool output read back is only 222 k chars across the group. The
cost is the resident context (135–223 k tokens) carried into every call, not what each call reads.

## Overhead (gates, reading, hand-back): 78 calls, 11.2 M cache read, 1,246 s

- **Rules and references read at the start, in large slices.** The five largest outputs of the whole
  run are all overhead reads: a grep across STANDING-ORDERS / logged-output / x960.md (9,789 chars),
  `sed -n 112,266p logged-output.md` (9,788), the queue ranges (8,993), the case text (8,492), and two
  tools/README.md ranges (8,443). All were needed once; none is a waste on its own, but each stayed
  resident for every later call.
- **Mid-group context growth.** Between T33365 and T33366 the tester read 4 documentation results
  (12,343 chars), wrote and committed `tools/hostnet.py`, and edited `tools/tb`. Every later call
  paid for that. Doing tool-building and doc lookups before the first case (or in a forked helper)
  would cut cache read for the rest of the group.
- **Bench setup** (`.static` with the Test Engineer's names, `apply` on both boxes, re-probe) was
  one-off for these two new boxes and will not recur.

## Findings that recur across cases (said once here)

1. **Working-log captures were filtered at write time.** In all four working logs, several
   `show auth supplicant brief` reads were kept only as grep fragments with no echoed command, and
   two were labelled `awplus#` although the DUT prompt is `x980-CDQ#`. T33366's setup read and its
   `show auth-web-server` reads were cut, and `show ip route` was paraphrased. The final logs label
   those blocks "[the DUT's supplicant table; only these lines were kept]" instead of naming a
   command. **Fix:** capture DUT reads with `ckcon` whole (verbatim), and filter only when
   displaying, never when writing the working log.
2. **The inherited bench rig shapes every auth case.** eth6's own MAC (`00-90-0b-2a-11-c3`) is a local
   RADIUS user in group TWOSTEP, and eth6 arrived web-logged-in as `webuser`. Any case that enables
   `auth-mac` or `dot1x` on port1.0.81 must plan around both. Triage described eth6 as
   "static-authorised"; it was not.
3. **Working logs point to another case's working log for session facts** (clock offset, host MACs:
   T33365 and T33357 refer to T33375's run1.log). That reference breaks when `work/` is deleted. State
   the facts inline, or put them in the queue's group recipe.
4. **Platform facts now recorded once.** `platforms/x980.md` §1.1–§1.4 hold: no `clear auth`
   (use `dot1x initialize interface <port>`); `auth-mac enable` ends existing web sessions; no
   `auth-web-server mode`; entering `crypto pki trustpoint <n>` creates it, even from a help probe;
   the PKI export and `crypto key zeroize <name>` syntax; TFTP to a client behind an Unauthorized
   dot1x port fails. Point the next dispatch at those sections.
5. **Captures started too late.** `arpleg --sniff-only` through `tools/tb sudotool` takes more than
   4 s to start tcpdump; T33366's first S5 capture missed the requests. Gate on
   `tools/tb ps tb5 'tcpdump.*<tag>'` before sending, or add a `--ready` mode that returns once
   tcpdump runs.
6. **Health-before copies the whole `show cpu` process table** (~80 lines) into each working log. The
   `health.py` summary line is enough there; the raw file stays on the box.
7. **The DUT's 150-line log tail shows no `802.1X` / `radiusd` line for cktls** in T33357, where the
   x960 logged both. `health.py`'s by-signature listing also shows only the first timestamp of each
   group, so it cannot show whether an event fell inside the case. Worth a check on the next x980
   auth run.
8. **Each Bash call is a fresh shell.** T33375 ran `rcdiff` twice because `$G` was unset in the second
   shell. Set every variable in the call that uses it.
9. **tb5's wpa_supplicant 2.6 cannot finish EAP-TLS over TLS 1.3**, here as on the x960. The
   `openssl-tls12.cnf` workaround was rebuilt with `printf` for the second campaign running (its 9
   lines are identical to tb277 T9032's copy).

## The three biggest savings for the next run

1. **Smaller resident context.** Do tool-building, doc lookups and rule reading before the first
   case, and dispatch later cases with line ranges, not files. Cache read is 97 % of the cost; the
   T33366 row (2.8× T33365) shows what 1.2× more context and 2.3× more calls do.
2. **Reusable auth-leg helpers** instead of hand-built Bash per leg (details in the case reviews):
   `tools/tb authreset` (`dot1x initialize interface`, wait, whole `show auth supplicant brief`);
   `tools/tb webauth` (login POST then ping, because the HTTP reply looks the same for a right and a
   wrong password); a `tools/tb sniff` / `arpleg --ready` that returns only when tcpdump is running;
   `wpasup.py --tls-max 1.2` in place of the hand-written OpenSSL file; `tools/pkitp.py` for
   trustpoint create / enrol / export / teardown.
3. **Read `platforms/x980.md` §1 first.** About 5 calls in T33365 and the 230 s TFTP stall in T33357
   (37 % of its wall time) were spent finding facts that file now records.

## Left on the bench (from the queue's Issues)

- `tb5:/tftpboot/cktls.p12`: the Test Engineer removes it (root on tb5).
- `tb5:/tmp/auth1304/`: test keys and certificates; tmpfs, cleared at reboot.
