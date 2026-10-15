# T43851 process review -- dhcp-server-2026-10-15T1458
Reviewed 2026-10-15 by /create-logs from agent-a355179677143f86e.jsonl and the working files.

## Token usage

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30 | 60 | 55,136 | 5,478,463 | 22,914 | 30 | 926 s | 18,583 chars |

## Process taken
1. Read the campaign queue's group rows and the group setup/restore recipe.
2. Re-ran the no-console occupancy precheck, then `bench_probe.py --box tb277 run` for the before state.
3. Read the DHCP ARP Probe TFS (S1566.1.01-.17) and the TPS row; cached both on the box under `/tmp/dhcp-2026-10-15T1458/`.
4. Built the group's VLAN 10 setup on swi_d and saved `swi_d.cfg`.
5. Ran six legs through one per-case driver script, each leg a crafted `dhcp4.py client` burst on eth3 with tcpdump alongside.
6. Patched `tools/dhcp4.py` twice mid-case (the option-82 integer-key trap), then wrote the working log and sent `RESULT`.

## Wasted input
- The single `sed -n '/^## Queue/,/^## Known bench notes/p'` of the queue returned 2,077 chars, most of it other groups' rows and the triage prose. A dispatch that carries this group's two rows inline removes the read entirely.
- Four console read-backs of 1,890 / 1,471 / 1,215 / 1,164 chars each re-printed `show running-config` fragments that had already been written to a file in the same command. Writing to the file and printing only the grep that decides the next step would have cut roughly 3 kB.

## Repetition
- `tools/dhcp4.py` was edited twice in this case for the same defect class (option keys). Both edits are now in `tools/`, so no later case paid it again -- but the second edit was avoidable by reading the option-handling block once, in full, at the first edit.
- The occupancy precheck and `bench_probe.py run` also ran in the session overhead segment. See the group `REVIEW.md`.

## Accuracy risks
- **No step text and no objective exist for this case** in AWPTCM or ck.db. The steps are the tester's own, graded against the TFS. A reader cannot check the steps against an authority that does not exist -- the TFS citations per step are what carries it.
- **The DUT MAC was never recorded.** The working log has the host NIC MAC only, so the final log's topology omits it. One `show interface vlan10 | include Hardware` at setup closes this permanently.
- **Reboot persistence for this case was measured inside the sibling case's leg** (the group shared one reload). It is the same run and it measured this case's own settings, but the evidence had to be fetched from another case's working files to write this log. A group reboot check should write its per-case findings into each case's own working log.
- Bootloader version reads `Unknown` on this unit, so it is absent from `Build:`.

## Next run: expected outputs
- `probe enable` + `probe packets 3` + `probe timeout 1000` -> exactly 3 ARP probes, inter-frame gaps 0.995 / 1.001 s.
- `no probe enable` -> 0 probes, address offered immediately.
- `probe packets 0` -> 0 probes (the boundary, not an error).
- An answered probe -> the address is withheld and a conflict binding appears with an EMPTY ClientId.
- `probe type ping` ARPs FIRST for a locally connected client, then sends ICMP -- "no ARP" does NOT discriminate the two probe types.

## Next run: scripts
- `tools/dhcp4.py client <iface> --mac <base> --clients N --gap 1 --broadcast --prl 1,3,6,51 --wait 3 --arp-answer <ip>` covers every leg here; nothing new is needed.
- Proposed: a thin `tools/` wrapper that runs one named leg (config, tcpdump start, client burst, tcpdump stop, JSON out) so each case stops rebuilding a leg driver by heredoc. Arguments: `--leg NAME --config-file F --iface I --client-args '...'`.

## Next run: references
- `DHCP ARP Probe TFS` S1566.1.01-.17, cached per campaign at `/tmp/<campaign>/DHCP_ARP_Probe_TFS.wiki` -- read it once per GROUP, not per case.
- `tools/README.md` entry for `dhcp4.py`, including the option-82 integer-key trap, instead of rediscovering it.
