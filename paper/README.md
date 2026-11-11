# MSR 2027 Mining Challenge manuscript

The active source is [main.tex](main.tex). It uses the IEEE conference class,
anonymous authorship, one research question, the frozen pre-reconsideration human Gold,
and the 382-case probability-sample results, including exploratory analyses
of class composition and task-status contrasts. The manuscript contains the
print-ready decision tree; its editable source is in the figure directory.

The [official challenge call](https://2027.msrconf.org/track/msr-2027-mining-challenge)
requires at most **four content pages plus one page of references**, IEEE
formatting, double-anonymous review, and a separate ethical implications
section. The source follows these structural requirements. A local Tectonic
build produced a three-page PDF with a full-width tree; all pages were rendered
and visually checked.
Final compilation in the submission environment remains advisable because
font substitution can differ across TeX installations.

The official call lists an abstract deadline of December 18, 2026 and a paper
deadline of December 23, 2026 (AoE). These are conference deadlines; the
advisor-review handoff can happen earlier.

Build in a standard TeX environment from the paper directory:

    latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

Check the resulting PDF for page count, overfull lines, legible table,
bibliography placement, author anonymity, and metadata. The local preview is
at `../output/pdf/specpath_msr2027_anonymous.pdf`. The manuscript's
artifact link is deliberately pending until an anonymous release is prepared.
