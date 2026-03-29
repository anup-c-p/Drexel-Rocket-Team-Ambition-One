import serial
import serial.tools.list_ports
import threading
import queue
from pathlib import Path

from config import BAUD_RATE, FAKE_MODE, SENSOR_RE, SERVO_RE, TAG_COLORS, DEFAULT_COLOR, PRESSURE_ABORT_THRESHOLD_V
from fake_data import fake_loop
from unit_converter import UnitConverter


class SerialMixin:
    # ── Port management ────────────────────────────────────────────────────────

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_cb['values'] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])

    def _toggle_connection(self):
        if self.running:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        if FAKE_MODE:
            self.running = True
            self.conn_btn.config(text='Disconnect')
            self.db_dir_entry.config(state='disabled')
            self.status_dot.config(fg='#ffaa00')   # orange = fake
            self._log_line('[FAKE MODE] Simulating serial data\n', '#ffaa00')
            try:
                self.logger.start()
            except OSError as e:
                self._log_line(f'[ERROR] Log file init failed: {e}\n', '#e74c3c')
            self.time_sync.start()
            self.sql_logger.set_db_path(Path(self.db_dir_var.get()))
            self.sql_logger.start(self._log_line)
            threading.Thread(target=fake_loop, args=(self.rx_queue, lambda: self.running), daemon=True).start()
            return

        port = self.port_var.get()
        if not port:
            self._set_status('No port selected — pick a COM port first', 'warn')
            return
        try:
            self.serial_port = serial.Serial(port, BAUD_RATE, timeout=1, write_timeout=1)
            self.running = True
            self.conn_btn.config(text='Disconnect')
            self.db_dir_entry.config(state='disabled')
            self.status_dot.config(fg='#00ff88')
            try:
                self.logger.start()
            except OSError as e:
                self._log_line(f'[ERROR] Log file init failed: {e}\n', '#e74c3c')
            self.time_sync.start()
            self.sql_logger.set_db_path(Path(self.db_dir_var.get()))
            self.sql_logger.start(self._log_line)
            threading.Thread(target=self._read_loop, daemon=True).start()
        except serial.SerialException as e:
            self._log_line(f'[ERROR] {e}\n', '#e74c3c')

    def _disconnect(self):
        if not self.running:
            return
        self.running = False
        self.logger.stop()
        self.sql_logger.stop()
        self.time_sync.reset()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_port = None
        self.conn_btn.config(text='Connect')
        self.db_dir_entry.config(state='normal')
        self.status_dot.config(fg='#9ca3af')

    def _on_close(self):
        """Clean shutdown: cancel the pending drain callback, disconnect, destroy window."""
        if self._drain_after_id:
            self.root.after_cancel(self._drain_after_id)
            self._drain_after_id = None
        self._disconnect()
        self.root.destroy()

    # ── Serial read thread ─────────────────────────────────────────────────────

    def _read_loop(self):
        while self.running:
            try:
                line = self.serial_port.readline().decode('utf-8', errors='replace')
                if line:
                    try:
                        self.rx_queue.put_nowait(line)
                    except queue.Full:
                        pass  # drop rather than block the read thread
            except (serial.SerialException, OSError):
                self.rx_queue.put(None)   # signal disconnect
                break

    # ── Queue drain (main thread) ──────────────────────────────────────────────

    def _drain_queue(self):
        try:
            for _ in range(30):   # cap per cycle to keep main thread responsive
                line = self.rx_queue.get_nowait()
                if line is None:
                    self._disconnect()
                    break
                self._process_line(line)
        except queue.Empty:
            pass
        self._drain_after_id = self.root.after(50, self._drain_queue)

    def _process_line(self, line):
        self.logger.log_raw(line)

        m = SENSOR_RE.search(line)
        if m:
            t, vP0, vP1, vP2, vF, rssi = m.groups()
            abs_dt = self.time_sync.to_absolute(int(t))

            # UI: show converted engineering units
            self.sensor_vars['t'].set(t)
            self.sensor_vars['abs_time'].set(self.time_sync.format(int(t)))
            self.sensor_vars['vP0'].set(f'{UnitConverter.voltage_to_psi(float(vP0)):.1f}')
            self.sensor_vars['vP1'].set(f'{UnitConverter.voltage_to_psi(float(vP1)):.1f}')
            self.sensor_vars['vP2'].set(f'{UnitConverter.voltage_to_psi(float(vP2)):.1f}')
            self.sensor_vars['vF'].set(f'{UnitConverter.voltage_to_lbf(float(vF)):.2f}')
            self.sensor_vars['rssi'].set(rssi)

            # Logs/SQL: always raw voltages
            self.logger.log_sensor(t, vP0, vP1, vP2, vF, rssi, abs_datetime=abs_dt)
            self.sql_logger.log_sensor(t, vP0, vP1, vP2, vF, rssi)

            # Abort if pressure sensor 0 exceeds the voltage threshold
            if not self.abort_active:
                if float(vP0) > PRESSURE_ABORT_THRESHOLD_V:
                    self._trigger_abort()

        sm = SERVO_RE.search(line)
        if sm:
            sa, sb, sc, sd = sm.groups()
            servo_states = {
                'a': bool(int(sa)),
                'b': bool(int(sb)),
                'c': bool(int(sc)),
                'd': bool(int(sd)),
            }
            if servo_states != self._last_servo_states:
                self._last_servo_states = servo_states
                self._update_servo_state_ui(servo_states)
                self.sql_logger.update_servo_state(
                    servo_states['a'], servo_states['b'],
                    servo_states['c'], servo_states['d'],
                )

        color = DEFAULT_COLOR
        for tag in TAG_COLORS:
            if tag in line:
                color = TAG_COLORS[tag]
                break

        self._log_line(line, color)