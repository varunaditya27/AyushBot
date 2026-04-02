from __future__ import annotations

import numpy as np

from backend.fl.aggregator import GradientQueue


def test_gradient_queue_fifo(tmp_path):
    queue = GradientQueue(str(tmp_path), max_queue_size=10)
    queue.enqueue(np.array([1.0, 2.0], dtype=np.float32), {"round": 1})
    queue.enqueue(np.array([3.0, 4.0], dtype=np.float32), {"round": 2})

    first = queue.dequeue()
    second = queue.dequeue()

    assert first is not None and second is not None
    assert first.metadata["round"] == 1
    assert second.metadata["round"] == 2
    assert queue.dequeue() is None
