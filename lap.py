"""Lap and checkpoint progress tracking using event-based line crossings."""

from __future__ import annotations

from dataclasses import dataclass, field

from track import Track


@dataclass
class LapState:
    """Mutable lap progress state for a single play session."""

    lap_started: bool = False
    lap_count: int = 0
    crossed_checkpoints: set[int] = field(default_factory=set)


class LapManager:
    """Track event-based crossings and lap completion from car position."""

    def __init__(self, track: Track) -> None:
        self.track = track
        self.state = LapState()
        self.total_checkpoints = len(track.get_checkpoint_regions())

        self._was_on_start_finish = False
        self._last_checkpoint_id: int | None = None

    def update(self, x: float, y: float) -> dict[str, object]:
        """Update lap state from current car position and return frame events."""
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

        if self.state.lap_started and entered_checkpoint:
            checkpoint_crossed_id = current_checkpoint_id
            self.state.crossed_checkpoints.add(current_checkpoint_id)

        self._was_on_start_finish = on_start_finish
        self._last_checkpoint_id = current_checkpoint_id

        return {
            "entered_start_finish": entered_start_finish,
            "entered_checkpoint": entered_checkpoint,
            "checkpoint_id": checkpoint_crossed_id,
            "lap_completed": lap_completed,
            "lap_count": self.state.lap_count,
            "crossed_checkpoints": len(self.state.crossed_checkpoints),
            "total_checkpoints": self.total_checkpoints,
            "lap_started": self.state.lap_started,
        }

    def _all_checkpoints_crossed(self) -> bool:
        """Return True when all known checkpoints are complete for the current lap."""
        return len(self.state.crossed_checkpoints) >= self.total_checkpoints
