import csv,collections,json
r=list(csv.DictReader(open('rows_r1112.csv')))
cells=collections.defaultdict(list)
for x in r: cells[(x['agent'],x['arm'],x['episode'])].append(int(x['identified'])*int(x['no_extra']))
cm=list(csv.DictReader(open('cm.csv')))
for x in cm:
  if x['batch'] in('b1','b2'): cells[(x['agent'],'main',x['episode'])].append(int(x['hard_pass']))
bb16={"ep411":(4,4),"ep413":(3,4),"ep415":(2,4),"ep472":(3,4),"ep474":(2,4),"ep476":(2,4)}
for e,(p,n) in bb16.items(): cells[('gpt','bb16',e)]=[1]*p+[0]*(n-p)
def icc1(groups):
  groups=[g for g in groups if len(g)>=2]
  N=sum(len(g) for g in groups); a=len(groups); gm=sum(map(sum,groups))/N
  ssb=sum(len(g)*(sum(g)/len(g)-gm)**2 for g in groups); ssw=sum(sum((v-sum(g)/len(g))**2 for v in g) for g in groups)
  msb=ssb/(a-1); msw=ssw/(N-a); k0=(N-sum(len(g)**2 for g in groups)/N)/(a-1)
  return (msb-msw)/(msb+(k0-1)*msw), msw, k0, a, N
def pairagree(groups):
  ag=tot=0
  for g in groups:
    for i in range(len(g)):
      for j in range(i+1,len(g)): tot+=1; ag+= g[i]==g[j]
  return ag/tot, tot
for name,sel in [('main',lambda k:k[1]=='main'),('block1',lambda k:k[1] in('open8','bb8','bb64')),('terra block1+bb16',lambda k:k[0]=='gpt' and k[1] in('open8','bb8','bb64','bb16')),('all with reps',lambda k:True)]:
  gs=[cells[k] for k in cells if sel(k)]
  i,msw,k0,a,N=icc1(gs); pa,t=pairagree(gs)
  mixed=sum(1 for g in gs if 0<sum(g)<len(g))
  sb=lambda m: m*i/(1+(m-1)*i)
  # runs per cell for cell-mean reliability 0.8
  m80=0.8*(1-i)/(i*0.2) if i>0 else float('inf')
  print(f"{name}: cells {a} runs {N} mixed {mixed} ICC1 {i:.3f} within-var {msw:.3f} k0 {k0:.2f} pair-agree {pa:.3f} ({t} pairs) cell-mean rel at k0 {sb(k0):.3f} runs/cell for 0.8: {m80:.1f}")
