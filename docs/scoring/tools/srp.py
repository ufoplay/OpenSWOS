"""Minimal .SRP reader (docs/REPLAY_FORMAT_V2.md): header, chunk directory, FRMS, CHAP."""
import struct
import zlib


def load(path):
    d = open(path, "rb").read()
    assert d[:4] == b"SWRP", "not an SRP"
    ver, flags, tick, quirks, pw, ph, nframes, nchunks = struct.unpack_from(">HHHHHHIH", d, 4)
    chunks = {}
    off = 32
    for _ in range(nchunks):
        fourcc, coff, stored, raw = struct.unpack_from(">4sIII", d, off)
        off += 16
        blob = d[coff:coff + stored]
        if stored != raw:
            blob = zlib.decompress(blob, -15)
        chunks[fourcc.decode()] = blob
    return {"tick": tick, "frames_n": nframes, "chunks": chunks}


def frames(srp):
    b = srp["chunks"]["FRMS"]
    out = []
    p = 0
    while p + 20 <= len(b):
        n, camx, camy, g1, g2, anim, minute, adline = struct.unpack_from(">HiiHHHHH", b, p)
        p += 20
        spr = []
        for _ in range(n):
            img, x, y = struct.unpack_from(">Hhh", b, p)
            p += 6
            spr.append((img, x, y))
        out.append({"camx": camx / 65536.0, "camy": camy / 65536.0, "g1": g1, "g2": g2,
                    "minute": minute, "sprites": spr})
    return out


def chapters(srp):
    b = srp["chunks"].get("CHAP", b"")
    if not b:
        return []
    (n,) = struct.unpack_from(">H", b, 0)
    out = []
    p = 2
    for _ in range(n):
        frame, kind, team, value = struct.unpack_from(">IHHH", b, p)
        p += 10
        out.append({"frame": frame, "kind": kind, "team": team, "value": value})
    return out
