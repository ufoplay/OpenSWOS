"""Situation 10, the central shot bent past the keeper: a human player's goal in SWOS 2020's team
training (Lazio v BEGINNER, its AMIGA (60FPS) style), replay "central then bend", frames
3216-3466 at 60 a second. Positions are measured from the replay (rpl.ball); nothing logged it.

    python3 render_s10.py REPLAY.RPL CAPTURE_DIR OUT_DIR      (CAPTURE_DIR: capture_rpl.py's)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpl  # noqa: E402
from figlib import CYAN, GREEN, ORANGE, RED, WHITE, YELLOW, Fig, RplMatch  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = RplMatch(rec, cap)
B = {f: rpl.ball(m.frames[f]) for f in range(3216, 3467)}


def track(f0, f1, step=1):
    return [(f, B[f][0], B[f][1]) for f in range(f0, f1 + 1, step) if B.get(f)]


# 0 -- the move: the ball's track while he had it, then the shot
g = Fig(m, 3424, 236, 108, 210, 254, scale=2)
g.path(track(3226, 3424, 3), (255, 255, 255, 170), r=2)
g.path(track(3424, 3454), (255, 171, 64, 255), r=3)
for f, txt, dx, dy in ((3226, "has it, frame 3226", 14, -10), (3366, "turns, 3366", -150, -36),
                       (3424, "shoots, 3424", 16, -4)):
    p = g.P(B[f][0], B[f][1])
    g.dot(p, YELLOW, 6)
    g.tag((p[0] + dx, p[1] + dy), txt, YELLOW)
g.label((8, 300), ["The move: 3.3 seconds on the ball", "white: the ball while he ran with it",
                   "orange: the shot"], WHITE, None)
g.save(os.path.join(out, "s10_0_overview.png"), 0, "The run")

# 1 -- the shot
g = Fig(m, 3424, 262, 104, 160, 150)
g.dashed(g.P(341, 239), g.P(341, 129), RED)
s = g.ring(g.player(341, 240), WHITE)
g.label((8, 230), ["The shot: 110 out, 7 right of", "the middle, kicked straight up",
                   "the pitch: at the keeper", "(red: the line it set off on)"], WHITE, (s[0] - 26, s[1] - 10))
k = g.ring(g.player(334, 140), CYAN)
g.label((g.P(366, 150)[0], g.P(366, 150)[1]), ["The keeper", "in line with it"], CYAN, (k[0] + 30, k[1]))
g.save(os.path.join(out, "s10_1_shot.png"), 1, "At the keeper")

V = (262, 96, 160, 130)
# 2 -- the bend
g = Fig(m, 3442, *V)
g.dashed(g.P(341, 239), g.P(341, 129), RED)
g.path(track(3424, 3454), (255, 255, 255, 255), r=3, alpha_after=3442)
bb = g.ring(g.ball(*B[3442]), ORANGE, r=6)
g.label((8, 200), ["Aftertouch bends it left: straight", "for 8 frames, then curling more and",
                   "more: 24 units off its line by the goal"], ORANGE, (bb[0] - 10, bb[1] + 14))
k = g.player(331, 138)
g.label((g.P(352, 136)[0], g.P(352, 136)[1]), ["He shuffles after it:", "2 units in 18 frames"],
        CYAN, (k[0] + 24, k[1]))
g.save(os.path.join(out, "s10_2_bend.png"), 2, "The bend")

# 3 -- the dive
g = Fig(m, 3450, *V)
g.path(track(3424, 3454), (255, 255, 255, 255), r=3, alpha_after=3450)
k = g.ring(g.player(327, 137), CYAN)
bb = g.ring(g.ball(*B[3450]), ORANGE, r=6)
g.label((8, 200), ["He dives only now, 4 frames from the", "line: the ball is 5 units to his left,",
                   "6 in front of him, at height 12"], CYAN, (k[0] - 10, k[1] + 30))
g.save(os.path.join(out, "s10_3_dive.png"), 3, "Too late")

# 4 -- goal
g = Fig(m, 3453, *V)
bb = g.ring(g.ball(*B[3453]), ORANGE, r=6)
g.d.line([g.P(302, 129), g.P(366, 129)], fill=GREEN, width=3)
g.dashed(g.P(334, 129), g.P(334, 152), CYAN, width=2)
g.label((8, 200), ["Over the line the next frame, at x 317", "and height 10: 17 units left of where",
                   "the keeper stood (cyan), 15 inside the post"], ORANGE, (bb[0], bb[1] + 16))
g.save(os.path.join(out, "s10_4_goal.png"), 4, "Goal")
print("ok")
