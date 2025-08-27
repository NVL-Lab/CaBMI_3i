author_= 'Saul Gurgua Lopez'

import sys
import time
from pathlib import Path
import matplotlib.pyplot as plt
#import suite2p

from roi_acqnvs_3i import roi_acqnvs_3i
from params.define_exp_path import get_exp_info
from params.define_bmi_task_settings import get_bmi_settings
from params.define_fb_audio_settings import get_fb_settings
from SBReadFile22.SBReadFile import *

from baseline_acqnvs_3i import baseline_acqnvs_3i
from plots.plot_neurons_baseline import plot_neurons_baseline
from plots.plot_neurons_ensemble import plot_neurons_ensemble
from rois.select_roi_data import select_roi_data
from calibration.baseline2target import baseline2target
from params.create_vector_random_stim import get_random_stim
from params.play_tone import play_tone
from bmi_acqnvs_3i import bmi_acqnvs_3i
from check_motor_behavior import check_motor_behavior

'''
    On Slidebook, create new slide
'''

def wait_for_reader(file_path, wait_seconds=500):
    for attempt in range(wait_seconds):
        if file_path.exists():
            try:
                reader = SBReadFile()
                reader.Open(str(file_path), All=False)
                return reader
            except FileNotFoundError:
                print(f"Attempt {attempt + 1}: file not ready, retrying...")
        else:
            if attempt == 0:
                print(
                    f"Input file does not exist. Retrying for up to {wait_seconds} seconds\n"
                    "Press Ctrl+C to exit."
                )
        time.sleep(1)
    print("Giving up.")
    sys.exit(1)

if __name__ == '__main__':
    # Acquire experiment settings
    fb_set = get_fb_settings()
    task_set = get_bmi_settings()
    exp_info = get_exp_info()

    # Initialize saving directory
    save_path = Path(f"{exp_info['folder']}/{exp_info['animal']}/{exp_info['date']}/{exp_info['day']}")
    #save_path.mkdir(parents=True, exist_ok=True)

    # Storing path and environment data
    path_data = {
        'sldy_path': Path(exp_info['sldy_dir_winsave']),
        'baseline_env': task_set['baseline_env'],
        'bmi_env': task_set['bmi_env'],
        'save_path': save_path,
        'im': save_path / 'im'
    }
    print('\nData Paths:\n', path_data, '\n')

    # Initializing slidebook object
    sb_file_reader = wait_for_reader(path_data['sldy_path'])

    '''
        ROI Acquisition
    '''
    roi_data = roi_acqnvs_3i(sb_file_reader, task_set, save_path, True, True)

    '''
        Baseline Acquisition
    '''
    bdata_path = baseline_acqnvs_3i(path_data, roi_data['roi_mask'], task_set, sb_file_reader)
    bdata = np.load(bdata_path, allow_pickle=True)

    # Plot neurons from baseline
    plot_neurons_baseline(bdata, None, None, np.max(roi_data['num_rois']))
    e1_base = sorted([11, 12])
    e2_base = sorted([4, 13]) # 1 3 5 6 8 9 13
    ensemble_neurons = e1_base + e2_base
    plot_neurons_ensemble(bdata, ensemble_neurons, [1] * len(e1_base) + [2] * len(e2_base))
    select_roi_data(roi_data, list(set(e2_base) | set(e1_base)))

    num_base_samples = np.sum(~np.isnan(bdata[0, :]))
    baseline_frame_rate = num_base_samples / (15 * 60)
    
    sec_per_reward_range = np.array([120, 90])

    frames_per_reward_range = sec_per_reward_range * baseline_frame_rate
    print('Time (s) per reward range:')
    print(sec_per_reward_range)
    print('Frames per reward range:')
    print(frames_per_reward_range)
    
    # Ensure sec_per_reward_range is greater than 80 seconds
    if np.any(sec_per_reward_range <= 80):
        raise ValueError("sec_per_reward_range must be higher than 80 seconds to keep the occurrence of artificial vs natural higher than 80%")
    
    # Calculate reward per frame range
    reward_per_frame_range = 1. / frames_per_reward_range

    # STOPPED - CONTINUE HERE
    target_info_path, target_cal_all_path, fb_cal = baseline2target(bdata_path, roi_data_path, e1_base, e2_base, frames_per_reward_range, task_set, save_path, fb_set)

    # Define the experiment length based on frame rate
    experiment_length = 30 * 60 * task_set['im']['frame_rate']

    # Generate vector_stim and ISI
    vector_stim, isi = get_random_stim(task_set['im']['frameRate'], experiment_length, task_set['rs']['IHSImean'], task_set['rs']['IHSIrange'], False)

    # Set the seed for baseline
    seed_base = 0
    if not seed_base:
        vector_stim += task_set['f0_win']

    '''
        Baseline Acquisition
    '''
    # Run BMI (Brain-Machine Interface) Experiment
    # --------------------------------------------------
    # DO!!!
    # Rename the file on the jetball computer!
    # Optionally load base_val_seed from previous BMI

    # Example of loading pretraining data
    #pretrain_file = 'BMI_online190524T131817.npy'
    #pretrain_data = np.load(os.path.join(savePath, pretrain_file), allow_pickle=True).item()

    # Handle pretrain_base and base_val_seed
    #pretrain_base = pretrain_data['baseVector']
    #pretrain_base = pretrain_base[:, ~np.isnan(pretrain_base[0, :])]
    #base_val_seed = pretrain_base[:, -1] if pretrain_base.size > 0 else None

    # Test Feedback (FB)
    if fb_set['fb_bool']:
        fb_freq_i = 7000
        fb_set['arduino']['duration'] = 1
        # Should change fbset['arduino']['duration'] to not include 'arduino' as a key
        play_tone(fb_freq_i, fb_set['arduino']['duration']) #This will be changed and will use the MiceBall/RATBALL code, which has tone code

    # Set up base_val_seed for the BMI experiment
    base_val_seed = np.ones(len(e1_base) + len(e2_base)) * np.nan

    # Close all plots and display the background image
    plt.close('all')
    plt.imshow(im_bg)

    # Define the type of experiment and run the BMI acquisition
    bmi_acqnvs_3i(path_data, exp_info['expt'], target_info_path, task_set, vector_stim, 0, [], base_val_seed, fb_set['fb_bool'], fb_cal, sb_file_reader)

    # D0:
    # 1) Save the workspace in folder
    # 2) Save this protocol script in the folder (savePath)

    # If motor behavior experiment, run this
    check_motor_behavior(path_data, task_set, exp_info['expt'], sb_file_reader)
