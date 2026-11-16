#!/bin/bash
# straighten.sh <work dir> [straighten.py options]
# One straightening pass on ../Monolith.kicad_pcb, in a scratch copy: dump -> straighten.py -> straighten_apply.py (edit + zone
# refill in KiCad) -> full-rule DRC -> dumps -> topocheck.py, pourcheck.py, boarddiff.py. Nothing in the repo is written;
# the result is <work dir>/out/Monolith.kicad_pcb. KiCad 10 runs in Docker (image kicad/kicad:10.0, one container at a time;
# start the daemon first or wrap this script in ./dk.sh). Needs python 3 with shapely on the host.
set -e
G=$(cd "$(dirname "$0")" && pwd); P=$(dirname "$G"); W=$(mkdir -p "$1" && cd "$1" && pwd); shift
mkdir -p $W/in $W/out $W/kconf/10.0 $W/tools
cp $G/dumpgeo.py $G/dumpcu.py $G/straighten_apply.py $W/tools/
for d in in out; do cp -r $P/Monolith.kicad_pro $P/Monolith.kicad_dru $P/*.kicad_sch $P/MonolithDev.kicad_sym $P/fp-lib-table $P/sym-lib-table $P/MonolithDev.pretty $W/$d/; done
cp $P/Monolith.kicad_pcb $W/in/Monolith.kicad_pcb; chmod -R a+rwX $W
# the board must be called Monolith.kicad_pcb beside its .kicad_pro and .kicad_dru, or the custom rules are not applied (to DRC
# and to the zone fill); root + KiCad's own fp-lib-table, or DRC reports about 200 library warnings
kc() { docker run --rm -u 0 -v $W:/w -v $W/kconf:/root/.config/kicad -w /w kicad/kicad:10.0 "$@"; }
kc bash -c "cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table /w/kconf/10.0/"
kc python3 /w/tools/dumpgeo.py /w/in/Monolith.kicad_pcb /w/before_geo.json | tail -n 1
kc python3 /w/tools/dumpcu.py /w/in/Monolith.kicad_pcb /w/before_cu.json | tail -n 1
python3 $G/straighten.py $W/before_geo.json $W/spec.json --log=$W/log.txt "$@"
cp $P/Monolith.kicad_pro $W/in/keep.kicad_pro
kc python3 /w/tools/straighten_apply.py /w/in/Monolith.kicad_pcb /w/in/new.kicad_pcb /w/spec.json 2>&1 | grep -v swig | tail -n 1
mv $W/in/new.kicad_pcb $W/out/Monolith.kicad_pcb; rm -f $W/in/new.kicad_pr?; cp $W/in/keep.kicad_pro $W/in/Monolith.kicad_pro
kc kicad-cli pcb drc --schematic-parity --severity-all --format json -o /w/drc.json /w/out/Monolith.kicad_pcb > $W/drc.log 2>&1
cp $P/Monolith.kicad_pro $W/out/Monolith.kicad_pro                  # kicad-cli rewrites the project file
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
kc python3 /w/tools/dumpcu.py /w/out/Monolith.kicad_pcb /w/after_cu.json | tail -n 1
python3 -c "import json,sys; json.dump(sorted(json.load(open('$W/spec.json'))['protected']), open('$W/protected.json','w'))"
python3 $G/boarddiff.py $W/in/Monolith.kicad_pcb $W/out/Monolith.kicad_pcb
python3 $G/topocheck.py $W/before_geo.json $W/after_geo.json $W/topo.json --protect=$W/protected.json
python3 $G/pourcheck.py $W/before_geo.json $W/after_geo.json $W/pour.json
echo "result: $W/out/Monolith.kicad_pcb   (then: compare/tidy.py, compare/runfix.sh <board> <tag>, compare/cmpsum.py)"
