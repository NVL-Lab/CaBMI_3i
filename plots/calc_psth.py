import numpy as np

def calc_psth(data_mat, event_idxs, win):
    """
    Return mean and stderr at each point

    Parameters:
    -----------
    data_mat : np.ndarray
        Shape (num_samples, num_var)
    event_idxs : array-like
        Indices of events to align to
    win : tuple or list
        (start, end) window relative to event index

    Returns:
    --------
    psth_mean : np.ndarray
        Mean across valid events (shape = (psth_len, num_var))
    psth_sem : np.ndarray
        Standard error of the mean (shape = (psth_len, num_var))
    psth_mat : np.ndarray
        Matrix of all valid event-aligned data (shape = (psth_len, num_var, num_valid_events))
    """

    event_idxs = np.asarray(event_idxs, dtype=int)
    num_events = len(event_idxs)
    num_samples, num_var = data_mat.shape

    psth_len = win[1] - win[0] + 1
    psth_mat = np.zeros((psth_len, num_var, num_events))

    event_valid = np.ones(num_events, dtype=bool)

    for i, event_idx in enumerate(event_idxs):
        event_sel = np.arange(win[0], win[1] + 1) + event_idx
        if np.min(event_sel) < 0 or np.max(event_sel) >= num_samples:
            event_valid[i] = False
        else:
            psth_mat[:, :, i] = data_mat[event_sel, :]

    # Keep only valid events
    valid_idxs = np.where(event_valid)[0]
    psth_mat = psth_mat[:, :, valid_idxs]
    num_valid_events = len(valid_idxs)

    # Compute mean, variance, std, sem
    psth_mean = np.mean(psth_mat, axis=2)
    psth_var = np.var(psth_mat, axis=2, ddof=0)
    psth_std = np.sqrt(psth_var)
    psth_sem = psth_std / np.sqrt(num_valid_events)

    return psth_mean, psth_sem, psth_mat