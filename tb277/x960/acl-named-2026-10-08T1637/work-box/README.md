# Raw group-2/3 evidence, preserved off the box by the sentinel — 2026-10-09 16:32

**Why this folder exists.** The tester was cut off by a session usage limit at ~12:31, part-way
through **T44979's service-policy pass**. It had reported all three `access-group` legs passing
but had **not yet written `T44979/work/run1.log`**, so that evidence existed only in these files
on tb277's `/tmp`, which does not survive a reboot of the box. Copied here unchanged. **Nothing
in this folder has been edited, re-ordered or summarised.**

This is NOT a substitute for the per-case working logs `logged-output.md` requires. When the run
resumes, T44979 still needs its `work/run1.log` ending in a `VERDICT:` line, citing these files.

Second time this has been needed — see `../../mirror-2026-10-08T1637/work-box/` for the group-1
equivalent. Both times the cause was the same: a tester interrupted between finishing the
measurements and writing the log.

## What the files are

- `console-u2.log` (184 KB) — every byte to and from the DUT console across **groups 2 and 3**:
  T44987, T44988, T44986 and T44979 up to the cut. The primary record.
- `console-u2-reload.log` — the DUT console across T44987's D3 reload.
- `console-u3.log` — the swi_b console.
- `pre-u2.txt`, `pre-u3.txt` — running-configs captured before the group-2/3 setup.
- `setup-u2.txt`, `setup-u3.txt` — running-configs captured immediately after it.
- `spoof.py` — the scapy helper that sent frames with a forged source MAC. This is what proved
  the MAC wildcard mask from the traffic side in T44988.
- `vtytest.py` — the helper that drove SSH attempts against `vty access-class` for T44986.

## Bench state at the moment of the cut, measured 16:32 (not inferred)

    Hardware IP access list t44979   4 deny icmp 10.38.22.65/32 10.38.22.70/32
    Hardware IP access list t44979b  4 deny tcp  10.38.22.65/32 10.38.22.70/32
    class-map  t44979cm  -> ACL t44979
    policy-map t44979pm  -> interfaces: port1.0.48, default class action permit
    interface port1.0.48 -> service-policy input t44979pm, switchport access vlan 100
    show mirror          -> empty
    mls qos              -> enabled globally

Plus the group-3 campaign setup (`sa1` = port1.0.2 + port1.0.16, swi_a isolated, off-bench
VLAN-100 ports shut) and the `vlan100 10.38.22.67/27` address T44986 added to the DUT.

**Nothing is at risk in this state**: the policy-map's default class action is `permit`, so no
traffic is blocked; consoles were left free; and none of it is in startup-config, so a reload of
the DUT clears all of it by itself.
