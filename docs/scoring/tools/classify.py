"""Sort every goal in trace4.gdb logs by how it was scored.

    python3 classify.py POOLDIR            one line per goal: match, frame, kind, details

A goal's kind comes from the events before it (the log's own frame numbers):
penalty / own goal from the GOAL line; then the last touch before the goal -- a HEADER
(from a corner if the kick before it was a corner), or a KICK: a direct free kick when
it was taken from a free-kick state (6..12, or 13 = ST_FOUL), a chip when the aftertouch's step-4 test took the
HIGH arm, a one-on-one when the point-blank roll was BEATEN, a rebound when the keeper
or the woodwork touched the ball in the 120 frames before that kick, else close-range
(the Finishing zone) or long-range by where the kick was taken.
"""
import glob
import os
import re
import sys

EV = re.compile(r"^([A-Z_]+) f=(\d+)(.*)$")


def parse(path):
    out = []
    for line in open(path, errors="replace"):
        m = EV.match(line)
        if not m:
            continue
        kv = dict(re.findall(r"(\w+)=([^ ]*(?: [A-Z][A-Z .'-]*?(?= \w+=))?)", m.group(3)))
        out.append((m.group(1), int(m.group(2)), m.group(3).strip(), kv))
    return out


def field(rest, key):
    m = re.search(r"\b" + key + r"=([-\d,]+)", rest)
    return m.group(1) if m else None


def nums(s):
    return [int(v) for v in s.split(",")]


def zone(bx, by):
    return 241 <= bx <= 431 and (by < 204 or by >= 694)


def classify(evs, gi):
    _, gf, grest, _ = evs[gi]
    pen = field(grest, "pen") == "1"
    pens = field(grest, "pens") == "1"
    own = field(grest, "own") == "1"
    if pens:
        return "shootout", None, {}
    if pen:
        kind = "penalty"
    elif own:
        kind = "own goal"
    else:
        kind = None
    # last touch: the last KICK or HEADER before the goal
    j = gi - 1
    while j >= 0 and evs[j][0] not in ("KICK", "HEADER"):
        j -= 1
    if j < 0:
        return kind or "?", None, {}
    tname, tf, trest, _ = evs[j]
    info = {"touch": tname, "touch_f": tf, "flight": gf - tf}
    between = [e for e in evs[j:gi] if e[0] in ("DUEL_BEATEN", "CONTACT", "DEFLECT", "POST", "BAR", "AT")]
    if kind:
        return kind, j, info
    if any(e[0] == "DUEL_BEATEN" for e in between):
        return "one-on-one", j, info
    if tname == "HEADER":
        # the kick that put the ball up for it
        k = j - 1
        while k >= 0 and evs[k][0] not in ("KICK", "HEADER"):
            k -= 1
        st = int(field(evs[k][2], "state") or -1) if k >= 0 and evs[k][0] == "KICK" else -1
        info["cross_state"] = st
        return ("header (corner)" if st in (4, 5) else "header"), j, info
    st = int(field(trest, "state"))
    spl = int(field(trest, "statePl"))
    info["state"] = st
    if spl != 100 and 6 <= st <= 13:          # 6..12 the free-kick spots, 13 ST_FOUL (taken at once)
        info["free kick from"] = field(trest, "ball")
        return "free kick", j, info
    # aftertouch HIGH arm at step 4 -> step-5 line shows dz 2.0 (131072) less one update of gravity
    for e in evs[j:gi]:
        if e[0] == "AT" and field(e[2], "spin") == "5":
            dz = int(field(e[2], "dz"))
            info["dz5"] = dz
            if dz > 100000:
                return "chip", j, info
            break
    # rebound: keeper or woodwork touched the ball shortly before this kick
    for e in evs[max(0, j - 400):j]:
        if e[0] in ("CONTACT", "DEFLECT", "POST", "BAR") and tf - e[1] <= 120:
            info["rebound_from"] = e[0]
            return "rebound", j, info
    bx, by, _ = nums(field(trest, "ball"))
    return ("close-range" if zone(bx, by) else "long shot"), j, info


if __name__ == "__main__":
    pool = sys.argv[1]
    for path in sorted(glob.glob(os.path.join(pool, "m*.log")), key=lambda p: int(re.findall(r"\d+", os.path.basename(p))[0])):
        evs = parse(path)
        for gi, e in enumerate(evs):
            if e[0] != "GOAL":
                continue
            kind, j, info = classify(evs, gi)
            touch = evs[j][2][:150] if j is not None else ""
            print(f"{os.path.basename(path)[:-4]:5} f={e[1]:5} {kind:16} {info}  | {touch}")
