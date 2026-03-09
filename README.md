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
- Added basic track-mask collision so the car respects road boundaries.
- Improved collision accuracy with multiple rotating footprint points.
- Added bump-away wall response to reduce wall-sticking.
- Added rotation-aware collision checks near walls.

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
- `update(track)` reads keyboard state with `pygame.key.get_pressed()` and checks movement against the track mask.
- Arrow keys control the car:
	- `UP`: accelerate forward
	- `DOWN`: accelerate backward / brake into reverse
	- `LEFT`: rotate left
	- `RIGHT`: rotate right
- Movement uses `math.cos(angle)` and `math.sin(angle)` with speed.
- Simple constants are included in `car.py` for forward acceleration, reverse acceleration, braking deceleration, rotation speed, max forward speed, max reverse speed, and friction.
- Forward and reverse speed are clamped consistently every frame.
- Friction now slows the car smoothly toward zero without overshooting.
- The car now checks multiple footprint points with `track.is_road(...)` before applying movement.
- On collision, the car is pushed slightly backward and speed is reduced strongly.
- Rotation is now validated against the track before angle changes are applied.
- `draw(screen)` renders a centered red triangle using `pygame.draw.polygon`.
- The triangle rotates from `self.angle`, so the front of the car is visually clear.

### Car rendering

- `main.py` now imports the `Car` class.
- A car instance is created at the center of the track.
- The game loop now calls `car.update()` every frame.
- The game loop now calls `car.update(track)` every frame.
- The car is drawn after the track using `car.draw(screen)`.

### Track collision update

- The car now respects track boundaries and cannot drive through walls.
- Collision detection uses the PNG track mask via `track.is_road(...)`.
- When the car tries to move off-road, movement is canceled and speed is set to zero.

### Collision accuracy update

- Collision detection now checks multiple points around the car footprint, not only one center point.
- Collision points rotate with the car angle so checks stay aligned with the car orientation.
- This reduces wall clipping, especially near corners and tight edges.

### Collision response update

- The car now bumps away from walls instead of only stopping abruptly.
- Wall collisions push the car slightly backward along the opposite movement direction.
- Collisions significantly reduce speed to punish impacts.
- This helps prevent the car from getting stuck against walls.

### Rotation collision update

- Rotation is now collision-aware, even when turning in place.
- The rotated car footprint is checked before applying angle changes.
- If rotation would overlap a wall, the turn is canceled.
- This reduces cases where the rear of the car gets stuck near walls.

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
