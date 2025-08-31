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

from matplotlib import pyplot as plt

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

def baseline_acqnvs_3i(task_set, path_data, roi_mask, capture, run=False) -> np.array:
    # Save path
    bdata_path = path_data['save_path'] / f'baseline_online{datetime.now().strftime("%y%m%dT%H%M%S")}.npy'
    if not run:
        try:
            bdata = np.load(bdata_path, allow_pickle=True)
            print(f'Loading {bdata_path.name}')
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
    expected_length = int(np.ceil(task_set['cb']['baseline_len'] * task_set['im']['frame_rate'] * dilation_factor))

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
    sleep_time = 0.01  # 10 ms (consider no sleep) - 0.001
    max_wait = 1  # seconds (old is 5 sec)

    print("Starting baseline acquisition")
    print(sb_file_reader.GetImageName(capture))

    fig = plt.figure(0)
    title = 'Timepoint: {tp:6d}'

    prev_image = np.zeros((sb_file_reader.GetNumYRows(capture), sb_file_reader.GetNumXColumns(capture)))
    read_break = False


    # Upon termination (including interruption) of the following code, data will be saved
    with on_cleanup(bdata_path, base_activity):
        for the_retry in range(0, 500):
            for time_point in range(init_time_point, time_point_count):
                print(f'*** Time Point: {time_point + 1}')
                start = time.perf_counter()
                # channel task_set['im']['chan_data']['chan_idx']
                image = sb_file_reader.ReadImagePlaneBuf(capture, 0, time_point, z_plane, 0, True)

                '''
                if time_point % 2 == 0:
                    if time_point == 0:
                        img_artist = plt.imshow(image)
                    else:
                        img_artist.set_data(image)
                    plt.draw()
                    fig.canvas.flush_events()
                    plt.title(title.format(tp=time_point), loc='left')
                    try:
                        plt.pause(0.01)
                    except KeyboardInterrupt:
                        print("Keyboard Interrupt")
                        exit()
                '''
                # Store ROI data
                '''
                # does not work
                unit_vals = get_roi(image, strc_mask)
                base_activity[:, frame] = unit_vals
                frame += 1
                '''
                end = time.perf_counter() - start

            # Check for new timepoints
            sb_file_reader.Refresh(capture) # Takes ~4ms
            n_time_point_count = sb_file_reader.GetNumTimepoints(capture)
            # Checks refreshing > 1 sec then refreshing stops
            refresh_start = time.perf_counter()
            while n_time_point_count == time_point_count:
                sb_file_reader.Refresh(capture)
                n_time_point_count = sb_file_reader.GetNumTimepoints(capture)
                if time.perf_counter() - refresh_start > max_wait:
                    read_break = True
                    break
            # If refreshing was halted, acquisition stops entirely
            if read_break:
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