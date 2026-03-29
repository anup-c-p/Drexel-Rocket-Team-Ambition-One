import os
import re
from pathlib import Path

# ── Serial config ──────────────────────────────────────────────────────────────
BAUD_RATE = 115200

# ── Default path for the SQLite session file ──────────────────────────────────
DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / 'data' / 'session.db'

# ── Unit conversion constants ──────────────────────────────────────────────────
ATMOSPHERIC_PRESSURE_PSI = 14.696   # standard atmosphere, used as offset in pressure conversion
V_INPUT = 5.0                        # supply voltage to force transducer (volts)

# ── Per-servo angle limits (degrees) ──────────────────────────────────────────
# Keys match the alphabet mapping in commands.py SERVOS list.
SERVO_ANGLE_LIMITS = {
    'a': (0, 180),   # GSE_N2ratio
    'b': (0, 180),   # GSE_N2O
    'c': (0,  90),   # MPV_Fuel
    'd': (0,  90),   # MPV_N2O
}

# ── Abort threshold (voltage) ─────────────────────────────────────────────────
# Any pressure sensor reading (vP0, vP1, vP2) above this value triggers abort.
PRESSURE_ABORT_THRESHOLD_V = 4.9

# ── Fake mode — set to False when real device is connected ────────────────────
FAKE_MODE = False

# ── Sensor line parser ────────────────────────────────────────────────────────
SENSOR_RE = re.compile(
    r'\[Sensor\]\s+t=(\d+)ms\s+'
    r'vP0=(-?[\d.]+)V\s+vP1=(-?[\d.]+)V\s+vP2=(-?[\d.]+)V\s+'
    r'vF=(-?[\d.]+)V\s+rssi=(-?\d+)'
)

# Servo state arrives on the line immediately after the sensor line
SERVO_RE = re.compile(r'a=([01])\s+b=([01])\s+c=([01])\s+d=([01])')

# ── Color map for raw log tags ─────────────────────────────────────────────────
TAG_COLORS = {
    '[Sensor]': '#15803d',   # dark green
    '[Poll]':   '#374151',   # dark gray
    '[LoRa]':   '#1d4ed8',   # dark blue
    '[SEQ]':    '#b45309',   # amber/brown
}
DEFAULT_COLOR = '#111827'
