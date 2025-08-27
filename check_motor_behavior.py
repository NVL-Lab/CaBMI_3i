import time
from save_files_3i import save_files_3i
from params.play_tone import play_tone

def check_motor_behavior(path_data, tset, expt_str, sb_file_reader):
    """
    Function to check the behavior of the animal while also recording activity.

    Parameters:
    - path_data: Object containing paths for data storage and environment settings.
    - tset: Object containing imaging and channel data settings.
    - expt_str: Experiment identifier string.
    """

    # Set the path where to store the imaging data
    save_files_3i(path_data['savePath'], '', expt_str)

    capture = sb_file_reader.GetNumCaptures() - 1  # This capture should be the fourth within the slide -> 3
    time_point_count = sb_file_reader.GetNumTimepoints(capture)
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    init_time_point = 0
    no_progress_counter = 0
    sleep_time = 0.001  # 10 ms (consider no sleep)
    max_wait = 5  # seconds

    print('Starting behavior acquisition')
    # Upon termination (including interruption) of the following code, data will be saved
    for the_retry in range(0, 500):  # Will run for 500 frames
        for time_point in range(init_time_point, time_point_count):
            print(f'*** Time Point: {time_point + 1}')
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, time_point, z_plane, tset['im']['chan_data']['chan_idx'], True)

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
    while counter_same < 500:
        #im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
        im = sb_file_reader.ReadImagePlaneBuf(capture, 0, 0, z_plane, tset['im']['chan_data']['chan_idx'], True)
        if not np.array_equal(Im, last_frame):
            last_frame = im  # Comparison and assignment takes ~4ms
            counter_same = 0
        else:
            counter_same += 1
    '''

    print('Finished behavior')
    play_tone(7000, 1)
