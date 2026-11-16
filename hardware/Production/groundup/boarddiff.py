#!/usr/bin/env python3
"""boarddiff.py before.kicad_pcb after.kicad_pcb     (plain python 3)
Compares two board files item by item at the file level: header, setup, layers, footprints (with every pad), vias,
graphics and zones without their fills must be identical; tracks may differ and are counted. Exit code 1 otherwise.
Use after a track-only edit to show that nothing else was touched."""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../docs/reviews/2026-10-30-routed-board/tools'))
from sx import parse
A, B = (parse(open(f, encoding='utf-8').read()) for f in sys.argv[1:3]); bad = 0
kinds = list(collections.OrderedDict((x[0], 1) for t in (A, B) for x in t[1:] if isinstance(x, list)))
nofill = lambda z: [x for x in z if not (isinstance(x, list) and x and x[0] == 'filled_polygon')]
for k in kinds:
    xa = [x for x in A[1:] if isinstance(x, list) and x[0] == k]; xb = [x for x in B[1:] if isinstance(x, list) and x[0] == k]
    if k == 'segment':
        sa, sb = collections.Counter(map(str, xa)), collections.Counter(map(str, xb))
        print('%-18s %5d -> %5d   only before %d, only after %d' % (k, len(xa), len(xb), sum((sa - sb).values()), sum((sb - sa).values()))); continue
    if k == 'zone':
        fa = sum(1 for z in xa for x in z if isinstance(x, list) and x and x[0] == 'filled_polygon'); fb = sum(1 for z in xb for x in z if isinstance(x, list) and x and x[0] == 'filled_polygon')
        same = [nofill(z) for z in xa] == [nofill(z) for z in xb]
        print('%-18s %5d -> %5d   %s (outline, net, layers, priority, settings); filled pieces %d -> %d, %d zones with a changed fill' % (k, len(xa), len(xb), 'identical' if same else 'DIFFERENT', fa, fb, sum(1 for p, q in zip(xa, xb) if p != q)))
    else:
        same = xa == xb; print('%-18s %5d -> %5d   %s' % (k, len(xa), len(xb), 'identical' if same else 'DIFFERENT'))
    bad += not same
sys.exit(1 if bad else 0)
