import joblib
import numpy as np

# 1. Load the exported model package
package = joblib.load("landslide_model.pkl")
model = package['classifier']
features = package['features']

print("Loaded Model:", type(model).__name__)
print("Required Features:", features)
print("-" * 55)

# Test Scenario A: Flat ground, low rain, stable hillside
scenario_safe = np.array([[12.0, 1.2, 25.0, 30.0, 450.0]])

# Test Scenario B: Steep cliff, heavy monsoon rain, high soil saturation, active ground creep
scenario_critical = np.array([[58.0, 38.5, 410.0, 92.0, 1650.0]])

# Run Prediction
prob_safe = model.predict_proba(scenario_safe)[0][1]
prob_crit = model.predict_proba(scenario_critical)[0][1]

print(f"SCENARIO A (Normal Conditions):")
print(f"  -> Failure Probability: {prob_safe * 100:.2f}%")
print(f"  -> Model Decision:      {'CRITICAL THREAT' if prob_safe >= 0.70 else 'STABLE'}")
print("-" * 55)

print(f"SCENARIO B (Extreme Monsoon + High Creep):")
print(f"  -> Failure Probability: {prob_crit * 100:.2f}%")
print(f"  -> Model Decision:      {'CRITICAL THREAT' if prob_crit >= 0.70 else 'STABLE'}")
print("-" * 55)