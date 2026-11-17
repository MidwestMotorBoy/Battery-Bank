#!/usr/bin/env python3
"""chk.py base_geo.json spec.json [--out=after_geo.json] [--maxexc=mm] [--json=result.json] [--full]
Check a track-edit spec against the board dump it was made for, without KiCad:
  hard checks (exit 1): same pads and vias joined on every net, no orphaned track groups, clearance of every new track
                        (board rules, old shortfalls grandfathered), no zero-length / duplicate / too-narrow track,
                        optional limit on how far a new centre line leaves the old copper of its net (--maxexc)
  reported:             new segments off the 45 degree grid, audit counts before -> after
--out writes the dump with the spec applied (tracks only; zone fills in it are the old ones), for pic.py / audit.py /
the next pass."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geolib as G
a = [x for x in sys.argv[1:] if not x.startswith('--')]; O = dict((x[2:].split('=', 1) + ['1'])[:2] for x in sys.argv[1:] if x.startswith('--'))
g0 = G.load(a[0]); spec = json.load(open(a[1]))
res, g1 = G.check(g0, spec, maxexc=float(O['maxexc']) if 'maxexc' in O else None)
if 'out' in O: json.dump(g1, open(O['out'], 'w'))
if 'json' in O: json.dump(res, open(O['json'], 'w'), indent=1)
print('tracks %d -> %d   (deleted %d, added %d)   nets changed %d' % (res['tracks'][0], res['tracks'][1], res['deleted'], res['added'], len(res['nets_changed'])))
print('nets where pads/vias that were joined are now apart:', res['connectivity_changed'] or 'none')
print('nets where separate groups (in this model) became joined, same net, harmless:', res['connectivity_merged'] or 'none')
print('new orphan track groups:', res['orphan_groups'] or 'none')
print('clearance violations: %d' % len(res['clearance']))
for v in res['clearance'][:None if 'full' in O else 15]: print('   ', v)
print('zero-length %d, below min width %d, duplicate tracks %d -> %d, unknown nets %s' % (len(res['new_zero_length']), len(res['new_below_min_width']), res['duplicates'][0], res['duplicates'][1], res['unknown_nets'] or 'none'))
print('new segments off the 45 degree grid: %d' % len(res['new_off45']))
for v in res['new_off45'][:None if 'full' in O else 8]: print('   ', v)
print('largest excursion of a new centre line from the old copper of its net: %.3f mm' % res['excursion_max_mm'], '' if not res['excursion_over_limit'] else 'OVER LIMIT: %s' % res['excursion_over_limit'][:10])
print('audit, before -> after:')
for k, (x, y) in res['audit'].items(): print('   %-14s %5d -> %5d %s' % (k, x, y, '  WORSE' if y > x else ''))
print('RESULT:', 'OK' if res['ok'] else 'FAIL')
sys.exit(0 if res['ok'] else 1)
