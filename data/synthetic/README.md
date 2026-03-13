This directory stores synthetic patient data generated for testing
and data augmentation purposes.

HEALTH GYM:
  Synthetic patient records generated using Health Gym or similar
  generative models. These records:
    - Follow realistic vital sign distributions
    - Include plausible symptom combinations
    - Are labeled with synthetic risk levels
    - Are 100% synthetic — no real patient data
    - Used for integration testing and demo scenarios

GENERATION:
  Synthetic data is generated on demand using scripts in ml/ or
  tests/ directories. Place generated CSV/Parquet files here.

SAFE TO COMMIT: Since all data is synthetic, these files can be committed
to Git (unlike the raw/ directory). However, large generated files
should still be git-ignored to keep the repository lightweight.
