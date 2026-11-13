import os, sys  # peec.py, loops.py, board.py, sx.py, run_all_defs.py live in hardware/Production/groundup/compare/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare'))
if 'PCB' not in os.environ: sys.exit('Set PCB to the hand-routed board: git show 8dd9eb6:hardware/Production/Monolith.kicad_pcb > hand.kicad_pcb')
import peec
peec.ZC['In1.Cu']=0.07+0.1+0.00875; peec.ZC['B.Cu']=peec.ZC['In4.Cu']+0.00875+0.1+0.035
from loops import *
for args in [('P1 VBUS thin', (103.4,120.4,86.8,102.6), '/USB Port 1/AC_SNS_N', ['C430','C420','C423','C424','C427','C456','C421'], 'Q401', ['2','3','4'], ['5','6','7']),
             ('P1 PACK thin', (103.4,120.4,94.0,104.6), '/USB Port 1/BAT_SNS_P', ['C438','C431','C434'], 'Q402', ['2','3','4'], ['5','6','7'])]:
    o,m=hot_loop(*args,h=0.3); print(fmt(o),flush=True); del m
