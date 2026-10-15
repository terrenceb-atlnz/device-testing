# T43850 process review -- dhcp-relay-2026-10-15T1458
Reviewed 2026-10-15 by /create-logs from agent-a355179677143f86e.jsonl and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | 40 | 36,996 | 6,941,355 | 8,990 | 20 | 1268 s | 20,671 chars |

## Process taken
1. Baseline with insertion disabled: no option 82 on any relayed DISCOVER.
2. Negative step: remote-id refused while agent-option is disabled.
3. Insertion on; read circuit-id and remote-id off the wire; ASCII override and revert.
4. `agent-option checking` across three legs, establishing it is a RESPONSE-side check.
5. All four information-policy actions, with the raw TLV dump proving `append` produced two blocks.
6. Reply-side strip per RFC 3046; removal; reboot persistence.

## Wasted input
- The largest single read of the case, **5,582 chars**, was an ssh grep over the AW+ CLI wiki command directory. Narrowing to the two pages actually needed, or reading the cached copy under `/tmp/<campaign>/`, would have cut most of it.
- Four configuration heredocs (2,752 / 2,329 / 1,528 / 1,364 chars) were sent as script text. Same finding as the sibling case: parameterise one runner.

## Repetition
- `o82cfg.sh`, `o82chk.sh` and `o82chkon.sh` are three near-identical drivers differing only in the config lines and the leg name.

## Accuracy risks
- **Removal is proven for two of four `no` forms, not all four.** `no ip dhcp-relay information policy` and `no ip dhcp-relay agent-option` were sent only in the teardown sequence, with no `show` after them, and teardown proof is excluded from a final log. The log therefore proves removal for `no ... agent-option remote-id` and `no ... agent-option checking` only, and attributes the policy revert to the explicit `information policy replace` that was actually sent -- not to the no-form. **Send every `no` form inside the removal STEP with a `show` after it**, and leave teardown to teardown.
- **`swi_d.cfg` captured at 16:30, after the legs**, not before step 1.
- `% Can not configure DHCP Relay agent option remote-id unless agent option is set` is a `%` line but is the EXPECTED result of the negative step -- graded PASS. A `%`-line gate that fails the run on any `%` would have wrongly failed this case.

## Next run: expected outputs
- Insertion on -> circuit-id = the ingress VLAN name (`vlan10`), remote-id = the switch MAC.
- `remote-id CK-REMOTE-82` -> that ASCII string; its no-form reverts to the MAC.
- remote-id is REFUSED while agent-option is disabled (S1566.100.07).
- `agent-option checking` validates SERVER RESPONSES -- it does NOT police untrusted client ingress. Measuring it on the ingress side proves nothing.
- `append` -> TWO option-82 blocks on the wire. A decoder that keeps only the first option of a name reports this as "append did not append".
- Option 82 is STRIPPED from the reply delivered to the client (RFC 3046).

## Next run: scripts
- `tools/opt82dump.py` (moved out of this case's `work/` by this run, with a README entry) dumps the raw option-82 sub-TLVs from a capture. Use it instead of trusting a decoder's option list.
- The proposed `tools/leg.py` from the sibling case applies here unchanged.

## Next run: references
- `DHCP Option 82 Remote ID TFS` S1566.100.01/.02/.06/.07/.08.
- `tools/README.md` -> `opt82dump.py`, for why a single-option decoder misreads `append`.
