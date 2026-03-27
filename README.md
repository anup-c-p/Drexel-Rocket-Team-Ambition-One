# Drexel Rocket Team Control Software

This repository contains the Python-side ground control software for a two-ESP32 architecture:

- **Control / transmit board**: receives valve and igniter commands over serial.
- **Sensor board**: streams sensor telemetry over serial.
- **SQLite database**: acts as the shared state layer between modules.

The current Python code is organized into four main files:

- `MainControl.py` — command entry and transmit-board serial output
- `Sensor.py` — sensor-board serial input and telemetry storage
- `Database.py` — SQLite schema and data access helpers
- `Keys.py` — command strings sent to the transmit board

---

## System overview

The intended data flow is:

1. `Sensor.py` reads a packet from the sensor ESP32 over serial.
2. The packet is parsed and written into SQLite.
3. `MainControl.py` can read the latest telemetry and abort status from SQLite.
4. `MainControl.py` sends operator commands to the control / transmit ESP32.
5. Servo states and global abort state are also persisted in SQLite so multiple modules can read the latest system status.

This structure separates responsibilities cleanly:

- **ESP32 #1** handles physical actuation / transmit-side commands.
- **ESP32 #2** handles sensor acquisition.
- **Python** handles operator interaction, logging, and shared state.

---

## File-by-file breakdown

## `Database.py`

`Database.py` is the shared persistence layer for the whole system. It opens SQLite connections, initializes the schema, stores telemetry, stores servo positions, and stores the global abort flag.

### Database path

The database file is currently hardcoded as:

```python
DB_PATH = "/Users/saltdev/rocketteam/Drexel-Rocket-Team-Ambition-One/data.db"
```

If the project is moved to another machine, this path must be updated.

### SQLite settings

Each connection enables:

- WAL journaling
- `synchronous=NORMAL`
- foreign keys
- row access by column name

This is meant to make concurrent reads and writes smoother across multiple Python modules.

### Tables

#### 1. `sensor_history`
Stores every telemetry sample.

Columns:

- `id`
- `timestamp_utc`
- `pressure_1`
- `pressure_2`
- `pressure_3`
- `force`
- `abort`
- `state`

Meaning of the last two fields:

- `abort` is an **integer flag reported by the transmit board** indicating whether an abort has been triggered.
- `state` is the **current step / phase the program is on**.

#### 2. `latest_sensor_data`
Stores only the newest telemetry snapshot for fast reads.

Columns:

- `id` (always `1`)
- `timestamp_utc`
- `pressure_1`
- `pressure_2`
- `pressure_3`
- `force`
- `abort`
- `state`

#### 3. `servo_state`
Stores the latest commanded state for four servos.

Columns:

- `id` (always `1`)
- `timestamp_utc`
- `servo_1_open`
- `servo_2_open`
- `servo_3_open`
- `servo_4_open`

These map to the valve booleans tracked in `MainControl.py`.

#### 4. `system_flags`
Stores high-level one-row flags.

Columns:

- `id` (always `1`)
- `timestamp_utc`
- `abort_flag`

This is the Python-side shared abort flag that other modules can poll.

### Main helper functions

- `initialize_database()`
  - Creates all tables if they do not exist.
  - Seeds single-row tables (`servo_state`, `system_flags`).

- `insert_sensor_reading(...)`
  - Appends a new row to `sensor_history`.
  - Updates the single latest row in `latest_sensor_data`.

- `get_latest_sensor_data()`
  - Returns the newest telemetry row as a dictionary.

- `get_sensor_history(limit=100)`
  - Returns recent telemetry samples in reverse chronological order.

- `update_servo_state(...)`
  - Stores the latest commanded servo booleans.

- `get_servo_state()`
  - Reads back the most recent servo booleans.

- `set_abort_flag(...)` / `get_abort_flag()`
  - Writes and reads the shared abort flag.

- `get_system_snapshot()`
  - Returns the latest telemetry, servo state, and abort flag in one call.

---

## `Keys.py`

`Keys.py` centralizes the short serial command strings sent to the transmit board.

### Defined commands

- `GSE_NOS_OPEN = "gn1"`
- `GSE_NOS_CLOSE = "gn0"`
- `GSE_CO2_OPEN = "gc1"`
- `GSE_CO2_CLOSE = "gc0"`
- `MPV_NOS_OPEN = "mn1"`
- `MPV_NOS_CLOSE = "mn0"`
- `MPV_E85_OPEN = "me1"`
- `MPV_E85_CLOSE = "me0"`
- `IGNITER_TRIGGER = "ig1"`
- `IGNITER_PURGE = "ig0"`

Using a separate file for keys avoids scattering literal serial strings throughout the control code.

---

## `MainControl.py`

`MainControl.py` is the operator-facing control module. Right now it acts as a simple terminal-to-serial command sender with hooks for database-backed state.

### Current configuration

```python
CONTROL_SERIAL_PORT = "/dev/cu.usbserial-0001"
CONTROL_BAUD_RATE = 115200
CONTROL_TIMEOUT_SEC = 1.0
```

This port value is currently set up like a macOS serial device and will need to be changed on other systems.

### Current tracked booleans

The file defines four booleans representing current commanded valve states:

- `gse_nos`
- `gse_co2`
- `mpv_nos`
- `mpv_e85`

These are what get written to `servo_state` when `save_servo_state()` is used.

### Other control variables

- `race_condition = True`
  - Used as the local run/abort condition.
  - `load_abort_flag()` flips it to `False` if the database abort flag is set.

- `P_F = 800.0`
- `P_N = 600.0`
- `P_MIN = 500.0`

These appear to be threshold / target pressure values reserved for future control logic.

### Main helper functions

- `open_control_serial_port()`
  - Opens the serial link to the transmit / servo ESP32.

- `initialize_main_control_module()`
  - Initializes the SQLite database.

- `save_servo_state()`
  - Persists the four valve booleans into `servo_state`.

- `load_abort_flag()`
  - Reads the shared abort flag from SQLite.
  - If the flag is set, `race_condition` becomes `False`.

- `load_servo_state()`
  - Reads back the most recent stored servo state.

- `get_sensor_data()`
  - Reads the latest telemetry row and currently returns only `pressure_1`.

- `await_user_input()`
  - Blocks on terminal input using `input("Awaiting Command: ")`.

- `send_serial_command()`
  - Sends a command string plus newline over serial.

- `run_main_control()`
  - Infinite loop:
    1. wait for user input
    2. send that command to the transmit board

### Current behavior

At the moment, `MainControl.py` is effectively a **manual command passthrough**:

- it initializes the database,
- opens the control serial port,
- waits for typed commands,
- sends them directly to the control board.

The database integration is present, but the current main loop does not yet use:

- automatic state transitions,
- pressure-based decision making,
- timeout-based command handling,
- automatic abort handling,
- or background threads.

---

## `Sensor.py`

`Sensor.py` handles telemetry intake from the sensor ESP32 and stores it in SQLite.

### Current configuration

```python
SENSOR_SERIAL_PORT = "COM5"
SENSOR_BAUD_RATE = 115200
SENSOR_TIMEOUT_SEC = 1.0
```

This port value is currently set up like a Windows COM port and will need to be updated to the actual sensor board serial device.

### Main helper functions

- `open_sensor_serial_port()`
  - Opens the serial link to the sensor ESP32.

- `initialize_sensor_module()`
  - Initializes the database.

- `read_raw_serial_line()`
  - Reads one line from serial.
  - Decodes UTF-8.
  - Strips whitespace.

- `parse_state_parameter(state)`
  - Placeholder match/case block for states `0` through `23`.
  - Currently does not perform any action.

- `parse_sensor_packet(raw_line)`
  - Parses the raw line as JSON.

- `save_sensor_packet(packet)`
  - Writes packet fields into SQLite through `insert_sensor_reading(...)`.

- `handle_sensor_stream()`
  - Infinite loop:
    1. read a line from serial
    2. parse JSON
    3. save to database
    4. sleep for 1 second

### Intended packet content

Based on the database schema and your clarification, the telemetry packet should represent:

- `p1` = pressure sensor 1
- `p2` = pressure sensor 2
- `p3` = pressure sensor 3
- `f` = force sensor
- `a` = abort integer from the transmit board
- `state` = current program step

A packet would ideally look like:

```json
{
  "p1": 0.0,
  "p2": 0.0,
  "p3": 0.0,
  "f": 0.0,
  "a": 0,
  "state": 0
}
```

### Current behavior

Right now, the code assumes JSON packets and pushes incoming telemetry into the database. It is meant to run continuously as the telemetry logger / bridge between the sensor ESP32 and SQLite.

---

## `requirements.txt`

The only declared Python dependency right now is:

```txt
pyserial>=3.5
```

This is used by both `MainControl.py` and `Sensor.py` to communicate with the two ESP32 boards.

---

## How to run

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Set the correct serial ports

Before running, update:

- `CONTROL_SERIAL_PORT` in `MainControl.py`
- `SENSOR_SERIAL_PORT` in `Sensor.py`
- optionally `DB_PATH` in `Database.py`

## 3. Start telemetry logging

Run the sensor process first so telemetry begins filling the database:

```bash
python Sensor.py
```

## 4. Start manual control

In a second terminal:

```bash
python MainControl.py
```

Then type commands such as:

```txt
gn1
gn0
gc1
gc0
mn1
mn0
me1
me0
ig1
ig0
```

---

## Shared state model

SQLite is being used as the communication layer between modules.

### Why this helps

It allows:

- one process to log telemetry,
- another process to read the latest telemetry,
- another process to watch for an abort,
- and all processes to stay synchronized through a single local database.

### Current shared values

#### Telemetry
Stored in both:

- `sensor_history` for logging
- `latest_sensor_data` for fast reads

#### Servo command state
Stored in:

- `servo_state`

#### Abort state
Stored in:

- `system_flags.abort_flag`
- telemetry field `abort`

These represent slightly different concepts:

- `abort` in telemetry is the abort status reported from the transmit side.
- `abort_flag` in `system_flags` is the Python-side shared flag used by software modules.

---

## Important notes about the current codebase

This README describes the architecture and intended role of each file, but there are still a few implementation mismatches in the current source that should be fixed.

### 1. `Sensor.py` does not currently pass `state` into the database insert

`Database.insert_sensor_reading(...)` requires:

- `pressure_1`
- `pressure_2`
- `pressure_3`
- `force`
- `abort`
- `state`

But `Sensor.py` currently calls it without a `state` argument. That means the current telemetry save path is incomplete and will need to be updated.

### 2. `Sensor.py` packet documentation does not yet list `state`

The parser currently documents JSON keys for:

- `p1`
- `p2`
- `p3`
- `f`
- `a`

but not `state`, even though the database schema expects it.

### 3. `Database.py` has a SQL syntax issue in the `latest_sensor_data` upsert

In the `ON CONFLICT ... DO UPDATE` statement, `abort = excluded.abort` and `state = excluded.state` need to be separated correctly. As written, that update statement will fail.

### 4. `MainControl.py` is still manual-only

The file contains imports and variables for more advanced logic, but the active loop is currently just:

- wait for terminal input
- send the command over serial

So the README reflects the present implementation rather than a more advanced autonomous controller.

---

## Recommended next steps

1. Update `Sensor.py` so packets include and save `state`.
2. Fix the SQL upsert statement in `Database.py`.
3. Decide whether `abort_flag` should always mirror telemetry `abort`, or whether they should remain separate concepts.
4. Add validation and error handling for malformed JSON packets.
5. Add reconnect logic for serial disconnects.
6. Expand `parse_state_parameter()` so each numeric state has documented behavior.
7. Integrate automatic abort handling and threshold logic into `MainControl.py`.

---

## Summary

This codebase already has the core structure for a solid two-board control system:

- one board for actuation,
- one board for sensing,
- and SQLite as the coordination layer between Python processes.

Right now the project is in a good intermediate state:

- the schema exists,
- serial interfaces exist,
- command keys are defined,
- telemetry logging scaffolding exists,
- and manual control works as a base.

The next phase is tightening the interfaces so the packet format, database schema, and control logic all match exactly.
