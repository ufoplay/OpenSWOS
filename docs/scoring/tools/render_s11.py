"""Situation 11, the long shot from the side: where to shoot from and where to aim (the shot
lab), and a person's goal of the kind in SWOS 2020's team training (Barcelona v BEGINNER, its
AMIGA (60FPS) style, replay "long from side", frames 530-770 at 60 a second; positions
measured from the replay, rpl.ball).

    python3 render_s11.py REPLAY.RPL CAPTURE_DIR LAB_DIR OUT_DIR

LAB_DIR holds the shot lab's runs (shotlab.sh), each a folder with its all.jsonl: band (the
plain diagonal swept across the goal line, right, keeper 4), bandL (the same from the left),
user (every technique from the person's own spot).
"""
import collections
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab_read  # noqa: E402
import rpl  # noqa: E402
from figlib import CYAN, FONTB, GREEN, ORANGE, PANEL, RED, WHITE, YELLOW, Fig, RplMatch, mosaic  # noqa: E402

rec, cap, lab, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
m = RplMatch(rec, cap)
B = {f: rpl.ball(m.frames[f]) for f in range(530, 770)}
KICK, REKICK, DIVE, GOAL = 686, 698, 738, 743
SPOT = (416, 295)


def track(f0, f1, step=1):
    return [(f, B[f][0], B[f][1]) for f in range(f0, f1 + 1, step) if B.get(f)]


def by_line(path):
    """(y, where the straight diagonal meets the goal line, technique) -> shots."""
    c = collections.defaultdict(list)
    for r in lab_read.load(path):
        x, y = r["target"]
        c[y, x - y + 129, r["tech"]].append(r)
    return c


band = by_line(os.path.join(lab, "band", "all.jsonl"))
bandL = by_line(os.path.join(lab, "bandL", "all.jsonl"))
user = collections.defaultdict(list)
for r in lab_read.load(os.path.join(lab, "user", "all.jsonl")):
    user[r["tech"]].append(r)
pct = lambda v: round(100 * lab_read.rate(v))  # noqa: E731
DISTS = (200, 230, 260, 290, 320)
R_C, L_C = 326, 318                 # the best crossings: right, left (mirrored: 668 - 318 = 350)
for y in DISTS:
    print(y - 129, "out: right", pct(band[y, R_C, "d-plain"]), "% (at 322:", pct(band[y, 322, "d-plain"]),
          ") left", pct(bandL[y, L_C, "d-plain"]), "%")

# ---- 0: the map ------------------------------------------------------------------------------
X0, Y0, W, H = 160, 104, 400, 256
bg = mosaic(m, range(530, 770), X0, Y0, W, H)
g = Fig(m, None, X0, Y0, W, H, scale=2, background=bg)


def band_poly(c0, c1, y0, y1, left=False):
    """The spots whose diagonal meets the goal line between c0 and c1, from y0 to y1."""
    if not left:
        return [g.P(c0 + y0 - 129, y0), g.P(c1 + y0 - 129, y0), g.P(c1 + y1 - 129, y1), g.P(c0 + y1 - 129, y1)]
    a0, a1 = 668 - c0, 668 - c1     # (the mirror: crossing a, spot x = a - (y - 129))
    return [g.P(a0 - (y0 - 129), y0), g.P(a1 - (y0 - 129), y0), g.P(a1 - (y1 - 129), y1), g.P(a0 - (y1 - 129), y1)]


g.d.polygon(band_poly(R_C - 3, R_C + 3, 129, 340), fill=(105, 240, 174, 110), outline=GREEN)
g.d.polygon(band_poly(L_C - 3, L_C + 3, 129, 340, left=True), fill=(105, 240, 174, 55), outline=(105, 240, 174, 150))
for y in DISTS:                     # the measured rates along the right's line
    p = g.P(R_C + y - 129 + 5, y)
    r = pct(band[y, R_C, "d-plain"])
    g.tag((p[0] + 4, p[1] - 12), f"{y - 129} out: {r}%", GREEN if r >= 60 else YELLOW if r >= 30 else RED)
# the red line: a kick along it, from 161 out
sx, sy = R_C + 290 - 129, 290
g.dashed(g.P(sx, sy), g.P(R_C, 129), RED, width=4)
g.dot(g.P(sx, sy), WHITE, 7)
# where it goes in, and the keeper as the ball leaves
g.d.line([g.P(R_C - 4, 129), g.P(R_C + 4, 129)], fill=GREEN, width=8)
v = band[290, R_C, "d-plain"]
gk = (statistics.median(r["kick"]["gk"][0] for r in v), statistics.median(r["kick"]["gk"][1] for r in v))
g.ring(g.P(gk[0] + 6, gk[1] + 4), CYAN, r=8)
# the person's shot: its straight line, its bent and lifted path
g.dashed(g.P(*SPOT), g.P(SPOT[0] - (SPOT[1] - 129), 129), (255, 82, 82, 230), width=3, dash=8, gap=8)
g.path(track(KICK, GOAL, 2), (255, 171, 64, 255), r=3)
g.ring(g.P(*SPOT), WHITE, r=7)
lv = [pct(bandL[y, L_C, "d-plain"]) for y in DISTS[:4]]
g.label(g.P(428, 108), ["Stand on the green line,", "kick along it, no bend:",
                        "in 24 inside the far post,", "past the keeper (cyan)"], GREEN, None)
g.label(g.P(166, 168), ["From the left (pale):", "16 inside the far post,", f"{min(lv)}-{max(lv)}% to 161 out"],
        (105, 240, 174), None)
g.label(g.P(262, 244), ["Your shot (orange):", "its line missed by 52"], ORANGE, g.P(SPOT[0] - 6, SPOT[1]))
g.save(os.path.join(out, "s11_0_map.png"), 0, "Where to shoot from")

# ---- 1: where to aim: the goal line ---------------------------------------------------------
X0, Y0, W, H = 268, 92, 144, 84
g = Fig(m, 700, X0, Y0, W, H, scale=5)
bins = collections.defaultdict(list)    # pooled over 71-161 out: the plain diagonal by its crossing
for (y, c, t), v in band.items():
    if t == "d-plain" and y <= 290:
        bins[c] += v
for c in sorted(bins):
    p = lab_read.rate(bins[c])
    col = GREEN if p >= 0.6 else YELLOW if p >= 0.3 else RED
    x0, x1 = g.P(c - 1.6, 0)[0], g.P(c + 1.6, 0)[0]
    top = g.P(0, 129 - 30 * p)[1]
    g.d.rectangle([x0, top, x1, g.P(0, 129)[1]], fill=col[:3] + (225,))
    if p >= 0.3:
        w = g.d.textlength(f"{round(100 * p)}", font=FONTB)
        g.d.text(((x0 + x1) / 2 - w / 2, top - 22), f"{round(100 * p)}", font=FONTB, fill=col)
k = g.ring(g.player(349, 141), CYAN)
g.tag((g.P(270, 134)[0], g.P(270, 134)[1]), "far post 302", WHITE)
g.tag((k[0] + 30, k[1] - 10), "the keeper", CYAN)
g.label(g.P(318, 150), ["Goals per 100 by where the kick's", "straight line meets the goal line",
                        "(diagonal from the right, 71-161 out)"], GREEN, None)
g.save(os.path.join(out, "s11_1_aim.png"), 1, "Where to aim")

# ---- 2..5: the person's goal ---------------------------------------------------------------
V = (236, 104, 230, 210)
g = Fig(m, KICK, 236, 133, 230, 186)        # (at the kick the picture starts at y 133)
g.dashed(g.P(*SPOT), g.P(250, 129), RED)
s = g.ring(g.player(SPOT[0], SPOT[1] + 2), WHITE)
g.label((g.P(240, 262)[0], g.P(240, 262)[1]), ["The shot: 166 out, 82 right of", "the middle, on the diagonal",
                                              "(red): 52 wide of the far post"], WHITE, (s[0] - 26, s[1]))
k = g.ring(g.player(353, 142), CYAN)
g.label((g.P(380, 160)[0], g.P(380, 160)[1]), ["The keeper", "by his near post"], CYAN, (k[0] + 28, k[1]))
g.save(os.path.join(out, "s11_2_shot.png"), 2, "Wide of the post")

g = Fig(m, 704, *V)
g.dashed(g.P(*SPOT), g.P(250, 129), RED)
g.path(track(KICK, GOAL), (255, 255, 255, 255), r=3, alpha_after=704)
bb = g.ring(g.ball(*B[704]), ORANGE, r=6)
g.label((g.P(240, 250)[0], g.P(240, 250)[1]), ["Bent in from the first update, then", "let go at the fifth (frame 698):",
                                              "re-kicked slower and higher: it climbs", "to 24 and stays in the air"], ORANGE,
        (bb[0] - 10, bb[1] + 12))
g.save(os.path.join(out, "s11_3_lift.png"), 3, "Bent and lifted")

V2 = (262, 100, 160, 130)
g = Fig(m, DIVE, *V2)
g.path(track(KICK, GOAL), (255, 255, 255, 255), r=3, alpha_after=DIVE)
k = g.ring(g.player(330, 138), CYAN)
bb = g.ring(g.ball(*B[DIVE]), ORANGE, r=6)
g.label((g.P(264, 200)[0], g.P(264, 200)[1]), ["He dives 5 frames from the line:", "the ball still flying fast,",
                                              "14 high, 7 units to his left"], CYAN, (k[0] - 10, k[1] + 30))
g.save(os.path.join(out, "s11_4_dive.png"), 4, "Too late")

g = Fig(m, GOAL, *V2)
g.ring(g.ball(*B[GOAL]), ORANGE, r=6)
g.d.line([g.P(302, 129), g.P(366, 129)], fill=GREEN, width=3)
g.label((g.P(264, 200)[0], g.P(264, 200)[1]), ["Over the line at x 316, height 6:",
                                              "14 inside the far post"], ORANGE, None)
g.save(os.path.join(out, "s11_5_goal.png"), 5, "Goal")
print("ok")
