# T35370 process review -- dhcp-client-2026-10-15T1458
Reviewed 2026-10-15 by /create-logs from agent-a355179677143f86e.jsonl and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | 32 | 27,863 | 6,226,109 | 7,408 | 16 | 964 s | 8,293 chars |

## Process taken
1. No TFS exists for "Extended ID", so the DUT's DHCP-client identity surface was enumerated by read-only CLI help probe FIRST.
2. Baseline capture with no identity options set.
3. Four legs: `client-id` (option 61), `hostname` (option 12), `vendor-identifying-class` (option 124), `request vendor-identifying-specific` (125 in the PRL).
4. Removal leg: every option back to the baseline.

## Wasted input
- Little. This is the leanest case in the campaign: 16 calls, no read over 1 kB. The two help-probe scripts (`qm.sh` 700, `qm2.sh` 926) are the only non-trivial inputs and they bought the whole test design.

## Repetition
- `legC.sh` / `runlegC.sh` are again a hand-built pair of leg drivers. Group finding.

## Accuracy risks
- **No reboot-persistence evidence exists for this case.** The group's reload saved `ckclient.cfg` at 17:11, AFTER this case's removal step had taken all four identity options out, so none of them were in the saved config. The final log therefore makes no persistence claim in either direction. Closing this needs a re-run, or a group reboot check staged BEFORE any removal step.
- **All SVIs share one MAC** (`vlan1`, `vlan10`, `vlan48` all `e01a.ead4.7043`), so `client-id vlan10` and `client-id vlan48` produce byte-identical option 61. Grading was on presence, type byte and length, and the log states that discriminator -- but a content comparison here would be meaningless, and a future tester must not treat matching bytes as proof the right interface was named.
- **`swi_d.cfg` captured at 16:55, after the legs.**
- 7 frames were on the wire where the scapy server decoded 4 of the 5 client frames: the first arrived during the tool's own import. **tcpdump is authoritative for the wire; the tool only for what it decoded.**

## Next run: expected outputs
- `client-id <IFNAME>` -> option 61 = type byte `0x01` + that interface's MAC.
- `hostname CKDHC1` -> option 12 = `CKDHC1`.
- `vendor-identifying-class` -> option 124 carrying IANA enterprise **207** (Allied Telesis).
- `request vendor-identifying-specific` -> **125** appended to the parameter request list.
- The AW+ client's default PRL is **[1,3,15,6,43]** -- option 43 is additional to what the wiki DHCP page documents.
- `% DHCP client is already running on this interface.` is a GENUINE REJECTION (exit 2, state unchanged), unlike the relay's similarly worded advisory. Measuring past it captures the DEFAULT client and reports it as configured.

## Next run: scripts
- `tools/qmark.py` for the read-only help probe; `tools/dhcp4.py server` for the capture side.
- The proposed `tools/leg.py` applies.

## Next run: references
- No TFS exists. The authorities are TPS row 30 and the DUT's own CLI surface -- enumerate it before designing steps, as this run did.
