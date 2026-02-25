import numpy as np
import matplotlib.pyplot as plt


def plot_e_activity(t, n, E_id, E_color, offset=0):
    """
    Python version of MATLAB function plot_E_activity

    Parameters
    ----------
    t : array-like
        Time vector, length num_samples
    n : array-like
        Neural activity, shape (num_samples, num_neurons)
    E_id : array-like of int
        Values 1 or 2 indicating membership in E1 or E2
    E_color : list
        List of colors for groups E1 and E2, e.g. ['r', 'b']
    offset : float, optional
        Initial vertical offset

    Returns
    -------
    fig : matplotlib.figure.Figure
    offset_vec : list
        Offsets applied to each neuron trace
    """

    n = np.asarray(n)
    num_neurons = n.shape[1]

    offset_vec = [offset]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    for i in range(num_neurons):
        y_plot = n[:, i]
        y_plot = y_plot - np.min(y_plot)  # normalize to zero
        y_amp = np.max(y_plot)  # amplitude

        if i > 0:
            offset += y_amp
            offset_vec.append(offset)

        y_plot = y_plot - offset  # shift downward

        ax.plot(t, y_plot, color=E_color[E_id[i] - 1])

    return fig, ax, offset_vec