import numpy as np
import matplotlib.pyplot as plt
from contextlib import contextmanager

from wait_on_task_3i import wait_for_reader_with_capture
from rois.scale_im_interactive import scale_im_interactive
from rois.label_mask2roi_data_single_channel import label_mask2roi_data_single_channel
from rois.obtain_roi_mask_suite2p import get_roi_mask

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

def roi_acqnvs_3i(task_set, path_data, capture, chan_data, roi_chan_data, chan_idx, see_roi_data_flag=False, run=False) -> np.array:
    """
        Records region of interest and extracts the regions of interest (ROIs)

        Parameters:
            task_set: dictionary with bmi parameters
            path_data: paths to experiment data
            capture: integer denoting the desired capture within 3i .sldy file
            chan_data: dictionary with desired channel information
            roi_chan_data: list with channel and ROI data
            chan_idx: integer denoting channel index for roi_chan_data
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

    #CONTINUE WORKING HERE
    # Check suite2p's way of creating the mean image and use that method.
    sleep_sec = 0.01
    max_wait_sec = 5 # wait at most 5 seconds. If over this, quit
    no_progress = 0
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    first_tp = 0
    tps = sb_file_reader.GetNumTimepoints(capture)
    try:
        for theRetry in range(0, 10000):
            for tp in range(first_tp, tps):
                print(f'*** Time Point: {tp}')
                image = sb_file_reader.ReadImagePlaneBuf(capture, 0, tp, z_plane, 0, True)

            # see if there are any new timepoints
            sb_file_reader.Refresh(capture)
            if first_tp == tps:
                no_progress += 1
                time.sleep(sleep_sec)  # sleep 10 ms
                theTimePaused += sleep_sec
            else:
                no_progress = 0
            time.sleep(sleep_sec)

            # if we have waited too long, quit
            if no_progress * sleep_sec > maxWaitS:
                break

            # loop again
            first_tp = tps
            tps = sb_file_reader.GetNumTimepoints(capture) - 1

    except:
        print("Keyboard Interrupt")

    # capture (0-n), position ( not montage = 0), timepoint, zplane num, channel, True for 2d array return


    # Single image is used to locate ROIs (Old method)
    im_raw = sb_file_reader.ReadImagePlaneBuf(capture, 0, 0, 0, task_set['im']['chan_data']['green']['fp_idx'], True)
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
    roi_data = label_mask2roi_data_single_channel(im_bg, roi_mask, roi_chan_data, chan_data['label'], chan_idx)

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