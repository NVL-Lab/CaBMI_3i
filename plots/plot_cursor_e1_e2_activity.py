import numpy as np
import matplotlib
import matplotlib.pyplot as plt

def plot_cursor_e1_e2_activity(cursor, e1, e2, n, e_id, e_color, offset=0) -> tuple[matplotlib.figure.Figure, list]:
    num_e1 = np.sum(e_id == 1)
    e1_sel = np.where(e_id == 1)[0]
    n_e1 = n[:, e1_sel]

    num_e2 = np.sum(e_id == 2)
    e2_sel = np.where(e_id == 2)[0]
    n_e2 = n[:, e2_sel]

    offset_vec = [offset]
    
    fig, ax = plt.subplots()
    ax.plot(cursor, label='cursor')
    y_amp = np.max(cursor) - np.min(cursor)
    offset += y_amp
    offset_vec.append(offset)

    e1_plot = e1 - offset
    ax.plot(e1_plot, 'k', label='E1')
    y_amp = np.max(e1_plot) - np.min(e1_plot)
    offset += y_amp
    offset_vec.append(offset)

    e2_plot = e2 - offset
    ax.plot(e2_plot, 'r', label='E2')
    y_amp = np.max(e2_plot) - np.min(e2_plot)
    offset += y_amp
    offset_vec.append(offset)

    # Plot neural activity for E1
    for i in range(num_e1):
        y_plot = n_e1[:, i]
        y_plot -= np.min(y_plot)
        y_amp = np.max(y_plot)
        
        offset += y_amp
        offset_vec.append(offset)
        y_plot -= offset
        ax.plot(y_plot, color=e_color[0])
    
    # Plot neural activity for E2
    for i in range(num_e2):
        y_plot = n_e2[:, i]
        y_plot -= np.min(y_plot)
        y_amp = np.max(y_plot)
        
        offset += y_amp
        offset_vec.append(offset)
        y_plot -= offset
        ax.plot(y_plot, color=e_color[1])
    
    ax.legend()
    #plt.show()

    return fig, offset_vec
