import time
import numpy as np
import pywin32 as win32
from save_files_3i import save_files_3i
from SBReadFile22.SBReadFile import *

def check_motor_behavior(path_data, tset, expt_str):
    """
    Function to check the behavior of the animal while also recording activity.

    Parameters:
    - a: Arduino object for controlling hardware.
    - path_data: Object containing paths for data storage and environment settings.
    - tset: Object containing imaging and channel data settings.
    - expt_str: Experiment identifier string.
    - apin: Pin number for Arduino control.
    """

    #global pl
    sb_file_reader = SBReadFile()
    if not sb_file_reader.Open(sldy_dir):
        print('.sldy file not found')
        exit(1)

    # Adds channels
    '''
    s = nidaqmx.Task()
    s.do_channels.add_do_chan("Dev6/port0/line0:2", line_grouping=LineGrouping.CHAN_PER_LINE)
    s.write([False, False, False])
    ni_getimage = [False, True, False]
    '''
    px = sb_file_reader.GetNumXColumns(0)
    py = sb_file_reader.GetNumYRows(0)

    '''
    # Prairie commands
    pl.SendScriptCommands("-srd True 0")
    pl.SendScriptCommands("-lbs True 0")

    # Set the environment for the Time Series in PrairieView
    load_command = f"-tsl {path_data['baseline_env']}"
    pl.SendScriptCommands(load_command)
    '''

    # Set the path where to store the imaging data
    save_files_3i(path_data['savePath'], '', expt_str)

    # Prepare the Arduino
    # Give random reward to trigger the jetball
    '''
    a.writeDigitalPin("D9", 1)
    time.sleep(1)
    a.writeDigitalPin("D9", 0)
    '''

    # Start the time_series scan
    '''
    time.sleep(2)
    pl.SendScriptCommands("-ts")
    print('Sent -ts, pausing')
    time.sleep(5)  # Empirically discovered time for Prairie to start gears
    '''

    counter_same = 0
    last_frame = np.zeros((px, py))
    print('Starting behavior acquisition')
    capture = 3  # This capture should be the second within the slide
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)

    while counter_same < 500:
        #im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
        im = sb_file_reader.ReadImagePlaneBuf(capture, 0, 0, z_plane, tset['im']['chan_data']['chan_idx'], True)
        if not np.array_equal(Im, last_frame):
            last_frame = im  # Comparison and assignment takes ~4ms
            counter_same = 0
        else:
            counter_same += 1

    print('Finished behavior')
    play_tone(7000, 1)
