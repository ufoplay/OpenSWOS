"""Situation 1 (long shot curled into the far corner): annotated frames from match h49.

Frames: the game's own replay viewer (--view-replay, PC graphics), one PNG per frame.
Positions: world coordinates from the engine log (gdb, trace2.gdb) and the .SRP sprites.
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srp          # noqa: E402
import trace_read   # noqa: E402

S = sys.argv[1]                 # scratchpad
OUT = sys.argv[2]               # output folder
LAG = 3146                      # shot k = frame LAG + k
SCALE = 3

tr = trace_read.read(f"{S}/rec/h49.trace")
fr = srp.frames(srp.load(f"{S}/rec/h49.SRP"))

FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
FONTB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
FONTS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
FONTT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)

WHITE = (255, 255, 255)
RED = (255, 82, 82)
CYAN = (77, 208, 225)
YELLOW = (255, 213, 79)
GREEN = (105, 240, 174)
ORANGE = (255, 171, 64)
PANEL = (16, 20, 28, 215)


def shadow_offset(f):
    s = [(x, y) for img, x, y in tr[f]["sprites"] if img == 1069][0]
    w = [(x, y) for img, x, y in fr[f]["sprites"] if img == 1069][0]
    return s[0] - w[0], s[1] - w[1]


def ball_path(f0, f1):
    """Ground positions of the ball (world) per frame, from its shadow sprite."""
    out = []
    for f in range(f0, f1 + 1):
        w = [(x, y) for img, x, y in fr[f]["sprites"] if img == 1069]
        if w:
            out.append((f, w[0][0], w[0][1] + 2))
    return out


class Fig:
    def __init__(self, frame, wx0, wy0, ww, wh):
        self.frame = frame
        k = frame - LAG
        im = Image.open(f"{S}/shots/h49/swos_shot{k:03d}.png").convert("RGB")
        sox, soy = shadow_offset(frame)
        self.ox, self.oy = sox, soy - 1          # world ground point -> screen pixel
        x0, y0 = wx0 + self.ox, wy0 + self.oy
        self.wx0, self.wy0 = wx0, wy0
        crop = im.crop((x0, y0, x0 + ww, y0 + wh)).resize((ww * SCALE, wh * SCALE), Image.NEAREST)
        self.base = crop.convert("RGBA")
        self.over = Image.new("RGBA", self.base.size, (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.over)

    def P(self, wx, wy, wz=0):
        """World (x, y, height) -> output pixel."""
        return ((wx - self.wx0 + 0.5) * SCALE, (wy - wz - self.wy0 + 0.5) * SCALE)

    # ---- primitives ------------------------------------------------------------------
    def dashed(self, a, b, col, width=3, dash=12, gap=8):
        (x0, y0), (x1, y1) = a, b
        L = math.hypot(x1 - x0, y1 - y0)
        n = int(L // (dash + gap)) + 1
        for i in range(n):
            s = i * (dash + gap) / L
            e = min(1, (i * (dash + gap) + dash) / L)
            if s >= 1:
                break
            self.d.line([(x0 + (x1 - x0) * s, y0 + (y1 - y0) * s),
                         (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)], fill=col, width=width)

    def dashed_rect(self, wx0, wy0, wx1, wy1, col, width=3):
        a, b = self.P(wx0, wy0), self.P(wx1, wy1)
        for p, q in (((a[0], a[1]), (b[0], a[1])), ((b[0], a[1]), (b[0], b[1])),
                     ((b[0], b[1]), (a[0], b[1])), ((a[0], b[1]), (a[0], a[1]))):
            self.dashed(p, q, col, width)

    def body(self, wx, wy, kinds, centre=(6, 8)):
        """Output pixel of the centre of the sprite (image in kinds) drawn nearest world (wx, wy)."""
        x0s, y0s = self.wx0 + self.ox, self.wy0 + self.oy
        best = None
        for img, bx, by in tr[self.frame]["sprites"]:
            if not any(img in k for k in kinds):
                continue
            px, py = (bx - x0s) * SCALE + centre[0] * SCALE, (by - y0s) * SCALE + centre[1] * SCALE
            tx, ty = self.P(wx, wy)
            dd = (px - tx) ** 2 + (py - ty) ** 2
            if best is None or dd < best[0]:
                best = (dd, px, py)
        return best[1], best[2]

    def ring_at(self, xy, col, r=11, width=3):
        x, y = xy
        self.d.ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3], outline=col, width=width)
        return x, y

    def ring(self, wx, wy, col, r=9, wz=0, lift=0, width=3):
        x, y = self.P(wx, wy, wz)
        y -= lift * SCALE
        self.d.ellipse([x - r * SCALE / 3 * 3, y - r * SCALE / 3 * 3, x + r * SCALE / 3 * 3, y + r * SCALE / 3 * 3],
                       outline=col, width=width)
        return x, y

    def arrow(self, a, b, col, width=3, head=12):
        self.d.line([a, b], fill=col, width=width)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (-0.45, 0.45):
            self.d.line([b, (b[0] - head * math.cos(ang + s), b[1] - head * math.sin(ang + s))], fill=col, width=width)

    def dimension(self, a, b, col, label, above=True):
        """A |<--->| measure between two output points on one row, with its label."""
        y = a[1]
        self.d.line([a, b], fill=col, width=2)
        for x in (a[0], b[0]):
            self.d.line([(x, y - 7), (x, y + 7)], fill=col, width=2)
        tw = self.d.textlength(label, font=FONTB)
        tx = (a[0] + b[0]) / 2 - tw / 2
        ty = y - 26 if above else y + 8
        self.d.rounded_rectangle([tx - 5, ty - 2, tx + tw + 5, ty + 20], 5, fill=PANEL)
        self.d.text((tx, ty), label, font=FONTB, fill=col)

    def label(self, xy, lines, col=WHITE, anchor_pt=None, title_col=None):
        """A dark panel of text at output pixel xy (top-left); a leader line to anchor_pt."""
        x, y = xy
        h = 0
        widths = []
        for i, t in enumerate(lines):
            f = FONTB if i == 0 else FONT
            widths.append(self.d.textlength(t, font=f))
            h += 22
        w = max(widths)
        W, H = self.base.size
        x = max(8, min(x, W - w - 24))
        y = max(8, min(y, H - h - 16 - 34))
        if anchor_pt:
            cx = min(max(anchor_pt[0], x), x + w + 16)
            cy = min(max(anchor_pt[1], y), y + h + 8)
            self.d.line([anchor_pt, (cx, cy)], fill=col, width=2)
        self.d.rounded_rectangle([x, y, x + w + 16, y + h + 8], 7, fill=PANEL, outline=col, width=2)
        for i, t in enumerate(lines):
            f = FONTB if i == 0 else FONT
            self.d.text((x + 8, y + 5 + i * 22), t, font=f, fill=(title_col or col) if i == 0 else WHITE)

    def step_badge(self, n, text):
        """The figure's step number and title, top-left."""
        t = f"{n}  {text}"
        w = self.d.textlength(t, font=FONTT)
        H = self.base.size[1]
        self.d.rounded_rectangle([8, H - 44, 8 + w + 20, H - 8], 8, fill=(0, 0, 0, 200))
        self.d.text((18, H - 40), t, font=FONTT, fill=WHITE)

    def frame_tag(self):
        t = f"frame {self.frame}"
        w = self.d.textlength(t, font=FONTS)
        W, H = self.base.size
        self.d.rounded_rectangle([W - w - 22, H - 32, W - 8, H - 8], 6, fill=(0, 0, 0, 170))
        self.d.text((W - w - 15, H - 29), t, font=FONTS, fill=(200, 200, 200))

    def save(self, name):
        self.frame_tag()
        Image.alpha_composite(self.base, self.over).convert("RGB").save(os.path.join(OUT, name), optimize=True)


os.makedirs(OUT, exist_ok=True)
WX0, WY0, WW, WH = 226, 104, 250, 172       # one view for the step figures: the box and the shooter

PATH = ball_path(3205, 3241)
T1, T2, GK = range(227, 530), range(530, 833), range(833, 1065)
BALL = range(1065, 1069)

# ---- 1: the shot -----------------------------------------------------------------------
g = Fig(3205, WX0, WY0, WW, WH)
g.dashed_rect(241, 129, 431, 204, YELLOW)
zx, zy = g.P(241, 204)
g.d.text((zx + 8, zy - 24), "FINISHING ZONE", font=FONTB, fill=YELLOW)
a, b = g.P(400, 248), g.P(281, 129)
g.dashed(a, b, RED, width=3)
g.label((g.P(232, 152)[0], g.P(232, 152)[1]), ["Straight line of the kick",
        "direction 7 (up-left): crosses the line", "at x 281, 21 units wide of the post"], RED, b)
sx, sy = g.ring_at(g.body(404, 252, [T1]), WHITE)
g.label((g.P(300, 258)[0] - 40, g.P(300, 258)[1] - 6), ["Shooter: Mark Hughes (Chelsea)",
        "Velocity 6, Finishing 7 this match", "119 units out: the zone ends at 75"], WHITE, (sx - 20, sy + 6))
kx, ky = g.ring_at(g.body(350, 140, [GK]), CYAN)
g.label((g.P(380, 150)[0], g.P(380, 150)[1]), ["Keeper: Steve Ogrizovic (Coventry)", "skill 4, standing at x 350"], CYAN, (kx + 20, ky))
g.step_badge(1, "The shot")
g.save("s1_1_shot.png")

# ---- 2: the curl -----------------------------------------------------------------------
g = Fig(3221, WX0, WY0, WW, WH)
a, b = g.P(400, 248), g.P(281, 129)
g.dashed(a, b, RED, width=3)
for f, x, y in PATH:
    p = g.P(x, y)
    col = (255, 255, 255, 255) if f <= 3221 else (255, 255, 255, 90)
    r = 3 if f <= 3221 else 2
    g.d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)
bx, by = g.ring_at(g.body(349, 182, [BALL], (2, 2)), ORANGE, r=6)
g.label((g.P(398, 140)[0], g.P(398, 140)[1]), ["Aftertouch bends it",
        "the stick moves to 'up': rightSpin.", "Each update the ball's target moves",
        "further up (-46 x4, then -23 x3)"], ORANGE, (bx + 12, by + 4))
g.label((g.P(232, 205)[0], g.P(232, 205)[1]), ["Two paths", "red dashes: the kick's straight line,",
        "heading wide of the post", "white dots: where the ball really goes"], WHITE, None)
kx, ky = g.ring_at(g.body(348, 144, [GK]), CYAN)
g.step_badge(2, "The curl")
g.save("s1_2_curl.png")

# ---- 3: the dive decision --------------------------------------------------------------
g = Fig(3230, WX0, WY0, WW, WH)
p0, p1 = g.P(WX0, 143), g.P(WX0 + WW, 167)
g.d.rectangle([p0[0], p0[1], p1[0], p1[1]], fill=(77, 208, 225, 55))
_bt = "24-unit reaction band"
_bx, _by = g.P(400, 150)
_bw = g.d.textlength(_bt, font=FONTB)
g.d.rounded_rectangle([_bx - 6, _by - 3, _bx + _bw + 6, _by + 21], 5, fill=PANEL)
g.d.text((_bx, _by), _bt, font=FONTB, fill=CYAN)
kx, ky = g.ring_at(g.body(345, 143, [GK]), CYAN)
cross = g.P(316, 143)
g.d.line([(cross[0] - 9, cross[1] - 9), (cross[0] + 9, cross[1] + 9)], fill=RED, width=4)
g.d.line([(cross[0] - 9, cross[1] + 9), (cross[0] + 9, cross[1] - 9)], fill=RED, width=4)
g.dimension((cross[0], g.P(0, 137)[1]), (g.P(345, 137)[0], g.P(0, 137)[1]), WHITE, "29 units")
bx, by = g.ring_at(g.body(326, 151, [BALL], (2, 2)), ORANGE, r=6)
g.label((g.P(362, 172)[0], g.P(362, 172)[1]), ["The keeper's sums",
        "ball reaches his line in 5 frames", "walking to x 316: 68 frames",
        "=> he must dive (to his left)"], CYAN, (kx + 18, ky + 10))
g.label((g.P(232, 186)[0], g.P(232, 186)[1]), ["Red X: where the ball", "will cross his line (x 316)"], RED, (cross[0], cross[1] + 10))
g.step_badge(3, "The keeper decides")
g.save("s1_3_decision.png")

# ---- 4: the miss -----------------------------------------------------------------------
g = Fig(3236, WX0, WY0, WW, WH)
a, b = g.P(322 - 5, 143 - 7), g.P(322 + 17, 143 + 7)
g.d.rectangle([a[0], a[1], b[0], b[1]], outline=CYAN, width=3, fill=(77, 208, 225, 50))
bx, by = g.ring_at(g.body(311, 135, [BALL], (2, 2)), ORANGE, r=6)
g.dimension((g.P(311, 0)[0], g.P(0, 154)[1]), (g.P(317, 0)[0], g.P(0, 154)[1]), ORANGE, "6", above=False)
g.label((g.P(345, 150)[0], g.P(345, 150)[1]), ["The keeper's reach",
        "the box the ball must enter:", "x-5 ... x+17, within 7 units deep", "here x 317 ... 339"], CYAN, (b[0], (a[1] + b[1]) / 2))
g.label((g.P(232, 168)[0], g.P(232, 168)[1]), ["The ball is at x 311",
        "6 units outside his reach.", "Two frames ago: 8 outside."], ORANGE, (bx, by + 12))
g.step_badge(4, "The dive falls short")
g.save("s1_4_miss.png")

# ---- 5: the goal -----------------------------------------------------------------------
g = Fig(3240, WX0, WY0, WW, WH)
a, b = g.P(302, 129), g.P(366, 129)
g.d.line([a, b], fill=GREEN, width=4)
for x in (a[0], b[0]):
    g.d.line([(x, a[1] - 8), (x, a[1] + 8)], fill=GREEN, width=4)
bx, by = g.ring_at(g.body(303, 129, [BALL], (2, 2)), ORANGE, r=6)
g.label((g.P(372, 140)[0], g.P(372, 140)[1]), ["Goal mouth x 302 ... 366"], GREEN, (b[0], b[1]))
g.label((g.P(232, 160)[0], g.P(232, 160)[1]), ["It crosses at x 303",
        "one unit inside the far post,", "at ground level. 2-2."], ORANGE, (bx, by + 12))
g.step_badge(5, "Goal")
g.save("s1_5_goal.png")

# ---- 0: the whole move on one picture ---------------------------------------------------
g = Fig(3236, WX0, WY0, WW, WH)
g.dashed_rect(241, 129, 431, 204, (255, 213, 79, 150), width=2)
a, b = g.P(400, 248), g.P(281, 129)
g.dashed(a, b, RED, width=3)
for f, x, y in PATH:
    p = g.P(x, y)
    g.d.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=WHITE)
keeper = [(3205, 350, 140), (3218, 350, 144), (3222, 348, 144), (3226, 346, 143), (3230, 345, 143),
          (3232, 337, 143), (3234, 329, 143), (3236, 322, 143), (3238, 315, 143), (3240, 309, 143)]
for f, x, y in keeper:
    p = g.P(x, y)
    g.d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=CYAN)
marks = {3205: "1", 3221: "2", 3230: "3", 3236: "4", 3240: "5"}
for f, x, y in PATH:
    if f in marks:
        p = g.P(x, y)
        g.d.ellipse([p[0] - 13, p[1] - 13, p[0] + 13, p[1] + 13], fill=(0, 0, 0, 210), outline=WHITE, width=2)
        tw = g.d.textlength(marks[f], font=FONTB)
        g.d.text((p[0] - tw / 2, p[1] - 11), marks[f], font=FONTB, fill=WHITE)
g.label((g.P(232, 196)[0], g.P(232, 196)[1] + 20), ["The whole move",
        "white: the ball (ground track)", "red dashes: the kick's straight line",
        "cyan: the keeper", "1-5: the steps below"], WHITE, None)
g.step_badge(0, "Long shot, curled into the far corner")
g.save("s1_0_overview.png")
print("ok")
