from __future__ import annotations

from typing import Any

import serial

from Database import DB_PATH, get_abort_flag, get_latest_sensor_data, get_servo_state, initialize_database, update_servo_state

from Keys import *

from time import sleep

CONTROL_SERIAL_PORT = "COM6"   # TODO: replace with the real servo ESP32 port
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


def await_user_input(key: str) -> None:
    key = key.lower()
    cmd = input("continue sequence").lower()
    while (cmd != key):
        cmd = input("continue sequence").lower()
    

def send_serial_command(control_serial: serial.Serial, command: str) -> None:
    """Send one command to the servo ESP32."""
    control_serial.write((command + "\n").encode("utf-8"))


def ignition_sequence(control_serial: serial.Serial) -> None:
    global gse_nos
    global gse_co2
    global mpv_nos
    global mpv_e85
    global race_condition
    
    print("----- Ignition Sequence Start -----")
    while (race_condition):
        print("Ignition Step 1: GSE NOS Open")
        send_serial_command(control_serial, GSE_NOS_OPEN)
        gse_nos = True
        save_servo_state()
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO: Fill this in
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 2: Await User Input")
        await_user_input("continue")
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO: Fill this in
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 3: GSE NOS Close")
        send_serial_command(control_serial, GSE_NOS_CLOSE)
        gse_nos = False
        save_servo_state()
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO: Fill this in
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 4: NOS Pressure Check")
        p_t = get_sensor_data()
        while (p_t < P_F and p_t > P_N):
            print("System Blowdown")
            p_t = get_sensor_data()
        
            if (p_t >= P_F):
                race_condition = False
                break
        
        if (not race_condition):
            break
        
        print("Ignition Step 5: Arm Ignition System")
        await_user_input("arm")
        print("WARNING: System Holding")
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO fill this in
        load_abort_flag()
        if not race_condition: break
        print("Ignition Step 6: Arm Ignition Sequence")
        await_user_input("arm")
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO fill this in
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 7: MPV NOS & E85 Open")
        send_serial_command(control_serial, MPV_NOS_OPEN)
        mpv_nos = True
        save_servo_state()
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO fill this in
        load_abort_flag()
        if not race_condition: break
        send_serial_command(control_serial, MPV_E85_OPEN)
        mpv_e85 = True
        save_servo_state()
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO fill this in
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 8: Ignition")
        send_serial_command(control_serial, IGNITER_TRIGGER)
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO fill this in
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 9: MPV NOS & E85 Close")
        send_serial_command(control_serial, MPV_NOS_CLOSE)
        mpv_nos = False
        save_servo_state()
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO fill this in
        load_abort_flag()
        if not race_condition: break
        send_serial_command(control_serial, MPV_E85_CLOSE)
        mpv_e85 = False
        save_servo_state()
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO fill this in
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 10: DELAY")
        for i in range(20):
            sleep(0.5)
            load_abort_flag()
            if not race_condition: break
        
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 11: MPV NOS Open")
        send_serial_command(control_serial, MPV_NOS_OPEN)
        mpv_nos = True
        save_servo_state()
        load_abort_flag()
        if not race_condition: break
        sleep(0) #TODO fill this in
        load_abort_flag()
        if not race_condition: break
        
        print("Ignition Step 12: Deactivate Ignition System")
        await_user_input("deactivate")
        send_serial_command(control_serial, IGNITER_PURGE)
        break
    
    if (not race_condition):
        print("----- EMERGENCY: Abort Sequence Initatiated -----")
        abort_sequence()


def safeing_sequence_1(control_serial: serial.Serial) -> None:
    global gse_nos
    global gse_co2
    global mpv_nos
    global mpv_e85
    global race_condition
    
    print("----- Safeing Sequence Start -----")
    while (race_condition):
        print("Safeing Step 1: Await User Input")
        await_user_input("continue")
        sleep(0) #TODO fill this in
        
        print("Safeing Step 2: GSE NOS Open")
        send_serial_command(control_serial, GSE_NOS_OPEN)
        gse_nos = True
        save_servo_state()
        sleep(0) #TODO fill this in
        
        print("Safeing Step 3: GSE NOS Close")
        send_serial_command(control_serial, GSE_NOS_CLOSE)
        gse_nos = False
        save_servo_state()
        sleep(0) #TODO fill this in
        
        print("Safeing Step 4: GSE CO2 Open")
        send_serial_command(control_serial, GSE_CO2_OPEN)
        gse_co2 = True
        save_servo_state()
        sleep(0) #TODO fill this in
        
        print("Safeing Step 5: GSE CO2 Close")
        send_serial_command(control_serial, GSE_CO2_CLOSE)
        gse_co2 = False
        save_servo_state()
        sleep(0) #TODO fill this in
        break


def safeing_sequence_2(control_serial: serial.Serial) -> None:
    global gse_nos
    global gse_co2
    global mpv_nos
    global mpv_e85
    global race_condition
    
    print("----- Safeing Sequence 2 Start -----")
    while (race_condition):
        print("Safeing 2 Step 1: Await User Input")
        await_user_input("continue")
        sleep(0) #TODO fill this in
        
        print("Safeing 2 Step 2: GSE NOS Open")
        send_serial_command(control_serial, GSE_NOS_OPEN)
        gse_nos = True
        save_servo_state()
        sleep(0) #TODO fill this in
        
        print("Safeing 2 Step 3: GSE CO2 Open")
        send_serial_command(control_serial, GSE_CO2_OPEN)
        gse_co2 = True
        save_servo_state()
        sleep(0) #TODO fill this in
        break


def abort_sequence(control_serial: serial.Serial) -> None:
    global gse_nos
    global gse_co2
    global mpv_nos
    global mpv_e85
    global race_condition
    
    print("----- Abort Sequence Start -----")
    
    print("Abort Step 1: GSE NOS & CO2 Close")
    send_serial_command(control_serial, GSE_NOS_CLOSE)
    send_serial_command(control_serial, GSE_CO2_CLOSE)
    gse_nos = False
    gse_co2 = False
    save_servo_state()
    print("Abort Step 2: MPV NOS & E85 Close")
    send_serial_command(control_serial, MPV_NOS_CLOSE)
    send_serial_command(control_serial, MPV_E85_CLOSE)
    mpv_nos = False
    mpv_e85 = False
    save_servo_state()
    sleep(0) #TODO fill this in
    
    print("Abort Step 3: MPV NOS Open")
    send_serial_command(control_serial, MPV_NOS_OPEN)
    mpv_nos = True
    save_servo_state()
    sleep(0) #TODO fill this in
    
    safeing_sequence_1(control_serial)
    safeing_sequence_2(control_serial)


def run_main_control(control_serial: serial.Serial) -> None:
    """Main control loop."""
    if (race_condition):
        ignition_sequence(control_serial)
        
    else:
        abort_sequence(control_serial)
    
    if (race_condition):
        safeing_sequence_1(control_serial)
    
    if (race_condition):
        safeing_sequence_2(control_serial)


def main() -> None:
    initialize_main_control_module()
    control_serial = open_control_serial_port()

    try:
        run_main_control(control_serial)
    finally:
        control_serial.close()


if __name__ == "__main__":
    main()
