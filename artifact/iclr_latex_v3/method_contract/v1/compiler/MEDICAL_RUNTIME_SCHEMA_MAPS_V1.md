# M4--M6 medical runtime schema maps v1

These manifests bind the frozen documentation payload column IDs to the existing runtime schemas.
They were produced from payload JSON, code/mapping metadata, file hashes, and Parquet footer schemas
only. No participant values, labels, predictions, or split memberships were opened.

| Task | Binding result | Current state |
|---|---|---|
| M4 HRS -> KLoSA | 38 HRS `hrs__* -> slot__*` aliases; 7 absent HRS fields plus `wave`; 42 target-native fields use the frozen wave-stacked sidecar | target ready; HRS authorization blocked |
| M5 HRS -> ELSA | 16 HRS aliases and 7 absent HRS fields; 9 safe target aliases; 5 raw-retention requirements | licensed-user-local prep and HRS authorization blocked |
| M6 HRS -> CHARLS | 16 HRS aliases and 7 absent HRS fields; all 7 target aliases are safe | target ready; HRS authorization blocked |

The exact frozen HRS source object is:

`data/benchmark/external_onboarding/hrs_v0/artifacts/hrs_function_cognition_strength_views_v1_1/hrs_function_cognition_strength_latest_snapshot_v1_1.parquet`

Its required SHA-256 is
`3033edb03b11beeb4848e48673d02337406b67cdae962391a59f39c05c17d18f`.
The similarly named HRS SSL wide table has a different hash and is not an in-place substitute.

## M4 target-side requirement

The following requirement has now been met by the private sidecar recorded in the additive target
binding; the original blocked runtime-map JSON remains immutable audit provenance. The frozen
KLoSA prepared table contains canonical `hrs__*` fields, not the payload's 42 native
`klosa__ww*` fields. A static `klosa__ww* -> w09*` alias would cover only wave 9 and is invalid for
the frozen longitudinal protocol. Build a hash-bound sidecar by stacking `str01.parquet` through
`str09.parquet`, renaming each wave-specific native field to its generic payload ID, and joining
one-to-one on `(subject_id, wave)`. `klosa__wwcadd_19` is structurally unavailable in waves 1--6;
the sidecar must materialize it as missing there. The manifest records every raw template, wave
hash, missing code, and the wave-1 `w01Alc` capitalization override.

## M5 unsafe target bindings

The v1 ELSA preparation drops all raw `elsa__*` fields after producing canonical `hrs__*` values.
Nine target aliases are identity-safe. The following five are intentionally mapped to `null`:

- `elsa__chol`: v1 multiplies by 38.67 into `hrs__total_cholesterol`;
- `elsa__fglu`: v1 multiplies by 18.0182 into `hrs__glucose`;
- `elsa__hba1c`: v1 applies a wave-dependent IFCC-to-NGSP transform at wave 6;
- `elsa__hdl`: v1 multiplies by 38.67 into `hrs__hdl`;
- `elsa__rwdrinkwn_e`: v1 divides weekly drinks by drinking days into a per-day quantity.

`scripts/prepare_elsa_external_v2.py` authors that additive preparation contract. It retains
all 14 exact `elsa__*` payload fields (including the five unsafe-to-alias fields) alongside the v1
canonical columns. It has not been run by the online agent. A licensed user-local execution must freeze
the new private table and key hashes before a new executable runtime-map version is issued.
Mapping the existing converted/derived columns to the five blocked IDs remains prohibited.

## Authored private preparation paths

The preparation code defaults to task-specific private locations outside the repository and
refuses to overwrite an existing table or manifest:

- M4: `scripts/prepare_crta_v3_m4_klosa_native_sidecar_v1.py` ->
  `data/private/crta_v3/m4_klosa_native_sidecar_v1/`;
- M5: `scripts/prepare_elsa_external_v2.py` ->
  `data/private/crta_v3/elsa_v2/`;
- M6: `scripts/prepare_charls_external_v2.py` ->
  `data/private/crta_v3/charls_v2/`.

M4 opens only the KLoSA target table and its nine native wave tables; it never opens HRS. M5
requires `--i-confirm-local-licensed-execution`. M4 requires
`--i-confirm-private-local-execution`. M6 also requires explicit local confirmation. M5 and M6
create new v2 subject-hash keys and never claim to reproduce the missing v1 partitions. M6 keeps
the seven identity-safe `charls__*` payload aliases alongside the canonical `hrs__*` columns.

Repository tests use only synthetic fixtures. The private local preparation has now completed for
KLoSA and CHARLS, without opening HRS: KLoSA produced 69,272 rows / 11,174 subjects and CHARLS
produced 77,233 rows / 25,586 subjects. Their exact table, manifest, key, mode, and builder hashes
are frozen additively in `MEDICAL_TARGET_PREP_BINDINGS_V1.json`. ELSA remains deliberately
unexecuted by the online agent and requires the licensed user-local command documented there.

The first KLoSA and CHARLS outputs were written on the T7 mount, whose effective permissions were
uniform `0755`. After byte hashes were reverified, owner-only copies were installed under
`data/private/crta_v3` (`0700` directories and `0600` files), and the two insecure
T7 derived directories were removed. The binding validator verifies both the secure copies and the
absence of those T7 copies without deserializing person-level rows.

## Missing private artifacts

The recorded ELSA v1 table/key (`fdc867...`, `b74149...`) and CHARLS v1 table/key
(`c4fa7a...`, `5c9b7d...`) remain absent from their historical private paths. CHARLS now has an
explicit v2 table/key with new hashes; it does not claim to reproduce the missing v1 partition.
ELSA still requires the analogous licensed-user-local v2 build. Historical salted subject splits
cannot be reproduced without the original keys.

## Validation and execution boundary

Run the structural validator with:

```bash
python scripts/validate_crta_v3_medical_runtime_maps.py
python scripts/validate_crta_v3_medical_runtime_maps.py --check-local-state
```

`--verify-hashes` is available for a byte-level local audit and still does not deserialize person
rows. A passing validator means the blocked mapping declarations are internally consistent; it
does not mean efficacy execution is authorized or ready.

The additive target-preparation binding is checked separately with:

```bash
python scripts/validate_medical_target_prep_bindings_v1.py
```

Every launcher must fail closed on authorization, payload/table/map hash, payload coverage,
accepted-member-to-null, sidecar join, private-table/key, and physical-GPU-1 violations. Training
is CPU-only, and the HRS authorization validator must pass for the exact task scope before any
person-level module import or row access.
