"""The shot lab's trials: spots x techniques x repeats, shuffled (so each worker plays a mix,
at all sorts of game ticks: the keeper's random draws come from the tick).

    python3 lab_trials.py OUT.json [--calibrate] [--reps N] [--techniques a,b,..]
                          [--grid X0:X1:DX,Y0:Y1:DY | --spots X,Y;X,Y.. | --band Y0:Y1:DY,C0:C1:DC]
                          [--left]

--band: the spots at those distances (y) whose diagonal, kicked straight, would cross the goal
line at C (x = C + y - 129): the aim, swept.

--left plays the same spots and techniques mirrored, from the left of the goal (x -> 668 - x,
the directions and sticks mirrored: 7 <-> 1); the results keep the right's spot as "target"
and say "side": "L".

A spot is where the ball is when it is kicked, attacking the top goal from the right (x > 334;
the left is its mirror). The player is put down RUNUP behind it: he runs that far, stick and
fire held, before the shot charges and goes (measured: 14 units each way on the diagonal;
straight, 17 back and 4 to the left, as the ball sits to his right).

A technique is the shot's direction and the stick at each of the ten aftertouch steps
(-1: let go). From the right: 7 is the diagonal across the keeper, 0 straight up; bending a
diagonal in is the stick at 0 (up), bending a straight one in is 7 (up-left). "lift" lets go
at step 4: the game re-kicks the ball, slower and higher (ApplyBallAfterTouch).
"""
import json
import random
import sys

RUNUP = {7: (14, 14), 0: (-4, 17), 1: (-14, 14)}


def techniques():
    """d: the diagonal, s: straight up. bendK: the stick turned to bend it from aftertouch step K
    (0 at once .. 6 late; the earlier, the more it bends); -lift: let go at step 4."""
    t = {"d-plain": (7, [7] * 10), "d-plain-lift": (7, [7] * 4 + [-1] * 6),
         "s-plain": (0, [0] * 10), "s-bend0-lift": (0, [7] * 4 + [-1] * 6)}
    for k in range(7):
        t[f"d-bend{k}"] = (7, [7] * k + [0] * (10 - k))
    for k in range(3):
        t[f"s-bend{k}"] = (0, [0] * k + [7] * (10 - k))
    for k in range(4):
        t[f"d-bend{k}-lift"] = (7, [7] * k + [0] * (4 - k) + [-1] * 6)
    return t


def main():
    out = sys.argv[1]
    reps = int(sys.argv[sys.argv.index("--reps") + 1]) if "--reps" in sys.argv else 4
    tech = techniques()
    if "--techniques" in sys.argv:
        keep = sys.argv[sys.argv.index("--techniques") + 1].split(",")
        tech = {k: v for k, v in tech.items() if k in keep}
    if "--calibrate" in sys.argv:
        spots = [(420, 260), (380, 200), (480, 320)]
    elif "--spots" in sys.argv:
        spots = [tuple(map(int, p.split(","))) for p in sys.argv[sys.argv.index("--spots") + 1].split(";")]
    elif "--band" in sys.argv:        # by where the diagonal's straight line meets the goal line
        gy, gc = (tuple(map(int, g.split(":"))) for g in sys.argv[sys.argv.index("--band") + 1].split(","))
        spots = [(c + y - 129, y) for y in range(gy[0], gy[1] + 1, gy[2]) for c in range(gc[0], gc[1] + 1, gc[2])]
    elif "--grid" in sys.argv:
        gx, gy = (tuple(map(int, g.split(":"))) for g in sys.argv[sys.argv.index("--grid") + 1].split(","))
        spots = [(x, y) for x in range(gx[0], gx[1] + 1, gx[2]) for y in range(gy[0], gy[1] + 1, gy[2])]
    else:
        spots = [(x, y) for x in range(334, 535, 20) for y in range(180, 341, 20)]
    left = "--left" in sys.argv
    mir = (lambda v: (8 - v) % 8 if v >= 0 else v) if left else (lambda v: v)
    trials = []
    for (x, y) in spots:
        for name, (d, at) in tech.items():
            for r in range(reps):
                dd = mir(d)
                rx, ry = RUNUP[dd] if dd != 0 else RUNUP[0]
                wx = 668 - x if left else x
                trials.append({"id": f"{'L' if left else ''}{name}@{x},{y}#{r}", "tech": name, "target": [x, y],
                               "side": "L" if left else "R", "spot": [wx + rx, y + ry], "dir": dd,
                               "at": [mir(v) for v in at]})
    random.Random(1).shuffle(trials)
    json.dump(trials, open(out, "w"))
    print(f"{len(trials)} trials: {len(spots)} spots x {len(tech)} techniques x {reps}")


main()
