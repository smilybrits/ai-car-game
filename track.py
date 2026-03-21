"""Track loading, road queries, and marker-region detection."""

from __future__ import annotations

from collections import deque
import math

import pygame


class Track:
    """Load a PNG track mask and expose road/marker lookups."""

    ROAD_COLOR = (255, 255, 255)
    START_FINISH_COLOR = (255, 0, 0)
    CHECKPOINT_COLOR = (0, 255, 0)

    def __init__(self, image_path: str) -> None:
        """Load the track image, cache dimensions, and scan marker regions."""
        self.surface = pygame.image.load(image_path)
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()

        self._checkpoint_regions: list[dict[str, int | tuple[int, int, int, int]]] = []
        self._start_finish_region: dict[str, int | tuple[int, int, int, int]] | None = None
        self._checkpoint_lookup: dict[tuple[int, int], int] = {}
        self._start_finish_lookup: set[tuple[int, int]] = set()

        self._scan_marker_regions()

    def get_pixel_color(self, x: float, y: float) -> tuple[int, int, int] | None:
        """Return RGB color at integer coordinates, or None when out of bounds."""
        pixel_x = int(x)
        pixel_y = int(y)

        if pixel_x < 0 or pixel_x >= self.width or pixel_y < 0 or pixel_y >= self.height:
            return None

        r, g, b, *_ = self.surface.get_at((pixel_x, pixel_y))
        return (r, g, b)

    def _get_pixel_color_int(self, pixel_x: int, pixel_y: int) -> tuple[int, int, int]:
        """Return RGB color for known in-bounds integer coordinates."""
        r, g, b, *_ = self.surface.get_at((pixel_x, pixel_y))
        return (r, g, b)

    def is_road(self, x: float, y: float) -> bool:
        """Return True for drivable pixels: white road, red, or green markers."""
        color = self.get_pixel_color(x, y)
        if color is None:
            return False

        return color in {
            self.ROAD_COLOR,
            self.START_FINISH_COLOR,
            self.CHECKPOINT_COLOR,
        }

    def is_wall(self, x: float, y: float) -> bool:
        """Return True for walls and out-of-bounds coordinates."""
        return not self.is_road(x, y)

    def raycast(
        self,
        origin: tuple[float, float],
        angle: float,
        max_dist: float,
        step: float = 1.0,
    ) -> float:
        """Step along a ray until a wall is hit or max distance is reached."""
        origin_x, origin_y = origin
        if self.is_wall(origin_x, origin_y):
            return 0.0

        distance = step
        while distance <= max_dist:
            sample_x = origin_x + math.cos(angle) * distance
            sample_y = origin_y + math.sin(angle) * distance
            if self.is_wall(sample_x, sample_y):
                return distance
            distance += step

        return max_dist

    def is_start_finish(self, x: float, y: float) -> bool:
        """Return True only when the queried pixel is the start/finish marker color."""
        return self.get_pixel_color(x, y) == self.START_FINISH_COLOR

    def is_checkpoint(self, x: float, y: float) -> bool:
        """Return True only when the queried pixel is the checkpoint marker color."""
        return self.get_pixel_color(x, y) == self.CHECKPOINT_COLOR

    def get_start_finish_region(self) -> dict[str, int | tuple[int, int, int, int]] | None:
        """Return metadata for the start/finish region, if present."""
        return self._start_finish_region

    def get_checkpoint_regions(self) -> list[dict[str, int | tuple[int, int, int, int]]]:
        """Return metadata for all checkpoint regions in deterministic id order."""
        return list(self._checkpoint_regions)

    def get_checkpoint_id_at(self, x: float, y: float) -> int | None:
        """Return checkpoint id at the queried point, or None if not on a checkpoint."""
        pixel_x = int(x)
        pixel_y = int(y)
        return self._checkpoint_lookup.get((pixel_x, pixel_y))

    def is_point_in_start_finish(self, x: float, y: float) -> bool:
        """Return True when the queried point is inside the start/finish region."""
        pixel_x = int(x)
        pixel_y = int(y)
        return (pixel_x, pixel_y) in self._start_finish_lookup

    def get_region_at(self, x: float, y: float) -> str | tuple[str, int] | None:
        """Return region type at point: start_finish, checkpoint tuple, or None."""
        if self.is_point_in_start_finish(x, y):
            return "start_finish"

        checkpoint_id = self.get_checkpoint_id_at(x, y)
        if checkpoint_id is not None:
            return ("checkpoint", checkpoint_id)

        return None

    def get_start_finish_pixels(self) -> list[tuple[int, int]]:
        """Return start/finish pixels in deterministic sorted order."""
        return sorted(self._start_finish_lookup, key=lambda point: (point[1], point[0]))

    def get_spawn_pose(self) -> tuple[float, float, float]:
        """Return a safe spawn pose (x, y, angle) derived from the red start line."""
        red_pixels = self.get_start_finish_pixels()
        if not red_pixels:
            raise ValueError("Spawn failed: no red start/finish region found in track image.")

        middle_index = len(red_pixels) // 2
        line_angle = self._estimate_start_line_angle(red_pixels)
        ordered_candidates = self._ordered_search_pixels(red_pixels, middle_index)

        for pixel_x, pixel_y in ordered_candidates:
            spawn_x = float(pixel_x)
            spawn_y = float(pixel_y)

            if not self.is_road(spawn_x, spawn_y):
                continue

            angle = self._choose_facing_perpendicular(spawn_x, spawn_y, line_angle)
            if angle is None:
                continue

            if self._is_spawn_safe(spawn_x, spawn_y, angle):
                return (spawn_x, spawn_y, angle)

        raise ValueError(
            "Spawn failed: no safe spawn pose found from the red start/finish region. "
            "Check that the red line is connected to drivable road and not inside walls."
        )

    def _estimate_start_line_angle(self, sorted_pixels: list[tuple[int, int]]) -> float:
        """Estimate start-line angle from a small window around middle pixels."""
        count = len(sorted_pixels)
        window_size = 11 if count >= 11 else (5 if count >= 5 else count)
        middle_index = count // 2
        half = window_size // 2

        start = max(0, middle_index - half)
        end = min(count, start + window_size)
        start = max(0, end - window_size)

        window = sorted_pixels[start:end]
        first_x, first_y = window[0]
        last_x, last_y = window[-1]

        delta_x = last_x - first_x
        delta_y = last_y - first_y
        if delta_x == 0 and delta_y == 0:
            return 0.0

        return math.atan2(delta_y, delta_x)

    def _ordered_search_pixels(
        self,
        sorted_pixels: list[tuple[int, int]],
        middle_index: int,
    ) -> list[tuple[int, int]]:
        """Return pixels ordered from center outward for deterministic fallback search."""
        ordered: list[tuple[int, int]] = []
        used: set[int] = set()
        total = len(sorted_pixels)

        for distance in range(total):
            left = middle_index - distance
            right = middle_index + distance

            if 0 <= left < total and left not in used:
                ordered.append(sorted_pixels[left])
                used.add(left)

            if 0 <= right < total and right not in used:
                ordered.append(sorted_pixels[right])
                used.add(right)

            if len(ordered) == total:
                break

        return ordered

    def _choose_facing_perpendicular(self, x: float, y: float, line_angle: float) -> float | None:
        """Choose perpendicular angle that faces drivable road from spawn point."""
        candidate_a = self._normalize_angle(line_angle + (math.pi / 2.0))
        candidate_b = self._normalize_angle(line_angle - (math.pi / 2.0))

        test_distance = 16.0
        valid_a = self.is_road(x + math.cos(candidate_a) * test_distance, y + math.sin(candidate_a) * test_distance)
        valid_b = self.is_road(x + math.cos(candidate_b) * test_distance, y + math.sin(candidate_b) * test_distance)

        if valid_a and valid_b:
            return min(candidate_a, candidate_b)
        if valid_a:
            return candidate_a
        if valid_b:
            return candidate_b

        return None

    def _is_spawn_safe(self, x: float, y: float, angle: float) -> bool:
        """Validate spawn center and footprint against drivable track pixels."""
        if not self.is_road(x, y):
            return False

        for point_x, point_y in self._get_car_footprint_points(x, y, angle):
            if not self.is_road(point_x, point_y):
                return False

        return True

    def _get_car_footprint_points(self, center_x: float, center_y: float, angle: float) -> list[tuple[float, float]]:
        """Return car collision footprint points at a candidate pose."""
        local_points = [
            (12.0, 0.0),
            (7.0, -4.5),
            (7.0, 4.5),
            (0.0, -6.0),
            (0.0, 6.0),
            (-8.0, -7.0),
            (-8.0, 7.0),
        ]

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        points: list[tuple[float, float]] = []

        for local_x, local_y in local_points:
            world_x = center_x + (local_x * cos_a - local_y * sin_a)
            world_y = center_y + (local_x * sin_a + local_y * cos_a)
            points.append((world_x, world_y))

        return points

    def _normalize_angle(self, angle: float) -> float:
        """Normalize radians to the range [-pi, pi]."""
        return math.atan2(math.sin(angle), math.cos(angle))

    def _scan_marker_regions(self) -> None:
        """Find connected marker regions and build fast point lookup tables."""
        checkpoint_components = self._find_connected_components(self.CHECKPOINT_COLOR)
        start_finish_components = self._find_connected_components(self.START_FINISH_COLOR)

        sorted_checkpoint_components = sorted(
            checkpoint_components,
            key=lambda component: (component["bbox"][1], component["bbox"][0]),
        )

        self._checkpoint_regions = []
        self._checkpoint_lookup = {}
        for index, component in enumerate(sorted_checkpoint_components):
            checkpoint_id = index
            self._checkpoint_regions.append(
                {
                    "id": checkpoint_id,
                    "bbox": component["bbox"],
                    "pixel_count": component["pixel_count"],
                }
            )

            for point in component["pixels"]:
                self._checkpoint_lookup[point] = checkpoint_id

        self._start_finish_region = None
        self._start_finish_lookup = set()
        if start_finish_components:
            sorted_start_components = sorted(
                start_finish_components,
                key=lambda component: component["pixel_count"],
                reverse=True,
            )
            start_component = sorted_start_components[0]
            self._start_finish_region = {
                "id": 0,
                "bbox": start_component["bbox"],
                "pixel_count": start_component["pixel_count"],
            }
            self._start_finish_lookup = set(start_component["pixels"])

    def _find_connected_components(self, target_color: tuple[int, int, int]) -> list[dict[str, object]]:
        """Return connected components for a target color using 8-way adjacency."""
        visited: set[tuple[int, int]] = set()
        components: list[dict[str, object]] = []

        for y in range(self.height):
            for x in range(self.width):
                point = (x, y)
                if point in visited:
                    continue
                if self._get_pixel_color_int(x, y) != target_color:
                    continue

                component = self._collect_component(start_point=point, target_color=target_color, visited=visited)
                components.append(component)

        return components

    def _collect_component(
        self,
        start_point: tuple[int, int],
        target_color: tuple[int, int, int],
        visited: set[tuple[int, int]],
    ) -> dict[str, object]:
        """Collect a single connected component with BFS flood-fill."""
        queue: deque[tuple[int, int]] = deque([start_point])
        visited.add(start_point)

        pixels: set[tuple[int, int]] = set()
        min_x, min_y = start_point
        max_x, max_y = start_point

        while queue:
            x, y = queue.popleft()
            pixels.add((x, y))

            if x < min_x:
                min_x = x
            if y < min_y:
                min_y = y
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y

            for neighbor_x, neighbor_y in self._get_neighbors8(x, y):
                neighbor = (neighbor_x, neighbor_y)
                if neighbor in visited:
                    continue

                visited.add(neighbor)
                if self._get_pixel_color_int(neighbor_x, neighbor_y) == target_color:
                    queue.append(neighbor)

        return {
            "pixels": pixels,
            "bbox": (min_x, min_y, max_x, max_y),
            "pixel_count": len(pixels),
        }

    def _get_neighbors8(self, x: int, y: int) -> list[tuple[int, int]]:
        """Return valid 8-way neighbors for an in-bounds pixel."""
        neighbors: list[tuple[int, int]] = []
        for offset_y in (-1, 0, 1):
            for offset_x in (-1, 0, 1):
                if offset_x == 0 and offset_y == 0:
                    continue

                nx = x + offset_x
                ny = y + offset_y
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append((nx, ny))

        return neighbors

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the track at the top-left corner."""
        screen.blit(self.surface, (0, 0))
