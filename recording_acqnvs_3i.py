import numpy as np
from contextlib import contextmanager
import time
import socket

from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from rois.obtain_roi import get_roi
from params.play_tone import play_tone

@contextmanager
def on_cleanup(image_path, image_data, save):
    try:
        yield
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    finally:
        print('Cleaning...')
        if save:
            np.save(image_path, image_data, allow_pickle=True)

def recording_acqnvs_3i_sbaccess(image_data, frame_limit, task_set, sb_access, image_path, expt_info):
    """
        Records region of interest and extracts the regions of interest (ROIs)

        Parameters:
            task_set: dictionary with bmi parameters
            path_data: paths to experiment data
            capture: integer denoting the desired capture within 3i .sldy file
            channel: type of channel

        Returns:
            test_info: dictionary containing dataframes with voltage data.
    """
    channel = task_set['im']['chan_data']['recording_chan']
    frame_counter = 0
    prev_tp = -2
    frame_interval = 1 / (task_set['im']['frame_rate']*1.2)
    total_process_time = 0

    if expt_info['type'] == 'baseline':
        save = task_set['expt']['baseline']['save']
    else:
        save = task_set['expt']['bg']['save']

    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: #on_cleanup(image_path, image_data, save): # may want to change to another variable than roi_data_path and image_data/roi_data
    # roi_bg_capture_id = sb_access.StartCapture('ROI_backgroung')
    '''
    # May need to save it in order to get info
    capture = sb_access.GetNumCaptures() - 1  # I need to create another slide. Any open slides will not be recognized
    positions = sb_access.GetNumPositions(capture) - 1  # What are positions
    im_name = sb_access.GetImageName(capture)
    plane_count = sb_access.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    
    
    print(f'The image name for capture {capture} (ID: {roi_bg_streaming_id}) is {im_name}')
    y = sb_access.GetXPosition(capture, positions)  # Y in sutter
    x = sb_access.GetYPosition(capture, positions)  # X in sutter
    z = sb_access.GetZPosition(capture, positions, z_plane)
    print(x, y, z)
    '''
    z_plane = 0
    #print(f'The image name for capture {capture} (ID: {roi_bg_streaming_id})')
    print('STARTING RECORDING!!!')
    capture = sb_access.StartStreaming()  # Always 32768
    print(f'The image name for capture {capture}')
    while sb_access.IsStreaming():
        # Stops recording when buffer is full
        if frame_counter >= frame_limit:
            sb_access.StopStreaming() # not working
            break

        # Wait for the first image gathered to continue
        while True:
            #latest_tp = sb_access.GetNumTimepoints(capture) # Not like lastimagestreamed, may take longer
            # Currently only misses two (maybe 1) frame
            latest_tp = sb_access.GetLastImageStreamed(capture) # Is the index the actual position ot should i subtract one
            if latest_tp >= 0 and latest_tp != prev_tp:
                break

        # capture (0-n), position ( not montage = 0), timepoint, zplane num, channel, True for 2d array return
        #image = sb_access.ReadImagePlaneBuf(capture, 0, latest_tp - 1, z_plane,
                                                 #task_set['im']['chan_data'][channel],
                                                 #True)
        image = sb_access.ReadImagePlaneBuf(capture, 0, latest_tp, z_plane, 0) # No option for 2D array

        print(f'*** Time Point: {latest_tp}')

        start_time = time.perf_counter()
        if expt_info['type'] == 'baseline':
            # Store ROI data
            unit_vals = get_roi(image, expt_info['strc_mask'])
            image_data[:, frame_counter] = unit_vals
        else:
            # Store frame data
            image_data[frame_counter] = image

        frame_counter += 1
        print(f'*** Frames captured: {frame_counter}')

        elapsed_time = time.perf_counter() - start_time
        total_process_time += elapsed_time
        print(f'Execution time: {elapsed_time} seconds')


        if elapsed_time < frame_interval:
            time.sleep(frame_interval - elapsed_time)

        prev_tp = latest_tp

    print('Total processing time: {:.2f} seconds'.format(total_process_time))
    return image_data, task_set

def recording_acqnvs_3i(image_data, frame_limit, task_set, sb_file_reader, image_path, capture, expt_info):
    """
        Records region of interest and extracts the regions of interest (ROIs)

        Parameters:
            task_set: dictionary with bmi parameters
            path_data: paths to experiment data
            capture: integer denoting the desired capture within 3i .sldy file
            channel: type of channel

        Returns:
            test_info: dictionary containing dataframes with voltage data.
    """
    channel = task_set['im']['chan_data']['recording_chan']
    frame_counter = 0
    counter_same = 0
    temp_time_point = 0
    frame_interval = 1 / (task_set['im']['frame_rate']*1.2)
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    total_process_time = 0

    if expt_info['type'] == 'baseline':
        save = task_set['expt']['baseline']['save']
    else:
        save = task_set['expt']['bg']['save']

    print('STARTING RECORDING!!!')
    with on_cleanup(image_path, image_data, save): # may want to change to another variable than roi_data_path and image_data/roi_data
        while counter_same < 1000 and frame_counter < frame_limit: # Stops recording when buffer is full
            sb_file_reader.Refresh(capture)
            curr_time_point = sb_file_reader.GetNumTimepoints(capture) # Lost curr_time_point-1 frames
            print(f'*** Time Point: {curr_time_point}')
            # capture (0-n), position ( not montage = 0), timepoint, zplane num, channel, True for 2d array return
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, curr_time_point - 1, z_plane,
                                                     task_set['im']['chan_data'][channel],
                                                     True)
            if curr_time_point != temp_time_point:
                temp_time_point = curr_time_point
                start_time = time.perf_counter()

                if expt_info['type'] == 'baseline':
                    # Store ROI data
                    unit_vals = get_roi(image, expt_info['strc_mask'])
                    image_data[:, frame_counter] = unit_vals
                else:
                    # Store frame data
                    image_data[frame_counter] = image
                frame_counter += 1
                counter_same = 0
                print(f'*** Frames captured: {frame_counter}')

                elapsed_time = time.perf_counter() - start_time
                total_process_time += elapsed_time
                print(f'Execution time: {elapsed_time} seconds')

                if elapsed_time < frame_interval:
                    time.sleep(frame_interval - elapsed_time)
            else:
                counter_same += 1
    print('Total processing time: {:.2f} seconds'.format(total_process_time))
    return image_data, task_set