# Group process review -- ntp-2026-10-21T1159

Reviewed 2026-10-22 by /create-logs from the tester's transcript and the working files.

## Token usage

| segment | calls | cache write | cache read | output | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- |
| T33399 | 45 | 57,224 | 8,257,143 | 503 | 1,116 s | 21,862 |
| T33400 | 12 | 27,754 | 3,074,551 | 126 | 1,040 s | 6,342 |
| T44298 | 12 | 21,610 | 3,558,512 | 143 | 398 s | 5,546 |
| T33380 run 2 | 13 | 19,308 | 4,309,284 | 134 | 427 s | 8,322 |
| T33386 run 2 | 18 | 26,286 | 6,357,050 | 208 | 487 s | 17,521 |
| T47192 run 2 | 15 | 24,016 | 5,700,261 | 185 | 638 s | 9,770 |
| overhead | 86 | 212,484 | 16,317,379 | 11,482 | 1,957 s | 223,862 |
| **total** | **201** | **388,682** | **47,574,180** | **12,781** | **101 min** | **293,225** |

**Group overhead: 34.3 %**, across six cases rather than three — this tester ran its own three
NTP cases and then all three campaign-end persistence limbs.

## The three re-run limbs cost 16.4 M and closed a two-campaign gap

T33380, T33386 and T47192 had each recorded reboot persistence as NOT MEASURED, because at the
time a `write` would have saved shared infrastructure the Test Engineer had not yet approved.
Once he did, **16.4 M of cache-read retro-fitted the limb to three already-closed cases** rather
than re-running them whole. Each is a focused run 2 averaging 15 calls — about a fifth of what a
full case costs. **That is the cheap way to close a measurement gap: a limb-only re-run, not a
repeat.**

## 🔥 The finding that matters most came from refusing to accept a timeout

T33400's post-reload re-sync poll **timed out at 180 s with the DUT unsynchronised**. Written up
as it stood, that is a defect report against the product: *NTP does not resume after a reboot.*

The window was extended because the same DUT had synced in ~45 s from configuration earlier in
the same case, so 180 s of silence was not self-consistent. It then **converged at 10 min 55 s**,
and `ntpwire` found why: a **kiss-o'-death, refid RATE**. The DUT's boot-time burst — two polls
in the same millisecond from two source ports — tripped **tb277's own ntpd `limited kod`
restriction**, and the DUT correctly backed off for nine minutes.

**A property of our bench's server, not a DUT defect.** For contrast the DUT syncs in ~75 s from
configuration and ~24 s on a daemon restart.

**The rule, which generalises well past NTP: a timeout is not a measurement.** When a wait ends
without the thing you were waiting for, the window itself is a variable — and if an earlier leg
of the same case did it faster, **the inconsistency is the finding, not the silence**.

## The second method rule this group produced

**After any reload, ping every leg to 4/4 before reading it.** It bit three times in one hour,
and once would have **inverted a verdict**: in T33386's limb, eth3's first post-boot ping was
0 of 4 and the second 4 of 4 — taken at the first attempt, the host the filter is meant to
PERMIT would have read as blocked, which looks exactly like a working filter. With
`arpleg --tcp`, *no reply row* means **silently dropped**. A login prompt is not readiness.

## Findings for the whole group

- **NTP server rate limiting is on by default and invisible in running-config** (burst 8,
  interval 8 s, leak 4). A 20-packet burst gets 11 answers until `ntp rate-limit burst 64` makes
  it 20/20. **Without knowing this, normal product behaviour reads as a bench fault.**
- **`show ntp status` and `show ntp counters` print completely empty output when NTP is not
  configured** — an empty read is a state, not a hung command.
- **The client randomises both its UDP source port and its request transmit timestamp** on every
  poll. A capture filter on source port 123 misses every packet, and that timestamp read as
  "the DUT's clock" is wildly wrong.

## Accuracy gaps to close next time

1. 🔴 **T44298's health BEFORE sample has no `show log` read at all** — a STANDING-ORDERS §8 gap
   in the run, so its HEALTH `log` line reports the after sample only.
2. 🔴 **The `ntp rate-limit` single-keyword finding has no sourced before/after pair**, despite
   being measured three times. It could not enter the deliverable and needs a re-run with a
   quoted `show running-config` pair before it can face a developer.
3. T33400 and T44298 recorded CPU percentages but no load averages.

## Next run

- Reuse `tools/ntpc.py` (crafted client, IPv4+IPv6, no root — a plain UDP socket deliberately,
  because the box's own ntpd owns UDP/123 and a raw responder would race the kernel) and
  `tools/ntpwire.py` (decoder with request/reply pairing and automatic kiss-o'-death flagging).
- Budget for the bench's own kiss-o'-death backoff in any NTP client case here.
