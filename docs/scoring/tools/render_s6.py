"""Situation 6, the direct free kick: Lomas (Manchester City) v Watson (Barnsley), pool match m753,
frames 2216-2246.

    python3 render_s6.py REC.SRP CAPTURE_DIR OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import CYAN, GREEN, ORANGE, PINK, RED, WHITE, YELLOW, Fig, Match  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = Match(rec, cap)
V = (262, 606, 200, 184)

# 1 -- the kick
g = Fig(m, 2216, *V)
g.dashed(g.P(384, 664), g.P(384, 769), RED)
s = g.ring(g.player(384, 663), WHITE)
g.label((8, 8), ["Lomas (Man City): free kick, 105 out",
        "a shot, so his Velocity counts: 2", "2208 - 162 = 2046. Aimed straight down:",
        "that line misses the post by 18"], WHITE, (s[0] - 20, s[1] - 26))
k = g.ring(g.player(339, 766), CYAN)
g.label((g.P(270, 700)[0], g.P(270, 700)[1] + 40), ["Watson (Barnsley)", "skill 3"], CYAN, (k[0] - 30, k[1]))
g.save(os.path.join(out, "s6_1_kick.png"), 1, "The free kick")

# 2 -- the curl
g = Fig(m, 2230, *V)
g.dashed(g.P(384, 664), g.P(384, 769), RED)
g.path(m.ball_path(2216, 2246), (255, 255, 255, 255), r=3, alpha_after=2230)
bb = g.ring(g.ball(375, 716, 10), ORANGE, r=6)
g.label((8, 8), ["Aftertouch curls it left",
        "rightSpin: each update the target", "moves left (384 -> -160)"], ORANGE, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s6_2_curl.png"), 2, "The curl")

# 3 -- the keeper waits
g = Fig(m, 2243, *V)
bb = g.ring(g.ball(355, 758, 7), ORANGE, r=6)
k = g.player(344, 766)
g.label((8, 8), ["13.6 units away, height 7:",
        "too far to gather (8.5), too low to catch", "(the catch test wants 12 to 22), and a dive",
        "(2 frames) would beat the ball (3): he waits"], CYAN, (k[0], k[1] - 20))
g.save(os.path.join(out, "s6_3_wait.png"), 3, "The keeper waits")

# 4 -- goal
g = Fig(m, 2246, *V)
bb = g.ring(g.ball(349, 771, 4), ORANGE, r=6)
g.d.line([g.P(302, 769), g.P(366, 769)], fill=GREEN, width=3)
g.label((8, 8), ["One frame earlier he dived; his next",
        "contact check never came. In at x 349,", "height 4, 4 units from where he stood"], ORANGE, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s6_4_goal.png"), 4, "Goal")

print("ok")
