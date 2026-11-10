#!/bin/bash
# route1.sh <in board under new/> <out board under new/> [router options]: DRC the input, route what is missing
set -e
i=$1; o=$2; shift 2
./kc kicad-cli pcb drc --schematic-parity --severity-all --format json -o /w/new/drc_in.json /w/new/$i > new/drc.log 2>&1 || true
./kc sh -c "PYTHONPATH=/w/pylib python3 /w/router.py /w/new/$i /w/new/drc_in.json /w/new/$o $*" 2>&1 | grep -v "^$"
cp base/Monolith.kicad_pro new/Monolith.kicad_pro
