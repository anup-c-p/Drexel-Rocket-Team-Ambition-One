from __future__ import annotations

from typing import Any

import serial

from Database import DB_PATH, get_abort_flag, get_servo_state, initialize_database, update_servo_state

CONTROL_SERIAL_PORT = "COM6"   # TODO: replace with the real servo ESP32 port
CONTROL_BAUD_RATE = 115200
CONTROL_TIMEOUT_SEC = 1.0

FINAL_PRESSURE = 800.0

def open_control_serial_port(port: str = CONTROL_SERIAL_PORT, baud_rate: int = CONTROL_BAUD_RATE, timeout: float = CONTROL_TIMEOUT_SEC) -> serial.Serial:
    """Open the serial connection to the servo-control ESP32."""
    return serial.Serial(port=port, baudrate=baud_rate, timeout=timeout)


def initialize_main_control_module() -> None:
    """Initialize persistent resources used by MainControl.py."""
    initialize_database(DB_PATH)


def save_servo_state(servo_1_open: bool, servo_2_open: bool, servo_3_open: bool, servo_4_open: bool) -> None:
    """Persist the latest commanded servo states in SQLite."""
    update_servo_state(servo_1_open=servo_1_open, servo_2_open=servo_2_open, servo_3_open=servo_3_open, servo_4_open=servo_4_open, db_path=DB_PATH)


def load_abort_flag() -> bool:
    """Read the latest abort flag from SQLite."""
    return get_abort_flag(DB_PATH)


def load_servo_state() -> dict[str, Any] | None:
    """Read the latest stored servo state from SQLite."""
    return get_servo_state(DB_PATH)


def build_servo_command(servo_index: int, state: bool) -> str:
    addon = 1 if state else 0
    match servo_index:
        case 1: return "a"+addon
        case 2: return "b"+addon
        case 3: return "c"+addon
        case 4: return "d"+addon
        case _: return ""


def send_servo_command(control_serial: serial.Serial, command: str) -> None:
    """Send one command to the servo ESP32.

    TODO:
    - Add command acknowledgements / retries if needed.
    - Add application-specific logging.
    """
    control_serial.write((command + "\n").encode("utf-8"))


def run_main_control(control_serial: serial.Serial) -> None:
    """Main control loop.

    TODO:
    - Read desired state from your higher-level control logic.
    - Check abort flag before sending movement commands.
    - Save commanded servo states after successful sends.
    """
    raise NotImplementedError("TODO: implement main control loop")


def main() -> None:
    initialize_main_control_module()
    control_serial = open_control_serial_port()

    try:
        run_main_control(control_serial)
    finally:
        control_serial.close()


if __name__ == "__main__":
    main()
