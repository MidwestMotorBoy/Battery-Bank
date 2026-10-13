"""Report overlapping text / symbols on each dev board sheet.  Usage: python tools/check_overlaps.py [sheet ...]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sch_geom as G  # noqa: E402

SHEETS = ['MonolithDev.kicad_sch', 'gauge.kicad_sch', 'power.kicad_sch', 'mcu.kicad_sch', 'usb_port.kicad_sch']
verbose = '-v' in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith('-')] or SHEETS
total = 0
for p in args:
    _, items, wires, _ = G.load(p)
    probs = G.problems(items, wires)
    total += len(probs)
    print(f'{p}: {len(probs)} overlaps')
    if verbose:
        for a, b in probs:
            print('   ', a, ' <> ', b)
print('TOTAL', total)
