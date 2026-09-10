#!/usr/bin/env python3
"""Render tb470.setup from bench-state.md and write it IN PLACE on the testbox.

bench-state.md is the source of truth. Every fenced ```setup block in it is
concatenated in document order to form the .setup file; prose outside the fences
never reaches the testbox.

    ./bench_setup.py render          # to stdout, touch nothing
    ./bench_setup.py check           # compare against the live file, exit 1 on drift
    ./bench_setup.py apply           # snapshot into backups/, then write in place

No .bak files are left beside the live file -- history lives in ./backups/.

apply REFUSES if the live file has drifted from tb470.setup.current (i.e. someone
hand-edited the box) so that an apply cannot silently discard their work. Override
with --force, which still snapshots first.
"""
import hashlib
import io
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "bench-state.md")
CURRENT = os.path.join(HERE, "tb470.setup.current")
STATE_MIRROR = os.path.join(HERE, "bench-state.current.md")
BACKUPS = os.path.join(HERE, "backups")

BOX = "tb470"
REMOTE = "/home/st-art/st-art/configs/tb470.setup"
SOCK = "/run/user/1971/keyring/ssh"
FENCE_OPEN = "```setup"
FENCE_CLOSE = "```"


def sha(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def render():
    """Concatenate every ```setup fence, in document order."""
    lines = io.open(STATE, encoding="utf-8").read().split("\n")
    blocks, buf, inside = [], None, False
    for n, ln in enumerate(lines, 1):
        if not inside:
            if ln.rstrip() == FENCE_OPEN:
                inside, buf = True, []
        elif ln.rstrip() == FENCE_CLOSE:
            blocks.append("\n".join(buf))
            inside, buf = False, None
        else:
            buf.append(ln)
    if inside:
        sys.exit("bench-state.md: unterminated ```setup fence")
    if not blocks:
        sys.exit("bench-state.md: no ```setup fences found -- nothing to render")
    return "\n".join(blocks) + "\n"


def ssh(args, stdin=None):
    env = dict(os.environ, SSH_AUTH_SOCK=SOCK)
    return subprocess.run(["ssh", BOX] + args, env=env, input=stdin,
                          stdout=subprocess.PIPE, check=True).stdout


def live():
    return ssh(["cat " + REMOTE]).decode("utf-8")


def snapshot(setup_text):
    """Archive the outgoing PAIR under one timestamp: the .setup that is about to be
    replaced, and the bench-state.md that produced it. The record is what matters --
    snapshotting only the generated file would keep the reflection and lose the source.

    `bench-state.md` always names the current truth; superseded versions are dated here.
    """
    if not os.path.isdir(BACKUPS):
        os.makedirs(BACKUPS)
    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    made = []
    p = os.path.join(BACKUPS, stamp + ".tb470.setup")
    io.open(p, "w", encoding="utf-8").write(setup_text)
    made.append(p)
    if os.path.exists(STATE_MIRROR):
        q = os.path.join(BACKUPS, stamp + ".bench-state.md")
        io.open(q, "w", encoding="utf-8").write(
            io.open(STATE_MIRROR, encoding="utf-8").read())
        made.append(q)
    return made


def _archive_state_if_changed():
    """Date the SUPERSEDED bench-state.md; the live one keeps its name.

    bench-state.md is never renamed or moved -- it always names the current truth, so
    every pointer to it stays correct. What gets a date is the version being replaced,
    written to backups/<stamp>.bench-state.md where <stamp> is the moment it was
    superseded, not the moment it was authored.
    """
    now = io.open(STATE, encoding="utf-8").read()
    was = io.open(STATE_MIRROR, encoding="utf-8").read() if os.path.exists(STATE_MIRROR) else None
    if was is None or was == now:
        return
    if not os.path.isdir(BACKUPS):
        os.makedirs(BACKUPS)
    stamp = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    p = os.path.join(BACKUPS, stamp + ".bench-state.md")
    io.open(p, "w", encoding="utf-8").write(was)
    io.open(STATE_MIRROR, "w", encoding="utf-8").write(now)
    print("record changed -> superseded version dated as %s" % os.path.basename(p))


def main():
    argv = sys.argv[1:]
    force = "--force" in argv
    cmd = ([a for a in argv if not a.startswith("-")] or ["check"])[0]

    if cmd == "render":
        sys.stdout.write(render())
        return 0

    want = render()
    have = live()
    cur = io.open(CURRENT, encoding="utf-8").read() if os.path.exists(CURRENT) else None

    print("render  %s  (%d bytes, %d sections)" % (sha(want), len(want), want.count("\n[")))
    print("live    %s  (%d bytes)" % (sha(have), len(have)))
    if cur is not None:
        print("current %s" % sha(cur))

    if cmd == "check":
        if want == have:
            print("\nIN SYNC")
            return 0
        print("\nDRIFT -- live differs from render. `apply` would change the box.")
        return 1

    if cmd != "apply":
        sys.exit("unknown command %r -- render | check | apply" % cmd)

    if want == have:
        print("\nthe testbox is already in sync -- nothing written there")
        if cur != have:
            io.open(CURRENT, "w", encoding="utf-8").write(have)
            print("refreshed tb470.setup.current")
        # A prose-only edit to the record does not move the render, but it IS a new
        # version of the record and must still be dated. Otherwise history keeps the
        # reflection and silently loses the source.
        _archive_state_if_changed()
        return 0

    if cur is not None and have != cur and not force:
        print("\nREFUSING: the live file does not match tb470.setup.current.")
        print("Someone hand-edited %s:%s. Reconcile that into bench-state.md" % (BOX, REMOTE))
        print("first, or re-run with --force (which snapshots the live file regardless).")
        return 2

    for p in snapshot(have):
        print("\nsnapshot -> %s" % p)
    ssh(["cat > " + REMOTE], stdin=want.encode("utf-8"))
    back = live()
    if back != want:
        print("VERIFY FAILED: readback does not match the render")
        return 3
    io.open(CURRENT, "w", encoding="utf-8").write(want)
    io.open(STATE_MIRROR, "w", encoding="utf-8").write(
        io.open(STATE, encoding="utf-8").read())
    print("written in place and verified by readback")
    return 0


if __name__ == "__main__":
    sys.exit(main())
