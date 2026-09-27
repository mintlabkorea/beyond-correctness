# Frozen semantic-construction contract

The primary executed run is `iclr_latex_v3/method_contract/v1/runs/proposer_bank_v2/models/gpt-5.6-sol/medical_nhanes_knhanes_full_documents_v2_attempt_02/`. The earlier attempt returned no response; it is not the experimental candidate bank. The successful attempt records GPT-5.6 Sol, Codex CLI 0.144.5, reasoning effort high, and flattened system-then-user transport.

Original components, input/output schemas, DSL, fixed candidate budgets, acceptance rules and validator are under `iclr_latex_v3/method_contract/v1/`. `decision_ledger.json` contains **accepted_bank**, every recorded candidate decision, abstentions and rejection reasons. `raw_response.txt` and `raw_candidate_bank.json` preserve the executed response. No candidate was regenerated.

`executed_system.txt`, `executed_user.txt` and `executed_cli_input.txt` are exact field projections of the existing stored prompt, using the recorded transport's `system + two newlines + user` concatenation. They are marked as packaging projections, not newly recovered historical files. Their hashes are checked against the executed manifest in `executed_component_hash_check.json`.

The separately stored current template/schema/validator can differ from earlier frozen bytes; consult the hash audit. Greedy/temperature=0/seed=0 are **stored configuration**, not explicit options in the CLI invocation. No deterministic regeneration claim is made. The target is the stored executed run.

`input_boundary_audit.json` records the inspection boundary. No observed person values, predictions, target-label vectors or performance results were found in the selected inputs. Clinical code meanings and leakage-role declarations remain because they are the scientific schema contract.
