#!/usr/bin/env python3
"""compose.py base_geo.json final_geo.json spec_out.json
The spec that turns the base dump into the final dump (tracks only): delete base tracks that are gone or altered,
add the final tracks that the base does not have. A final track identical to a deleted base track (same net, layer,
width, ends) is kept under its old id instead."""
import json, sys
A = json.load(open(sys.argv[1])); B = json.load(open(sys.argv[2]))
key = lambda t: (t['net'], t['l'], t['w'], frozenset(((t['x1'], t['y1']), (t['x2'], t['y2']))))
ta = {t['id']: t for t in A['tracks']}; tb = {t['id']: t for t in B['tracks']}
keep = {i for i in ta if i in tb and key(ta[i]) == key(tb[i])}
gone = {}
for i, t in ta.items():
    if i not in keep: gone.setdefault(key(t), []).append(i)
add = []
for i, t in tb.items():
    if i in keep: continue
    k = key(t)
    if gone.get(k): keep.add(gone[k].pop()); continue
    add.append(dict(net=t['net'], l=t['l'], w=t['w'], x1=t['x1'], y1=t['y1'], x2=t['x2'], y2=t['y2']))
spec = {'del': sorted(i for i in ta if i not in keep), 'add': add}
json.dump(spec, open(sys.argv[3], 'w'))
print('compose: del %d add %d (base %d tracks, final %d)' % (len(spec['del']), len(add), len(ta), len(tb)))
