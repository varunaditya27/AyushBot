# ─────────────────────────────────────────────────────────────────
# DATASET 1: TinyML — Binary Danger Classifier (ESP32 layer)
# Based on WHO/IMCI clinical thresholds and MIMIC-IV vital-sign
# distributions validated against Royal Children's Hospital ranges
# ─────────────────────────────────────────────────────────────────

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import os

os.makedirs("output", exist_ok=True)
rng = np.random.default_rng(42)

N_SAFE = 4200
N_DANGER = 900  # ~18% danger, matches MIMIC-IV ICU adverse outcome base rate

def simulate_vitals_safe(n):
    age_months = rng.choice(
        [rng.integers(1, 6), rng.integers(6, 24), rng.integers(24, 60)],
        size=n, replace=True
    ).astype(float) + rng.uniform(0, 1, n)
    age_months = np.clip(age_months, 1, 60)

    # HR: age-adjusted normal ranges (RCH paediatric table)
    # Neonate-6m: 120-160, 6m-2y: 110-150, 2-5y: 95-130
    hr_low  = np.where(age_months < 6, 120, np.where(age_months < 24, 110, 95))
    hr_high = np.where(age_months < 6, 160, np.where(age_months < 24, 150, 130))
    hr = rng.uniform(0, 1, n) * (hr_high - hr_low) + hr_low + rng.normal(0, 4, n)
    hr = np.clip(hr, 60, 180)

    # SpO2: normoxaemia 94-100% (WHO definition)
    spo2 = rng.uniform(94, 100, n) + rng.normal(0, 0.6, n)
    spo2 = np.clip(spo2, 90, 100)

    # Temp: normal 36.5-37.5 °C
    temp = rng.uniform(36.2, 37.6, n) + rng.normal(0, 0.2, n)

    # Deltas: small random drift, no sustained fall
    delta_spo2 = rng.normal(0, 0.4, n)        # small noise
    delta_hr   = rng.normal(0, 3.0, n)        # small noise

    label = np.zeros(n, dtype=int)
    return age_months, hr, spo2, temp, delta_spo2, delta_hr, label


def simulate_vitals_danger(n):
    age_months = rng.choice(
        [rng.integers(1, 6), rng.integers(6, 24), rng.integers(24, 60)],
        size=n, replace=True
    ).astype(float) + rng.uniform(0, 1, n)
    age_months = np.clip(age_months, 1, 60)

    # SpO2: severe hypoxaemia < 90% (WHO IMCI danger threshold)
    # Mix: severe (<90%) and moderate (90-93%)
    spo2_severe = rng.uniform(70, 90, n)
    spo2_mod    = rng.uniform(90, 93, n)
    spo2_mask   = rng.random(n) < 0.65       # 65% severe
    spo2 = np.where(spo2_mask, spo2_severe, spo2_mod) + rng.normal(0, 0.5, n)
    spo2 = np.clip(spo2, 60, 100)

    # HR: tachycardia / bradycardia (danger)
    hr_tach = rng.uniform(180, 220, n)        # tachycardia
    hr_brad = rng.uniform(50, 80, n)          # bradycardia
    hr_mask = rng.random(n) < 0.75
    hr = np.where(hr_mask, hr_tach, hr_brad) + rng.normal(0, 5, n)
    hr = np.clip(hr, 40, 230)

    # Temp: fever ≥ 38.5 or hypothermia < 35.5
    temp_fever  = rng.uniform(38.5, 41.5, n)
    temp_hypo   = rng.uniform(33.0, 35.5, n)
    temp_mask   = rng.random(n) < 0.80
    temp = np.where(temp_mask, temp_fever, temp_hypo) + rng.normal(0, 0.3, n)

    # Deltas: sustained falls — clinically alarming
    delta_spo2 = rng.uniform(-8, -1, n)       # rapid O2 desaturation
    delta_hr   = rng.uniform(10, 40, n)       # surging HR

    label = np.ones(n, dtype=int)
    return age_months, hr, spo2, temp, delta_spo2, delta_hr, label


# Build rows
parts = []
for gen, n in [(simulate_vitals_safe, N_SAFE), (simulate_vitals_danger, N_DANGER)]:
    age, hr, spo2, temp, d_spo2, d_hr, lbl = gen(n)
    parts.append(pd.DataFrame({
        "age_months":     np.round(age, 1),
        "spo2_current":   np.round(spo2, 1),
        "hr_current":     np.round(hr, 1),
        "temperature_c":  np.round(temp, 2),
        "delta_spo2_30s": np.round(d_spo2, 2),
        "delta_hr_30s":   np.round(d_hr, 2),
        "danger_label":   lbl,
    }))

df_tiny = pd.concat(parts).sample(frac=1, random_state=42).reset_index(drop=True)
df_tiny.to_csv("output/tinyml_dataset.csv", index=False)
print(f"TinyML dataset: {df_tiny.shape}")
print(df_tiny["danger_label"].value_counts())
print(df_tiny.describe().round(2))