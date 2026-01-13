import numpy as np
import matplotlib.pyplot as plt
from contextlib import contextmanager
import time

from wait_on_task_3i import wait_for_reader_with_capture
from rois.scale_im_interactive import scale_im_interactive
from rois.label_mask2roi_data_single_channel import label_mask2roi_data_single_channel
from rois.obtain_roi_mask_suite2p import get_roi_mask

@contextmanager
def on_cleanup(roi_data_path, roi_activity):
    try:
        yield
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    finally:
        print('Cleaning...')
        # consider storing everything under an npz
        # ROI recording will be save in npy, while the rest will be npz
        #np.save(roi_data_path, roi_activity, allow_pickle=True)

def roi_acqnvs_3i(task_set, path_data, capture, channel, roi_chan_data, see_roi_data_flag=False, run=False) -> np.array:
    """
        Records region of interest and extracts the regions of interest (ROIs)

        Parameters:
            task_set: dictionary with bmi parameters
            path_data: paths to experiment data
            capture: integer denoting the desired capture within 3i .sldy file
            channel: type of channel
            roi_chan_data: list with channel and ROI data
            see_roi_data_flag: bool used to determine if ROIs should be plotted
            run: bool used to determine if the code should be run (typically ran unless code has been ran already)

        Returns:
            test_info: dictionary containing dataframes with voltage data.
    """
    roi_data_path = path_data['save_path'] / 'roi_data.npz'

    # Checks if ROI file already exists
    if not run:
        try:
            roi_data = np.load(roi_data_path, allow_pickle=True)
            print(f'Loading {roi_data_path.name}')
            return roi_data
        except FileNotFoundError:
            print('ROI data not found. Please run roi_acqnvs_3i')
            exit(1)

    # Creates an instance of slidebook reader
    sb_file_reader = wait_for_reader_with_capture(path_data['sldy_path'], capture)
    '''
    while sb_file_reader.GetNumCaptures() < capture + 1:
        capture = int(input('Did you start the desired capture? If not, enter new capture number and press enter: '))
        sb_file_reader = wait_for_reader(path_data['sldy_path'])
    '''

    chan_data = task_set['im']['chan_data'][channel]

    minute_recording_len = int(task_set['im']['frame_rate'] * 60) # Actual microscope fps seems to be halved
    image_data = np.full((minute_recording_len, task_set['im']['resolution'][1], task_set['im']['resolution'][0]), np.nan)
    frame_counter = 0
    counter_same = 0
    temp_time_point = 0
    frame_interval = 1 / (task_set['im']['frame_rate']*1.2)
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    loop_duration_sec = 0
    with on_cleanup(roi_data_path, image_data): # may want to change to another variable than roi_data_path and image_data/roi_data
        while counter_same < 1000:
            # Stops recording when buffer is full
            if frame_counter >= minute_recording_len:
                break
            sb_file_reader.Refresh(capture)
            curr_time_point = sb_file_reader.GetNumTimepoints(capture)
            print(f'*** Time Point: {curr_time_point}')
            # capture (0-n), position ( not montage = 0), timepoint, zplane num, channel, True for 2d array return
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, curr_time_point - 1, z_plane,
                                                     chan_data['pmt_idx'],
                                                     True)
            if curr_time_point != temp_time_point:
                temp_time_point = curr_time_point
                start_time = time.perf_counter()

                image_data[frame_counter] = image
                frame_counter += 1
                counter_same = 0

                elapsed_time = time.perf_counter() - start_time
                loop_duration_sec = loop_duration_sec + elapsed_time
                print(f'Execution time: {elapsed_time} seconds')

                if elapsed_time < frame_interval:
                    time.sleep(frame_interval - elapsed_time)
            else:
                counter_same += 1

    # Check suite2p's way of creating the mean image and use that method.
    #image_data = np.load('F:cabmi/bmi_test/slidebook/capture_slide.dir/Streamtodisk-1765822852-121.imgdir/ImageData_Ch0_TP0000000.npy')
    # Don't create a mean. Pass to suite2p frame by frame
    im_raw = np.nanmean(image_data, axis=0)
    print(len(image_data))

    # Single image is used to locate ROIs (Old method)
    #im_raw = sb_file_reader.ReadImagePlaneBuf(capture, 0, 0, 0, task_set['im']['chan_data']['green']['fp_idx'], True)
    #im_raw = path_data['test_data'][99]

    # Scale image to see ROIs better
    print('\nImage Scaling')
    print('----------------------------------------')
    im_sc_struct, _ = scale_im_interactive(im_raw, [],0)
    im_bg = im_sc_struct[-1]['im']
    plt.figure()
    plt.imshow(im_bg, cmap='bone', vmin=0, vmax=4 * np.nanmean(im_bg))
    plt.title('Background for tseROI Identification')
    plt.show()
    plt.close()
    print('----------------------------------------')

    plot_images = [{'im': None, 'label': ''} for _ in range(2)]
    plot_images[0]['im'] = im_raw # raw image
    plot_images[0]['label'] = 'green mean'
    plot_images[1]['im'] = im_bg # scaled image
    plot_images[1]['label'] = 'scaled'

    print('Obtaining ROI mask!')
    print('----------------------------------------')
    roi_mask = get_roi_mask(im_bg, path_data['save_path'])
    roi_data = label_mask2roi_data_single_channel(im_bg, roi_mask, roi_chan_data, chan_data['label'])

    # See ROI if needed
    if see_roi_data_flag:
        plt.figure()
        plt.imshow(roi_data['roi_mask'], cmap='gray')
        plt.title(f'ROI Mask. Num Roi: {roi_data["num_rois"]}')
        plt.show()

        plt.figure()
        plt.imshow(roi_data['im_roi'], cmap='gray')
        plt.title(f'ROI footprint overlay in blue. Num ROI: {roi_data["num_rois"]}')
        plt.show()
    print('----------------------------------------')

    np.savez(roi_data_path, plot_images=plot_images, im_sc_struct=im_sc_struct, roi_data=roi_data, allow_pickle=True)
    return np.load(roi_data_path, allow_pickle=True)