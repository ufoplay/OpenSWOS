"""Situation 3, the point-blank roll: Hughes (Chelsea) v Bennett (Birmingham), match m16 of the
human-fire batch (human_fire.gdb), frames 6354-6373.

    python3 render_s3.py REC.SRP CAPTURE_DIR OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import CYAN, GREEN, ORANGE, PINK, RED, WHITE, YELLOW, Fig, Match  # noqa: E402

rec, cap, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
m = Match(rec, cap)
V = (236, 648, 200, 144)          # the bottom goal

# 1 -- the shot
g = Fig(m, 6354, *V)
g.dashed_rect(241, 694, 431, 769, YELLOW)
g.tag((g.P(380, 700)[0], g.P(380, 700)[1] + 2), "FINISHING ZONE", YELLOW)
g.dashed(g.P(303, 713), g.P(359, 769), RED)
s = g.ring(g.player(297, 708), WHITE)
g.label((8, 8), ["Hughes (Chelsea), 56 units out",
        "Finishing 7: 2208 + 608 = 2816", "and, as a human would, fire held"], WHITE, (s[0], s[1] - 32))
k = g.ring(g.player(319, 744), CYAN)
g.label((g.P(380, 650)[0], 8), ["Bennett (Birmingham)", "skill 3"], CYAN, (k[0] + 30, k[1]))
g.save(os.path.join(out, "s3_1_shot.png"), 1, "The shot")

# 2 -- the roll
g = Fig(m, 6361, *V)
bb = g.ring(g.ball(329, 735, 6), ORANGE, r=6)
k = g.ring(g.player(322, 746), CYAN)
g.label((8, 8), ["8.6 units from the keeper, fire down:",
        "the roll. Finishing read: 5 (see below)", "5 - keeper 3 + 8 = 10 chances in 16",
        "the tick draws 1: 1 < 10, BEATEN"], PINK, (bb[0] - 10, bb[1] - 14))
g.save(os.path.join(out, "s3_2_roll.png"), 2, "The roll")

# 3 -- the beaten keeper's dive
g = Fig(m, 6365, *V)
a, b = g.P(329 - 17, 746 - 7), g.P(329 + 5, 746 + 7)
g.d.rectangle([a[0], a[1], b[0], b[1]], outline=CYAN, width=3, fill=(77, 208, 225, 50))
bb = g.ring(g.ball(337, 741, 9), ORANGE, r=6)
g.dimension((g.P(334, 0)[0], g.P(0, 735)[1]), (g.P(337, 0)[0], g.P(0, 735)[1]), ORANGE, "3")
g.label((g.P(352, 650)[0], 8), ["A beaten keeper's dive",
        "speed 1024 + (tick & 255) = 1059,", "not 2048; the ball capped at 1536.",
        "Reach x 312 ... 334, ball at 337"], CYAN, (b[0], a[1]))
g.save(os.path.join(out, "s3_3_dive.png"), 3, "Beaten")

# 4 -- goal
g = Fig(m, 6373, *V)
bb = g.ring(g.ball(351, 758, 10), ORANGE, r=6)
g.d.line([g.P(302, 769), g.P(366, 769)], fill=GREEN, width=3)
g.label((8, 8), ["In at x 353", "the keeper still sliding at x 339"], ORANGE, (bb[0] - 10, bb[1] - 12))
g.save(os.path.join(out, "s3_4_goal.png"), 4, "Goal")

print("ok")
