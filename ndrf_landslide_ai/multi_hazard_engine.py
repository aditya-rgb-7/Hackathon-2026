import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Synthetic Multi-Hazard Dataset representing NER corridors
np.random.seed(42)
N = 9000

# Features: Slope, Rain, Soil Saturation, Seismic Factor, Drainage Density, Forest Loss Rate
df = pd.DataFrame({
    'slope_deg': np.random.uniform(5, 65, N),
    'rainfall_72h_mm': np.random.uniform(0, 500, N),
    'soil_moist_pct': np.random.uniform(10, 100, N),
    'seismic_zone': np.random.choice([4, 5], N),  # NER is predominantly Zone V
    'drainage_density': np.random.uniform(0.5, 4.5, N),
    'forest_loss_pct': np.random.uniform(0, 60, N)
})

# Hazard Classification Logic:
# 0 = Stable, 1 = Landslide, 2 = Flash Flood, 3 = Severe Debris Flow
conditions = [
    (df['slope_deg'] > 40) & (df['rainfall_72h_mm'] > 180) & (df['soil_moist_pct'] > 75),
    (df['slope_deg'] <= 25) & (df['rainfall_72h_mm'] > 200) & (df['drainage_density'] > 3.0),
    (df['slope_deg'] > 35) & (df['forest_loss_pct'] > 30) & (df['rainfall_72h_mm'] > 140)
]
choices = [1, 2, 3]
df['hazard_type'] = np.select(conditions, choices, default=0)

X = df[['slope_deg', 'rainfall_72h_mm', 'soil_moist_pct', 'seismic_zone', 'drainage_density', 'forest_loss_pct']]
y = df['hazard_type']

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

joblib.dump({
    'model': model,
    'features': list(X.columns),
    'labels': {0: 'Stable', 1: 'Landslide', 2: 'Flash Flood', 3: 'Debris Flow'}
}, 'multi_hazard_engine.pkl')

print("Saved multi_hazard_engine.pkl successfully.")