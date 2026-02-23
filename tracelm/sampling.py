from __future__ import annotations

import random


def should_sample(rate: float) -> bool:
    if not 0.0 <= rate <= 1.0:
        raise ValueError("rate must be between 0.0 and 1.0")
    if rate == 1.0:
        return True
    if rate == 0.0:
        return False
    return random.random() < rate
