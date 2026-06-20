# Pre-Triage Medical Review Checklist

`pretriage_rules.json` is a software-ready **draft**, not a clinically approved
ruleset. Every value below must be confirmed, changed if necessary, and signed
off by an appropriately qualified paediatric/IMCI reviewer before operational
use. After review, change `status` to `MEDICALLY_REVIEWED`, assign an immutable
`ruleset_version`, and record the exact guideline edition and section.

## Values Requiring Review

| Configuration | Draft value | Repository source |
|---|---:|---|
| SpO2 emergency comparison | `< 90%` | `research/ayushbot_paper.tex` |
| Temperature emergency comparison | `> 40 C` | `research/ayushbot_paper.tex` |
| SpO2 signal window | 10 readings | `docs/prd.md` |
| SpO2 coefficient-of-variation rejection | `> 3%` | `docs/prd.md` |
| Trend window | 30 seconds | `docs/prd.md` |
| Fast breathing, age 2-11 months | `> 50/min` | `docs/dataset-analysis.md` |
| Fast breathing, age 12-59 months | `> 40/min` | `docs/dataset-analysis.md` |
| Severe weight-for-age threshold | WAZ `< -3` | `docs/ml-design.md` |
| SpO2 validity bounds | 40-100% | previous implementation; source required |
| Heart-rate validity bounds | 30-250/min | previous implementation; source required |
| Temperature validity bounds | 30-45 C | previous implementation; source required |
| Weight validity bounds | 0-60 kg | previous implementation; source required |

## Rules Requiring Review

Confirm both the classification tier and any age/applicability constraints for:

- convulsions;
- lethargy, reduced consciousness, or unconsciousness;
- unable to drink, feed, or breastfeed;
- vomiting everything;
- chest indrawing;
- bilateral oedema;
- visible severe wasting;
- prolonged fever;
- diarrhea duration and dehydration checklist signs;
- stridor at rest, stiff neck, pallor, and all remaining Android checklist
  danger signs.

## Missing Required Inputs

The repository does not contain approved values for:

- age-dependent lower and upper heart-rate limits;
- respiratory-rate rules for children outside the configured 2-59 month bands;
- diarrhea-duration severity thresholds;
- age-specific temperature interpretation;
- combinations that upgrade malnutrition or diarrhea to emergency status;
- minimum acceptable sensor quality scores;
- complete neonatal and older-child applicability rules.

Add these as rules in `pretriage_rules.json`; do not add thresholds to Python.

## WHO Growth Reference

Replace `who_weight_for_age_lms.json` with the complete official WHO
weight-for-age LMS table for male and female children, preserving:

```json
{
  "sex": "female",
  "age_months": 0,
  "l": 0.0,
  "m": 0.0,
  "s": 0.0
}
```

Set `reference_version`, `source`, and `status: "MEDICALLY_REVIEWED"`. The
loader rejects duplicate sex/age rows and does not extrapolate outside the
provided age range.

## Model Release Review

Each XGBoost artifact must have a matching metadata file based on
`ml/triage_classifier/model_metadata.example.json`. Review and freeze:

- exact feature order;
- class order;
- model version;
- calibration temperature;
- validation/calibration metrics;
- intended population and age range.

The gateway rejects feature-count or feature-name mismatches. Missing feature
values are passed as XGBoost missing values (`NaN`), never zero.
