import numpy as np
import matplotlib.pyplot as plt

from wait_on_task_3i import *
from rois.scale_im_interactive import scale_im_interactive
from rois.label_mask2roi_data_single_channel import label_mask2roi_data_single_channel
from rois.obtain_roi_mask_suite2p import get_roi_mask
from recording_acqnvs_3i import recording_acqnvs_3i

from pathlib import Path

def get_roi_bg(task_set, path_data, default_run=False, run=False) -> np.array:
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
    #roi_bg_path = path_data['save_path'] / f'roi_bg_{channel}.npy'
    roi_bg_path = Path('F:/cabmi_rg_pmts/bmi_test/slidebook/capture_slide.dir/capture_test-1768411287-992.imgdir/ImageData_Ch1_TP0000000.npy')

    # Checks if ROI file already exists
    if not run:
        try:
            roi_bg = np.load(roi_bg_path, allow_pickle=True)
            print(f'Loading {roi_bg_path.name}')
            return roi_bg
        except FileNotFoundError:
            print('ROI data not found. Please run roi_acqnvs_3i')
            exit(1)

    # Creates an instance of slidebook reader
    #task_set['roi']['capture'] = 0
    #sb_file_reader = wait_for_reader_with_capture(path_data['sldy_path'],task_set['roi']['capture'])
    sb_file_reader, task_set['roi']['capture'] = wait_for_reader_with_latest_capture(path_data['sldy_path'])
    task_set = get_recording_settings(sb_file_reader, task_set['roi']['capture'], task_set, default_run)

    # int(task_set['im']['frame_rate'] * 60) # Actual microscope fps seems to be halved
    task_set['roi']['recording_frames'] = 1100 # 1160 in actual record
    roi_bg = np.full((task_set['roi']['recording_frames'], task_set['im']['resolution'][1], task_set['im']['resolution'][0]), np.nan)

    return recording_acqnvs_3i(roi_bg, task_set['roi']['recording_frames'], task_set, sb_file_reader, roi_bg_path, task_set['roi']['capture'], {'type': 'default'})

def get_roi_data(image_data, path_data, task_set, see_roi_data_flag=False, run=False) -> np.array:
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

    # Check suite2p's way of creating the mean image and use that method.
    #image_data = np.load('F:cabmi/bmi_test/slidebook/capture_slide.dir/Streamtodisk-1765822852-121.imgdir/ImageData_Ch0_TP0000000.npy')
    # Don't create a mean. Pass to suite2p frame by frame
    im_raw = np.nanmean(image_data, axis=0)
    #print(len(image_data))

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
    roi_chan_data = [{}]
    roi_info = label_mask2roi_data_single_channel(im_bg, roi_mask, roi_chan_data, task_set['im']['chan_data']['recording_chan'])

    # See ROI if needed
    if see_roi_data_flag:
        plt.figure()
        plt.imshow(roi_info['roi_mask'], cmap='gray')
        plt.title(f'ROI Mask. Num Roi: {roi_info["num_rois"]}')
        plt.show()

        plt.figure()
        plt.imshow(roi_info['im_roi'], cmap='gray')
        plt.title(f'ROI footprint overlay in blue. Num ROI: {roi_info["num_rois"]}')
        plt.show()
    print('----------------------------------------')

    np.savez(roi_data_path, plot_images=plot_images, im_sc_struct=im_sc_struct, roi_data=roi_info, allow_pickle=True)
    return np.load(roi_data_path, allow_pickle=True)