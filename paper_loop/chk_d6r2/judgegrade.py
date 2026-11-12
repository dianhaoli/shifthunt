# Judge-implied pass counts from committed judge.json aggregates (a20fa7b). judge pass = (cert pass - false blame) + false credit.
import json, subprocess
G='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/gpu'
d=json.loads(subprocess.check_output(['git','-C',G,'show','a20fa7b:results/blackbox_1112/judge/judge.json']))
def kn(s): a,b=s.split('/'); return int(a),int(b)
def row(name,v):
    cp,n=kn(v['certified_pass']); fb,_=kn(v['false_blame']); fc,nf=kn(v['false_credit'])
    jp=cp-fb+fc
    print(f"{name:16s} n={n:3d} certified {cp}/{n}={cp/n:.3f}  judged {jp}/{n}={jp/n:.3f}  diff {jp/n-cp/n:+.3f}")
    return cp/n, jp/n
r={}
for k,v in d['hard_by_access'].items(): r[k]=row(k,v)
for k,v in d['hard_by_agent'].items(): row(k,v)
for k,v in d['hard_by_population'].items(): row(k,v)
o,b8,b64=r['open_open8'],r['blackbox_bb8'],r['blackbox_bb64']
print('Open8-BB8 certified %+.3f judged %+.3f'%(o[0]-b8[0],o[1]-b8[1]))
print('BB64-BB8  certified %+.3f judged %+.3f'%(b64[0]-b8[0],b64[1]-b8[1]))
print('BB64-Open8 certified %+.3f judged %+.3f'%(b64[0]-o[0],b64[1]-o[1]))
