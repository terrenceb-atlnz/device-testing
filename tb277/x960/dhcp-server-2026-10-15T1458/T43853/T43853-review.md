# T43853 process review -- dhcp-server-2026-10-15T1458
Reviewed 2026-10-15 by /create-logs from agent-a355179677143f86e.jsonl and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17 | 34 | 28,341 | 3,952,821 | 7,242 | 17 | 623 s | 10,705 chars |

## Process taken
1. Cleared bindings, applied `lease 120 0 0`, read the pool.
2. Ran the 120-day leg and read option 51 out of OFFER and ACK.
3. Probed the boundary: 120 accepted, 121 and 999 refused.
4. Ran 1-day and 1-hour legs as in-place overwrites in the same run.
5. `no lease` -> the 86,400 default, re-measured on the wire.
6. Staged `ckdhcp.cfg`, reloaded, and re-proved the lease after reboot (this leg also covered the sibling case).

## Wasted input
- `sed -n '220,245p' tools/README.md` returned 1,517 chars to re-read a tool entry the tester had already used in the previous case of the same group. Once per group, not once per case.
- A 2,126-char combined `echo`/console read printed the whole post-config running-config fragment when the graded quantity was a single `lease` line.

## Repetition
- The leg driver was rebuilt from the previous case's by heredoc rather than parameterised. Group finding -- see `REVIEW.md`.

## Accuracy risks
- **One line of the final log is not a verbatim capture.** `work/clear.log` recorded the `show ip dhcp binding` command without its output, so the empty-binding state is carried as a parenthetical note, not as device output. Capture the output of every `show` the log will cite, even an expected-empty one.
- **No feature-OFF baseline leg exists in this case.** The feature-off value (opt51 = 86,400) is measured at the removal step instead. That works, but it inverts the discipline of baselining first.
- **No lease was run to renewal, rebinding or expiry**, so only the advertised value is proven, not the server's behaviour at T1/T2.
- Options 58 and 59 are absent from every OFFER and ACK although requested in option 55. Graded as a caveat, not a failure, on the reading that this server does not emit T1/T2 unless configured.

## Next run: expected outputs
- `lease 120 0 0` -> option 51 = **10,368,000** in both OFFER and ACK; binding expiry exactly 120 days out.
- `lease 121 0 0` and `lease 999 0 0` -> refused by the parser. That boundary IS the 30-to-120-day feature.
- `lease 1 0 0` -> 86,400. `lease 0 1 0` -> 3,600.
- `no lease` -> back to 86,400 (1 day is the default; do NOT read the `no` form as a silent discard).
- `show ip dhcp pool` after `no lease` reads `<1:0:0:0>`.

## Next run: scripts
- `tools/dhcp4.py` as used; no new tool needed.
- The reboot persistence pattern (stage a named boot config, `ckreload.py`, re-measure on the wire) is worth a `tools/` helper. Arguments: `--cfg-name F --console /dev/uN --baud B --verify-cmd '...'`.

## Next run: references
- The wiki `DHCP` feature page, section "120 Lease", and TPS row 25 -- both already quoted verbatim in this case's final log's `Case:` line.
