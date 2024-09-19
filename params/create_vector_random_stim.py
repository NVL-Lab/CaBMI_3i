import numpy as np
import matplotlib.pyplot as plt

def get_random_stim(frame_rate, experiment_length, ihsi_mean, ihsi_range, plot=False) -> tuple[list,list]:
    """
    Generate a vector of random stimulus intervals.

    Args:
    - frame_rate: The frame rate of the experiment.
    - experiment_length: The expected length of the experiment in frames.
    - ihsi_mean: The mean inter-stimulus interval (ISI).
    - ihsi_range: The range around the mean ISI.
    - plot: If True, generate plots for debugging.

    Returns:
    - vector_holo: A vector of stimulus times in frames.
    - isi: The inter-stimulus intervals in frames.
    """
    
    # Calculate the average stimulus period and ISI range in frames
    average_stim_eriod = ihsi_mean * frame_rate
    range_ = ihsi_range * frame_rate
    
    # Calculate the number of stimuli
    num_stims = round(experiment_length / average_stim_period)
    
    # Generate random ISIs
    isi = np.random.rand(num_stims) * 2 * range_ + (average_stim_period - range_)
    
    # Generate the cumulative sum of ISIs to get stimulus times
    vector_holo = np.round(np.cumsum(isi))
    
    if plot:
        # Debugging plots
        plt.figure()
        plt.plot(vector_holo, '.-', markersize=15)
        plt.ylabel('Frame Number')
        plt.xlabel('Stim Number')
        plt.title('Frame Number vs Stim Number')
        plt.show()
        
        plt.figure()
        plt.plot(vector_holo / (frame_rate * 60), '.-', markersize=15)
        plt.ylabel('Time (min)')
        plt.title('Stim time (min) vs Stim Number')
        plt.show()
        
        plt.figure()
        plt.hist(isi, bins=100)
        plt.xlabel('isi (frames)')
        plt.ylabel('Count')
        plt.title('isi distribution (unnormalized)')
        plt.show()
    
    return vector_holo, isi
