# .github/copilot-instructions.md
# Repository: ai-car-game
# Purpose: Keep Copilot aligned with the "Car Game - ML" design doc + milestones.
# Read this file before making changes. Follow it strictly.

## 0) High-level goal
Build a 2D top-down car racing game in **Python + Pygame** that becomes a **Gym-style RL environment**.
The track is a **PNG mask** where:
- **White = road**
- **Black = wall**
Collisions and sensors use **pixel sampling** against this mask.

The project must support:
- A playable human-controlled prototype
- Ray-based sensors for observations
- Laps/checkpoints
- `reset()` / `step(action)` environment API
- **Headless mode** (no window / no rendering) for fast training

## 1) Non-negotiable architecture (keep it modular)
Do NOT merge everything into one file. Use these modules:

- `track.py`:
  - Load track mask PNG
  - Provide `is_road(x,y)` / `is_wall(x,y)`
  - Provide `raycast(origin, angle, max_dist, step=...)`
  - Provide optional helpers: checkpoint lines / start position / heading
- `car.py`:
  - Car state (position, heading, speed)
  - Physics update with dt
  - Collision check (sample corners)
  - Sensor reading helper calling Track.raycast
- `lap.py`:
  - Lap logic, checkpoints, lap counting
- `env.py`:
  - Gym-style wrapper with `reset()` and `step(action)`
  - Reward shaping + termination conditions
  - Optional headless operation
- `main.py`:
  - Human-playable game loop + debug overlays

Optional later:
- `assets/` for images
- `tests/` for pytest
- `scripts/` for training runners

## 2) Milestone-driven delivery (build in order)
Only implement one milestone at a time, and keep the code runnable after each milestone.

### Milestone 1 — playable prototype
Definition of done:
- `python main.py` opens a window and you can drive the car with keyboard.
- Track drawn + car drawn.
- Collision with walls works (car stops / slides off wall).
Files typically touched: `track.py`, `car.py`, `main.py`.

### Milestone 2 — sensors
Definition of done:
- Car has ray sensors (e.g., 7 rays) returning normalized distances.
- Debug draw shows rays in the window.
Files touched: `track.py` (raycast), `car.py` (sensor readings), `main.py` (debug).

### Milestone 3 — laps + checkpoints
Definition of done:
- Checkpoints + start/finish line.
- Lap increments only when checkpoints are passed in order.
Files touched: `lap.py` (+ small hooks in `main.py` / `env.py` if needed).

### Milestone 4 — ML environment
Definition of done:
- `env.py` provides `reset()` and `step(action)` with a stable observation.
- Headless mode runs without opening a window.
- A tiny demo script can step random actions for 200 steps without crashing.

Do NOT jump to Milestone 4 before Milestones 1–3 are stable.

## 3) Track mask rules (critical)
- The track is a 2D image mask.
- White pixels = road; black pixels = wall. Treat out-of-bounds as wall.
- Collision: sample car corners (or multiple points) against wall pixels.
- Raycast: step pixel-by-pixel (or small step size) until wall or max distance.

When implementing, keep mask lookup efficient:
- Load mask once.
- Use `pygame.surfarray` or `Surface.get_at` carefully.
- For headless, still load assets but do not open a display window.

## 4) Car physics rules (simple + consistent)
Keep “arcade physics” first. No complex tire models.
- Position (float x,y), heading (radians), speed.
- Acceleration from throttle; deceleration from brake; friction/drag when no input.
- Steering affects heading (scaled by speed).
- Clamp speed to sensible min/max.
- Collision response can be simple:
  - revert movement for the frame OR
  - push back along velocity direction OR
  - zero speed on collision

Do not add fancy physics unless requested.

## 5) Environment API rules (Gym-like)
`env.py` must expose:

- `reset(seed=None) -> obs`
- `step(action) -> (obs, reward, done, info)`

Where:
- `action` is continuous:
  - `steer` in [-1, 1]
  - `throttle` in [0, 1]
  - `brake` in [0, 1]
- `obs` includes:
  - sensor distances (normalized)
  - speed (normalized)
  - optional: heading delta to next checkpoint (keep minimal unless asked)

Headless mode requirements:
- No window creation (no `pygame.display.set_mode`) when headless
- Still runs physics + collisions + sensors
- Rendering calls must be skipped in headless mode

## 6) Reward and termination (keep simple and explainable)
Default reward strategy:
- Positive reward for forward progress along track / reaching checkpoints
- Small penalty for time steps to encourage finishing
- Big penalty for hitting walls or going off-track
- `done=True` when:
  - crash condition (optional)
  - max steps exceeded
  - lap completed (optional depending on training mode)

Always keep reward shaping clearly commented and easy to modify.

## 7) Coding style rules (important)
- Keep code readable for a student-level project (no over-engineering).
- Use clear names: `position`, `heading`, `speed`, `mask_surface`.
- Add docstrings to classes and public methods.
- Use defensive checks:
  - Validate action ranges in `step`
  - Guard against None assets
  - Treat out-of-bounds as wall
- Prefer small functions over long ones.
- Avoid global state (except constants).

## 8) Testing rules (pytest)
As soon as Milestone 2 exists, add `tests/` with `pytest` tests:
Minimum tests to include:
- `Track.is_wall` returns True for out-of-bounds
- `Track.raycast` returns near 0 when starting inside a wall
- `Track.raycast` returns larger distance on clear road region (use a tiny synthetic mask if needed)
- Car collision prevents moving into a wall

Tests must run headless (no window).

## 9) How Copilot should work in this repo
When asked to implement something:
1) Identify which milestone it belongs to.
2) Propose which files will change and why.
3) Implement minimal code to satisfy the milestone definition of done.
4) Provide run instructions (`pip install ...`, `python main.py`, `pytest`).
5) Do not refactor unrelated files.

## 10) Dependency guidelines
Preferred:
- `pygame`
- `numpy` (optional, only if it truly improves mask/sensor performance)
- `pytest` for tests

Do NOT add heavy dependencies unless requested (no torch/tensorflow unless training code is explicitly asked for).

## 11) Run targets (should stay working)
These commands should work during development:
- `python main.py`  (playable demo)
- `pytest`          (tests)
- `python -c "from env import CarRacingEnv; env=CarRacingEnv(headless=True); obs=env.reset(); print(len(obs))"`

(Adjust the env class name if you pick a different one, but keep it consistent.)

# End of instructions