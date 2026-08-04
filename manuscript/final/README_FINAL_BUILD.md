# Final LaTeX build

## Source manuscript
- `manuscript/full_manuscript_v2_clean.md`
- `manuscript/abstract_v2.md`
- `manuscript/references_verified_v2.md`
- `manuscript/declarations_v2.md`
- `manuscript/figures/figure_captions_v2.md`
- `manuscript/tables_v2/`

## Generated files
- `Foziljon_Alisherov_Remittances_Shocks_Reader.tex`
- `Foziljon_Alisherov_Remittances_Shocks_Submission.tex`
- `references_final.bib`
- `appendix_final.tex`

## MiKTeX version / detection
latexmk=D:\apps\mitex\miktex\bin\x64\latexmk.EXE; pdflatex=D:\apps\mitex\miktex\bin\x64\pdflatex.EXE; biber=D:\apps\mitex\miktex\bin\x64\biber.EXE

## Tool versions
pdflatex: MiKTeX-pdfTeX 4.27 (MiKTeX 26.5) (D:\apps\mitex\miktex\bin\x64\pdflatex.EXE)
biber: biber version: 2.21 (D:\apps\mitex\miktex\bin\x64\biber.EXE)
latexmk:  (D:\apps\mitex\miktex\bin\x64\latexmk.EXE)

## Compilation command
Preferred: `latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error <file>.tex`

Fallback: `pdflatex`, `biber`, `pdflatex`, `pdflatex`.

## Required packages
geometry, setspace, lineno, amsmath, amssymb, booktabs, threeparttable, threeparttablex, longtable, tabularx, array, graphicx, caption, subcaption, float, placeins, microtype, xcolor, hyperref, url, csquotes, biblatex, enumitem, titlesec, fancyhdr, lastpage.

## Reference backend
BibLaTeX with biber.

## Figure sources
Approved figure sources are taken from `manuscript/final_figure_plan.csv`.

## Declarations
Final declaration statements are included in the manuscript. No title-page declaration placeholders remain.

## Target-journal status
Not yet selected.

## Reproduction instructions
Run `python src/run_phase_09_latex_package.py` from the project root after MiKTeX commands are available on PATH.
