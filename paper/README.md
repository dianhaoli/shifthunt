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

Status 11-11: builds with no errors, no undefined citations, no overfull boxes; 7 pages in total, of which the
body is about 5.3 pages. The body is short of the 6-page minimum until the pending results (Tables 2–3, §3.3, §4.2)
are filled in.
