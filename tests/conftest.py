import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def pygame_headless() -> None:
    pygame.init()
    yield
    pygame.quit()