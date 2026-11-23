#!/bin/bash
# Record CPU v CPU matches under gdb with trace4.gdb's logging, several at a time.
#
#   run_batch.sh OUTDIR FIRST COUNT WORKERS [ASSETS]
#   MODE=training run_batch.sh ...     the training drills instead (SWOS_PRACTICE_TRAINING_TEST:
#                                      17 restarts -- free kicks before goal, corners -- CPU v CPU)
#   PRE=human_fire.gdb run_batch.sh ...  a gdb file loaded before trace4.gdb (the one-on-one roll)
#
# Match i plays two English clubs picked from i, from minute 40 at 2-1 (SWOS_MOD_MATCH_TEST),
# records OUTDIR/m<i>.SRP and logs OUTDIR/m<i>.log. Run from the repository root, after
# `make X86_64=1`. Each worker has a home of its own, so nothing touches ~/.swos.
set -u
OUT=$1; FIRST=$2; COUNT=$3; WORKERS=$4
ASSETS=${5:-${SWOS_ASSETS:-$HOME/.swos/assets}}
TOOLS=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"

one() {
    local i=$1
    local a b
    a=$(printf '08%02x' $(( (i * 3) % 20 )))
    b=$(printf '08%02x' $(( (i * 7 + 11) % 20 )))
    [ "$a" = "$b" ] && b=$(printf '08%02x' $(( (i * 7 + 12) % 20 )))
    local home="$OUT/home$i"
    mkdir -p "$home"
    local test="SWOS_MOD_MATCH_TEST=1 SWOS_MOD_MATCH_TEAMS=$a,$b"
    [ "${MODE:-}" = training ] && test="SWOS_PRACTICE_TRAINING_TEST=1"
    env HOME="$home" SWOS_ASSETS="$ASSETS" SDL_VIDEODRIVER=offscreen SWOS_AUDIO_OFF=1 SWOS_SKIP_INTRO=1 \
    SWOS_NO_ASSETS_CHECK=1 SWOS_HARNESS_TURBO=1 SWOS_WORLD=9697 $test timeout 600 gdb -batch ${PRE:+-x "$TOOLS/$PRE"} -x "$TOOLS/trace4.gdb" \
        --args bin/SWOS.x86_64 --renderer=software --record-replay="$OUT/m$i.SRP" > "$OUT/m$i.log" 2>&1
    echo "m$i $a-$b $(grep -c '^GOAL' "$OUT/m$i.log") goals"
}
export -f one
export OUT ASSETS TOOLS MODE PRE
seq "$FIRST" $((FIRST + COUNT - 1)) | xargs -P "$WORKERS" -I{} bash -c 'one {}'
