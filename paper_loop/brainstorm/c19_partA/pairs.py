exec(open('analyse_bounds.py').read().split("for name,L in")[0])
L=L9; S=list(L); n={s:sum(sum(cells[c]) for c in cs) for s,cs in L.items()}
pairs=[('Haiku-open','Terra-BB64'),('Terra-BB16','Terra-BB64'),('Opus-open','Terra-BB64'),('Opus-open','Terra-open'),('Terra-open','Terra-BB64'),('Haiku-BB64','Terra-BB64'),('Terra-BB8','Terra-BB64')]
mn={p:9 for p in pairs}; mx={p:-9 for p in pairs}
tb=[]
for f in fc:
    for b in fb:
        j={s:sum(jc(c,f,b) for c in cs)/n[s] for s,cs in L.items()}
        for p in pairs:
            d=j[p[0]]-j[p[1]]; mn[p]=min(mn[p],d); mx[p]=max(mx[p],d)
        t={a:jc(('block1','gpt',a),f,b) for a in ('open8','bb8','bb64')}
        tb.append(((t['bb64']-t['bb8'])/24,(t['open8']-t['bb8'])/24,(t['bb64']-t['open8'])/24, 21/24-t['bb64']/24))
for p in pairs: print(p, 'judge diff range', round(mn[p],3), round(mx[p],3))
for i,lab in enumerate(['Terra budget BB64-BB8 (cert +0.667)','Terra proxy O8-BB8 (cert +0.625)','Terra BB64-O8 (cert +0.042)','Terra BB16-BB64 (cert -0.25)']):
    print(lab, round(min(x[i] for x in tb),3), round(max(x[i] for x in tb),3), 'share of splits with budget effect < +0.333' if i==0 else '', round(sum(x[0]<1/3 for x in tb)/len(tb),2) if i==0 else '')
