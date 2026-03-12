from __future__ import annotations

import importlib.util
import math
import random
import sys
import time
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("AMB1_Database_SQL_2026-03-11_v02.py")
MODULE_NAME = "amb1_database_module"

spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load database module from: {MODULE_PATH}")

amb1_db = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = amb1_db
spec.loader.exec_module(amb1_db)

DB_PATH = Path(amb1_db.DB_PATH)
initialize_database = amb1_db.initialize_database
insert_sensor_reading = amb1_db.insert_sensor_reading
update_servo_state = amb1_db.update_servo_state
set_abort_flag = amb1_db.set_abort_flag


# ---------- User settings ----------
SAMPLE_PERIOD_S = 0.25   # 4 Hz update rate
TOTAL_RUN_TIME_S = 120   # set to None if you want it to run forever
USE_PHASED_PROFILE = True
# ----------------------------------


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))



def phased_profile(elapsed_s: float) -> tuple[float, float, float, float, bool, bool, bool, bool, bool]:
    """
    Simple fabricated test profile for Ambition 1 style data.

    Returns:
        pressure_1, pressure_2, pressure_3, force,
        servo_1_open, servo_2_open, servo_3_open, servo_4_open,
        abort_flag
    """
    if elapsed_s < 5:
        return 0.0, 0.0, 0.0, 0.0, False, False, False, False, False

    if elapsed_s < 15:
        t = elapsed_s - 5
        p1 = 30 + 8 * t + random.uniform(-1.0, 1.0)
        p2 = 45 + 10 * t + random.uniform(-1.5, 1.5)
        p3 = 60 + 12 * t + random.uniform(-2.0, 2.0)
        force = random.uniform(-2.0, 2.0)
        return p1, p2, p3, force, True, True, False, False, False

    if elapsed_s < 35:
        t = elapsed_s - 15
        ripple = math.sin(t * 5.5)
        p1 = 180 + 18 * ripple + random.uniform(-3.0, 3.0)
        p2 = 320 + 30 * ripple + random.uniform(-5.0, 5.0)
        p3 = 520 + 40 * ripple + random.uniform(-6.0, 6.0)
        force = 180 + 25 * math.sin(t * 4.0) + random.uniform(-4.0, 4.0)
        return p1, p2, p3, force, True, True, True, False, False

    if elapsed_s < 50:
        t = elapsed_s - 35
        decay = math.exp(-t / 5.0)
        p1 = 140 * decay + random.uniform(-2.0, 2.0)
        p2 = 220 * decay + random.uniform(-2.0, 2.0)
        p3 = 320 * decay + random.uniform(-3.0, 3.0)
        force = 120 * decay + random.uniform(-3.0, 3.0)
        return p1, p2, p3, force, False, False, False, True, False

    return 0.0, 0.0, 0.0, 0.0, False, False, False, False, False



def continuous_profile(elapsed_s: float) -> tuple[float, float, float, float, bool, bool, bool, bool, bool]:
    """Endless smooth profile with small oscillations for general testing."""
    p1 = clamp(120 + 25 * math.sin(elapsed_s * 0.55) + random.uniform(-2.5, 2.5), 0, 1000)
    p2 = clamp(240 + 40 * math.sin(elapsed_s * 0.75 + 1.0) + random.uniform(-3.5, 3.5), 0, 1000)
    p3 = clamp(420 + 60 * math.sin(elapsed_s * 0.95 + 2.0) + random.uniform(-4.5, 4.5), 0, 1000)
    force = clamp(140 + 20 * math.sin(elapsed_s * 0.85 + 0.4) + random.uniform(-3.0, 3.0), 0, 1000)

    servo_1 = p1 > 80
    servo_2 = p2 > 180
    servo_3 = p3 > 350
    servo_4 = force < 20
    abort_flag = False
    return p1, p2, p3, force, servo_1, servo_2, servo_3, servo_4, abort_flag



def main() -> None:
    print(f"Live script location: {Path(__file__).resolve()}")
    print(f"Live cwd: {Path.cwd()}")
    print(f"Live module path: {MODULE_PATH.resolve()}")
    print(f"Live DB_PATH raw: {DB_PATH}")
    print(f"Live DB_PATH resolved: {DB_PATH.resolve()}")
    print(f"Initializing database: {DB_PATH.resolve()}")
    initialize_database(DB_PATH)

    print("Starting live feed into SQLite. Press Ctrl+C to stop.")
    start = time.time()
    sample_count = 0

    try:
        while True:
            now = time.time()
            elapsed = now - start

            if TOTAL_RUN_TIME_S is not None and elapsed >= TOTAL_RUN_TIME_S:
                print("Requested runtime reached. Stopping feed.")
                break

            if USE_PHASED_PROFILE:
                (
                    pressure_1,
                    pressure_2,
                    pressure_3,
                    force,
                    servo_1_open,
                    servo_2_open,
                    servo_3_open,
                    servo_4_open,
                    abort_flag,
                ) = phased_profile(elapsed)
            else:
                (
                    pressure_1,
                    pressure_2,
                    pressure_3,
                    force,
                    servo_1_open,
                    servo_2_open,
                    servo_3_open,
                    servo_4_open,
                    abort_flag,
                ) = continuous_profile(elapsed)

            insert_sensor_reading(
                pressure_1=round(pressure_1, 3),
                pressure_2=round(pressure_2, 3),
                pressure_3=round(pressure_3, 3),
                force=round(force, 3),
                db_path=DB_PATH,
            )

            update_servo_state(
                servo_1_open=servo_1_open,
                servo_2_open=servo_2_open,
                servo_3_open=servo_3_open,
                servo_4_open=servo_4_open,
                db_path=DB_PATH,
            )

            set_abort_flag(abort_flag=abort_flag, db_path=DB_PATH)

            sample_count += 1
            print(
                f"[{sample_count:05d}] "
                f"p1={pressure_1:7.2f}  "
                f"p2={pressure_2:7.2f}  "
                f"p3={pressure_3:7.2f}  "
                f"F={force:7.2f}  "
                f"servos=({int(servo_1_open)},{int(servo_2_open)},{int(servo_3_open)},{int(servo_4_open)})  "
                f"abort={int(abort_flag)}"
            )

            time.sleep(SAMPLE_PERIOD_S)

    except KeyboardInterrupt:
        print("\nLive feed stopped by user.")


if __name__ == "__main__":
    main()
