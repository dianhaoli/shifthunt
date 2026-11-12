import csv,sys
R=[r for r in csv.DictReader(open(sys.argv[1])) if r['agent']=='gpt' and r['counted']=='1']
A={a:[r for r in R if r['arm']==a] for a in ('open8','bb8','bb64')}
caps=sorted(set(int(r['tokens_out']) for r in R))
rate=lambda a,c: sum(int(r['name']) and int(r['tokens_out'])<=c for r in A[a])/24
print(min(rate('bb64',c)-rate('open8',c) for c in caps), min((round(rate('open8',c)-rate('bb8',c),3),c) for c in caps))
for e in sorted(set(r['episode'] for r in R)):
  print(e,[sum(int(r['name']) for r in A[a] if r['episode']==e) for a in A])
