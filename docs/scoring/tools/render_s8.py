"""Situation 8, the rebound: Derby County v Crystal Palace, pool match m617, frames 3420-3459.
Gabbiadini's shot, Day's scattered parry, Sturridge's finish.

    python3 render_s8.py REC.SRP CAPTURE_DIR OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import CYAN, GREEN, ORANGE, PINK, RED, WHITE, YELLOW, Fig, Match  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = Match(rec, cap)
V = (250, 606, 200, 184)

# 1 -- the shot
g = Fig(m, 3420, *V)
s = g.ring(g.player(400, 644), WHITE)
g.label((8, 8), ["Gabbiadini (Derby) shoots",
        "119 out: Velocity 5, 2208 + 162 = 2370"], WHITE, (s[0] - 20, s[1] - 26))
k = g.ring(g.player(350, 757), CYAN)
g.label((g.P(258, 700)[0], g.P(258, 700)[1] + 40), ["Day (Palace)", "skill 5"], CYAN, (k[0] - 30, k[1]))
g.save(os.path.join(out, "s8_1_shot.png"), 1, "The shot")

# 2 -- the parry
g = Fig(m, 3451, *V)
a, b = g.P(324 - 5, 760 - 7), g.P(324 + 17, 760 + 7)
g.d.rectangle([a[0], a[1], b[0], b[1]], outline=CYAN, width=3, fill=(77, 208, 225, 50))
bb = g.ring(g.ball(322, 758, 4), ORANGE, r=6)
g.label((8, 8), ["Day dives left: the ball is in his reach",
        "a scattered parry: speed x 3/4, and x 7/8", "again (tick bit 4 set): 2055 -> 1286,",
        "sent back out into the six-yard box"], CYAN, (a[0], a[1]))
g.save(os.path.join(out, "s8_2_parry.png"), 2, "The parry")

# 3 -- the finish
g = Fig(m, 3456, *V)
s = g.ring(g.player(321, 752), PINK)
bb = g.ring(g.ball(321, 753, 0), ORANGE, r=6)
g.label((8, 8), ["Sturridge (Derby) is there first",
        "16 units out, inside the zone:", "Finishing 6, 2208 + 480 = 2688",
        "Day is still on the ground"], PINK, (s[0] - 20, s[1] - 26))
g.save(os.path.join(out, "s8_3_finish.png"), 3, "The finish")

# 4 -- goal
g = Fig(m, 3459, *V)
bb = g.ring(g.ball(321, 769, 4), ORANGE, r=6)
g.d.line([g.P(302, 769), g.P(366, 769)], fill=GREEN, width=3)
g.label((8, 8), ["In, 3 frames after the kick",
        "8 frames after the parry"], ORANGE, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s8_4_goal.png"), 4, "Goal")

print("ok")
