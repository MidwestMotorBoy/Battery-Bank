#!/bin/bash
# finish.sh <board under new/> : DRC, drop flagged router copper until the report is quiet -> new/<name>_c.kicad_pcb
b=${1%.kicad_pcb}
cp new/$b.kicad_pcb new/${b}_c.kicad_pcb
for k in 1 2 3 4 5 6; do
  ./kc kicad-cli pcb drc --schematic-parity --severity-all --format json -o /w/new/drc_${b}_c.json /w/new/${b}_c.kicad_pcb > new/drc.log 2>&1
  r=$(./kc python3 /w/cleanup.py /w/new/${b}_c.kicad_pcb /w/new/${b}_c.kicad_pcb /w/new/drc_${b}_c.json /w/new/Monolith.kicad_pcb --errors | tail -1)
  echo "round $k: $r"
  case "$r" in "removed 0 "*) break;; esac
done
cp base/Monolith.kicad_pro new/Monolith.kicad_pro
./kc kicad-cli pcb drc --schematic-parity --severity-all --format json -o /w/new/drc_${b}_c.json /w/new/${b}_c.kicad_pcb > new/drc.log 2>&1
python3 drcsum.py new/drc_${b}_c.json
