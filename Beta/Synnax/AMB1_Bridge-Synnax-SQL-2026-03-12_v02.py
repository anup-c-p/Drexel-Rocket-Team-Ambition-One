import sqlite3
import time
from pathlib import Path

import synnax as sy

DB_PATH = Path("AMB1_Database-Anup-Test1_v11.db")
POLL_INTERVAL = 0.05


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_system_snapshot(cursor: sqlite3.Cursor):
    row = cursor.execute(
        """
        SELECT
            lsd.timestamp_utc                  AS sensor_timestamp_utc,
            lsd.pressure_1                     AS pressure_1,
            lsd.pressure_2                     AS pressure_2,
            lsd.pressure_3                     AS pressure_3,
            lsd.force                          AS force,

            ss.timestamp_utc                   AS servo_timestamp_utc,
            ss.servo_1_open                    AS servo_1_open,
            ss.servo_2_open                    AS servo_2_open,
            ss.servo_3_open                    AS servo_3_open,
            ss.servo_4_open                    AS servo_4_open,

            sf.timestamp_utc                   AS abort_timestamp_utc,
            sf.abort_flag                      AS abort_flag
        FROM latest_sensor_data lsd
        LEFT JOIN servo_state ss
            ON ss.id = 1
        LEFT JOIN system_flags sf
            ON sf.id = 1
        WHERE lsd.id = 1
        """
    ).fetchone()

    return row


def safe_float(value, default=0.0):
    return float(value) if value is not None else default


def safe_bool(value, default=False):
    return bool(value) if value is not None else default


def main():
    # THIS WAS ADDED FOR DEBUG
    print(f"Bridge DB_PATH raw: {DB_PATH}")
    print(f"Bridge DB_PATH resolved: {DB_PATH.resolve()}")
    print(f"Bridge script location: {Path(__file__).resolve()}")
    print(f"Bridge cwd: {Path.cwd()}")
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH.resolve()}")

    conn = get_connection(DB_PATH)
    cursor = conn.cursor()

    client = sy.Synnax(
        host="demo.synnaxlabs.com",
        port=9090,
        username="synnax",
        password="seldon",
        secure=True,
    )

    print("Connected to SQLite and Synnax.")

    last_sensor_timestamp = None

    try:
        with client.open_writer(
            start=sy.TimeStamp.now(),
            channels=[
                "sim_time",
                "chamber_pressure",
                "Fuel_Pressure",
                "nox_pressure",
                "Force",
                "fuel_valve",
                "nox_valve",
                "gse_nox",
                "gse_co2",
                "abort_flag",
            ],
        ) as writer:
            while True:
                snapshot = fetch_system_snapshot(cursor)

                if snapshot is None:
                    print("No row yet in latest_sensor_data. Waiting....")
                    time.sleep(POLL_INTERVAL)
                    continue

                current_sensor_timestamp = snapshot["sensor_timestamp_utc"]

                if current_sensor_timestamp == last_sensor_timestamp:
                    time.sleep(POLL_INTERVAL)
                    continue

                now = sy.TimeStamp.now()

                writer.write(
                    {
                        "sim_time": now,
                        "chamber_pressure": safe_float(snapshot["pressure_1"]),
                        "Fuel_Pressure": safe_float(snapshot["pressure_2"]),
                        "nox_pressure": safe_float(snapshot["pressure_3"]),
                        "Force": safe_float(snapshot["force"]),
                        "fuel_valve": safe_bool(snapshot["servo_1_open"]),
                        "nox_valve": safe_bool(snapshot["servo_2_open"]),
                        "gse_nox": safe_bool(snapshot["servo_3_open"]),
                        "gse_co2": safe_bool(snapshot["servo_4_open"]),
                        "abort_flag": safe_bool(snapshot["abort_flag"]),
                    }
                )

                print(
                    "Wrote -> "
                    f"T={current_sensor_timestamp}, "
                    f"P1={safe_float(snapshot['pressure_1'])}, "
                    f"P2={safe_float(snapshot['pressure_2'])}, "
                    f"P3={safe_float(snapshot['pressure_3'])}, "
                    f"F={safe_float(snapshot['force'])}, "
                    f"S1={safe_bool(snapshot['servo_1_open'])}, "
                    f"S2={safe_bool(snapshot['servo_2_open'])}, "
                    f"S3={safe_bool(snapshot['servo_3_open'])}, "
                    f"S4={safe_bool(snapshot['servo_4_open'])}, "
                    f"ABORT={safe_bool(snapshot['abort_flag'])}"
                )

                last_sensor_timestamp = current_sensor_timestamp
                time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("Stopping bridge.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()