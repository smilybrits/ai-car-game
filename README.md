# ai-car-game
Machine learning car racing simulator built in Python using Pygame.

## Milestone 1 status

- Added `track.py` with a `Track` class for PNG mask loading.
- White pixels (`255, 255, 255`) are treated as drivable road.
- Black and non-white pixels are treated as walls.
- Out-of-bounds coordinates are treated as walls.
- Added keyboard-controlled movement to the `Car` class.
- Milestone 1 now includes a playable moving car.
- Updated car visuals to a direction-indicating triangle.
- Improved movement logic for smooth and stable speed behavior.

### Implemented API

- `Track(image_path: str)` loads the image and stores `surface`, `width`, and `height`.
- `is_road(x: float, y: float) -> bool` checks whether a point is drivable.
- `draw(screen)` draws the track at `(0, 0)`.

### Current runnable entry point

- Added `main.py` for the Milestone 1 display loop.
- `main.py` initializes pygame, loads `Track("assets/track.png")`, opens a window sized from the track, draws every frame, handles quit, and caps at 60 FPS.

### Car module (Milestone 1)

- Added `car.py` with a basic `Car` class and simple movement physics.
- `Car(x, y)` stores position and initializes `x`, `y`, `angle`, and `speed`.
- `update()` reads keyboard state with `pygame.key.get_pressed()`.
- Arrow keys control the car:
	- `UP`: accelerate forward
	- `DOWN`: accelerate backward / brake into reverse
	- `LEFT`: rotate left
	- `RIGHT`: rotate right
- Movement uses `math.cos(angle)` and `math.sin(angle)` with speed.
- Simple constants are included in `car.py` for forward acceleration, reverse acceleration, braking deceleration, rotation speed, max forward speed, max reverse speed, and friction.
- Forward and reverse speed are clamped consistently every frame.
- Friction now slows the car smoothly toward zero without overshooting.
- `draw(screen)` renders a centered red triangle using `pygame.draw.polygon`.
- The triangle rotates from `self.angle`, so the front of the car is visually clear.

### Car rendering

- `main.py` now imports the `Car` class.
- A car instance is created at the center of the track.
- The game loop now calls `car.update()` every frame.
- The car is drawn after the track using `car.draw(screen)`.

### Controls

- `UP` / `DOWN` to change speed
- `LEFT` / `RIGHT` to steer

### Movement stability update

- Car movement logic was improved for smoother acceleration and deceleration.
- Speed now increases and decreases smoothly with clearer forward/reverse behavior.
- Forward and reverse speed limits are clamped consistently.
- Friction now slows the car down smoothly without sudden jumps.

### Visual update (orientation)

- The car now has a triangle shape instead of a rectangle.
- The triangle rotates based on the car angle.
- The front of the car is now visually identifiable.
- This improves player control and usability.
