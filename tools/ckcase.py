#!/usr/bin/env python3
"""Print a test case's authored text from the Ask-CK database (ck.db).

It runs on a testbox or on a dev host that mounts the lab home: with no --db it uses the
first ck.db it finds among $CK_DB, the Test-cases checkout beside this repo (found from this
file's own path), and ~/claude/Test-cases/... (2026-10-27: the dev host needed --db every
time, which cost a failed call per campaign).

Lookup order (first hit wins):
  1. `zephyr_cases`, keyed on `key` = the AWPTCM id exactly as the Test Engineer gives it
     (`AWPTCM-T43870`).  This is the modern table and holds `objective`, `precondition`,
     `steps_text` and `num_steps`.
  2. `testlink_cases`, joined on `title` (the legacy AWP-nnnn corpus), when `--title` is given
     or when the key is not found and `--title` was supplied as a fallback.

Usage:
  ckcase.py <KEY> [KEY ...] [--db PATH] [--title TEXT] [--columns] [--raw-steps]

  --db PATH     override the database (default: the first of DB_CANDIDATES that exists)
  --title TEXT  also search `testlink_cases.title` for this substring
  --columns     just print each table's column list and exit
  --raw-steps   also dump the raw `steps` column (usually HTML/JSON), unmodified
"""
import argparse
import os
import sqlite3
import sys

_REL = os.path.join("Test-cases", "ask-ck", "db", "ck.db")
DB_CANDIDATES = [p for p in (
    os.environ.get("CK_DB"),
    # <lab home>/claude/device-testing/tools/ckcase.py -> <lab home>/claude/Test-cases/...
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), _REL),
    os.path.join(os.path.expanduser("~"), "claude", _REL),
) if p]
DEFAULT_DB = next((p for p in DB_CANDIDATES if os.path.isfile(p)), DB_CANDIDATES[-1])


def connect(path):
    return sqlite3.connect("file:%s?mode=ro" % path, uri=True)


def cols(con, table):
    try:
        return [r[1] for r in con.execute("PRAGMA table_info(%s)" % table)]
    except sqlite3.Error:
        return []


def show_row(names, row, raw_steps):
    for name, val in zip(names, row):
        if val is None or val == "":
            continue
        if name == "steps" and not raw_steps:
            print("--- steps (raw column suppressed; use --raw-steps) --- %d chars" % len(str(val)))
            continue
        text = str(val)
        print("--- %s ---" % name)
        print(text)
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help="case keys, e.g. AWPTCM-T43870")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--title", default=None)
    ap.add_argument("--columns", action="store_true")
    ap.add_argument("--raw-steps", action="store_true")
    a = ap.parse_args()

    try:
        con = connect(a.db)
    except sqlite3.Error as e:
        print("cannot open %s: %s" % (a.db, e), file=sys.stderr)
        return 2

    if a.columns:
        for t in ("zephyr_cases", "testlink_cases"):
            print("%s: %s" % (t, ", ".join(cols(con, t)) or "(table absent)"))
        return 0

    if not a.keys and not a.title:
        ap.error("give at least one KEY or --title")

    zc = cols(con, "zephyr_cases")
    found_any = False
    for key in a.keys:
        print("=" * 72)
        print("zephyr_cases  key = %s" % key)
        print("=" * 72)
        rows = list(con.execute("SELECT * FROM zephyr_cases WHERE key = ?", (key,)))
        if not rows:
            print("(no row)")
            continue
        found_any = True
        for row in rows:
            show_row(zc, row, a.raw_steps)

    if a.title:
        tc = cols(con, "testlink_cases")
        print("=" * 72)
        print("testlink_cases  title LIKE %%%s%%" % a.title)
        print("=" * 72)
        rows = list(con.execute(
            "SELECT * FROM testlink_cases WHERE title LIKE ?", ("%" + a.title + "%",)))
        if not rows:
            print("(no row)")
        for row in rows:
            found_any = True
            show_row(tc, row, a.raw_steps)

    return 0 if found_any else 1


if __name__ == "__main__":
    sys.exit(main())
