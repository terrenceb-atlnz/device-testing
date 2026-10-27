# securemode-2026-10-23T1304 -- group process review

Reviewed 2026-10-28 by /create-logs from `agent-a3ceda2b4189e77a9.jsonl` and the working files.
One case in the group. The per-case detail is in
[T44287/T44287-review.md](T44287/T44287-review.md); this file holds the group totals and the
findings that belong to the group rather than to the case.

## Token usage

| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T44287 | 100 | 200 | 171,310 | 14,904,364 | 2,073 | 106 | 2,792 s | 152,035 chars |
| overhead | 3 | 6 | 38,678 | 504,889 | 844 | 3 | 48 s | 13,884 chars |
| **total** | **103** | **206** | **209,988** | **15,409,253** | **2,917** | **109** | **2,840 s** | **165,919 chars** |

`case_tokens.py` splits at the first tool call that touches the case folder. The tester entered
`T44287/` on its third call, so `overhead` holds only two queue reads and the case row is
effectively the whole run. Read the totals, not the split.

**Cache read is 14.9 M, the largest figure in this campaign.** It is a direct function of step
count: 100 sequential console calls over 47 minutes each re-read the accumulated context. The
only lever that moves it is fewer, larger console batches.

## The overhead's own findings

1. **Reading the rules cost 23.3 KB in two calls**, and the first of those two was a headings
   dump used only to find the line numbers for the second. `grep -n '^## '` instead of
   `grep -n '^#'` would have cut that first call by about 90%.
2. **The prior working log was re-read for 16.0 KB** to recover a limb table and a recovery
   ladder of roughly 60 lines. When a dispatch resumes an unfinished case, those 60 lines belong
   in the dispatch.
3. **Reaching one case block cost a 614-line read of the campaign queue** (9.7 KB).

## Findings that would recur across cases

- 🔴 **`tools/tb probe --template` resolves its path ON THE BOX.** The same tree is
  `/media/bidhanc/mnt/testbox_home/claude/device-testing` on the dev host and
  `/home/bidhanc/claude/device-testing` on tb277. A dev-host path prints
  `no template at <path> -- diff skipped` and **still exits 0**, which is indistinguishable
  from `MATCH` at a glance. This group lost two probe invocations to it. Pass the box-side path,
  and confirm the word `MATCH` appears rather than trusting exit 0.
- 🔴 **Probe `CHECK_CABLE` on this bench is forwarding-database ageing, and one ping clears it.**
  Settled here rather than inferred: the after-probe exited 2 with `CHECK_CABLE` on eth3 and
  eth4, two `tools/tb ping` calls refreshed the table, and the re-probe exited 0 `MATCH`. An
  all-console case sends no traffic, `--read-only` suppresses the probe's own pings, and a
  reboot flushes the table outright, so this will happen in every reboot-heavy console case.
- 🔴 **A deliberate reboot always produces a DIRTY health verdict.** The matcher counts ordinary
  kernel boot messages because they contain the word `kernel`. Attribute them to the reboot you
  caused; do not report a fault, and do not quietly drop the lines either. A `--expect-reboots`
  flag for `tools/health.py` is proposed in the case review.
- 🔴 **`tools/snmpq.py` can report `RESULT VALUE` with exit 0 for a net-snmp usage error.** This
  is the one item in either review that can change a verdict, and it is written up in full in
  the case review. Fix it before the next SNMP case.
- **tb277 cannot drive SNMPv3 with SHA-256.** net-snmp 5.7.3 accepts only `MD5|SHA` for `-a`,
  and the installed pysnmp cannot load its crypto backend. Any future case needing SHA-256 or
  AES-192/256 SNMPv3 must either get a package installed by the Test Engineer, or declare the
  limb NOT MEASURABLE with that reason.
- **`bench-setup/tb277/bench-state.md` is rewritten by every probe**, and a one-console probe
  reduces the three-unit record to one unit. Revert it after every probe and do not commit it
  from a one-console run.
- **Take the recovery copy first.** `copy running-config flash:/pre-securemode.cfg` was the
  first action of the window, before any read. That order matters here more than usual: a
  `write` while secure mode is on permanently drops every configuration line secure mode
  refuses, and they do not come back when it is turned off.
