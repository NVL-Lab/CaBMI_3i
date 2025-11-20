import numpy as np
import matplotlib.pyplot as plt
from skimage.color import gray2rgb
from .roi_bin_cell2center_radius import roi_bin_cell2center_radius

def label_mask2roi_data_single_channel(im_bg, label_mask, temp_data, chan_label, chan_idx):
    roi_data = {}

    roi_data['im_bg'] = gray2rgb(im_bg)  # Convert grayscale to RGB
    roi_data['num_rows'] = im_bg.shape[0]
    roi_data['num_cols'] = im_bg.shape[1]

    roi_data['num_rois'] = int(label_mask.max())
    roi_data['roi_mask'] = label_mask
    roi_data['roi_mask_bin'] = label_mask > 0
    roi_data['roi_bin_cell'] = [(label_mask == roi_id) for roi_id in range(1, roi_data['num_rois'] + 1)]

    roi_data['chan_logical'] = np.vstack([
        np.zeros(roi_data['num_rois']),
        np.ones(roi_data['num_rois'])
    ])

    # Calculate x, y, r from binary ROI masks
    roi_ctr = roi_bin_cell2center_radius(roi_data['roi_bin_cell'])
    roi_data['x'] = roi_ctr['x']
    roi_data['y'] = roi_ctr['y']
    roi_data['r'] = roi_ctr['r']

    # ROI visualizations
    roi_data['im_roi'] = np.zeros((im_bg.shape[0], im_bg.shape[1], 3))
    roi_data['im_roi'][:, :, 1] = im_bg  # Green channel
    roi_data['im_roi'][:, :, 2] = roi_data['roi_mask_bin']  # Blue overlay

    roi_idxs = np.nonzero(roi_data['roi_mask_bin'])
    im_roi_rg = gray2rgb(im_bg)
    g_mod = im_roi_rg[:, :, 1].copy()
    g_mod[roi_idxs] = 1
    im_roi_rg[:, :, 1] = g_mod
    roi_data['im_roi_rg'] = im_roi_rg

    roi_data['chan'] = temp_data
    #chan_idx = len(temp_data)
    roi_data['chan'][chan_idx]['label'] = chan_label
    roi_data['chan'][chan_idx]['num_rois'] = roi_data['num_rois']
    roi_data['chan'][chan_idx]['idxs'] = list(range(1, roi_data['num_rois'] + 1))
    roi_data['chan'][chan_idx]['im_roi'] = roi_data['im_roi']
    roi_data['chan'][chan_idx]['roi_mask'] = label_mask
    roi_data['chan'][chan_idx]['roi_mask_bin'] = roi_data['roi_mask_bin']

    return roi_data