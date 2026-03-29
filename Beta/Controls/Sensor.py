from __future__ import annotations

import json
from typing import Any

import serial

from Database import DB_PATH, initialize_database, insert_sensor_reading

from time import sleep

SENSOR_SERIAL_PORT = "COM5"   # TODO: replace with the real sensor ESP32 port
SENSOR_BAUD_RATE = 115200
SENSOR_TIMEOUT_SEC = 1.0

def open_sensor_serial_port(port: str = SENSOR_SERIAL_PORT, baud_rate: int = SENSOR_BAUD_RATE, timeout: float = SENSOR_TIMEOUT_SEC) -> serial.Serial:
    """Open the serial connection to the sensor ESP32."""
    return serial.Serial(port=port, baudrate=baud_rate, timeout=timeout)


def initialize_sensor_module() -> None:
    """Initialize any persistent resources used by Sensor.py."""
    initialize_database(DB_PATH)


def read_raw_serial_line(sensor_serial: serial.Serial) -> str:
    """Read one raw line from the sensor ESP32.

    TODO:
    - Decide the exact serial packet format used by the ESP32.
    - Add error handling for empty lines and corrupt packets.
    """
    raw_bytes = sensor_serial.readline()
    return raw_bytes.decode("utf-8", errors="replace").strip()

def parse_state_parameter(state) -> None:
    match state:
        case 0:
            return
        
        case 1:
            return
        
        case 2:
            return
        
        case 3:
            return
        
        case 4:
            return
        
        case 5:
            return
        
        case 6:
            return
        
        case 7:
            return
        
        case 8:
            return
        
        case 9:
            return
        
        case 10:
            return
        
        case 11:
            return
        
        case 12:
            return
        
        case 13:
            return
        
        case 14:
            return
        
        case 15:
            return
        
        case 16:
            return
        
        case 17:
            return
        
        case 18:
            return
        
        case 19:
            return
        
        case 20:
            return
        
        case 21:
            return
        
        case 22:
            return
        
        case 23:
            return


def parse_sensor_packet(raw_line: str) -> dict[str, Any]:
    """Parse one sensor packet.

    Expected dictionary shape:
        {
            "p1":float,
            "p2":float,
            "p3":float,
            "f":float,
            "a":int,
        }

    TODO:
    - Confirm whether the ESP32 sends JSON, CSV, or another format.
    - Validate units and scaling for each sensor.
    """
    return json.loads(raw_line)


def save_sensor_packet(packet: dict[str, Any]) -> None:
    """Write one sensor packet into SQLite."""
    insert_sensor_reading(pressure_1=float(packet["p1"]), pressure_2=float(packet["p2"]), pressure_3=float(packet["p3"]), force=float(packet["f"]), abort=float(packet["a"]), db_path=DB_PATH)


def handle_sensor_stream(sensor_serial: serial.Serial) -> None:
    """Continuously read serial data and store it to SQLite.

    TODO:
    - Add the main read/parse/save loop.
    - Add reconnect logic if the serial link drops.
    - Add logging for malformed packets.
    """
    while(True):
        data = read_raw_serial_line(sensor_serial)
        data_dict = parse_sensor_packet(data)
        save_sensor_packet(data_dict)
        sleep(1)
        


def main() -> None:
    initialize_sensor_module()
    sensor_serial = open_sensor_serial_port()

    try:
        handle_sensor_stream(sensor_serial)
    finally:
        sensor_serial.close()


if __name__ == "__main__":
    main()
