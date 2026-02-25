# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 16:07:46 2026

@author: bergsman_lab_admin
"""

import serial
import pandas as pd
import winsound
import time
from datetime import datetime
from IPython.display import clear_output


def monitor_scale(port="COM3", baudrate=9600, timeout=1.0, beep=True):
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    data = []
    times = []

    first_time = None

    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                continue

            time_now = time.time()
            if first_time is None:
                first_time = time_now

            time_elapsed = round(time_now - first_time, 1)

            data.append(line)
            times.append(time_elapsed)

            clear_output(wait=True)
            print(f"Time: {time_elapsed:6.1f} s | Data: {line}")

    except KeyboardInterrupt:
        # Graceful stop (Ctrl+C)
        clear_output(wait=True)
        print("Keyboard interrupt received — stopping logging...")

    finally:
        # Save what we captured (even if interrupted)
        if len(times) > 0:
            df = pd.DataFrame({"time": times, "mass": data})

            filename = datetime.now().strftime(
                "C:/Users/bergsman_lab_admin/Documents/scale_output/mass_data_%Y%m%d_%H%M%S.csv"
            )
            #df.to_csv(filename, index=False)
            #print(f"Data saved to {filename}")

            if beep:
                winsound.Beep(2000, 600)
        else:
            print("No data captured; nothing to save.")

        ser.close()
        print("Serial port closed.")