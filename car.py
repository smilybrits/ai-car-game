import pygame
import math


class Car:
    """Simple top-down car model for Milestone 1 keyboard driving."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.angle = 75
        self.speed = 0.0
        self.sensor_relative_angles = tuple(math.radians(angle) for angle in (-90, -45, -20, 0, 20, 45, 90))
        self.sensor_max_distance = 140.0
        self.sensor_readings = [1.0] * len(self.sensor_relative_angles)
        self.sensor_debug_rays: list[dict[str, object]] = []

        # Tuned for smooth, predictable Milestone 1 movement.
        self.forward_acceleration = 0.01
        self.reverse_acceleration = 0.075
        self.brake_deceleration = 0.10
        self.friction = 0.02
        self.rotation_speed = 0.05
        self.max_forward_speed = 5
        self.max_reverse_speed = -2.5
        self.turn_min_speed = 0.05
        self.collision_bump_distance = 12.0
        self.collision_speed_factor = 0.3

    def update(self, track) -> None:
        """Update speed, heading, and position from keyboard input."""
        keys = pygame.key.get_pressed()

        up_pressed = keys[pygame.K_UP]
        down_pressed = keys[pygame.K_DOWN]

        # Longitudinal speed control.
        if up_pressed and not down_pressed:
            if self.speed < 0.0:
                self.speed = min(0.0, self.speed + self.brake_deceleration)
            else:
                self.speed += self.forward_acceleration
        elif down_pressed and not up_pressed:
            if self.speed > 0.0:
                self.speed = max(0.0, self.speed - self.brake_deceleration)
            else:
                self.speed -= self.reverse_acceleration
        else:
            # Apply friction toward zero without crossing past it.
            if self.speed > 0.0:
                self.speed = max(0.0, self.speed - self.friction)
            elif self.speed < 0.0:
                self.speed = min(0.0, self.speed + self.friction)

        self.speed = max(self.max_reverse_speed, min(self.speed, self.max_forward_speed))

        # Keep steering stable: reduced turning response when almost stopped.
        turn_multiplier = 1.0 if abs(self.speed) >= self.turn_min_speed else 0.35
        proposed_angle = self.angle
        if keys[pygame.K_LEFT]:
            proposed_angle -= self.rotation_speed * turn_multiplier
        if keys[pygame.K_RIGHT]:
            proposed_angle += self.rotation_speed * turn_multiplier

        # Rotation check: only apply angle if rotated footprint stays on road.
        if self._is_footprint_on_road(track, self.x, self.y, proposed_angle):
            self.angle = proposed_angle

        next_x = self.x + math.cos(self.angle) * self.speed
        next_y = self.y + math.sin(self.angle) * self.speed

        can_move = self._is_footprint_on_road(track, next_x, next_y, self.angle)

        if can_move:
            self.x = next_x
            self.y = next_y
        else:
            move_dx = next_x - self.x
            move_dy = next_y - self.y
            move_length = math.hypot(move_dx, move_dy)

            if move_length > 0.0:
                bump_x = self.x - (move_dx / move_length) * self.collision_bump_distance
                bump_y = self.y - (move_dy / move_length) * self.collision_bump_distance
                can_bump = self._is_footprint_on_road(track, bump_x, bump_y, self.angle)

                if can_bump:
                    self.x = bump_x
                    self.y = bump_y

            self.speed *= self.collision_speed_factor

            if abs(self.speed) < 0.01:
                self.speed = 0.0

    def _is_footprint_on_road(self, track, center_x: float, center_y: float, angle: float) -> bool:
        """Return True only when all collision points are on drivable track."""
        collision_points = self._get_collision_points(center_x, center_y, angle)
        return all(track.is_road(point_x, point_y) for point_x, point_y in collision_points)

    def _get_collision_points(self, center_x: float, center_y: float, angle: float) -> list[tuple[float, float]]:
        """Return rotated footprint points used for track-mask collision checks."""
        # Front/rear points plus side points give better edge and corner blocking.
        local_points = [
            (12.0, 0.0),   # front tip
            (7.0, -4.5),   # front-left
            (7.0, 4.5),    # front-right
            (0.0, -6.0),   # mid-left
            (0.0, 6.0),    # mid-right
            (-8.0, -7.0),  # rear-left
            (-8.0, 7.0),   # rear-right
        ]

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        world_points: list[tuple[float, float]] = []

        for local_x, local_y in local_points:
            world_x = center_x + (local_x * cos_a - local_y * sin_a)
            world_y = center_y + (local_x * sin_a + local_y * cos_a)
            world_points.append((world_x, world_y))

        return world_points

    def get_sensor_readings(self, track) -> list[float]:
        """Return 7 normalized sensor distances and cache ray endpoints for debug drawing."""
        readings: list[float] = []
        debug_rays: list[dict[str, object]] = []

        for relative_angle in self.sensor_relative_angles:
            sensor_angle = self.angle + relative_angle
            distance = track.raycast((self.x, self.y), sensor_angle, self.sensor_max_distance, step=1.0)
            normalized_distance = max(0.0, min(1.0, distance / self.sensor_max_distance))
            end_x = self.x + math.cos(sensor_angle) * distance
            end_y = self.y + math.sin(sensor_angle) * distance

            readings.append(normalized_distance)
            debug_rays.append(
                {
                    "start": (self.x, self.y),
                    "end": (end_x, end_y),
                    "distance": distance,
                    "normalized": normalized_distance,
                }
            )

        self.sensor_readings = readings
        self.sensor_debug_rays = debug_rays
        return list(readings)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the car as a rotated rectangle with colored front and back halves."""
        car_width = 20
        car_height = 10
        half_width = car_width // 2

        car_surface = pygame.Surface((car_width, car_height), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, (255, 0, 0), (0, 0, half_width, car_height))
        pygame.draw.rect(car_surface, (0, 255, 0), (half_width, 0, car_width - half_width, car_height))

        rotated_surface = pygame.transform.rotate(car_surface, -math.degrees(self.angle))
        rotated_rect = rotated_surface.get_rect(center=(self.x, self.y))
        screen.blit(rotated_surface, rotated_rect)
