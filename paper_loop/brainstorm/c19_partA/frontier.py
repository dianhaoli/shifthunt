exec(open('analyse_bounds.py').read().split("for name,L in")[0])
import collections
L=L9; S=list(L); n={s:sum(sum(cells[c]) for c in cs) for s,cs in L.items()}
cert={s:sum(cells[c][0] for c in cs)/n[s] for s,cs in L.items()}
# exact queries used per run (approx budget): open arms 8, BB8 8, BB16 16, BB64 64
q={'Terra-open':8,'Opus-open':8,'Sonnet-open':8,'Haiku-open':8,'Terra-BB8':8,'Terra-BB16':16,'Terra-BB64':64,'Haiku-BB8':8,'Haiku-BB64':64}
base=dict(cost)
for p in (0,0.006,0.05):
    for s in S: cost[s]=base[s]+p*q[s]
    mem=collections.Counter(); sizes=collections.Counter(); N=0
    for f in fc:
        for b in fb:
            j={s:sum(jc(c,f,b) for c in cs)/n[s] for s,cs in L.items()}
            fr=frontier(j); N+=1; sizes[len(fr)]+=1
            for s in fr: mem[s]+=1
    print(f'gold price {p}: certified frontier {frontier(cert)}; judge frontier size dist {dict(sizes)}; membership share', {s:round(mem[s]/N,2) for s in S})
