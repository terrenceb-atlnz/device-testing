# Process review -- mdix-2026-10-13T0949 (tb470, x230v2-28GS)
Reviewed 2026-10-13 by /create-logs from the tester transcript `agent-a56f1efcb6f6b0267.jsonl`
(token figures from `tools/case_tokens.py`; tool inputs and result sizes only) and the working
files. One case: [33234/33234-review.md](33234/33234-review.md).

## Token usage
| segment | calls | input | cache write | cache read | output | tool calls | wall | tool output read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| T33234 | 55 | 110 | 74,665 | 8,739,869 | 2,718 | 56 | 1,275 s | 59,244 chars |
| overhead | 25 | 50 | 97,107 | 2,362,075 | 390 | 25 | 148 s | 154,157 chars |
| **total** | **80** | **160** | **171,772** | **11,101,944** | **3,108** | **81** | **1,423 s** | **213,401 chars** |

Overhead = calls #1-#24 (gate and up-front reading, 22:43:35Z-22:45:44Z) and #81 (hand-back).
The overhead read 2.6 times the case's tool output in its first 2.5 minutes, and that context
was then carried through all 55 case calls (cache read 8.7 M).

## Overhead findings
- **Whole files read up front (#6, #9-#11, 83k chars together).**
  - #6: `TESTBOX-ACCESS.md` read in full (34,015 chars). The gate is now `tools/tb precheck` /
    `peek` / `probe`, which the tester learned from `tools/tb --help` (#12, 4,118). A `grep -n '^#'`
    and the one section it needed would have done.
  - #9-#11: `library_5000.py`, `test-5000.0004` and `test-5000.0003` printed with `cat -n`
    (49,117 chars). A grep of `testCaseNum|testCaseDesc|testCaseMethod|configurePort|polarity`
    (~4k) gives the TestCase map and the defaulting commands.
- **Rules re-read in ranges (#2-#4, #7-#8, 51k chars).**
  - #2: the queue lines 1-134 (12,868). The group needed its Queue row, the Triage T33234
    bullet and the group 2 recipe (~3k).
  - #4: ranges of `platforms/x230v2-28GS.md`, `STANDING-ORDERS.md` and `logged-output.md`
    (12,800). #78 re-read `logged-output.md` 47-71 at the end.
  - #7: `tools/README.md` 20-188 (11,565).
- **#16-#17: group 1's working log read to copy the probe arguments** (4,481). The probe line
  belongs in the queue's group recipe, which already holds the setup and restore commands.
- **The read that would have changed the outcome was missing.** None of the up-front reading
  was the same case id's earlier verdict, or the platform's MDI/MDI-X ruling. The triage
  re-classified T33234 as runnable via the copper-SFP scripts, and the tester ran it to a PASS
  that the Test Engineer re-graded UNSUPPORTED (see the case review). Since 2026-10-13
  `platforms/x230v2-28GS.md` §2 and `.claude/memory/sfp-is-not-a-fixed-copper-port.md` carry
  the ruling.

## Cross-case findings
With one case in the group, these are the findings that will recur in any framework group:
- **Framework polling and result discovery** cost ~20 calls (case review, "Repetition"). A
  `tools/tb fw --wait --summary` mode (proposed in the case review) would serve every
  framework case on any box.
- **The framework's `--nodefaultcfg` side effects** need the same restore every time: it moves
  the boot pointer to `flash:/swi_X_<set>.cfg` and leaves `swi_X_<set>[_N].cfg` and
  `TestCase_tear_down.cfg` on each unit (#72-#75). A `tools/fwclean.py` (proposed) makes it one
  call.
- **Grade against the platform's rulings before the run, not after.** A triage step that greps
  `platforms/<FAMILY>.md` §2 and earlier `<id>-*.log` files for the case id would have caught
  this verdict before 21 minutes of bench time.
