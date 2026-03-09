# ai-car-game
Machine learning car racing simulator built in Python using Pygame.

## Milestone 1 status

- Added `track.py` with a `Track` class for PNG mask loading.
- White pixels (`255, 255, 255`) are treated as drivable road.
- Black and non-white pixels are treated as walls.
- Out-of-bounds coordinates are treated as walls.

### Implemented API

- `Track(image_path: str)` loads the image and stores `surface`, `width`, and `height`.
- `is_road(x: float, y: float) -> bool` checks whether a point is drivable.
- `draw(screen)` draws the track at `(0, 0)`.

### Current runnable entry point

- Added `main.py` for the Milestone 1 display loop.
- `main.py` initializes pygame, loads `Track("assets/track.png")`, opens a window sized from the track, draws every frame, handles quit, and caps at 60 FPS.

### Car module (Milestone 1)

- Added `car.py` with a basic `Car` class.
- `Car(x, y)` stores position and initializes `angle = 0` and `speed = 0`.
- `update()` exists as a placeholder for future physics work.
- `draw(screen)` renders a centered red rectangle (`20 x 10`) using `pygame.draw.rect`.

### Car rendering

- `main.py` now imports the `Car` class.
- A car instance is created at the center of the track.
- The game loop now calls `car.update()` every frame.
- The car is drawn after the track using `car.draw(screen)`.
