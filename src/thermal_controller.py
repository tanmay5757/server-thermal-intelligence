# ============================================================
# AUTO COOLDOWN CONTROLLER
# ============================================================
def auto_cooldown_controller(group_vals, temp, fail_prob):

    new_vals = group_vals.copy()

    if fail_prob > 0.75:
        step = 0.30
    elif fail_prob > 0.5:
        step = 0.20
    elif temp > 80:
        step = 0.10
    else:
        return new_vals

    new_vals["AC Power"] = min(3.0, new_vals["AC Power"] + step)
    new_vals["Compute Power"] = max(-3.0, new_vals["Compute Power"] - step)

    for g in ["Measured Temp", "Cold Column Temp"]:
        new_vals[g] = max(-3.0, new_vals[g] - step / 2)

    return new_vals
