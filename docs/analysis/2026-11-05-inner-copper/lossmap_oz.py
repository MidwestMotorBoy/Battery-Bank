"""Copper DC solver run with a chosen inner-layer copper weight (the 2026-11-05 INNER_OZ patch, as a wrapper).

The study patched the solver of the 2026-10-30 review so that the inner-layer sheet resistance follows an INNER_OZ
environment variable. That patched copy was not kept. This wrapper makes the same change without editing the solver:
it scales the inner-layer sheet resistance in solve.RS (0.983 mOhm/sq at 0.5 oz, inversely with the weight) and then
runs lossmap.py from hardware/Production/groundup/compare/k/, which is the same solver and the same path list.
Outer layers stay at 2 oz (0.246 mOhm/sq).

    git show 8081416:hardware/Production/Monolith.kicad_pcb > /tmp/hand_routed.kicad_pcb
    PCB=/tmp/hand_routed.kicad_pcb INNER_OZ=1 python3 lossmap_oz.py      -> cu_oz1.json (+ lossmap_oz1_*.npy) in the cwd

Needs numpy, scipy, Pillow and pyamg.
"""
import os, sys, runpy
K = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../hardware/Production/groundup/compare/k'))
sys.path.insert(0, K)
W = float(os.environ.get('INNER_OZ', '0.5'))
import solve                                   # noqa: E402  (board.py reads $PCB on import)
for L in ('In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu'):
    solve.RS[L] = 0.983e-3 * 0.5 / W           # same dict object that lossmap.py gets through "from solve import *"
os.environ.setdefault('TAG', f'oz{W:g}')
print(f'inner copper {W:g} oz: RS inner {solve.RS["In1.Cu"]*1e3:.3f} mOhm/sq, outer {solve.RS["F.Cu"]*1e3:.3f} mOhm/sq', flush=True)
runpy.run_path(os.path.join(K, 'lossmap.py'), run_name='__main__')
