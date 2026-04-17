import numpy as np
from contextlib import contextmanager
import time

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

def recording_acqnvs_3i_sbaccess(image_data, frame_limit, task_set, sb_access, image_path, capture, expt_info):
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
    prev_tp = -1
    frame_interval = 1 / (task_set['im']['frame_rate']*1.2)
    plane_count = sb_access.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    total_process_time = 0

    if expt_info['type'] == 'baseline':
        save = task_set['expt']['baseline']['save']
    else:
        save = task_set['expt']['bg']['save']

    print('STARTING RECORDING!!!')
    with on_cleanup(image_path, image_data, save): # may want to change to another variable than roi_data_path and image_data/roi_data
        im_name = sb_access.GetImageName(capture)
        print(f'The image name for capture {capture} is {im_name}')
        while sb_access.IsCapturing():
            # Stops recording when buffer is full
            if frame_counter >= frame_limit:
                sb_access.StopCapture()
                break

            curr_tp = sb_access.GetNumTimepoints(capture) # Lost curr_time_point-1 frames
            latest_tp = sb_access.GetLastImageCaptured(capture)
            print(curr_tp)
            print(latest_tp)

            print(f'*** Time Point: {latest_tp}')
            # capture (0-n), position ( not montage = 0), timepoint, zplane num, channel, True for 2d array return
            image = sb_access.ReadImagePlaneBuf(capture, 0, latest_tp - 1, z_plane,
                                                     task_set['im']['chan_data'][channel],
                                                     True)
            if latest_tp == prev_tp:
                continue

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
            #if latest_tp == tp_count-1 :
            #    break

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