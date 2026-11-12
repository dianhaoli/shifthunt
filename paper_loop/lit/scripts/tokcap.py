import csv,sys,statistics as st
rows=[r for r in csv.DictReader(open(sys.argv[1])) if r['counted'] in ('1','True','true')]
print('counted',len(rows))
for ag in sorted(set(r['agent'] for r in rows)):
  for arm in ('open8','bb8','bb64'):
    R=[r for r in rows if r['agent']==ag and r['arm'].lower().replace('-','')==arm]
    if not R: 
      continue
    t=[int(float(r['tokens_out'])) for r in R]
    print(ag,arm,len(R),'NAME',sum(int(r['name']) for r in R),'out_tok med',st.median(t),'min',min(t),'max',max(t))
def rate(ag,arm,cap):
  R=[r for r in rows if r['agent']==ag and r['arm'].lower().replace('-','')==arm]
  return sum(1 for r in R if int(r['name'])==1 and float(r['tokens_out'])<=cap)/len(R)
ag=[a for a in set(r['agent'] for r in rows) if 'gpt' in a.lower()][0]
for cap in (41000,50000,62000,70000,86000,95000,1e9):
  o,b,b64=rate(ag,'open8',cap),rate(ag,'bb8',cap),rate(ag,'bb64',cap)
  print('cap',cap,'C1=%.3f C2=%.3f C4=%.3f'%(o-b,b64-b,b64-o))
