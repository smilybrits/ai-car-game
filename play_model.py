"""Visual playback of a trained PPO model driving in the car racing environment."""

from __future__ import annotations

import time

import numpy as np
from stable_baselines3 import PPO

from env import CarRacingEnv

MODEL_PATH = "ppo_car_model"


def main() -> None:
    print(f"Loading trained model from '{MODEL_PATH}'...")
    model = PPO.load(MODEL_PATH)

    print("Creating visible environment...")
    env = CarRacingEnv(headless=False)

    try:
        obs = env.reset()
        obs_array = np.array(obs, dtype=np.float32)
        print("Playback started. Close the window to exit.")

        episode = 1
        # env.screen becomes None when the user closes the pygame window.
        while env.screen is not None:
            action, _ = model.predict(obs_array, deterministic=True)
            # _validate_action expects a Sequence; numpy arrays don't satisfy
            # isinstance(x, Sequence), so convert explicitly.
            obs, reward, done, info = env.step(action.tolist())
            obs_array = np.array(obs, dtype=np.float32)

            # Small delay so each rendered frame is visible.
            time.sleep(0.02)

            if done:
                print(
                    f"Episode {episode} finished — "
                    f"laps: {info.get('lap_count', 0)}, "
                    f"steps: {info.get('step_count', 0)}"
                )
                episode += 1
                obs = env.reset()
                obs_array = np.array(obs, dtype=np.float32)

    finally:
        env.close()
        print("Playback ended.")


if __name__ == "__main__":
    main()
