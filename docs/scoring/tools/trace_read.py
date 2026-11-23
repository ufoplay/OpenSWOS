import re
def read(path):
    """frame -> {'view': (x, y), 'sprites': [(img, sx, sy)]}"""
    out = {}
    cur = None
    for line in open(path):
        if line.startswith('frame ') and ' sprites ' in line:
            p = line.split()
            f = int(p[1])
            v = p.index('view')
            cur = out.setdefault(f, {'view': (int(p[v + 1]), int(p[v + 2])), 'sprites': []})
            cur['sprites'] = []
        elif line.startswith('  sprite ') and cur is not None:
            _, img, x, y = line.split()
            cur['sprites'].append((int(img), int(x), int(y)))
    return out
