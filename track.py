"""Track loading, road queries, and marker-region detection."""

from __future__ import annotations

from collections import deque

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
