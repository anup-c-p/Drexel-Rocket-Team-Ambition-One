from __future__ import annotations

import sqlite3
import time
from pathlib import Path

# ── Toggle ─────────────────────────────────────────────────────────────────────
# Set to True when the database / visualization pipeline is ready to receive data.
SQL_ENABLED = True
# ──────────────────────────────────────────────────────────────────────────────

from config import DB_PATH

# Field mapping: our sensor → reference schema column
#   vP0  → pressure_1
#   vP1  → pressure_2
#   vP2  → pressure_3
#   vF   → force
#   (rssi and t_ms have no column in the reference schema)


class SQLLogger:
    """Writes sensor readings to a SQLite database using the exact same schema
    as AMB1_Database_SQL_2026-03-11_v02.py so the visualization software works
    without any changes.

    Servo state is seeded to all-False at session start and never changed
    (we have no servo data from the serial device).
    Abort flag defaults to False.

    All exceptions are caught internally and reported through the UI log
    so the main application keeps running even if the database fails.

    A single connection is held open for the duration of the session to avoid
    the overhead and lock contention of opening a new connection per reading.
    """

    def __init__(self):
        self._target_path: Path = DB_PATH
        self._log_fn = None
        self._conn: sqlite3.Connection | None = None

    def set_db_path(self, path: Path):
        self._target_path = path

    def start(self, log_fn):
        """Open (or create) the session database and hold the connection open.

        log_fn(message, color) is the UI log callback used to surface errors.
        """
        self._log_fn = log_fn
        if not SQL_ENABLED:
            return
        try:
            self._target_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = _open_connection(self._target_path)
            _initialize_database(self._conn)
        except Exception as e:
            self._error(f'SQL init failed: {e}')
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None

    def stop(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
        self._log_fn = None

    def log_sensor(self, _t, vP0, vP1, vP2, vF, *_):
        """Insert one sensor reading. Silently skipped if SQL_ENABLED is False."""
        if not SQL_ENABLED or not self._conn:
            return
        try:
            _insert_sensor_reading(
                pressure_1=float(vP0),
                pressure_2=float(vP1),
                pressure_3=float(vP2),
                force=float(vF),
                conn=self._conn,
            )
        except Exception as e:
            self._error(f'SQL write failed: {e}')

    def update_servo_state(self, servo_a: bool, servo_b: bool, servo_c: bool, servo_d: bool):
        """Update the servo_state table with current open/closed state for all four servos."""
        if not SQL_ENABLED or not self._conn:
            return
        try:
            ts = time.time()
            self._conn.execute(
                'INSERT INTO servo_state '
                '(id, timestamp_utc, servo_1_open, servo_2_open, servo_3_open, servo_4_open) '
                'VALUES (1, ?, ?, ?, ?, ?) '
                'ON CONFLICT(id) DO UPDATE SET '
                'timestamp_utc = excluded.timestamp_utc, '
                'servo_1_open = excluded.servo_1_open, '
                'servo_2_open = excluded.servo_2_open, '
                'servo_3_open = excluded.servo_3_open, '
                'servo_4_open = excluded.servo_4_open',
                (ts, int(servo_a), int(servo_b), int(servo_c), int(servo_d)),
            )
            self._conn.commit()
        except Exception as e:
            self._error(f'SQL servo state update failed: {e}')

    def set_abort_flag(self, flag: bool):
        """Update the system_flags table with the current abort state."""
        if not SQL_ENABLED or not self._conn:
            return
        try:
            ts = time.time()
            self._conn.execute(
                'INSERT INTO system_flags (id, timestamp_utc, abort_flag) VALUES (1, ?, ?) '
                'ON CONFLICT(id) DO UPDATE SET '
                'timestamp_utc = excluded.timestamp_utc, abort_flag = excluded.abort_flag',
                (ts, int(flag)),
            )
            self._conn.commit()
        except Exception as e:
            self._error(f'SQL abort flag update failed: {e}')

    def _error(self, msg: str):
        if self._log_fn:
            self._log_fn(f'[SQL ERROR] {msg}\n', '#e74c3c')


# ── Internal DB helpers (mirrors AMB1_Database_SQL_2026-03-11_v02.py) ──────────

def _open_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.execute('PRAGMA foreign_keys=ON;')
    return conn


def _initialize_database(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sensor_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc REAL    NOT NULL,
            pressure_1    REAL    NOT NULL,
            pressure_2    REAL    NOT NULL,
            pressure_3    REAL    NOT NULL,
            force         REAL    NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS latest_sensor_data (
            id            INTEGER PRIMARY KEY CHECK (id = 1),
            timestamp_utc REAL    NOT NULL,
            pressure_1    REAL    NOT NULL,
            pressure_2    REAL    NOT NULL,
            pressure_3    REAL    NOT NULL,
            force         REAL    NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS servo_state (
            id            INTEGER PRIMARY KEY CHECK (id = 1),
            timestamp_utc REAL    NOT NULL,
            servo_1_open  INTEGER NOT NULL,
            servo_2_open  INTEGER NOT NULL,
            servo_3_open  INTEGER NOT NULL,
            servo_4_open  INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS system_flags (
            id            INTEGER PRIMARY KEY CHECK (id = 1),
            timestamp_utc REAL    NOT NULL,
            abort_flag    INTEGER NOT NULL
        )
    ''')

    # Seed single-row state tables with defaults (servos all closed, no abort)
    now = time.time()
    conn.execute('''
        INSERT OR IGNORE INTO servo_state
            (id, timestamp_utc, servo_1_open, servo_2_open, servo_3_open, servo_4_open)
        VALUES (1, ?, 0, 0, 0, 0)
    ''', (now,))
    conn.execute('''
        INSERT OR IGNORE INTO system_flags (id, timestamp_utc, abort_flag)
        VALUES (1, ?, 0)
    ''', (now,))

    conn.commit()


def _insert_sensor_reading(
    pressure_1: float,
    pressure_2: float,
    pressure_3: float,
    force: float,
    conn: sqlite3.Connection,
) -> None:
    ts = time.time()
    conn.execute(
        'INSERT INTO sensor_history (timestamp_utc, pressure_1, pressure_2, pressure_3, force) '
        'VALUES (?, ?, ?, ?, ?)',
        (ts, pressure_1, pressure_2, pressure_3, force),
    )
    conn.execute('''
        INSERT INTO latest_sensor_data (id, timestamp_utc, pressure_1, pressure_2, pressure_3, force)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            timestamp_utc = excluded.timestamp_utc,
            pressure_1    = excluded.pressure_1,
            pressure_2    = excluded.pressure_2,
            pressure_3    = excluded.pressure_3,
            force         = excluded.force
    ''', (ts, pressure_1, pressure_2, pressure_3, force))
    conn.commit()
