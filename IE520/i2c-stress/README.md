# i2c-stress — IE520 i2c bus stress via interleaved show commands

Re-creation of the 2026-08-19/20 i2c-lockup campaign tooling for use on
**other IE520 units**: interleave the two i2c-taxing commands N times each
(default 300) and watch for the lock → watchdog-reset signature.

Provenance: `~/i2c_evidence.log` (the full campaign record). `show platform
port` was the single-command reproducer (+2.6 s on a unit hosting faulty
AT-SPTXc S/N A10217F213300006); `show system pluggable diagnostics` exercises
the DDM path and doubles as the defect screen — the faulty module reads
**Vcc 3.4167 V, above the 3.4000 V High-warning threshold**.

Two standalone variants, both stop-on-first-lock, both hands-off recovery
(no PDU use; the IE520 watchdog self-resets ~42 s after a lock):

| | `i2c_stress.py` | `i2c_stress_fw.py` |
|---|---|---|
| needs | python3 + pyserial | `PYTHONPATH=/home/st-art` (framework) |
| .setup file | none | none (constructs `Switch(devicePath)` directly) |
| baud | `--baud` flag (115200 default) | framework default only |

Run either **from a fresh dated directory** (logs land in CWD), detached:

    cd ~/i2c-stress-runs/$(date +%Y%m%d)-<bench> 
    setsid nohup <script> /dev/uN -n 300 > stdout.log 2>&1 < /dev/null &

Assumptions: standalone unit (warns if `show stack` disagrees), populated
cages (no per-port targeting), console driven directly (kernel printk is
in-band only there). Expected duration ≈ 20–30 min for 300+300 clean
iterations. Read-only `show` commands only; nothing is written to the DUT.

Exit codes: 0 = all iterations clean · 1 = lock/reset detected (evidence
log has iteration, in-flight command, epoch, and post-event reboot history)
· 2 = aborted (port held, no prompt) or wedged with no self-recovery.
