import sys, glob
sys.path.insert(0, sys.path[0] or '.')
import srp, goals
for p in sys.argv[1:]:
    s = srp.load(p); fr = srp.frames(s)
    for g, team in goals.goals(fr):
        r = goals.analyse(fr, g, team)
        name = p.split('/')[-1]
        if r.get('kick') is None:
            print(name, g, 'no kick found'); continue
        bx, by = r['kick_ball']; line = r['line']
        dist = abs(by + 2 - line)
        zone = 'FIN' if (241 <= bx <= 431 and dist < 75) else 'VEL'
        k = r['keeper_at_kick']; sh = r['shooter']
        dive = any(i in range(857, 869) or i in range(973, 999) for i in r['keeper_imgs'])
        print(name, g, 'kick', r['kick'], 'ball', (bx, by), 'dist', dist, zone, 'cross_x', r['cross_x'],
              'z', r.get('z_at_line'), 'keeper', k[:2] if k else None, 'flight', r['frames_in_flight'],
              'shooter', sh[1], round(sh[0]), 'dive', dive)
