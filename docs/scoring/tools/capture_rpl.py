"""capture.py for a PC / SWOS 2020 replay (.RPL): render its frames with the game's viewer.

    python3 capture_rpl.py REPLAY.RPL FIRST COUNT OUTDIR [ASSETS] [SHIFT]

SHIFT, when the search below cannot find it (a move that is mostly mid-pitch, where no line
fixes the camera): which screenshot is which frame, read off the scoreboard -- the first
screenshot showing the goal, less the frame the replay counts it (its goals dword).

--view-replay does not take an .RPL, but an .RPL is a PC .HIL of one scene, which it does
take (as a name in the save folder): the file is copied into OUTDIR/home/.swos/save as
REPLAY.HIL and played headless with a screenshot of every present, the whole replay (one
frame a present, as fast as it goes: seconds).

The viewer writes no trace for a .HIL, and it does not draw with the replay's camera: it
moves a camera of its own after the ball (src/highlight.c, ReplayCameraX), and its vertical
camera lags the recorded one. So the viewer is run a second time under gdb, logging the
camera it set for each frame; the pictures fix the rest. Which screenshot is which frame is a
constant shift (the presents before the replay starts): a first guess from where the
sprites fall on non-grass pixels, then the one that puts the ball's white pixels where the
replay says the ball is, through cameras measured from the pitch's lines (goal lines, boxes,
halfway line: long, white, at known world places). Those line fits also give the one constant
between the logged camera and the picture.
Writes OUTDIR/f<frame>.png for FIRST .. FIRST+COUNT-1 and OUTDIR/screen.txt, one line per
frame, "frame ox oy": window pixel = the replay's screen position + (ox, oy).
Run from the repository root (the binary writes its screenshots into bin/).
"""
import collections
import glob
import os
import re
import shutil
import subprocess
import time
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rpl  # noqa: E402

src, first, count, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
assets = sys.argv[5] if len(sys.argv) > 5 else os.environ.get("SWOS_ASSETS", os.path.expanduser("~/.swos/assets"))
save = os.path.join(out, "home", ".swos", "save")
os.makedirs(save, exist_ok=True)
shutil.copyfile(src, os.path.join(save, "REPLAY.HIL"))
fr = rpl.frames(src)
for f in glob.glob("bin/swos_shot*.png"):
    os.remove(f)
env = dict(os.environ, HOME=os.path.join(out, "home"), SWOS_ASSETS=assets, SDL_VIDEODRIVER="offscreen",
           SWOS_AUDIO_OFF="1", SWOS_SKIP_INTRO="1", SWOS_NO_ASSETS_CHECK="1", SWOS_SCREENSHOT_INTERVAL="1",
           SWOS_SCREENSHOT_FROM="1", SWOS_SCREENSHOT_MAX=str(len(fr) + 200))
game = subprocess.Popen(["bin/SWOS.x86_64", "--renderer=software", "--view-replay=REPLAY.HIL"],
                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
last, still = -1, 0                 # (the viewer does not quit after the last frame: stop it once
for _ in range(600):                # the screenshots stop coming)
    if game.poll() is not None:
        break
    n = len(glob.glob("bin/swos_shot*.png"))
    still = still + 1 if n == last and n > 0 else 0
    if still >= 3 or n >= len(fr) + 200:
        break
    last = n
    time.sleep(1)
game.terminate()
game.wait()
shots = {int(re.findall(r"(\d+)\.png$", p)[0]): p for p in glob.glob("bin/swos_shot*.png")}
_pics = {}


def pic(k):
    """(not grass, white) of screenshot k. The pitch is two shades, (51,119,0) and (119,119,0)."""
    if k not in _pics:
        a = np.asarray(Image.open(shots[k]).convert("RGB")).astype(int)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        _pics[k] = (~((b < 40) & (g >= 100) & (g >= r) & (r <= 130)), (r > 200) & (g > 200) & (b > 200))
    return _pics[k]


def sprite_score(m, P, pcxs, pcy):
    """Per candidate pcx: sprites on non-grass, less 0.6 for each on grass (off-screen: 0)."""
    H, W = m.shape
    X = P[:, 0][:, None] - pcxs[None, :]
    Y = np.broadcast_to((P[:, 1] - pcy)[:, None], X.shape)
    ok = (X >= 0) & (X < W) & (Y >= 0) & (Y < H)
    hit = np.where(ok, m[np.clip(Y, 0, H - 1), np.clip(X, 0, W - 1)], False).sum(0)
    return hit - 0.6 * (ok.sum(0) - hit)


def body_points(f):
    return np.array([(x + 6, y + 8) for i, x, y in fr[f]["sprites"] if 227 <= i < 1065])


# ---- the camera from the sprites: picture pixel = world - (pcx, pcy) ---------------------
def sprite_cam(k, f, pcys=None):
    m, _ = pic(k)
    P = body_points(f)
    pcxs = np.arange(fr[f]["camx"] - 60, fr[f]["camx"] + 240)
    best = None
    for pcy in pcys if pcys is not None else range(fr[f]["camy"] - 14, fr[f]["camy"] + 15):
        v = sprite_score(m, P, pcxs, pcy)
        j = int(v.argmax())
        if best is None or v[j] > best[0]:
            best = (float(v[j]), int(pcxs[j]), pcy)
    return best[1], best[2]


# ---- the camera from the pitch's lines -------------------------------------------------------
# world lines (the Amiga pitch: goal lines 129 and 769, boxes 190..475 by 87, six-yard boxes
# 270..395 by 24, halfway 449): (y, x0, x1) across, (x, y0, y1) down
ACROSS = [(129, 0, 700), (216, 190, 475), (449, 0, 700), (682, 190, 475), (769, 0, 700)]
DOWN = [(190, 129, 216), (475, 129, 216), (270, 129, 153), (395, 129, 153),
        (190, 682, 769), (475, 682, 769), (270, 745, 769), (395, 745, 769)]


def line_cam(k, camx, camy):
    """(pcx or None, pcy or None): each only when the lines that fix it are in the picture."""
    _, wh = pic(k)
    H, W = wh.shape
    rowc = np.concatenate([np.zeros((H, 1), int), np.cumsum(wh, 1)], 1)
    colc = np.concatenate([np.zeros((1, W), int), np.cumsum(wh, 0)], 0)
    pcxs = np.arange(camx - 60, camx + 240)
    best = None
    for pcy in range(camy - 14, camy + 15):
        sa = np.zeros(len(pcxs))
        sd = np.zeros(len(pcxs))
        for y, x0, x1 in ACROSS:
            r = y - pcy
            if 0 <= r < H:
                c0, c1 = np.clip(x0 - pcxs, 0, W), np.clip(x1 - pcxs + 1, 0, W)
                sa += np.where(c1 > c0, rowc[r, c1] - rowc[r, c0], 0)
        for x, y0, y1 in DOWN:
            c = x - pcxs
            r0, r1 = max(0, min(H, y0 - pcy)), max(0, min(H, y1 - pcy + 1))
            ok = (c >= 0) & (c < W) & (r1 > r0)
            cc = np.clip(c, 0, W - 1)
            sd += np.where(ok, colc[r1, cc] - colc[r0, cc], 0)
        v = sa + 2 * sd
        j = int(v.argmax())
        if best is None or v[j] > best[0]:
            best = (float(v[j]), int(pcxs[j]), pcy, float(sa[j]), float(sd[j]))
    _, pcx, pcy, sa, sd = best
    return (pcx if sd >= 30 else None), (pcy if sa >= 120 else None)


LINED = {}                          # picture -> (x from the lines, y from the lines)


def camera(k, f):
    lx, ly = line_cam(k, fr[f]["camx"], fr[f]["camy"])
    LINED[k] = (lx is not None, ly is not None)
    if lx is not None and ly is not None:
        return lx, ly
    sx, sy = sprite_cam(k, f, [ly] if ly is not None else None)
    return (lx if lx is not None else sx), (ly if ly is not None else sy)


# 1. a first guess at the shift: the one whose sprite fits score best across the replay
total = collections.Counter()
for k in [k for k in range(40, len(fr), max(1, len(fr) // 40)) if k in shots]:
    m, _ = pic(k)
    for s in range(0, 31):
        f = k - s
        if 0 <= f < len(fr):
            P = body_points(f)
            pcxs = np.arange(fr[f]["camx"] - 60, fr[f]["camx"] + 240)
            total[s] += max(float(sprite_score(m, P, pcxs, pcy).max())
                            for pcy in range(fr[f]["camy"] - 14, fr[f]["camy"] + 15))
shift0 = total.most_common(1)[0][0]
if len(sys.argv) > 6:
    shift0 = int(sys.argv[6])

# 2. each picture's camera, then the shift that puts the ball where its pixels are: searched
# well past the first guess (a replay that starts with everyone standing still at a kick-off
# fits every shift about as well, and the guess comes out 0; "long from side" is 13)
WIDE = 30
cams = {}
for k in range(first + shift0 - 3, first + count + shift0 + WIDE + 3):
    if k in shots and 0 <= k - shift0 < len(fr):
        cams[k] = camera(k, k - shift0)


def ball_score(s):
    v = 0
    for f in range(first, first + count):
        k = f + s
        if k not in cams or f >= len(fr):
            continue
        _, wh = pic(k)
        H, W = wh.shape
        for i, x, y in fr[f]["sprites"]:
            if 1065 <= i <= 1068:
                c, r = x - cams[k][0], y - cams[k][1]
                if 0 <= c < W - 3 and 0 <= r < H - 3:
                    v += int(wh[r:r + 3, c:c + 3].sum())
    return v


scores = {s: ball_score(s) for s in range(shift0 - 2, shift0 + WIDE + 1)}
shift = max(scores, key=scores.get) if len(sys.argv) <= 6 else shift0

# 3. the camera the viewer drew each frame with, from the viewer itself: run once more under
# gdb, logging Render_CameraX/Y as each frame's camera is set (highlight.c, after MoveView).
# The pictures' own fits only pin the camera where a pitch line shows -- mid-pitch they can
# be 80 units out. Sprites are drawn at their world place less that camera, so no constant
# is added; the ball's white pixels check it (they peak there, within a unit). The pitch
# lines' world places here (ACROSS, DOWN) are a few units out in x: good enough to find the
# shift, not to place a camera -- what this script did until situation 11 showed it.
gdbf = os.path.join(out, "camera.gdb")
open(gdbf, "w").write("set pagination off\nset confirm off\nset breakpoint pending on\nset $i = 0\n"
                      "break highlight.c:849\ncommands\nsilent\n"
                      'printf "CAM %d %d %d\\n", $i, (int)Render_CameraX(), (int)Render_CameraY()\n'
                      "set $i = $i + 1\ncontinue\nend\nrun\nquit\n")
log = subprocess.run(["gdb", "-batch", "-x", gdbf, "--args", "bin/SWOS.x86_64", "--renderer=software",
                      "--view-replay=REPLAY.HIL"], env=dict(env, SDL_VIDEODRIVER="dummy"),
                     capture_output=True, text=True, timeout=600).stdout
R = {int(a): (int(b), int(c)) for _, a, b, c in (ln.split() for ln in log.splitlines() if ln.startswith("CAM "))}


def ball_fit(cx, cy):
    """White pixels under the ball, all frames, with the logged camera and (cx, cy) more."""
    v = 0
    for f in range(first, first + count):
        k = f + shift
        if k not in shots or f not in R:
            continue
        _, wh = pic(k)
        for i, x, y in fr[f]["sprites"]:
            if 1065 <= i <= 1068:
                c, r = x - R[f][0] + cx, y - R[f][1] + cy
                if 0 <= c < wh.shape[1] - 4 and 0 <= r < wh.shape[0] - 4:
                    v += int(wh[r:r + 4, c:c + 4].sum())
    return v


fits = {(a, b): ball_fit(a, b) for a in range(-8, 9) for b in range(-8, 9)}
best_fit = max(fits, key=fits.get)
cx, cy = 0, 0       # (the viewer draws a sprite at its world place less Render_Camera: the fit checks it)
lines = []
for f in range(first, first + count):
    k = f + shift
    if k not in shots or f not in R:
        continue
    shutil.copyfile(shots[k], os.path.join(out, f"f{f}.png"))
    lines.append(f"{f} {fr[f]['camx'] - R[f][0] + cx} {fr[f]['camy'] - R[f][1] + cy}\n")
for p in shots.values():
    os.remove(p)
open(os.path.join(out, "screen.txt"), "w").writelines(lines)
print(f"the viewer's camera, logged: {len(R)} frames; the ball's pixels: {fits[0, 0]} at (0, 0), "
      f"best {fits[best_fit]} at {best_fit}")
best = sorted(scores, key=scores.get, reverse=True)[:4]
print(f"screenshot = frame + {shift} (ball pixels, best shifts: {[(s, scores[s]) for s in best]}): frames {first} .. {first + count - 1} in {out}")
