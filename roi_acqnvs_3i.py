import numpy as np
import matplotlib.pyplot as plt

from wait_on_reader_3i import wait_for_reader
from rois.scale_im_interactive import scale_im_interactive
#from segmentation.im_find_cells_tm import im_find_cells_tm
from segmentation.im_find_cells_suite2p import im_find_cells_suite2p
from rois.get_center import get_center
from rois.label_mask2roi_data_single_channel import label_mask2roi_data_single_channel
from rois.delete_roi_2chan import delete_roi_2chan
from rois.edit_roi_mask_suite2p import edit_roi_mask

def roi_acqnvs_3i(task_set, path_data, capture, see_roi_data_flag=False, run=False) -> np.array:
    roi_data_path = path_data['save_path'] / 'roi_data.npz'
    if not run:
        try:
            roi_data = np.load(roi_data_path, allow_pickle=True)
            print(f'Loading {roi_data_path.name}')
            return roi_data
        except FileNotFoundError:
            print('ROI data not found. Please run roi_acqnvs_3i')
            exit(1)

    sb_file_reader = wait_for_reader(path_data['sldy_path'])
    while sb_file_reader.GetNumCaptures() < capture + 1:
        capture = int(input('Did you start the desired capture? If not, enter new capture number and press enter: '))
        sb_file_reader.Refresh(capture)

    # Single image is used to locate ROIs
    # first = roi detect capture, second=baseline recording, third=bmi recording, fourth=behavior recording
    im_summary = sb_file_reader.ReadImagePlaneBuf(capture,0,0,0,task_set['im']['chan_data']['chan_idx'],True) # capture (0-n), position (~montage = 0), timepoint, zplane num, channel (0=RFP, 1=GFP), True for 2d array return
    im_summary = path_data['test_data'][99]

    # Scale image to see ROIs better
    print('\nImage Scaling')
    print('----------------------------------------')
    im_sc_struct, _ = scale_im_interactive(im_summary, [],0)
    im_bg = im_sc_struct[-1]['im']
    plt.figure()
    plt.imshow(im_bg, cmap='bone', vmin=0, vmax=4 * np.nanmean(im_bg))
    plt.title('Background for tseROI Identification')
    plt.show()
    print('----------------------------------------')

    # PLOT_IMAGES data
    # 'plot_images' contains a set of images so user can tell if ROI selection is appropriate
    plot_images = [{'im': None, 'label': ''} for _ in range(2)]
    plot_images[0]['im'] = im_summary # check if it's the same as im_bg
    plot_images[0]['label'] = 'green mean'
    plot_images[1]['im'] = im_bg
    plot_images[1]['label'] = 'scaled'

    # we may want 10 hits per 5 min (every 60 to 90 sec)
    # show more of a range of hits for cursor
    # A T = 0.3 or 0.4 (OR 3 or 4) (we want 0.5 to 1) might be noise so we wouldn't want that
    # Want a Gaussian distribution of T, if not a bit flatter overall
    # Calibration may be wrong if no hits happen in the first 5 min

    print('Detecting Cells')
    print('----------------------------------------')
    '''
    mask_intermediate, _ = im_find_cells_tm(im_bg, task_set['roi']['template_diam'],task_set['roi']['thres'], task_set['roi']['cell_diam'], task_set['roi']['finemode'], task_set['roi']['temmode'] )
    init_roi_mask = label(mask_intermediate)
    x_center, y_center = get_center(init_roi_mask[0], im_bg, True)
    roi_data = label_mask2roi_data_single_channel(im_bg, init_roi_mask[0], task_set['im']['chan_data'])
    '''
    roi_mask = im_find_cells_suite2p(im_bg)
    #x_center, y_center = get_center(roi_mask, im_bg, True)

    # Add ROI if needed
    # print('Adding ROIs to image!')
    print('Editing ROI mask!')
    roi_mask = edit_roi_mask(roi_mask, path_data['save_path'])
    # roi_data = draw_roi_g_chan(plot_images, roi_data)
    plt.close('all')

    # Need to make sure that the F is greater than 0 for added ROIs
    # Figure out how to delete
    roi_data = label_mask2roi_data_single_channel(im_bg, roi_mask, task_set['im']['chan_data'])

    '''
    # Delete ROI if needed
    print('Deleting ROIs from image!')
    print('----------------------------------------')
    roi_data = delete_roi_2chan(plot_images, roi_data)
    plt.close('all')
    '''

    # Visualize
    plt.figure()
    plt.imshow(roi_data['im_roi'])
    plt.title('ROI footprint overlay in blue')
    plt.show()

    plt.figure()
    plt.imshow(roi_data['roi_mask'])
    plt.title('ROI Mask')
    plt.show()
    print('----------------------------------------')

    # See ROI if needed
    if see_roi_data_flag:
        plt.figure()
        plt.imshow(roi_data['roi_mask'], cmap='gray')
        plt.title(f'roi_mask num roi: {roi_data["num_rois"]}')
        plt.show()

        plt.figure()
        plt.imshow(roi_data['im_roi'], cmap='gray')
        plt.title(f'ROI footprint overlay in blue. Num ROI: {roi_data["num_rois"]}')
        plt.show()

    #np.savez(roi_data_path, plot_images=plot_images, im_sc_struct=im_sc_struct, roi_data=roi_data, allow_pickle=True)
    return np.load(roi_data_path, allow_pickle=True)