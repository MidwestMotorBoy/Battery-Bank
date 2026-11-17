import sys,json,collections; sys.path.insert(0,'.')
from mylib import *
import audit as A
g=G.load(sys.argv[1] if len(sys.argv)>1 else 'after_geo.json'); R=REG
a=A.audit(g)
ins=[x for x in a if R[0]<=x['x']<R[2] and R[1]<=x['y']<R[3]]
print(sorted(collections.Counter(x['kind'] for x in ins).items()))
for x in sorted(ins,key=lambda x:(x['l'],x['net'],x['kind'],x['x'])):
    print(' ',x['kind'],x['l'],x['x'],x['y'],x['net'],{k:v for k,v in x.items() if k in('off','w','len','d','ang','pad')})
json.dump(a,open('after_audit.json','w'))
