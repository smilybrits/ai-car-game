# ai-car-game
Machine learning car racing simulator built in Python using Pygame.

## Current status

### Milestone 1

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
- The race now ends automatically after 3 valid completed laps.
- When lap 3 is completed, gameplay updates stop and timing is frozen.
- The game displays a finish screen with total time and fastest lap.
- The finish screen now includes a clickable `Retry` button.
- Clicking `Retry` starts a new race without restarting the program.
- Retry resets laps, checkpoints, timers, fastest lap, and finished state.
- On retry, the car respawns on the start line using automatic spawn pose detection.
- Added keyboard-controlled movement to the `Car` class.
- Milestone 1 now includes a playable moving car.
- Updated car visuals to a direction-indicating rectangle.
- Improved movement logic for smooth and stable speed behavior.
- Added basic track-mask collision so the car respects road boundaries.
- Improved collision accuracy with multiple rotating footprint points.
- Added bump-away wall response to reduce wall-sticking.
- Added rotation-aware collision checks near walls.

### Milestone 2

- Added `Track.raycast(...)` for simple pixel-sampled wall-distance checks.
- Added `Track.is_wall(...)` so wall and out-of-bounds checks are explicit.
- Added 7 car sensors using relative angles `[-90, -45, -20, 0, 20, 45, 90]` degrees.
- Sensor readings are normalized to the range `0.0..1.0`.
- Sensor rays are drawn in the playable game as a debug overlay.
- Added headless pytest coverage for wall checks, raycasting, collision behavior, and sensor output length/range.

### Milestone 4

- Added `env.py` with a `CarRacingEnv` wrapper for headless RL-style interaction.
- `CarRacingEnv.reset(seed=None)` returns a stable 8-value observation.
- `CarRacingEnv.step(action)` returns `(obs, reward, done, info)`.
- Observation is exactly 7 normalized sensor values plus 1 normalized speed value.
- Action accepts `steer`, `throttle`, and `brake` with safe clamping.
- Headless mode runs without opening a pygame window.
- The environment reuses the existing track, car, lap, collision, and sensor systems instead of duplicating them.

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
- `is_wall(x: float, y: float) -> bool` checks for walls and treats out-of-bounds as wall.
- `raycast(origin, angle, max_dist, step=1.0) -> float` steps along a ray until it hits a wall or reaches max distance.
- `draw(screen)` draws the track at `(0, 0)`.

### Environment API (Milestone 4)

- `CarRacingEnv(headless=True, track_path=None, max_steps=1000, max_stuck_steps=120)` creates the environment wrapper.
- `reset(seed=None) -> list[float]` resets the simulation and returns the initial observation.
- `step(action) -> (obs, reward, done, info)` advances one simulation step.
- `obs` is exactly 8 values in this order: 7 normalized sensor values, then 1 normalized speed value.
- `action` accepts either a dict with `steer`, `throttle`, `brake` or a 3-item sequence in that order.
- `headless=True` skips window creation while still running physics, laps, and sensors.

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
- `main.py` initializes pygame, loads `Track("assets/Track.png")`, opens a window sized from the track, draws every frame, handles quit, and caps at 60 FPS.

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
- `draw(screen)` renders a centered rotated rectangle using a temporary surface.
- The front half is green and the back half is red, so direction is visually clear.

### Car module (Milestone 2)

- `get_sensor_readings(track)` returns exactly 7 normalized sensor values.
- Sensor directions are derived from the current car heading, so the rays rotate with the car.
- Sensor debug endpoints are cached on the car for the game loop to draw.

### Car rendering

- `main.py` now imports the `Car` class.
- A car instance is created at the center of the track.
- The game loop now calls `car.update()` every frame.
- The game loop now calls `car.update(track)` every frame.
- The car is drawn after the track using `car.draw(screen)`.
- The game now also draws the 7 sensor rays every frame for debugging.

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

- The car is now rendered as a rectangle instead of a triangle.
- The rectangle rotates based on the car angle.
- The front half is green and the back half is red to indicate direction.
- This improves player control and usability.

### Tests

- Added headless pytest tests under `tests/`.
- Tests cover out-of-bounds wall handling, raycast behavior, collision blocking, and 7-value normalized sensor output.

### Run commands

- `python main.py`
- `pytest`
- `python -c "from env import CarRacingEnv; env=CarRacingEnv(headless=True); obs=env.reset(); print(len(obs)); env.close()"`
- `python env.py`
