#!/usr/bin/env python3
"""conkey.py <tty> <baud> <transcript> ITEM [ITEM ...]: send raw keys and lines to a
console that is NOT at a prompt, and print what came back.

Why this exists: every other console tool here logs in first, so every one of them is
useless on exactly the console that most needs driving -- one parked mid-state.
`peek.py` reports such a console but can only send a bare CR, and a CR is the wrong
key for most of the states a console gets parked in.  Two real cases:

  * **gate item 2 recovery.**  A killed run leaves a console inside a pager, a
    half-typed line, a `(y/n)` or a text-entry mode.  Ctrl-C, Ctrl-U or `q` gets it
    back to exec; a CR usually makes it worse.
  * **interactive CLI commands.**  AlliedWare Plus `mail to <addr> subject <s>` answers
    "Type the message below and finish with a CTRL-d" and then consumes every
    subsequent line as message body -- it cannot be driven by a prompt-driven tool at
    all (measured on x960-56YSQ, AWPTCM-T33368, where it parked the console for 90 s
    and then a tool that insists on a prompt could not even reach it).

So this tool does NOT log in, does NOT look for a prompt, and sends exactly the bytes
it is told, in order.  It is the deliberate counterpart to `peek.py`: peek reports the
state, conkey changes it.  Use it on a console already logged in (after a prompt-driven
tool has left it at exec) or on one that is stuck; use the prompt-driven tools for
everything else, because they check for `% ` errors and this one cannot.

Usage:
  conkey.py <tty> <baud> <transcript> ITEM [ITEM ...]

  ITEM is one of:
    key:NAME      one control byte.  NAME is ctrl-a .. ctrl-z, or one of
                  cr, lf, crlf, esc, tab, space, bs, del
    hex:XXXX      raw bytes, as pairs of hex digits
    text:STRING   the string, with NO carriage return after it
    line:STRING   the string followed by a carriage return
    wait:SECS     read quietly for SECS before the next item (default settle between
                  items is 0.4 s; use this where the device needs longer)

  --settle SECS   the quiet read after every item (default 0.4)
  --final SECS    the quiet read after the LAST item (default 3.0)
  --quiet         print only the last line of what came back

Everything sent and received is appended to <transcript>, which should be the
campaign's `/tmp/<scratch>/console-<uN>.log` so the sentinel sees it.

Exit codes: 0 sent, 2 argument error.  It cannot tell success from failure -- it does
not know what a prompt is.  Read the output, or follow it with `peek.py`.
"""

import os
import sys
import time

USAGE = ("usage: conkey.py <tty> <baud> <transcript> ITEM [ITEM ...]\n"
         "       ITEM = key:NAME | hex:XXXX | text:STRING | line:STRING | wait:SECS")

NAMED = {
    "cr": b"\r", "lf": b"\n", "crlf": b"\r\n", "esc": b"\x1b",
    "tab": b"\t", "space": b" ", "bs": b"\x08", "del": b"\x7f",
}


def keybytes(name):
    n = name.strip().lower()
    if n in NAMED:
        return NAMED[n]
    if n.startswith("ctrl-") and len(n) == 6 and "a" <= n[5] <= "z":
        return bytes([ord(n[5]) - ord("a") + 1])
    return None


def main(argv):
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0

    settle, final, quiet = 0.4, 3.0, False
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--settle" and i + 1 < len(argv):
            settle = float(argv[i + 1]); i += 2
        elif a == "--final" and i + 1 < len(argv):
            final = float(argv[i + 1]); i += 2
        elif a == "--quiet":
            quiet = True; i += 1
        else:
            rest.append(a); i += 1

    if len(rest) < 4:
        print(USAGE)
        return 2
    tty, baud_s, tr = rest[0], rest[1], rest[2]
    items = rest[3:]
    try:
        baud = int(baud_s)
    except ValueError:
        print(USAGE)
        print("bad baud: %r" % baud_s)
        return 2

    # Validate every item BEFORE opening the port, so a typo never half-drives a
    # console that is already in a delicate state.
    plan = []
    for it in items:
        kind, _, val = it.partition(":")
        kind = kind.lower()
        if kind == "key":
            b = keybytes(val)
            if b is None:
                print(USAGE); print("unknown key name: %r" % val); return 2
            plan.append(("send", b, it))
        elif kind == "hex":
            h = val.strip().replace(" ", "")
            try:
                b = bytes.fromhex(h)
            except ValueError:
                print(USAGE); print("bad hex: %r" % val); return 2
            plan.append(("send", b, it))
        elif kind == "text":
            plan.append(("send", val.encode(), it))
        elif kind == "line":
            plan.append(("send", val.encode() + b"\r", it))
        elif kind == "wait":
            try:
                plan.append(("wait", float(val), it))
            except ValueError:
                print(USAGE); print("bad wait: %r" % val); return 2
        else:
            print(USAGE); print("unknown item: %r" % it); return 2

    import serial  # late, so --help works without pyserial

    # The IE520 DTR-drop/BREAK workaround (see console.py); harmless elsewhere.
    os.system("stty -F {} -hupcl 2>/dev/null".format(os.path.realpath(tty)))
    s = serial.Serial(tty, baud, timeout=0.2)
    t = open(tr, "a", errors="replace")
    t.write("\n===== conkey {} {} =====\n".format(tty, time.strftime("%F %T")))

    def drain(secs):
        got = b""
        t0 = time.time()
        while time.time() - t0 < secs:
            b = s.read(4096)
            if b:
                got += b
        return got

    all_rx = b""
    try:
        all_rx += drain(0.3)          # whatever was already sitting there
        for kind, payload, raw in plan:
            if kind == "wait":
                t.write("\n>>> [wait {}]\n".format(payload))
                all_rx += drain(payload)
                continue
            t.write("\n>>> [{}]\n".format(raw))
            s.write(payload)
            s.flush()
            all_rx += drain(settle)
        all_rx += drain(final)
    finally:
        t.write(all_rx.decode(errors="replace"))
        t.close()
        s.close()

    text = all_rx.decode(errors="replace").replace("\r", "")
    if quiet:
        lines = [l for l in text.strip().splitlines() if l.strip()]
        print(tty, "TAIL:", repr(lines[-1] if lines else ""))
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
