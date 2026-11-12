import re,sys
for f in sys.argv[1:]:
    s=open(f).read().split('\n## References')[0]
    toks=[t for t in s.split() if re.search(r'[A-Za-z0-9]',t)]
    s2=s.split('## Abstract')[1]; 
    t2=[t for t in s2.split() if re.search(r'[A-Za-z0-9]',t)]
    noimg=[t for t in t2 if not t.startswith('![')]
    print(f.split('/')[-1],'all',len(toks),'abstract->end',len(t2))
