import numpy as np
import matplotlib.pyplot as plt
from skimage.color import gray2rgb
from .roi_bin_cell2center_radius import roi_bin_cell2center_radius

def label_mask2roi_data_single_channel(im_bg, label_mask, chan_data):
    roi_data = {}

    num_chan = 1 #len(chan_data)
    num_rows, num_cols = im_bg.shape[:2]

    roi_data['num_chan'] = num_chan
    roi_data['im_bg'] = gray2rgb(im_bg)  # Convert grayscale to RGB
    roi_data['num_rows'] = num_rows
    roi_data['num_cols'] = num_cols

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
    roi_data['im_roi'] = np.zeros((num_rows, num_cols, 3))
    roi_data['im_roi'][:, :, 1] = im_bg  # Green channel
    roi_data['im_roi'][:, :, 2] = roi_data['roi_mask_bin']  # Blue overlay

    roi_idxs = np.nonzero(roi_data['roi_mask_bin'])
    im_roi_rg = gray2rgb(im_bg)
    g_mod = im_roi_rg[:, :, 1].copy()
    g_mod[roi_idxs] = 1
    im_roi_rg[:, :, 1] = g_mod
    roi_data['im_roi_rg'] = im_roi_rg

    # Assign channel info
    roi_data['chan'] = [{} for _ in range(num_chan)]
    for i, chan in enumerate(chan_data):
        chan_idx = chan_data['gfp_idx']-1
        roi_data['chan'][chan_idx]['label'] = 'g' #chan_data['label']
        roi_data['chan'][chan_idx]['num_rois'] = roi_data['num_rois']
        roi_data['chan'][chan_idx]['idxs'] = list(range(1, roi_data['num_rois'] + 1))
        roi_data['chan'][chan_idx]['im_roi'] = roi_data['im_roi']
        roi_data['chan'][chan_idx]['roi_mask'] = label_mask
        roi_data['chan'][chan_idx]['roi_mask_bin'] = roi_data['roi_mask_bin']

    # Visualization
    plt.figure(figsize=(8, 8))
    plt.imshow(roi_data['im_bg'])
    plt.title('Background Image')
    #plt.axis('square')
    plt.colorbar()
    plt.show()

    plt.figure(figsize=(8, 8))
    plt.imshow(roi_data['im_roi'])
    plt.title(f'Num ROI: {roi_data["num_rois"]}')
    #plt.axis('square')
    plt.colorbar()
    plt.show()

    return roi_data