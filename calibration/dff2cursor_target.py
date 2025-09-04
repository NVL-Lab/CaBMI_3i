import numpy as np

def dff2cursor_target(dff, bdata, cursor_zscore_bool):
    """
    Function to process dF/F values, calculate cursor values, and determine if a target is hit.

    Parameters:
    dff (array-like): Smoothed dF/F values.
    bdata (dict): Data structure containing the following fields:
                  - n_mean: Mean of neural data.
                  - n_std: Standard deviation of neural data.
                  - decoder: Decoder vector.
                  - E1_sel_idxs: Indices for E1 selection.
                  - E2_sel_idxs: Indices for E2 selection.
                  - E1_thresh: Threshold for E1.
                  - E2_subord_thresh: Threshold for E2 subordinates.
                  - T1: Target threshold.
    cursor_zscore_bool (bool): If True, z-score dF/F values before processing.

    Returns:
    tuple: (dff_z, cursor, target_hit, c1_bool, c2_val, c2_bool, c3_val, c3_bool)
    """
    num_e2 = len(bdata['e2_sel_idxs'].flatten())

    # Ensure dff is a row vector
    dff = np.array(dff).flatten()
    dff_z = dff

    # Z-score normalization if required
    if cursor_zscore_bool:
        dff_z = (dff - bdata['n_mean']) / bdata['n_std']
        dff_z = dff_z.flatten()  # Ensure dff_z is a row vector
        n_analyze = dff_z
    else:
        n_analyze = dff

    # Select E1 and E2 ensembles
    e1 = n_analyze[bdata['e1_sel_idxs'].flatten()-1]
    e2 = n_analyze[bdata['e2_sel_idxs'].flatten()-1]

    # c1: cursor
    cursor = np.dot(n_analyze, bdata['decoder'])
    #c1_val = cursor #Unknown usage

    # c2: E1_mean
    e1_mean = np.mean(e1)
    c2_val = e1_mean

    # c3: E2_subord
    e2_sum = np.sum(e2)
    e2_dom_samples = np.max(e2)
    e2_dom_sel = np.argmax(e2)
    e2_subord_mean = (e2_sum - e2_dom_samples) / (num_e2 - 1)
    c3_val = e2_subord_mean

    # Boolean checks
    c1_bool = cursor >= bdata['t1']
    c2_bool = e1_mean <= bdata['e1_thresh']
    c3_bool = e2_subord_mean >= bdata['e2_subord_thresh'][e2_dom_sel]

    # Determine if the target is hit
    target_hit = c1_bool

    return dff_z, cursor, target_hit, c1_bool, c2_val, c2_bool, c3_val, c3_bool