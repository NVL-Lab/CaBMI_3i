import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label

from rois.scale_im_interactive import scale_im_interactive
from segmentation.im_find_cells_tm import im_find_cells_tm
from rois.get_center import get_center
from rois.label_mask2roi_data_single_channel import label_mask2roi_data_single_channel
from rois.delete_roi_2chan import delete_roi_2chan
from rois.draw_roi_g_chan import draw_roi_g_chan

def roi_acqnvs_3i(sb_file_reader, capture, task_set, path_data, see_roi_data_flag=False, run=False) -> np.array:

    roi_data_path = path_data['save_path'] / 'roi_data.npz'
    if not run:
        try :
            roi_data = np.load(roi_data_path, allow_pickle=True)
            return roi_data
        except FileNotFoundError:
            print('ROI data not found. Please run roi_acqnvs_3i')
            exit(1)

    # Single image is used to locate ROIs
    # first = roi detect capture, second=baseline recording, third=bmi recording, fourth=behavior recording
    im_summary = sb_file_reader.ReadImagePlaneBuf(capture,0,0,0,0,True) # capture (0-n), position (~montage = 0), timepoint, zplane num, channel, True for 2d array return

    # Scale image to see ROIs better
    '''
        Why save them all?
        num_im_sc will not be used
        only necessary parameter is im_summary
    '''
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
    print('Cell Identification')
    print('----------------------------------------')
    mask_intermediate, _ = im_find_cells_tm(im_bg, task_set['roi']['template_diam'],task_set['roi']['thres'], task_set['roi']['cell_diam'], task_set['roi']['finemode'], task_set['roi']['temmode'] )
    init_roi_mask = label(mask_intermediate)
    x_center, y_center = get_center(init_roi_mask[0], im_bg, True)
    roi_data = label_mask2roi_data_single_channel(im_bg, init_roi_mask[0], task_set['im']['chan_data'])

    '''
    print('Detecting Cells')
    ops, stat = suite2p.detection_wrapper(f_reg=im_bg, ops=suite2p.default_ops(), classfile=suite2p.classification.builtin_classfile) # im_bg must be npy file
    iscell = suite2p.detection.classify(stat, suite2p.classification.builtin_classfile )
    roi_mask = np.zeros((ops['Ly'], ops['Lx']), dtype=np.uint32)
    cell_count = 0
    for i, roi in enumerate(stat):
        if iscell[i]:
            cell_count += 1
            roi_mask[roi['ypix'], roi['xpix']] = cell_count * roi['lam']
    print(f"{cell_count} cells detected.")
    plt.figure()
    plt.imshow(roi_mask, cmap='nipy_spectral')
    plt.title("ROI Neurons")
    plt.colorbar(label="Label index")
    plt.show()
    roi_data = label_mask2roi_data_single_channel(im_bg, roi_mask[0], task_set['im']['chan_data'])
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

    # Delete ROI if needed
    print('Deleting ROIs from image!')
    print('----------------------------------------')
    roi_data = delete_roi_2chan(plot_images, roi_data)
    plt.close('all')

    # Add ROI if needed
    '''
    print('Adding ROIs to image!')
    roi_data = draw_roi_g_chan(plot_images, roi_data)
    plt.close('all')
    '''

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

    #np.savez(roi_data_path, plot_images=plot_images, roi_data=roi_data, allow_pickle=True)
    return roi_data, im_bg