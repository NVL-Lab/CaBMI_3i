import os
import time
from datetime import datetime
import numpy as np
from contextlib import contextmanager
from pathlib import Path
from scipy.io import savemat

from params.play_tone import play_tone
#import nidaqmx
#from nidaqmx.constants import LineGrouping

from save_files_3i import save_files_3i
from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from rois.obtain_roi import get_roi
from params.play_tone import play_tone

from SBReadFile22.SBReadFile import *

'''
# Custom cleanup context
@contextmanager
def on_cleanup(mat_path):
    try:
        yield
    finally:
        # The following is the clean_me_up():
        global pl, baseActivity
        print("cleaning")
        savemat(mat_path, {'baseActivity': baseActivity})
        if pl.Connected():
            pl.Disconnect()
'''

def baseline_acqnvs_3i(path_data, roi_mask, tset):
    dilation_factor = 2
    expected_length = int(np.ceil(tset['cb']['baseline_len'] * tset['im']['frameRate'] * dilation_factor))

    # Save path
    # Should be equivalent to the mat files but in npz format (multiple arrays)
    npz_path = path_data["save_path"] / f'baseline_online{datetime.now().strftime("%y%m%dT%H%M%S")}.npz'


    #with on_cleanup(np_path):

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

    # Not sure what these are
    #pl.SendScriptCommands("-srd True 0")
    #pl.SendScriptCommands("-lbs True 0")

    save_path_3i = path_data['save_path'] / 'im'
    #save_path_3i.mkdir(parents=True, exist_ok=True)

    #save_files_3i(path_data['save_path'], pl, 'baseline')  # custom

    last_frame = np.zeros((px, py))

    #load_command = f"-tsl {path_data['baseline_env']}"
    #pl.SendScriptCommands(load_command)

    # Initialize baseline variables
    number_neurons = int(np.max(roi_mask))
    strc_mask = obtain_strc_mask_from_mask(roi_mask)  # custom
    baseActivity = np.full((number_neurons, expected_length), np.nan)

    frame = 1
    '''
    time.sleep(2)
    pl.SendScriptCommands("-ts")
    print("sent -ts, pausing")
    time.sleep(5)
    '''
    counter_same = 0
    print("Starting baseline acquisition")
    capture = 1 # This capture should be the second within the slide
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count/2)

    while counter_same < 500:
        #Im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
        Im = sb_file_reader.ReadImagePlaneBuf(0, 0, 0, z_plane, 0, True)
        if not np.array_equal(Im, last_frame):
            start = time.perf_counter()
            last_frame = Im
            #s.write(ni_getimage)
            time.sleep(0.001)
            #s.write([False, False, False])

            unit_vals = get_roi(Im, strc_mask)  # custom
            baseActivity[:, frame - 1] = unit_vals
            frame += 1
            counter_same = 0

            elapsed = time.perf_counter() - start
            delay = max(0, (1 / (tset['im']['frameRate'] * 1.2)) - elapsed)
            time.sleep(delay)
        else:
            counter_same += 1

    print("Finished baseline")
    play_tone(7000, 1)
    return npz_path
