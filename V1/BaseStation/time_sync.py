from datetime import datetime, timedelta


class TimeSync:
    """Maps device-relative time (ms) to wall-clock absolute time.

    The device reports cumulative milliseconds since its own boot, not since
    we connected. So we anchor on the *first* sensor reading we receive:
      absolute_time = session_start + (t_ms - first_t_ms)

    This means the first reading always shows the exact connection time, and
    subsequent readings drift naturally from there.
    """

    def __init__(self):
        self._session_start: datetime | None = None
        self._first_device_ms: int | None = None

    def start(self):
        """Call when a connection is established."""
        self._session_start = datetime.now()
        self._first_device_ms = None

    def reset(self):
        """Call when disconnected."""
        self._session_start = None
        self._first_device_ms = None

    def to_absolute(self, t_ms: int) -> datetime | None:
        """Return the wall-clock datetime for a device timestamp in ms."""
        if self._session_start is None:
            return None
        if self._first_device_ms is None:
            self._first_device_ms = t_ms
        elapsed_ms = t_ms - self._first_device_ms
        return self._session_start + timedelta(milliseconds=elapsed_ms)

    def format(self, t_ms: int) -> str:
        """Return a formatted HH:MM:SS.mmm string, or '—' if not started."""
        dt = self.to_absolute(t_ms)
        if dt is None:
            return '—'
        return dt.strftime('%H:%M:%S.') + f'{dt.microsecond // 1000:03d}'
