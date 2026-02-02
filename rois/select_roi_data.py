import numpy as np
import matplotlib.pyplot as plt

def select_roi_data(roi_data, sel_idxs):
    sel_idxs = np.unique(sel_idxs)
    roi_data_sel = {}

    roi_data_sel['sel_idxs'] = sel_idxs.tolist()
    roi_data_sel['im_bg'] = roi_data['im_bg']
    roi_data_sel['num_rows'] = roi_data['num_rows']
    roi_data_sel['num_cols'] = roi_data['num_cols']
    roi_data_sel['num_rois'] = len(sel_idxs)
    roi_data_sel['roi_bin_cell'] = [roi_data['roi_bin_cell'][i] for i in sel_idxs]
    roi_data_sel['chan_logical'] = roi_data['chan_logical'][:, sel_idxs]
    roi_data_sel['x'] = roi_data['x'][sel_idxs]
    roi_data_sel['y'] = roi_data['y'][sel_idxs]
    roi_data_sel['r'] = roi_data['r'][sel_idxs]

    roi_data_sel['im_roi'] = roi_data['im_bg'].copy()
    roi_data_sel['im_roi_rg'] = roi_data['im_bg'].copy()
    roi_data_sel['roi_mask'] = np.zeros((roi_data_sel['num_rows'], roi_data_sel['num_cols']))
    roi_data_sel['roi_mask_bin'] = np.zeros((roi_data_sel['num_rows'], roi_data_sel['num_cols']))

    for i in range(roi_data_sel['num_rois']):
        roi_num = sel_idxs[i]
        roi_i = roi_data_sel['roi_bin_cell'][i]
        roi_idxs = np.where(roi_i)[0]
        roi_data_sel['roi_mask'].flat[roi_idxs] = roi_num
        roi_data_sel['roi_mask_bin'].flat[roi_idxs] = 1

        chan_idx = np.where(roi_data_sel['chan_logical'][:, i])[0]
        for c in chan_idx:
            chan_im = roi_data_sel['im_roi_rg'][:, :, c]
            chan_im.flat[roi_idxs] = 1
            roi_data_sel['im_roi_rg'][:, :, c] = chan_im

    roi_data_sel['im_roi'][:, :, 2] = roi_data_sel['roi_mask_bin']

    # Visualize
    plt.figure(figsize=(8, 8))
    plt.title('Background Image + Rois')
    plt.imshow(roi_data_sel['im_roi'])
    plt.show()

    plt.figure(figsize=(8, 8))
    plt.title(f'Num ROI: {roi_data_sel["num_rois"]}')
    #plt.imshow(roi_data_sel['roi_mask'], cmap='gray')
    plt.imshow(roi_data['roi_mask'])
    plt.show()

    return roi_data_sel, sel_idxs