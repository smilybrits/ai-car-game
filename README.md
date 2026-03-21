# ai-car-game

Machine learning car racing simulator built in Python using Pygame.

---

# 1. Project Overview

This project is a **2D top-down car racing simulator** built in Python using Pygame. It is designed to evolve into a **reinforcement learning (RL) training environment**.

The system serves two primary purposes:

1. A **playable racing game** where a human can control a car
2. A **machine learning environment** where an AI agent can learn to drive using structured observations and rewards

The key idea is to:
- First build a **fully functional game**
- Then progressively expose **clean inputs and outputs**
- So that an AI can interact with the simulation in a standard way

---

# 2. Project Goals

The project aims to:

- Simulate a car driving on a track using simple physics
- Use an image-based track system for easy editing
- Provide sensor-based observations for AI instead of images
- Implement laps and checkpoint logic
- Provide a Gym-style environment API (`reset()` / `step()`)
- Support headless execution for fast training

---

# 3. Core Design Principles

- **Simple > complex**
  - Arcade physics instead of realistic physics
- **Modular architecture**
  - No large combined files
- **Track = image mask**
  - Fast iteration, no track editor required
- **Sensors instead of vision**
  - Faster and easier for ML
- **Milestone-driven development**
  - System is always runnable

---

# 4. Track System (Critical)

The track is defined using a PNG image.

## Color Rules

| Color | RGB | Meaning |
|------|-----|--------|
| White | (255,255,255) | Drivable road |
| Black / other | Any | Wall / off-track |
| Red | (255,0,0) | Start / finish line |
| Green | (0,255,0) | Checkpoints |

Important rules:

- Red and green pixels are also treated as **drivable road**
- Out-of-bounds coordinates are treated as **walls**
- The entire game logic (collision + sensors) depends on this mask

---

# 5. Key Design Decisions (and Why)

## 5.1 Pygame

- Beginner-friendly
- Full control over game loop
- Easy rendering and input handling

---

## 5.2 Image-Based Track

Why this approach:

- Extremely fast to create/edit tracks
- No custom editor needed
- Pixel sampling enables:
  - Collision detection
  - Raycasting for sensors

---

## 5.3 Ray Sensors (AI Vision System)

The car uses 7 ray sensors:

Angles (relative to car direction):
[-90, -45, -20, 0, 20, 45, 90]

Each ray:
- Moves forward pixel by pixel
- Stops when it hits a wall
- Returns distance normalized to 0..1

Why:

- Efficient representation of environment
- Avoids heavy image processing
- Standard in RL driving tasks

---

## 5.4 Arcade Physics

The car uses simplified physics:

- Acceleration increases speed
- Braking reduces speed
- Friction reduces speed naturally
- Steering rotates the car (scaled by speed)

Why:

- Easier to implement
- Stable for ML training
- Good enough for gameplay

---

## 5.5 Modular Architecture

Files are strictly separated:

- `track.py` → track logic and raycasting
- `car.py` → car physics and sensors
- `lap.py` → lap and checkpoint logic
- `env.py` → RL environment wrapper
- `main.py` → game loop and rendering

Why:

- Easier debugging
- Cleaner structure
- AI reuses game logic without duplication

---

## 5.6 Gym-Style Environment

The AI interacts using:

```python
obs = env.reset()
obs, reward, done, info = env.step(action)

Why:

Standard RL interface
Compatible with ML frameworks
Clean separation between simulation and UI

5.7 Headless Mode

The environment can run without rendering.

Why:

Training requires many iterations
Rendering slows down performance
Headless allows faster simulation

# 6. System Architecture
6.1 track.py

Responsibilities:

Load track image
Provide pixel color access
Detect road vs wall
Perform raycasting
Detect start/finish region
Detect checkpoint regions
Provide spawn position and angle

6.2 car.py

Responsibilities:

Store position, angle, speed
Apply movement physics
Handle collision detection
Read sensor values

Features:

Multi-point collision detection
Rotation-aware collision
Smooth speed handling
Sensor system (7 rays)
6.3 lap.py

Responsibilities:

Track checkpoint progress
Count laps
Manage timing

Important logic:

Checkpoints can be crossed in any order
All checkpoints must be crossed before lap counts
Lap completes when start line is crossed again
6.4 env.py

Responsibilities:

Provide AI interface
Run simulation headless
Compute rewards

Provides:

reset()
step(action)

6.5 main.py

Responsibilities:

Run game loop
Handle player input
Render track, car, UI
Draw debug visuals
7. Player Controls

Arrow keys are used:

Key	Action
UP	Accelerate
DOWN	Brake / reverse
LEFT	Steer left
RIGHT	Steer right
8. Game Mechanics
8.1 Collision System
Uses track mask
Checks multiple points on car
Prevents driving through walls
Applies push-back and speed reduction
8.2 Sensors
7 ray sensors
Rotate with car direction
Return normalized distances
Drawn for debugging
8.3 Lap System
Start line = red region
Checkpoints = green regions
Must cross all checkpoints (any order)
Lap completes when red line is crossed again
8.4 Timing System

Tracks:

Total run time
Current lap time
Fastest lap

Rules:

Timer starts on first acceleration
Fastest lap updates only after valid lap
8.5 Race Completion
Race ends after 3 laps
Finish screen is displayed
Retry button resets full game state
9. AI Environment Design
9.1 Observations

Vector of 8 values:

Index	Description
0–6	Sensor distances
7	Normalized speed
9.2 Actions

Continuous input:

steer ∈ [-1, 1]
throttle ∈ [0, 1]
brake ∈ [0, 1]
9.3 Reward System

Encourages:

Forward progress
Checkpoint completion
Lap completion

Penalizes:

Collisions
Being stuck
Time steps
9.4 Termination Conditions

Episode ends when:

Max steps reached
Car stuck too long
Race completed

10. Current Status

Milestone 1 – Playable Game ✅
Full car control
Collision system
Track rendering
Spawn system
Smooth movement

Milestone 2 – Sensors ✅
Raycasting implemented
7 sensors working
Debug rendering
Pytest tests added

Milestone 3 – Laps & Race System ✅
Checkpoints implemented
Lap counting working
Timing system added
Finish screen + retry
Milestone 4 – RL Environment ✅

env.py implemented
Headless mode working
Observation and action space defined
Reward system implemented

11. System Flow
Play Mode
main.py runs game loop
User controls car
Car interacts with track
Lap system updates
UI renders output
AI Mode
env.reset() initializes environment
AI sends action
Simulation updates:
physics
sensors
lap progress
Returns:
observation
reward
done

12. Run Commands
python main.py
pytest
python -c "from env import CarRacingEnv; env=CarRacingEnv(headless=True); obs=env.reset(); print(len(obs), obs)"

13. Future Work (Next Milestones)
Milestone 5 – Training
Integrate Stable-Baselines3
Train PPO agent
Save/load models
Evaluate lap times
Milestone 6 – Observation Improvements
Add angle to next checkpoint
Add distance to checkpoint
Improve navigation awareness
Milestone 7 – Reward Optimization
Improve reward shaping
Penalize inefficient driving
Encourage smooth control
Milestone 8 – Multi-Track Support
Multiple track files
Randomized training
Generalization
Milestone 9 – Baseline AI
Rule-based driver
Debug and benchmarking tool
Milestone 10 – Data Collection
Record human gameplay
Build imitation learning dataset

14. Summary

This project provides:

A fully playable racing game
A structured simulation environment
A reinforcement learning interface

It forms a complete pipeline from:

GAME → SIMULATION → AI TRAINING

while remaining:

Simple
Modular
Extensible