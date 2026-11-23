"""Situation 7, the chip: Sharpe (Leeds) v Forrest (Ipswich), pool match m912, frames 5282-5379.
A long ball, the aftertouch's HIGH arm, a bounce in the box and the keeper's catch test.

    python3 render_s7.py REC.SRP CAPTURE_DIR OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import CYAN, GREEN, ORANGE, PINK, RED, WHITE, YELLOW, Fig, Match  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = Match(rec, cap)

# 0 -- the lob's second half, over the frame it lands (scale 2: a tall view)
g = Fig(m, 5352, 262, 556, 250, 236, scale=2)
pts = m.ball_path(5282, 5380)
g.path(pts, (255, 255, 255, 255), r=3)
heights = {5316: "45 (peak)", 5334: "35", 5346: "12", 5352: "0: lands", 5364: "16", 5379: "14: in"}
for f, x, y in pts:
    if f in heights:
        p = g.P(x, y)
        g.dot(p, ORANGE, 5)
        g.tag((p[0] + 10, p[1] - 10) if f != 5379 else (p[0] + 34, p[1] - 34), "height " + heights[f], ORANGE)
k = g.ring(g.player(348, 761), CYAN)
g.label((8, 8), ["Sharpe's lob, the second half of its flight",
        "white: the ball's ground track; orange: its height", "(it climbed to 45 from the right wing)"], WHITE, None)
g.save(os.path.join(out, "s7_0_overview.png"), 0, "The lob")

# 1 -- the kick
g = Fig(m, 5282, 400, 436, 200, 124)
s = g.ring(g.player(537, 472), WHITE)
g.label((8, 8), ["Sharpe (Leeds), right wing, 296 out",
        "a long ball down-left, not a shot:", "speed 2208, no bonus"], WHITE, (s[0] - 20, s[1]))
g.save(os.path.join(out, "s7_1_kick.png"), 1, "The long ball")

# 2 -- the HIGH arm
g = Fig(m, 5294, 400, 436, 200, 124)
bb = g.ring(g.ball(502, 511, 12), ORANGE, r=6)
g.label((8, 8), ["Aftertouch step 4: the stick points",
        "back against the kick (diff 3): HIGH.", "Speed 2688 x 7/8 = 2352, lift 2.0:",
        "a chip"], ORANGE, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s7_2_high.png"), 2, "The chip")

# 3 -- the catch gate
g = Fig(m, 5365, 262, 648, 200, 144)
bb = g.ring(g.ball(361, 738, 13), ORANGE, r=6)
k = g.ring(g.player(346, 763), CYAN)
g.label((8, 8), ["Forrest (skill 4): every catch test passes",
        "but one. The ball reaches his line at height", "16, 1 unit from him; but outside the six-yard",
        "box a random gate blocks the catch: the tick's", "nibble 15 >= his 9 (7 ticks in 16 block it)"], CYAN, (k[0] - 20, k[1] - 26))
g.save(os.path.join(out, "s7_3_gate.png"), 3, "The catch gate")

# 4 -- goal
g = Fig(m, 5379, 262, 648, 200, 144)
bb = g.ring(g.ball(341, 770, 14), ORANGE, r=6)
g.d.line([g.P(302, 769), g.P(366, 769)], fill=GREEN, width=3)
g.label((8, 8), ["In the six-yard box the gate is gone and",
        "he goes to catch it (frame 5367) - but he",
        "only takes a ball within 5.6 units of him.", "It drops in at x 341, height 14"], ORANGE, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s7_4_goal.png"), 4, "Goal")

print("ok")
