# ShiftHunt workshop paper (AAAI-27 Workshop on Effective and Efficient Evaluation for AI Scientists)

Anonymous submission in the official **AAAI-27 two-column author kit** (`aaai2027.sty`, `aaai2027.bst`,
TemplateVersion 2027.1, downloaded from https://aaai.org/authorkit27/ on 2026-11-11). Full papers: 6–8 pages,
references excluded; deadline 20 Nov 2026 06:00 UTC on OpenReview.

| File | Contents |
|---|---|
| `main.tex` | the paper (anonymous). `\pending{...}` marks results still being computed; `grep -n PENDING main.tex` |
| `references.bib` | bibliography; every entry checked in full text (`docs/CITATION_CHECK_1111.md`) |
| `figures_aaai/` | figures, made by `scripts/paper_figures.py` from committed public files |
| `aaai2027.sty`, `aaai2027.bst` | AAAI-27 kit files (do not edit) |
| `RELATED_WORK_NOTES.md` | related-work sweep notes (some claims superseded by the citation check) |

The Markdown source of the same text is `docs/PAPER_DRAFT_1111_v2.md`. The earlier ICLR-2027 draft (with the
October Opus 4.8 reference run and the ep321–323 note) was removed; it is in git history (before 11-11).

## Build

```bash
cd paper && latexmk -pdf main.tex && latexmk -c
```

Needs TeX Live with `texlive-fonts-extra` (the kit loads `newtxtext`). The kit forbids hyperref, float, geometry
and page-layout commands, and requires no page numbers; do not add them. Check the page count after any edit:
`pdftotext main.pdf - | grep -n '^References'` (the body must be 6–8 pages for a full paper).

Status 11-11 (after the GPU follow-up results): builds with no errors, no undefined citations and no overfull
boxes; 8 pages in total, the body about 5.6 pages (References start in the right column of page 6). Still pending
(`\pending{}`): band and gap tells, privileged vs non-privileged and brute-force solvers, and trap-seed solvability
(Table 2, §3.3). The body is still a little short of the 6-page minimum for a full paper.
