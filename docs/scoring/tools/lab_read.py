"""Reading the shot lab's results (shotlab.py's JSON lines).

    python3 lab_read.py ALL.jsonl            a summary: by technique, the best spots, the aim

Each shot: the spot (where the ball was kicked from, aimed: "target"; as it happened: kick.ball),
the technique, what became of it, and the ball's path frame by frame. `line_x` is where it
crossed the goal line (y 129) or, for one the keeper stopped, where it was going to: the line
through its last two points before he touched it.
"""
import collections
import json
import sys

GOAL_Y, POST_L, POST_R = 129, 302, 366
SAVED = ("caught", "parried")


def load(path):
    rows = []
    for line in open(path):
        r = json.loads(line)
        if r["result"] in ("nokick", "noposs", "touched") or not r.get("kick"):
            continue
        r["line_x"] = line_x(r)
        rows.append(r)
    return rows


def line_x(r):
    if r.get("cross"):
        return r["cross"]["x"]
    stop = min([e[1] for e in r["events"] if e[0] in ("contact", "claim", "parry", "deflect")] or [10 ** 9])
    p = [q for q in r["path"] if q[0] < stop]
    if len(p) < 2:
        return None
    (_, x0, y0, *_), (_, x1, y1, *_) = p[-2], p[-1]
    if y1 >= y0:
        return None
    return round(x1 + (x1 - x0) * (y1 - GOAL_Y) / (y0 - y1))


def rate(rows):
    return sum(r["result"] == "goal" for r in rows) / len(rows) if rows else 0.0


def main():
    rows = load(sys.argv[1])
    print(len(rows), "shots;", collections.Counter(r["result"] for r in rows))
    by = collections.defaultdict(list)
    for r in rows:
        by[r["tech"]].append(r)
    print("\nby technique (all spots):")
    for t in sorted(by, key=lambda t: -rate(by[t])):
        print(f"  {t:14} {len(by[t]):5}  goal {100 * rate(by[t]):5.1f}%")
    cell = collections.defaultdict(list)
    for r in rows:
        cell[tuple(r["target"]), r["tech"]].append(r)
    best = sorted(((rate(v), k, len(v)) for k, v in cell.items()), reverse=True)[:25]
    print("\nbest spot x technique:")
    for g, (spot, t), n in best:
        print(f"  {spot} {t:14} {100 * g:5.1f}% of {n}")
    # where the diagonal, bent shots crossed (or were going to): goals against the rest
    print("\nthe aim: diagonal shots by where they reached the line (far post 302, keeper side 366)")
    h = collections.defaultdict(collections.Counter)
    for r in rows:
        if r["dir"] == 7 and r["line_x"] is not None:
            h[(r["line_x"] - POST_L) // 4 * 4][r["result"]] += 1
    for k in sorted(h):
        if -24 <= k <= 64:
            n = sum(h[k].values())
            print(f"  {k:+4} .. {k + 3:+3} inside: {n:4}  goal {100 * h[k]['goal'] / n:5.1f}%  {dict(h[k])}")


if __name__ == "__main__":
    main()
