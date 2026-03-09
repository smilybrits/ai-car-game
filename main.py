import pygame

from car import Car
from track import Track


def main() -> None:
    pygame.init()

    track = Track("assets/track.png")
    car = Car(track.width / 2, track.height / 2)
    screen = pygame.display.set_mode((track.width, track.height))
    pygame.display.set_caption("AI Car Game")

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        car.update()
        screen.fill((0, 0, 0))
        track.draw(screen)
        car.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
