import pygame

from car import Car
from lap import LapManager
from track import Track


def main() -> None:
    pygame.init()

    track = Track("assets/test_track.png")
    try:
        spawn_x, spawn_y, spawn_angle = track.get_spawn_pose()
    except ValueError as error:
        pygame.quit()
        raise RuntimeError(str(error)) from error

    car = Car(spawn_x, spawn_y)
    car.angle = spawn_angle
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

        keys = pygame.key.get_pressed()
        accelerating = keys[pygame.K_UP] and not keys[pygame.K_DOWN]

        car.update(track)
        lap_info = lap_manager.update(car.x, car.y, car.speed, accelerating)

        screen.fill((0, 0, 0))
        track.draw(screen)
        car.draw(screen)

        lap_text = hud_font.render(f"Laps: {lap_info['lap_count']}", True, (255, 255, 255))
        checkpoint_text = hud_font.render(
            f"Checkpoints: {lap_info['crossed_checkpoints']}/{lap_info['total_checkpoints']}",
            True,
            (255, 255, 255),
        )
        total_time_text = hud_font.render(f"Total: {lap_info['total_time_text']}", True, (255, 255, 255))
        current_lap_text = hud_font.render(
            f"Current Lap: {lap_info['current_lap_time_text']}",
            True,
            (255, 255, 255),
        )
        fastest_lap_text = hud_font.render(
            f"Fastest Lap: {lap_info['fastest_lap_text']}",
            True,
            (255, 255, 255),
        )
        screen.blit(lap_text, (12, 10))
        screen.blit(checkpoint_text, (12, 38))
        screen.blit(total_time_text, (12, 66))
        screen.blit(current_lap_text, (12, 94))
        screen.blit(fastest_lap_text, (12, 122))

        pygame.display.flip()
        clock.tick(240)

    pygame.quit()


if __name__ == "__main__":
    main()
