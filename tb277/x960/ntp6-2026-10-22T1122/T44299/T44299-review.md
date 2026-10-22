# T44299 process review -- ntp6-2026-10-22T1122
Reviewed 2026-10-22 by /create-logs from `agent-aeb5642c4fb54bf61.jsonl` and the working files.

## Token usage

`tools/case_tokens.py --find ... --cases T44299` found the tester's transcript but printed
`no RESULT line found for: T44299`, so it could not split the case out and reported every
call under `overhead`. The tester sent its RESULT to the sentinel with `SendMessage`, which
the splitter does not see. This group held exactly ONE case, so the overhead row below IS
the case plus its group overhead.

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 242 | 484 | 238,327 | 42,248,268 | 3,519 | 241 | 2,876 s | 144,707 chars |

Derived: about 174,580 cache-read tokens per API call, and 2,876 s of wall time for 8 steps.

## Process taken

1. Calls 1-5: read the campaign queue (21,760 chars), the STANDING-ORDERS and
   logged-output.md headings, STANDING-ORDERS sections 7-8, platforms/x960.md section 7H.5,
   logged-output.md lines 112-270, and the `tb` / `ntpc.py` / `ntpwire.py` entries of
   tools/README.md.
2. Calls 6-10: read the previous NTP group's folder listing, its two review files, its run
   `.setup`, and two ranges of a prior final log, to reuse the method.
3. Calls 11-13: the gate -- `tb precheck`, `tb scratch`, `tb template`, `tb peek`.
4. Call 14: wrote this group's run `.setup` (swi_d only).
5. Calls 15-21: probe, `bench_probe.py diff` (MATCH), reverted the regenerated
   `bench-state.md`, and wrote the bench-setup section into the campaign queue.
6. Calls 22-27: read the box's NICs, its ntpd and its clock; proved the instrument by
   running `ntpc.py` against the box's own server BEFORE involving the DUT; took the setup
   reads.
7. Call 28: `tb health ... --label before`.
8. Calls 29-30: applied the setup (the IPv6 address on vlan10); saved `swi_d.cfg`.
9. Calls 31-40: STEP 0 -- capture started in the background, ping inside the window, writer
   confirmed exited, `ntpwire` decode.
10. Calls 41-55: STEPS 1-3 -- capture first, then the configuration, then the two association
    reads, then the decode of the deciding capture.
11. Calls 56-114: STEP 4 -- `tb qmark` for the `clock set` form, the 480 s capture, the
    injection, the 100 s wait, the client restart, `show log | include chronyd`, the decode.
12. Calls 116-141: STEP 5 -- capture first, removal, ping inside the window, decode.
13. Calls 136-165: STEPS 6-7 -- an orchestrator script in the scratchpad did `write`,
    `reload`, ping-to-ready and the first reads in one process; then `tb health --label after`.
14. Calls 227-237: the persistence decode, teardown, `rcdiff`, the post-run probe, the
    console logout, and the two raw health samples pulled off the box.
15. Calls 238-241: queue update, `SendMessage` to the sentinel, final tree check, hand-back.
16. Seven `git commit` calls were made along the way, one per finished step group.

## Wasted input

1. **116 of the 241 tool calls were pure waiting, and nothing else** -- 104 of them the
   identical `sleep 5; echo .`, plus `echo idle`, `echo idle2`, `echo waiting`, `echo "."`,
   `sleep 2; echo waiting`, `sleep 3; echo z`, `sleep 1; echo ok`. That is 48% of every call
   in the case. Each one re-reads the whole conversation cache, about 174,580 tokens, so the
   waiting alone cost on the order of 20.3 million cache-read tokens -- roughly half of the
   case's 42.2 million. This is by far the largest single waste in the case, and it bought
   nothing: the captures were already time-bounded and the results were already being written
   to scratchpad files.
   - The narrower form is the one the tester used correctly three times and then stopped
     using: `Monitor` with an until-loop on the output file (calls 64, 82, 90), and
     `run_in_background` with a single wake-up when the job exits. One `Monitor` call
     replaces a 100-call `sleep` chain.
2. **Call 1 read the whole campaign queue, 21,760 chars**, to find a one-case group. The
   queue's Group A section and the Results row for T44299 are a few hundred characters.
   `sed -n '/^## Group A/,/^## /p'` would have done.
3. **Calls 9 and 10 read 195 lines of a prior final log** to copy its shape. The review file
   read at call 7 already carried the "expected outputs" and "scripts" sections for the same
   feature, so the log read was largely a second copy of the same information.
4. **Call 16 ran a probe with the wrong flag spelling** (`--outlet 1 --name swi_d`) and had to
   be re-run at call 17 with `--outlet u2=1 --name u2=swi_d`. The correct spelling is in the
   `tb` entry of tools/README.md, which call 5 had already read.

## Repetition

1. The `sleep 5; echo .` call, 104 times. See above.
2. `cat .../tasks/<id>.output` was issued repeatedly against the same background task file
   (calls 46, 51, 53, 66, 68, 81, 89, 126, 159, 198) to see whether a job had finished.
   `Monitor` on the file does this in one call.
3. The scratchpad decode file `s4-wire.txt` was read five times (calls 92, 97, 109, 110, 112)
   before it was complete.
4. The probe plus `bench_probe.py diff` plus the `bench-state.md` revert ran twice, once at
   the gate and once after the run. That pair is required by STANDING-ORDERS and is not waste,
   but the revert step (calls 20 and 232) is manual book-keeping that a flag on the probe
   could do.

## Accuracy risks

1. **The case has no authored text in the test-case database.** `has_objective = 0` and the
   single step holds a 53-character empty-JSON placeholder. The objective and all 8 steps were
   designed by the tester before the run. Every verdict therefore rests on steps nobody else
   wrote. The tester wrote the designed steps down before running them, which is the right
   mitigation, but a second reader should confirm the design matches what AWPTCM-T44299 is
   meant to cover. What would close it: authored step text in the database.
2. **The TPS row number is offset from the title.** The title says "(265)" and the matching
   TPS row is 263, "NTP / IPv6 NTP Client". Row 265 is a different case entirely. The tester
   checked this and recorded it. Anyone who trusts the bracketed number will grade against the
   wrong requirement.
3. **Two display behaviours on this platform will make a correct device look wrong to a
   parser.** For an IPv6 server, `Reference ID` prints a 32-bit hash, not the address.
   `show ntp associations` wraps an IPv6 remote onto its own line, so a single-line regex
   matches nothing. Both are measured and quoted in the final log.
4. **The step-4 clock error was 50.914 s, not the 45 s the tester aimed for.** The aim was
   computed from the box's clock a few seconds before the command landed. The tester graded on
   the size the DUT itself measured, and cross-checked it against the DUT's own log, so the
   measurement is sound. A next run should still compute the injection from a timestamp taken
   in the same command that sends it.
5. **The health-after read was tool-reported DIRTY (exit 4) and adjudicated CLEAN by the
   tester.** The reasoning is complete and the raw samples were kept, so the Test Engineer can
   disagree. This is a judgement, not a measurement, and it is the one place in the case where
   a verdict rests on reading rather than on printed output.
6. Nothing in the final log had to be left out for want of a source.

## Next run: expected outputs

| step | what this bench gave |
| --- | --- |
| setup | `vlan10  unassigned` in `show ipv6 interface brief` -- the x960 has NO IPv6 address on the test VLAN until the case adds one |
| setup | `show ntp status`, `show ntp associations` and `show ntp counters` all print COMPLETELY EMPTY output when NTP is unconfigured. No error, no header. An empty read is a state, not a hung command |
| 0 | `ntpwire: ... 28 frames in the capture, 0 NTP packets on port(s) 123`, exit 2 |
| 1 | `ntp server ?` offers `A.B.C.D`, `WORD`, `X:X::X:X`. There is no separate IPv6 command |
| 1 | with IPv6 literals the two `ntp server` lines come back from running-config in the order they were typed |
| 2 | synchronisation about 4 s after configuration when the clock error is about 2 s |
| 2 | `Reference ID : 09D7146F (fd32:b1f0:dff8:1603::1)` -- the hex is a hash, NOT the address |
| 2 | `show ntp associations` wraps the IPv6 remote; the `*` stays on the address line and the numbers print on the next line |
| 2 | `Update interval` settles at about 64.7 s; `reach` climbs 17 -> 77 -> 377 |
| 3 | 8 paired exchanges in 300 s; eight DIFFERENT source ports; the request transmit timestamp is random and is NOT the DUT's clock |
| 4 | `clock set` gives `systemd-journald[140]: Time jumped backwards, rotating.` and puts `show ntp status` at Stratum 0, `Reference ID : 00000000 ()`, Ref time 1970, `Leap status : Not synchronised` |
| 4 | a RUNNING chronyd will NOT undo a hand-set clock. It logs `Backward time jump detected!` and leaves the clock wrong, with `reach 377` all the while. `no ntp server` then `ntp server` restarts the daemon (the pid changes) and it steps within 3 s |
| 5 | after removal, 0 NTP packets in 170 s, and all three NTP show commands empty again |
| 6 | a 63 s cold boot; `ntp server` returns by itself from startup-config; the first poll is 8 s after the login prompt |
| 7 | about 12 s from the login prompt to the clock step, about 20 s to `Leap status : Normal` at Stratum 6; the step size across a reboot was 0.655756 s |
| health | `show cpu` prints `1 second: 0%, 20 seconds: 0%, 60 seconds: 0%`. It NEVER prints an idle percentage on this platform |

## Next run: scripts

- `tools/ntpwire.py` -- already present and catalogued. Decoded all five captures. Exit 2 is
  its deliberate "zero packets" control code, which is a measurement and not an error.
- `tools/ntpc.py` -- already present and catalogued. Used as the instrument control against
  the box's own ntpd before the DUT was involved. Keep doing this.
- `tools/tb` -- `precheck`, `scratch`, `peek`, `probe`, `template`, `ckcon`, `cfg`, `qmark`,
  `capture`, `ping`, `health`, `ckreload`, `tool`, `ps`, `tail`, `waitfor`. No new tool was
  needed for this case and none was left behind in the case folder.
- **Proposed: `tools/tb waitjob <scratch> <file-or-pattern> [--timeout S]`**, a single blocking
  call that returns when a background capture's writer has exited or a scratchpad result file
  is non-empty. This is the one helper that would have removed 116 of the 241 tool calls in
  this case. Until it exists, use `Monitor` with an until-loop, which the tester used three
  times and which worked.
- **Proposed: `tools/tb probe --keep-state`** (or `--no-write`), so a single-console probe does
  not regenerate a multi-unit `bench-state.md` that then has to be reverted by hand. It was
  reverted twice in this case.

## Next run: references

- `platforms/x960.md` section 7H.5 -- the NTP behaviour of this platform, including the empty
  show output when unconfigured and the client's randomised source port. Read it instead of
  rediscovering.
- `platforms/x960.md` section 7G -- `| include` is NEVER chained with `| exclude` on AW+. The
  whole string after `include` becomes one alternation pattern, so the output looks filtered
  and is not.
- `logged-output.md` section 2 "Check the DUT's health, every case" -- in particular point 1,
  which says a new reboot entry caused by the case itself is expected and must be named with
  its time. That is exactly the adjudication this case needed.
- `tools/README.md`, the `tb` entry -- the exact flag spellings `--outlet u2=1` and
  `--name u2=swi_d`. Getting these from the README costs one read; getting them wrong costs a
  failed probe and a re-run.
- The memory `two-console-calls-in-one-block-run-sequentially` -- start the capture FIRST, as
  its own call, before the call that changes the DUT. This case did that for all five captures.
- The memory `tcpdump-nfs-root-squash-capture` -- confirm the writer has EXITED before reading
  a capture's size or count. A zero read from a running writer is not a measurement.
