import time
import numpy as np
import pywin32 as win32
from save_files_3i import save_files_3i

def check_motor_behavior(a, path_data, tset, expt_str, apin):
    """
    Function to check the behavior of the animal while also recording activity.

    Parameters:
    - a: Arduino object for controlling hardware.
    - path_data: Object containing paths for data storage and environment settings.
    - tset: Object containing imaging and channel data settings.
    - expt_str: Experiment identifier string.
    - apin: Pin number for Arduino control.
    """

    global pl
    
    # Initialize PrairieLink.Application
    pl = win32.Dispatch("PrairieLink.Application")
    pl.Connect()
    time.sleep(2)  # Pause to give time for Prairie to connect

    # Prairie variables
    px = pl.PixelsPerLine()
    py = pl.LinesPerFrame()

    # Prairie commands
    pl.SendScriptCommands("-srd True 0")
    pl.SendScriptCommands("-lbs True 0")

    # Set the environment for the Time Series in PrairieView
    load_command = f"-tsl {path_data['baseline_env']}"
    pl.SendScriptCommands(load_command)

    # Set the path where to store the imaging data
    save_files_3i(path_data['savePath'], pl, expt_str)

    # Prepare the Arduino
    # Give random reward to trigger the jetball
    a.writeDigitalPin("D9", 1)
    time.sleep(1)
    a.writeDigitalPin("D9", 0)

    # Start the time_series scan
    time.sleep(2)
    pl.SendScriptCommands("-ts")
    print('Sent -ts, pausing')
    time.sleep(5)  # Empirically discovered time for Prairie to start gears

    counter_same = 0
    last_frame = np.zeros((px, py))
    print('Starting behavior acquisition')

    while counter_same < 500:
        Im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
        if not np.array_equal(Im, last_frame):
            last_frame = Im  # Comparison and assignment takes ~4ms
            counter_same = 0
        else:
            counter_same += 1

    print('Finished behavior')
    play_tone(a, apin, 7000, 1)
