import numpy as np
import matplotlib.pyplot as plt

def find_center(temp, mat=None, toplot=False):
    if mat is None:
        mat = np.zeros_like(temp)
    elif not toplot:
        toplot = True

    cell_ind = np.unique(temp)
    cell_ind = cell_ind[cell_ind != 0]
    num_cells = len(cell_ind)

    y = np.zeros(num_cells, dtype=int)
    x = np.zeros(num_cells, dtype=int)

    for i in range(num_cells):
        y_vals = np.where(temp.T == cell_ind[i])[0]
        x_vals = np.where(temp == cell_ind[i])[0]
        y[i] = int(np.round(np.mean(y_vals) / temp.shape[1])) if len(y_vals) > 0 else 0
        x[i] = int(np.round(np.mean(x_vals) / temp.shape[0])) if len(x_vals) > 0 else 0

    if toplot:
        plt.figure()

        if len(y) > 0:
            plt.subplot(1, 2, 1)
            plt.imshow(temp, cmap='bone', vmin=0, vmax=np.nanmedian(temp) * 5)
            plt.scatter(x, y, c='r')
            plt.axis('square')

            plt.subplot(1, 2, 2)
            plt.imshow(mat, cmap='bone', vmin=0, vmax=np.nanmedian(mat) * 5)
            plt.scatter(x, y, c='r')
            plt.axis('square')
        else:
            plt.subplot(1, 2, 1)
            plt.imshow(temp, cmap='bone', vmin=0, vmax=np.nanmedian(temp) * 5)

            plt.subplot(1, 2, 2)
            plt.imshow(mat, cmap='bone', vmin=0, vmax=np.nanmedian(mat) * 5)

        plt.show()

    return x, y