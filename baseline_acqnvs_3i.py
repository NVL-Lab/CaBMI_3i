import os
import time
from datetime import datetime
import numpy as np
from contextlib import contextmanager
from scipy.io import savemat

#import nidaqmx
#from nidaqmx.constants import LineGrouping

from save_files_3i import save_files_3i
from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from rois.obtain_roi import get_roi

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

def baseline_acqnvs_3i(path_data, roi_mask, tset, a, apin):
    dilation_factor = 2
    expected_length = int(np.ceil(tset['cb']['baseline_len'] * tset['im']['frameRate'] * dilation_factor))

    # Save path
    mat_path = os.path.join(path_data['savePath'], f"BaselineOnline{datetime.now():%y%m%dT%H%M%S}.mat")

    # Initialize globals
    global pl, baseActivity

    with on_cleanup(mat_path):
        # Prepare NI-DAQ
        s = nidaqmx.Task()
        s.do_channels.add_do_chan("Dev6/port0/line0:2", line_grouping=LineGrouping.CHAN_PER_LINE)
        s.write([False, False, False])
        ni_getimage = [False, True, False]

        # Prairie Link COM interface
        import win32com.client
        pl = win32com.client.Dispatch("PrairieLink.Application")
        pl.Connect()
        time.sleep(2)

        px = pl.PixelsPerLine
        py = pl.LinesPerFrame

        pl.SendScriptCommands("-srd True 0")
        pl.SendScriptCommands("-lbs True 0")

        save_path_3i = os.path.join(path_data['savePath'], 'im')
        os.makedirs(save_path_3i, exist_ok=True)

        save_files_3i(path_data['savePath'], pl, 'baseline')  # custom

        last_frame = np.zeros((px, py))

        load_command = f"-tsl {path_data['baseline_env']}"
        pl.SendScriptCommands(load_command)

        # Initialize baseline variables
        number_neurons = int(np.max(roi_mask))
        strc_mask = obtain_strc_mask_from_mask(roi_mask)  # custom
        baseActivity = np.full((number_neurons, expected_length), np.nan)

        # Arduino signal
        if a is not None:
            a.write_digital_pin("D9", 1)
            time.sleep(1)
            a.write_digital_pin("D9", 0)

        frame = 1
        time.sleep(2)
        pl.SendScriptCommands("-ts")
        print("sent -ts, pausing")
        time.sleep(5)
        counter_same = 0
        print("Starting baseline acquisition")

        while counter_same < 500:
            Im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
            if not np.array_equal(Im, last_frame):
                start = time.time()
                last_frame = Im.copy()
                s.write(ni_getimage)
                time.sleep(0.001)
                s.write([False, False, False])

                unit_vals = get_roi(Im, strc_mask)  # custom
                baseActivity[:, frame - 1] = unit_vals
                frame += 1
                counter_same = 0

                elapsed = time.time() - start
                delay = max(0, (1 / (tset['im']['frameRate'] * 1.2)) - elapsed)
                time.sleep(delay)
            else:
                counter_same += 1

        print("Finished baseline")
        #playTone(a, apin, 7000, 1)  # custom, will we use an arduino?
        # pl.Disconnect() will be handled in cleanup
    return mat_path
