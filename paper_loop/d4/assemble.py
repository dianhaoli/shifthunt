import re
P='parts/'
p4=open(P+'p4_appendix_tail.md').read()
prompt=open('../d1/rendered_prompt_open.md').read().rstrip('\n')
appA=("\n---\n\n# Appendix\n\n## Appendix A. Full task prompt (open access, templated substrate, 8 exact queries)\n\n"
      "This is `prompt.md` rendered with the episode's parameters and the tool server's help text (9,459 characters). "
      "Free-text (two-part) episodes make two additions. One sentence is appended to the paragraph that defines dependence: "
      "\"A few of the note generator's properties can only occur together with another of its properties, so such a pair does not vary "
      "independently; every other statement in this text that properties vary independently or are coin flips holds as written.\" "
      "They also append the hint section described in Appendix B.\n\n"
      "````text\n"+prompt+"\n````\n")
body=open(P+'p1_body.md').read()+open(P+'p2_findings.md').read()+open(P+'p3_rest.md').read()
full=body+appA+p4
open('draft_r1.md','w').write(full)
b=body.split('## References')[0]
def wc(t): return len(re.findall(r"\S+",t))
print('abstract', wc(b.split('## Abstract')[1].split('## 1 Introduction')[0].replace('---','')))
print('body', wc(b), 'tables', sum(wc(l) for l in b.split('\n') if l.startswith('|')))
print('total', wc(full))
