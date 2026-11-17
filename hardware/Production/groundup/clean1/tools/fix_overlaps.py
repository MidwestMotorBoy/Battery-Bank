#!/usr/bin/env python3
"""fix_overlaps.py [base_geo.json] [out_spec.json] [--noacute] [--proposals] [--log=file]

Redundant / overlapping copper (point e of the clean form). Makes a spec against the base board.

  A. mechanical, whole board (RF nets excluded):
     A1  exact duplicates (same net, layer, end points)            -> one piece, the widest
     A2  collinear pieces on one exact 0/45/90 line that overlap    -> one piece per stretch, widest width per stretch,
         a node kept wherever another track of the net ends on the line or the width changes  (copper outline unchanged)
     A3  a via of the net whose centre lies on the centre line of an exact 0/45/90 track (<= 0.03 mm) with no node
         -> the track is split at the foot point (nothing moves)
  B. reviewed list (HAND below): near-duplicates, stubs, crossings, small loops. Every entry was looked at in a picture.

  --noacute    do not make a node on a through track where the branch leaves at 45 degrees (the audit calls every such
               T 'acute'); the branch then ends on the centre line of the unsplit through track, as on the base board.
  --proposals  also apply the PROPOSALS list (routing decisions that the task rules leave to the lead).
  --tees       also split every other track on which a branch of its net ends exactly on the centre line with no node
               (10 on the base board, none of them flagged by the audit; nothing moves).
"""
import json, sys, math, collections, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geolib as G

RF = ('/MCU/RFIO', '/MCU/ANT_IN', 'Net-(C313-Pad2)')
MM = 1e-6
def nm(v): return int(round(v * 1e6))
def P(x, y): return (nm(x), nm(y))

class Work:
    def __init__(s, g, noacute=False, log=None):
        s.g = g; s.base = {t['id']: t for t in g['tracks']}; s.T = dict(s.base); s.n = 0; s.noacute = noacute; s.logf = log
        s.vias = collections.defaultdict(list); s.pads = collections.defaultdict(list)
        for v in g['vias']:
            for l in G.LN[G.LN.index(v['top']):G.LN.index(v['bot']) + 1]: s.vias[(v['net'], l)].append(v)
        for p in g['pads']:
            for l in p['L']: s.pads[(p['net'], l)].append(p)
        s.notes = []
    def log(s, *a):
        msg = ' '.join(str(x) for x in a); s.notes.append(msg)
        if s.logf: s.logf.write(msg + '\n')
    # ---- primitives
    def find(s, pfx):
        m = [t for i, t in s.T.items() if i.startswith(pfx)]
        if len(m) != 1: raise KeyError('track %s: %d matches' % (pfx, len(m)))
        return m[0]
    def has(s, pfx): return any(i.startswith(pfx) for i in s.T)
    def dele(s, pfx, why=''):
        t = s.find(pfx); del s.T[t['id']]
        s.log('  del  %s %s %s w%.2f (%.4f,%.4f)-(%.4f,%.4f) %s' % (t['id'][:8], t['net'], t['l'], t['w'] * MM, t['x1'] * MM, t['y1'] * MM, t['x2'] * MM, t['y2'] * MM, why))
        return t
    def add(s, net, l, w, a, b, why=''):
        assert a != b, 'zero length'
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        t = dict(id='ovl-%04d' % s.n, net=net, l=l, w=int(w), x1=a[0], y1=a[1], x2=b[0], y2=b[1], new=True); s.n += 1
        t['on45'] = (dx == 0 or dy == 0 or dx == dy)
        s.T[t['id']] = t
        s.log('  add  %s %s w%.2f (%.4f,%.4f)-(%.4f,%.4f) %s%s' % (net, l, w * MM, a[0] * MM, a[1] * MM, b[0] * MM, b[1] * MM, why, '' if t['on45'] else '  [off 45]'))
        return t
    def group(s, net, l): return [t for t in s.T.values() if t['net'] == net and t['l'] == l]
    def ends_at(s, net, l, pt, skip=()):
        return [t for t in s.group(net, l) if pt in G.P(t) and t['id'] not in skip]
    def through(s, net, l, pt):
        """tracks of the net whose centre line passes exactly through pt, strictly between their ends"""
        r = []
        for t in s.group(net, l):
            a, b = G.P(t)
            if pt in (a, b) or a == b: continue
            cr = (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0])
            dot = (pt[0] - a[0]) * (b[0] - a[0]) + (pt[1] - a[1]) * (b[1] - a[1]); L2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
            if cr == 0 and 0 < dot < L2: r.append(t)
        return r
    def makes_acute(s, t, pt, skip=()):
        """would a node at pt on track t put another piece of the net at less than 89 degrees to one half of t?"""
        a, b = G.P(t)
        for u in s.ends_at(t['net'], t['l'], pt, skip=(t['id'],) + tuple(skip)):
            o = G.P(u)[1] if G.P(u)[0] == pt else G.P(u)[0]
            for q in (a, b):
                ax, ay = q[0] - pt[0], q[1] - pt[1]; bx, by = o[0] - pt[0], o[1] - pt[1]
                c = (ax * bx + ay * by) / math.hypot(ax, ay) / math.hypot(bx, by)
                ang = math.degrees(math.acos(max(-1, min(1, c))))
                if 1 <= ang < 89: return True
        return False
    def split(s, net, l, pt, why='', force=False):
        """make a node at pt on the track of net/layer that runs through it"""
        th = s.through(net, l, pt)
        if not th:
            if s.ends_at(net, l, pt): return None
            raise ValueError('no track of %s on %s through (%.4f,%.4f)' % (net, l, pt[0] * MM, pt[1] * MM))
        out = []
        for t in th:
            if s.noacute and not force and s.makes_acute(t, pt):
                s.log('  (no node at (%.4f,%.4f) on %s: a branch leaves at 45 deg, --noacute)' % (pt[0] * MM, pt[1] * MM, t['id'][:8])); continue
            a, b = G.P(t); del s.T[t['id']]
            s.log('  split %s %s %s w%.2f (%.4f,%.4f)-(%.4f,%.4f) at (%.4f,%.4f) %s' % (t['id'][:8], net, l, t['w'] * MM, a[0] * MM, a[1] * MM, b[0] * MM, b[1] * MM, pt[0] * MM, pt[1] * MM, why))
            out += [s.add(net, l, t['w'], a, pt), s.add(net, l, t['w'], pt, b)]
        return out
    def cross(s, net, l, pt, why='crossing -> 4-way node'):
        """two tracks of the net cross at pt with no node: split both"""
        th = s.through(net, l, pt); assert len(th) == 2, ('cross: %d tracks through' % len(th), net, l, pt)
        (a, b), (c, d) = G.P(th[0]), G.P(th[1])
        perp = (b[0] - a[0]) * (d[0] - c[0]) + (b[1] - a[1]) * (d[1] - c[1]) == 0
        if s.noacute and not perp:
            s.log('  (no node at the crossing (%.4f,%.4f): the two tracks cross at 45 deg, --noacute)' % (pt[0] * MM, pt[1] * MM)); return None
        return s.split(net, l, pt, why, force=True)
    def del_on(s, net, l, a, b, why=''):
        """delete every piece of the net that lies on the segment a-b (both ends on it)"""
        def on(q):
            cr = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0]); dot = (q[0] - a[0]) * (b[0] - a[0]) + (q[1] - a[1]) * (b[1] - a[1])
            return cr == 0 and 0 <= dot <= (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        m = [t for t in s.group(net, l) if on(G.P(t)[0]) and on(G.P(t)[1])]
        assert m, ('del_on: nothing on', a, b)
        for t in m: s.dele(t['id'], why)
    def retip(s, pfx, old, new, why='', w=None):
        t = s.find(pfx); a, b = G.P(t)
        assert old in (a, b), ('retip: %s has no end at' % pfx, old)
        keep = b if old == a else a
        del s.T[t['id']]
        s.log('  retip %s %s %s (%.4f,%.4f) -> (%.4f,%.4f) %s' % (t['id'][:8], t['net'], t['l'], old[0] * MM, old[1] * MM, new[0] * MM, new[1] * MM, why))
        return s.add(t['net'], t['l'], w or t['w'], keep, new)
    # ---- A1 duplicates
    def a1(s):
        s.log('A1 exact duplicates'); n = 0
        seen = collections.defaultdict(list)
        for t in s.T.values():
            if t['net'] in RF: continue
            seen[(t['net'], t['l'], frozenset(G.P(t)))].append(t)
        for k, ts in seen.items():
            if len(ts) > 1:
                ts.sort(key=lambda t: -t['w'])
                for t in ts[1:]: s.dele(t['id'], 'duplicate of %s' % ts[0]['id'][:8]); n += 1
        return n
    # ---- A2 collinear overlap on exact lines
    @staticmethod
    def linekey(t):
        a, b = G.P(t); dx, dy = b[0] - a[0], b[1] - a[1]
        if a == b: return None
        if dy == 0: return ('H', a[1]), a[0], b[0]
        if dx == 0: return ('V', a[0]), a[1], b[1]
        if dx == dy: return ('D1', a[1] - a[0]), a[0], b[0]
        if dx == -dy: return ('D2', a[1] + a[0]), a[0], b[0]
        return None
    @staticmethod
    def linept(key, p):
        k, c = key
        return {'H': (p, c), 'V': (c, p), 'D1': (p, p + c), 'D2': (p, c - p)}[k]
    def a2(s):
        s.log('A2 collinear overlaps'); n = 0
        byline = collections.defaultdict(list)
        for t in list(s.T.values()):
            if t['net'] in RF: continue
            k = s.linekey(t)
            if k: byline[(t['net'], t['l'], k[0])].append((min(k[1], k[2]), max(k[1], k[2]), t))
        for (net, l, key), items in sorted(byline.items(), key=lambda kv: (kv[0][0], kv[0][1], str(kv[0][2]))):
            if len(items) < 2: continue
            items.sort(key=lambda x: (x[0], x[1])); groups = []; cur = [items[0]]; hi = items[0][1]
            for it in items[1:]:
                if it[0] < hi: cur.append(it); hi = max(hi, it[1])
                else: groups.append(cur); cur = [it]; hi = it[1]
            groups.append(cur)
            for grp in groups:
                if len(grp) < 2: continue
                ids = {it[2]['id'] for it in grp}
                ps = sorted({p for it in grp for p in it[:2]})
                segs = []
                for p0, p1 in zip(ps, ps[1:]):
                    w = max(it[2]['w'] for it in grp if it[0] <= p0 and it[1] >= p1); segs.append([p0, p1, w])
                # union as one track per stretch; where must a node stay?
                def ext_at(p):
                    pt = s.linept(key, p)
                    if s.ends_at(net, l, pt, skip=ids): return True
                    if any((v['x'], v['y']) == pt for v in s.vias[(net, l)]): return True
                    if any((q['x'], q['y']) == pt for q in s.pads[(net, l)]): return True
                    return False
                def acute_at(p, p_lo, p_hi):
                    pt = s.linept(key, p); fake = dict(id='?', net=net, l=l, x1=s.linept(key, p_lo)[0], y1=s.linept(key, p_lo)[1], x2=s.linept(key, p_hi)[0], y2=s.linept(key, p_hi)[1])
                    return s.makes_acute(fake, pt, skip=ids)
                out = [segs[0][:]]
                for sg in segs[1:]:
                    p = sg[0]; brk = sg[2] != out[-1][2]
                    if not brk and ext_at(p):
                        if s.noacute and acute_at(p, ps[0], ps[-1]): s.log('  (no node at (%.4f,%.4f): a branch leaves at 45 deg, --noacute)' % tuple(v * MM for v in s.linept(key, p)))
                        else: brk = True
                    if brk: out.append(sg[:])
                    else: out[-1][1] = sg[1]
                have = sorted((it[0], it[1], it[2]['w']) for it in grp); want = sorted(tuple(o) for o in out)
                if have == want: continue
                s.log(' collinear group %s %s line %s: %d pieces -> %d' % (net, l, key, len(grp), len(out)))
                for it in grp: s.dele(it[2]['id'])
                for p0, p1, w in out: s.add(net, l, w, s.linept(key, p0), s.linept(key, p1))
                n += 1
        return n
    # ---- A3 via on the centre line without a node
    def a3(s, tol=30000):
        s.log('A3 via on centre line without node'); n = 0
        for t in list(s.T.values()):
            if t['net'] in RF or t['id'] not in s.T: continue
            k = s.linekey(t)
            if not k: continue
            a, b = G.P(t); L = G.tlen(t)
            for v in s.vias[(t['net'], t['l'])]:
                c = (v['x'], v['y'])
                if c in (a, b): continue
                ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; sp = (c[0] - a[0]) * ux + (c[1] - a[1]) * uy
                d = abs((c[0] - a[0]) * uy - (c[1] - a[1]) * ux)
                if d > tol or sp <= v['d'] / 2 or sp >= L - v['d'] / 2: continue
                # foot point on the exact line (integer): parameter is x (or y on a vertical)
                key = k[0]; p = c[1] if key[0] == 'V' else (c[0] if key[0] == 'H' else int(round(a[0] + sp * ux)))
                pt = s.linept(key, p)
                if s.split(t['net'], t['l'], pt, 'via %s on the centre line (off %.3f)' % (v['id'][:8], d * MM), force=True): n += 1
                break
        return n
    # ---- A4 (optional) every other T whose branch ends exactly on the centre line of an unsplit track
    def a4(s):
        s.log('A4 exact T junctions without a node (whole board)'); n = 0
        for t in list(s.T.values()):
            if t['net'] in RF or t['id'] not in s.T: continue
            for e in G.P(t):
                if s.through(t['net'], t['l'], e) and s.split(t['net'], t['l'], e, 'T (branch %s)' % t['id'][:8], force=True): n += 1
        return n
    # ---- spec
    def spec(s):
        dele = [i for i in s.base if i not in s.T]; add = [t for t in s.T.values() if t.get('new')]
        # a new piece identical to a deleted one: keep the old one
        def key(t): return (t['net'], t['l'], t['w'], frozenset(G.P(t)))
        old = collections.defaultdict(list)
        for i in dele: old[key(s.base[i])].append(i)
        add2 = []
        for t in add:
            k = key(t)
            if old.get(k): dele.remove(old[k].pop())
            else: add2.append(t)
        return {'tag': 'ovl', 'del': sorted(dele), 'add': [dict(net=t['net'], l=t['l'], w=t['w'], x1=t['x1'], y1=t['y1'], x2=t['x2'], y2=t['y2']) for t in add2]}

# ------------------------------------------------------------------------------------------------ the reviewed list
def hand_pre(W):
    """whole pieces that go (before the mechanical merge)"""
    W.log('B reviewed list, deletions')
    # F /USB Port 2/REGN, pin U503.24: a second, 1 degree off escape lying on the proper one (6897187d + 1c2893b3)
    W.dele('4821f3b1', 'near-duplicate pin escape U503.24')
    # F /USB Port 1/REGN, pin U403.24: the same
    W.dele('3e26b193', 'near-duplicate pin escape U403.24')
    # F /USB Port 2/TS, pin U503.8: second escape ending on the body of 80f1fed8
    W.dele('0f487ed7', 'near-duplicate pin escape U503.8')
    # F SCL / SDA at U401.9 / U401.8: two escapes 3 um apart, keep the one that ends on the node
    W.dele('c0b75c8d', 'near-duplicate pin escape U401.9'); W.dele('6ceb887a', 'near-duplicate pin escape U401.8')
    # F /USB Port 1/I2CC_SCL U403.1 -> via 7345ea5e: off-angle twin of the straight piece
    W.dele('1366fb5f', 'near-duplicate pad-to-via piece')
    # F CELL_1N at U102.9: 0.2 piece pad centre -> via lying inside the 0.25 piece 89d37531
    W.dele('048ca436', 'inside the wider 89d37531')
    # F 3V3 at C403.1: 0.2 piece inside the 0.3 trunk 2824d243 (35 um off its centre line)
    W.dele('c60c0fed', 'inside the wider 2824d243')
    # F /MCU/NRST: second route R302.2 -> U301.14, 5 um beside bc322a10 + ff92856a (rebuilt in hand_post)
    for i in ('8978250a', '4ee9368b', '31e8a79b', 'ff92856a'): W.dele(i, 'NRST doubled route')
    # In2 SCL: two bumps on the vertical bb06fae2 and a second 0.4 mm branch start beside 53199a81 (small loops, Default)
    for i in ('3bd92f69', '1577a1c9', '4814fc50', '8aa136db', 'bb6b37b2', 'cd40886d', '48e86a8e', 'd7d9de8e'): W.dele(i, 'SCL In2 small loop')
    # In3 /USB Port 1/I2CC_SCL: detour b15bab92 + 648e393b + 623fe086 round the diagonal 9e97981c (loop 1.0 mm, Default)
    for i in ('b15bab92', '648e393b', '623fe086'): W.dele(i, 'I2CC_SCL In3 small loop')
    # In3 EN_5V2: 0.25 mm stub from via 58c39245 into free space
    W.dele('b4a49623', 'stub into free space')

def hand_post(W):
    W.log('B reviewed list, nodes / trims')
    # F /USB Port 2/LDO_3V3: stub of ab355357 beyond the end of 40633774; nodes for 0a76fbdf and 40633774
    t = W.retip('ab355357', P(86.725, 74.5745), P(86.625, 74.6745), 'stub trimmed to the junction')
    W.split(t['net'], 'F', P(86.575, 74.7245), 'node for 0a76fbdf')
    # F /USB Port 2/REGN: via branch 8b37c704 overshoots the trunk by 0.02
    W.retip('8b37c704', P(87.625, 105.0745), P(87.605, 105.0745), 'ends on the trunk'); W.split('/USB Port 2/REGN', 'F', P(87.605, 105.0745), 'T')
    # F PACK_P: ff4639f6 stops 0.04 short of pad C111.2 (copper touches): end it on the pad centre line
    W.retip('ff4639f6', P(93.8, 127.75), P(94.12, 127.75), 'into pad C111.2, on its centre line')
    # F SDA: 5e3796fb stops on the edge of pad R116.2
    W.retip('5e3796fb', P(107.65, 122.95), P(107.42, 122.95), 'into pad R116.2, on its centre line')
    # F CELL_1N: 70027d02 ends on the centre line of d2e8c54e
    W.split('/Cells and Gauge/CELL_1N', 'F', P(94.775, 123.5245), 'T')
    # F /USB Port 1/ACP_F (Kelvin): via spur 726c6811 ends on the centre line of 8bcd47fd; node only, nothing moves
    W.split('/USB Port 1/ACP_F', 'F', P(107.175, 109.5245), 'T')
    # F 3V3 at C403.1: ccf39f57 ran 0.05 past the trunk to reach the deleted c60c0fed
    W.retip('ccf39f57', P(108.275, 76.0245), P(108.275, 76.0745), 'ends on the trunk'); W.split('3V3', 'F', P(108.275, 76.0745), 'T')
    # F /MCU/NRST: one line C304.1 -> U301.14 with a node for the via branch
    W.add('/MCU/NRST', 'F', 200000, P(109.95, 124.08), P(111.1305, 124.08), 'NRST single route')
    W.add('/MCU/NRST', 'F', 200000, P(111.1305, 124.08), P(111.5696, 124.08), 'NRST single route')
    W.retip('cc5a8d87', P(111.125, 124.0745), P(111.1305, 124.08), 'via branch on the node')
    # F /USB Port 1/DRV_SUP: via branch d04d6f4f crosses the pin track 25 um below the 0.15 -> 0.25 step; one node
    W.retip('d04d6f4f', P(111.075, 108.3245), P(111.091, 108.3245), 'starts on the pin track')
    W.retip('2d301383', P(111.091, 108.30), P(111.091, 108.3245), 'node moved 25 um')
    W.retip('d96dc44c', P(111.091, 108.30), P(111.091, 108.3245), 'node moved 25 um')
    # F 3V3 near U301: 77d80eb4 ends on the centre line of f8df70cd
    W.split('3V3', 'F', P(114.525, 114.4745), 'T')
    # In2 SCL: branch 6162ef5d ends on the centre line of 53199a81
    W.split('SCL', 'In2', P(111.125, 122.0745), 'T')
    # In3 CELL_1N: two branches cross
    W.cross('/Cells and Gauge/CELL_1N', 'In3', P(91.875, 124.7245))
    # In2 CELL_1N: the two braided routes cross twice (see proposals P4 for the real cure)
    W.cross('/Cells and Gauge/CELL_1N', 'In2', P(91.875, 119.1745)); W.cross('/Cells and Gauge/CELL_1N', 'In2', P(95.075, 116.3745))
    # In3 Net-(U403-ACUV): 073f7cd1 runs 0.21 past the end of 56e12939 into free space
    W.retip('073f7cd1', P(108.675, 116.0745), P(108.525, 116.2245), 'stub trimmed to the junction')

# ------------------------------------------------------------------------------------------------ proposals (not applied by default)
def proposals(W):
    """routing decisions the rules leave to the lead; each one keeps every pad/via joined"""
    W.log('P proposals')
    def end_to(net, l, old, new, why):
        m = W.ends_at(net, l, old); assert len(m) == 1, (net, l, old, len(m))
        return W.retip(m[0]['id'], old, new, why)
    # P1  In2 /USB Port 2/REGN: 06f04a71 runs 4.15 mm at 0.05 mm beside 1e045432 (port 1 has ONE track there):
    #     keep 1e045432 as trunk, tee the two side branches onto it
    n = '/USB Port 2/REGN'
    W.dele('06f04a71', 'P1 parallel double')
    end_to(n, 'In2', P(88.275, 105.0745), P(88.325, 105.0745), 'P1'); W.split(n, 'In2', P(88.325, 105.0745), 'P1', force=True)
    end_to(n, 'In2', P(88.275, 109.2245), P(88.325, 109.2245), 'P1'); W.split(n, 'In2', P(88.325, 109.2245), 'P1', force=True)
    # P2  F /USB Port 2/LDO_3V3: 0a76fbdf runs 0.7 mm at 0.07 mm beside 40633774: tee the horizontal 69e8cf64 onto 40633774
    n = '/USB Port 2/LDO_3V3'
    W.dele('0a76fbdf', 'P2 parallel double')
    end_to(n, 'F', P(86.075, 74.2245), P(86.175, 74.2245), 'P2'); W.split(n, 'F', P(86.175, 74.2245), 'P2', force=True)
    W.merge_runs(n, 'F')
    # P3  F 3V3 at C503: a08381d4 runs 0.6 mm at 0.05 mm beside 7fbdb58a: tee f3889848 onto 7fbdb58a
    W.dele('a08381d4', 'P3 parallel double')
    end_to('3V3', 'F', P(85.925, 75.8745), P(85.975, 75.9245), 'P3'); W.split('3V3', 'F', P(85.975, 75.9245), 'P3', force=True)
    t = W.ends_at('3V3', 'F', P(86.525, 75.8745))[0]                   # the 0.07 mm tail of d1407149 beyond the junction
    if P(86.575, 75.9245) in G.P(t): W.dele(t['id'], 'P3 tail')
    else: W.retip(t['id'], P(86.525, 75.8745), P(86.575, 75.9245), 'P3 tail')
    # P4  In2 CELL_1N: a second route N1 (91.575,119.4745) -> via 57cdb072 braided round the first one (loop 7.4 mm,
    #     two crossings, 3 shared stretches): remove it, keep the route with fewer bends
    n = '/Cells and Gauge/CELL_1N'
    for a, b in (((91.775, 119.2745), (91.775, 119.1745)), ((91.775, 119.1745), (92.425, 119.1745)), ((92.425, 119.1745), (92.575, 119.0245)),
                 ((92.825, 118.7745), (92.825, 118.6245)), ((92.825, 118.6245), (93.225, 118.2245)), ((93.475, 117.9745), (94.075, 117.9745)),
                 ((94.075, 117.9745), (95.075, 116.9745)), ((95.075, 116.9745), (95.075, 115.2745)), ((95.075, 115.2745), (95.275, 115.2745)),
                 ((96.325, 115.2745), (96.325, 115.8245)), ((96.325, 115.8245), (96.375, 115.8245))):
        W.del_on(n, 'In2', P(*a), P(*b), 'P4 second route')
    W.merge_runs(n, 'In2')

def merge_runs(W, net, l):
    """join collinear pieces of one width that meet at a node nothing else uses (after a proposal removed the branch)"""
    again = True
    while again:
        again = False
        nodes = collections.defaultdict(list)
        for t in W.group(net, l):
            for e in G.P(t): nodes[e].append(t)
        for pt, lst in nodes.items():
            if len(lst) != 2 or lst[0]['w'] != lst[1]['w']: continue
            if any((v['x'], v['y']) == pt for v in W.vias[(net, l)]) or any((q['x'], q['y']) == pt for q in W.pads[(net, l)]): continue
            k0, k1 = W.linekey(lst[0]), W.linekey(lst[1])
            if not k0 or not k1 or k0[0] != k1[0]: continue
            if W.through(net, l, pt): continue
            if not (lst[0].get('new') or lst[1].get('new')): continue          # only undo our own splits
            if G.tlen(lst[0]) > 60000 and G.tlen(lst[1]) > 60000 and not (lst[0].get('new') and lst[1].get('new')): continue
            o = [e for t in lst for e in G.P(t) if e != pt]
            for t in lst: del W.T[t['id']]
            W.add(net, l, lst[0]['w'], o[0], o[1], 'run rejoined'); again = True; break
Work.merge_runs = merge_runs

def build(g, noacute=False, props=False, log=None, tees=False):
    W = Work(g, noacute, log)
    hand_pre(W)
    n1 = W.a1(); n2 = W.a2(); n3 = W.a3()
    hand_post(W)
    if props: proposals(W)
    if tees: W.log('A4 %d more T junctions given a node' % W.a4())
    W.log('A1 %d duplicates removed, A2 %d collinear groups merged, A3 %d vias given a node' % (n1, n2, n3))
    return W

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; o = [x for x in sys.argv[1:] if x.startswith('--')]
    base = a[0]; out = a[1]
    logfn = [x.split('=', 1)[1] for x in o if x.startswith('--log=')]
    lf = open(logfn[0], 'w') if logfn else None
    W = build(G.load(base), '--noacute' in o, '--proposals' in o, lf, '--tees' in o)
    sp = W.spec(); json.dump(sp, open(out, 'w'), indent=0)
    print('wrote %s: %d deleted, %d added' % (out, len(sp['del']), len(sp['add'])))
    print(W.notes[-1])
