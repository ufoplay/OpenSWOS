import sys, glob
from PIL import Image, ImageDraw
src, out, start, step, count = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
fs = sorted(glob.glob(src + '/*.png'))
sel = list(range(start, min(len(fs), start + step * count), step))
W, H = 362, 272; cols = 6; s = 0.5
rows = (len(sel) + cols - 1) // cols
sheet = Image.new('RGB', (int(W * s) * cols, int(H * s) * rows))
d = ImageDraw.Draw(sheet)
for k, i in enumerate(sel):
    im = Image.open(fs[i]).convert('RGB').resize((int(W * s), int(H * s)))
    x = (k % cols) * int(W * s); y = (k // cols) * int(H * s)
    sheet.paste(im, (x, y)); d.rectangle((x, y, x + 30, y + 12), fill=(0, 0, 0)); d.text((x + 3, y + 1), str(i), fill=(255, 255, 0))
sheet.save(out)
