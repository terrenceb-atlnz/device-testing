# T47201 process review -- bfd-vrrp-2026-10-16T1406
Reviewed 2026-10-19 by /create-logs from `a0fe415a0d5fbb48a.output` and the working files.

## Token usage
| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 97 | 194 | 140,408 | 16,869,029 | 1,986 | 114 | 40m 45s | 83,570 |

**This is the campaign's most expensive case to think through, and its verdict is UNSUPPORTED.**
1,986 output tokens and 114 tool calls are both campaign highs, and 16.9 M cache-read is the
second highest of ten cases. That is the opposite of the intuition that a case with nothing to
configure is cheap. It is worth stating plainly for the next tester: **proving an absence costs
more probing than proving a presence**, because a presence is proved by one positive reading
and an absence has to be proved by enumerating a surface and then ruling out every innocent
explanation for the silence.

## Process taken
1. Calls 20-26 -- gate: case folders created, `tb scratch`, `tb template`, `tb peek` on u2/u3/u5,
   then `tb probe` with the Test Engineer's facts (PDU 10.36.230.212, outlets u2=1/u3=7, names
   u2=swi_d, u3=swi_b, u5=swi_a).
2. Calls 27-31 -- `show running-config` from all three consoles **redirected into `work/pre-*.log`**,
   then read back only through `grep -n -E 'vlan10|vlan48|ip address|service|...'`. The right
   pattern; none of the three dumps entered the context whole.
3. Call 32 -- `ckcase AWPTCM-T47201 AWPTCM-T47873` in ONE fetch for both cases of the group.
4. Call 34 -- `ckcase --raw-steps` for T47201: the `steps` array holds **one completely empty
   step**. That is a real answer rather than a tooling failure, and the final log declares it.
5. Calls 35-36 -- `pdftotext` on the RIP Feature Overview guide already in `Feature Overview
   Guides/`, into the scratchpad.
6. Calls 37-38, 40-45 -- ToolSearch + WebFetch of the **VRRP** guide and six reads of its text.
   This is T47873's authority, fetched here. See "Wasted input".
7. Calls 47-52 -- read and extend `tools/arpleg.py` with `--show-ttl` and per-spec `%L2DST`.
   Also T47873's instrument, built here.
8. Calls 55-58 -- setup staged and committed; `spanning-tree priority 0` and the port/VLAN build
   on both units.
9. Calls 62-65 -- STEP 1, the service gate: `service bfd` and `service rip` sent **alone, each in
   its own batch ~10 s apart**, each gated on `show process | include <daemon>` rather than on
   the absence of an error. bfdd pid 4391, ripd pid 4416.
10. Calls 66-70 -- STEP 2, the five `tb qmark` probes (global `bfd ?`, global `ip ?`,
    `config-router` `bfd ?`, the complete `config-router ?` list, `neighbor <addr> ?`), each
    self-testing before it fired.
11. Calls 71-72 -- a cross-group read of `igp-2026-10-15T1747/T43856` to recover the loopback /
    192.168.70 addressing used by the prior RIP case.
12. Calls 73-83 -- STEP 3: RIP configured on both units, then the dataplane A/B turned by one
    `network` statement on the far router, measured with `arpleg` (`L1-rip-on`,
    `L2-rip-71-advertised`).
13. Calls 84-88 -- STEP 4: `bfd peer` on both units with **no routing-protocol binding at all**,
    read from both ends' session state and from a `tcpdump` of the wire; a `tb poll` armed on u2.
14. Calls 89-103 -- STEP 5: the silent neighbour failure (`shutdown` on swi_b's vlan61 SVI), with
    an epoch stamp taken immediately before it, then `awk` extraction from the poll file rather
    than reading the poll file back.
15. Calls 104-118 -- STEPS 6-7: RIP v1 forced, the version read off the wire, the probe of STEP 2
    repeated in `config-router` mode, and the identical failure reproduced.
16. Calls 119-130 -- teardown with `no service bfd` ordering corrected (see O-34 below), and the
    `.cfg` capture at call 126.
17. Calls 97-98 -- `tools/README.md` updated for the two `arpleg` flags.
18. Calls 131-133 -- `work/run1.log` assembled, committed, `RESULT T47201 UNSUPPORTED` to the
    sentinel at 05:55:26.

## Wasted input
- **The four largest reads in this segment all belong to the NEXT case.** The VRRP guide extract
  (4,838 + 3,890 + 3,707 chars, calls 41/42/44) and `tools/arpleg.py` (4,077 chars, call 48) are
  T47873's authority and T47873's instrument. They were read here because the tester front-loaded
  them, which is good practice on its own -- but it means **`case_tokens.py` bills them to
  T47201**, and any comparison of the two cases' costs is distorted by roughly 16 k chars of
  read-back plus whatever reasoning sat on top of it. Not waste; a measurement artefact to know
  about.
- Beyond that, little to name: 83,570 chars over 114 tool calls is ~733 chars per call. The
  console reads were redirected to `work/` files and narrowed with `grep` / `sed` / `awk`
  (calls 31, 76, 91-94, 96, 101, 103, 119, 129) rather than read back whole. **Three separate
  `show running-config` captures (calls 121, 125, 130) each went to a file first.** This case is
  a good model for that discipline.

## Repetition
- **No command was issued verbatim twice** in this segment (`case_tokens.py` reports no repeats).
- The one real repetition is structural and was deliberate: the STEP 2 CLI probe was re-run under
  RIP v1 at call 112 and again at 118. That is STEP 7's evidence that the gap is not a property
  of one RIP version, so it earns its cost.
- Calls 71-72 re-derive the prior RIP group's loopback and 192.168.70 addressing from its final
  log. That belongs in `platforms/x960.md` §7A so the next RIP case reads it once (see
  References).

## Accuracy risks
- **The `.cfg` files are a reconstruction, not a capture.** The log's own PROVENANCE block says
  the capture point before step 1 was missed, so `swi_d.cfg` / `swi_b.cfg` were produced by
  **re-applying the case's setup verbatim after the measurements**, with the BFD session
  confirmed `up` and both RIP routes confirmed installed at the moment of capture. The
  configuration is the configuration the case ran under, and the log declares it -- but it is one
  inference away from a direct reading. **Closing evidence: capture `show running-config` per
  device immediately after setup and before STEP 1**, as its own numbered artefact.
- **O-33 -- a BFD state change writes NOTHING to the device log.** `show log | include bfd` and
  `| include BFD` across four measured up/down transitions returned only IMISH command echoes.
  So the ~1.4 s (v2) and ~1.1 s (v1) detection figures, and the ~171.6 s RIP hold, do **not** rest
  on a device timestamp: they rest on a polled `show bfd peer` whose `Uptime:` / `Downtime:`
  field is 1-second resolution and is **lost the moment the session re-establishes**. The tester
  handled this correctly (an epoch stamp taken immediately before the stimulus at call 89, and a
  `tb poll` running across it), and the quoted figures carry `~`. The next tester must know that
  **polling is the only instrument for BFD timing on this platform** and must arm it *before* the
  stimulus; there is no way to recover a missed transition afterwards.
- **The UNSUPPORTED verdict's own guard is sound and should be copied.** It does not rest on one
  refused command. It rests on five probes **taken with both daemons already running** (so it is
  not the service gate), a vendor guide with **0 occurrences of "bfd" in 1045 lines** (so it is
  not an undocumented command), and **`ip ospf bfd` accepted by the same parser on the same
  interface in the same minute** (so the capability exists in this image and is simply not wired
  to RIP). That shape -- *enumerate the surface with the daemon up, then produce a positive
  contrast on the same box in the same minute* -- is the reusable method, and it is why this case
  cost what it did.
- **O-34 -- `no service bfd` silently drops the console out of configuration mode.** Reproduced on
  both devices, twice each: the prompt goes `awplus(config)#` -> `awplus#` with nothing sent in
  between, so the following `end` fails with `% Invalid input detected at '^' marker.` and
  `cfg.py` abandons the rest of the batch. **It must go LAST in any stop-on-error batch.** A
  teardown that puts it mid-batch half-completes and reads as success.

## Next run: expected outputs
| step | value / CLI line this bench gave |
| --- | --- |
| 0, BFD off | `% BFD protocol daemon is not running` -- **no licence clause** |
| 0, RIP off | `% RIP protocol daemon is not running or feature license is not available` -- the missing half of that sentence is how you tell service-gated from licence-gated without `show license` (O-32) |
| 1 | `service bfd` then `service rip`, each alone ~10 s apart; `show process \| include bfdd` -> pid 4391, `ripd` -> pid 4416 |
| 2 | `bfd ?` (global config) -> `echo` / `peer` / `profile` only; `ip ?` -> 32 completions, none `bfd`; `config-router` `bfd ?` -> `% Unrecognized command`; `config-router ?` -> **24 commands, no `bfd`**; `neighbor <addr> ?` -> takes no suffix |
| 2, contrast | `ip ospf bfd` **accepted** on the same interface in the same minute |
| 2, guide | `RIP_Feature_Overview_Guide.pdf`: **0 occurrences of "bfd" in 1045 lines** |
| 4 | session verb is **`show bfd peer`** -- `show bfd session` does NOT exist, it answers `% Invalid input detected at '^' marker.` (O-31) |
| 4 | negotiated **3 x 300 ms**; on the wire UDP/3784, TTL 255, TOS 0xc0, 52 bytes, bidirectional |
| 4 | this build's `tcpdump` mislabels BFD as `BCM-LI-SHIM: direction unused, pkt-type unknown ... (invalid)` -- the frames are correct, only the dissector is wrong (O-35) |
| 5 | BFD detects a silent neighbour failure in **~1.4 s** (v2); RIP keeps the dead prefix `Known via "rip", distance 120, metric 2, best` for **~171.6 s**; counted dataplane leg **0/5** on both subjects with its in-leg instrument at **5/5** |
| 6 | v1 on the wire = classful entries to the **subnet broadcast at TTL 64**; v2 = prefixed entries to **224.0.0.9 at TTL 1** |
| 7 | reproduces under v1: detection **~1.1 s**, `bfd` still `% Unrecognized command` in `config-router` |
| setup trap | `ip address <a>/<m> secondary` on `lo` is refused `% Configure primary first lo` if `lo` has no primary -- and **the two units differed**: the DUT needed it WITHOUT `secondary`, swi_b WITH (O-36) |
| teardown | `no service bfd` **LAST** (O-34) |

## Next run: scripts
Nothing was hand-built for this case; `tb qmark` / `cfg` / `ckcon` / `poll` / `arpleg` carried all
of it. Two proposals, both drawn from what this case did by hand:

- **`tools/clisurface.py`** -- the STEP 2 method as one call, since it is what every
  "does this binding exist?" case needs and it is what cost this case its 114 tool calls.
  `clisurface.py --box tbNNN --scratch TAG --console uN --baud B --require-daemon "bfdd,ripd"
  --probe "config:bfd" --probe "config:ip" --probe "config-router(router rip):bfd"
  --probe "config-router(router rip):" --probe "config-if(interface vlanN):neighbor 10.0.61.2"
  --contrast "config-if(interface vlanN):ip ospf bfd" --out DIR`
  It would refuse to run until `show process` proves every `--require-daemon` is up, fire each
  `--probe` through the existing `qmark.py` self-test, run `--contrast` as a real (accepted)
  command on the same interface, and print one `PRESENT` / `ABSENT` line with every probe's
  verbatim output beneath it. Five hand-written `tb qmark` calls (66-70, plus 112 and 118 for the
  v1 repeat) is what it replaces, and it enforces the daemon-up precondition that the whole
  verdict depends on.
- **`tools/guidegrep.py`** -- `guidegrep.py "<guide filename or substring>" <term> [<term> ...]`.
  `pdftotext`-caches a `Feature Overview Guides/` PDF into the scratchpad once, then reports hits
  **and the total line count**, because "0 hits in 1045 lines" is the evidence form, not "0 hits".
  Calls 35-36 did this by hand, and T47873 needed the same thing for "alternate" / "checksum".

## Next run: references
- `platforms/x960.md` §7A -- the service gate for `bfd` / `rip`, including that start is
  asynchronous and stop needs a reload.
- Memory `awplus-service-gated-routing-daemons` -- `service <proto>` before `router <proto>`.
- Memory `bench-scripts-stop-on-cli-errors` -- why O-34 and O-36 truncate a `cfg.py` batch.
- `tb277/x960/igp-2026-10-15T1747/T43856/T43856.log` -- the RIPv1 vs RIPv2 wire signatures and the
  loopback / 192.168.70 addressing. Calls 71-72 re-derived these; read them instead.
- `tb277/x960/CAMPAIGN-QUEUE-2026-10-16T1406.md`, entries **O-31 to O-36** -- every CLI trap this
  case hit, written up with its reproduction.
- `Feature Overview Guides/RIP Feature Overview and Configuration Guide - RIP_Feature_Overview_Guide.pdf`
  -- in the repo; do not re-fetch.

---
Group-wide findings are in [REVIEW.md](../REVIEW.md) and are not repeated here.
Recommendations are the reviewer's; findings cite the transcript call or working-file line they come from. A review never changes a verdict: a doubt about one goes to the Test Engineer.
