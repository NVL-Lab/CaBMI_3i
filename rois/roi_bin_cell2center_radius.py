import numpy as np

def roi_bin_cell2center_radius(roi_bin_cell):
    """
    Calculate the center and radius of each ROI in the roi_bin_cell.
    
    Parameters:
    roi_bin_cell (list): List of binary images (2D numpy arrays) where each array represents an ROI.
    
    Returns:
    roi_ctr (dict): Dictionary containing the center coordinates (x, y) and radius (r) for each ROI.
    """
    num_roi = len(roi_bin_cell)
    roi_ctr = {
        'x': np.zeros(num_roi),
        'y': np.zeros(num_roi),
        'r': np.zeros(num_roi)
    }

    for roi_i in range(num_roi):
        roi_im = roi_bin_cell[roi_i]
        roi_idxs = np.argwhere(roi_im)

        if roi_idxs.size > 0:
            roi_ctr['x'][roi_i] = np.round(np.mean(roi_idxs[:, 1]))
            roi_ctr['y'][roi_i] = np.round(np.mean(roi_idxs[:, 0]))

            x_occupy = np.where(np.sum(roi_im, axis=0) > 0)[0]
            y_occupy = np.where(np.sum(roi_im, axis=1) > 0)[0]

            xdel = np.max(x_occupy) - np.min(x_occupy)
            ydel = np.max(y_occupy) - np.min(y_occupy)
            roi_ctr['r'][roi_i] = max(xdel, ydel) / 2
    
    return roi_ctr

