import pygame
import math


class Car:
    """Simple top-down car model for Milestone 1 keyboard driving."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.angle = 0.0
        self.speed = 0.0

        # Tuned for smooth, predictable Milestone 1 movement.
        self.forward_acceleration = 0.14
        self.reverse_acceleration = 0.05
        self.brake_deceleration = 0.10
        self.friction = 0.08
        self.rotation_speed = 0.05
        self.max_forward_speed = 9
        self.max_reverse_speed = -2.5
        self.turn_min_speed = 0.05

    def update(self) -> None:
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
        if keys[pygame.K_LEFT]:
            self.angle -= self.rotation_speed * turn_multiplier
        if keys[pygame.K_RIGHT]:
            self.angle += self.rotation_speed * turn_multiplier

        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the car as a rotated triangle with a clear front point."""
        # Local triangle points around the car center: front, rear-left, rear-right.
        local_points = [
            (12.0, 0.0),
            (-8.0, -7.0),
            (-8.0, 7.0),
        ]

        world_points = []
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        for px, py in local_points:
            rotated_x = px * cos_a - py * sin_a
            rotated_y = px * sin_a + py * cos_a
            world_points.append((self.x + rotated_x, self.y + rotated_y))

        pygame.draw.polygon(screen, (255, 0, 0), world_points)
