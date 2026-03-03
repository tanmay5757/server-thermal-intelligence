import numpy as np

def predict_with_inertia(input_df, model, session_state, y_mean, y_std):
    """
    Predict temperature with thermal inertia effect.
    """

    y_standardized = model.predict(input_df)[0]
    target_temp = y_standardized * y_std + y_mean

    alpha = 0.15

    new_temp = (
        (1 - alpha) * session_state.thermal_state
        + alpha * target_temp
    )

    session_state.thermal_state = new_temp

    fail_prob = np.clip((new_temp - 70) / 20, 0, 1)

    return round(new_temp, 2), round(fail_prob, 2)