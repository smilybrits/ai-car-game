"""Headless validation runner for the RL environment (Milestone 4)."""

from __future__ import annotations

from pathlib import Path
import math
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from env import CarRacingEnv


def random_action() -> dict[str, float]:
    """Return a random continuous action inside the supported ranges."""
    return {
        "steer": random.uniform(-1.0, 1.0),
        "throttle": random.uniform(0.0, 1.0),
        "brake": random.uniform(0.0, 1.0),
    }


def validate_observation(obs: list[float], expected_length: int) -> None:
    """Raise if observation is malformed, non-numeric, or unstable in size."""
    if obs is None:
        raise RuntimeError("Observation is None")

    if len(obs) != expected_length:
        raise RuntimeError(
            f"Observation length changed: expected {expected_length}, got {len(obs)}"
        )

    for index, value in enumerate(obs):
        if value is None:
            raise RuntimeError(f"Observation contains None at index {index}")

        if not isinstance(value, (int, float)):
            raise RuntimeError(
                f"Observation contains non-numeric value at index {index}: {value!r}"
            )

        if math.isnan(value):
            raise RuntimeError(f"Observation contains NaN at index {index}")


def main() -> None:
    """Run 1000 random headless environment steps with safety checks."""
    env = CarRacingEnv(headless=True)

    try:
        obs = env.reset(seed=0)
        expected_length = len(obs)

        print("Initial observation:", obs)
        print("Observation length:", expected_length)

        for step in range(1000):
            action = random_action()
            obs, reward, done, info = env.step(action)

            validate_observation(obs, expected_length)

            if reward is None or (isinstance(reward, float) and math.isnan(reward)):
                raise RuntimeError("Reward is invalid")

            if not isinstance(done, bool):
                raise RuntimeError(f"Done flag must be bool, got {type(done).__name__}")

            if not isinstance(info, dict):
                raise RuntimeError(f"Info must be dict, got {type(info).__name__}")

            print(f"Step {step} | Reward: {float(reward):.3f} | Done: {done}")

            if done:
                print("Episode finished. Resetting...")
                obs = env.reset()
                validate_observation(obs, expected_length)

        print("Validation completed successfully for 1000 steps.")
    finally:
        env.close()


if __name__ == "__main__":
    main()
