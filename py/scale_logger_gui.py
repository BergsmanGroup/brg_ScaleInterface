"""
Simple GUI wrapper for scale_logger.monitor_scale() with a live textbox console.

Requires:
  pip install pyserial

Files:
  - scale_logger.py
  - scale_logger_gui.py
"""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

import scale_logger  # must define monitor_scale(...)


class TextRedirector:
    """
    File-like object that sends writes into a queue.
    Safe for use from background threads.
    """
    def __init__(self, q: queue.Queue[str]) -> None:
        self.q = q

    def write(self, s: str) -> None:
        if s:
            self.q.put(s)

    def flush(self) -> None:
        # Needed for file-like compatibility
        pass


class ScaleLoggerGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Scale Logger")
        self.geometry("700x520")

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        # Queue for console output
        self._out_q: queue.Queue[str] = queue.Queue()

        # Redirect stdout/stderr for this process (GUI + worker thread prints)
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        sys.stdout = TextRedirector(self._out_q)
        sys.stderr = TextRedirector(self._out_q)

        # ----- Variables -----
        self.var_port = tk.StringVar(value="COM3")
        self.var_baud = tk.IntVar(value=9600)
        self.var_timeout = tk.DoubleVar(value=1.0)
        self.var_duration = tk.StringVar(value="")  # blank => continuous
        self.var_units = tk.StringVar(value="")
        self.var_regex = tk.StringVar(value=r"([-+]?\d*\.?\d+)")
        self.var_outfile = tk.StringVar(value="")  # blank => auto
        self.var_clearbuf = tk.BooleanVar(value=True)

        self._build_ui()
        self._set_running(False)

        # Start polling console queue
        self.after(50, self._drain_console_queue)

        # Clean shutdown handling
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill="both", expand=True)

        # Top controls
        controls = ttk.Frame(outer)
        controls.pack(fill="x")

        controls.columnconfigure(1, weight=1)

        r = 0
        ttk.Label(controls, text="COM Port:").grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.var_port, width=12).grid(row=r, column=1, sticky="w", pady=4)

        r += 1
        ttk.Label(controls, text="Baudrate:").grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.var_baud, width=12).grid(row=r, column=1, sticky="w", pady=4)

        r += 1
        ttk.Label(controls, text="Timeout (s):").grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.var_timeout, width=12).grid(row=r, column=1, sticky="w", pady=4)

        r += 1
        ttk.Label(controls, text="Duration (s):").grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.var_duration, width=12).grid(row=r, column=1, sticky="w", pady=4)
        ttk.Label(controls, text="(blank = continuous)").grid(row=r, column=2, sticky="w", pady=4)

        r += 1
        ttk.Label(controls, text="Units (display only):").grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.var_units).grid(row=r, column=1, sticky="ew", pady=4)

        r += 1
        ttk.Label(controls, text="Value regex:").grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.var_regex).grid(row=r, column=1, sticky="ew", pady=4)

        r += 1
        ttk.Label(controls, text="Output CSV:").grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(controls, textvariable=self.var_outfile).grid(row=r, column=1, sticky="ew", pady=4)
        ttk.Label(controls, text="(blank = auto name)").grid(row=r, column=2, sticky="w", pady=4)

        r += 1
        ttk.Checkbutton(
            controls, text="Clear serial buffer on start", variable=self.var_clearbuf
        ).grid(row=r, column=0, columnspan=2, sticky="w", pady=6)

        # Buttons + status
        btn_row = ttk.Frame(outer)
        btn_row.pack(fill="x", pady=(6, 6))

        self.btn_start = ttk.Button(btn_row, text="Start", command=self.on_start)
        self.btn_start.pack(side="left")

        self.btn_stop = ttk.Button(btn_row, text="Stop", command=self.on_stop)
        self.btn_stop.pack(side="left", padx=8)

        self.btn_clear = ttk.Button(btn_row, text="Clear Console", command=self.clear_console)
        self.btn_clear.pack(side="left", padx=8)

        self.lbl_status = ttk.Label(btn_row, text="Idle")
        self.lbl_status.pack(side="left", padx=12)

        # Console textbox
        ttk.Label(outer, text="Console:").pack(anchor="w")
        self.txt_console = ScrolledText(outer, height=18, wrap="word")
        self.txt_console.pack(fill="both", expand=True)
        self.txt_console.configure(state="disabled")

    def _set_running(self, running: bool) -> None:
        self.btn_start.configure(state=("disabled" if running else "normal"))
        self.btn_stop.configure(state=("normal" if running else "disabled"))

    def _append_console(self, s: str) -> None:
        self.txt_console.configure(state="normal")
        self.txt_console.insert("end", s)
        self.txt_console.see("end")
        self.txt_console.configure(state="disabled")

    def _drain_console_queue(self) -> None:
        try:
            while True:
                s = self._out_q.get_nowait()
                self._append_console(s)
        except queue.Empty:
            pass
        self.after(50, self._drain_console_queue)

    def clear_console(self) -> None:
        self.txt_console.configure(state="normal")
        self.txt_console.delete("1.0", "end")
        self.txt_console.configure(state="disabled")

    def on_start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        port = self.var_port.get().strip()
        if not port:
            messagebox.showerror("Error", "COM port is required (e.g., COM3).")
            return

        dur_txt = self.var_duration.get().strip()
        duration_s = None
        if dur_txt:
            try:
                duration_s = float(dur_txt)
                if duration_s <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Duration must be blank or a positive number (seconds).")
                return

        outfile_txt = self.var_outfile.get().strip()
        outfile = outfile_txt if outfile_txt else None

        self._stop_event.clear()
        self._set_running(True)
        self.lbl_status.configure(text="Running...")

        kwargs = dict(
            port=port,
            baudrate=int(self.var_baud.get()),
            timeout=float(self.var_timeout.get()),
            outfile=outfile,
            duration_s=duration_s,
            units=self.var_units.get().strip(),
            value_regex=self.var_regex.get().strip(),
            clear_buffer_on_start=bool(self.var_clearbuf.get()),
            stop_event=self._stop_event,  # requires the stop_event patch in scale_logger.py
        )

        def runner() -> None:
            try:
                scale_logger.monitor_scale(**kwargs)
            except Exception as e:
                print(f"\n[GUI] ERROR: {e}\n", file=sys.stderr)
                self.after(0, lambda: messagebox.showerror("Scale Logger Error", str(e)))
            finally:
                self.after(0, self._on_finished)

        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()

    def _on_finished(self) -> None:
        self._set_running(False)
        self.lbl_status.configure(text="Idle")

    def on_stop(self) -> None:
        self._stop_event.set()
        self.lbl_status.configure(text="Stopping...")

    def on_close(self) -> None:
        # Stop worker if running
        try:
            self._stop_event.set()
        except Exception:
            pass

        # Restore stdout/stderr
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr

        self.destroy()


if __name__ == "__main__":
    app = ScaleLoggerGUI()
    app.mainloop()