import os
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_model():
    model = joblib.load(os.path.join(BASE_DIR, "ensemble_model.joblib"))
    feature_names = joblib.load(os.path.join(BASE_DIR, "feature_names.joblib"))
    return model, feature_names
