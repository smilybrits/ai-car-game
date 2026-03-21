import pygame

from car import Car
from lap import LapManager
from track import Track


def create_car_at_spawn(track: Track) -> Car:
    """Create a new car using the track-derived spawn pose."""
    spawn_x, spawn_y, spawn_angle = track.get_spawn_pose()
    car = Car(spawn_x, spawn_y)
    car.angle = spawn_angle
    return car


def draw_sensor_rays(screen: pygame.Surface, sensor_debug_rays: list[dict[str, object]]) -> None:
    """Draw sensor rays and endpoints for the current car pose."""
    for ray in sensor_debug_rays:
        start = ray["start"]
        end = ray["end"]
        pygame.draw.line(screen, (0, 220, 255), start, end, 2)
        pygame.draw.circle(screen, (255, 255, 0), (int(end[0]), int(end[1])), 3)


def draw_finish_screen(
    screen: pygame.Surface,
    hud_font: pygame.font.Font,
    lap_info: dict[str, object],
    mouse_pos: tuple[int, int],
) -> pygame.Rect:
    """Render the end-of-race summary once target laps are completed."""
    screen.fill((20, 20, 20))

    title_font = pygame.font.SysFont(None, 56)
    title = title_font.render("Race Complete", True, (255, 255, 255))
    laps_text = hud_font.render(
        f"Laps Completed: {lap_info['lap_count']}/{lap_info['laps_to_finish']}",
        True,
        (220, 220, 220),
    )
    total_time_text = hud_font.render(f"Total Time: {lap_info['total_time_text']}", True, (220, 220, 220))
    fastest_lap_text = hud_font.render(
        f"Fastest Lap: {lap_info['fastest_lap_text']}",
        True,
        (220, 220, 220),
    )

    center_x = screen.get_width() // 2
    start_y = screen.get_height() // 2 - 90

    button_width = 180
    button_height = 46
    button_rect = pygame.Rect(0, 0, button_width, button_height)
    button_rect.center = (center_x, start_y + 190)
    hover = button_rect.collidepoint(mouse_pos)
    button_color = (85, 150, 90) if hover else (70, 120, 75)

    pygame.draw.rect(screen, button_color, button_rect, border_radius=6)
    pygame.draw.rect(screen, (230, 230, 230), button_rect, width=2, border_radius=6)
    retry_text = hud_font.render("Retry", True, (255, 255, 255))

    screen.blit(title, title.get_rect(center=(center_x, start_y)))
    screen.blit(laps_text, laps_text.get_rect(center=(center_x, start_y + 60)))
    screen.blit(total_time_text, total_time_text.get_rect(center=(center_x, start_y + 95)))
    screen.blit(fastest_lap_text, fastest_lap_text.get_rect(center=(center_x, start_y + 130)))
    screen.blit(retry_text, retry_text.get_rect(center=button_rect.center))

    return button_rect


def main() -> None:
    pygame.init()

    track = Track("assets/Track.png")
    try:
        car = create_car_at_spawn(track)
    except ValueError as error:
        pygame.quit()
        raise RuntimeError(str(error)) from error

    lap_manager = LapManager(track)
    screen = pygame.display.set_mode((track.width, track.height))
    pygame.display.set_caption("AI Car Game")
    hud_font = pygame.font.SysFont(None, 28)

    clock = pygame.time.Clock()
    running = True
    lap_info = lap_manager.get_status()
    retry_button_rect = pygame.Rect(0, 0, 0, 0)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and lap_info["race_finished"]
                and retry_button_rect.collidepoint(event.pos)
            ):
                lap_manager.reset()
                car = create_car_at_spawn(track)
                lap_info = lap_manager.get_status()

        if not lap_info["race_finished"]:
            keys = pygame.key.get_pressed()
            accelerating = keys[pygame.K_UP] and not keys[pygame.K_DOWN]

            car.update(track)
            car.get_sensor_readings(track)
            lap_info = lap_manager.update(car.x, car.y, car.speed, accelerating)

        if lap_info["race_finished"]:
            retry_button_rect = draw_finish_screen(screen, hud_font, lap_info, pygame.mouse.get_pos())
        else:
            screen.fill((0, 0, 0))
            track.draw(screen)
            draw_sensor_rays(screen, car.sensor_debug_rays)
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
