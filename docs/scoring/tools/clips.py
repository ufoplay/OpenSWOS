"""The goal clips: each move as the game's camera showed it, from the player on the ball to
the goal. Real speed until the shot, half speed from it, a name over the player who matters.

    python3 clips.py NAME REC.SRP CAPTURE_DIR OUT.webp     (NAME: s1 .. s9)
    python3 clips.py s10 REPLAY.RPL CAPTURE_DIR OUT.webp     (and s11: capture_rpl.py's CAPTURE_DIR)
    python3 clips.py --possession REC.SRP FRAME X Y        (when did he get the ball?)

CAPTURE_DIR holds capture.py's screenshots of the range (start .. end) and its trace.txt.
The clip is an animated WebP, lossless: the game's own colours, and a sixth of a GIF's size.
A player is followed through the recording from an anchor (a frame and his world position
there, from the engine log): his sprite at the anchor, then the nearest sprite of the same
team frame by frame, back and forward. --possession walks back from a kick until the ball
was more than 14 units from the kicker for 5 frames running: that is when he got it.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpl          # noqa: E402
import srp          # noqa: E402
import trace_read   # noqa: E402

SHADOW = 1069
FOOT = (1, 12)      # a player's world position, less his sprite's top-left
_FONTDIR = "/usr/share/fonts/truetype/dejavu/"
FONT = ImageFont.truetype(_FONTDIR + "DejaVuSans-Bold.ttf", 15)
YELLOW = (255, 213, 79)

# start: the first frame shown; slow: half speed from here (just before the shot); end: the
# last frame (a little after the goal), held for a second. marks: (name, anchor frame, world
# x, y there, shown from, shown to).
CLIPS = {
    # Hughes has the ball from 3152 and shoots at 3205
    "s1": dict(start=3131, slow=3201, end=3256, marks=[("HUGHES", 3205, 404, 252, 3131, 3205)]),
    # Mathie has it for only 8 frames (723-731): Thomsen's pass to him is in, from 695
    "s2": dict(start=685, slow=727, end=748, marks=[("MATHIE", 731, 310, 177, 685, 731)]),
    # Petrescu's corner (6284) reaches Hughes at 6338; he shoots at 6354
    "s3": dict(start=6270, slow=6350, end=6379, marks=[("HUGHES", 6354, 297, 708, 6270, 6354)]),
    # Vialli has it from 3379, shoots at 3404, heads the parry in at 3416
    "s4": dict(start=3355, slow=3400, end=3435, marks=[("VIALLI", 3404, 414, 717, 3355, 3416)]),
    # Bergkamp walks up from 1484, stands over the ball from 1528, shoots at 1613
    "s5": dict(start=1480, slow=1609, end=1630, marks=[("BERGKAMP", 1613, 337, 188, 1480, 1613)]),
    # Lomas reaches the ball at 2180 and shoots at 2216
    "s6": dict(start=2165, slow=2212, end=2252, marks=[("LOMAS", 2216, 384, 663, 2165, 2216)]),
    # Sharpe gets the ball on the right wing at 5271 and kicks at 5282
    "s7": dict(start=5235, slow=5278, end=5385, marks=[("SHARPE", 5282, 537, 472, 5235, 5282)]),
    # Gabbiadini has it from 3341 and shoots at 3420; Sturridge scores the parry at 3456
    "s8": dict(start=3325, slow=3416, end=3465, marks=[("GABBIADINI", 3420, 400, 644, 3325, 3420),
                                                      ("STURRIDGE", 3456, 321, 752, 3428, 3456)]),
    # Gabbiadini has it from 6972 and shoots at 6994; it goes in off Roberts at 7044
    "s9": dict(start=6950, slow=6990, end=7050, marks=[("GABBIADINI", 6994, 429, 646, 6950, 6994),
                                                      ("ROBERTS", 7044, 315, 768, 7015, 7044)]),
    # SWOS 2020, team training (replays/central then bend): on the ball from 3226, he runs away
    # from goal, turns at 3366, comes back up the middle and shoots at 3424; in at 3454
    "s10": dict(start=3216, slow=3420, end=3466, marks=[("SHOOTER", 3424, 340, 236, 3216, 3424)]),
    # SWOS 2020, team training (replays/long from side): the kick-off pass reaches him at 547,
    # he runs out to the right wing, turns at 640, comes back in on the diagonal and shoots
    # at 686; in at 743
    "s11": dict(start=540, slow=682, end=765, marks=[("SHOOTER", 686, 414, 296, 540, 686)]),
}


def team_of(img):
    return 1 if 227 <= img < 530 else 2 if 530 <= img < 833 else 0


def shadow(fr):
    s = [(x, y + 2) for img, x, y in fr["sprites"] if img == SHADOW]
    return s[0] if s else None


def track(frs, af, x, y, f0, f1):
    """frame -> the sprite top-left (world) of the outfield player at (x, y) in frame af."""
    sp = [s for s in frs[af]["sprites"] if team_of(s[0])]
    c = min(sp, key=lambda s: abs(s[1] - (x - FOOT[0])) + abs(s[2] - (y - FOOT[1])))
    t = team_of(c[0])
    out = {af: (c[1], c[2])}
    for rng in (range(af - 1, f0 - 1, -1), range(af + 1, f1 + 1)):
        cur = (c[1], c[2])
        for f in rng:
            s = min((s for s in frs[f]["sprites"] if team_of(s[0]) == t),
                    key=lambda s: (s[1] - cur[0]) ** 2 + (s[2] - cur[1]) ** 2)
            cur = (s[1], s[2])
            out[f] = cur
    return out


def possession(frs, af, x, y, lim=14, gap=4):
    tr = track(frs, af, x, y, max(0, af - 600), af)
    start, miss = af, 0
    for f in range(af, max(0, af - 600), -1):
        b = shadow(frs[f])
        if not b:
            continue
        px, py = tr[f][0] + FOOT[0], tr[f][1] + FOOT[1]
        if ((b[0] - px) ** 2 + (b[1] - py) ** 2) ** 0.5 <= lim:
            start, miss = f, 0
        else:
            miss += 1
            if miss > gap:
                break
    return start


def screen_offsets(frs, trace, f0, f1):
    """frame -> (dx, dy): screen = recorded world + offset. From the ball's shadow where it is
    drawn, else from the camera (offset + camera is constant)."""
    out, k = {}, None
    for f in range(f0, f1 + 1):
        w = shadow(frs[f])
        s = [(x, y) for img, x, y in trace.get(f, {"sprites": []})["sprites"] if img == SHADOW]
        if w and s:
            dx, dy = s[0][0] - w[0], s[0][1] - (w[1] - 2)
            out[f] = (dx, dy)
            k = (dx + frs[f]["camx"], dy + frs[f]["camy"])
    for f in range(f0, f1 + 1):
        if f not in out and k:
            out[f] = (round(k[0] - frs[f]["camx"]), round(k[1] - frs[f]["camy"]))
    return out


def make(name, rec, cap, path, scale=2, hold=25):
    c = CLIPS[name]
    if rec.upper().endswith(".RPL"):        # a PC / SWOS 2020 replay: capture_rpl.py's screen.txt
        frs, fps, trace = rpl.frames(rec), 60, {}
        for line in open(os.path.join(cap, "screen.txt")):
            f, ox, oy = map(int, line.split())
            trace[f] = {"sprites": [(i, x + ox, y + oy) for i, x, y in frs[f]["screen"]]}
    else:
        frs, fps = srp.frames(srp.load(rec)), 50
        trace = trace_read.read(os.path.join(cap, "trace.txt"))
    tick = round(2000 / fps)                # ms a picture: every other frame, or every frame at half speed
    offs = screen_offsets(frs, trace, c["start"], c["end"])
    marks = [(n, track(frs, af, x, y, a, b), a, b) for n, af, x, y, a, b in c["marks"]]
    frames, durations = [], []
    f = c["start"]
    while f <= c["end"]:
        p = os.path.join(cap, f"f{f}.png")
        slow = f >= c["slow"]
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            d = ImageDraw.Draw(im)
            dx, dy = offs.get(f, (0, 0))
            for n, tr, a, b in marks:
                if a <= f <= b and f in tr:
                    x = (tr[f][0] + dx + 6) * scale
                    y = (tr[f][1] + dy - 3) * scale
                    d.polygon([(x - 7, y - 10), (x + 7, y - 10), (x, y)], fill=YELLOW, outline=(0, 0, 0))
                    w = d.textlength(n, font=FONT)
                    tx, ty = max(4, min(x - w / 2, im.width - w - 4)), y - 32
                    if ty < 4:              # no room above him: under his feet
                        ty = y + 22 * scale
                    d.rounded_rectangle([tx - 5, ty - 2, tx + w + 5, ty + 19], 5, fill=(0, 0, 0))
                    d.text((tx, ty), n, font=FONT, fill=YELLOW)
            badge = "1/2 speed" if slow else "real speed"
            w = d.textlength(badge, font=FONT)
            d.rounded_rectangle([im.width - w - 22, im.height - 30, im.width - 8, im.height - 8], 5, fill=(0, 0, 0))
            d.text((im.width - w - 15, im.height - 28), badge, font=FONT, fill=(255, 255, 255) if not slow else YELLOW)
            frames.append(im)
            durations.append(tick)
        f += 1 if slow else 2
    durations[-1] = tick * hold
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durations, loop=0, lossless=True,
                   method=6)
    print(f"{path}: frames {c['start']}-{c['end']}, {len(frames)} pictures")


if __name__ == "__main__":
    if sys.argv[1] == "--possession":
        rec, af, x, y = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
        print("on the ball from frame", possession(srp.frames(srp.load(rec)), af, x, y))
    else:
        make(*sys.argv[1:5])
