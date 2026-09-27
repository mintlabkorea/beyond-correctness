# Published outcome source inventory v1

Unit: each of the frozen 25 comparisons. This inventory selects locations by arm construction, not outcome direction. Official local source PDFs and layout text are in `../sources`; parent construction/source manifests retain their provenance. No study or design code is changed.

| Fixed IDs | Direct published outcome locations | Complete reported scope / handling |
|---|---|---|
| C01-A–D | Main Table 9 (p.8); supplement D.2.1, Tables 34–35 (printed pp.44–45) | GPT-3 classification: 4 datasets; GPT-J classification: 3; GPT-3 regression: 2 datasets × 5 fractions. Shared unnamed arm in supplement does not identify format I/II: retain C/D rows as ambiguous. Vehicle starred correct arm is explicitly shared. |
| C03-A–C | Tables 12–14; Figure 2; C03-A also healthcare Table 15 | Public 9 datasets × 10 displayed budgets; preserve missing full-data cells. Healthcare 3 tasks × 8 displayed budgets, including blank surgery 16384 and absent all-data cells. Figure 2 is an aggregate repeat. Other healthcare serializations are outside the frozen pairs. |
| C04-A–C | Tables 3–4, §4.1 | BRCA PearsonR; full vs feature-only, no KG, and 50% edges. Table 2 repeats full/no-KG results. 70%/90% edges are additional arms, outside the frozen C04-C=50% comparison. |
| C05-A–C | Appendix C.3, Figure 10 (p.21) | Regression and classification panels, all sizes 32/64/128/256/512/1024; figure-only exact values unavailable. Caption/prose kept separately from point directions. |
| C06-A | Table 18 (p.26); Table 4 (p.8) | 13 datasets × 5 shots; aggregate changes for 5 shots and Avg, with SE distinct from per-dataset SD. -Reasoning is outside the corrected frozen set. |
| C07-A | Appendix F.2, Figure 12 (pp.26–27) | Both UniPredict 16-shot and 32-shot subset panels, complete displayed shot ranges; prose's 3–5pp and 32-shot similarity are scoped author reports. |
| C08-A–F | Table 2 semantic block (p.9); Appendix A.4, Figures 9–10 (pp.27–28) | All/CARTE rank, CARTE accuracy and R2; other benchmark cells explicitly N/A. Both directions of printed win-ratio cells retained together, pairwise Wilcoxon p-values preserved at printed precision. No digitization. |
| C09-A–B | Table 4 (p.10); Appendix G.4, Figure 8 (p.52), Table 32 (p.54) | All 20 datasets (8 classification,12 regression), both aggregate tasks, classification figure. Figure uses Numerical-Full/Range/None labels: linkage retained as ambiguous presentation, no invented exact values. |
| C10-A–B | Published TMLR 08/2025 §4.3, Figure 6 (p.10) | Ridge embeddings, train sizes 32–1024, critical-difference diagram. Published indexed source confirms arms/scope, exact ranks unavailable; official PDF download remains restricted. Preacceptance mirror/supplied tarte.pdf not used for published numeric results. |

TARTE published source: https://openreview.net/pdf/7dfbc481b152839b35e7f200b528bd880a6826e2.pdf (indexed official text checked 2026-09-08). Source describes Ridge comparisons on small tables, the MinHash/random arm and removal of column names. Exact numerical ranks and pairwise significance are not supplied in the accessible text. No inference from layout order.

Table/prose repeats are recorded without treating them as independent evidence. Aggregate-only studies still receive summaries of their published aggregates; aggregate repeats of extracted per-dataset data are excluded from direction counts. Statistical tests and win ratios are retained in separate strata, not counted as extra dataset results.
