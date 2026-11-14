#!/bin/bash
# Make the whole JLC order package for ../Monolith.kicad_pcb from one save, in this folder:
# gerbers + drill (zip), kicad-pos.csv and BOM / CPL / hand-solder list (make_jlc_files.py); prints a DRC / ERC summary.
# Needs Docker with kicad/kicad:10.0 (docker pull kicad/kicad:10.0). Works on a scratch copy: kicad-cli rewrites the
# .kicad_pro, and the board file itself is never written.
#   usage: hardware/Production/jlc/make_package.sh
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
PROD=$(dirname "$HERE")
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/p" "$WORK/cfg/10.0"
cp "$PROD"/*.kicad_pcb "$PROD"/*.kicad_sch "$PROD"/*.kicad_pro "$PROD"/*.kicad_dru "$PROD"/*.kicad_sym \
   "$PROD"/fp-lib-table "$PROD"/sym-lib-table "$WORK/p/"
cp -r "$PROD/MonolithDev.pretty" "$PROD/3dmodels" "$WORK/p/"
cp "$HERE/make_jlc_files.py" "$WORK/"
chmod -R a+rwX "$WORK"

docker run --rm -u 0 -v "$WORK/p:/p" -v "$WORK/cfg:/root/.config/kicad" -v "$WORK/make_jlc_files.py:/make_jlc_files.py" \
  kicad/kicad:10.0 bash -euc '
    cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table /root/.config/kicad/10.0/
    cd /p && mkdir -p out/gerbers
    kicad-cli pcb drc --refill-zones --schematic-parity --severity-all --format json -o out/drc.json Monolith.kicad_pcb
    kicad-cli sch erc --severity-all --format json -o out/erc.json Monolith.kicad_sch
    kicad-cli pcb export gerbers --check-zones -o out/gerbers/ \
      --layers F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts Monolith.kicad_pcb
    kicad-cli pcb export drill -o out/gerbers/ --format excellon --excellon-units mm --excellon-separate-th Monolith.kicad_pcb
    kicad-cli pcb export pos -o out/kicad-pos.csv --format csv --units mm --side both Monolith.kicad_pcb
    python3 /make_jlc_files.py Monolith.kicad_pcb out/kicad-pos.csv out
  '

# inner-layer names carry the layer descriptions ("In1_Cu (GND)"): drop them so no file name has spaces, in the job file too
cd "$WORK/p/out/gerbers"
for f in *" ("*; do
  n=$(echo "$f" | sed -E 's/ \([^)]*\)//'); mv "$f" "$n"
  sed -i "s|\"Path\": \"$f\"|\"Path\": \"$n\"|" Monolith-job.gbrjob
done
rm -f "$HERE/Monolith_gerbers_JLC.zip"
zip -q -X "$HERE/Monolith_gerbers_JLC.zip" Monolith-*
cd "$WORK/p/out"
cp Monolith_*.csv kicad-pos.csv "$HERE/"
python3 - <<'PY'
import collections, json
for f in ('drc.json', 'erc.json'):
    d = json.load(open(f))
    v = d.get('violations', []) + [x for s in d.get('sheets', []) for x in s['violations']]
    c = collections.Counter((x['severity'], x['type']) for x in v)
    extra = f", unconnected {len(d.get('unconnected_items', []))}, parity {len(d.get('schematic_parity', []))}" if f == 'drc.json' else ''
    print(f"{f}: errors {sum(n for (s, _), n in c.items() if s == 'error')}{extra}; " + ', '.join(f'{t} {n}' for (_, t), n in sorted(c.items())))
PY
echo "package written to $HERE"
