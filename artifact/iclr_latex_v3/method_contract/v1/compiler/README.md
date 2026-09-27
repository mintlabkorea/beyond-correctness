# CRTA fixed-width compiler v1

`compile_bank.py` converts an automatically accepted bank into the only
downstream interface used by the v3 screen.

- Concept: four slots per accepted candidate (`mean`, `std`, `range`,
  `observed_fraction`).
- Relation: two slots per accepted candidate (support-normalized value and
  availability).
- Width: always `24 * 4 + 48 * 2 = 192`; unoccupied and disabled arm slots are
  zero padded.
- Fit boundary: member and cue location/scale use only the supplied reference
  mask. Target query rows never fit compiler statistics.
- Runtime absence: a documented column absent from the executable table is
  retained as missing. The candidate is not silently removed.
- Task leakage: `forbidden_column_ids` disables every concept or relation that
  touches the cell's prediction target.

`runtime_schema_maps.json` is an execution-name registry, not a semantic
candidate registry. For example, the N-CMAPSS documentation name `s_t24`
resolves to the retained tiny-table column `T24`. A `null` entry records that a
documented channel is not present in the frozen downstream table.
