# switching group — IE520, tb470, 2026-09-22

11 cases. **7 PASS · 2 UNMEASURED · 2 SKIPPED** — 6057 re-run 2026-09-24; 24032 and 12067 SKIPPED by Terrence's ruling 2026-09-23 (was 6 PASS · 1 PARTIAL · 4 UNMEASURED).

| case | title | verdict |
| --- | --- | --- |
| [38418](38418.log) | frame forwarding rules - unicast & broadcast | **PASS** |
| [10300](10300.log) | MLD Snooping disabled, send UDP multicast | **PASS** |
| [10304](10304.log) | MLD Snooping enabled, send UDP multicast | **PASS** |
| [38417](38417.log) | IGMP Snooping disabled - multicast packets | **PASS** |
| [8633](8633.log) | IGMP Snooping enabled - multicast packets | **PASS** |
| [29770](29770.log) | UDP broadcast helper | **PASS** |
| [6057](6057.log) | ARP Learning with full tables | **PASS + finding** (re-run 2026-09-24) — table caps at 2045; while full a NEW neighbour cannot be resolved (`No buffer space available`) |
| [45788](45788.log) | 5005 EPSR performance test on SFP port | **UNMEASURED** — bench: no SFP fitted |
| [45789](45789.log) | 5005 EPSR performance test on SFP+ port | **UNMEASURED** — bench: no free SFP+ |
| [24032](../epsr-l2-2026-09-29/24032-fail.log) | 5706 L2 platform test | **MOVED 2026-10-02** to `../epsr-l2-2026-09-29/24032-fail.log` (re-run: FAIL, 1 unexplained TestCase of 19). The 09-22 "case-scope mismatch" reading was wrong: 5706 is a framework suite (raw-data/test_scripts/5706_Platform_L2) |
| [12067](../epsr-l2-2026-09-29/12067-unsupported.log) | Flow control operation with MDI | **MOVED 2026-10-02** to `../epsr-l2-2026-09-29/12067-unsupported.log` (re-run: UNSUPPORTED — the IE520 refuses `flowcontrol`: "not supported on this product") |

## Bench limits vs case-scope — they need different answers

- **Bench limits** (more hardware fixes them): 45788/45789 need SFP transceivers
  fitted — every non-stackport cage reads `not present`, and the only populated
  SFP ports are the stackports carrying the VCStack. 12067 needed a line-rate
  generator with two ports (2026-09-24: tcpreplay now gives ~983 Mbps per NIC; 12067 is SKIPPED by
  ruling, reopen open — queue I-19). (6057's "full tables" was closed on 2026-09-24 with an
  ARP responder on tb470 -- see its log.)
- **Case-scope mismatch** (hardware will never fix it): **24032** is "Run the
  5706 automated test". That is a platform suite for a different product; running
  it against an IE520 would not produce a meaningful IE520 result. The question
  is whether it belongs in this set at all.

## Two product findings worth keeping

**The DUT does not learn ARP from unsolicited (gratuitous) ARP.** 6000
gratuitous replies from 6000 distinct sender IP/MAC pairs on an on-link
10.90.0.0/16 produced **zero** entries, while a single `ping` immediately
created one. That is correct anti-poisoning behaviour, and it is *why* the
table cannot be filled from one host.

**Snooping prunes after the first frame of a new group.** With snooping enabled,
three back-to-back bursts gave `1/10, 0/10, 0/10` — the first frame floods while
the entry installs, then pruning is complete. Grading "enabled" as requiring
exactly 0 is wrong.

## Measurement correction — read [MEASUREMENT-NOTE.md](MEASUREMENT-NOTE.md)

The observation path runs **through the x230**, which has its own IGMP/MLD
snooping on by default. The first snooping pass showed `1/10` with DUT snooping
*disabled* — the DUT was flooding correctly and the x230 was pruning downstream.
The result said nothing about the DUT. **When a measurement runs through the
x230, ask what the x230 does to it: it is a switch in the path, not a wire.**

## Bench state at exit

DUT and x230 both back to IGMP and MLD snooping enabled. UDP helper and
`ip forward-protocol` removed, 10.90.0.0/16 secondary removed, ARP cache
cleared. Stack `Normal operation`, all three TB paths verified.
