# ─────────────────────────────────────────────────────────────────
# DATASET 2: XGBoost — 4-class Pre-Triage Risk Classifier (RPi layer)
# 24 features: Group A (6 sensors), Group B (11 clinical indices),
# Group C (7 temporal trends)
# Label distribution inspired by triage literature:
# ~55% Low, 25% Medium, 13% High, 7% Critical  (Pubmed 2021, cardiovascular triage)
# ─────────────────────────────────────────────────────────────────

N = 8000

def waz_from_age_weight(age_months, weight_kg):
    """Approximate WAZ using WHO median and SD (simplified lookup)."""
    # Approximate WHO medians (kg) by age band
    who_median = np.where(age_months < 3,  5.1,
                 np.where(age_months < 6,  6.9,
                 np.where(age_months < 12, 8.9,
                 np.where(age_months < 24, 11.5,
                 np.where(age_months < 36, 13.5,
                 np.where(age_months < 48, 15.0, 16.3))))))
    sd = 0.95  # approx WHO SD for under-5
    return (weight_kg - who_median) / sd

# ── Age & weight ──────────────────────────────────────────────────
age_months = np.clip(rng.exponential(18, N) + rng.uniform(1, 5, N), 1, 59).round(1)
# Weight correlated with age + malnutrition noise
who_weight  = np.where(age_months < 3, 5.0,
              np.where(age_months < 6, 6.8,
              np.where(age_months < 12, 8.8,
              np.where(age_months < 24, 11.2,
              np.where(age_months < 36, 13.2,
              np.where(age_months < 48, 14.7, 16.0))))))
# Add malnutrition noise (NFHS-5: ~32% underweight)
malnutrition_factor = rng.choice([1.0, 0.80, 0.65], size=N,
                                  p=[0.68, 0.20, 0.12])
weight_kg = np.clip(who_weight * malnutrition_factor + rng.normal(0, 0.5, N), 1.5, 25).round(1)

# ── WAZ ───────────────────────────────────────────────────────────
waz = waz_from_age_weight(age_months, weight_kg).round(2)

# ── Group A: Direct sensor readings ──────────────────────────────
spo2       = np.clip(rng.normal(96, 3.5, N), 70, 100).round(1)
hr         = np.clip(rng.normal(130, 22, N), 50, 230).round(1)
temp       = np.clip(rng.normal(37.3, 1.1, N), 33, 42).round(2)
rr         = np.clip(rng.normal(38, 9, N), 15, 80).round(1)    # resp. rate breaths/min
hr_spo2_ratio = (hr / spo2).round(3)                           # systolic BP proxy
ppg_rr_est    = np.clip(rr + rng.normal(0, 2, N), 15, 80).round(1)  # PPG morphology estimate

# ── Group B: Derived clinical indices ─────────────────────────────
# Symptom binary flags from WHO IMCI checklist
p_symptom_base = 0.15
fast_breathing   = (rr > np.where(age_months < 12, 50, 40)).astype(int)
chest_indrawing  = (rng.random(N) < 0.12).astype(int)
unable_to_drink  = (rng.random(N) < 0.08).astype(int)
convulsions_24h  = (rng.random(N) < 0.05).astype(int)
pallor           = (rng.random(N) < 0.18).astype(int)         # NFHS-5: ~18% anaemia under-5
severe_edema     = (rng.random(N) < 0.03).astype(int)
severe_wasting   = (waz < -3).astype(int)                     # WAZ < -3 = SAM
neonate_danger   = ((age_months < 1) & (rng.random(N) < 0.20)).astype(int)
prolonged_fever  = (rng.random(N) < 0.10).astype(int)         # >7 days
time_in_field_h  = np.clip(rng.exponential(2, N), 0.1, 10).round(2)

# ── Group C: Temporal trend features ─────────────────────────────
delta_spo2_30s   = rng.normal(-0.1, 1.8, N).round(2)
delta_hr_30s     = rng.normal(0.5, 6, N).round(2)
spo2_cv          = np.abs(rng.normal(1.5, 0.8, N)).round(3)   # coeff of variation
temp_ma3         = (temp + rng.normal(0, 0.1, N)).round(2)    # moving avg 3 readings
hr_iqr           = np.abs(rng.normal(12, 5, N)).round(2)      # IQR of HR window
spo2_variance_flag = (spo2_cv > 2.5).astype(int)

# ── Derive risk label from clinical logic ─────────────────────────
# Critical: SpO2<85 OR convulsions OR SAM+fever OR neonate_danger OR HR>190
# High:     SpO2<90 OR fast_breathing + chest_indrawing OR waz<-2 + pallor
# Medium:   SpO2<94 OR fast_breathing OR fever>38.5 OR pallor
# Low:      otherwise
def assign_risk(i):
    critical = (spo2[i] < 85 or convulsions_24h[i] == 1 or
                (waz[i] < -3 and temp[i] > 38.5) or
                neonate_danger[i] == 1 or hr[i] > 190 or
                unable_to_drink[i] == 1)
    high     = (spo2[i] < 90 or
                (fast_breathing[i] == 1 and chest_indrawing[i] == 1) or
                (waz[i] < -2 and pallor[i] == 1))
    medium   = (spo2[i] < 94 or fast_breathing[i] == 1 or
                temp[i] > 38.5 or pallor[i] == 1 or
                prolonged_fever[i] == 1)
    if critical: return 3
    if high:     return 2
    if medium:   return 1
    return 0

labels = np.array([assign_risk(i) for i in range(N)])
label_map = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
label_names = [label_map[l] for l in labels]

# ── Assemble dataframe ─────────────────────────────────────────────
df_xgb = pd.DataFrame({
    # Group A
    "spo2_current":      spo2,
    "hr_current":        hr,
    "temperature_c":     temp,
    "weight_kg":         weight_kg,
    "hr_spo2_ratio":     hr_spo2_ratio,
    "ppg_rr_est":        ppg_rr_est,
    # Group B
    "age_months":        age_months,
    "waz":               waz,
    "fast_breathing":    fast_breathing,
    "chest_indrawing":   chest_indrawing,
    "unable_to_drink":   unable_to_drink,
    "convulsions_24h":   convulsions_24h,
    "pallor":            pallor,
    "severe_edema":      severe_edema,
    "severe_wasting":    severe_wasting,
    "neonate_danger":    neonate_danger,
    "prolonged_fever":   prolonged_fever,
    "time_in_field_h":   time_in_field_h,
    # Group C
    "delta_spo2_30s":    delta_spo2_30s,
    "delta_hr_30s":      delta_hr_30s,
    "spo2_cv":           spo2_cv,
    "temp_ma3":          temp_ma3,
    "hr_iqr":            hr_iqr,
    "spo2_variance_flag": spo2_variance_flag,
    # Label
    "risk_label":        label_names,
    "risk_code":         labels,
})

df_xgb = df_xgb.sample(frac=1, random_state=42).reset_index(drop=True)
df_xgb.to_csv("output/xgboost_dataset.csv", index=False)

print(f"XGBoost dataset: {df_xgb.shape}")
print(df_xgb["risk_label"].value_counts())
print(df_xgb.describe().round(2))