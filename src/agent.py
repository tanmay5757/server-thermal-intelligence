import numpy as np


def thermal_agent(temp, fail_prob, inputs, history):
    """
    Analyze thermal state and classify system severity.
    """

    actions = []
    reasons = []

    abs_vals = [abs(v) for v in inputs.values()]

    elevated_count = sum(v >= 0.5 for v in abs_vals)
    high_count = sum(v >= 1.0 for v in abs_vals)
    critical_count = sum(v >= 2.0 for v in abs_vals)

    if critical_count >= 3:
        severity = "CRITICAL"
        actions.append("🚨 Multiple Critical Sensors")
        reasons.append("≥3 features above +2σ")

    elif high_count >= 3:
        severity = "HIGH"
        actions.append("⚠ Multiple High Sensors")
        reasons.append("≥3 features above +1σ")

    elif elevated_count >= 3:
        severity = "ELEVATED"
        actions.append("⚠ Elevated Operating Conditions")
        reasons.append("≥3 features above +0.5σ")

    else:
        severity = "NORMAL"
        actions.append("✅ System Stable")
        reasons.append("Inputs within normal range")

    # Trend awareness
    if len(history) >= 5:
        slope = np.polyfit(range(5), history[-5:], 1)[0]
        if slope > 0.8:
            actions.append("⚠ Rapid Thermal Escalation")
            reasons.append(f"Temp rising at {slope:.2f} °C / step")

    return severity, actions, reasons