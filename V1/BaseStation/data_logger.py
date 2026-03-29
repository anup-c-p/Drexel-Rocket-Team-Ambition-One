import os
from datetime import datetime

# Folder is always created next to the script, regardless of working directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class DataLogger:
    """Opens two timestamped files on start() and closes them on stop().

    Files created per session:
      data/YYYY-MM-DD_HH-MM-SS_raw_log.txt   — every raw line with a timestamp prefix
      data/YYYY-MM-DD_HH-MM-SS_sensor.csv    — parsed sensor readings in CSV format
    """

    def __init__(self):
        self._raw_file    = None
        self._sensor_file = None

    def start(self):
        """Call when a connection is established."""
        os.makedirs(DATA_DIR, exist_ok=True)
        ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self._raw_file = open(
            os.path.join(DATA_DIR, f'{ts}_raw_log.txt'), 'w', encoding='utf-8'
        )
        self._sensor_file = open(
            os.path.join(DATA_DIR, f'{ts}_sensor.csv'), 'w', encoding='utf-8'
        )
        self._sensor_file.write('datetime,abs_datetime,t_ms,vP0,vP1,vP2,vF,rssi\n')
        self._sensor_file.flush()

    def stop(self):
        """Call when the connection is closed."""
        for f in (self._raw_file, self._sensor_file):
            if f:
                f.close()
        self._raw_file    = None
        self._sensor_file = None

    def log_raw(self, line: str):
        """Write one raw serial line with a datetime prefix."""
        if not self._raw_file:
            return
        ts = _now()
        self._raw_file.write(f'[{ts}] {line}')
        self._raw_file.flush()

    def log_sensor(self, t, vP0, vP1, vP2, vF, rssi, abs_datetime=None):
        """Append one parsed sensor reading to the CSV."""
        if not self._sensor_file:
            return
        ts = _now()
        abs_ts = abs_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if abs_datetime else ''
        self._sensor_file.write(f'{ts},{abs_ts},{t},{vP0},{vP1},{vP2},{vF},{rssi}\n')
        self._sensor_file.flush()


def _now() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
