# TransTab transformers-4.30 environment comparison

Status: complete; 60 paired realization cells per environment.
Versions: ['5.12.0'] -> ['4.30.0'].
Construction hashes identical: True.
Deltas are replication minus baseline; no post-hoc equivalence margin is used.

## K=32

### Frozen contrast deltas

- C_content_correct_vs_wrong/additive: old=+0.527180, new=+0.527180, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_content_correct_vs_wrong/pairwise: old=+0.491329, new=+0.491329, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_content_correct_vs_wrong/sparse: old=+0.576700, new=+0.576700, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_utility_correct_vs_reference/additive: old=+0.178853, new=+0.178853, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_utility_correct_vs_reference/pairwise: old=+0.245453, new=+0.245453, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_utility_correct_vs_reference/sparse: old=+0.211737, new=+0.211737, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_wrong_vs_reference/additive: old=-0.348326, new=-0.348326, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_wrong_vs_reference/pairwise: old=-0.245875, new=-0.245875, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_wrong_vs_reference/sparse: old=-0.364963, new=-0.364963, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True

### Arm Q deltas

- correct/additive: +0.000000 [+0.000000, +0.000000]
- correct/pairwise: +0.000000 [+0.000000, +0.000000]
- correct/sparse: +0.000000 [+0.000000, +0.000000]
- c_wrong/additive: +0.000000 [+0.000000, +0.000000]
- c_wrong/pairwise: +0.000000 [+0.000000, +0.000000]
- c_wrong/sparse: +0.000000 [+0.000000, +0.000000]
- c_reference/additive: +0.000000 [+0.000000, +0.000000]
- c_reference/pairwise: +0.000000 [+0.000000, +0.000000]
- c_reference/sparse: +0.000000 [+0.000000, +0.000000]

## K=512

### Frozen contrast deltas

- C_content_correct_vs_wrong/additive: old=+0.160527, new=+0.160527, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_content_correct_vs_wrong/pairwise: old=+0.157280, new=+0.157280, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_content_correct_vs_wrong/sparse: old=+0.165421, new=+0.165421, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_utility_correct_vs_reference/additive: old=+0.017475, new=+0.017475, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_utility_correct_vs_reference/pairwise: old=+0.014295, new=+0.014295, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_utility_correct_vs_reference/sparse: old=+0.015642, new=+0.015642, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_wrong_vs_reference/additive: old=-0.143052, new=-0.143052, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_wrong_vs_reference/pairwise: old=-0.142985, new=-0.142985, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True
- C_wrong_vs_reference/sparse: old=-0.149779, new=-0.149779, delta=+0.000000 [+0.000000, +0.000000], sign_preserved=True

### Arm Q deltas

- correct/additive: +0.000000 [+0.000000, +0.000000]
- correct/pairwise: +0.000000 [+0.000000, +0.000000]
- correct/sparse: +0.000000 [+0.000000, +0.000000]
- c_wrong/additive: +0.000000 [+0.000000, +0.000000]
- c_wrong/pairwise: +0.000000 [+0.000000, +0.000000]
- c_wrong/sparse: +0.000000 [+0.000000, +0.000000]
- c_reference/additive: +0.000000 [+0.000000, +0.000000]
- c_reference/pairwise: +0.000000 [+0.000000, +0.000000]
- c_reference/sparse: +0.000000 [+0.000000, +0.000000]

