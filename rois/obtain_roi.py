import numpy as np

def get_roi(im, strc_mask, units=None):
    """
    Function to obtain the activity of each neuron, given a spatial filter.
    
    Parameters:
    im (ndarray): Image data.
    strc_mask (dict): Structure with the matrix for spatial filters with px*py*unit
                     and the positions of that mask.
    units (list): List of indices of the neurons in the neuron_ask that we want.
                  If not provided, all units will be used.
    
    Returns:
    unit_vals (ndarray): The activity values for each neuron.
    """
    if units is None:
        units = range(len(strc_mask['neuron_mask']))
    
    unit_vals = np.zeros(len(units))
    
    for auxu, u in enumerate(units):
        posmaxx = strc_mask['maxx'][u]
        posminx = strc_mask['minx'][u]
        posmaxy = strc_mask['maxy'][u]
        posminy = strc_mask['miny'][u]
        imd = im[posminy:posmaxy+1, posminx:posmaxx+1].astype(np.float64)
        mask = strc_mask['neuron_mask'][u]
        unit_vals[auxu] = np.nansum(imd * mask / u / np.nansum(mask))
    
    return unit_vals
