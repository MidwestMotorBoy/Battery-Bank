import os, sys  # peec.py, loops.py, board.py, sx.py, run_all_defs.py live in hardware/Production/groundup/compare/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare'))
if 'PCB' not in os.environ: sys.exit('Set PCB to the hand-routed board: git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb > hand.kicad_pcb')
import json, pickle, numpy as np, sys
from loops import *
H = 0.3
res = {}; maps = {}
HOT = [
 ('P1 VBUS leg (Q401)', (103.4,120.4,86.8,102.6), '/USB Port 1/AC_SNS_N', ['C430','C420','C423','C424','C427','C456','C421'], 'Q401', ['2','3','4'], ['5','6','7']),
 ('P1 PACK leg (Q402)', (103.4,120.4,94.0,104.6), '/USB Port 1/BAT_SNS_P', ['C438','C431','C434'], 'Q402', ['2','3','4'], ['5','6','7']),
 ('P2 VBUS leg (Q501)', (80.0,97.4,86.8,102.6), '/USB Port 2/AC_SNS_N', ['C530','C520','C523','C524','C527','C556','C521'], 'Q501', ['2','3','4'], ['5','6','7']),
 ('P2 PACK leg (Q502)', (80.0,97.4,94.0,104.6), '/USB Port 2/BAT_SNS_P', ['C538','C531','C534'], 'Q502', ['2','3','4'], ['5','6','7']),
 ('P1 5V buck (U404)', (97.0,107.5,102.5,116.5), 'PACK_P', ['C446','C444','C209','C210','C213'], 'U404', ['3'], ['4']),
 ('P2 5V buck (U504)', (83.0,94.5,112.5,123.5), 'PACK_P', ['C546','C544'], 'U504', ['3'], ['4']),
 ('3V3 buck (U204)', (77.6,87.0,124.5,134.0), 'PACK_P', ['C206'], 'U204', ['2'], ['1']),
]
only = sys.argv[1:] 
for k,(name, box, pnet, caps, dev, dp, sp) in enumerate(HOT):
    if only and str(k) not in only: continue
    o, m = hot_loop(name, box, pnet, caps, dev, dp, sp, h=H)
    print(fmt(o), flush=True)
    best = min(o['caps'], key=o['caps'].get)
    maps[name] = {'box': m.box, 'h': m.h, 'best': best, 'mbest': currmap(m, m.curr[best]), 'mall': currmap(m, m.curr['all'])}
    res[name] = o; del m
    json.dump(res, open('hot_%s.json' % ('_'.join(only) or 'all'), 'w'), indent=1, default=float)
    pickle.dump(maps, open('maps_%s.pkl' % ('_'.join(only) or 'all'), 'wb'))
