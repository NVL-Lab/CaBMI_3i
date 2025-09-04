import numpy as np
from .find_center import find_center

def get_mask(mask) -> dict:
    """
    Function to create a structure with a reduced image given a spatial filter.

    Parameters:
        mask (ndarray): 2D array representing the mask.

    Returns:
        dict: A dictionary with information about the spatial filters and their positions.
    """

    # Assuming find_center is a previously defined function that returns the center of the mask
    x, y = find_center(mask)
    roi_ctr = np.vstack((x, y))  # size: 2 x num_roi

    # Adjust indices to loop over using 'unique'
    roi_ind = np.unique(mask)
    roi_ind = roi_ind[roi_ind != 0]  # remove the 0 index
    num_roi = len(roi_ind)

    # Initialize the structure (dictionary in Python)
    strc_mask = {
        'roi_ind': roi_ind,
        'num_roi': num_roi,
        'maxx': np.zeros(num_roi, dtype=int),
        'minx': np.zeros(num_roi, dtype=int),
        'maxy': np.zeros(num_roi, dtype=int),
        'miny': np.zeros(num_roi, dtype=int),
        'neuron_mask': [None] * num_roi,
        'xctr': np.zeros(num_roi),
        'yctr': np.zeros(num_roi),
        'width': np.zeros(num_roi),
        'height': np.zeros(num_roi),
    }

    for u in range(num_roi):
        aux_mask = mask.copy()
        aux_mask[aux_mask != roi_ind[u]] = 0
        posx = np.nonzero(np.sum(aux_mask, axis=0))[0]
        posy = np.nonzero(np.sum(aux_mask, axis=1))[0]
        strc_mask['maxx'][u] = posx[-1]
        strc_mask['minx'][u] = posx[0]
        strc_mask['maxy'][u] = posy[-1]
        strc_mask['miny'][u] = posy[0]
        strc_mask['neuron_mask'][u] = aux_mask[posy[0]:posy[-1]+1, posx[0]:posx[-1]+1]

        # Auxiliary Information:
        strc_mask['xctr'][u] = roi_ctr[0, u]
        strc_mask['yctr'][u] = roi_ctr[1, u]
        strc_mask['width'][u] = abs(strc_mask['maxx'][u] - strc_mask['minx'][u])
        strc_mask['height'][u] = abs(strc_mask['maxy'][u] - strc_mask['miny'][u])

    return strc_mask
