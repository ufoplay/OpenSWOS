"""Render frames of a recording with the game's own replay viewer, and line them up.

    python3 capture.py REC.SRP FIRST COUNT OUTDIR [ASSETS]

Plays REC.SRP headless (--view-replay) with SWOS_REPLAY_TRACE on (which also hides the
viewer's overlay), screenshots COUNT presents from about FIRST, moves them to OUTDIR as
f<frame>.png, and writes OUTDIR/trace.txt. A screenshot's frame is found by putting the
traced ball sprite on the picture: the lag between presents and recording frames that puts
the most white ball pixels where the trace says the ball is drawn.
Run from the repository root (the binary writes its screenshots into bin/).
"""
import glob
import os
import shutil
import subprocess
import sys
import time

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trace_read  # noqa: E402

rec, first, count, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
assets = sys.argv[5] if len(sys.argv) > 5 else os.environ.get("SWOS_ASSETS", os.path.expanduser("~/.swos/assets"))
os.makedirs(out, exist_ok=True)
home = os.path.join(out, "home")
os.makedirs(home, exist_ok=True)
for f in glob.glob("bin/swos_shot*.png"):
    os.remove(f)
GUESS = 54
margin = 30
env = dict(os.environ, HOME=home, SWOS_ASSETS=assets, SDL_VIDEODRIVER="offscreen", SWOS_AUDIO_OFF="1",
           SWOS_SKIP_INTRO="1", SWOS_NO_ASSETS_CHECK="1", SWOS_REPLAY_TRACE=os.path.join(out, "trace.txt"),
           SWOS_REPLAY_TRACE_SPRITES="1", SWOS_SCREENSHOT_INTERVAL="1",
           SWOS_SCREENSHOT_FROM=str(first + GUESS - margin), SWOS_SCREENSHOT_MAX=str(count + 2 * margin))
# The viewer goes on playing after its last screenshot: stop it once they are all written.
game = subprocess.Popen(["bin/SWOS.x86_64", "--renderer=software", "--view-replay=" + rec, "--replay-window"],
                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(600):
    if game.poll() is not None or len(glob.glob("bin/swos_shot*.png")) >= count + 2 * margin:
        break
    time.sleep(1)
time.sleep(1)
game.terminate()
game.wait()
shots = sorted(glob.glob("bin/swos_shot*.png"))
tr = trace_read.read(os.path.join(out, "trace.txt"))
ims = [Image.open(p).convert("RGB") for p in shots]


def ballpos(f):
    for img, x, y in tr.get(f, {"sprites": []})["sprites"]:
        if 1065 <= img <= 1068:
            return x, y
    return None


best = None
for lag in range(GUESS - 20, GUESS + 21):
    score = 0
    for k in range(0, len(ims), 2):
        f = first - margin + k + GUESS - lag
        p = ballpos(f)
        if not p:
            continue
        x, y = p
        for dx in range(6):
            for dy in range(6):
                if 0 <= x + dx < ims[k].width and 0 <= y + dy < ims[k].height:
                    r, g, b = ims[k].getpixel((x + dx, y + dy))
                    score += r > 200 and g > 200 and b > 200
    if best is None or score > best[0]:
        best = (score, lag)
lag = best[1]
for k, p in enumerate(shots):
    f = first - margin + k + GUESS - lag
    shutil.move(p, os.path.join(out, f"f{f}.png"))
print(f"lag {lag} (score {best[0]}): frames {first - margin + GUESS - lag} .. {first - margin + len(shots) - 1 + GUESS - lag} in {out}")
