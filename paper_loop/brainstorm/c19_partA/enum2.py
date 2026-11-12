import pickle, time
exec(open('bounds.py').read().split("keys=list(cells)")[0])
order=[('bb16','gpt','bb16'),('main','opus','open'),('hv','opus','open'),('main','sonnet','open'),('hv','sonnet','open'),
 ('hv','gpt','open'),('hv','haiku','open'),('main','gpt','open'),('main','haiku','open'),
 ('block1','gpt','open8'),('block1','haiku','open8'),('block1','gpt','bb64'),('block1','haiku','bb64'),('block1','gpt','bb8'),('block1','haiku','bb8')]
keys=order
def enum(tot, cap):
    cons=[]
    for dim,idx in (('pop',0),('agent',1),('access',2)):
        for v,t in tot[dim].items(): cons.append(([i for i,k in enumerate(keys) if k[idx]==v],t))
    caps=[cap(k) for k in keys]; sols=[]; cur=[]
    def ok(i):
        for members,t in cons:
            s=sum(cur[m] for m in members if m<=i); rem=sum(caps[m] for m in members if m>i)
            if s>t or s+rem<t: return False
        return True
    def rec(i):
        if i==len(keys): sols.append(tuple(cur)); return
        for x in range(caps[i]+1):
            cur.append(x)
            if ok(i): rec(i+1)
            cur.pop()
    rec(0); return sols
t=time.time()
FC={'agent':{'gpt':18,'haiku':24,'opus':6,'sonnet':5},'access':{'open':21,'open8':7,'bb8':16,'bb64':4,'bb16':5},'pop':{'main':16,'hv':5,'block1':27,'bb16':5}}
FB={'agent':{'gpt':21,'haiku':7,'opus':1,'sonnet':3},'access':{'open':6,'open8':5,'bb8':7,'bb64':12,'bb16':2},'pop':{'main':5,'hv':1,'block1':24,'bb16':2}}
fc=enum(FC, lambda k: cells[k][1]); print('FC',len(fc),round(time.time()-t,1),flush=True)
fb=enum(FB, lambda k: cells[k][0]); print('FB',len(fb),round(time.time()-t,1),flush=True)
pickle.dump((keys,cells,fc,fb),open('sols.pkl','wb'))
