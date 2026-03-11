# ai-car-game
Machine learning car racing simulator built in Python using Pygame.

## Milestone 1 status

- Added `track.py` with a `Track` class for PNG mask loading.
- White pixels (`255, 255, 255`) are treated as drivable road.
- Red pixels (`255, 0, 0`) represent the start / finish line.
- Green pixels (`0, 255, 0`) represent checkpoint lines.
- Red and green marker pixels are also treated as drivable road.
- Black and unexpected colors are treated as walls.
- Out-of-bounds coordinates are treated as walls.
- The game scans the PNG and groups connected green pixels into separate checkpoint regions by position.
- Each checkpoint region is stored individually with a stable id and bounding box.
- The red marker area is tracked as the start / finish region.
- Checkpoints can be crossed in any order, but all must be crossed before a lap can count.
- Crossing detection is event-based (entering a region), so standing on a line does not repeatedly trigger progress.
- Live HUD now shows lap count and checkpoint progress.
- Car spawn is now derived automatically from the red start / finish region.
- Spawn selection uses the middle area of the red region, with nearby red-pixel fallback if needed.
- Start-line direction is estimated from a small middle-pixel window on the red region.
- Car spawn angle is set perpendicular to the estimated start-line direction.
- The chosen perpendicular is the one whose forward test point faces drivable track.
- Spawn is safety-validated against road and car footprint points to avoid starting inside walls.
- The game now tracks timing information for the run and laps.
- Timing starts only when the car first accelerates, not when the window opens.
- The HUD shows total run time, current lap time, and fastest completed lap time.
- Fastest lap updates only from valid completed laps.
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
- `get_pixel_color(x: float, y: float) -> tuple[int, int, int] | None` returns pixel RGB or `None` when out of bounds.
- `is_road(x: float, y: float) -> bool` checks whether a point is drivable (white, red, or green).
- `is_start_finish(x: float, y: float) -> bool` checks for exact start / finish marker color (red).
- `is_checkpoint(x: float, y: float) -> bool` checks for exact checkpoint marker color (green).
- `get_start_finish_region()` returns stored metadata for the start / finish region.
- `get_checkpoint_regions()` returns all checkpoint regions with deterministic ids and metadata.
- `get_checkpoint_id_at(x: float, y: float)` returns the checkpoint id under a point, if any.
- `is_point_in_start_finish(x: float, y: float)` checks whether a point lies in the start / finish region.
- `get_region_at(x: float, y: float)` returns a unified region query result.
- `get_start_finish_pixels()` returns sorted red region pixels for deterministic spawn logic.
- `get_spawn_pose()` returns `(spawn_x, spawn_y, spawn_angle)` derived from the red start line.
- `draw(screen)` draws the track at `(0, 0)`.

### Lap and checkpoint progression

- Added `lap.py` with `LapManager` for checkpoint progress and lap counting.
- Lap tracking starts on the first red-line crossing event.
- A lap is counted only when the red line is crossed again after all checkpoint ids have been crossed in the current lap.
- Checkpoint completion is reset only after a lap is completed.
- Re-entering a line can generate a new crossing event, but already completed checkpoints stay completed for the current lap.
- `LapManager` now also handles run/lap timing state.
- Timing uses `mm:ss.xx` formatting and shows `--:--.--` for fastest lap until the first valid completion.

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
