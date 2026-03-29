import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog

from config import TAG_COLORS, DEFAULT_COLOR, DB_PATH, SERVO_ANGLE_LIMITS, FAKE_MODE
from commands import COMMANDS, SERVOS

BG       = '#f0f2f5'
PANEL    = '#ffffff'
BORDER   = '#c9cdd4'
FG       = '#111827'
FG_MUTED = '#4b5563'


class UIMixin:
    def _build_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox', fieldbackground=PANEL, background=PANEL,
                        foreground=FG, selectbackground=BORDER,
                        selectforeground=FG)
        style.map('TCombobox', fieldbackground=[('readonly', PANEL)],
                  foreground=[('readonly', FG)])

        pad = dict(padx=10, pady=5)

        # ── Top bar: port selector + connect ──────────────────────────────────
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill='x', **pad)

        tk.Label(top, text='PORT', bg=BG, fg=FG_MUTED,
                 font=('Consolas', 9, 'bold')).pack(side='left')

        self.port_var = tk.StringVar()
        self.port_cb = ttk.Combobox(top, textvariable=self.port_var, width=16, state='readonly',
                                    font=('Consolas', 10))
        self.port_cb.pack(side='left', padx=(6, 10))

        self.conn_btn = tk.Button(top, text='Connect', width=12,
                                  bg=PANEL, fg=FG, relief='solid',
                                  activebackground=BORDER, activeforeground=FG,
                                  font=('Consolas', 10, 'bold'),
                                  bd=1, highlightthickness=0,
                                  command=self._toggle_connection)
        self.conn_btn.pack(side='left')

        self.status_dot = tk.Label(top, text='●', bg=BG, fg='#9ca3af',
                                   font=('Consolas', 18))
        self.status_dot.pack(side='left', padx=8)

        tk.Button(top, text='↺  Refresh', bg=BG, fg=FG_MUTED, relief='flat',
                  activebackground=PANEL, activeforeground=FG,
                  font=('Consolas', 9),
                  command=self._refresh_ports).pack(side='left')

        # DB file picker (right side of top bar)
        tk.Button(top, text='Browse', bg=PANEL, fg=FG, relief='solid', bd=1,
                  activebackground=BORDER, activeforeground=FG,
                  font=('Consolas', 9),
                  command=self._browse_db_file).pack(side='right')

        self.db_dir_var = tk.StringVar(value=str(DB_PATH))
        self.db_dir_entry = tk.Entry(top, textvariable=self.db_dir_var,
                                     font=('Consolas', 9), width=34,
                                     bg=PANEL, fg=FG, relief='solid', bd=1,
                                     disabledbackground='#e5e7eb',
                                     disabledforeground=FG_MUTED)
        self.db_dir_entry.pack(side='right', padx=(0, 4))

        tk.Label(top, text='DB FILE', bg=BG, fg=FG_MUTED,
                 font=('Consolas', 9, 'bold')).pack(side='right', padx=(16, 4))

        # ── FAKE MODE banner (persistent, only shown when FAKE_MODE is True) ──
        if FAKE_MODE:
            tk.Label(self.root,
                     text='  [!]  FAKE MODE ACTIVE — simulated data only, no real device connected  [!]',
                     bg='#92400e', fg='#fef3c7',
                     font=('Consolas', 9, 'bold'),
                     anchor='center', pady=4
                     ).pack(fill='x', padx=10, pady=(0, 2))

        # ── Status bar (warnings / errors from the app, not device data) ─────
        self._status_clear_id = None
        self.status_bar = tk.Label(self.root, text='', bg=BG, fg=BG,
                                   font=('Consolas', 9, 'bold'),
                                   anchor='w', padx=14, pady=3)
        self.status_bar.pack(fill='x', padx=10)

        # ── Abort banner (hidden until abort is active) ───────────────────────
        self.abort_banner = tk.Label(
            self.root,
            text='  ⚠  ABORT ACTIVE — engine abort triggered  ⚠',
            bg='#dc2626', fg='#ffffff',
            font=('Consolas', 12, 'bold'),
            anchor='center', pady=8,
        )
        # Not packed initially — shown via _trigger_abort()

        # ── Sensor data panel ─────────────────────────────────────────────────
        sensor_frame = tk.LabelFrame(self.root, text='  SENSOR DATA  ',
                                     bg=PANEL, fg=FG_MUTED,
                                     font=('Consolas', 9, 'bold'),
                                     relief='flat', bd=1,
                                     highlightbackground=BORDER)
        sensor_frame.pack(fill='x', **pad)

        fields = [
            ('t',        'TIME (ms)',  7),
            ('abs_time', 'ABS TIME',  12),
            ('vP0',      'P0 (PSI)',   8),
            ('vP1',      'P1 (PSI)',   8),
            ('vP2',      'P2 (PSI)',   8),
            ('vF',       'F (mV)',     8),
            ('rssi',     'RSSI',       7),
        ]
        self.sensor_vars = {}
        for col, (key, label, w) in enumerate(fields):
            cell = tk.Frame(sensor_frame, bg=PANEL)
            cell.grid(row=0, column=col, padx=18, pady=10)
            tk.Label(cell, text=label, bg=PANEL, fg=FG_MUTED,
                     font=('Consolas', 9)).pack()
            var = tk.StringVar(value='—')
            self.sensor_vars[key] = var
            tk.Label(cell, textvariable=var, bg=PANEL, fg=FG,
                     font=('Consolas', 17, 'bold'), width=w).pack()

        # Servo state indicators (second row of sensor panel)
        servo_state_row = tk.Frame(sensor_frame, bg=PANEL)
        servo_state_row.grid(row=1, column=0, columnspan=len(fields),
                             padx=18, pady=(0, 10), sticky='w')
        tk.Label(servo_state_row, text='SERVOS', bg=PANEL, fg=FG_MUTED,
                 font=('Consolas', 9, 'bold')).pack(side='left', padx=(0, 14))
        self.servo_state_labels = {}
        for name, letter in SERVOS:
            tk.Label(servo_state_row, text=name, bg=PANEL, fg=FG_MUTED,
                     font=('Consolas', 9)).pack(side='left', padx=(0, 4))
            lbl = tk.Label(servo_state_row, text='OFF',
                           bg='#6b7280', fg='#ffffff',
                           font=('Consolas', 9, 'bold'), width=4, padx=4)
            lbl.pack(side='left', padx=(0, 18))
            self.servo_state_labels[letter] = lbl

        # ── Command buttons ───────────────────────────────────────────────────
        cmd_frame = tk.LabelFrame(self.root, text='  COMMANDS  ',
                                  bg=PANEL, fg=FG_MUTED,
                                  font=('Consolas', 9, 'bold'),
                                  relief='flat', bd=1)
        cmd_frame.pack(fill='x', **pad)

        # Critical group: ABORT + LAUNCH
        critical = [c for c in COMMANDS if c[0] in ('abort', 'launch')]
        # Operational group: everything else
        operational = [c for c in COMMANDS if c[0] not in ('abort', 'launch')]

        col = 0
        for cmd, bg, fg in critical:
            btn = tk.Button(cmd_frame,
                            text=cmd.upper(),
                            width=12, pady=12,
                            bg=bg, fg=fg, relief='flat',
                            font=('Consolas', 12, 'bold'),
                            activebackground=bg, activeforeground=fg,
                            command=lambda c=cmd: self._send_command(c))
            btn.grid(row=0, column=col, padx=(8, 4), pady=10)
            col += 1

        # Vertical separator
        tk.Frame(cmd_frame, bg=BORDER, width=2).grid(
            row=0, column=col, padx=10, pady=6, sticky='ns')
        col += 1

        for cmd, bg, fg in operational:
            btn = tk.Button(cmd_frame,
                            text=cmd.upper(),
                            width=12, pady=12,
                            bg=bg, fg=fg, relief='flat',
                            font=('Consolas', 12, 'bold'),
                            activebackground=bg, activeforeground=fg,
                            command=lambda c=cmd: self._send_command(c))
            btn.grid(row=0, column=col, padx=(4, 8), pady=10)
            col += 1

        # ── Servo control (collapsible, 2×2 horizontal layout) ────────────────
        servo_wrapper = tk.Frame(self.root, bg=BG)
        servo_wrapper.pack(fill='x')

        servo_header = tk.Frame(servo_wrapper, bg=BG)
        servo_header.pack(fill='x', padx=10, pady=(6, 0))

        self.servo_visible = tk.BooleanVar(value=False)
        self.servo_toggle_btn = tk.Button(servo_header, text='►  Servo Control',
                                          bg=BG, fg=FG_MUTED,
                                          font=('Consolas', 10), relief='flat',
                                          activebackground=PANEL, activeforeground=FG,
                                          command=self._toggle_servo)
        self.servo_toggle_btn.pack(side='left')

        self.servo_content = tk.Frame(servo_wrapper, bg=PANEL,
                                      highlightbackground=BORDER, highlightthickness=1)
        # Starts collapsed — content is built but not packed yet.

        self.servo_angle_vars = {}
        for group_servos, side_pad in [(SERVOS[:2], (4, 0)), (SERVOS[2:], (0, 4))]:
            group = tk.Frame(self.servo_content, bg=PANEL)
            group.pack(side='left', fill='y', padx=side_pad, pady=6)

            if side_pad == (4, 0):   # add separator after left group
                tk.Frame(self.servo_content, bg=BORDER, width=2).pack(
                    side='left', fill='y', padx=16, pady=8)

            for row, (name, letter) in enumerate(group_servos):
                lo, hi = SERVO_ANGLE_LIMITS.get(letter, (None, None))

                tk.Label(group, text=f'{name}  [{letter}]',
                         bg=PANEL, fg=FG, font=('Consolas', 10, 'bold'),
                         width=16, anchor='w').grid(row=row, column=0, padx=(8, 4), pady=6)

                tk.Button(group, text='ON', width=6, pady=5,
                          bg='#16a34a', fg='#ffffff', relief='flat',
                          font=('Consolas', 10, 'bold'),
                          activebackground='#15803d', activeforeground='#ffffff',
                          command=lambda l=letter: self._send_servo(l, 'on')
                          ).grid(row=row, column=1, padx=3, pady=6)

                tk.Button(group, text='OFF', width=6, pady=5,
                          bg='#dc2626', fg='#ffffff', relief='flat',
                          font=('Consolas', 10, 'bold'),
                          activebackground='#b91c1c', activeforeground='#ffffff',
                          command=lambda l=letter: self._send_servo(l, 'off')
                          ).grid(row=row, column=2, padx=3, pady=6)

                var = tk.StringVar()
                self.servo_angle_vars[letter] = var
                tk.Entry(group, textvariable=var, font=('Consolas', 10), width=6,
                         bg=PANEL, fg=FG, relief='solid', bd=1, justify='center'
                         ).grid(row=row, column=3, padx=(10, 2), pady=6)

                limit_text = f'° {lo}–{hi}' if lo is not None else '°'
                tk.Label(group, text=limit_text, bg=PANEL, fg=FG_MUTED,
                         font=('Consolas', 8)).grid(row=row, column=4, padx=(0, 6), sticky='w')

                tk.Button(group, text='SET', width=6, pady=5,
                          bg='#1e293b', fg='#ffffff', relief='flat',
                          font=('Consolas', 10, 'bold'),
                          activebackground='#334155', activeforeground='#ffffff',
                          command=lambda l=letter: self._send_servo_angle(l)
                          ).grid(row=row, column=5, padx=(2, 8), pady=6)

        # ── Structured log (collapsible, three resizable panels) ─────────────
        _LOG_PANELS = [('SEQ', 'seq'), ('LoRa', 'lora'), ('Sensor', 'sensor')]
        self.log_visible = tk.BooleanVar(value=True)
        log_header = tk.Frame(self.root, bg=BG)
        log_header.pack(fill='x', padx=10, pady=(6, 4))

        self.toggle_btn = tk.Button(log_header, text='▼  Structured Log',
                                    bg=BG, fg=FG_MUTED,
                                    font=('Consolas', 10), relief='flat',
                                    activebackground=PANEL, activeforeground=FG,
                                    command=self._toggle_log)
        self.toggle_btn.pack(side='left')

        # Per-panel visibility toggles
        self.log_panel_vars = {}
        for title, key in _LOG_PANELS:
            var = tk.BooleanVar(value=True)
            self.log_panel_vars[key] = var
            tk.Checkbutton(log_header, text=title, variable=var,
                           command=lambda k=key: self._toggle_log_panel(k),
                           bg=BG, fg=FG_MUTED, selectcolor=BG,
                           activebackground=BG, activeforeground=FG,
                           font=('Consolas', 9)).pack(side='left', padx=(10, 0))

        tk.Button(log_header, text='Clear', bg=BG, fg=FG_MUTED,
                  font=('Consolas', 10), relief='flat',
                  activebackground=PANEL, activeforeground=FG,
                  command=self._clear_log).pack(side='right')

        # ── Raw log section (anchored at bottom, closed by default) ──────────
        # Must be packed with side='bottom' BEFORE log_frame so it doesn't get
        # crowded out when log_frame uses expand=True.
        self.raw_log_visible = tk.BooleanVar(value=False)
        raw_log_section = tk.Frame(self.root, bg=BG)
        raw_log_section.pack(side='bottom', fill='x', padx=10, pady=(0, 6))

        raw_log_hdr = tk.Frame(raw_log_section, bg=BG)
        raw_log_hdr.pack(fill='x')
        self.raw_toggle_btn = tk.Button(raw_log_hdr, text='►  Raw Log',
                                        bg=BG, fg=FG_MUTED,
                                        font=('Consolas', 10), relief='flat',
                                        activebackground=PANEL, activeforeground=FG,
                                        command=self._toggle_raw_log)
        self.raw_toggle_btn.pack(side='left')
        tk.Button(raw_log_hdr, text='Clear', bg=BG, fg=FG_MUTED,
                  font=('Consolas', 10), relief='flat',
                  activebackground=PANEL, activeforeground=FG,
                  command=self._clear_raw_log).pack(side='right')

        self.raw_log_content = tk.Frame(raw_log_section, bg=PANEL)
        # Not packed initially — shown via _toggle_raw_log()
        self.raw_log_box = scrolledtext.ScrolledText(
            self.raw_log_content, bg=PANEL, fg=DEFAULT_COLOR,
            font=('Consolas', 10), relief='flat', state='disabled',
            wrap='word', height=8, insertbackground=FG,
            bd=1, highlightbackground=BORDER,
        )
        self.raw_log_box.pack(fill='both', expand=True)

        # ── Structured log frame ──────────────────────────────────────────────
        self.log_frame = tk.Frame(self.root, bg=BG)
        self.log_frame.pack(fill='both', expand=True, padx=10, pady=(2, 4))

        # Resizable side-by-side panels via PanedWindow (drag sash to resize)
        self.log_paned = ttk.PanedWindow(self.log_frame, orient='horizontal')
        self.log_paned.pack(fill='both', expand=True)

        self.log_boxes = {}
        self.log_panes = {}
        for title, key in _LOG_PANELS:
            pane = tk.Frame(self.log_paned, bg=PANEL,
                            highlightbackground=BORDER, highlightthickness=1)
            tk.Label(pane, text=title, bg=PANEL, fg=FG_MUTED,
                     font=('Consolas', 9, 'bold'), anchor='w',
                     padx=6, pady=3).pack(fill='x')
            tk.Frame(pane, bg=BORDER, height=1).pack(fill='x')
            box = scrolledtext.ScrolledText(
                pane, bg=PANEL, fg=DEFAULT_COLOR,
                font=('Consolas', 10), relief='flat', state='disabled',
                wrap='word', height=10, insertbackground=FG, bd=0,
            )
            box.pack(fill='both', expand=True)
            self.log_boxes[key] = box
            self.log_panes[key] = pane
            self.log_paned.add(pane, weight=1)

        # Pre-register every color tag on all boxes so _log_line
        # never needs to call tag_config() after startup.
        self._log_tags: set = set()
        _known_colors = (
            list(TAG_COLORS.values())
            + [DEFAULT_COLOR,
               '#ffaa00',   # fake/connect
               '#e74c3c',   # errors
               '#ffdd57',   # sent commands
               '#dc2626',   # abort
               '#16a34a',   # abort cleared / SQL ok
               ]
        )
        for _color in _known_colors:
            _tag = f'color_{_color.replace("#", "")}'
            for _box in list(self.log_boxes.values()) + [self.raw_log_box]:
                _box.tag_config(_tag, foreground=_color)
            self._log_tags.add(_tag)

        self._last_log_line: dict = {}   # last text written per panel key

        # ── Custom serial command entry ────────────────────────────────────────
        cmd_row = tk.Frame(self.log_frame, bg=PANEL)
        cmd_row.pack(fill='x', padx=4, pady=(4, 4))

        tk.Label(cmd_row, text='CMD', bg=PANEL, fg=FG_MUTED,
                 font=('Consolas', 9, 'bold')).pack(side='left', padx=(4, 6))

        self.custom_cmd_var = tk.StringVar()
        cmd_entry = tk.Entry(cmd_row, textvariable=self.custom_cmd_var,
                             font=('Consolas', 10), bg=PANEL, fg=FG,
                             relief='solid', bd=1, insertbackground=FG)
        cmd_entry.pack(side='left', fill='x', expand=True, padx=(0, 6))
        cmd_entry.bind('<Return>', lambda _e: self._send_custom_command())

        tk.Button(cmd_row, text='Send', width=8, pady=3,
                  bg='#1e293b', fg='#ffffff', relief='flat',
                  font=('Consolas', 10, 'bold'),
                  activebackground='#334155', activeforeground='#ffffff',
                  command=self._send_custom_command).pack(side='right', padx=(0, 4))

        # Snapshot the initial required height so _fit_height can work by delta.
        self.root.update_idletasks()
        self._last_req_height = self.root.winfo_reqheight()

    def _browse_db_file(self):
        from pathlib import Path
        current = Path(self.db_dir_var.get())
        f = filedialog.asksaveasfilename(
            initialdir=str(current.parent),
            initialfile=current.name,
            defaultextension='.db',
            filetypes=[('SQLite database', '*.db'), ('All files', '*.*')],
            confirmoverwrite=False,
        )
        if f:
            self.db_dir_var.set(f)

    # ── Status bar ─────────────────────────────────────────────────────────────

    def _set_status(self, msg, level='warn'):
        if level == 'warn':
            self.status_bar.config(text=f'  [WARN]  {msg}', fg='#92400e', bg='#fef3c7')
        else:
            self.status_bar.config(text=f'  [ERROR]  {msg}', fg='#7f1d1d', bg='#fee2e2')
        if self._status_clear_id:
            self.root.after_cancel(self._status_clear_id)
        self._status_clear_id = self.root.after(5000, self._clear_status)

    def _clear_status(self):
        self.status_bar.config(text='', bg=BG, fg=BG)
        self._status_clear_id = None

    def _update_servo_state_ui(self, states: dict):
        """Update the servo ON/OFF indicator labels in the sensor panel."""
        for letter, is_open in states.items():
            lbl = self.servo_state_labels.get(letter)
            if lbl:
                if is_open:
                    lbl.config(text='ON', bg='#16a34a')
                else:
                    lbl.config(text='OFF', bg='#6b7280')

    def _trigger_abort(self):
        if self.abort_active:
            return
        self.abort_active = True
        self.abort_banner.pack(fill='x', padx=10, pady=(0, 4), after=self.status_bar)
        self.sql_logger.set_abort_flag(True)
        self._log_line('[ABORT] Abort triggered — pressure threshold exceeded or abort commanded\n', '#dc2626')

    def _toggle_servo(self):
        if self.servo_visible.get():
            self.servo_content.pack_forget()
            self.servo_toggle_btn.config(text='►  Servo Control')
            self.servo_visible.set(False)
        else:
            self.servo_content.pack(fill='x', padx=10, pady=(2, 5))
            self.servo_toggle_btn.config(text='▼  Servo Control')
            self.servo_visible.set(True)
        self._fit_height()

    def _fit_height(self):
        self.root.update_idletasks()
        req_h = self.root.winfo_reqheight()
        delta = req_h - self._last_req_height
        self._last_req_height = req_h
        if delta != 0:
            new_h = max(1, self.root.winfo_height() + delta)
            self.root.geometry(f'{self.root.winfo_width()}x{new_h}')

    # ── Log helpers ────────────────────────────────────────────────────────────

    def _log_line(self, text, color=DEFAULT_COLOR):
        if '[Poll]' in text:
            return
        tag = f'color_{color.replace("#","")}'
        if tag not in self._log_tags:
            for box in list(self.log_boxes.values()) + [self.raw_log_box]:
                box.tag_config(tag, foreground=color)
            self._log_tags.add(tag)

        # ── Raw log: every non-Poll line ─────────────────────────────────────
        if self._last_log_line.get('_raw') != text:
            self._last_log_line['_raw'] = text
            self.raw_log_box.config(state='normal')
            self.raw_log_box.insert('end', text, tag)
            self.raw_log_box.see('end')
            self.raw_log_box.config(state='disabled')

        # ── Structured panels: additional filters ────────────────────────────
        if '[LoRa] poll sent, waiting for response' in text:
            return
        if '[SEQ] >>> send "go" to confirm or "hold" to abort' in text:
            return
        if '[SEQ]' in text:
            targets = [self.log_boxes['seq']]
        elif '[LoRa]' in text or '[CMD]' in text or '[ACK]' in text:
            targets = [self.log_boxes['lora']]
        elif '[Sensor]' in text:
            targets = [self.log_boxes['sensor']]
        else:
            return
        for box in targets:
            key = next(k for k, b in self.log_boxes.items() if b is box)
            if self._last_log_line.get(key) == text:
                continue
            self._last_log_line[key] = text
            box.config(state='normal')
            box.insert('end', text, tag)
            box.see('end')
            box.config(state='disabled')

    def _clear_log(self):
        self._last_log_line.clear()
        for box in self.log_boxes.values():
            box.config(state='normal')
            box.delete('1.0', 'end')
            box.config(state='disabled')

    def _send_custom_command(self):
        val = self.custom_cmd_var.get().strip()
        if not val:
            return
        self._send_command(val)
        self.custom_cmd_var.set('')

    def _toggle_log(self):
        if self.log_visible.get():
            self.log_frame.pack_forget()
            self.toggle_btn.config(text='►  Structured Log')
            self.log_visible.set(False)
        else:
            self.log_frame.pack(fill='both', expand=True, padx=10, pady=(2, 4))
            self.toggle_btn.config(text='▼  Structured Log')
            self.log_visible.set(True)
        self._fit_height()

    def _toggle_raw_log(self):
        if self.raw_log_visible.get():
            self.raw_log_content.pack_forget()
            self.raw_toggle_btn.config(text='►  Raw Log')
            self.raw_log_visible.set(False)
        else:
            self.raw_log_content.pack(fill='both', expand=True, pady=(2, 0))
            self.raw_toggle_btn.config(text='▼  Raw Log')
            self.raw_log_visible.set(True)
        self._fit_height()

    def _clear_raw_log(self):
        self._last_log_line.pop('_raw', None)
        self.raw_log_box.config(state='normal')
        self.raw_log_box.delete('1.0', 'end')
        self.raw_log_box.config(state='disabled')

    def _toggle_log_panel(self, key):
        _order = ['seq', 'lora', 'sensor']
        if self.log_panel_vars[key].get():
            # Count visible earlier panels to find insertion position
            pos = sum(1 for k in _order[:_order.index(key)]
                      if self.log_panel_vars[k].get())
            current = len(self.log_paned.panes())
            if pos >= current:
                self.log_paned.add(self.log_panes[key], weight=1)
            else:
                self.log_paned.insert(pos, self.log_panes[key], weight=1)
        else:
            self.log_paned.forget(self.log_panes[key])
