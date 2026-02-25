"""
Scale logger (benchtop scale over COM port)

- Logs time as seconds since start (time_s) using time.time()
- Auto-generates filename like: scalelog_260225_1020.csv
- Prints each reading on a new line
- Optional run duration (seconds). If duration is reached, beeps and exits.

Requires:
  pip install pyserial
"""

from __future__ import annotations

import csv
import re
import time
from datetime import datetime
from typing import Optional
import threading
import os
import serial
import winsound


import os
from datetime import datetime


def generate_filename(prefix: str = "scalelog") -> str:
    """Return path like ../logs/scalelog_DDMMYY_HHMM.csv"""

    stamp = datetime.now().strftime("%d%m%y_%H%M")

    # Directory of this script ( .../brg_ScaleInterface/py )
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Project root (one level up)
    project_root = os.path.dirname(script_dir)

    # logs directory at project root
    logs_dir = os.path.join(project_root, "logs")

    os.makedirs(logs_dir, exist_ok=True)

    return os.path.join(logs_dir, f"{prefix}_{stamp}.csv")


def parse_weight(line: str, pattern: re.Pattern) -> Optional[float]:
    m = pattern.search(line)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def monitor_scale(
    port: str = "COM3",
    baudrate: int = 9600,
    timeout: float = 1.0,
    outfile: Optional[str] = None,
    duration_s: Optional[float] = None,  # None => continuous
    units: str = "",
    value_regex: str = r"([-+]?\d*\.?\d+)",
    flush_every: int = 1,
    clear_buffer_on_start: bool = True,
    stop_event: Optional[threading.Event] = None,
) -> None:
    if outfile is None:
        outfile = generate_filename()

    pattern = re.compile(value_regex)

    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    # Optional: drop any queued lines so "t=0" corresponds to fresh data
    if clear_buffer_on_start:
        try:
            ser.reset_input_buffer()
        except Exception:
            pass

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "value"])
        f.flush()

        print(
            f"Reading {port} @ {baudrate}. Logging to {outfile}."
            + (f" Duration: {duration_s}s." if duration_s is not None else " Continuous.")
        )

        start = time.time()
        rows_since_flush = 0

        try:
            while True:
                elapsed = time.time() - start
                if stop_event is not None and stop_event.is_set():
                    print("\nStopped by GUI.")
                    break

                if duration_s is not None and elapsed >= duration_s:
                    print("\nTimer complete.")
                    winsound.Beep(1200, 400)
                    break

                raw = ser.readline()
                if not raw:
                    continue

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                value = parse_weight(line, pattern)
                if value is None:
                    continue

                elapsed = time.time() - start  # timestamp as close to logging as possible

                print(f"{elapsed:10.3f} s | {value:.6g}{(' ' + units) if units else ''}")
                writer.writerow([f"{elapsed:.6f}", value])

                rows_since_flush += 1
                if rows_since_flush >= flush_every:
                    f.flush()
                    rows_since_flush = 0

        except KeyboardInterrupt:
            print("\nStopped by user (Ctrl+C).")

        finally:
            f.flush()
            ser.close()


if __name__ == "__main__":
    monitor_scale(
        port="COM3",
        baudrate=9600,
        timeout=1.0,
        outfile=None,        # auto name
        duration_s=None,     # e.g. 60
        units="",
        clear_buffer_on_start=True,
    )