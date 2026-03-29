from __future__ import annotations

from typing import Any

import serial

from Database import DB_PATH, get_abort_flag, get_latest_sensor_data, get_servo_state, initialize_database, update_servo_state

from Keys import *

from time import sleep

import threading

CONTROL_SERIAL_PORT = "/dev/cu.usbserial-0001"   # TODO: replace with the real servo ESP32 port
CONTROL_BAUD_RATE = 115200
CONTROL_TIMEOUT_SEC = 1.0

gse_nos = False
gse_co2 = False
mpv_nos = False
mpv_e85 = False

race_condition = True

P_F = 800.0
P_N = 600.0
P_MIN = 500.0


def open_control_serial_port(port: str = CONTROL_SERIAL_PORT, baud_rate: int = CONTROL_BAUD_RATE, timeout: float = CONTROL_TIMEOUT_SEC) -> serial.Serial:
    """Open the serial connection to the servo-control ESP32."""
    return serial.Serial(port=port, baudrate=baud_rate, timeout=timeout)


def initialize_main_control_module() -> None:
    """Initialize persistent resources used by MainControl.py."""
    initialize_database(DB_PATH)


def save_servo_state() -> None:
    """Persist the latest commanded servo states in SQLite."""
    update_servo_state(servo_1_open=gse_nos, servo_2_open=gse_co2, servo_3_open=mpv_nos, servo_4_open=mpv_e85, db_path=DB_PATH)


def load_abort_flag() -> None:
    global race_condition
    """Read the latest abort flag from SQLite."""
    race_condition = False if get_abort_flag(DB_PATH) else True


def load_servo_state() -> dict[str, Any] | None:
    """Read the latest stored servo state from SQLite."""
    return get_servo_state(DB_PATH)


def get_sensor_data() -> float | None:
    values = get_latest_sensor_data(db_path=DB_PATH)
    if (values == None):
        return None
    
    return float(values["pressure_1"])


def await_user_input() -> str:
    return input("Awaiting Command: ")
    

def send_serial_command(control_serial: serial.Serial, command: str) -> None:
    """Send one command to the servo ESP32."""
    control_serial.write((command + "\n").encode("utf-8"))


def run_main_control(control_serial: serial.Serial) -> None:
    """Main control loop."""
    while(True):
        cmd = await_user_input()
        send_serial_command(control_serial, cmd)


def main() -> None:
    initialize_main_control_module()
    control_serial = open_control_serial_port()

    try:
        run_main_control(control_serial)
    finally:
        control_serial.close()


if __name__ == "__main__":
    main()
