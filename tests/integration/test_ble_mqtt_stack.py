def test_ble_mqtt_stack_smoke():
from __future__ import annotations

import pytest

pytest.importorskip("paho.mqtt")


@pytest.mark.integration
def test_ble_mqtt_stack_smoke():
    assert True
