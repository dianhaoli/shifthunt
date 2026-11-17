import re,sys,subprocess
src=open(sys.argv[1]).read()
WIDE=set(sys.argv[3].split(',')) if len(sys.argv)>3 else set()
s=src.index('## Abstract'); e=src.index('## References')
title=re.search(r'^# (.*)$',src,re.M).group(1)
body=src[s:e]
def inline(x):
    x=re.sub(r':\n- ', ':\n\n- ', x); x=re.sub(r'\*\*\n1\. ', '**\n\n1. ', x)
    x=x.replace('ᵃ','QQSUPa').replace('ᵇ','QQSUPb').replace('ᶜ','QQSUPc')
    out=subprocess.run(['pandoc','-f','markdown-auto_identifiers','-t','latex','--wrap=none'],input=x,capture_output=True,text=True).stdout.strip()
    for c in 'abc': out=out.replace('QQSUP%s'%c,'\\textsuperscript{%s}'%c)
    out=out.replace('\\passthrough','')
    out=out.replace('κ','$\\kappa$').replace('τ_b','$\\tau_b$').replace('τ','$\\tau$').replace('−','$-$').replace('→','$\\rightarrow$').replace('≥','$\\geq$').replace('×','$\\times$')
    return out
blocks=re.split(r'\n\s*\n',body)
out=[]; pending_caption=None; i=0; tabn=0
while i<len(blocks):
    b=blocks[i].strip()
    if not b or b=='---': i+=1; continue
    if b.startswith('## Abstract'):
        i+=1; out.append('\\begin{abstract}\n'+inline(blocks[i].strip())+'\n\\end{abstract}'); i+=1; continue
    m=re.match(r'^(#+) (.*)',b)
    if m and '\n' not in b:
        lvl=len(m.group(1)); t=re.sub(r'^[\d.]+ ','',m.group(2))
        out.append(('\\section{' if lvl==2 else '\\subsection{')+inline(t)+'}'); i+=1; continue
    if b.startswith('**Table'):
        cap=b; i+=1
        tb=blocks[i].strip(); i+=1
        note=''
        if i<len(blocks) and blocks[i].strip()[:1] in 'ᵃᵇᶜ':
            note=blocks[i].strip(); i+=1
        rows=[r for r in tb.splitlines() if not re.match(r'^\|[-| ]+\|$',r.strip())]
        cells=[[inline(c.strip()) for c in r.strip().strip('|').split('|')] for r in rows]
        n=len(cells[0]); tabn+=1
        wide=str(tabn) in WIDE
        env='table*' if wide else 'table'
        spec='l'*n if not wide else 'l'+'l'*(n-1)
        t='\\begin{%s}[t]\n\\centering\n\\caption{%s}\n\\footnotesize\n\\begin{tabular}{%s}\n\\toprule\n'%(env,inline(re.sub(r'^\*\*Table \d+\. ','**',cap)),spec)
        t+=' & '.join(cells[0])+' \\\\\n\\midrule\n'
        for r in cells[1:]: t+=' & '.join(r)+' \\\\\n'
        t+='\\bottomrule\n\\end{tabular}\n'
        if note: t+='\n\\smallskip\n\\raggedright\\footnotesize\n'+inline(note)+'\n'
        t+='\\end{%s}'%env
        out.append(t); continue
    if b.startswith('!['):
        f=re.search(r'\((.*?)\)',b).group(1).split('/')[-1].replace('.png','.pdf')
        i+=1; cap=blocks[i].strip(); i+=1
        out.append('\\begin{figure}[t]\n\\centering\n\\includegraphics[width=\\columnwidth]{%s}\n\\caption{%s}\n\\end{figure}'%(f,inline(re.sub(r'^\*\*Figure \d+\. ','**',cap))))
        continue
    out.append(inline(b)); i+=1
keys='bowyer2025,bragg2026,chen2026,chow1970optimum,engels2025,geifman2017selective,jung2025trust,kabir2026,khalifa2026gaming,krumdick2026nofreelabels,lieberum2024,marks2025a,marks2025b,rosu2026auditorsrl,rottshaham2024maia,schwettmann2023find,sheshadri2026,starace2025,sternlicht2026oldideas,tiwari2026decodability,lu2026endtoend,zheng2023judging,zhong2026pando,zhu2025abc'
pre=r'''\documentclass[letterpaper]{article}
\usepackage[submission]{aaai2027}
\usepackage[hyphens]{url}
\usepackage{graphicx}
\urlstyle{rm}
\def\UrlFont{\rm}
\usepackage{natbib}
\usepackage{caption}
\frenchspacing
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{textcomp}
\usepackage[utf8]{inputenc}
\DeclareUnicodeCharacter{2013}{--}
\DeclareUnicodeCharacter{2014}{---}
\DeclareUnicodeCharacter{00A7}{\S}
\DeclareUnicodeCharacter{03BA}{$\kappa$}
\DeclareUnicodeCharacter{2212}{$-$}
\DeclareUnicodeCharacter{2248}{$\approx$}
\pdfinfo{
/TemplateVersion (2027.1)
}
\setcounter{secnumdepth}{2}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
'''
doc=pre+'\\title{%s}\n\\author{Anonymous submission}\n\\affiliations{}\n\\begin{document}\n\\maketitle\n'%inline(title.replace('"','``',1).replace('"',"''",1))+'\n\n'.join(out)+'\n\\nocite{'+keys+'}\n\\bibliography{references}\n\\end{document}\n'
open(sys.argv[2],'w').write(doc)
