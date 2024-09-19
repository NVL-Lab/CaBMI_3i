import numpy as np
import matplotlib.pyplot as plt

def get_center(temp, mat=None, toplot=False):
    """
    Function to find the center of mass for the detected cells.
    
    Parameters:
        temp (ndarray): The template or ROI mask
        mat (ndarray, optional): The raw image
        toplot (bool, optional): Flag to allow plotting
        
    Returns:
        tuple: x, y coordinates of the centers
    """

    # This part is questionable
    if mat is None:
        mat = np.zeros_like(temp)
        toplot = False
    
    cell_ind = np.unique(temp)
    cell_ind = cell_ind[cell_ind != 0]  # Remove the 0 index
    num_cells = len(cell_ind)
    
    y = np.zeros(num_cells)
    x = np.zeros(num_cells)
    
    for i in range(num_cells):
        y[i] = round(np.mean(np.where(temp.T == cell_ind[i])[0]) / temp.shape[1])
        x[i] = round(np.mean(np.where(temp == cell_ind[i])[0]) / temp.shape[0])
    
    if toplot:
        plt.figure()
        if y.size > 0:
            plt.subplot(1, 2, 1)
            plt.imshow(temp, cmap='bone')
            plt.clim([-0, np.nanmedian(temp) * 5])
            plt.scatter(x, y, c='r', s=50)
            plt.axis('square')
            
            plt.subplot(1, 2, 2)
            plt.imshow(mat, cmap='bone')
            plt.clim([-0, np.nanmedian(mat) * 5])
            plt.scatter(x, y, c='r', s=50)
            plt.axis('square')
        else:
            plt.subplot(1, 2, 1)
            plt.imshow(temp, cmap='bone')
            plt.clim([-0, np.nanmedian(temp) * 5])
            
            plt.subplot(1, 2, 2)
            plt.imshow(mat, cmap='bone')
            plt.clim([-0, np.nanmedian(mat) * 5])

        plt.show()
    
    return x, y
