import time
from datetime import datetime
import numpy as np
from contextlib import contextmanager

from save_files_3i import save_files_3i
from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from rois.obtain_roi import get_roi
from params.play_tone import play_tone
from SBReadFile22.SBReadFile import *

from wait_on_reader_3i import wait_for_reader

@contextmanager
def on_cleanup(bdata_path, base_activity):
    try:
        yield
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    finally:
        print('Cleaning...')
        # consider storing everything under an npz
        np.save(bdata_path, base_activity, allow_pickle=True)

def baseline_acqnvs_3i(sb_file_reader, capture, tset, path_data, roi_mask, run=False) -> np.array:
    # Save path
    bdata_path = path_data['save_path'] / f'baseline_online{datetime.now().strftime("%y%m%dT%H%M%S")}.npy'
    if not run:
        try:
            bdata = np.load(bdata_path, allow_pickle=True)
            return bdata
        except FileNotFoundError:
            print('Baseline data not found. Please run baseline_acqnvs_3i.')
            exit(1)

    sb_file_reader = wait_for_reader(path_data['sldy_path'])
    while sb_file_reader.GetNumCaptures() < capture+1:
        capture = int(input('Did you start the desired capture? If not, enter new capture number and press enter: '))
        sb_file_reader = wait_for_reader(path_data['sldy_path'])

    save_path_3i = path_data['save_path'] / 'im'
    save_path_3i.mkdir(parents=True, exist_ok=True)
    #save_files_3i(path_data['save_path'], '', 'baseline')

    dilation_factor = 2
    expected_length = int(np.ceil(tset['cb']['baseline_len'] * tset['im']['frame_rate'] * dilation_factor))

    # Initialize baseline variables
    number_neurons = int(np.max(roi_mask))
    strc_mask = obtain_strc_mask_from_mask(roi_mask)
    base_activity = np.full((number_neurons, expected_length), np.nan)

    frame = 0
    time_point_count = sb_file_reader.GetNumTimepoints(capture)
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    init_time_point = 0
    no_progress_counter = 0
    sleep_time = 0.001  # 10 ms (consider no sleep)
    max_wait = 5  # seconds

    print("Starting baseline acquisition")
    print(sb_file_reader.GetImageName(capture))

    # Upon termination (including interruption) of the following code, data will be saved
    with on_cleanup(bdata_path, base_activity):
        for the_retry in range(0, 500):  # Will run for 500 frames
            for time_point in range(init_time_point, time_point_count):
                print(f'*** Time Point: {time_point + 1}')
                start = time.perf_counter()
                image = sb_file_reader.ReadImagePlaneBuf(capture, 0, time_point, z_plane, tset['im']['chan_data']['chan_idx'], True)

                # Store ROI data
                unit_vals = get_roi(image, strc_mask)
                base_activity[:, frame] = unit_vals
                frame += 1

                end = time.perf_counter() - start
                delay = max(0, (1 / (tset['im']['frameRate'] * 1.2)) - end)
                time.sleep(delay) # done in order to synchronize frame acquisition

            # Check for new timepoints
            sb_file_reader.Refresh(capture)
            if init_time_point == time_point_count:
                no_progress_counter += 1
            else:
                no_progress_counter = 0
            time.sleep(sleep_time)
            print(no_progress_counter)

            # If we have waited too long, quit
            if no_progress_counter * sleep_time > max_wait:
                break

            # Loop again
            init_time_point = time_point_count
            time_point_count = sb_file_reader.GetNumTimepoints(capture)

        '''
        counter_same = 0
        while counter_same < 500:
            #Im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
            print(theSBFileReader.GetImageName(capture))
            im = sb_file_reader.ReadImagePlaneBuf(capture, 0, 0, z_plane, tset['im']['chan_data']['chan_idx'], True)
            if not np.array_equal(im, last_frame):
                start = time.perf_counter()
                last_frame = im
                #s.write(ni_getimage)
                time.sleep(0.001)
                #s.write([False, False, False])

                unit_vals = get_roi(im, strc_mask)  # custom
                base_activity[:, frame - 1] = unit_vals
                frame += 1
                counter_same = 0

                elapsed = time.perf_counter() - start
                delay = max(0, (1 / (tset['im']['frameRate'] * 1.2)) - elapsed)
                time.sleep(delay)
            else:
                counter_same += 1
        '''

    print('Finished baseline acquisition')
    play_tone(7000, 1)
    return np.load(bdata_path, allow_pickle=True)