"""Situation 2, the close-range finish: Mathie (Ipswich) v Nixon (Bradford), pool match m65, frames 731-742.

    python3 render_s2.py REC.SRP CAPTURE_DIR OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import CYAN, GREEN, ORANGE, RED, WHITE, YELLOW, Fig, Match  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = Match(rec, cap)
V = (236, 100, 200, 124)

# 1 -- the shot
g = Fig(m, 731, *V)
g.dashed_rect(241, 129, 431, 204, YELLOW)
g.tag((g.P(244, 196)[0] + 4, g.P(244, 196)[1] - 4), "FINISHING ZONE", YELLOW)
g.dashed(g.P(312, 176), g.P(359, 129), RED)
s = g.ring(g.player(310, 177), WHITE)
g.label((g.P(338, 186)[0], g.P(338, 186)[1]), ["Mathie (Ipswich), 47 units out",
        "Velocity 1, Finishing 7: inside the zone", "2208 + 608 = 2816 (outside it: 1938)"], WHITE, (s[0] + 30, s[1]))
k = g.ring(g.player(320, 135), CYAN)
g.label((g.P(372, 132)[0], g.P(372, 132)[1]), ["Nixon (Bradford)", "skill 3, on his line"], CYAN, (k[0] + 30, k[1]))
g.save(os.path.join(out, "s2_1_shot.png"), 1, "The shot")

# 2 -- the keeper waits
g = Fig(m, 736, *V)
g.band(135, 159, CYAN, "24-unit reaction band", (g.P(380, 160)[0], g.P(380, 160)[1]))
bb = g.ring(g.ball(331, 156, 5), ORANGE, r=6)
g.cross(g.P(349, 135), RED)
k = g.player(322, 135)
g.label((g.P(244, 170)[0], g.P(244, 170)[1]), ["Frame 736: a dive would make it",
        "ball to his line: 6 frames", "dive to x 349: 5 frames",
        "5 < 6, so the game keeps him up"], CYAN, (k[0], k[1] + 20))
g.save(os.path.join(out, "s2_2_wait.png"), 2, "The keeper waits")

# 3 -- the dive falls short
g = Fig(m, 740, *V)
a, b = g.P(331 - 17, 135 - 7), g.P(331 + 5, 135 + 7)
g.d.rectangle([a[0], a[1], b[0], b[1]], outline=CYAN, width=3, fill=(77, 208, 225, 50))
bb = g.ring(g.ball(344, 140, 8), ORANGE, r=6)
g.dimension((g.P(336, 0)[0], g.P(0, 150)[1]), (g.P(344, 0)[0], g.P(0, 150)[1]), ORANGE, "8", above=False)
g.label((g.P(244, 160)[0], g.P(244, 160)[1]), ["Frame 738: 4 frames left, he dives",
        "right. His reach going right: x-17 ... x+5,", "here 314 ... 336. The ball: 344"], CYAN, (a[0], b[1]))
g.save(os.path.join(out, "s2_3_dive.png"), 3, "The dive falls short")

# 4 -- goal
g = Fig(m, 742, *V)
a, b = g.P(339 - 17, 135 - 7), g.P(339 + 5, 135 + 7)
g.d.rectangle([a[0], a[1], b[0], b[1]], outline=CYAN, width=3, fill=(77, 208, 225, 50))
bb = g.ring(g.ball(351, 131, 9), ORANGE, r=6)
g.d.line([g.P(302, 129), g.P(366, 129)], fill=GREEN, width=3)
g.label((g.P(372, 150)[0], g.P(372, 150)[1]), ["In at x 354, height 9",
        "7 beyond his reach.", "11 frames from the kick"], ORANGE, (bb[0] + 12, bb[1] + 6))
g.save(os.path.join(out, "s2_4_goal.png"), 4, "Goal")

print("ok")
