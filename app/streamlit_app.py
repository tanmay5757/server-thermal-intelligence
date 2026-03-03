import streamlit as st
import joblib

import pandas as pd
import numpy as np

import sys
from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
from src.predictor import predict_with_inertia
from src.agent import thermal_agent
from src.thermal_controller import auto_cooldown_controller
# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Server Thermal Intelligence", layout="wide")
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# LOAD MODEL + FEATURES
# ============================================================
@st.cache_resource
def load_models():
    model = joblib.load(BASE_DIR / "models" / "ensemble_model.joblib")
    feature_names = joblib.load(BASE_DIR / "models" / "feature_names.joblib")
    return model, feature_names

model, feature_names = load_models()

# ============================================================
# LOAD TARGET STATS
# ============================================================
@st.cache_data
def load_target_stats():
    df = pd.read_csv(BASE_DIR / "data" / "final_dataset_std.csv", sep=";")
    y = df["TLHC"]
    return float(y.mean()), float(y.std())

Y_MEAN, Y_STD = load_target_stats()

# ============================================================
# FEATURE GROUPS
# ============================================================
GROUPS = {
    "AC Power": [f"P_ac-{i}" for i in range(8)],
    "Compute Power": [f"P_cu-{i}" for i in range(8)],
    "Outside Temp": [f"T_out-{i}" for i in range(8)],
    "Measured Temp": [f"T_MEAS-{i}" for i in range(8)],
    "Cold Column Temp": [f"T_celCC-{i}" for i in range(8)],
}

# ============================================================
# STATE
# ============================================================
if "thermal_state" not in st.session_state:
    st.session_state.thermal_state = Y_MEAN

if "history" not in st.session_state:
    st.session_state.history = []

if "auto_cooldown" not in st.session_state:
    st.session_state.auto_cooldown = False




# ============================================================
# UI
# ============================================================
st.title("🔥 Server Thermal Intelligence Dashboard")
st.sidebar.header("🔧 Group Controls (Standardized)")

preset = st.sidebar.selectbox(
    "Preset Mode", ["Custom", "Low Load", "Medium Load", "High Load"]
)

# Automatic indicator (no manual control)
st.sidebar.toggle(
    "❄️ Automatic Cooldown Mode",
    key="auto_cooldown",
    disabled=True
)

# Presets
if preset == "Low Load":
    preset_vals = {
        "AC Power": -1.0,
        "Compute Power": -2.0,
        "Outside Temp": -1.5,
        "Measured Temp": -1.5,
        "Cold Column Temp": -1.5,
    }
elif preset == "High Load":
    preset_vals = {
        "AC Power": 0.5,
        "Compute Power": 2.8,
        "Outside Temp": 2.5,
        "Measured Temp": 2.5,
        "Cold Column Temp": 2.0,
    }
else:
    preset_vals = {k: 0.0 for k in GROUPS}

group_values = {}
for group in GROUPS:
    group_values[group] = st.sidebar.slider(
        f"{group} (z-score)", -3.0, 3.0, preset_vals[group], 0.1
    )

# ============================================================
# BUILD INPUT VECTOR
# ============================================================
inputs = {}
for feature in feature_names:
    for group, members in GROUPS.items():
        if feature in members:
            inputs[feature] = group_values[group]
            break
    else:
        inputs[feature] = 0.0

input_df = pd.DataFrame([inputs], columns=feature_names)

# ============================================================
# RUN MODEL
# ============================================================
pred_temp, fail_prob = predict_with_inertia(
    input_df,
    model,
    st.session_state,
    Y_MEAN,
    Y_STD
)

st.session_state.history.append(st.session_state.thermal_state)
st.session_state.history = st.session_state.history[-30:]

severity, actions, reasons = thermal_agent(
    pred_temp,
    fail_prob,
    inputs,
    st.session_state.history
)

# ============================================================
# FULLY AUTOMATIC COOLING CONTROL
# ============================================================

auto_cooling_active = severity in ["HIGH", "CRITICAL"]

current_fail = np.clip((st.session_state.thermal_state - 70) / 20, 0, 1)

if auto_cooling_active:

    group_values = auto_cooldown_controller(
        group_values,
        st.session_state.thermal_state,
        current_fail
    )

    st.sidebar.error("❄️ Emergency Auto Cooling Active")

# Display indicator switch
st.sidebar.toggle(
    "❄️ Automatic Cooldown Mode",
    value=auto_cooling_active,
    disabled=True
)


# ============================================================
# OUTPUT
# ============================================================
col1, col2 = st.columns(2)

with col1:
    st.metric("🌡 Temperature", f"{pred_temp} °C")

    if severity == "CRITICAL":
        st.error("🔥 CRITICAL")
    elif severity == "HIGH":
        st.warning("⚠ HIGH")
    elif severity == "ELEVATED":
        st.info("🟡 ELEVATED")
    else:
        st.success("✅ NORMAL")

with col2:
    st.subheader("🤖 System Assessment")
    for a in actions:
        st.write(f"- {a}")

    st.subheader("💡 Reasons")
    for r in reasons:
        st.write(f"- {r}")

# ============================================================
# TREND
# ============================================================
st.markdown("---")
st.subheader("📈 Temperature Trend")

trend_df = pd.DataFrame({
    "Step": range(len(st.session_state.history)),
    "Temperature": st.session_state.history
})

st.line_chart(trend_df.set_index("Step"))
