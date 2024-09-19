import numpy as np

def roi_data2chan(roi_data):
    """
    Function to update channel information for each channel in roi_data.
    """
    num_chan = len(roi_data['chan'])
    
    for chan_i in range(num_chan):
        # Find indices where chan_logical is True for the current channel
        roi_data['chan'][chan_i]['idxs'] = np.where(roi_data['chan_logical'][chan_i, :])[0]
        roi_data['chan'][chan_i]['num_rois'] = len(roi_data['chan'][chan_i]['idxs'])
        
        # Initialize roi_mask and roi_mask_bin
        roi_data['chan'][chan_i]['roi_mask'] = np.zeros((roi_data['num_rows'], roi_data['num_cols']))
        roi_data['chan'][chan_i]['roi_mask_bin'] = np.zeros((roi_data['num_rows'], roi_data['num_cols']))
        roi_data['chan'][chan_i]['im_roi'] = roi_data['im_bg'].copy()
        
        # Build roi_mask and roi_mask_bin for the current channel
        for sel_i in roi_data['chan'][chan_i]['idxs']:
            roi_sel = roi_data['roi_bin_cell'][sel_i]
            roi_idxs = np.nonzero(roi_sel)
            
            roi_data['chan'][chan_i]['roi_mask'][roi_idxs] = sel_i + 1
            roi_data['chan'][chan_i]['roi_mask_bin'][roi_idxs] = 1
            
            # Update the third channel (blue) of the im_roi image
            roi_data['chan'][chan_i]['im_roi'][:, :, 2] = roi_data['chan'][chan_i]['roi_mask_bin']
    
    return roi_data

