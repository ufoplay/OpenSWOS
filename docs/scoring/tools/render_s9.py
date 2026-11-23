"""Situation 9, the own goal: Derby County v Crystal Palace, pool match m157, frames 6994-7044.
Gabbiadini's shot, Day's touch, Roberts the last to play it.

    python3 render_s9.py REC.SRP CAPTURE_DIR OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import CYAN, GREEN, ORANGE, PINK, RED, WHITE, Fig, Match  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = Match(rec, cap)
V = (240, 630, 210, 160)          # the bottom goal and the shot's start

# 1 -- the shot (the camera is far right here: the view moves right with it)
g = Fig(m, 6994, 262, 630, 210, 160)
g.dashed(g.P(429, 647), g.P(310, 769), RED)
s = g.ring(g.player(429, 646), WHITE)
g.label((8, 8), ["Gabbiadini (Derby) shoots", "122 units out: Velocity 4, +54 = 2262",
        "aimed down-left, across the keeper"], WHITE, (s[0] - 24, s[1] - 20))
k = g.ring(g.player(356, 758), CYAN)
g.label((g.P(256, 700)[0], g.P(256, 700)[1]), ["Day (Palace keeper)"], CYAN, (k[0] - 30, k[1]))
g.save(os.path.join(out, "s9_1_shot.png"), 1, "The shot")

# 2 -- the keeper's touch
g = Fig(m, 7029, *V)
bb = g.ring(g.ball(339, 757, 0), ORANGE, r=6)
g.label((8, 8), ["Day dives and the ball hits his body", "(frame 7029). It stays alive, slowed,",
        "rolling along his goal line"], CYAN, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s9_2_touch.png"), 2, "The keeper's touch")

# 3 -- Roberts
g = Fig(m, 7037, *V)
bb = g.ring(g.ball(317, 761, 0), ORANGE, r=6)
r = g.ring(g.player(314, 749), PINK)
pts = m.ball_path(7029, 7044)
g.path(pts, (255, 255, 255, 255), r=2)
g.label((8, 8), ["Roberts (Palace) reaches it", "at his own post, facing his own goal:",
        "now HE is the last to play it"], PINK, (r[0] - 20, r[1] - 26))
g.save(os.path.join(out, "s9_3_roberts.png"), 3, "The last touch")

# 4 -- goal
g = Fig(m, 7044, *V)
bb = g.ring(g.ball(317, 768, 0), ORANGE, r=6)
g.d.line([g.P(302, 769), g.P(366, 769)], fill=GREEN, width=3)
g.label((8, 8), ["Over the line at x 317", "credited to Roberts: (OG)",
        "a goal for Derby"], ORANGE, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s9_4_goal.png"), 4, "Own goal")

print("ok")
