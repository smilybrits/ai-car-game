import pygame


class Car:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0

    def update(self) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        width = 20
        height = 10
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(screen, (255, 0, 0), rect)
