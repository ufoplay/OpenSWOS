"""A PC / SWOS 2020 whole-match replay (.RPL) read the way srp.py reads a .SRP.

The file is the PC game's .HIL layout with one scene (src/dos_replay_load.c): a 3626-byte
little-endian header (teams at 8 and 1712, 1704 bytes each; scenes, goals, pitch at 0xE20),
then the frames. A frame is a camera dword (bit 31 set, Y<<16 | X), a goals dword
(t2<<16 | t1), an animation dword, then one dword per sprite, [index:11][x:10][y:10] signed,
the index 114 above ours and the position on screen, i.e. less the camera. 0xFFFFFFFF ends
the scene. There is no engine state: positions only.

frames() gives what srp.frames() gives -- per frame the camera, the score and the sprites as
(our image index, world x, y of the sprite's top-left) -- so the tools work on either.
"""
import struct

HDR = 0x0E2A
DOS_SPRITE_BASE = 114


def header(path):
    b = open(path, "rb").read(HDR)
    name = lambda off: b[off + 22:off + 22 + 17].split(b"\0")[0].decode("latin1")  # noqa: E731
    scenes, g1, g2, pitch, subs = struct.unpack_from("<HHHHH", b, 0xE20)
    return {"style": b[5], "team1": name(8), "team2": name(1712),
            "competition": b[0xD58:0xD58 + 40].split(b"\0")[0].decode("latin1"),
            "scenes": scenes, "goals": (g1, g2), "pitch": pitch}


def _signed10(v):
    return v - 1024 if v & 512 else v


def frames(path):
    b = open(path, "rb").read()
    out, cur, after = [], None, 0
    for (d,) in struct.iter_unpack("<I", b[HDR:HDR + (len(b) - HDR) // 4 * 4]):
        if d == 0xFFFFFFFF:
            after = 0
        elif after == 1:
            cur["g1"], cur["g2"] = d & 0xFFFF, d >> 16
            after = 2
        elif after == 2:
            after = 0
        elif d & 0x80000000:
            v = d & 0x7FFFFFFF
            cur = {"camx": v & 0xFFFF, "camy": v >> 16, "g1": 0, "g2": 0, "sprites": [], "screen": []}
            out.append(cur)
            after = 1
        else:
            idx, x, y = (d >> 20) - DOS_SPRITE_BASE, _signed10((d >> 10) & 1023), _signed10(d & 1023)
            cur["screen"].append((idx, x, y))
            cur["sprites"].append((idx, x + cur["camx"], y + cur["camy"]))
    return out


def ball(frame):
    """The ball's world (x, y, z) from its sprite and its shadow's. The shadow is drawn at
    (x + z/2 + 1, y + z/4 + 1) less its centre, 3 and 7 (src/ball_physics.c), and the ball
    z higher than the ball's own point: so the gap between the two is about z * 5/4 + 1."""
    sh = [(x, y) for i, x, y in frame["sprites"] if i == 1069]
    bl = [(x, y) for i, x, y in frame["sprites"] if 1065 <= i <= 1068]
    if not sh or not bl:
        return None
    z = max(0, round((sh[0][1] - bl[0][1] - 1) * 0.8))
    return sh[0][0] + 2 - z // 2, sh[0][1] + 6 - z // 4, z
