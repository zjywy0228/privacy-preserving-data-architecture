"""
Demo: DP training loop with budget accounting.

Shows how to configure a DPTrainer, run a mock training loop,
and monitor privacy budget consumption — stopping before the
target epsilon is exhausted.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dp_trainer import DPTrainer, PrivacyConfig


def main():
    print("=== Differential Privacy Training Demo ===\n")

    config = PrivacyConfig(
        target_epsilon=3.0,
        target_delta=1e-5,
        max_grad_norm=1.0,
        noise_multiplier=1.1,
    )
    print(config.describe())

    DATASET_SIZE = 50_000
    BATCH_SIZE = 256
    MAX_STEPS = 500

    trainer = DPTrainer(
        model=None,          # set to your nn.Module in real use
        optimizer=None,      # set to your DP-wrapped optimizer
        config=config,
        dataset_size=DATASET_SIZE,
        batch_size=BATCH_SIZE,
    )

    # Pre-training noise-multiplier check
    needed_noise = trainer.get_noise_multiplier_for_target(
        target_epsilon=config.target_epsilon,
        num_epochs=5,
    )
    print(f"\nNoise multiplier needed for epsilon={config.target_epsilon} over 5 epochs: "
          f"{needed_noise:.4f}")
    print(f"Configured noise multiplier: {config.noise_multiplier}\n")

    print(f"Training for up to {MAX_STEPS} steps "
          f"(batch {BATCH_SIZE} / dataset {DATASET_SIZE})...")

    for step in range(1, MAX_STEPS + 1):
        _ = trainer.step(batch=None)  # pass real (inputs, labels) in production

        if step % 50 == 0:
            budget = trainer.privacy_budget_spent()
            print(f"  Step {step:4d} | epsilon spent: {budget['epsilon_spent']:.4f} "
                  f"/ {config.target_epsilon} | "
                  f"exhausted: {budget['budget_exhausted']}")

        if trainer.should_stop():
            print(f"\n  Budget exhausted at step {step}. Stopping training.")
            break

    print("\nFinal privacy accounting:")
    for k, v in trainer.privacy_budget_spent().items():
        print(f"  {k}: {v}")

    print("\nDone.")


if __name__ == "__main__":
    main()
