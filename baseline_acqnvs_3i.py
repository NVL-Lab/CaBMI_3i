import time
from datetime import datetime
import numpy as np
from matplotlib import pyplot as plt
from contextlib import contextmanager

from wait_on_reader_3i import wait_for_reader
from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from rois.obtain_roi import get_roi
from params.play_tone import play_tone

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

def baseline_acqnvs_3i(task_set, path_data, roi_mask, capture, plot=False, run=False) -> np.array:
    bname = 'baseline_online'
    if not run:
        try:
            matches = [path for path in path_data['save_path'].rglob('*') if bname in path.name]
            bdata = np.load(matches[-1], allow_pickle=True)
            print(f'Loading {matches[-1].name}')
            return bdata
        except FileNotFoundError:
            print('Baseline data not found. Please run baseline_acqnvs_3i.')
            exit(1)

    # Save path
    bdata_path = path_data['save_path'] / f'{bname}_{datetime.now().strftime("%y%m%dt%H%M%S")}.npy'
    sb_file_reader = wait_for_reader(path_data['sldy_path'])
    while sb_file_reader.GetNumCaptures() < capture+1:
        capture = int(input('Did you start the desired capture? If not, enter new capture number and press enter: '))
        sb_file_reader = wait_for_reader(path_data['sldy_path'])
        #sb_file_reader.Refresh(capture)

    save_path_expt = path_data['save_path'] / 'im' / 'baseline'
    save_path_expt.mkdir(parents=True, exist_ok=True)

    dilation_factor = 1 # 2
    expected_length = int(np.ceil(task_set['cb']['baseline_len'] * task_set['im']['frame_rate'] * dilation_factor))

    # Initialize baseline variables
    #number_neurons = int(np.max(roi_mask))
    #strc_mask = obtain_strc_mask_from_mask(roi_mask)
    #base_activity = np.full((number_neurons, expected_length), np.nan)
    base_activity = np.full((39, expected_length), np.nan)

    frame = 0
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
    # Upon termination (including interruption) of the following code, data will be saved
    with on_cleanup(bdata_path, base_activity):
        while counter_same < 1000:
            #for time_point in range(init_time_point, time_point_count):
            sb_file_reader.Refresh(capture)  # Takes ~4ms
            curr_time_point = sb_file_reader.GetNumTimepoints(capture)

            print(f'*** Time Point: {curr_time_point}')
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, curr_time_point, z_plane, 0, True)  # recording is different index

            #if not np.array_equal(image, last_image):
            if curr_time_point != temp_time_point:
                temp_time_point = curr_time_point
                frames_captured += 1
                print(f'*** Frames captured: {frames_captured}')
                start_time = time.perf_counter()
                last_image = image  # comparison and assignment

                # Store ROI data
                # unit_vals = get_roi(image, strc_mask)
                # base_activity[:, frame] = unit_vals
                frame += 1
                counter_same = 0

                elapsed_time = time.perf_counter() - start_time
                print(f'Execution time: {elapsed_time} seconds')

                frame_interval = 1 / (task_set['im']['frame_rate'])# * 1.2)
                if elapsed_time < frame_interval:
                    time.sleep(frame_interval - elapsed_time)
            else:
                counter_same += 1


        '''
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
            
        '''

        '''
        # Loop again
        init_time_point = time_point_count
        time_point_count = sb_file_reader.GetNumTimepoints(capture)
        '''

    print('Finished baseline acquisition')
    play_tone(7000, 1)
    return base_activity