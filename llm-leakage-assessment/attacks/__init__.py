"""
Membership-inference attack reference implementations.

Import ``LossThresholdAttack`` to evaluate MIA effectiveness on a target
model, or call ``simulate_attack`` for a self-contained demonstration.
"""

from .membership_inference import (
    AttackResult,
    LossThresholdAttack,
    dp_advantage_bound,
    simulate_attack,
)

__all__ = ["AttackResult", "LossThresholdAttack", "dp_advantage_bound", "simulate_attack"]
