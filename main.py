import pygame

from car import Car
from lap import LapManager
from track import Track


def main() -> None:
    pygame.init()

    track = Track("assets/test_track.png")
    car = Car(50, track.height-50)
    lap_manager = LapManager(track)
    screen = pygame.display.set_mode((track.width, track.height))
    pygame.display.set_caption("AI Car Game")
    hud_font = pygame.font.SysFont(None, 28)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        car.update(track)
        lap_info = lap_manager.update(car.x, car.y)

        screen.fill((0, 0, 0))
        track.draw(screen)
        car.draw(screen)

        lap_text = hud_font.render(f"Laps: {lap_info['lap_count']}", True, (255, 255, 255))
        checkpoint_text = hud_font.render(
            f"Checkpoints: {lap_info['crossed_checkpoints']}/{lap_info['total_checkpoints']}",
            True,
            (255, 255, 255),
        )
        screen.blit(lap_text, (12, 10))
        screen.blit(checkpoint_text, (12, 38))

        pygame.display.flip()
        clock.tick(240)

    pygame.quit()


if __name__ == "__main__":
    main()
