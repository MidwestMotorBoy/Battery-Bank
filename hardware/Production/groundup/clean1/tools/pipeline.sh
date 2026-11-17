#!/bin/bash
# pipeline.sh <base_geo.json> <out dir>
# Round 1 of the clean-up, all in plain python on a dump from ../../dumpgeo.py (no KiCad needed):
#   overlaps -> junctions/entries/angles -> one width per run -> straighten (default, then relaxed), and the last three
#   again up to three times. Every step is checked by chk.py against the step before; the result is <out dir>/spec.json
#   (against the base dump) and <out dir>/after.json. Apply it in KiCad with kfull.sh.
set -e
T=$(cd "$(dirname "$0")" && pwd); G=$(cd $T/../.. && pwd)
BASE=$(realpath "$1"); O=$(mkdir -p "$2" && cd "$2" && pwd); cd $O
ck() { python3 $T/chk.py "$@" > chk_last.txt || { cat chk_last.txt; echo "CHK FAILED: $*"; exit 1; }; grep -E "^tracks" chk_last.txt; }
python3 $T/fix_overlaps.py $BASE sp1.json --proposals --log=overlaps.log > /dev/null
ck $BASE sp1.json --out=s1.json --maxexc=0.3
python3 $T/rethread.py s1.json sp2.json --log=rethread1.log | tail -1
ck s1.json sp2.json --out=s2.json --maxexc=0.8
python3 $T/runwidth.py s2.json sp3.json --log=runwidth1.log > /dev/null
ck s2.json sp3.json --out=s3.json --maxexc=0.001
python3 $G/straighten.py s3.json sp4.json --log=str1.log | grep "changed runs"
ck s3.json sp4.json --out=s4.json
python3 $G/straighten.py s4.json sp5.json --log=str2.log --protect=$T/protect2.json --maxmove=0.6 | grep "changed runs"
ck s4.json sp5.json --out=s5.json
cur=s5.json
for i in 1 2 3; do
  python3 $T/rethread.py $cur r$i.json --log=rethread_l$i.log --exc-from=$cur | tail -1
  ck $cur r$i.json --out=a$i.json --maxexc=0.8
  python3 $T/runwidth.py a$i.json w$i.json --log=runwidth_l$i.log > /dev/null
  ck a$i.json w$i.json --out=b$i.json --maxexc=0.001
  python3 $G/straighten.py b$i.json t$i.json --log=str_l$i.log --protect=$T/protect2.json --maxmove=0.6 | grep "changed runs"
  ck b$i.json t$i.json --out=c$i.json
  cur=c$i.json
  n=$(python3 -c "import json;print(sum(len(json.load(open(f))['del']) for f in ('r$i.json','w$i.json','t$i.json')))")
  echo "loop $i: $n tracks touched"; [ "$n" = 0 ] && break
done
cp $cur final.json
python3 $T/compose.py $BASE final.json spec.json
python3 $T/chk.py $BASE spec.json --out=after.json | tee chk.txt | tail -19
