import serial
import pandas as pd
import winsound
import time
from datetime import datetime

ser = serial.Serial(port='COM3')  
data = []
times = []
runtime = 1800   # seconds

start = time.time()
first_time = None

try:
    while time.time() - start < runtime:
        line = ser.readline().decode("utf-8").strip()  # Read and clean input

        if line:
            time_now = time.time()
            if first_time is None:  
                 first_time = time_now  # Set first timestamp
            
            time_elapsed = time_now - first_time  # Adjust time
            data.append(line)
            time_elapsed = round(time_elapsed,1)
            times.append(time_elapsed)
            
            print(f"Time elapsed: {time_elapsed} s - Data: {line}")

    df = pd.DataFrame({'time': times,'mass': data})  # Store in DataFrame
    print("\nFinal Data Collected:")
    print(df)  # Print DataFrame
    
    # Generate dynamic filename with current date & time
    filename = datetime.now().strftime("C:/Users/bergsman_lab_admin/Documents/scale_output/mass_data_%Y%m%d_%H%M%S.csv")
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"\nData saved to {filename}")
    winsound.Beep(2000, 1500)  # Beep after completion

finally:
    ser.close()  # Close COM port
    print("Serial port closed.")
