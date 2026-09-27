# Seven-model measurement-code extraction

This audit is separate from the primary GPT-5.6 Sol semantic-candidate run. The fixed v3 prompt, system/user messages and hashes are in `experiments/crta_v3_measurement_layer_v1/harmon_prompts_v3/`. All seven raw responses, parser materializations and model/version manifests are in `experiments/crta_v3_e2_open_panel_v1/runs/`; `model_audit.csv` indexes them.

`E2_SCORE_V1.json` preserves item-level valid-code checks. `SUMMARY_V1.json` preserves the downstream materializable/complete/evaluable distinction, including failures. A parsed JSON object is not automatically an evaluable code set. The archived full table remains in this directory. The scoring script is `scripts/score_crta_v3_e2_open_panel_v1.py`; external questionnaire-key inputs must be obtained before independently rescoring against the original key.
