import re
d='/tmp/claude-0/-home-user-shifthunt/31197046-e7fc-5377-820d-5f00261e8f4e/scratchpad/paperloop/d4/'
s=open(d+'r3parts/body.md').read()
ab=open(d+'r3parts/appAB.md').read(); ch=open(d+'r3parts/appCH.md').read()
out=s.rstrip()+'\n\n---\n\n'+ab.rstrip()+'\n'+ch
i=out.index('## References'); refs=out[i:]; out=out[:i].rstrip().rstrip('-').rstrip()+'\n'
out=out.replace('\n---\n\n# Appendix','\n---\n\n'+refs.strip()+'\n\n---\n\n# Appendix',1)
open(d+'draft_r3.md','w').write(out)
b=out[:out.index('## References')]
abst=b[b.index('## Abstract')+11:b.index('## 1 Introduction')]
toks=[t for t in re.findall(r"\S+",b) if t not in ('|','---','|---','>')]
nb='\n'.join(l for l in b.split('\n') if not l.startswith('|') and not l.startswith('>'))
print('body no-pipes',len(toks),'prose',len(re.findall(r"\S+",nb)),'abstract',len(re.findall(r"\S+",abst.replace('---',''))))
