"""Run logger for Milestone 6 data capture."""

from __future__ import annotations

from datetime import datetime
import csv
import json
from pathlib import Path


class TrainingLogger:
    """Persist step, episode, and run metadata for each training execution."""

    def __init__(
        self,
        base_dir: str = "data",
        environment_settings: dict[str, object] | None = None,
        total_episodes_planned: int = 0,
    ) -> None:
        self.base_path = Path(base_dir)
        self.run_path = self._create_run_directory()
        self.steps_path = self.run_path / "steps.csv"
        self.episodes_path = self.run_path / "episodes.json"
        self.metadata_path = self.run_path / "metadata.json"

        self._episode_summaries: list[dict[str, object]] = []

        self._steps_file = self.steps_path.open("w", newline="", encoding="utf-8")
        self._steps_writer = csv.DictWriter(
            self._steps_file,
            fieldnames=[
                "episode_id",
                "step_id",
                "observation",
                "steer",
                "throttle",
                "brake",
                "reward",
                "done",
                "car_x",
                "car_y",
                "speed",
            ],
        )
        self._steps_writer.writeheader()
        self._steps_file.flush()

        self.metadata: dict[str, object] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "environment_settings": environment_settings or {},
            "total_episodes_planned": int(total_episodes_planned),
        }
        self._write_metadata()

    def log_step(
        self,
        episode_id: int,
        step_id: int,
        observation: list[float],
        steer: float,
        throttle: float,
        brake: float,
        reward: float,
        done: bool,
        car_x: float,
        car_y: float,
        speed: float,
    ) -> None:
        """Write one environment transition to steps.csv."""
        observation_text = "|".join(f"{float(value):.6f}" for value in observation)
        self._steps_writer.writerow(
            {
                "episode_id": int(episode_id),
                "step_id": int(step_id),
                "observation": observation_text,
                "steer": float(steer),
                "throttle": float(throttle),
                "brake": float(brake),
                "reward": float(reward),
                "done": bool(done),
                "car_x": float(car_x),
                "car_y": float(car_y),
                "speed": float(speed),
            }
        )
        self._steps_file.flush()

    def log_episode(
        self,
        episode_id: int,
        total_reward: float,
        total_steps: int,
        done_reason: str,
        lap_completed: bool,
    ) -> None:
        """Store one episode summary in memory until finalize()."""
        self._episode_summaries.append(
            {
                "episode_id": int(episode_id),
                "total_reward": float(total_reward),
                "total_steps": int(total_steps),
                "done_reason": done_reason,
                "lap_completed": bool(lap_completed),
            }
        )

    def finalize(self) -> None:
        """Write final JSON outputs and close resources."""
        with self.episodes_path.open("w", encoding="utf-8") as file:
            json.dump(self._episode_summaries, file, indent=2)

        self._write_metadata()

        if not self._steps_file.closed:
            self._steps_file.close()

    def _write_metadata(self) -> None:
        with self.metadata_path.open("w", encoding="utf-8") as file:
            json.dump(self.metadata, file, indent=2)

    def _create_run_directory(self) -> Path:
        self.base_path.mkdir(parents=True, exist_ok=True)

        run_index = 1
        while True:
            candidate = self.base_path / f"run_{run_index:03d}"
            if not candidate.exists():
                candidate.mkdir(parents=True)
                return candidate
            run_index += 1
