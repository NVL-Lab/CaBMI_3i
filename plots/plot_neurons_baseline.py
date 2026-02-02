import numpy as np
import matplotlib.pyplot as plt

def plot_neurons_baseline(base_activity, c_comp, yr_a, total_neurons=20):
    """
    Function to plot the temporal activity of neurons collected during baseline
    to select the best neurons.

    Parameters:
    - base_activity: Activity during baseline (2D NumPy array)
    - c_comp: C_on from holostim period given by onacid (2D NumPy array)
    - yr_a: Background noise of C (2D NumPy array)
    - total_neurons: Amount of neurons to be displayed (integer)
    """
    # Calculate standard deviation and mean
    s = np.nanstd(base_activity[:, 10:], axis=1)
    sm = s / np.nanmean(base_activity[:, 10:], axis=1)

    # Sort neurons based on sm and s
    ind = np.argsort(s)[::-1]
    indm = np.argsort(sm)[::-1]

    # Display neuron indices from best to worst
    print('Neurons from best to worst S:')
    print(ind[:total_neurons])
    print('Neurons from best to worst Sm:')
    print(indm[:total_neurons])

    subplot_nmb = int(np.ceil(np.sqrt(total_neurons)))
    plt.figure(figsize=(12, 12))
    
    for idx in range(total_neurons):
        plt.subplot(subplot_nmb, subplot_nmb, idx + 1)
        plt.plot(base_activity[ind[idx], :].T)
        plt.title(f'ROI {ind[idx]}')

    plt.tight_layout()
    plt.show()

    # Plot C and Cnoise
    if c_comp is not None:
        c_noise = c_comp + yr_a
        plt.figure(figsize=(12, 12))
        
        for idx in range(total_neurons):
            plt.subplot(subplot_nmb, subplot_nmb, idx + 1)
            plt.plot(c_noise[indm[idx], :].T, label='CNoise')
            plt.plot(c_comp[indm[idx], :].T, label='CComp')
            plt.title(f'ROI {indm[idx]}')
            plt.legend()

        plt.tight_layout()
        plt.show()

