from __future__ import annotations

import numpy as np

from backend.fl.privacy import clip_by_l2


def test_gradient_clipping_max_norm():
    vector = np.array([3.0, 4.0], dtype=np.float32)  # norm=5
    clipped, norm = clip_by_l2(vector, max_norm=1.0)
    assert round(float(np.linalg.norm(clipped)), 6) == 1.0
    assert round(norm, 6) == 5.0


def test_gradient_clipping_no_effect_below_threshold():
    vector = np.array([0.3, 0.4], dtype=np.float32)  # norm=0.5
    clipped, _ = clip_by_l2(vector, max_norm=1.0)
    assert np.allclose(clipped, vector)
