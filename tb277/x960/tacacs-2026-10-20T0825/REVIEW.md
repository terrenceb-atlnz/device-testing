# Group process review -- tacacs-2026-10-20T0825

Reviewed 2026-10-20 by /create-logs from the tester's transcript and the working files.

## Token usage

| segment | calls | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T33411 | 59 | 100,760 | 11,138,633 | 644 | 59 | 1,898 s | 54,993 |
| T33410 | 32 | 51,032 | 8,716,427 | 267 | 32 | 1,562 s | 21,600 |
| T33412 | 28 | 48,456 | 9,409,040 | 257 | 28 | 1,278 s | 20,107 |
| overhead | 36 | 141,467 | 4,037,256 | 2,531 | 48 | 454 s | 161,136 |
| **total** | **155** | **341,715** | **33,301,356** | **3,699** | **167** | **5,192 s** | **257,936** |

**Group overhead: 12.1 %.**

Cost per call rose across the group: T33411 averaged 189 k cache-read per call, T33412 averaged
336 k — **1.8x** for the same kind of work, purely because the context had grown.

## The finding worth keeping beyond this group

**A chained `| exclude` after `| include` is silently swallowed by AW+.** T33411 measured it:

```
awplus# show log | include kernel|exception|crash|restart|Unexpected | exclude IMISH
  2026 Oct 19 23:16:50 user.notice awplus IMISH[32687]: [SCRIPT]snmp restart isis
```

No `% ` error, the command succeeds, and the IMISH lines are still there. AW+ takes the whole
string after `include` as one alternation pattern, so ` exclude IMISH` becomes another
alternative inside the include regex.

**This is the worst of the three possible outcomes**, because the output looks filtered and is
not. It directly affects the STANDING-ORDERS §8 health read, which has exactly that shape. This
group worked around it by filtering box-side after the read. Recorded in
`platforms/x960.md` §7G and in STANDING-ORDERS §8.

## Findings that apply to the whole group

1. **T33412's STEP 8 table was built from another case's output.** Five of its twelve rows had
   no source in T33412's own evidence and were dropped from the final log. A table that spans
   cases belongs in the group review or the platform file, not in one case's deliverable.
2. **T33411's most useful conclusion is weaker in the deliverable than in the evidence.** The
   stale `Last login:` is explained by AW+ lastlog being keyed on a recycled UID, but that
   mechanism is sourced only through another campaign's working log. The final log keeps the
   measurement and drops the mechanism. **Re-source it in a case of its own and it becomes a
   real finding.**
3. **A step verdict of `PARTIAL` was used**, which is not in the §4 step vocabulary
   (`done`, `PASS`, `FAIL`, `UNSUPPORTED`, `NOT RUN`). It was preserved rather than re-graded.
   Either the vocabulary grows or the step reads `PASS` with the gap named.
4. **The group's instruments were the right shape.** Three independent ones on every leg: the
   DUT's own `show`, the server's accounting file read in a bounded window with
   `tools/filewin.py` so that zero records is a measurement, and the wire via
   `tools/tcpflow.py`. That is what makes the NOT MEASURED items credible as measurements
   rather than omissions.

## Next run

- Reboot persistence is NOT MEASURED for all three cases, because the layer 3 underlay is
  running-config only. One decision — whether the underlay may be written to startup-config —
  unblocks persistence for the whole campaign.
- Enable authentication via TACACS+ (S1599.1.011-016) was never measured. It needs a
  recoverability plan before it is attempted.
