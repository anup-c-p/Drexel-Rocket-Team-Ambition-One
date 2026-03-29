import serial
from config import FAKE_MODE, SERVO_ANGLE_LIMITS

# ── Servo definitions ──────────────────────────────────────────────────────────
# Each entry: (display_name, letter)
SERVOS = [
    ('GSE_N2ratio', 'a'),
    ('GSE_N2O',     'b'),
    ('MPV_Fuel',    'c'),
    ('MPV_N2O',     'd'),
]

# ── Command definitions ────────────────────────────────────────────────────────
# Each entry: (command_name, button_bg, button_fg)
COMMANDS = [
    ('abort',     '#dc2626', '#ffffff'),   # critical — red
    ('launch',    '#16a34a', '#ffffff'),   # critical — green
    # --- separator ---
    ('go',        '#1e293b', '#ffffff'),   # operational — dark slate
    ('hold',      '#1e293b', '#ffffff'),
    ('ignite',    '#1e293b', '#ffffff'),
    ('igniteoff', '#1e293b', '#ffffff'),
]


class CommandMixin:
    def _send_command(self, command):
        if command == 'abort':
            self._trigger_abort()

        if FAKE_MODE and self.running:
            self._log_line(f'> {command}\n', '#ffdd57')
            return
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write((command + '\n').encode('utf-8'))
                self._log_line(f'> {command}\n', '#ffdd57')
            except serial.SerialException as e:
                self._set_status(f'Send failed: {e}', 'error')
        else:
            self._set_status('Not connected', 'warn')

    def _send_servo(self, letter, value):
        """Send a servo on/off or angle command, e.g. 'a on', 'b 45'."""
        self._send_command(f'{letter}_{value}')

    def _send_servo_angle(self, letter):
        """Read the angle entry for this servo, validate against limits, and send."""
        val = self.servo_angle_vars[letter].get().strip()
        if not val:
            return
        try:
            angle = float(val)
        except ValueError:
            self._set_status(f'Invalid angle value: "{val}"', 'warn')
            return
        lo, hi = SERVO_ANGLE_LIMITS.get(letter, (None, None))
        if lo is not None and not (lo <= angle <= hi):
            self._set_status(
                f'Servo {letter}: {angle}° is outside allowed range [{lo}–{hi}°]', 'warn')
            return
        # Send as integer degrees; the entry field already validated the range.
        self._send_command(f'{letter} {int(round(angle))}')
