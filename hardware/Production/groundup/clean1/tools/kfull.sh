#!/bin/bash
# kfull.sh <spec.json> <work dir> [base board .kicad_pcb, default ../../../Monolith.kicad_pcb]
# Apply a spec to the board in KiCad 10 (Docker image kicad/kicad:10.0), refill the zones, run the full-rule DRC,
# dump the result, check the pours and diff the two board files. One KiCad at a time (lock file in /tmp).
# Result: <work dir>/out/Monolith.kicad_pcb, after_geo.json, drc.json, pour.json. Writes nothing in the repo.
set -e
T=$(cd "$(dirname "$0")" && pwd); G=$(cd $T/../.. && pwd); P=$(dirname $G)
SPEC=$(realpath "$1"); W=$(mkdir -p "$2" && cd "$2" && pwd); BASE=${3:-$P/Monolith.kicad_pcb}
exec 9>/tmp/clean1_kicad.lock; flock 9
mkdir -p $W/in $W/out $W/kconf/10.0 $W/tools
cp $G/dumpgeo.py $G/dumpcu.py $G/straighten_apply.py $W/tools/
for d in in out; do cp -r $P/Monolith.kicad_pro $P/Monolith.kicad_dru $P/*.kicad_sch $P/MonolithDev.kicad_sym $P/fp-lib-table $P/sym-lib-table $P/MonolithDev.pretty $W/$d/; done
cp $BASE $W/in/Monolith.kicad_pcb; cp $SPEC $W/spec.json; chmod -R a+rwX $W
kc() { docker run --rm -u 0 -v $W:/w -v $W/kconf:/root/.config/kicad -w /w kicad/kicad:10.0 "$@"; }
kc bash -c "cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table /w/kconf/10.0/"
[ -f $W/before_geo.json ] || kc python3 /w/tools/dumpgeo.py /w/in/Monolith.kicad_pcb /w/before_geo.json | tail -n 1
cp $P/Monolith.kicad_pro $W/in/keep.kicad_pro
kc python3 /w/tools/straighten_apply.py /w/in/Monolith.kicad_pcb /w/in/new.kicad_pcb /w/spec.json 2>&1 | grep -v swig | tail -n 1
mv $W/in/new.kicad_pcb $W/out/Monolith.kicad_pcb; rm -f $W/in/new.kicad_pr?; cp $W/in/keep.kicad_pro $W/in/Monolith.kicad_pro
kc kicad-cli pcb drc --schematic-parity --severity-all --format json -o /w/drc.json /w/out/Monolith.kicad_pcb > $W/drc.log 2>&1
cp $P/Monolith.kicad_pro $W/out/Monolith.kicad_pro
python3 - $W/drc.json <<'PY'
import json, sys, collections
d = json.load(open(sys.argv[1])); v = d.get('violations', [])
print('DRC: errors', sum(1 for x in v if x['severity'] == 'error'), 'warnings', sum(1 for x in v if x['severity'] == 'warning'), 'unconnected', len(d.get('unconnected_items', [])), 'parity', len(d.get('schematic_parity', [])),
      dict(collections.Counter(x['type'] for x in v)))
for x in v:
    if x['severity'] == 'error': print('  ERROR', x['type'], '; '.join('%s @(%.3f, %.3f)' % (i['description'][:70], i['pos']['x'], i['pos']['y']) for i in x['items']))
for x in d.get('unconnected_items', []): print('  UNCONNECTED', '; '.join('%s @(%.3f, %.3f)' % (i['description'][:70], i['pos']['x'], i['pos']['y']) for i in x['items']))
PY
kc python3 /w/tools/dumpgeo.py /w/out/Monolith.kicad_pcb /w/after_geo.json | tail -n 1
python3 $G/pourcheck.py $W/before_geo.json $W/after_geo.json $W/pour.json | tail -n 25
python3 $G/boarddiff.py $W/in/Monolith.kicad_pcb $W/out/Monolith.kicad_pcb | tail -n 8
