from pathlib import Path

import pygame

from car import Car
from track import Track


class FakePressed:
    def __init__(self, pressed_keys: set[int] | None = None) -> None:
        self._pressed_keys = pressed_keys or set()

    def __getitem__(self, key: int) -> bool:
        return key in self._pressed_keys


def create_track_image(
    file_path: Path,
    width: int,
    height: int,
    road_rects: list[tuple[int, int, int, int]],
) -> Track:
    surface = pygame.Surface((width, height))
    surface.fill((0, 0, 0))

    for rect in road_rects:
        pygame.draw.rect(surface, (255, 255, 255), rect)

    pygame.image.save(surface, str(file_path))
    return Track(str(file_path))


def test_is_wall_returns_true_for_out_of_bounds(tmp_path: Path) -> None:
    track = create_track_image(tmp_path / "bounds.png", 20, 20, [(0, 0, 20, 20)])

    assert track.is_wall(-1, 5) is True
    assert track.is_wall(5, -1) is True
    assert track.is_wall(20, 5) is True
    assert track.is_wall(5, 20) is True


def test_raycast_returns_zero_when_starting_in_wall(tmp_path: Path) -> None:
    track = create_track_image(tmp_path / "wall_start.png", 20, 20, [(10, 10, 5, 5)])

    assert track.raycast((1.0, 1.0), 0.0, 50.0) == 0.0


def test_raycast_returns_larger_distance_on_clear_road(tmp_path: Path) -> None:
    track = create_track_image(tmp_path / "clear_lane.png", 80, 30, [(10, 5, 60, 20)])

    distance = track.raycast((20.0, 15.0), 0.0, 100.0)

    assert distance >= 45.0
    assert distance <= 55.0


def test_car_collision_prevents_moving_into_wall(tmp_path: Path, monkeypatch) -> None:
    track = create_track_image(tmp_path / "collision.png", 60, 60, [(0, 0, 40, 60)])
    car = Car(27.0, 30.0)
    car.angle = 0.0
    car.speed = 5.0

    monkeypatch.setattr(pygame.key, "get_pressed", lambda: FakePressed())

    starting_x = car.x
    car.update(track)

    assert car.x <= starting_x
    assert car.speed < 5.0


def test_car_sensor_readings_return_seven_normalized_values(tmp_path: Path) -> None:
    track = create_track_image(tmp_path / "sensors.png", 80, 80, [(10, 10, 60, 60)])
    car = Car(40.0, 40.0)
    car.angle = 0.0

    readings = car.get_sensor_readings(track)

    assert len(readings) == 7
    assert len(car.sensor_debug_rays) == 7
    assert all(0.0 <= reading <= 1.0 for reading in readings)