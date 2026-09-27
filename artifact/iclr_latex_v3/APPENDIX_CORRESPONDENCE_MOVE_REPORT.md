# Appendix Correspondence Move Report

## Scope

This phase made one structural edit in `appendix.tex`: it moved the complete correspondence-construction audit, renamed the subsection, introduced its section label, and added the requested navigation row. `main.tex` is byte-identical to its pre-edit snapshot. No empirical text, numerical result, table body, figure, caption, citation, criterion, interpretation, provenance designation, or artifact file was changed.

## Old and new source locations

- **Old location:** pre-edit `appendix.tex` lines 994--1031, at the end of `\section{Correspondence knowledge}`, after `\subsection{Target-support dependence}` and before `\section{Relation knowledge}`.
- **New location:** post-edit `appendix.tex` lines 1630--1668, inside `\section{Construction and reproducibility}`, after `\subsection{Documentation-only construction}` and before `\subsection{Numerical environment and access boundaries}`.
- The old title `\subsection{Matching quality and abstention}` was replaced by `\subsection{Open-world correspondence construction audit}`.
- The new subsection label is `\label{sec:app-correspondence-construction-audit}`.

The exact pre-edit moved range, lines 994--1031 inclusive, contained:

1. the subsection heading;
2. all open-world matching and abstention prose;
3. the complete table carrying `tab:app-correspondence-decoy-matcher`;
4. the forced plausible-neighbour performance-loss prose;
5. the complete figure carrying `fig:app-correspondence-decoy-damage`; and
6. the subsection's closing `\FloatBarrier`.

The prose and both floats remain complete in the new location. The first two sentences still state that the open-world audit expands the construction task and evaluates correspondence construction rather than predictive utility.

After removal, `\section{Correspondence knowledge}` now ends with the target-support subsection's scope and diagnostic prose, its clean-rerun statement, and its existing `\FloatBarrier`. No replacement prose was added.

## New section order

The final order within `\section{Construction and reproducibility}` is:

1. `\subsection{Documentation-only construction}`
2. `\subsection{Open-world correspondence construction audit}`
3. `\subsection{Numerical environment and access boundaries}`

The moved subsection remains separate from `\paragraph{Transfer abstention versus component references}`.

## Navigation change

One row was added to the Appendix A navigation table at post-edit line 68:

```tex
Open-world correspondence construction audit & Section~\ref{sec:app-correspondence-construction-audit} & Table~\ref{tab:app-correspondence-decoy-matcher} \\
```

No other navigation row was changed. The new subsection label has exactly one incoming reference, from this row.

## Integrity validation

- The moved table is byte-identical to its pre-move form:
  - pre/post SHA-256: `8dd44ca8380ed923fc20a0f44430de6dd5c0a03156452874ba362d4abcf8604f`
- The moved figure environment is byte-identical to its pre-move form:
  - pre/post SHA-256: `2657bb7211b9b840c7e0eb018ec07f16f04994772bf9f2d1c761072091a26fb2`
- Numerical-token multiplicities are unchanged: 2,308 tokens before and after under the same validator.
- Appendix float count is unchanged: 47 total, comprising 41 tables and 6 figures.
- The old subsection title occurs zero times.
- Label comparison found only the requested addition `sec:app-correspondence-construction-audit`; no label was removed or otherwise changed.
- The combined static audit finds 91 unique labels, 89 reference commands, zero duplicate labels, and zero undefined references across `main.tex` and `appendix.tex`.
- Citation commands and keys were not edited.

## Compilation

Both clean builds completed successfully with `latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error`.

- Standalone appendix: success, 32 pages.
- Integrated manuscript with appendix: success, 43 pages.
- Undefined references: 0 in both final logs.
- Undefined citations: 0 in both final logs.
- Package or rerun warnings: 0 in both final logs.

The final logs contain the following box-layout warnings.

### Standalone appendix

- Underfull `\\hbox` (badness 1968), line 29.
- Overfull `\\hbox` (9.26 pt), lines 449--469.
- Underfull `\\hbox` (badness 1661), line 847.
- Underfull `\\hbox` (badness 2334), lines 1237--1239.

### Integrated manuscript

- Underfull `\\hbox` (badness 1968), line 45.
- Overfull `\\hbox` (2.83388 pt), line 184.
- Underfull `\\vbox` (badness 2846).
- Underfull `\\hbox` (badness 3229), lines 298--300.
- Underfull `\\vbox` (badness 1472).
- The four appendix-originating box warnings listed for the standalone build recur in the integrated build.
