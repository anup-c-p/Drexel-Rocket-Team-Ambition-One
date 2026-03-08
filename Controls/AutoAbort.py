from __future__ import annotations

from typing import Any

from Database import DB_PATH, get_abort_flag, get_latest_sensor_data, initialize_database, set_abort_flag

from Keys import *

from time import sleep

P_F = 800.0
P_N = 600.0
P_MIN = 500.0

def initialize_auto_abort_module() -> None:
    """Initialize persistent resources used by AutoAbort.py."""
    initialize_database(DB_PATH)


def load_latest_sensor_data() -> dict[str, Any] | None:
    """Read the latest pressure and force values from SQLite."""
    return get_latest_sensor_data(DB_PATH)


def update_abort_flag(abort_flag: bool) -> None:
    """Persist the abort flag in SQLite."""
    set_abort_flag(abort_flag=abort_flag, db_path=DB_PATH)


def load_abort_flag() -> bool:
    """Read the current abort flag from SQLite."""
    return get_abort_flag(DB_PATH)


def should_abort(sensor_data: dict[str, Any]) -> bool:
    """Evaluate whether the current system state should trigger an abort.

    TODO:
    - Add your actual safety thresholds for all three pressure sensors.
    - Add your actual force threshold.
    - Add stale-data or timeout checks if needed.
    """
    raise NotImplementedError("TODO: implement abort decision logic")


def run_auto_abort() -> None:
    """Continuously monitor SQLite data and update the abort flag.

    TODO:
    - Add the polling loop.
    - Decide the polling rate.
    - Handle the case where no sensor data exists yet.
    """
    raise NotImplementedError("TODO: implement auto-abort loop")


def main() -> None:
    initialize_auto_abort_module()
    run_auto_abort()


if __name__ == "__main__":
    main()
