"""Situation 5, the penalty: Bergkamp (Arsenal) v Immel (Manchester City), match t0, frames 1605-1624.

    python3 render_s5.py REC.SRP CAPTURE_DIR OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import CYAN, GREEN, ORANGE, RED, WHITE, YELLOW, Fig, Match  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = Match(rec, cap)
V = (236, 100, 200, 124)          # the view: the goal and the spot

# 1 -- the set-up
g = Fig(m, 1606, *V)
g.dashed_rect(241, 129, 431, 204, YELLOW)
g.tag((g.P(244, 196)[0] + 4, g.P(244, 196)[1] - 4), "FINISHING ZONE", YELLOW)
s = g.ring(g.player(337, 188), WHITE)
g.label((g.P(352, 196)[0], g.P(352, 196)[1]), ["Bergkamp (Arsenal), on the spot",
        "58 units out, inside the zone:", "Finishing 7 sets the pace"], WHITE, (s[0] + 30, s[1]))
k = g.ring(g.player(336, 131), CYAN)
g.label((g.P(370, 136)[0], g.P(370, 136)[1]), ["Immel (Man City)", "skill 5, in the middle"], CYAN, (k[0] + 30, k[1]))
g.save(os.path.join(out, "s5_1_setup.png"), 1, "The set-up")

# 2 -- the kick
g = Fig(m, 1614, *V)
a, b = g.P(336, 187), g.P(307, 129)
g.dashed(a, b, RED)
g.label((g.P(244, 150)[0], g.P(244, 150)[1]), ["The kick: up-left",
        "speed 2208 + 608 = 2816", "5.5 units a frame: 11 frames", "to the line, at x 307"], RED, b)
g.cross(g.P(307, 129), RED)
g.save(os.path.join(out, "s5_2_kick.png"), 2, "The kick")

# 3 -- not yet
g = Fig(m, 1620, *V)
g.band(131, 143, CYAN, "12-unit penalty band", (g.P(372, 132)[0], g.P(372, 132)[1] - 4))
p0, p1 = g.P(236, 143), g.P(436, 151)
g.d.rectangle([p0[0], p0[1], p1[0], p1[1]], fill=(77, 208, 225, 25))
bb = g.ring(g.ball(321, 151, 7), ORANGE, r=6)
g.label((g.P(352, 160)[0], g.P(352, 160)[1]), ["The ball is 20 units away",
        "each check the game draws the gap", "he reacts to: 12 (3 in 4) or 20 (1 in 4).",
        "This time 12: he waits"], CYAN, (bb[0] + 14, bb[1]))
g.save(os.path.join(out, "s5_3_wait.png"), 3, "Not yet")

# 4 -- the dive
g = Fig(m, 1622, *V)
k = g.player(334, 131)
g.arrow((k[0] + 10, k[1] + 34), (k[0] - 60, k[1] + 34), CYAN)
bb = g.ring(g.ball(317, 141, 9), ORANGE, r=6)
g.label((g.P(352, 150)[0], g.P(352, 150)[1]), ["10 units: he dives, the right way",
        "(a wrong-way guess comes 1 time in 4)", "dive speed 2048, about 4 a frame,",
        "and the ball is 2 frames from the line"], CYAN, (k[0] + 20, k[1] + 30))
g.save(os.path.join(out, "s5_4_dive.png"), 4, "The dive")

# 5 -- goal
g = Fig(m, 1624, *V)
a, b = g.P(326 - 5, 131 - 5), g.P(326 + 17, 131 + 5)
g.d.rectangle([a[0], a[1], b[0], b[1]], outline=CYAN, width=3, fill=(77, 208, 225, 50))
bb = g.ring(g.ball(313, 131, 10), ORANGE, r=6)
g.dot(bb, ORANGE, r=5)
g.dimension((g.P(313, 0)[0], g.P(0, 140)[1]), (g.P(321, 0)[0], g.P(0, 140)[1]), ORANGE, "8", above=False)
gl, gr = g.P(302, 129), g.P(366, 129)
g.d.line([gl, gr], fill=GREEN, width=3)
g.label((380, g.P(0, 168)[1]), ["His reach: x 321 ... 343",
        "5 units deep in a penalty", "(7 in open play)"], CYAN, (b[0], (a[1] + b[1]) / 2))
g.label((8, g.P(0, 158)[1]), ["The ball: x 313, height 10",
        "(drawn behind the netting),", "8 outside his reach. Goal."], ORANGE, (bb[0], bb[1] + 12))
g.save(os.path.join(out, "s5_5_goal.png"), 5, "Goal")

print("ok")
