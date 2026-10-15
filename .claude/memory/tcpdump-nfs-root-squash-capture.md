---
name: tcpdump-nfs-root-squash-capture
description: "tcpdump -Z <user> writing to the root-squashed NFS lab home produces header-only pcaps that read as NO TRAFFIC; capture to the box's local /tmp as root, then copy and chown"
metadata:
  node_type: memory
  type: reference
---

Measured on tb277, 2026-10-15, during the x960 DHCP campaign.

**The trap.** Captures were landing in a case's `work/` directory on the NFS lab home as
**root-owned files**, which is untidy and blocks later cleanup. The obvious fix —
`sudo tcpdump -Z $(whoami) -w <share path>/leg.pcap` — is **wrong on this share**. Dropping
privilege means tcpdump can no longer write to the **root-squashed** NFS home, so the file is
created (the header is written before the drop) and then nothing is appended. The pcap is
header-only, 24 bytes, and every reader reports **zero packets**.

**Why it costs a session.** A zero-packet capture on the far side of a DUT is
indistinguishable from the DUT dropping the traffic. On this campaign the earlier group's
captures had worked *precisely because* they were root-owned, so the "fix" turned a working
measurement into a false negative that mimics a dropping relay.

**The method that works:**

```bash
sudo tcpdump -i ethN -w /tmp/leg.pcap ...        # local tmpfs, still root
cp /tmp/leg.pcap <case>/work/
sudo chown $(id -u):$(id -g) <case>/work/leg.pcap
```

Local `/tmp` on a testbox is tmpfs and is not squashed, so root writes freely; the copy and
`chown` afterwards leave the share clean. Verify with `ls -l` (a 24-byte pcap is the symptom)
or `tcpdump -r` before grading anything on the result.

`*.pcap` is gitignored repo-wide, so a capture left in a case's `work/` has **no git history** —
`/create-logs` deleting `work/` removes the tracked files but leaves the pcaps on disk, and
deleting those is irreversible. Decide deliberately.

Related: [[scapy-for-traffic-tests]], [[campaign-measurement-discipline]],
[[tb277-x960-dhcp-campaign-2026-10-15]].
