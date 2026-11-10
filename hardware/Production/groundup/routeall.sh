#!/bin/bash
# full routing: Kelvin pairs first, then everything else at 0.2 mm, then what is left at 0.15 mm
KV='ACP_F|ACN_F|SRP_F|SRN_F|/Cells and Gauge/SR[PN]$'
./route1.sh Monolith.kicad_pcb rk.kicad_pcb "--only='$KV'" > new/rk.log 2>&1
./route1.sh rk.kicad_pcb rs.kicad_pcb > new/rs.log 2>&1
./route1.sh rs.kicad_pcb rt.kicad_pcb --w=0.15 > new/rt.log 2>&1
grep -c FAILED new/rk.log new/rs.log new/rt.log; grep "routed\|unconnected\|edges" new/rk.log new/rs.log new/rt.log
