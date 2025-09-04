import numpy as np

def get_roi(im, strc_mask, units=None):
    """
    Obtain the activity of each neuron given a spatial filter.

    Parameters
    ----------
    im : np.ndarray
        2D image (e.g. fluorescence frame).
    strc_mask : dict
        Dictionary with:
            - 'neuron_mask': list of 2D numpy arrays (one mask per neuron).
            - 'minx', 'maxx', 'miny', 'maxy': lists/arrays with bounding box coords.
    units : list[int], optional
        Indices of neurons to extract. If None, all neurons are used.

    Returns
    -------
    np.ndarray
        Activity values, one per requested unit.
    """

    # Default: all units
    if units is None:
        units = range(len(strc_mask['neuron_mask']))

    unit_vals = np.zeros(len(units))

    for i, u in enumerate(units):
        # bounding box
        posminx, posmaxx = strc_mask['minx'][u], strc_mask['maxx'][u]
        posminy, posmaxy = strc_mask['miny'][u], strc_mask['maxy'][u]

        # crop the image and corresponding mask
        imd = im[posminy:posmaxy+1, posminx:posmaxx+1].astype(float)
        mask = strc_mask['neuron_mask'][u].astype(float)

        # compute mean intensity within ROI
        roi_pixels = imd[mask > 0]
        if roi_pixels.size > 0:
            unit_vals[i] = np.nanmean(roi_pixels)
        else:
            unit_vals[i] = np.nan  # no valid pixels

        '''
        # weighted activity (normalized by mask sum). why do they scale down?
        mask_sum = np.nansum(mask)
        if mask_sum == 0:
            unit_vals[i] = np.nan
        else:
            unit_vals[i] = np.nansum(imd * mask / mask_sum) / (u+1)
        '''

    return unit_vals