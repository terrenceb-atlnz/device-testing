"""filewin.py <path> [--from OFFSET] [--grep REGEX] [--max-lines N] [--quiet]

Reads a WINDOW of a growing text file: the bytes it gained since a byte offset the
caller recorded earlier. It is the instrument for grading a case against a file that
some OTHER process writes and keeps appending to -- a TACACS+ accounting file, a
syslog, a RADIUS detail file, a daemon log -- where the whole file is history and only
this case's own window is evidence.

Why an offset and not `tail -n`: a tail of N lines is not a window. It silently drops
evidence when the writer is busy and silently re-reads old records when it is idle,
and neither failure is visible in the output. An offset recorded before the step and
read after it bounds the window exactly, and the header says how many bytes arrived,
so ZERO new bytes is a measurement rather than an absence of output.

To MARK the file before a step, call it with `--quiet` and no `--from`: the header alone
is printed. Record its `size=`, run the step, then call again with `--from <that size>`
to read exactly the window the step produced. Without `--from` it reads from byte 0, so
a first call without `--quiet` prints the whole file.

Header line, always printed first, on stdout:
    FILEWIN <path> size=<bytes now> from=<offset> new-bytes=<n> new-lines=<n> matched=<n>
then the matching new lines, one per line, unchanged.

Exit: 0 the file was read; 3 the file does not exist or is not readable (a first-class
result -- a server that never wrote anything, or a file the case may not read); 4 the
file SHRANK below --from (it was rotated or truncated: the window is not trustworthy,
and everything from byte 0 is printed instead); 6 usage.

Reads only; writes nothing anywhere. Runs anywhere, needs nothing beyond Python.
"""
import os, re, sys

def die(msg, code=6):
    sys.stderr.write("filewin.py: %s\nusage: filewin.py <path> [--from OFFSET] "
                     "[--grep REGEX] [--max-lines N] [--quiet]\n" % msg)
    sys.exit(code)

a = sys.argv[1:]
if not a or a[0] in ("-h", "--help"):
    sys.stdout.write(__doc__)
    sys.exit(0 if a else 6)

path = a[0]
off = 0
pat = None
maxl = 0
quiet = False
i = 1
while i < len(a):
    o = a[i]
    if o == "--from":
        i += 1
        if i >= len(a):
            die("--from needs an offset")
        try:
            off = int(a[i])
        except ValueError:
            die("--from must be an integer, got %r" % a[i])
        if off < 0:
            die("--from must not be negative")
    elif o == "--grep":
        i += 1
        if i >= len(a):
            die("--grep needs a regex")
        try:
            pat = re.compile(a[i])
        except re.error as e:
            die("bad --grep regex: %s" % e)
    elif o == "--max-lines":
        i += 1
        if i >= len(a):
            die("--max-lines needs a number")
        try:
            maxl = int(a[i])
        except ValueError:
            die("--max-lines must be an integer, got %r" % a[i])
    elif o == "--quiet":
        quiet = True
    else:
        die("unknown option %r" % o)
    i += 1

try:
    size = os.path.getsize(path)
    fh = open(path, "rb")
except OSError as e:
    sys.stdout.write("FILEWIN %s UNREADABLE (%s)\n" % (path, e.strerror or e))
    sys.exit(3)

rc = 0
start = off
if off > size:
    # rotated or truncated: the recorded offset no longer points into this file
    start = 0
    rc = 4

with fh:
    fh.seek(start)
    data = fh.read()

text = data.decode("utf-8", "replace")
lines = text.splitlines()
# a trailing partial line (the writer may be mid-append) is kept: it is still evidence
shown = [l for l in lines if pat is None or pat.search(l)]
total = len(shown)
if maxl and total > maxl:
    shown = shown[-maxl:]

sys.stdout.write("FILEWIN %s size=%d from=%d new-bytes=%d new-lines=%d matched=%d%s\n"
                 % (path, size, start, len(data), len(lines), total,
                    "  (ROTATED: offset was past end, read from 0)" if rc == 4 else ""))
if not quiet:
    for l in shown:
        sys.stdout.write(l + "\n")
sys.exit(rc)
