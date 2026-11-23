"""Find and describe every goal in .SRP recordings (positions from FRMS sprites)."""
import math
import sys

import srp

BALL = range(1065, 1069)
SHADOW = 1069
GK1 = range(833, 949)     # team 1's keeper
GK2 = range(949, 1065)    # team 2's keeper
T1 = range(227, 530)
T2 = range(530, 833)
GK1_DIVE, GK2_DIVE = 857, 973   # dive animation bases (docs/GAMEPLAY.md §15.5)


def kind(img):
    if img in BALL: return "ball"
    if img == SHADOW: return "shadow"
    if img in GK1: return "gk1"
    if img in GK2: return "gk2"
    if img in T1: return "t1"
    if img in T2: return "t2"
    return None


def parse(f):
    o = {"ball": None, "shadow": None, "gk1": None, "gk2": None, "t1": [], "t2": []}
    for img, x, y in f["sprites"]:
        k = kind(img)
        if k in ("t1", "t2"):
            o[k].append((x, y, img))
        elif k:
            o[k] = (x, y, img)
    return o


def goals(fr):
    out = []
    for i in range(1, len(fr)):
        if (fr[i]["g1"], fr[i]["g2"]) != (fr[i - 1]["g1"], fr[i - 1]["g2"]):
            out.append((i, 1 if fr[i]["g1"] != fr[i - 1]["g1"] else 2))
    return out


def analyse(fr, gframe, team):
    """Walk back from the score change: the frame the ball crossed the line, the kick, the shooter."""
    P = [parse(fr[i]) for i in range(max(0, gframe - 250), gframe + 1)]
    base = max(0, gframe - 250)
    # crossing: last frame where shadow y is inside the field before the score changed
    goal_y = 769 if team == 1 else 129     # team 1 attacks ... decided below by the shadow
    sh = [(base + j, p["shadow"]) for j, p in enumerate(P) if p["shadow"]]
    # which goal: the shadow at the score change
    lastx, lasty = sh[-1][1][0], sh[-1][1][1]
    top = lasty < 449
    line = 129 if top else 769
    cross = None
    for fi, s in reversed(sh):
        if (s[1] > line) if top else (s[1] < line):
            cross = fi
            break
    # kick: walking back from the crossing, the frame where the ball's speed jumps
    def spd(a, b):
        return math.hypot(b[0] - a[0], b[1] - a[1])
    shd = {fi: s for fi, s in sh}
    kick = None
    fi = cross
    while fi - 1 in shd and fi - 2 in shd:
        v1 = spd(shd[fi - 1], shd[fi])
        v0 = spd(shd[fi - 2], shd[fi - 1])
        if v1 > 2.5 and v0 < v1 * 0.55:
            kick = fi - 1
            break
        fi -= 1
        if cross - fi > 200:
            break
    res = {"goal_frame": gframe, "team": team, "cross": cross, "kick": kick, "top": top,
           "line": line, "cross_x": shd[cross][0] if cross in shd else None}
    if kick is None:
        return res
    pk = parse(fr[kick])
    bx, by = shd[kick][0], shd[kick][1]
    best = None
    for side in ("t1", "t2", "gk1", "gk2"):
        lst = pk[side] if side in ("t1", "t2") else ([pk[side]] if pk[side] else [])
        for (x, y, img) in lst:
            d = math.hypot(x - bx, y - by)
            if best is None or d < best[0]:
                best = (d, side, x, y, img)
    keeper = pk["gk2"] if (pk["gk2"] and ((pk["gk2"][1] < 449) == top)) else pk["gk1"]
    res.update({"kick_ball": (bx, by), "shooter": best, "keeper_at_kick": keeper,
                "frames_in_flight": cross - kick})
    # keeper images during the flight: dive?
    imgs = []
    for f in range(kick, cross + 1):
        p = parse(fr[f])
        k = p["gk1"] if (p["gk1"] and ((p["gk1"][1] < 449) == top)) else p["gk2"]
        if k:
            imgs.append(k[2])
    res["keeper_imgs"] = sorted(set(imgs))
    # ball height at the line: shadow y - ball y
    pc = parse(fr[cross])
    if pc["ball"] and pc["shadow"]:
        res["z_at_line"] = pc["shadow"][1] - pc["ball"][1] - 1
    return res


if __name__ == "__main__":
    for path in sys.argv[1:]:
        s = srp.load(path)
        fr = srp.frames(s)
        for g, team in goals(fr):
            r = analyse(fr, g, team)
            print(path.split("/")[-1], r)
