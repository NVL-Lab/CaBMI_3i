__author__= 'Saul Gurgua Lopez'

import numpy as np
import matplotlib.pyplot as plt

from params.play_tone import play_tone

from roi_acqnvs_3i import get_roi_bg, get_roi_data
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

from simulation.load_mat_files import *

"""
    Performs data acquisition of calcium imaging through the use of a 3i microscope

    Requirements:
        Slidebook (3i software): for manually starting the recording and storing of npy image data
        Suite2p (Image processing software): for ROI detection
"""

if __name__ == '__main__':
    # Acquire experiment settings
    exp_types = ['sim', 'sim_mat', 'retrieve']
    exp_type = exp_types[1]
    exp_info = get_exp_info(exp_type=exp_type)
    task_set = get_bmi_settings(save=False, fr=29.752, res=(512, 512), rec='R PMT')
    fb_set = get_fb_settings()

    # Storing path and environment data
    path_data = {
        'sldy_path': Path(f"{exp_info['sldy_dir']}/{exp_info['sldy_name']}").expanduser().resolve(), # Make sure of existence before starting (w/ slidebook)
        'baseline_env': task_set['baseline_env'],
        'bmi_env': task_set['bmi_env'],
        'save_path': Path(f"{exp_info['save_base_dir']}/{exp_info['animal']}/{exp_info['date']}/{exp_info['day']}").expanduser().resolve(),
        'test_dir': Path(exp_info['recording_onedrive_mac_dir'])
    }
    if task_set['save']:
        path_data['save_path'].mkdir(parents=True, exist_ok=True)
    print('\nData Paths:\n', path_data, '\n')

    '''
        ROI Acquisition: roi_acqnvs_3i
            Capture the image and input the capture index
    '''
    if exp_type == 'sim_mat':
        #roi_bg, task_set = load_roi_bg(task_set, exp_info)
        #roi_info = get_roi_data(roi_bg, path_data, task_set, True, exp_type) # can't use base_activity as a result
        roi_info, task_set = load_roi_info(task_set, exp_info)
    else:
        roi_bg, task_set = get_roi_bg(task_set, path_data, exp_type)
        roi_info = get_roi_data(roi_bg, path_data, task_set, True, exp_type)

    '''
        Baseline Acquisition: baseline_acqnvs_3i
    '''
    if isinstance(roi_info, np.lib.npyio.NpzFile):
        roi_data = roi_info['roi_data'].item()
    else:
        roi_data = roi_info['roi_data']

    # for each frame, the roi mean will be within a numpy array index
    # there will be n (number of ROIs) arrays, within each array

    if exp_type == 'sim_mat':
        base_activity, task_set = load_base_activity(task_set, exp_info)
    else:
        base_activity, task_set = baseline_acqnvs_3i(task_set, path_data, roi_data['roi_mask'], exp_type)

    plot_neurons_baseline(base_activity, None, None, np.max(roi_data['num_rois']))
    # Choose out of the neurons found
    #e1_base = sorted([23, 15]) #sorted([16, 30])
    #e2_base = sorted([6, 40]) #sorted([10, 25])

    # subract 1 per roi
    # E1 [4, 10, 15, 20] => [14, 21, 22, 52] through suite2p
    # E2 [31, 33, 36, 37] => [20, 11, 26, 46] through suite2p

    e1_base = sorted(np.array([4, 10, 15, 20])-1)
    e2_base = sorted(np.array([31, 33, 36, 37])-1)

    #e1_base = sorted(np.array([14, 21, 22, 52])-1)
    #e2_base = sorted(np.array([20, 11, 26, 46])-1)

    plot_neurons_ensemble(base_activity, e1_base + e2_base, [1] * len(e1_base) + [2] * len(e2_base))
    select_roi_data(roi_data, list(set(e1_base) | set(e2_base)))

    baseline_frame_rate = np.sum(~np.isnan(base_activity[0, :])) / task_set['cb']['baseline_len'] #task_set['im']['frame_rate']
    sec_per_reward_range = np.array(task_set['cb']['sec_per_reward_range'])
    frames_per_reward_range = sec_per_reward_range * baseline_frame_rate
    print('Time (s) per reward range:')
    print(sec_per_reward_range)
    print('Frames per reward range:')
    print(frames_per_reward_range)
    print('Reward per frame range:')
    print(1. / frames_per_reward_range)

    # Ensure sec_per_reward_range is greater than 80 seconds
    #if np.any(sec_per_reward_range <= 80):
    #    raise ValueError("sec_per_reward_range must be higher than 80 seconds to keep the occurrence of artificial vs natural higher than 80%")

    # plot 13 not quite the same
    # Works now but may want to check on convolution (may just work on even windows)
    target_info, target_cal_all, fb_cal, strc_info = baseline2target(base_activity, roi_data, e1_base, e2_base, frames_per_reward_range, task_set, path_data['save_path'], fb_set, exp_type)

    # works, but what is the purpose?
    vector_stim, isi = get_random_stim(task_set['im']['frame_rate'], task_set['bmi_len']*task_set['im']['frame_rate'], task_set['rs']['ihsi_mean'], task_set['rs']['ihsi_range'], False)

    seed_base = False
    if not seed_base:
        vector_stim += task_set['f0_win']

    '''
        BMI Acquisition
    '''
    motor_run = False
    # Test Feedback (FB)
    if fb_set['fb_bool']:
        print('Testing Feedback...')
        play_tone(7000, 1)

    # Close all plots and display the background image
    plt.close('all')
    '''
    plt.figure()
    #plt.imshow(roi_info['plot_images'][1]['im'])
    #plt.title(roi_info['plot_images'][1]['label'])
    plt.imshow(roi_info['plot_images']['scaled'])
    plt.title('scaled')
    plt.show()
    '''

    base_val_seed = np.ones(len(e1_base) + len(e2_base)) * np.nan

    # Define the type of experiment and run the BMI acquisition
    bmi_data = bmi_acqnvs_3i(task_set, path_data, exp_info['expt'], target_info, vector_stim,
                             0, [], fb_set['fb_bool'], fb_cal, strc_info, base_val_seed, True, False, True)

    #print(bmi_data)
    #np.savez_compressed('/Users/saulglopez/Downloads/bmi_data.npz', **bmi_data)

    if motor_run:
        check_motor_behavior(task_set, path_data, 3, exp_info['expt'], False, False)