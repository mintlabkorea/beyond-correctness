"""Frozen exact single-item endpoint registry for stage-factorial expansion."""

ENDPOINTS = {
    "diabetes_history": ("DIQ010", "ALL__de1_dg"),
    "hypertension_history": ("BPQ020", "ALL__di1_dg"),
    "current_smoking_status": ("SMQ040", "ALL__bs3_1"),
    "kidney_disease_history": ("KIQ022", "ALL__dn1_dg"),
    "stroke_history": ("MCQ160F", "ALL__di3_dg"),
    "arthritis_history": ("MCQ160A", "ALL__dm1_dg"),
    "asthma_history": ("MCQ010", "ALL__dj4_dg"),
    "cancer_history": ("MCQ220", "ALL__dc1_dg"),
    "heart_attack_history": ("MCQ160E", "ALL__di5_dg"),
    "angina_history": ("MCQ160D", "ALL__di6_dg"),
}


def configure(sf) -> None:
    sf.TARGETS = dict(ENDPOINTS)
    source_binary = {1: 1, 2: 0}
    target_binary = {1: 1, 0: 0}
    sf.PIPELINE_LABEL_MAPS = {
        target: {"source": dict(source_binary), "target": dict(target_binary)}
        for target in ENDPOINTS
    }
    sf.PIPELINE_LABEL_MAPS["current_smoking_status"] = {
        "source": {1: 1, 2: 1, 3: 0},
        "target": {1: 1, 2: 1, 3: 0, 4: 0},
    }
    sf.EVAL_LABEL_MAPS = {
        target: dict(target_binary) for target in ENDPOINTS
    }
    sf.EVAL_LABEL_MAPS["current_smoking_status"] = {
        1: 1, 2: 1, 3: 0, 4: 0,
    }
    sf.LABEL_ITEMS = {
        target: {"source": ("nhanes", pair[0]),
                 "target": ("knhanes", pair[1])}
        for target, pair in ENDPOINTS.items()
    }
    basis = dict(sf.PLACEBO_BASIS)
    for target, (nh_col, kn_col) in ENDPOINTS.items():
        if target == "current_smoking_status":
            basis[("nhanes", nh_col)] = {
                "valid": [1, 2, 3], "sentinel": [7, 9],
                "outputs": [1, 1, 0]}
            basis[("knhanes", kn_col)] = {
                "valid": [1, 2, 3, 4], "sentinel": [8, 9],
                "outputs": [1, 1, 0, 0]}
        else:
            nh_sentinel = [3, 7, 9] if target == "diabetes_history" else [7, 9]
            basis[("nhanes", nh_col)] = {
                "valid": [1, 2], "sentinel": nh_sentinel,
                "outputs": [1, 0]}
            basis[("knhanes", kn_col)] = {
                "valid": [0, 1], "sentinel": [8, 9],
                "outputs": [0, 1]}
    sf.PLACEBO_BASIS = basis

