# TabLLM retrospective three-arm audit, v1

Frozen 2026-08-27 before the new reproduction is run.  This is an external
retrospective methods demonstration on a published knowledge-augmented tabular
learner, not a cross-schema validation and not a claim that the original
authors' aggregate result was wrong.

## Cells and arms

Reproduce the original TabLLM zero-shot T0 classification evaluation on all
nine published datasets and the original fixed train/test assets and prompt
contract.  Four arms are required:

1. `list_template` (S): original List Template with correct feature names;
2. `list_permuted_names` (W): original List Permuted Names arm;
3. `list_only_values` (R_pub): original List Only Values arm;
4. `list_stable_anonymous` (R_anon): the List Template serialization with the
   same punctuation, field order and value formatting as S, but feature names
   replaced by deterministic within-dataset identifiers `feature_001`, ... .

The stable anonymous arm is the primary format-matched reference.  R_pub is
retained to reproduce the published three arms and diagnose serialization
format sensitivity.  The name permutation is fixed per dataset and matches the
published implementation.  No dataset is selected or dropped after outputs
are observed.

## Fixed estimands and summaries

The original paper's metric, AUROC (macro one-versus-rest for multiclass), is
primary.  Accuracy is descriptive only.  Use the released TabLLM-vendored
T-Few execution code, the implementation-pinned `bigscience/T0` 11B backbone,
and the upstream T-Few checkpoint
`pretrained_checkpoints/t011b_ia3_finish.pt` and the original class
verbalizers: each class score is the
conditional probability of its verbalizer token sequence, normalized across
classes, rather than a greedy generated-label proxy.  For reference R in
{R_anon, R_pub}:

- content = Q(S) - Q(W);
- utility = Q(S) - Q(R);
- matched-wrong harm = Q(R) - Q(W);
- identity check = content - utility - harm.

Run the five original split seeds in their published order
`42, 1024, 0, 1, 32`; zero-shot has no task-specific fitting, but the held-out
20% split changes with this seed.  The unweighted macro mean over all nine
datasets after averaging the five split-seed AUROCs within dataset is the
primary panel summary.
Prespecified secondary summaries are the full per-dataset table, median and
range of harm share `harm/content` when content is positive, counts of
utility-dominant and harm-dominant cells, and the count/list of utility sign
reversals.  Credit-g and Jungle are illustrative only.

Save one record per test example containing dataset, stable example ID, gold
label, predicted label, every normalized class/verbalizer score, arm and prompt
hash.  Paired example bootstrap within dataset uses 10,000 draws and fixed seed
20260827; the macro interval resamples datasets and then examples.  Deterministic
zero-shot scoring has no pseudo-replication over random seeds.

## Provenance and failure policy

Record the TabLLM and upstream T-Few repository commits, data hashes,
prompt/template hashes, base-model snapshot revision, IA3 checkpoint hash,
tokenizer revision, package versions, scoring arguments and hardware.  The
paper text names `bigscience/T0pp` once, whereas the released 11B execution
config and T-Few checkpoint use `bigscience/T0`; the audit follows the released
execution config and discloses this source discrepancy.  If an exact asset is
unavailable, stop and report that fact; do not silently substitute a model or
dataset.  Any compatibility repair is documented before the first full-grid
output is opened.
