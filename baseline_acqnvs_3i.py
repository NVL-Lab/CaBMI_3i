import time
from datetime import datetime
import numpy as np
from matplotlib import pyplot as plt
from contextlib import contextmanager

from wait_on_task_3i import wait_for_reader_with_capture
from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from rois.obtain_roi import get_roi
from params.play_tone import play_tone
from recording_acqnvs_3i import recording_acqnvs_3i

from pathlib import Path

@contextmanager
def on_cleanup(bdata_path, base_activity):
    try:
        yield
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    finally:
        print('Cleaning...')
        # consider storing everything under an npz
        #np.save(bdata_path, base_activity, allow_pickle=True)

def baseline_acqnvs_3i(task_set, path_data, roi_mask, capture, channel, plot=False, run=False) -> np.array:

    # Save path
    bname = 'baseline_online'
    bdata_path = path_data['save_path'] / f'{bname}_{datetime.now().strftime("%y%m%dt%H%M%S")}.npy'

    if not run:
        try:
            matches = [path for path in path_data['save_path'].rglob('*') if bname in path.name]
            bdata = np.load(matches[-1], allow_pickle=True)
            print(f'Loading {matches[-1].name}')
            return bdata
        except FileNotFoundError:
            print('Baseline data not found. Please run baseline_acqnvs_3i.')
            exit(1)

    # Creates an instance of slidebook reader
    sb_file_reader = wait_for_reader_with_capture(path_data['sldy_path'], capture)

    #save_path_expt = path_data['save_path'] / 'im' / 'baseline'
    #save_path_expt.mkdir(parents=True, exist_ok=True)

    dilation_factor = 1 # 2
    #expected_length = int(np.ceil(task_set['cb']['baseline_len'] * task_set['im']['frame_rate'] * dilation_factor))
    expected_length = 1130

    # Initialize baseline variables
    #'''
    number_neurons = int(np.max(roi_mask)) # wrong because the labels are for all neurons
    strc_mask = obtain_strc_mask_from_mask(roi_mask) # mask should not include non-cells
    base_activity = np.full((number_neurons, expected_length), np.nan)
    print(base_activity.shape)
    #'''
    #base_activity = np.full((250, 390, 403), np.nan) # FOR TESTING

    base_activity = recording_acqnvs_3i(base_activity, expected_length, task_set, sb_file_reader, bdata_path, capture, channel, {'type': 'baseline', 'strc_mask': strc_mask})

    print('Finished baseline acquisition')
    play_tone(7000, 1)
    return base_activity

    '''
    frame_counter = 0
    time_point_count = sb_file_reader.GetNumTimepoints(capture)
    #time_point_count = 8925
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    init_time_point = 0
    no_progress_counter = 0
    sleep_time = 0.01  # 10 ms (consider no sleep) - 0.001
    max_wait = 1  # seconds (old is 5 sec)

    print("Starting baseline acquisition")
    print(sb_file_reader.GetImageName(capture))

    if plot:
        fig = plt.figure(0)
        title = 'Timepoint: {tp:6d}'

    read_break = False

    counter_same = 0
    last_image = np.zeros((sb_file_reader.GetNumYRows(capture), sb_file_reader.GetNumXColumns(capture)))
    print("Starting baseline acquisition")

    frames_captured = 0
    temp_time_point = 0
    frame_interval = 1 / (task_set['im']['frame_rate']*1.2)

    # Upon termination (including interruption) of the following code, data will be saved
    with on_cleanup(bdata_path, base_activity):
        while counter_same < 1000:
            # Stops recording when buffer is full
            if frame_counter >= expected_length:
                break
            sb_file_reader.Refresh(capture)  # Takes ~4ms
            curr_time_point = sb_file_reader.GetNumTimepoints(capture)

            print(f'*** Time Point: {curr_time_point}')
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, curr_time_point-1, z_plane, task_set['im']['chan_data'][channel]['pmt_idx'], True)  # recording is different index

            # check desired amount of frames start perhaps start recording past 50
            if curr_time_point != temp_time_point:
                temp_time_point = curr_time_point
                frames_captured += 1
                print(f'*** Frames captured: {frames_captured}')
                start_time = time.perf_counter()
                #last_image = image  # comparison and assignment

                # Store ROI data
                unit_vals = get_roi(image, strc_mask)
                base_activity[:, frame_counter] = unit_vals

                #base_activity[frame_counter] = image # FOR TESTING
                frame_counter += 1
                counter_same = 0

                elapsed_time = time.perf_counter() - start_time
                print(f'Execution time: {elapsed_time} seconds')

                if elapsed_time < frame_interval:
                    time.sleep(frame_interval - elapsed_time)
            else:
                counter_same += 1
        
        
        # Older version
        for time_point in range(0, 250):
            #for time_point in range(init_time_point, time_point_count):

            
            sb_file_reader.Refresh(capture)  # Takes ~4ms
            curr_time_point = sb_file_reader.GetNumTimepoints(capture)
            refresh_start = time.perf_counter()
            while n_time_point_count != time_point:
                sb_file_reader.Refresh(capture)
                n_time_point_count = sb_file_reader.GetNumTimepoints(capture)
                if time.perf_counter() - refresh_start > max_wait:
                    read_break = True
                    break
            


            print(f'*** Time Point: {time_point + 1}')
            start = time.perf_counter()
            print(sb_file_reader.GetNumTimepoints(capture)-1)
            print(time_point)
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, sb_file_reader.GetNumTimepoints(capture)-1, z_plane, 0
                                                     , True) # recording is different index
            # image = path_data['test_data'][time_point]

            # Store ROI data
            # unit_vals = get_roi(image, strc_mask)
            # base_activity[:, frame] = unit_vals
            frame += 1

            print(f'Execution time: {time.perf_counter() - start} seconds')

            
            if plot:
                if time_point == 0:
                    img_artist = plt.imshow(image)
                elif time_point % 2 == 0:
                    img_artist.set_data(image)
                    plt.draw()
                    fig.canvas.flush_events()
                    plt.title(title.format(tp=time_point), loc='left')
                    try:
                        plt.pause(0.01)
                    except KeyboardInterrupt:
                        print("Keyboard Interrupt")
                        exit()
            

            
            # Check for new timepoints
            sb_file_reader.Refresh(capture)  # Takes ~4ms
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