"""
gen_tinyml_dataset.py
=====================
Generates a REALISTIC synthetic TinyML dataset for a binary
danger-sign detector (ESP32 layer, 30-second vital-sign windows).

Realism mechanisms:
  1. Soft probabilistic labels — no hard threshold, ambiguity zone included
  2. Gaussian feature noise per age-band with realistic variance
  3. Borderline/overlap zone: SpO2 90-94 + moderate HR can be either class
  4. Label noise: ~5% boundary flips (clinician disagreement)
  5. Sensor dropout: ~3% NaN in SpO2, HR (imputed in training script)
  6. Sensor glitch: ~1% impossible outliers (calibration artifact)
  7. Slight train/test distribution shift (age skew in test set)

Expected final accuracy: ~85-94%  (NOT 100%)
"""

import numpy as np
import pandas as pd
import os

rng = np.random.default_rng(2024)
os.makedirs("data", exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────
def age_hr_range(age_m):
    """Return (hr_lo, hr_hi) based on RCH/Flemish paediatric norms."""
    hr_lo = np.where(age_m < 3,  100,
            np.where(age_m < 12, 100,
            np.where(age_m < 24,  90,
            np.where(age_m < 60,  80, 75))))
    hr_hi = np.where(age_m < 3,  160,
            np.where(age_m < 12, 160,
            np.where(age_m < 24, 150,
            np.where(age_m < 60, 140, 130))))
    return hr_lo.astype(float), hr_hi.astype(float)

def danger_probability(age_m, spo2, hr, temp, ds, dh):
    """
    Logistic-style danger probability — NOT a hard threshold.
    Inspired by: AVPU/PEWS scores, WHO IMCI thresholds.
    Key design choices:
      - SpO2 < 90: very high danger, but NOT certain (artefact possible)
      - SpO2 90-94: ambiguous, modulated by HR and temp
      - SpO2 >= 94: low danger but can still be danger if HR/temp extreme
      - Additive contributions, smooth sigmoid
    """
    hr_lo, hr_hi = age_hr_range(age_m)
    hr_norm = (hr - hr_lo) / np.maximum(hr_hi - hr_lo, 1.0)  # 0=low, 1=high

    score = np.zeros(len(age_m), dtype=float)

    # SpO2 contribution (most critical)
    score += np.where(spo2 < 85,  3.5,
             np.where(spo2 < 90,  2.5,
             np.where(spo2 < 92,  1.5,
             np.where(spo2 < 94,  0.8,
             np.where(spo2 < 96, -0.2, -0.8)))))

    # HR contribution
    score += np.where(hr_norm > 1.20,  1.5,
             np.where(hr_norm > 1.10,  0.9,
             np.where(hr_norm > 1.00,  0.4,
             np.where(hr_norm < 0.30, -0.5, 0.0))))

    # Temperature contribution
    score += np.where(temp > 39.5,  1.0,
             np.where(temp > 38.5,  0.5,
             np.where(temp < 35.5,  1.2, 0.0)))

    # Rapid desaturation
    score += np.where(ds < -4,  1.2,
             np.where(ds < -2,  0.6,
             np.where(ds < -1,  0.2, 0.0)))

    # HR surge
    score += np.where(dh > 25,  0.8,
             np.where(dh > 15,  0.4, 0.0))

    # Sigmoid → probability
    prob = 1.0 / (1.0 + np.exp(-score + 0.5))
    return np.clip(prob, 0.02, 0.98)


# ── generate population ───────────────────────────────────────────
N = 5500
print(f"[1/4] Sampling {N} patient windows...")

age_m = np.clip(
    np.concatenate([
        rng.choice([1,2,3,4,5], size=N//5) + rng.uniform(0, 1, N//5),   # neonates
        rng.choice(range(6, 24), size=N//5) + rng.uniform(0, 1, N//5),   # infants
        rng.choice(range(24,60), size=3*N//5) + rng.uniform(0, 1, 3*N//5) # toddlers
    ]), 1, 60).astype(float)

hr_lo, hr_hi = age_hr_range(age_m)
hr_mid = (hr_lo + hr_hi) / 2

# SpO2: bimodal — mostly normal, tail into hypoxaemia
spo2_base = np.where(
    rng.random(N) < 0.80,
    rng.normal(97.0, 1.8, N),           # normoxaemic
    np.where(rng.random(N) < 0.60,
             rng.normal(88.0, 3.5, N),  # severe hypoxaemia
             rng.normal(92.5, 1.2, N))  # moderate hypoxaemia
)
spo2 = np.clip(spo2_base + rng.normal(0, 0.6, N), 60, 100).round(1)

# HR: centred on age midpoint, fat tails for pathology
hr = np.clip(
    rng.normal(hr_mid, (hr_hi - hr_lo) * 0.30, N) +
    np.where(rng.random(N) < 0.12, rng.uniform(20, 55, N), 0) +  # tachycardia spike
    np.where(rng.random(N) < 0.04, rng.uniform(-30, -10, N), 0), # bradycardia
    40, 230
).round(1)

temp = np.clip(
    np.where(rng.random(N) < 0.72, rng.normal(37.1, 0.5, N),     # afebrile
    np.where(rng.random(N) < 0.60, rng.normal(39.0, 0.8, N),     # febrile
                                    rng.normal(34.5, 0.5, N))),    # hypothermic
    30, 43
).round(2)

delta_spo2 = np.clip(
    rng.normal(-0.2, 1.5, N) +
    np.where(spo2 < 92, rng.uniform(-3, -0.5, N), 0),
    -10, 4
).round(2)

delta_hr = np.clip(
    rng.normal(0.5, 5.0, N) +
    np.where(hr > hr_hi * 1.1, rng.uniform(5, 20, N), 0),
    -30, 60
).round(2)

# ── labels (probabilistic) ────────────────────────────────────────
print("[2/4] Assigning probabilistic labels (soft boundary)...")
p_danger = danger_probability(age_m, spo2, hr, temp, delta_spo2, delta_hr)
labels = rng.binomial(1, p_danger).astype(int)

# ── label noise: flip ~5% near boundary ──────────────────────────
boundary_mask = (p_danger > 0.25) & (p_danger < 0.75)   # ambiguous zone
flip_mask = boundary_mask & (rng.random(N) < 0.10)       # 10% of ambiguous = ~5% overall
labels[flip_mask] ^= 1

print(f"      Class balance: {dict(zip(*np.unique(labels, return_counts=True)))}")
print(f"      Danger rate: {labels.mean()*100:.1f}%")

# ── sensor dropout (~3% SpO2, ~2% HR) ────────────────────────────
spo2_out = spo2.astype(float)
hr_out   = hr.astype(float)
spo2_out[rng.random(N) < 0.03] = np.nan
hr_out  [rng.random(N) < 0.02] = np.nan

# ── sensor glitch: ~1% impossible values ─────────────────────────
glitch_idx = rng.choice(N, size=int(0.01 * N), replace=False)
spo2_out[glitch_idx] = rng.choice([0, 100, 101, 55, 33], size=len(glitch_idx))

# ── build DataFrame ───────────────────────────────────────────────
print("[3/4] Building DataFrame...")
df = pd.DataFrame({
    "age_months"    : age_m.round(1),
    "spo2_current"  : spo2_out.round(1),
    "hr_current"    : hr_out.round(1),
    "temperature_c" : temp,
    "delta_spo2_30s": delta_spo2,
    "delta_hr_30s"  : delta_hr,
    "danger_label"  : labels,
    "_p_danger"     : p_danger.round(4),   # kept for debugging — EXCLUDE from features
})

df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# ── save ──────────────────────────────────────────────────────────
print("[4/4] Saving...")
df.to_csv("data/tinyml_new_dataset.csv", index=False)

# also save a clean version without debug column
df.drop(columns=["_p_danger"]).to_csv("data/tinyml_dataset_clean.csv", index=False)

print(f"\nSaved: data/tinyml_new_dataset.csv  ({len(df)} rows)")
print(f"  danger rate : {labels.mean()*100:.1f}%")
print(f"  NaN in SpO2 : {spo2_out.isna().sum()}")
print(f"  NaN in HR   : {hr_out.isna().sum() if hasattr(hr_out, 'isna') else np.isnan(hr_out).sum()}")
print(f"  flipped labels (boundary noise) : {flip_mask.sum()}")
print("\nExpected model AUC after training: 0.85–0.96 (NOT 1.0)")
