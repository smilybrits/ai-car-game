"""Gym-style environment wrapper built on the existing game modules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
import math
import random

import pygame

from car import Car
from lap import LapManager
from track import Track


class _PressedState:
    """Minimal pygame key-state replacement for environment-driven control."""

    def __init__(self, pressed_keys: set[int]) -> None:
        self._pressed_keys = pressed_keys

    def __getitem__(self, key: int) -> bool:
        return key in self._pressed_keys


class CarRacingEnv:
    """Simple RL-style wrapper around the current track, car, and lap systems."""

    DEFAULT_REWARD_CONFIG: dict[str, float] = {
        "time_penalty": -0.01,
        "checkpoint_bonus": 1.0,
        "lap_bonus": 5.0,
        "speed_reward_weight": 0.02,
        "collision_penalty": -1.0,
        "stuck_penalty": -0.05,
        "slow_penalty": -0.02,
        "stuck_steps_threshold": 15.0,
        "slow_speed_threshold": 0.05,
        "action_threshold": 0.1,
    }

    def __init__(
        self,
        headless: bool = True,
        track_path: str | None = None,
        max_steps: int = 1000,
        max_stuck_steps: int = 120,
        reward_config: Mapping[str, float] | None = None,
    ) -> None:
        self.headless = headless
        self.max_steps = max_steps
        self.max_stuck_steps = max_stuck_steps
        self.random = random.Random()
        self.reward_config = self._resolve_reward_config(reward_config)

        self._ensure_pygame_ready()
        self.track_path = self._resolve_track_path(track_path)
        self.track = Track(str(self.track_path))

        self.screen: pygame.Surface | None = None
        if not self.headless:
            self.screen = pygame.display.set_mode((self.track.width, self.track.height))
            pygame.display.set_caption("AI Car Game Env")

        self.car = self._create_car_at_spawn()
        self.lap_manager = LapManager(self.track)
        self.step_count = 0
        self.stuck_steps = 0
        self.last_lap_info = self.lap_manager.get_status()

    def reset(self, seed: int | None = None) -> list[float]:
        """Reset the simulation and return the initial 8-value observation."""
        if seed is not None:
            self.random.seed(seed)
            random.seed(seed)

        self.car = self._create_car_at_spawn()
        self.lap_manager.reset()
        self.step_count = 0
        self.stuck_steps = 0
        self.last_lap_info = self.lap_manager.get_status()
        self.car.get_sensor_readings(self.track)

        if not self.headless:
            self._render_frame()

        return self._get_observation()

    def step(self, action) -> tuple[list[float], float, bool, dict[str, object]]:
        """Advance the simulation by one fixed step using a continuous action."""
        validated_action = self._validate_action(action)
        previous_x = self.car.x
        previous_y = self.car.y
        previous_speed = self.car.speed
        previous_lap_info = self.last_lap_info

        self._apply_action(validated_action)
        self.step_count += 1

        moved_distance = math.hypot(self.car.x - previous_x, self.car.y - previous_y)
        accelerating = validated_action["throttle"] > validated_action["brake"] and validated_action["throttle"] > 0.1
        lap_info = self.lap_manager.update(self.car.x, self.car.y, self.car.speed, accelerating)
        self.last_lap_info = lap_info

        collision = self._detect_collision(validated_action, moved_distance, previous_speed)
        self._update_stuck_counter(validated_action, moved_distance)

        observation = self._get_observation()
        reward = self._compute_reward(previous_lap_info, lap_info, validated_action, collision)
        done = self._is_done(lap_info)
        info = {
            "lap_count": lap_info["lap_count"],
            "crossed_checkpoints": lap_info["crossed_checkpoints"],
            "total_checkpoints": lap_info["total_checkpoints"],
            "race_finished": lap_info["race_finished"],
            "lap_complete": bool(lap_info["race_finished"]),
            "collision": collision,
            "stuck_steps": self.stuck_steps,
            "step_count": self.step_count,
            "action": dict(validated_action),
            "x": float(self.car.x),
            "y": float(self.car.y),
            "speed": float(self.car.speed),
        }

        if not self.headless:
            self._render_frame()

        return observation, reward, done, info

    def close(self) -> None:
        """Close any display resources created by the environment."""
        if self.screen is not None:
            pygame.display.quit()
            self.screen = None

    def _resolve_track_path(self, track_path: str | None) -> Path:
        """Resolve and validate the track asset path."""
        if track_path is None:
            candidate = Path(__file__).resolve().parent / "assets" / "Track.png"
        else:
            candidate = Path(track_path)
            if not candidate.is_absolute():
                candidate = Path(__file__).resolve().parent / candidate

        if not candidate.is_file():
            raise FileNotFoundError(f"Track image not found: {candidate}")

        return candidate

    def _ensure_pygame_ready(self) -> None:
        """Initialize pygame once so timing, images, and optional rendering work."""
        if not pygame.get_init():
            pygame.init()

    def _create_car_at_spawn(self) -> Car:
        """Create a car using the existing track-derived spawn pose."""
        spawn_x, spawn_y, spawn_angle = self.track.get_spawn_pose()
        car = Car(spawn_x, spawn_y)
        car.angle = spawn_angle
        return car

    def _resolve_reward_config(self, reward_config: Mapping[str, float] | None) -> dict[str, float]:
        """Merge user reward settings over defaults and coerce to float."""
        resolved = dict(self.DEFAULT_REWARD_CONFIG)
        if reward_config is not None:
            for key, value in reward_config.items():
                if key in resolved:
                    resolved[key] = float(value)
        return resolved

    def _get_observation(self) -> list[float]:
        """Return 7 sensor readings plus 1 signed normalized speed value."""
        sensor_values = self.car.get_sensor_readings(self.track)
        normalized_speed = self._normalize_speed(self.car.speed)
        return sensor_values + [normalized_speed]

    def _normalize_speed(self, speed: float) -> float:
        """Normalize forward and reverse speed into a stable signed range."""
        if speed >= 0.0:
            if self.car.max_forward_speed == 0:
                return 0.0
            return max(0.0, min(1.0, speed / self.car.max_forward_speed))

        if self.car.max_reverse_speed == 0:
            return 0.0

        reverse_limit = abs(self.car.max_reverse_speed)
        return max(-1.0, min(0.0, speed / reverse_limit))

    def _validate_action(self, action) -> dict[str, float]:
        """Validate action structure and clamp values into safe ranges."""
        if isinstance(action, Mapping):
            raw_steer = action.get("steer", 0.0)
            raw_throttle = action.get("throttle", 0.0)
            raw_brake = action.get("brake", 0.0)
        elif isinstance(action, Sequence) and not isinstance(action, (str, bytes)):
            if len(action) != 3:
                raise ValueError("Action sequence must contain exactly 3 values: steer, throttle, brake.")
            raw_steer, raw_throttle, raw_brake = action
        else:
            raise TypeError("Action must be a dict-like object or a 3-item sequence.")

        return {
            "steer": self._clamp_float(raw_steer, -1.0, 1.0),
            "throttle": self._clamp_float(raw_throttle, 0.0, 1.0),
            "brake": self._clamp_float(raw_brake, 0.0, 1.0),
        }

    def _clamp_float(self, value, minimum: float, maximum: float) -> float:
        """Convert to float and clamp into the requested numeric range."""
        numeric_value = float(value)
        return max(minimum, min(maximum, numeric_value))

    def _apply_action(self, action: dict[str, float]) -> None:
        """Map continuous action values onto the current keyboard-driven car update."""
        pressed_keys: set[int] = set()

        if action["steer"] <= -0.1:
            pressed_keys.add(pygame.K_LEFT)
        elif action["steer"] >= 0.1:
            pressed_keys.add(pygame.K_RIGHT)

        if action["throttle"] > action["brake"] and action["throttle"] >= 0.1:
            pressed_keys.add(pygame.K_UP)
        elif action["brake"] > action["throttle"] and action["brake"] >= 0.1:
            pressed_keys.add(pygame.K_DOWN)

        original_get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: _PressedState(pressed_keys)
        try:
            self.car.update(self.track)
        finally:
            pygame.key.get_pressed = original_get_pressed

    def _detect_collision(self, action: dict[str, float], moved_distance: float, previous_speed: float) -> bool:
        """Detect a likely wall hit using attempted motion, low displacement, and speed loss."""
        requested_motion = action["throttle"] > 0.1 or action["brake"] > 0.1
        speed_dropped = abs(self.car.speed) + 0.05 < abs(previous_speed)
        return requested_motion and moved_distance < 0.05 and speed_dropped

    def _update_stuck_counter(self, action: dict[str, float], moved_distance: float) -> None:
        """Track repeated slow or stationary steps when the agent is trying to move."""
        action_threshold = self.reward_config["action_threshold"]
        slow_speed_threshold = self.reward_config["slow_speed_threshold"]
        requested_motion = action["throttle"] > action_threshold or action["brake"] > action_threshold
        if requested_motion and moved_distance < 0.05 and abs(self.car.speed) < slow_speed_threshold:
            self.stuck_steps += 1
        else:
            self.stuck_steps = 0

    def _compute_reward(
        self,
        previous_lap_info: dict[str, object],
        current_lap_info: dict[str, object],
        action: dict[str, float],
        collision: bool,
    ) -> float:
        """Compute a simple reward from race progression, speed, and failure signals."""
        reward = self.reward_config["time_penalty"]

        previous_checkpoints = int(previous_lap_info["crossed_checkpoints"])
        current_checkpoints = int(current_lap_info["crossed_checkpoints"])
        previous_laps = int(previous_lap_info["lap_count"])
        current_laps = int(current_lap_info["lap_count"])

        if current_checkpoints > previous_checkpoints:
            reward += self.reward_config["checkpoint_bonus"] * (current_checkpoints - previous_checkpoints)

        if current_laps > previous_laps:
            reward += self.reward_config["lap_bonus"] * (current_laps - previous_laps)

        reward += self.reward_config["speed_reward_weight"] * max(0.0, self._normalize_speed(self.car.speed))

        if collision:
            reward += self.reward_config["collision_penalty"]

        if self.stuck_steps >= int(self.reward_config["stuck_steps_threshold"]):
            reward += self.reward_config["stuck_penalty"]
        elif abs(self.car.speed) < self.reward_config["slow_speed_threshold"] and (
            action["throttle"] > self.reward_config["action_threshold"]
            or action["brake"] > self.reward_config["action_threshold"]
        ):
            reward += self.reward_config["slow_penalty"]

        return reward

    def _is_done(self, lap_info: dict[str, object]) -> bool:
        """Stop on max steps, repeated stuck state, or race completion."""
        return (
            self.step_count >= self.max_steps
            or self.stuck_steps >= self.max_stuck_steps
            or bool(lap_info["race_finished"])
        )

    def _render_frame(self) -> None:
        """Draw a lightweight debug view when the environment is not headless."""
        if self.screen is None:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return

        self.screen.fill((0, 0, 0))
        self.track.draw(self.screen)

        for ray in self.car.sensor_debug_rays:
            start = ray["start"]
            end = ray["end"]
            pygame.draw.line(self.screen, (0, 220, 255), start, end, 2)
            pygame.draw.circle(self.screen, (255, 255, 0), (int(end[0]), int(end[1])), 3)

        self.car.draw(self.screen)
        pygame.display.flip()


if __name__ == "__main__":
    demo_env = CarRacingEnv(headless=True)
    observation = demo_env.reset(seed=0)
    done = False
    steps = 0

    while steps < 200 and not done:
        random_action = {
            "steer": random.uniform(-1.0, 1.0),
            "throttle": random.uniform(0.0, 1.0),
            "brake": random.uniform(0.0, 1.0),
        }
        observation, reward, done, info = demo_env.step(random_action)
        steps += 1

    print(f"obs_len={len(observation)} steps={steps} done={done}")
    demo_env.close()