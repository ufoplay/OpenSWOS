#!/bin/bash
# The shot lab (shotlab.py) over many workers.
#
#   shotlab.sh TRIALS.json OUTDIR WORKERS [ASSETS]
#   LAB_KEEPER=6 shotlab.sh ...           (and LAB_SHOOTING, LAB_FINISHING, LAB_SETTLE)
#
# Splits the trials into WORKERS lists, plays each in a game of its own under gdb (its own
# home, so nothing touches ~/.swos), and writes OUTDIR/r<pid>-<i>.jsonl, then OUTDIR/all.jsonl.
# Resumable: the trials already in OUTDIR's results are not played again (run it again with
# the same OUTDIR after a stop). Run from the repository root, after `make X86_64=1`.
#
# Memory: SDL's "dummy" video driver, never "offscreen" -- offscreen loads EGL and with it the
# GPU driver, whose mappings grew to ~4.8 GB a game in a long run. With dummy a game stays
# near 30 MB and gdb near 200 MB. Run it capped, as a user service that can be stopped whole:
#   systemd-run --user --unit=swos-lab --collect -p MemoryMax=12G -p MemorySwapMax=0 \
#       --working-directory=$PWD docs/scoring/tools/shotlab.sh ...
#   systemctl --user stop swos-lab
set -u
TRIALS=$1; OUT=$2; WORKERS=$3
ASSETS=${4:-${SWOS_ASSETS:-$HOME/.swos/assets}}
TOOLS=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
python3 - "$TRIALS" "$OUT" "$WORKERS" <<'EOF'
import glob, json, sys
done = set()
for p in glob.glob(f"{sys.argv[2]}/[wr]*.jsonl"):
    for line in open(p):
        try:
            done.add(json.loads(line)["id"])
        except ValueError:
            pass
t = [x for x in json.load(open(sys.argv[1])) if x["id"] not in done]
n = int(sys.argv[3])
print(f"{len(done)} trials done already, {len(t)} to play")
for i in range(n):
    json.dump(t[i::n], open(f"{sys.argv[2]}/t{i}.json", "w"))
EOF
one() {
    local i=$1
    mkdir -p "$OUT/home$i"
    [ "$(python3 -c "import json; print(len(json.load(open('$OUT/t$i.json'))))")" = 0 ] && return
    env HOME="$OUT/home$i" SWOS_ASSETS="$ASSETS" SDL_VIDEODRIVER=dummy SWOS_AUDIO_OFF=1 SWOS_SKIP_INTRO=1 \
        SWOS_NO_ASSETS_CHECK=1 SWOS_HARNESS_TURBO=1 SWOS_WORLD=9697 SWOS_SHOOTING_TEST=1 \
        LAB_TRIALS="$OUT/t$i.json" LAB_OUT="$OUT/r$$-$i.jsonl" timeout 7200 \
        gdb -batch -x "$TOOLS/shotlab.py" --args bin/SWOS.x86_64 --renderer=software > "$OUT/w$i.log" 2>&1
    echo "worker $i: $(wc -l < "$OUT/r$$-$i.jsonl") shots"
}
export -f one
export OUT ASSETS TOOLS
seq 0 $((WORKERS - 1)) | xargs -P "$WORKERS" -I{} bash -c 'one {}'
cat "$OUT"/[wr]*.jsonl > "$OUT/all.jsonl"
echo "$(wc -l < "$OUT/all.jsonl") shots in $OUT/all.jsonl"
