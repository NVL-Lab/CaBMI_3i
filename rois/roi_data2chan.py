import numpy as np
#from skimage.color import gray2rgb

def roi_data2chan(roi_data):
    num_chan = len(roi_data['chan'])
    for chan_i in range(num_chan):
        idxs = np.where(roi_data['chan_logical'][chan_i, :] > 0)[0]
        roi_data['chan'][chan_i]['idxs'] = idxs.tolist()
        roi_data['chan'][chan_i]['num_rois'] = len(idxs)

        roi_mask = np.zeros((roi_data['num_rows'], roi_data['num_cols']))
        roi_mask_bin = np.zeros((roi_data['num_rows'], roi_data['num_cols']))
        im_roi = roi_data['im_bg'].copy()

        for i_sel in idxs:
            roi_sel = roi_data['roi_bin_cell'][i_sel]
            roi_idxs = np.nonzero(roi_sel)
            roi_mask[roi_idxs] = i_sel + 1  # MATLAB indexing starts from 1
            roi_mask_bin[roi_idxs] = 1

        im_roi[:, :, 2] = roi_mask_bin  # Blue channel overlay

        roi_data['chan'][chan_i]['roi_mask'] = roi_mask
        roi_data['chan'][chan_i]['roi_mask_bin'] = roi_mask_bin
        roi_data['chan'][chan_i]['im_roi'] = im_roi

    return roi_data