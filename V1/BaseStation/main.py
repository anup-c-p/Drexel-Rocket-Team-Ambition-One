import tkinter as tk
import queue

from ui import UIMixin
from serial_io import SerialMixin
from commands import CommandMixin
from data_logger import DataLogger
from time_sync import TimeSync
from sql_logger import SQLLogger


class SerialMonitor(UIMixin, SerialMixin, CommandMixin):
    def __init__(self, root):
        self.root = root
        self.root.title('Base Station')
        self.root.configure(bg='#f0f2f5')
        self.root.resizable(True, True)

        self.serial_port = None
        self.running = False
        self.abort_active = False
        self._last_servo_states = {}
        self.rx_queue = queue.Queue(maxsize=1000)
        self._drain_after_id = None
        self.logger = DataLogger()
        self.time_sync = TimeSync()
        self.sql_logger = SQLLogger()

        self._build_ui()
        self._refresh_ports()
        self.sql_logger.start(self._log_line)
        self._drain_after_id = self.root.after(50, self._drain_queue)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('980x650')
    app = SerialMonitor(root)
    root.protocol('WM_DELETE_WINDOW', app._on_close)
    root.mainloop()