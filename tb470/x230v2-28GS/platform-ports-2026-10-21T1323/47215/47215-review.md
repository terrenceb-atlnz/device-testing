# T47215 process review -- platform-ports-2026-10-21T1323
Reviewed 2026-10-21 by /create-logs from agent-ad7157fdc1eed0717.jsonl and the working files. Case: "sh sys environment".

## Token usage
This case shared one console login and one RESULT message with T47226, T47227 and T47215, so the three have one segment.
How it was cut, and the run's other segments: [../REVIEW.md](../REVIEW.md).

| calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 (shared by 3 cases) | 164 | 133,677 | 737,072 | 39 | 10 | 343 s | 29,634 chars |

## Process taken
1. Read the tools README entries for cfg, ckyn, qmark, peek, rcdiff and rc2cfg (7,980 chars).
2. Marked the queue row RUNNING, made the case folders, listed the host NICs (`tools/tb nics`).
3. One `tools/tb ckcon` login on u1: setup reads, then a health sample, show version, a health sample, show license, a
   health sample, show system environment, a health sample. Output saved to a scratch file.
4. One baseline `ckcon` on the 4050 (u0), for the later port cases.
5. Three reads of the saved output: the grading lines (3,513 chars), the four health samples (7,779 chars), and a check of
   the reboot-history order and cpu/memory headers (5,964 chars).
6. One script wrote the three working logs and `swi_f.cfg` files, then committed. One RESULT message for all three.

## Wasted input
- The health summary call read 7,779 chars to reduce four health samples to five numbers each. A health helper would print
  those numbers directly (../REVIEW.md, proposed scripts).
- The reboot-history order check (5,964 chars) re-read the morning's final log to confirm that the x230 prints entries
  unsorted. That fact is now recorded; next time read it, do not re-check it.

## Repetition
none found

## Accuracy risks
- The case database holds no objective and no steps. The expected result is the tester's reading ("answers in full, no
  `% ` line, content sane"). The Test Engineer accepted it at grading. The fan speed moves a little between reads; grade on Ok within limits, not on the exact rpm.

## Next run: expected outputs
- `show system environment`: `Overall Status: Normal`; 9 sensors all Ok within limits (Fan 1 about 3,665 rpm, 5 voltages, 3 temperatures).

## Next run: scripts
- `tools/tb ckcon tb470 <scratch> u1 115200 "show version" "show license" "show system environment"`, with the health
  reads between them. Keep all three show cases in ONE login, as this run did.
- Proposed `tools/tb health` for the health samples (../REVIEW.md).

## Next run: references
- [platforms/x230v2-28GS.md](../../../../platforms/x230v2-28GS.md) §1: the x220 build name, and `show cpu` prints busy %.
- This case's final log in this folder: the full expected output.
