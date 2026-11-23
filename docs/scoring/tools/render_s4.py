"""Situation 4, the header: Vialli (Chelsea) v Bennett (Birmingham), pool match m596, frames 3404-3429.
A shot, a scattered parry, Vialli's header.

    python3 render_s4.py REC.SRP CAPTURE_DIR OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import CYAN, GREEN, ORANGE, PINK, RED, WHITE, YELLOW, Fig, Match  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = Match(rec, cap)
V = (262, 648, 200, 144)

# 1 -- the shot
g = Fig(m, 3404, *V)
g.dashed(g.P(418, 718), g.P(367, 769), RED)
s = g.ring(g.player(414, 717), WHITE)
g.label((8, 8), ["Vialli (Chelsea) shoots", "inside the zone: Finishing 7, 2816",
        "down-left, heading for x 367:", "just wide of the post (366)"], WHITE, (s[0] - 20, s[1] - 26))
k = g.ring(g.player(379, 741), CYAN)
g.label((g.P(270, 700)[0], g.P(270, 700)[1] + 30), ["Bennett (Birmingham)", "skill 3"], CYAN, (k[0] - 30, k[1]))
g.save(os.path.join(out, "s4_1_shot.png"), 1, "The shot")

# 2 -- the parry
g = Fig(m, 3411, *V)
a, b = g.P(396 - 17, 741 - 7), g.P(396 + 5, 741 + 7)
g.d.rectangle([a[0], a[1], b[0], b[1]], outline=CYAN, width=3, fill=(77, 208, 225, 50))
bb = g.ring(g.ball(390, 744, 7), ORANGE, r=6)
g.label((8, 8), ["He dives right, and this time the ball",
        "is inside his reach (x 379 ... 401):", "a scattered parry. Its speed 2740 -> 1536,",
        "sent back out, up and away from goal"], CYAN, (a[0], a[1]))
g.save(os.path.join(out, "s4_2_parry.png"), 2, "The parry")

# 3 -- the header
g = Fig(m, 3416, *V)
s = g.ring(g.player(405, 726), PINK)
bb = g.ring(g.ball(399, 728, 10), ORANGE, r=6)
g.label((8, 8), ["Vialli follows in and heads it",
        "ball height 10: a jump header", "speed 1976 x 1.25 - 144 (heading 4) = 2326",
        "back down-left, the keeper still down"], PINK, (s[0] - 20, s[1] - 26))
g.save(os.path.join(out, "s4_3_header.png"), 3, "The header")

# 4 -- goal
g = Fig(m, 3429, *V)
bb = g.ring(g.ball(355, 771, 11), ORANGE, r=6)
g.d.line([g.P(302, 769), g.P(366, 769)], fill=GREEN, width=3)
g.label((8, 8), ["In at x 355, height 11", "13 frames after the header"], ORANGE, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s4_4_goal.png"), 4, "Goal")

print("ok")
