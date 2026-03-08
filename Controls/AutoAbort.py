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


def should_abort(sensor_data: dict[str, Any]) -> bool:
    """Evaluate whether the current system state should trigger an abort."""
    p_t = float(sensor_data["pressure 1"])
    return (p_t >= P_F)


def run_auto_abort() -> None:
    """Continuously monitor SQLite data and update the abort flag.

    TODO:
    - Add the polling loop.
    - Decide the polling rate.
    - Handle the case where no sensor data exists yet.
    """
    while (True):
        sensor_data = get_latest_sensor_data(db_path=DB_PATH)
        if (should_abort(sensor_data)):
            update_abort_flag(True)
            break
        
        sleep(0) #TODO fill this in


def main() -> None:
    initialize_auto_abort_module()
    run_auto_abort()


if __name__ == "__main__":
    main()
