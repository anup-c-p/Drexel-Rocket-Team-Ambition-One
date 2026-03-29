from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any
from contextlib import closing

DB_PATH = "AMB1_Database-Anup-Production1_v01.db"



def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Create a new SQLite connection.

    Notes:
    - SQLite stores booleans as integers (0 = False, 1 = True).
    - WAL mode allows one writer and multiple readers more smoothly.
    """
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    print("Successfully Connected to DB")
    return conn


def initialize_database(db_path: Path | str = DB_PATH) -> None:
    """Create all required tables and seed single-row state tables."""
    with closing(get_connection(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc REAL NOT NULL,
                pressure_1 REAL NOT NULL,
                pressure_2 REAL NOT NULL,
                pressure_3 REAL NOT NULL,
                force REAL NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS latest_sensor_data (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                timestamp_utc REAL NOT NULL,
                pressure_1 REAL NOT NULL,
                pressure_2 REAL NOT NULL,
                pressure_3 REAL NOT NULL,
                force REAL NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS servo_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                timestamp_utc REAL NOT NULL,
                servo_1_open INTEGER NOT NULL,
                servo_2_open INTEGER NOT NULL,
                servo_3_open INTEGER NOT NULL,
                servo_4_open INTEGER NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_flags (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                timestamp_utc REAL NOT NULL,
                abort_flag INTEGER NOT NULL
            )
            """
        )

        now = time.time()

        conn.execute(
            """
            INSERT OR IGNORE INTO servo_state (
                id, timestamp_utc, servo_1_open, servo_2_open, servo_3_open, servo_4_open
            ) VALUES (1, ?, 0, 0, 0, 0)
            """,
            (now,),
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO system_flags (id, timestamp_utc, abort_flag)
            VALUES (1, ?, 0)
            """,
            (now,),
        )

        conn.commit()

        print("Tables Successfully Created")


def insert_sensor_reading(pressure_1: float, pressure_2: float, pressure_3: float, force: float, db_path: Path | str = DB_PATH) -> None:
    """Append a sensor reading to history and update the latest snapshot."""
    timestamp_utc = time.time()

    with closing(get_connection(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO sensor_history (
                timestamp_utc, pressure_1, pressure_2, pressure_3, force
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp_utc, pressure_1, pressure_2, pressure_3, force),
        )

        conn.execute(
            """
            INSERT INTO latest_sensor_data (
                id, timestamp_utc, pressure_1, pressure_2, pressure_3, force
            ) VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                timestamp_utc = excluded.timestamp_utc,
                pressure_1 = excluded.pressure_1,
                pressure_2 = excluded.pressure_2,
                pressure_3 = excluded.pressure_3,
                force = excluded.force
            """,
            (timestamp_utc, pressure_1, pressure_2, pressure_3, force),
        )

        conn.commit()


def get_latest_sensor_data(db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    with closing(get_connection(db_path)) as conn:
        row = conn.execute(
            """
            SELECT timestamp_utc, pressure_1, pressure_2, pressure_3, force
            FROM latest_sensor_data
            WHERE id = 1
            """
        ).fetchone()
        return dict(row) if row else None


def get_sensor_history(limit: int = 100, db_path: Path | str = DB_PATH) -> list[dict[str, Any]]:
    with closing(get_connection(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp_utc, pressure_1, pressure_2, pressure_3, force
            FROM sensor_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def update_servo_state(servo_1_open: bool, servo_2_open: bool, servo_3_open: bool, servo_4_open: bool, db_path: Path | str = DB_PATH) -> None:
    timestamp_utc = time.time()
    with closing(get_connection(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO servo_state (
                id, timestamp_utc, servo_1_open, servo_2_open, servo_3_open, servo_4_open
            ) VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                timestamp_utc = excluded.timestamp_utc,
                servo_1_open = excluded.servo_1_open,
                servo_2_open = excluded.servo_2_open,
                servo_3_open = excluded.servo_3_open,
                servo_4_open = excluded.servo_4_open
            """,
            (
                timestamp_utc,
                int(servo_1_open),
                int(servo_2_open),
                int(servo_3_open),
                int(servo_4_open),
            ),
        )
        conn.commit()


def get_servo_state(db_path: Path | str = DB_PATH) -> dict[str, bool | float] | None:
    with closing(get_connection(db_path)) as conn:
        row = conn.execute(
            """
            SELECT timestamp_utc, servo_1_open, servo_2_open, servo_3_open, servo_4_open
            FROM servo_state
            WHERE id = 1
            """
        ).fetchone()

    if not row:
        return None

    return {
        "timestamp_utc": row["timestamp_utc"],
        "servo_1_open": bool(row["servo_1_open"]),
        "servo_2_open": bool(row["servo_2_open"]),
        "servo_3_open": bool(row["servo_3_open"]),
        "servo_4_open": bool(row["servo_4_open"]),
    }


def set_abort_flag(abort_flag: bool, db_path: Path | str = DB_PATH) -> None:
    timestamp_utc = time.time()
    with closing(get_connection(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO system_flags (id, timestamp_utc, abort_flag)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                timestamp_utc = excluded.timestamp_utc,
                abort_flag = excluded.abort_flag
            """,
            (timestamp_utc, int(abort_flag)),
        )
        conn.commit


def get_abort_flag(db_path: Path | str = DB_PATH) -> bool:
    with closing(get_connection(db_path)) as conn:
        row = conn.execute(
            """
            SELECT abort_flag
            FROM system_flags
            WHERE id = 1
            """
        ).fetchone()
    return bool(row["abort_flag"]) if row else False


def get_system_snapshot(db_path: Path | str = DB_PATH) -> dict[str, Any]:
    """Convenience helper to read all current state in one call."""
    return {
        "latest_sensor_data": get_latest_sensor_data(db_path),
        "servo_state": get_servo_state(db_path),
        "abort_flag": get_abort_flag(db_path),
    }

initialize_database()
print("Success")