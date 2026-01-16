import numpy as np
from contextlib import contextmanager
import time

from rois.obtain_roi import get_roi

@contextmanager
def on_cleanup(image_path, image_data):
    try:
        yield
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    finally:
        print('Cleaning...')
        #np.save(image_path, image_data, allow_pickle=True)

def recording_acqnvs_3i(image_data, frame_limit, task_set, sb_file_reader, image_path, capture, channel, expt_info) -> np.array:
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
    #image_data = np.full((frame_limit, task_set['im']['resolution'][1], task_set['im']['resolution'][0]), np.nan)
    frame_counter = 0
    counter_same = 0
    temp_time_point = 0
    frame_interval = 1 / (task_set['im']['frame_rate']*1.2)
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    #loop_duration_sec = 0
    with on_cleanup(image_path, image_data): # may want to change to another variable than roi_data_path and image_data/roi_data
        while counter_same < 1000:
            # Stops recording when buffer is full
            if frame_counter >= frame_limit:
                break
            sb_file_reader.Refresh(capture)
            curr_time_point = sb_file_reader.GetNumTimepoints(capture)
            print(f'*** Time Point: {curr_time_point}')
            # capture (0-n), position ( not montage = 0), timepoint, zplane num, channel, True for 2d array return
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, curr_time_point - 1, z_plane,
                                                     task_set['im']['chan_data'][channel]['pmt_idx'],
                                                     True)
            if curr_time_point != temp_time_point:
                temp_time_point = curr_time_point
                start_time = time.perf_counter()

                if expt_info['type'] == 'baseline':
                    # Store ROI data
                    unit_vals = get_roi(image, expt_info['strc_mask'])
                    print(len(unit_vals))
                    image_data[:, frame_counter] = unit_vals
                else:
                    # Store frame data
                    image_data[frame_counter] = image
                frame_counter += 1
                counter_same = 0

                elapsed_time = time.perf_counter() - start_time
                #loop_duration_sec = loop_duration_sec + elapsed_time
                print(f'Execution time: {elapsed_time} seconds')

                if elapsed_time < frame_interval:
                    time.sleep(frame_interval - elapsed_time)
            else:
                counter_same += 1
    return image_data

# create a function that will go through each frame like recording