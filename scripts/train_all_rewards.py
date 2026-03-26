"""Run training sequentially for every reward configuration in reward_configs/."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    config_dir = repo_root / "reward_configs"
    config_paths = sorted(config_dir.glob("*.json"))

    if not config_paths:
        raise FileNotFoundError(f"No reward configs found in: {config_dir}")

    for config_path in config_paths:
        print(f"\n=== Training with {config_path.name} ===")
        subprocess.run(
            [sys.executable, "train.py", "--reward-config", str(config_path)],
            cwd=repo_root,
            check=True,
        )

    print("\nAll reward configurations finished.")


if __name__ == "__main__":
    main()
