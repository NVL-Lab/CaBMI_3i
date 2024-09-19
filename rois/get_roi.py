import numpy as np

def get_roi(im, mask, units=None):
    """
    Function to obtain the activity of each neuron, given a spatial filter.
    
    Parameters:
    im (numpy.ndarray): Image data.
    mask (dict): Structure containing the matrix for spatial filters, positions, and other relevant data.
    units (list): Indices of the neurons in the neuron_mask that we want to process.
    
    Returns:
    numpy.ndarray: Array of activity values for the specified neurons.
    """
    if units is None:
        units = range(len(mask['neuron_mask']))

    unit_vals = np.zeros(len(units))

    for auxu, u in enumerate(units):
        posmaxx = mask['maxx'][u]
        posminx = mask['minx'][u]
        posmaxy = mask['maxy'][u]
        posminy = mask['miny'][u]

        imd = im[posminy:posmaxy+1, posminx:posmaxx+1].astype(float)

        neuron_mask = mask['neuron_mask'][u].astype(float)
        unit_vals[auxu] = np.nansum(imd * neuron_mask / u / np.nansum(neuron_mask))

    return unit_vals
