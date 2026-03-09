"""Track loading and road-mask queries for Milestone 1."""

from __future__ import annotations

import pygame


class Track:
    """Load a PNG track mask and expose road lookups."""

    def __init__(self, image_path: str) -> None:
        """Load the track image and cache its dimensions."""
        self.surface = pygame.image.load(image_path)
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()

    def is_road(self, x: float, y: float) -> bool:
        """Return True when the queried pixel is a white road pixel."""
        pixel_x = int(x)
        pixel_y = int(y)

        if pixel_x < 0 or pixel_x >= self.width or pixel_y < 0 or pixel_y >= self.height:
            return False

        r, g, b, *_ = self.surface.get_at((pixel_x, pixel_y))
        return (r, g, b) == (255, 255, 255)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the track at the top-left corner."""
        screen.blit(self.surface, (0, 0))
