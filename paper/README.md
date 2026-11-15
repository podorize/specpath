# MSR 2027 Mining Challenge manuscript

The official source is `main.tex`, with
`references.bib`. It uses the IEEE conference
class, anonymous authorship, a 90-case human Gold, and a 382-reference
probability sample. The editable figure is
`figures/decision_flow_compact.svg`.

The [official challenge call](https://2027.msrconf.org/track/msr-2027-mining-challenge)
requires at most four content pages plus one page of references, IEEE
formatting, double-anonymous review, and a separate ethical implications
section. The source follows these structural requirements. Check the rendered
PDF in the final submission environment for page count and figure legibility.

Build from this directory in a standard TeX environment:

    latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

Check the resulting PDF for page count, overfull lines, legible tables,
bibliography placement, author anonymity, and metadata. The review package is available through https://anonymous.4open.science/r/specpath-msr2027-review-artifact-5668/

