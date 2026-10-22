---
name: tcpdump-nfs-root-squash-capture
description: "Three ways a tcpdump capture lies that it saw NO TRAFFIC: -Z <user> to the root-squashed NFS home gives header-only pcaps; and a file SIZE read before the writer has exited reads 0 while the buffer is unflushed. and a syslog destination the box does not listen on goes quiet for exactly 60 s at a time. Capture to local /tmp as root, confirm the writer exited, and size the window to the protocol's own back-off before believing a zero"
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

**A THIRD way, measured on tb277 2026-10-22 (x960 syslog campaign).** With **no UDP/514
listener on the box**, every syslog datagram the DUT sends draws an **ICMP port-unreachable**.
The DUT's syslog-ng marks the destination broken and **reopens it after exactly 60 s**
(`time_reopen='60'` in its own log), then flushes the whole backlog in one sub-millisecond
burst. **Three capture windows read ZERO while the feature was working perfectly.** Windows of
170 s or more saw everything.

**The general rule this third case gives:** before believing a zero, ask what back-off the
*protocol or the daemon* applies, and make the window longer than it. A capture shorter than
the sender's retry interval measures the retry interval, not the feature.

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


## The second way a capture lies: reading its SIZE before the writer has exited

Measured on tb277, 2026-10-15, during the x960 BGP case — and it **nearly produced a false
product finding**.

A port mirror was being validated. The check ran `ls -la` on the capture **in the same command
line** as a `sudo kill -INT $TD` that never reached tcpdump, because `$!` had captured the
wrapper, not tcpdump itself. The capture was therefore still running with its buffer unflushed,
the file read **0 bytes**, and that was written up as "the mirror copied zero frames — a fourth
instance of the platforms/x960.md §5 read-back-vs-dataplane defect class".

**It was false.** Finding the stray process with `ps` at group hand-back, stopping it by PID and
reading **the same file** gave 14 mirrored TCP/179 frames plus mirrored ICMP, every timestamp
inside the mirror's own window. The mirror had worked the whole time. The claim was retracted in
the working log, the queue and the platform file before anything rested on it.

**The rule:** a `tcpdump -w` file's size is not a measurement until its writer has exited.
Confirm with `ps`, or read tcpdump's own `N packets captured` line, before concluding that
nothing arrived.

**Why this one matters beyond its own case:** `platforms/x960.md` §5's evidence for three *real*
mirroring/read-back defects is itself built on capture sizes (1 byte = nothing arrived). The
caution belongs beside them, or the same mistake gets made in the other direction.

**The general form, which both halves of this memory share:** a zero from an instrument is only a
measurement once that same instrument has produced a non-zero in the same run. Every counted leg
of the 2026-10-15 routing campaign carried an instrument control for exactly this reason.

Related: [[scapy-for-traffic-tests]], [[campaign-measurement-discipline]],
[[tb277-x960-dhcp-campaign-2026-10-15]].
