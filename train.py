"""Milestone 5 training entrypoint using Stable-Baselines3 PPO."""

from __future__ import annotations

import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import PPO

from env import CarRacingEnv
from logger import TrainingLogger


class SB3CarRacingEnv(gym.Env):
    """Small adapter that exposes CarRacingEnv with a Gymnasium-compatible API."""

    metadata = {"render_modes": []}

    def __init__(self, logger: TrainingLogger | None = None) -> None:
        super().__init__()
        self._env = CarRacingEnv(headless=True)
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
    total_timesteps = 10_000

    print("Creating headless car racing environment...")
    env = SB3CarRacingEnv()
    environment_settings = {
        "headless": env._env.headless,
        "max_steps": env._env.max_steps,
        "max_stuck_steps": env._env.max_stuck_steps,
        "track_path": str(env._env.track_path),
    }
    estimated_episodes = int(math.ceil(total_timesteps / env._env.max_steps))
    logger = TrainingLogger(
        environment_settings=environment_settings,
        total_episodes_planned=estimated_episodes,
    )
    env.logger = logger
    print(f"Logging run data to: {logger.run_path}")

    try:
        print(f"Starting PPO training for {total_timesteps} timesteps...")
        model = PPO("MlpPolicy", env, verbose=1)
        model.learn(total_timesteps=total_timesteps)

        model_path = "ppo_car_model"
        model.save(model_path)

        print(f"Training finished. Model saved to '{model_path}'.")
        print(f"Run data saved in '{logger.run_path}'.")
    finally:
        logger.finalize()
        env.close()
