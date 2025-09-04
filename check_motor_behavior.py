import time
from matplotlib import pyplot as plt

from save_files_3i import save_files_3i
from params.play_tone import play_tone
from wait_on_reader_3i import wait_for_reader

def check_motor_behavior(tset, path_data, capture, expt_str, plot=False, run=False):
    """
    Function to check the behavior of the animal while also recording activity.

    Parameters:
    - path_data: Object containing paths for data storage and environment settings.
    - tset: Object containing imaging and channel data settings.
    - expt_str: Experiment identifier string.
    """
    if not run:
        exit()

    sb_file_reader = wait_for_reader(path_data['sldy_path'])
    while sb_file_reader.GetNumCaptures() < capture + 1:
        capture = int(input('Did you start the desired capture? If not, enter new capture number and press enter: '))
        # sb_file_reader = wait_for_reader(path_data['sldy_path'])
        sb_file_reader.Refresh(capture)

    '''
    channel_count = sb_file_reader.GetNumChannels(capture) 
    print(f'There are {channel_count} channels')
    for count in channel_count:
        print(sb_file_reader.GetChannelName(capture, count))
    '''

    # Set the path where to store the imaging and pl command data
    #save_files_3i(path_data['savePath'], pl = None, expt_str)

    capture = sb_file_reader.GetNumCaptures() - 1  # This capture should be the fourth within the slide -> 3
    time_point_count = sb_file_reader.GetNumTimepoints(capture)
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    init_time_point = 0
    #no_progress_counter = 0
    #sleep_time = 0.001  # 10 ms (consider no sleep)
    max_wait = 5  # seconds
    #last_image = np.zeros((sb_file_reader.GetNumYRows(capture), sb_file_reader.GetNumXColumns(capture)))

    if plot:
        fig = plt.figure(0)
        title = 'Timepoint: {tp:6d}'

    print('Starting behavior acquisition')
    for the_retry in range(0, 500):  # Will run for 500 frames
        for time_point in range(init_time_point, time_point_count):
            start = time.perf_counter()
            print(f'*** Time Point: {time_point + 1}')
            # image = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, time_point, z_plane, tset['im']['chan_data']['chan_idx'], True)
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

        '''
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
        '''

        # Loop again
        init_time_point = time_point_count
        time_point_count = sb_file_reader.GetNumTimepoints(capture)

    '''
    counter_same = 0
    while counter_same < 500:
        #im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
        im = sb_file_reader.ReadImagePlaneBuf(capture, 0, 0, z_plane, tset['im']['chan_data']['chan_idx'], True)
        if not np.array_equal(Im, last_frame):
            start = time.perf_counter()
            last_frame = im  # Comparison and assignment takes ~4ms
            counter_same = 0
           
            # FOR BASELINE 
            unit_vals = get_roi(im, strc_mask)  # custom
            base_activity[:, frame - 1] = unit_vals
            frame += 1

            elapsed = time.perf_counter() - start
            delay = max(0, (1 / (tset['im']['frameRate'] * 1.2)) - elapsed)
            time.sleep(delay)
            # FOR BASELINE 
        else:
            counter_same += 1
    '''

    print('Finished behavior')
    play_tone(7000, 1)