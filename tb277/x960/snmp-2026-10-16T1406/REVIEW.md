# snmp-2026-10-16T1406 -- process review
Reviewed 2026-10-19 by /create-logs from `a87c820765d559dd7.output` and the working files.
Per-case reviews are in each case folder as `<id>-review.md`.

Group A of the 2026-10-16 tb277 campaign: one case, T43870 IPv4_SNMP - SNMPv3, PASS.
DUT swi_d (AT-x960-56YSQ, `sin_x96056-20261012-24`) on /dev/u2; swi_b and swi_a were opened by
the two probe gates and by nothing else, and no PDU outlet was operated.

## Token usage

| case | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T43870 | 50 | 100 | 287,019 | 7,667,530 | 491 | 52 | 26m | 52,979 |
| **overhead** | 27 | 54 | 76,756 | 2,372,141 | 280 | 34 | 4m | 100,548 |
| **total** | **77** | **154** | **363,775** | **10,039,671** | **771** | **86** | **31m** | **153,527** |

Campaign-wide: **10 cases, 599 calls, 126.0 M cache-read, 4.7 h of case wall time**, of which
**9% is group overhead** rather than case work. The comparable campaign on this bench a day
earlier (2026-10-15) ran **46%** overhead. That is the single biggest process improvement in
the record and it is worth being explicit about why: the 2026-10-15 run paid for triage, gates,
rules-reading and instrument-building inside its first group; the 2026-10-16 campaign inherited
a proven bench, a proven `tools/tb`, and a `REVIEW.md` from that campaign which this group's
tester read before it started anything (overhead call #9). The review loop closed, and it is
worth roughly a third of a campaign.

This group is 8.0% of the campaign's cache read while carrying 12.9% of its calls -- a cheap
group that did a lot of work.

### This group's own overhead

27 calls, 2.37 M cache read (1.9% of the campaign), 100.5 kB of tool output -- nearly twice the
case's own 53 kB. It is small in tokens and large in reading, and it breaks down as:

| what was read | calls | chars |
| --- | ---: | ---: |
| `CAMPAIGN-QUEUE-2026-10-16T1406.md` (504 lines, the triage for all ten cases) | 5 | ~37,000 |
| `tools/README.md` + `tb --help` | 4 | ~19,700 |
| `logged-output.md` §2-§3 | 1 | 8,852 |
| `STANDING-ORDERS.md` §§ | 1 | 5,825 |
| `TESTBOX-ACCESS.md` | 3 | ~7,800 |
| prior campaign's `arp-2026-10-15T1747/REVIEW.md` + `SESSION-HANDOVER-2026-10-16.md` | 2 | ~9,100 |
| gates: precheck, scratch, template, peek, probe | 6 | ~1,600 |
| ck.db memory + building and proving `tools/ckcase.py` | 5 | ~5,900 |

Findings from the overhead:

1. **Read-then-reslice is the overhead's dominant waste, at three scales.** `TESTBOX-ACCESS.md`
   was `cat`-ed whole (#11, 2,188), *then* its headings grepped (#12), *then* three ranges
   sliced (#14, 4,091) -- 3 calls and 7.8 kB where #12 + #14 alone (5.7 kB) would have done.
   The queue was `cat`-ed whole (#0), then heading-grepped (#2), then read in three ranges
   (#4-#6). `tools/README.md` was heading-grepped (#8), sliced twice (#13, #15), and then
   heading-grepped and sliced *again* at write-up time (#77, #78). The right pattern is the one
   the tester used second each time and first never: index by headings, then slice. Doing both
   costs the whole file twice. Roughly 12 kB recoverable across the three files.
2. **`tools/tb` did not know tb277's python -- now fixed, permanently.** tb277's `python3` is
   3.6, so the first `tb hostname`/`tb precheck` calls failed (#17-#19) until the tester patched
   `BOX_PY = {'tb105': 'python3.8', 'tb277': 'python3.8'}` in `tools/tb` (#20). That patch is
   committed; the next tester on tb277 pays none of those four calls. Any *new* box will hit it
   again -- the symptom is a syntax error or empty output from an otherwise valid `tb` verb.
3. **One call lost to `tb put`'s argument order** (#29 omitted the box: `tb put tools/ckcase.py
   ckt1406`), corrected at #30. The usage line is in `tools/README.md` §`tb`; every `tb` verb
   takes the box first.
4. **`tools/ckcase.py` was built here and is the campaign's best overhead purchase.** Memory
   `ckdb-case-lookup-by-title` says AWPTCM ids do not exist in ck.db; the tester checked (#26),
   found `zephyr_cases` keyed exactly on `AWPTCM-T43870`, built the tool (#28), proved it
   (#31-#32, 2.4 kB of real authored procedure) and documented the memory's obsolescence in the
   README entry. Five calls, and it gave this case and four others in the campaign a real
   authored procedure instead of a designed-from-scratch one. **The memory needs updating.**
5. **Gates were clean and cheap**: precheck, scratch, template, peek and probe cost ~1.6 kB
   total and all passed. Nothing to improve.
6. **Keep doing #9.** Reading the previous campaign's `REVIEW.md` before starting cost 4.6 kB
   and is visible in this group's numbers.

## Findings that recur beyond this case

Only one case ran in this group, so nothing is yet *observed* to recur. Two of its per-case
findings will apply to any credentialed or config-heavy case, and are stated once here:

- **Credential boilerplate is both a cost and an accuracy hazard.** The v3 flag block was
  re-typed in full 17 times inside one case. The passwords in this case are literally
  ``!#$%&'()*+,-./[\]^_` `` and `:;<=@{}~0123456789ab` -- shell metacharacters end to end --
  and the tester spent a mid-case patch (#47) turning `snmpq.py`'s password *redaction* into a
  *fingerprint* (`<PASS len=20 sha1=0eeef6a537>`) precisely so a quoting accident could be told
  apart from a real authentication failure. That was the right call and it is now documented in
  `tools/README.md` §`snmpq.py` "Password handling". The next step is to stop re-typing the
  secret at all: a `--profile`/`--creds-file` option on `snmpq.py`, or net-snmp's
  `SNMPCONFPATH` + `defAuthPassphrase`.
- **Gate every config-driver call on its own `% ` lines.** Three calls and ~75 s went on the
  removal step because `% Invalid input detected at '^' marker.` scrolled past in a `tail -35`
  (#66-#69). Memory `bench-scripts-stop-on-cli-errors` already says this; the mechanical form
  is to append `grep -nE '^% |Invalid input' $W/<log>` to every `tb cfg`/`tb ckcon` call, or to
  make `tools/tb cfg` exit non-zero when its captured output contains one.

## The cost model this group demonstrates

T43870 was the **cheapest-but-one** case of the ten by cache read, yet read back **51.7 kB** of
tool output -- the **third highest**. Those two facts are not in tension, and the resolution is
the most reusable thing in this review: **cost is accumulated context multiplied by API calls,
not the volume of output read.** The case averaged 153 k of context per call against the
campaign's 210 k because it ran as one near-linear pass of 52 calls, every bench command wrote
its full output to `work/` and read back only a `grep -E '^(---|RESULT|GRADE|rc=)'` slice, and
no large document was re-read after the gates. Reading a lot *once*, in small per-call slices,
is cheap. Re-reading a little, many times -- which is what the overhead's read-then-reslice
pattern does -- is not.

## Accuracy risks at group level

Carried from `T43870/T43870-review.md`, where each has its closing evidence:

1. The log's `port1.0.10` label ("default VLAN 1, no per-port configuration") is inferred from
   the *absence* of a stanza in `swi_d.cfg`; one `show running-config interface port1.0.10`
   closes it. No graded leg depends on it.
2. The STEP 5 walk and the STEP 11 wire decode exist in full only in `work/s5-steps4-5.log` and
   `work/s11-wire-decode.log`, which this step deletes; after that the log's transcription is
   the only record. Verified against the dumps before deletion -- the log's "32 varbinds" is
   exact.
3. The STEP 11 pcap was left in the box's tmpfs at `/tmp/ckt1406/snmpwire.pcap` and is gone.
   Captures must be fetched and chowned into `work/`.
4. **O-9 is a defect in the Zephyr case text and the next run will hit it again.** The authored
   precondition never defines the view its group reads, and step 6's OID `1.3.6.1.1.2.1.1.5` is
   not a path to sysName. The one line that fixes the *run* is
   `snmp-server view MOSTmostMOSTmostMOST 1.3.6.1.2.1.1 included` after the authored block, with
   step 6 read as `1.3.6.1.2.1.1.5`. The fix that stops it recurring is in AWPTCM-T43870 itself.
5. F-12 (SNMPv3 GetNext at a MIB-view boundary gets no response, RFC 3416 §4.2.2) rests on
   measured output with instrument controls either side -- **no accuracy risk**. It is a product
   finding for a developer.

## Next group / next run

- Run `tools/ckcase.py AWPTCM-T<id>` on the box first, before designing any step.
- Use `tools/snmpq.py` and `tools/snmpwire.py`; both are proven on this platform and documented.
- Read `bench-setup/tb277/bench-state.md` for host-NIC and link facts instead of `tb nics`.
- Index a reference by headings, then slice it. Never both `cat` it and index it.
- The per-case expected-output table in `T43870/T43870-review.md` has every value this bench
  gave, step by step, including the `no snmp-server <object> <NAME-ONLY>` removal syntax and the
  300 s / 5-failure SNMP user lockout.
