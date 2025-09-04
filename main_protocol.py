author_= 'Saul Gurgua Lopez'

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

from params.play_tone import play_tone

from roi_acqnvs_3i import roi_acqnvs_3i
from params.define_exp_path import get_exp_info
from params.define_bmi_task_settings import get_bmi_settings
from params.define_fb_audio_settings import get_fb_settings

from baseline_acqnvs_3i import baseline_acqnvs_3i
from plots.plot_neurons_baseline import plot_neurons_baseline
from plots.plot_neurons_ensemble import plot_neurons_ensemble
from rois.select_roi_data import select_roi_data
from calibration.baseline2target import baseline2target
from params.create_vector_random_stim import get_random_stim
from bmi_acqnvs_3i import bmi_acqnvs_3i

from check_motor_behavior import check_motor_behavior

"""
    Performs data acquisition of calcium imaging through the use of a 3i microscope

    Requirements:
        Slidebook (3i software): for manually starting the recording and storing of npy image data
        Suite2p (Image processing software): for ROI detection
"""

if __name__ == '__main__':
    # Acquire experiment settings
    fb_set = get_fb_settings()
    #task_set = get_bmi_settings(38.6)
    task_set = get_bmi_settings()
    exp_info = get_exp_info()

    # Storing path and environment data
    path_data = {
        'sldy_path': Path(exp_info['sldy_dir_macsave']),
        'baseline_env': task_set['baseline_env'],
        'bmi_env': task_set['bmi_env'],
        'save_path': Path(f"{exp_info['folder']}/{exp_info['animal']}/{exp_info['date']}/{exp_info['day']}"),
        'test_data': np.load(exp_info['test_data'])
    }
    path_data['save_path'].mkdir(parents=True, exist_ok=True)
    print('\nData Paths:\n', path_data, '\n')

    '''
        ROI Acquisition
    '''
    roi_info = roi_acqnvs_3i(task_set, path_data, 0,True, True)

    '''
        Baseline Acquisition
    '''
    roi_data = roi_info['roi_data'].item()
    # for each frame, the roi mean will be within a numpy array index
    # there will be n (number of ROIs) arrays, within each array
    bdata = baseline_acqnvs_3i(task_set, path_data, roi_data['roi_mask'], 0, True, False)

    plot_neurons_baseline(bdata, None, None, np.max(roi_data['num_rois']))
    # Choose out of the neurons found
    e1_base = sorted([16, 30])
    e2_base = sorted([10, 25])
    plot_neurons_ensemble(bdata, e1_base + e2_base, [1] * len(e1_base) + [2] * len(e2_base))
    select_roi_data(roi_data, list(set(e2_base) | set(e1_base)))

    baseline_frame_rate = np.sum(~np.isnan(bdata[0, :])) / task_set['im']['frame_rate'] # num_base_samples / fr
    sec_per_reward_range = np.array([120, 90])
    frames_per_reward_range = sec_per_reward_range * baseline_frame_rate
    print('Time (s) per reward range:')
    print(sec_per_reward_range)
    print('Frames per reward range:')
    print(frames_per_reward_range)
    print('Reward per frame range:')
    print(1. / frames_per_reward_range)

    # Ensure sec_per_reward_range is greater than 80 seconds
    if np.any(sec_per_reward_range <= 80):
        raise ValueError("sec_per_reward_range must be higher than 80 seconds to keep the occurrence of artificial vs natural higher than 80%")

    target_info, target_cal_all, fb_cal = baseline2target(bdata, roi_data, e1_base, e2_base, frames_per_reward_range, task_set, path_data['save_path'], fb_set, False)

    vector_stim, isi = get_random_stim(task_set['im']['frame_rate'], task_set['bmi_len'] * task_set['im']['frame_rate'], task_set['rs']['ihsi_mean'], task_set['rs']['ihsi_range'], False)

    '''
        BMI Acquisition
    '''
    # Test Feedback (FB)
    if fb_set['fb_bool']:
        print('Testing Feedback...')
        play_tone(7000, 1)

    # Close all plots and display the background image
    plt.close('all')
    plt.figure()
    plt.imshow(roi_info['plot_images'][1]['im'])
    plt.title(roi_info['plot_images'][1]['label'])
    plt.show()

    # Define the type of experiment and run the BMI acquisition
    bmi_data = bmi_acqnvs_3i(task_set, path_data, 0, exp_info['expt'], target_info, vector_stim + task_set['f0_win'],
                             0, [], np.ones(len(e1_base) + len(e2_base)) * np.nan, fb_set['fb_bool'], fb_cal, False, True)

    # If motor behavior experiment, run this
    check_motor_behavior(task_set, path_data, 0, exp_info['expt'], False, False)