import numpy as np
import matplotlib.pyplot as plt

def plot_neurons_ensemble(base_activity, ensemble_neurons, ensemble_id):
    """
    Function to plot the temporal activity of neurons collected during baseline to select the best neurons.
    
    Parameters:
    - base_activity: 2D NumPy array with activity during baseline (neurons x time)
    - ensemble_neurons: List of neuron indices to be plotted
    - ensemble_id: List of IDs corresponding to the ensemble group for each neuron
    """
    
    # Define colors
    plot_b = [0, 0.4470, 0.7410]  # Blue
    plot_o = [0.8500, 0.3250, 0.0980]  # Orange
    e_color = [plot_b, plot_o] 

    total_neurons = len(ensemble_neurons)
    subplot_nmb = int(np.ceil(total_neurons / 2))
    
    # Create a new figure
    plt.figure(figsize=(subplot_nmb * 5, 4))
    
    for idx, neuron in enumerate(ensemble_neurons):
        plt.subplot(2, subplot_nmb, idx + 1)
        plot_color = e_color[ensemble_id[idx] - 1]  # Adjust for 0-based index
        plt.plot(base_activity[neuron, :], color=plot_color)
        plt.title(f'ROI {neuron}')
        plt.legend([str(ensemble_id[idx])])
    
    plt.tight_layout()
    plt.show()
