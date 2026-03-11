"""Lap and checkpoint progress tracking using event-based line crossings."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from track import Track


@dataclass
class LapState:
    """Mutable lap progress state for a single play session."""

    lap_started: bool = False
    lap_count: int = 0
    crossed_checkpoints: set[int] = field(default_factory=set)
    timer_started: bool = False
    run_start_ms: int | None = None
    current_lap_start_ms: int | None = None
    fastest_lap_ms: int | None = None
    last_completed_lap_ms: int | None = None
    race_finished: bool = False
    final_total_time_ms: int | None = None


class LapManager:
    """Track event-based crossings and lap completion from car position."""

    def __init__(self, track: Track, laps_to_finish: int = 3) -> None:
        self.track = track
        self.state = LapState()
        self.total_checkpoints = len(track.get_checkpoint_regions())
        self.laps_to_finish = laps_to_finish

        self._was_on_start_finish = False
        self._last_checkpoint_id: int | None = None

    def update(self, x: float, y: float, speed: float, accelerating: bool) -> dict[str, object]:
        """Update lap state from current car position and return frame events."""
        now_ms = pygame.time.get_ticks()

        if self.state.race_finished:
            return self._build_info(now_ms, lap_completed=False)

        if not self.state.timer_started and accelerating and speed > 0.05:
            self.state.timer_started = True
            self.state.run_start_ms = now_ms
            self.state.current_lap_start_ms = now_ms

        on_start_finish = self.track.is_point_in_start_finish(x, y)
        current_checkpoint_id = self.track.get_checkpoint_id_at(x, y)

        entered_start_finish = on_start_finish and not self._was_on_start_finish
        entered_checkpoint = (
            current_checkpoint_id is not None and current_checkpoint_id != self._last_checkpoint_id
        )

        checkpoint_crossed_id: int | None = None
        lap_completed = False

        if entered_start_finish:
            if not self.state.lap_started:
                self.state.lap_started = True
                self.state.crossed_checkpoints.clear()
            elif self._all_checkpoints_crossed():
                self.state.lap_count += 1
                self.state.crossed_checkpoints.clear()
                lap_completed = True

                if self.state.timer_started and self.state.current_lap_start_ms is not None:
                    completed_lap_ms = now_ms - self.state.current_lap_start_ms
                    self.state.last_completed_lap_ms = completed_lap_ms

                    if self.state.fastest_lap_ms is None or completed_lap_ms < self.state.fastest_lap_ms:
                        self.state.fastest_lap_ms = completed_lap_ms

                    self.state.current_lap_start_ms = now_ms

                if self.state.lap_count >= self.laps_to_finish:
                    self.state.race_finished = True
                    if self.state.timer_started and self.state.run_start_ms is not None:
                        self.state.final_total_time_ms = now_ms - self.state.run_start_ms
                    else:
                        self.state.final_total_time_ms = 0

        if self.state.lap_started and entered_checkpoint:
            checkpoint_crossed_id = current_checkpoint_id
            self.state.crossed_checkpoints.add(current_checkpoint_id)

        self._was_on_start_finish = on_start_finish
        self._last_checkpoint_id = current_checkpoint_id

        return self._build_info(now_ms, lap_completed=lap_completed)

    def get_status(self) -> dict[str, object]:
        """Return a snapshot of lap and timer state without advancing logic."""
        return self._build_info(pygame.time.get_ticks(), lap_completed=False)

    def reset(self) -> None:
        """Reset race progress and timing state for a fresh run."""
        self.state = LapState()
        self._was_on_start_finish = False
        self._last_checkpoint_id = None

    def _build_info(self, now_ms: int, lap_completed: bool) -> dict[str, object]:
        """Build a consistent state payload for HUD or finish screen rendering."""
        total_elapsed_ms = 0
        if self.state.race_finished:
            total_elapsed_ms = self.state.final_total_time_ms or 0
        elif self.state.timer_started and self.state.run_start_ms is not None:
            total_elapsed_ms = now_ms - self.state.run_start_ms

        current_lap_elapsed_ms = 0
        if (
            not self.state.race_finished
            and self.state.timer_started
            and self.state.current_lap_start_ms is not None
        ):
            current_lap_elapsed_ms = now_ms - self.state.current_lap_start_ms

        return {
            "entered_start_finish": False,
            "entered_checkpoint": False,
            "checkpoint_id": None,
            "lap_completed": lap_completed,
            "lap_count": self.state.lap_count,
            "crossed_checkpoints": len(self.state.crossed_checkpoints),
            "total_checkpoints": self.total_checkpoints,
            "lap_started": self.state.lap_started,
            "timer_started": self.state.timer_started,
            "race_finished": self.state.race_finished,
            "laps_to_finish": self.laps_to_finish,
            "total_time_ms": total_elapsed_ms,
            "current_lap_time_ms": current_lap_elapsed_ms,
            "fastest_lap_ms": self.state.fastest_lap_ms,
            "last_completed_lap_ms": self.state.last_completed_lap_ms,
            "total_time_text": self.format_time_ms(total_elapsed_ms),
            "current_lap_time_text": self.format_time_ms(current_lap_elapsed_ms),
            "fastest_lap_text": self.format_time_ms(self.state.fastest_lap_ms),
        }

    def _all_checkpoints_crossed(self) -> bool:
        """Return True when all known checkpoints are complete for the current lap."""
        return len(self.state.crossed_checkpoints) >= self.total_checkpoints

    @staticmethod
    def format_time_ms(milliseconds: int | None) -> str:
        """Format milliseconds as mm:ss.xx, or placeholder when unavailable."""
        if milliseconds is None:
            return "--:--.--"

        total_centiseconds = max(0, milliseconds // 10)
        minutes = total_centiseconds // 6000
        seconds = (total_centiseconds % 6000) // 100
        centiseconds = total_centiseconds % 100
        return f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
