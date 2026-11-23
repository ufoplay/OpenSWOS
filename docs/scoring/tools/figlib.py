"""Annotated figures over frames rendered by capture.py (shared by the render_s*.py scripts).

A Fig is one frame, cropped to a world rectangle and scaled 3x. P(x, y, z) turns a world
point (z: height) into a picture pixel; body() finds the drawn sprite nearest a world point.
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpl          # noqa: E402
import srp          # noqa: E402
import trace_read   # noqa: E402

SCALE = 3
_FONTDIR = "/usr/share/fonts/truetype/dejavu/"
FONT = ImageFont.truetype(_FONTDIR + "DejaVuSans.ttf", 17)
FONTB = ImageFont.truetype(_FONTDIR + "DejaVuSans-Bold.ttf", 17)
FONTS = ImageFont.truetype(_FONTDIR + "DejaVuSans.ttf", 15)
FONTT = ImageFont.truetype(_FONTDIR + "DejaVuSans-Bold.ttf", 22)

WHITE = (255, 255, 255)
RED = (255, 82, 82)
CYAN = (77, 208, 225)
YELLOW = (255, 213, 79)
GREEN = (105, 240, 174)
ORANGE = (255, 171, 64)
PINK = (240, 98, 146)
PANEL = (16, 20, 28, 215)

PLAYERS = range(227, 833)
GK = range(833, 1065)
BALL = range(1065, 1069)
SHADOW = 1069


class Match:
    """A recording, its replay trace and its captured frames."""

    def __init__(self, srp_path, shots_dir):
        self.frames = srp.frames(srp.load(srp_path))
        self.trace = trace_read.read(os.path.join(shots_dir, "trace.txt"))
        self.shots = shots_dir

    def shadow_offset(self, f):
        s = [(x, y) for img, x, y in self.trace[f]["sprites"] if img == SHADOW][0]
        w = [(x, y) for img, x, y in self.frames[f]["sprites"] if img == SHADOW][0]
        return s[0] - w[0], s[1] - w[1]

    def ball_path(self, f0, f1):
        """(frame, x, y) of the ball on the ground (its shadow), world."""
        out = []
        for f in range(f0, f1 + 1):
            w = [(x, y) for img, x, y in self.frames[f]["sprites"] if img == SHADOW]
            if w:
                out.append((f, w[0][0], w[0][1] + 2))
        return out


class RplMatch(Match):
    """A PC / SWOS 2020 replay (.RPL) and the frames capture_rpl.py rendered from it. The
    replay gives the world positions; screen.txt where the viewer drew them, frame by frame."""

    def __init__(self, rpl_path, shots_dir):
        self.frames = rpl.frames(rpl_path)
        self.shots = shots_dir
        self.trace = {}
        for line in open(os.path.join(shots_dir, "screen.txt")):
            f, ox, oy = map(int, line.split())
            self.trace[f] = {"sprites": [(i, x + ox, y + oy) for i, x, y in self.frames[f]["screen"]]}


def mosaic(match, frames, wx0, wy0, ww, wh):
    """The pitch itself over a world rectangle, with nobody on it: from many captured frames,
    each pixel's median (as a packed colour: always one the game drew) over the frames that
    show it. Players move, the grass and the lines stay."""
    import numpy as np
    stack, have = [], []
    for f in frames:
        if f not in match.trace:
            continue
        sox, soy = match.shadow_offset(f)
        a = np.asarray(Image.open(os.path.join(match.shots, f"f{f}.png")).convert("RGB")).astype(np.int64)
        packed = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
        H, W = packed.shape
        out = np.full((wh, ww), -1, np.int64)
        ys, xs = np.mgrid[0:wh, 0:ww]
        px, py = xs + wx0 + sox, ys + wy0 + soy - 1
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        out[ok] = packed[py[ok], px[ok]]
        stack.append(out)
    st = np.stack(stack)
    s = np.sort(st, axis=0)                                 # -1 (not shown) sorts first
    n = (s >= 0).sum(0)
    first = s.shape[0] - n
    med = np.take_along_axis(s, (first + n // 2).clip(max=s.shape[0] - 1)[None], 0)[0]
    med[n == 0] = 0
    # The lines are a pixel thin and the frames' cameras a pixel apart now and then: a pixel
    # that showed line white in a quarter of its frames is line.
    white = (((st >> 16) & 255) > 200) & (((st >> 8) & 255) > 200) & ((st & 255) > 200) & (st >= 0)
    line = white.sum(0) * 4 >= np.maximum(n, 1)
    med[line] = 0xFFFFFF
    rgb = np.stack([(med >> 16) & 255, (med >> 8) & 255, med & 255], -1).astype(np.uint8)
    return Image.fromarray(rgb)


class Fig:
    def __init__(self, match, frame, wx0, wy0, ww, wh, offset_frame=None, scale=SCALE, background=None):
        if background is not None:      # a picture of the world rectangle already (mosaic)
            self.m, self.s, self.frame = match, scale, frame
            self.ox = self.oy = 0
            self.wx0, self.wy0 = wx0, wy0
            self.base = background.resize((ww * scale, wh * scale), Image.NEAREST).convert("RGBA")
            self.over = Image.new("RGBA", self.base.size, (0, 0, 0, 0))
            self.d = ImageDraw.Draw(self.over)
            return
        self.m = match
        self.s = scale
        self.frame = frame
        im = Image.open(os.path.join(match.shots, f"f{frame}.png")).convert("RGB")
        sox, soy = match.shadow_offset(offset_frame or frame)
        self.ox, self.oy = sox, soy - 1
        self.wx0, self.wy0 = wx0, wy0
        x0, y0 = wx0 + self.ox, wy0 + self.oy
        crop = im.crop((x0, y0, x0 + ww, y0 + wh)).resize((ww * scale, wh * scale), Image.NEAREST)
        self.base = crop.convert("RGBA")
        self.over = Image.new("RGBA", self.base.size, (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.over)

    def P(self, wx, wy, wz=0):
        return ((wx - self.wx0 + 0.5) * self.s, (wy - wz - self.wy0 + 0.5) * self.s)

    def body(self, wx, wy, kinds, centre=(6, 8)):
        """Picture pixel of the centre of the sprite (image in kinds) drawn nearest world (wx, wy)."""
        x0s, y0s = self.wx0 + self.ox, self.wy0 + self.oy
        best = None
        tx, ty = self.P(wx, wy)
        for img, bx, by in self.m.trace[self.frame]["sprites"]:
            if not any(img in k for k in kinds):
                continue
            px, py = (bx - x0s) * self.s + centre[0] * self.s, (by - y0s) * self.s + centre[1] * self.s
            dd = (px - tx) ** 2 + (py - ty) ** 2
            if best is None or dd < best[0]:
                best = (dd, px, py)
        return (best[1], best[2]) if best else (tx, ty)

    def ball(self, wx, wy, wz=0):
        return self.body(wx, wy - wz, [BALL], (2, 2))

    def player(self, wx, wy):
        return self.body(wx, wy, [PLAYERS, GK])

    # ---- drawing ------------------------------------------------------------------------
    def dashed(self, a, b, col, width=3, dash=12, gap=8):
        (x0, y0), (x1, y1) = a, b
        L = math.hypot(x1 - x0, y1 - y0) or 1
        i = 0
        while i * (dash + gap) < L:
            s = i * (dash + gap) / L
            e = min(1, (i * (dash + gap) + dash) / L)
            self.d.line([(x0 + (x1 - x0) * s, y0 + (y1 - y0) * s), (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)],
                        fill=col, width=width)
            i += 1

    def dashed_rect(self, wx0, wy0, wx1, wy1, col, width=3):
        a, b = self.P(wx0, wy0), self.P(wx1, wy1)
        for p, q in (((a[0], a[1]), (b[0], a[1])), ((b[0], a[1]), (b[0], b[1])),
                     ((b[0], b[1]), (a[0], b[1])), ((a[0], b[1]), (a[0], a[1]))):
            self.dashed(p, q, col, width)

    def ring(self, xy, col, r=11, width=3):
        x, y = xy
        self.d.ellipse([x - r * self.s, y - r * self.s, x + r * self.s, y + r * self.s], outline=col, width=width)
        return x, y

    def dot(self, xy, col, r=3):
        x, y = xy
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def cross(self, xy, col, r=9):
        x, y = xy
        self.d.line([(x - r, y - r), (x + r, y + r)], fill=col, width=4)
        self.d.line([(x - r, y + r), (x + r, y - r)], fill=col, width=4)

    def arrow(self, a, b, col, width=3, head=12):
        self.d.line([a, b], fill=col, width=width)
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for s in (-0.45, 0.45):
            self.d.line([b, (b[0] - head * math.cos(ang + s), b[1] - head * math.sin(ang + s))], fill=col, width=width)

    def path(self, pts, col, r=3, alpha_after=None):
        """Dots at world (x, y) points; points after frame alpha_after are faint."""
        for f, x, y in pts:
            c = col if alpha_after is None or f <= alpha_after else col[:3] + (90,)
            self.dot(self.P(x, y), c, r if alpha_after is None or f <= alpha_after else 2)

    def dimension(self, a, b, col, label, above=True):
        y = a[1]
        self.d.line([a, (b[0], y)], fill=col, width=2)
        for x in (a[0], b[0]):
            self.d.line([(x, y - 7), (x, y + 7)], fill=col, width=2)
        tw = self.d.textlength(label, font=FONTB)
        tx = (a[0] + b[0]) / 2 - tw / 2
        ty = y - 26 if above else y + 8
        self.d.rounded_rectangle([tx - 5, ty - 2, tx + tw + 5, ty + 20], 5, fill=PANEL)
        self.d.text((tx, ty), label, font=FONTB, fill=col)

    def band(self, wy0, wy1, col, text=None, text_at=None):
        a, b = self.P(self.wx0, wy0), self.P(self.wx0 + self.base.size[0] / self.s, wy1)
        self.d.rectangle([a[0], a[1], b[0], b[1]], fill=col[:3] + (55,))
        if text:
            x, y = text_at
            w = self.d.textlength(text, font=FONTB)
            x = max(14, min(x, self.base.size[0] - w - 16))
            self.d.rounded_rectangle([x - 6, y - 3, x + w + 6, y + 21], 5, fill=PANEL)
            self.d.text((x, y), text, font=FONTB, fill=col)

    def tag(self, xy, text, col):
        """A one-line tag at a picture pixel (its top-left)."""
        x, y = xy
        w = self.d.textlength(text, font=FONTB)
        x = max(14, min(x, self.base.size[0] - w - 16))
        self.d.rounded_rectangle([x - 6, y - 3, x + w + 6, y + 21], 5, fill=PANEL)
        self.d.text((x, y), text, font=FONTB, fill=col)

    def label(self, xy, lines, col=WHITE, anchor_pt=None):
        """A panel of text (first line bold, in col) at picture pixel xy; a leader to anchor_pt."""
        x, y = xy
        widths = [self.d.textlength(t, font=FONTB if i == 0 else FONT) for i, t in enumerate(lines)]
        w, h = max(widths), 22 * len(lines)
        W, H = self.base.size
        x = max(8, min(x, W - w - 24))
        y = max(8, min(y, H - h - 16 - 34))
        if anchor_pt:
            cx = min(max(anchor_pt[0], x), x + w + 16)
            cy = min(max(anchor_pt[1], y), y + h + 8)
            self.d.line([anchor_pt, (cx, cy)], fill=col, width=2)
        self.d.rounded_rectangle([x, y, x + w + 16, y + h + 8], 7, fill=PANEL, outline=col, width=2)
        for i, t in enumerate(lines):
            self.d.text((x + 8, y + 5 + i * 22), t, font=FONTB if i == 0 else FONT, fill=col if i == 0 else WHITE)

    def save(self, path, step, title):
        W, H = self.base.size
        t = f"{step}  {title}"
        w = self.d.textlength(t, font=FONTT)
        self.d.rounded_rectangle([8, H - 44, 8 + w + 20, H - 8], 8, fill=(0, 0, 0, 200))
        self.d.text((18, H - 40), t, font=FONTT, fill=WHITE)
        ft = f"frame {self.frame}" if isinstance(self.frame, int) else self.frame
        if ft:
            fw = self.d.textlength(ft, font=FONTS)
            self.d.rounded_rectangle([W - fw - 22, H - 32, W - 8, H - 8], 6, fill=(0, 0, 0, 170))
            self.d.text((W - fw - 15, H - 29), ft, font=FONTS, fill=(200, 200, 200))
        Image.alpha_composite(self.base, self.over).convert("RGB").save(path, optimize=True)

