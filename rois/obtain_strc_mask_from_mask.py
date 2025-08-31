import numpy as np
from rois.find_center import find_center

def obtain_strc_mask_from_mask(mask):
    x, y = find_center(mask)
    roi_ctr = np.vstack((x, y))  # shape: (2, num_roi)

    roi_ind = np.unique(mask)
    roi_ind = roi_ind[roi_ind != 0]  # remove the 0 index
    num_roi = len(roi_ind)

    strc_mask = {
        'roi_ind': roi_ind,
        'num_roi': num_roi,
        'maxx': [],
        'minx': [],
        'maxy': [],
        'miny': [],
        'neuron_mask': [],
        'xctr': [],
        'yctr': [],
        'width': [],
        'height': [],
    }

    for u in range(num_roi):
        aux_mask = np.copy(mask)
        aux_mask[aux_mask != roi_ind[u]] = 0
        posx = np.where(np.sum(aux_mask, axis=0) != 0)[0]
        posy = np.where(np.sum(aux_mask, axis=1) != 0)[0]

        strc_mask['maxx'].append(posx[-1])
        strc_mask['minx'].append(posx[0])
        strc_mask['maxy'].append(posy[-1])
        strc_mask['miny'].append(posy[0])
        strc_mask['neuron_mask'].append(aux_mask[posy[0]:posy[-1]+1, posx[0]:posx[-1]+1])

        strc_mask['xctr'].append(roi_ctr[0, u])
        strc_mask['yctr'].append(roi_ctr[1, u])
        strc_mask['width'].append(abs(posx[-1] - posx[0]))
        strc_mask['height'].append(abs(posy[-1] - posy[0]))

    return strc_mask