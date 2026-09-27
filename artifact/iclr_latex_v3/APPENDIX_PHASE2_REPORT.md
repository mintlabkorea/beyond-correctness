# Appendix Phase 2 report

Phase 2 used the post-Phase-1 `main.tex` and `appendix.tex` snapshots as its baseline. The only manuscript sources changed were the opening of Appendix A, the two required local TabLLM pointers, and the single noisy-proxy appendix pointer in `main.tex`.

## Before/after ordering of Appendix A

| Before Phase 2 | After Phase 2 |
| --- | --- |
| 1. Navigation table | 1. Navigation table |
| 2. Interpretive labels | 2. Interpretive labels |
| 3. Three distinct comparisons | 3. Three distinct comparisons |
| 4. Full reference-admissibility discussion | 4. Short reference-admissibility pointer |
| 5. Reference-construction provenance | 5. `Reference checks across interventions` subsection |
| 6. Analysis provenance | 6. `Common scoring, experimental, and inference details` subsection |
| 7. `Common scoring, experimental, and inference details` subsection | 7. `Provenance summary` subsection, including reference-construction timing, analysis timing, and `tab:app-analysis-registry` |
| 8. `Provenance summary`, containing `tab:app-analysis-registry`, followed by `tab:app-reference-portability` | — |

The new subsection is:

```tex
\subsection{Reference checks across interventions}
\label{sec:app-reference-checks}
```

`tab:app-reference-portability` moved intact from after the provenance registry into this subsection. A byte-for-byte table-environment comparison, including its caption and body, passed. `tab:app-analysis-registry` remains unchanged inside `Provenance summary`.

## Exact prose deleted, moved, and added

### Reference-admissibility prose deleted

The following method repetition was deleted:

```tex
For each predictive-utility claim, we specify the tested use that may change
and the information and predictive setup that must be preserved.
A candidate reference is admissible only if it passes the same three checks
defined in the main paper: Removal, Preservation, and Interface validity.
Allowing additional components to change may define a broader comparison, but
does not identify the original component-specific utility.

If these requirements cannot be satisfied simultaneously, predictive utility is reported as not separately evaluable for that intervention.
Retaining the tested input while randomizing its semantic assignment defines a wrong condition rather than a reference.
```

The following full-space explanation was replaced by the shorter required scope statement:

```tex
Admissibility need not determine a unique reference, so the admissible reference space may contain multiple admissible references.
Where several are evaluated, their variation is summarized as a range over the evaluated references and not as a bound over the full admissible reference space (Section~\ref{sec:app-tabllm-reference-audit}).
```

The following post-table prose was deleted. Its second sentence was replaced by the two narrower self-application statements shown below:

```tex
The same abstract checks therefore apply across measurement, correspondence, and relation interventions, while the editable component and protected complement depend on the claim being evaluated.
Notably, the survey no-added-columns comparison fails Preservation and is retained only as an ablation, while the controlled correct-versus-deranged correspondence comparison retains a binding and therefore supports content sensitivity rather than predictive utility.
```

### Provenance prose moved

The timing sentence formerly inside `Reference admissibility` moved under `Provenance summary`:

```tex
When a new reference is constructed after earlier results are known, its timing is reported explicitly and the construction is fixed before the new comparison is executed; alternative references are not selected using the outcomes of that comparison.
```

The following reference-construction and analysis-provenance prose moved under `Provenance summary` without textual changes:

```tex
\paragraph{Reference-construction provenance.}
For every \emph{not separately evaluable} verdict and every later reference extension, the supplementary artifact records the candidate construction, its timing relative to outcome inspection, and the admissibility criterion that prevented or permitted the comparison.
A later admissible construction does not retroactively replace the original design-level verdict.
For example, the width-matched examination reference was constructed after the original comparison and is therefore reported as a post-result reference extension.

For retrospective contracts, the artifact records a requirement-level crosswalk from each contract element to the corresponding frozen design constraint where such a constraint already existed.
Requirements without such support are explicitly labeled post-result diagnostics and do not retroactively change reference membership or primary-reference selection.
For TabLLM, the editable label region and preservation of the List Template structure, field order, value formatting, and stable-anonymous mapping are reconstructed from the frozen reference protocols, whereas the additional-truncation diagnostic is post-result.
The generic-lexical vocabulary (\texttt{Feature one}, \ldots, \texttt{Feature twenty}) and canonical line mapping were fixed before scoring and are included verbatim in the artifact for exact membership checking.

\paragraph{Analysis provenance.}
\emph{Confirmatory} analyses were fixed before the corresponding outcome comparison. \emph{Frozen-before-execution} extensions were specified after an earlier analysis but before the new experiment; \emph{exploratory existing-cell}, \emph{post-hoc}, \emph{post-result}, and \emph{retrospective external} labels state later timing directly. Optional analyses that were not executed are marked \emph{not run}.

There was no external public registration or independently verifiable external pre-execution timestamp for these analyses.
Local manifests, hashes, retained run artifacts, and pre-execution decision records document internal freezing where available, but are not equivalent to externally verifiable preregistration or timestamping.
Consequential provenance statuses are stated locally where they affect interpretation.
```

In the new location, the moved timing sentence appears immediately after the `Reference-construction provenance` heading. No provenance status or registry-table text changed.

### Prose added

The compressed admissibility pointer is:

```tex
Appendix reference admissibility follows the Removal, Preservation, and Interface validity checks defined in the main paper.
When multiple references are evaluated, the reported range covers only the evaluated references, not the full admissible space.
```

The portability table now has this explicit introduction:

```tex
Table~\ref{tab:app-reference-portability} applies the reference checks across semantic interventions.
```

The two retained self-application results now read:

```tex
The survey no-added-columns comparison fails Preservation and is retained only as an ablation rather than correspondence predictive utility.
The controlled correspondence derangement retains the tested binding and therefore supports content sensitivity but not separately evaluable predictive utility.
```

The TabLLM reference-audit prose gained these local pointers:

```tex
Table~\ref{tab:app-tabllm-reference-gates} applies the three reference checks to the candidate constructions and diagnostics.
```

```tex
Table~\ref{tab:app-tabllm-generic-lexical} reports this lexical-reference sensitivity.
```

No TabLLM result prose, number, or table content changed.

## Navigation rows added or altered

Four rows were added exactly as follows:

```tex
Reference checks across interventions & Section~\ref{sec:app-reference-checks} & Table~\ref{tab:app-reference-portability} \\
TabLLM reference admissibility audit & Section~\ref{sec:app-tabllm-reference-audit} & Table~\ref{tab:app-tabllm-reference-gates} \\
Generic-lexical reference sensitivity & Section~\ref{sec:app-tabllm-reference-audit} & Table~\ref{tab:app-tabllm-generic-lexical} \\
Fixed-width noisy-proxy diagnostic & Section~\ref{sec:app-noisy-proxy} & Tables~\ref{tab:app-noisy-proxy-dose} and~\ref{tab:app-noisy-proxy-within-dose} \\
```

The broad reconstructibility row previously read:

```tex
Controlled and real-data reconstructibility &
Sections~\ref{sec:app-reconstructibility-proxy} and~\ref{sec:app-relation-real-data} &
Tables~\ref{tab:app-reconstructibility-controlled-compact},
\ref{tab:app-noisy-proxy-dose},
\ref{tab:app-noisy-proxy-within-dose}, and~\ref{tab:app-reconstructibility-real} \\
```

It now retains the controlled and real-data boundary entries while the noisy-proxy tables have their own row:

```tex
Controlled and real-data reconstructibility &
Sections~\ref{sec:app-reconstructibility-proxy} and~\ref{sec:app-relation-real-data} &
Tables~\ref{tab:app-reconstructibility-controlled-compact} and~\ref{tab:app-reconstructibility-real} \\
Fixed-width noisy-proxy diagnostic & Section~\ref{sec:app-noisy-proxy} & Tables~\ref{tab:app-noisy-proxy-dose} and~\ref{tab:app-noisy-proxy-within-dose} \\
```

All other useful navigation rows remain.

## Every changed reference

### `main.tex`

Exactly one line changed. Before:

```tex
Eligible real-data probes do not establish the same relationship, so we treat reconstructibility as controlled diagnostic evidence rather than a general predictor of utility (Supplementary Sections~\ref{sec:app-reconstructibility-proxy} and~\ref{sec:app-relation-real-data}).
```

After:

```tex
Eligible real-data probes do not establish the same relationship, so we treat reconstructibility as controlled diagnostic evidence rather than a general predictor of utility (Supplementary Sections~\ref{sec:app-noisy-proxy} and~\ref{sec:app-relation-real-data}).
```

No other byte in `main.tex` changed.

### `appendix.tex`

| Reference change | Current location |
| --- | --- |
| Added navigation `\ref{sec:app-reference-checks}` | line 66 |
| Added navigation `\ref{tab:app-reference-portability}` | line 66 |
| Added navigation `\ref{tab:app-tabllm-reference-gates}` | line 68 |
| Added navigation `\ref{tab:app-tabllm-generic-lexical}` | line 69 |
| Added navigation `\ref{sec:app-noisy-proxy}` | line 80 |
| Moved the existing `\ref{tab:app-noisy-proxy-dose}` and `\ref{tab:app-noisy-proxy-within-dose}` from the broad reconstructibility row to the new fixed-width row | line 80 |
| Added local `\ref{tab:app-reference-portability}` | line 124 |
| Added local `\ref{tab:app-tabllm-reference-gates}` | line 559 |
| Added local `\ref{tab:app-tabllm-generic-lexical}` | line 626 |
| Removed the former parenthetical `\ref{sec:app-tabllm-reference-audit}` from the compressed admissibility discussion | former line 129 |

The two new TabLLM navigation rows add two `sec:app-tabllm-reference-audit` references; removal of the old parenthetical produces a net count change from two to three references to that subsection. No existing result pointer was redirected.

## Static validation

- Labels: 94.
- Reference calls: 87.
- Duplicate label definitions: 0.
- Undefined reference targets across `main.tex` and `appendix.tex`: 0.
- Appendix floats: 50, consisting of the same ordered sequence of 43 tables and 7 figures as the Phase-1 baseline.
- Numeric tokens: unchanged in identity and multiplicity. `main.tex` contains the same 217 numeric tokens; `appendix.tex` contains the same 2,338 numeric tokens. Reordering the unchanged portability table changes token position, so validation compared the full token multisets.
- `tab:app-reference-portability` and `tab:app-analysis-registry`: table environments byte-for-byte unchanged.
- The complete `Cross-component interaction and model coverage` section: byte-for-byte unchanged.

Explicit incoming references after Phase 2:

| Destination | Incoming references |
| --- | --- |
| `tab:app-reference-portability` | appendix.tex:66, appendix.tex:124 |
| `tab:app-tabllm-reference-gates` | appendix.tex:68, appendix.tex:559 |
| `tab:app-tabllm-generic-lexical` | appendix.tex:69, appendix.tex:626 |
| `sec:app-noisy-proxy` | main.tex:446, appendix.tex:80 |

## Compilation status and warnings

Both builds used clean staged copies of the final sources under `.runtime`. The existing figures and conference-style directory were made available read-only through temporary symlinks. No pre-existing manuscript auxiliary files were copied into the staging area.

### Standalone appendix

- Command: `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=.runtime appendix.tex`
- Status: success, exit code 0.
- Output: 33 pages.
- Undefined references: 0.
- Undefined citations: 0.

Final-pass warnings:

```text
Underfull \hbox (badness 1968) in paragraph at lines 29--29
Overfull \hbox (9.26pt too wide) in paragraph at lines 446--466
Underfull \hbox (badness 1661) in paragraph at lines 844--844
Underfull \hbox (badness 2334) in paragraph at lines 1272--1274
```

Full log: `.runtime`.

### Integrated manuscript

- Wrapper: `\def\ICLRIncludeAppendix{1}` followed by `\input{main.tex}`.
- Command: `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=.runtime phase2_integrated.tex`
- Status: success, exit code 0.
- Output: 44 pages.
- Undefined references: 0.
- Undefined citations: 0.

Final-pass warnings:

```text
Underfull \hbox (badness 1968) in paragraph at lines 45--45
Overfull \hbox (2.83388pt too wide) in paragraph at lines 184--184
Underfull \vbox (badness 2846) has occurred while \output is active []
Underfull \hbox (badness 3229) in paragraph at lines 298--300
Underfull \vbox (badness 1472) has occurred while \output is active []
Overfull \hbox (9.26pt too wide) in paragraph at lines 446--466
Underfull \hbox (badness 1661) in paragraph at lines 844--844
Underfull \hbox (badness 2334) in paragraph at lines 1272--1274
```

Full log: `.runtime`.

No layout edits were made to suppress box warnings. Phase 2 is complete; no later-phase work was performed.
