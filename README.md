# AI Car Game – Machine Learning Racing Simulator

---

# 1. Project Overview

This project is a **2D top-down car racing simulator** built in Python using Pygame.

The purpose of the system is to evolve into a **reinforcement learning (RL) training environment** where:

* A human can play and generate driving behaviour
* An AI agent can learn to drive using structured observations
* Model behaviour and outputs are recorded for analysis and improvement

---

# 2. Core Objective (Aligned to Design Doc)

The system must support:

1. A fully playable game
2. A structured simulation environment
3. A Gym-style RL interface
4. Headless training capability
5. **Data capture of model behaviour and performance (Priority 1)**

---

# 3. Core Design Principles

* Simple arcade physics (no complex models)
* Modular architecture (no large combined files)
* Track defined as image mask (white = road, black = wall)
* Sensors instead of vision for ML
* Milestone-driven development
* System must remain runnable at every stage

---

# 4. System Architecture

The system is strictly modular:

* `track.py` → track loading, mask logic, raycasting
* `car.py` → physics, movement, sensors
* `lap.py` → checkpoints and lap logic
* `env.py` → RL environment interface
* `main.py` → playable game loop
* `train.py` → model training
* `play_model.py` → visual playback of a trained model
* `reward_utils.py` → reward config loading and validation
* `reward_configs/` → named reward setup JSON files
* `scripts/train_all_rewards.py` → sequential training runner for all reward configs
* `data/` → model outputs and training data storage

---

# 5. Detailed Implementation Status

This section is the code-aware implementation log for the current repository state.

Status baseline used for this report:

* Source documents found and reviewed in repository:
  * `.github/copilot-instructions.md`
  * `README.md`
  * `DEVELOPMENT_PLAN`
* Documents requested but not found in repository at the time of this update:
  * `DevelopmentPlanDoc.docx`
  * `AI_Prompt_Rules.docx`
  * `Car Game - ML Design Doc.txt`

## 5.1 Current Implementation by Module

### track.py

Exists: Yes.

Key class:

* `Track`

What it currently does:

* Loads PNG track mask and stores width and height.
* Uses color-based semantics:
  * white = road
  * red = start/finish marker
  * green = checkpoint marker
* Treats out-of-bounds as wall through `is_wall()`.
* Provides `is_road()`, `is_wall()`, and `raycast(origin, angle, max_dist, step)`.
* Scans connected components for red and green markers and builds lookup tables.
* Exposes region helpers: checkpoint id at point, start/finish membership, region metadata.
* Derives spawn pose from the red region with safety checks against collision footprint.

Partially implemented or fragile points:

* Marker semantics extend the original white/black mask rule by treating red and green as drivable. This is valid for current lap logic, but should remain explicitly documented in track authoring rules.

Missing relative to strict design expectations:

* No explicit performance optimization using cached pixel arrays; lookups rely on per-pixel surface access.

### car.py

Exists: Yes.

Key class:

* `Car`

What it currently does:

* Stores car state: x, y, angle, speed.
* Implements keyboard-driven arcade physics (acceleration, braking, friction, speed clamps).
* Applies steering with low-speed turn damping.
* Uses multi-point rotated footprint collision checking against track mask.
* Handles collision response with bump-back and speed reduction.
* Implements 7 ray sensors with normalized outputs and debug ray cache.
* Renders the car as a rotated red/green rectangle.

Partially implemented or fragile points:

* Constructor default angle is a hardcoded numeric value and is later overridden by spawn pose in main and env flows. This works today but is easy to misinterpret.

Missing relative to strict design expectations:

* No dt-based physics step parameter; update is frame-rate dependent.

### lap.py

Exists: Yes.

Key structures:

* `LapState` dataclass
* `LapManager`

What it currently does:

* Tracks race lifecycle: lap count, crossed checkpoints, timers, fastest lap, race completion.
* Detects entry onto start/finish and checkpoints using region lookups from track.
* Requires all checkpoints to be crossed before a lap can complete.
* Supports race completion after configurable number of laps (default 3).
* Provides formatted time strings and status payload for HUD/finish screen.

Partially implemented or fragile points:

* Checkpoints are treated as set completion (all visited) rather than enforced sequence order.
* Status payload includes `entered_start_finish` and `entered_checkpoint` keys, but current implementation always returns them as false placeholders.

Missing relative to strict design expectations:

* No checkpoint order enforcement if the milestone definition requires ordered progression.

### env.py

Exists: Yes.

Key class:

* `CarRacingEnv`

What it currently does:

* Provides Gym-style API:
  * `reset(seed=None) -> observation`
  * `step(action) -> observation, reward, done, info`
* Supports headless mode by skipping display creation and rendering.
* Loads track and car from spawn pose, integrates lap manager.
* Validates and clamps continuous actions:
  * steer [-1, 1]
  * throttle [0, 1]
  * brake [0, 1]
* Converts continuous action to the keyboard-control path used by car update.
* Emits observation vector of 8 values (7 sensors + normalized speed).
* Implements reward shaping using configurable weights from `reward_config`.
* Uses built-in defaults when no reward config is provided (backward compatible).
* Implements done logic (max steps, stuck limit, race completion).
* Provides telemetry in info including collision, lap fields, x, y, speed.

Partially implemented or fragile points:

* Action application temporarily monkey-patches pygame key state, which works in this single-env flow but is not ideal for multi-env or concurrent execution.

Missing relative to strict design expectations:

* No native Gymnasium terminated/truncated split in base env (handled in adapter inside train script).

### reward_utils.py

Exists: Yes.

What it currently does:

* Loads reward configuration JSON files.
* Validates required reward keys and numeric fields.
* Supports loading by explicit file path and by config name (`reward_configs/<name>.json`).

### main.py

Exists: Yes.

Key functions:

* `create_car_at_spawn(track)`
* `draw_sensor_rays(screen, sensor_debug_rays)`
* `draw_finish_screen(...)`
* `main()`

What it currently does:

* Starts pygame, loads track, spawns car from start line, and runs the game loop.
* Handles keyboard driving and lap progression.
* Draws track, car, sensor rays, and race HUD.
* Provides finish screen and retry flow after race completion.

Partially implemented or fragile points:

* Control mapping is arrow keys, not WASD (some docs still mention WASD).

Missing relative to strict design expectations:

* No explicit debug toggle controls; sensor overlay is always shown during race.

### train.py

Exists: Yes.

Key class/functionality:

* `SB3CarRacingEnv` Gymnasium adapter wrapping `CarRacingEnv`
* Standalone training entrypoint

What it currently does:

* Creates headless environment.
* Defines action and observation spaces for stable-baselines3 compatibility.
* Trains PPO with `MlpPolicy` in a time-based loop.
* Runs training in fixed chunks (`TRAINING_CHUNK_TIMESTEPS`) using repeated `model.learn(..., reset_num_timesteps=False)` calls.
* Stops automatically when configured wall-clock duration (`MAX_TRAINING_TIME`) is reached.
* Accepts reward selection by:
  * `--reward-config <path-to-json>`
  * `--reward-name <name>` (loads `reward_configs/<name>.json`)
* Passes selected reward config into `CarRacingEnv(headless=True, reward_config=...)`.
* Saves periodic checkpoints under `models/<reward_name>/ppo_car_model.zip`.
* Always saves a final model under `models/<reward_name>/ppo_car_model_final.zip`.
* Writes logs under `data/<reward_name>/run_xxx/` via `TrainingLogger`.

Partially implemented or fragile points:

* Time stop condition is checked between chunks, so real elapsed time can overshoot the exact target by up to one training chunk runtime.
* Default training duration is currently very short (`MAX_TRAINING_TIME = 30`), which is useful for quick checks but not for meaningful policy quality.

### reward_configs/

Exists: Yes.

Current files:

* `reward_configs/baseline.json`
* `reward_configs/safe_driver.json`
* `reward_configs/progress_heavy.json`

What they currently do:

* Define named reward-weight presets for training experiments.
* Allow training multiple models without overwriting each other's outputs.

### scripts/train_all_rewards.py

Exists: Yes.

What it currently does:

* Finds all `*.json` files in `reward_configs/`.
* Runs `train.py --reward-config <file>` sequentially for each config.
* Uses no parallel execution.

### play_model.py

Exists: Yes.

Key functionality:

* `main()` entrypoint for visual model playback

What it currently does:

* Loads trained PPO model from `ppo_car_model`.
* Instantiates `CarRacingEnv(headless=False)` to open a visible game window.
* Runs deterministic model predictions in a loop: predict action → step → render.
* Resets environment automatically when an episode ends.
* Terminates cleanly when the window is closed.

Missing relative to strict design expectations:

* No model path argument; path is a fixed constant at the top of the file.

### tests/

Exists: Yes.

Current tests:

* Headless pygame fixture setup in `tests/conftest.py`.
* Track and car tests in `tests/test_track_and_car.py` covering:
  * out-of-bounds wall behavior
  * raycast starting in wall
  * raycast clear-road distance behavior
  * collision preventing forward penetration
  * sensor output size and normalization

Partially implemented or fragile points:

* No direct tests for lap manager, environment reward/done behavior, training adapter, or logger outputs.

Missing relative to strict design expectations:

* End-to-end regression tests for env and training logging flows.

### assets/

Exists: Yes.

Current files:

* `assets/Track.png` (primary track used by game and env).
* `assets/prac.png` (present but not referenced by current runtime paths).

Partially implemented or fragile points:

* Track loading path is fixed by default to `assets/Track.png`; no asset management abstraction.

### logger.py (additional implemented module)

Exists: Yes.

Key class:

* `TrainingLogger`

What it currently does:

* Creates incremental run folders under the configured base directory (for training this is `data/<reward_name>/run_xxx`).
* Writes step-level rows to `steps.csv` incrementally.
* Stores episode summaries and writes `episodes.json` at finalize.
* Writes `metadata.json` with timestamp, environment settings, and planned episode estimate.

## 5.2 Current Implementation by Milestone (Code-Verified)

### Milestone 1 – Playable prototype

Status: Implemented but needs refinement.

Why:

* `main.py` opens a window, draws track/car, and supports keyboard driving.
* Collision and lap/timing/race-finish loop are functioning.
* Documentation mismatch exists on controls (implemented controls are arrow keys, not WASD in some planning text).

### Milestone 2 – Sensors

Status: Implemented.

Why:

* 7 rays are implemented in car and use track raycast.
* Outputs are normalized.
* Visual rays are rendered in play mode.
* Tests include sensor normalization and raycast behavior checks.

### Milestone 3 – Laps + checkpoints

Status: Implemented but needs refinement.

Why:

* Start/finish and checkpoints are detected and lap progression works.
* Current logic requires all checkpoints crossed but does not enforce ordered checkpoint sequence.
* If ordered checkpoints are a strict requirement, this milestone is functionally close but not fully aligned.

### Milestone 4 – RL environment

Status: Implemented.

Why:

* `env.py` exposes reset and step.
* Continuous actions are validated and applied.
* Stable observation vector is returned.
* Headless mode works and is used in training.
* Random-step validation script exists in `scripts/env_test.py`.

### Milestone 5 – Training

Status: Implemented.

Why:

* `train.py` integrates stable-baselines3 PPO with a Gymnasium adapter.
* Headless training run starts and executes in wall-clock bounded chunks.
* Reward configuration can be selected by name or JSON path.
* Checkpoint model is saved to disk per reward profile (`models/<reward_name>/ppo_car_model.zip`) during training.
* Final model is saved per reward profile (`models/<reward_name>/ppo_car_model_final.zip`) on shutdown.
* Data logging is integrated during training.
* Data logging is separated per reward profile (`data/<reward_name>/run_xxx/`).

## 5.3 Exact Behaviour Currently Supported

Confirmed supported now:

* The game opens and runs via `python main.py`.
* Keyboard driving works with arrow keys.
* Collision against track walls works through multi-point footprint checks.
* Sensor system works with 7 normalized ray distances and debug ray rendering.
* Start/finish and checkpoint-aware lap progression works.
* Race completion flow and retry screen are implemented.
* Environment API exists and returns observation, reward, done, info.
* Headless mode exists and is used by training.
* PPO training entrypoint uses time-based chunked learning, configurable reward profiles, and per-profile outputs.
* Trained model playback via `play_model.py` opens the game window with autonomous driving.
* Automated tests exist and pass for track/car coverage.
* Data capture is active during training and writes:
  * `data/<reward_name>/run_xxx/steps.csv`
  * `data/<reward_name>/run_xxx/episodes.json`
  * `data/<reward_name>/run_xxx/metadata.json`

## 5.4 Known Gaps, Risks, and Next Work

Known gaps and likely fragile areas:

* Checkpoint ordering is not enforced in lap logic; only set completion is enforced.
* No dedicated tests for lap progression rules, env reward/termination correctness, or logger output schema.
* Env action application uses temporary pygame key monkey-patching; acceptable for now but fragile for scaling.
* Time-based training loop stops between chunks, so long chunk runtimes can reduce stopping-time precision.
* Reward config validation currently checks required keys and numeric values, but does not enforce domain-specific bounds for each field.
* Documentation source files requested by import process are missing from repository (`.docx` and design txt names), which can cause alignment drift.

Recommended next development step:

* Add targeted tests for Milestone 3 and Milestone 4 behavior:
  * ordered checkpoint progression policy (if required)
  * done-reason correctness
  * logger file schema and non-empty outputs after training

---

# 6. Run Commands

Install dependencies:

pip install -r requirements.txt

Run game:

python main.py

Run tests:

python -m pytest

Run environment test:

python -c "from env import CarRacingEnv; env=CarRacingEnv(headless=True); obs=env.reset(); print(len(obs))"

Train model:

python train.py

Train with a specific reward config path:

python train.py --reward-config reward_configs/baseline.json

Train with a reward config by name:

python train.py --reward-name safe_driver

Train all reward configs sequentially:

python scripts/train_all_rewards.py

Training outputs from `train.py`:

* Periodic checkpoint: `models/<reward_name>/ppo_car_model.zip`
* Final model on shutdown: `models/<reward_name>/ppo_car_model_final.zip`
* Logged run data under `data/<reward_name>/run_xxx/`

Play trained model (opens game window):

python play_model.py

---

# 7. Model Playback

The `play_model.py` script allows visual inspection of a trained model.

How it works:

* Loads the saved PPO model from `ppo_car_model` (repo root).
* Opens the full game window (non-headless mode).
* The car drives automatically without keyboard input.
* Each episode resets automatically when it ends.
* Close the window to stop playback.

How to run:

```
python play_model.py
```

Requirements:

* A trained model must exist at repo root as `ppo_car_model.zip`.
* Current training stores models under `models/<reward_name>/...`, so copy the model you want to inspect to repo root as `ppo_car_model.zip`, or edit `MODEL_PATH` in `play_model.py`.
* Stable-Baselines3 must be installed (`pip install -r requirements.txt`).

---

# 8. README Maintenance Rule

This repository uses README as a living implementation log.

Maintenance requirements:

* Every implementation change must update README in the same change set.
* README must reflect the actual current code state, not planned state.
* Detailed Implementation Status must remain specific, code-aware, and accurate.
* A milestone can be marked complete only when code satisfies its definition of done.

---

# 9. Summary

Current codebase state:

* Playable game loop is implemented.
* Sensor-based driving observations are implemented.
* Lap/checkpoint system is implemented with sequence-order refinement pending.
* RL environment and headless training are implemented.
* PPO training is time-based, supports multiple reward configs, and saves separate models/logs per reward config.
* Run data capture is implemented.

Current priority:

* Keep status documentation synchronized with real code and close behavior/test gaps before adding larger new features.
