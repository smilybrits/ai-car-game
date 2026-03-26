"""Milestone 5 training entrypoint using Stable-Baselines3 PPO."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO

from env import CarRacingEnv
from logger import TrainingLogger
from reward_utils import load_reward_config, load_reward_config_by_name


MAX_TRAINING_TIME = 30
TRAINING_CHUNK_TIMESTEPS = 10_000
DEFAULT_REWARD_NAME = "baseline"


class SB3CarRacingEnv(gym.Env):
    """Small adapter that exposes CarRacingEnv with a Gymnasium-compatible API."""

    metadata = {"render_modes": []}

    def __init__(
        self,
        logger: TrainingLogger | None = None,
        reward_config: dict[str, float] | None = None,
    ) -> None:
        super().__init__()
        self._env = CarRacingEnv(headless=True, reward_config=reward_config)
        self.logger = logger
        self._episode_id = 1
        self._episode_step_id = 0
        self._episode_reward = 0.0

        # Action format: [steer, throttle, brake]
        self.action_space = spaces.Box(
            low=np.array([-1.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )

        # Observation format: 7 normalized sensor distances + normalized speed.
        self.observation_space = spaces.Box(
            low=np.array([0.0] * 7 + [-1.0], dtype=np.float32),
            high=np.array([1.0] * 7 + [1.0], dtype=np.float32),
            dtype=np.float32,
        )

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        del options
        super().reset(seed=seed)
        observation = np.array(self._env.reset(seed=seed), dtype=np.float32)
        return observation, {}

    def step(self, action):
        steer, throttle, brake = np.asarray(action, dtype=np.float32).tolist()
        observation, reward, done, info = self._env.step([steer, throttle, brake])

        # The base env exposes a single done flag. Map it to Gymnasium semantics.
        terminated = bool(info.get("lap_complete", False))
        truncated = bool(done and not terminated)

        self._episode_step_id += 1
        self._episode_reward += float(reward)

        if self.logger is not None:
            self.logger.log_step(
                episode_id=self._episode_id,
                step_id=self._episode_step_id,
                observation=observation,
                steer=steer,
                throttle=throttle,
                brake=brake,
                reward=float(reward),
                done=bool(done),
                car_x=float(info.get("x", 0.0)),
                car_y=float(info.get("y", 0.0)),
                speed=float(info.get("speed", 0.0)),
            )

        if done and self.logger is not None:
            if terminated:
                done_reason = "lap_complete"
            elif bool(info.get("collision", False)):
                done_reason = "crash"
            else:
                done_reason = "max_steps"

            self.logger.log_episode(
                episode_id=self._episode_id,
                total_reward=self._episode_reward,
                total_steps=self._episode_step_id,
                done_reason=done_reason,
                lap_completed=terminated,
            )

            self._episode_id += 1
            self._episode_step_id = 0
            self._episode_reward = 0.0

        return np.array(observation, dtype=np.float32), float(reward), terminated, truncated, info

    def close(self) -> None:
        self._env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PPO car models with reward configurations.")
    parser.add_argument(
        "--reward-config",
        type=str,
        default=None,
        help="Path to a reward configuration JSON file.",
    )
    parser.add_argument(
        "--reward-name",
        type=str,
        default=DEFAULT_REWARD_NAME,
        help="Reward config name from reward_configs/<name>.json (ignored if --reward-config is set).",
    )
    args = parser.parse_args()

    if args.reward_config:
        reward_config_path = Path(args.reward_config)
        reward_config = load_reward_config(reward_config_path)
    else:
        reward_config, reward_config_path = load_reward_config_by_name(args.reward_name)

    reward_name = str(reward_config["name"])
    model_dir = Path("models") / reward_name
    model_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_model_path = model_dir / "ppo_car_model"
    final_model_path = model_dir / "ppo_car_model_final"

    print("Creating headless car racing environment...")
    env = SB3CarRacingEnv(reward_config=reward_config)
    environment_settings = {
        "headless": env._env.headless,
        "max_steps": env._env.max_steps,
        "max_stuck_steps": env._env.max_stuck_steps,
        "track_path": str(env._env.track_path),
        "max_training_time_seconds": MAX_TRAINING_TIME,
        "training_chunk_timesteps": TRAINING_CHUNK_TIMESTEPS,
        "reward_config_name": reward_name,
        "reward_config_path": str(reward_config_path),
        "reward_config": reward_config,
    }

    logger = TrainingLogger(
        base_dir=str(Path("data") / reward_name),
        environment_settings=environment_settings,
        total_episodes_planned=0,
    )
    env.logger = logger
    print(f"Using reward config '{reward_name}' from '{reward_config_path}'.")
    print(f"Logging run data to: {logger.run_path}")
    print(f"Saving models to: {model_dir}")
    model = PPO("MlpPolicy", env, verbose=1)
    start_time = time.time()
    loop_count = 0

    try:
        print(f"Starting PPO training for {MAX_TRAINING_TIME} seconds...")

        while True:
            current_time = time.time()
            elapsed_seconds = current_time - start_time
            remaining_seconds = MAX_TRAINING_TIME - elapsed_seconds

            if remaining_seconds <= 0:
                print("Configured training duration reached.")
                break

            loop_count += 1
            print(
                f"[Loop {loop_count}] "
                f"Elapsed: {elapsed_seconds:.1f}s | "
                f"Remaining: {remaining_seconds:.1f}s"
            )

            model.learn(
                total_timesteps=TRAINING_CHUNK_TIMESTEPS,
                reset_num_timesteps=False,
            )
            model.save(str(checkpoint_model_path))
            print(f"Checkpoint saved to '{checkpoint_model_path}.zip'.")
    except KeyboardInterrupt:
        print("Training interrupted by user (KeyboardInterrupt).")
    finally:
        model.save(str(final_model_path))
        print(f"Final model saved to '{final_model_path}.zip'.")
        print(f"Run data saved in '{logger.run_path}'.")
        logger.finalize()
        env.close()
