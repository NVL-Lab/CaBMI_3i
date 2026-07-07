__author__= 'Saul Gurgua Lopez'

import numpy as np
import matplotlib.pyplot as plt
import socket
import serial
import time

from params.play_tone import play_tone
from slidebook.SBAccess import *

from roi_acqnvs_3i import get_roi_bg, get_roi_data, get_roi_bg_sbaccess
from params.define_exp_path import get_exp_info
from params.define_bmi_task_settings import get_bmi_settings
from params.define_fb_audio_settings import get_fb_settings

from baseline_acqnvs_3i import baseline_acqnvs_3i
from plots.plot_neurons_baseline import plot_neurons_baseline
from plots.plot_neurons_ensemble import plot_neurons_ensemble
from rois.select_roi_data import get_neuron_ensemble, select_roi_data
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

def main():
    # Acquire experiment settings
    exp_info = get_exp_info()
    task_set = get_bmi_settings(save=True)
    fb_set = get_fb_settings()
    # Check if arduino is available, else return none maybe
    #a = serial.Serial(fb_set['arduino']['com'], fb_set['arduino']['baudrate'])

    # Storing path and environment data
    path_data = {
        'save_path': Path(f"{exp_info['save_base_dir']}/{exp_info['date']}/{exp_info['animal']}/{exp_info['day']}").expanduser().resolve(),
    }
    path_data['sldy_path'] = path_data['save_path'] / 'slidebook'

    if task_set['save']:
        path_data['sldy_path'].mkdir(parents=True, exist_ok=True)
    print('\nData Paths:\n', path_data, '\n')

    # Should create new slides per different day of experiment per mouse
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((task_set['HOST'], task_set['PORT']))
    sb_access = SBAccess(s)
    slide_id = sb_access.CreateNewSlide() # Always 1
    sb_access.SetTargetSlide(slide_id)
    sb_access.SaveAsSlide(slide_id, str(path_data['sldy_path'] / exp_info['sldy_name'])) # access denied folder already exists

    '''
        ROI Acquisition: roi_acqnvs_3i
            Capture the image and input the capture index
    '''
    cont = input("Acquire ROI background image? [Y/y] ")
    if cont == "" or cont.lower() == "y":
        print("Acquiring ROI background image...")
    else:
        print("Stopping...")
        exit(0)

    roi_bg, task_set = get_roi_bg_sbaccess(task_set, path_data, sb_access)
    s.close()
    # Should pass the recording to suite2p rather than creating a mean
    roi_info = get_roi_data(roi_bg, path_data, task_set, True)
    exit()

    cont = input("Acquire Baseline? [Y/y] ")
    if cont == "" or cont.lower() == "y":
        print("Acquiring Baseline...")
    else:
        print("Stopping...")
        exit(0)
    '''
        Baseline Acquisition: baseline_acqnvs_3i
    '''
    if isinstance(roi_info, np.lib.npyio.NpzFile):
        roi_data = roi_info['roi_data'].item()
    else:
        roi_data = roi_info['roi_data']

    neuron_max = roi_data['num_rois']
    base_activity, task_set = baseline_acqnvs_3i(task_set, path_data, roi_data['roi_mask'])

    cont = input("Gather ROI info for BMI? [Y/y] ")
    if cont == "" or cont.lower() == "y":
        print("Plotting neurons...")
    else:
        print("Stopping...")
        exit(0)
    '''
        Ensemble neuron data
    '''
    neuron_ensembles = []
    while True:
        if not task_set['expt']['calib']['load']:
            plot_neurons_baseline(base_activity, None, None, neuron_max)

            for count in range(task_set['cb']['ensemble_count']):
                print(f"Selecting neuron ensemble {count+1}")
                ensemble = get_neuron_ensemble(neuron_max, task_set['cb']['neurons_per_ensemble'])

                if any(set(ensemble) & set(existing) for existing in neuron_ensembles):
                    print("This ensemble shares neurons with a previous one. Try again.")
                    neuron_ensembles = []
                    continue
                else:
                    neuron_ensembles.append(ensemble)

            if not neuron_ensembles:
                continue

            plot_neurons_ensemble(base_activity, neuron_ensembles[0] + neuron_ensembles[1], [1] * len(neuron_ensembles[0]) + [2] * len(neuron_ensembles[1]))
            select_roi_data(roi_data, list(set(neuron_ensembles[0]) | set(neuron_ensembles[1])))

            baseline_frame_rate = np.sum(~np.isnan(base_activity[0, :])) / task_set['cb']['baseline_len']  # task_set['im']['frame_rate']
            sec_per_reward_range = np.array(task_set['cb']['sec_per_reward_range'])
            frames_per_reward_range = sec_per_reward_range * baseline_frame_rate
            print('Time (s) per reward range:')
            print(sec_per_reward_range)
            print('Frames per reward range:')
            print(frames_per_reward_range)
            print('Reward per frame range:')
            print(1. / frames_per_reward_range)

        target_info, target_cal_all, fb_cal, strc_info = baseline2target(base_activity, roi_data, neuron_ensembles[0], neuron_ensembles[1],
                                                                         frames_per_reward_range, task_set,
                                                                         path_data['save_path'], fb_set)
        cont = input("Are ROIs good for BMI? [Y/y] ")
        if cont == "" or cont.lower() == "y":
            print("Continuing...")
        else:
            print("Repeating...")
            neuron_ensembles = []
            continue

    if isinstance(strc_info, np.lib.npyio.NpzFile):
        strc_mask = strc_info['strc_mask'].item()
    else:
        strc_mask = strc_info['strc_mask']

    vector_stim, isi = get_random_stim(task_set['im']['frame_rate'], task_set['bmi_len']*task_set['im']['frame_rate'], task_set['rs']['ihsi_mean'], task_set['rs']['ihsi_range'], False)

    seed_base = False
    if not seed_base:
        vector_stim += task_set['f0_win']

    cont = input("Acquire BMI? [Y/y]")
    if cont == "" or cont.lower() == "y":
        print("Acquiring BMI...")
    else:
        print("Stopping...")
        exit(0)
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

    base_val_seed = np.ones(len(neuron_ensembles[0]) + len(neuron_ensembles[1])) * np.nan
    bmi_data = bmi_acqnvs_3i(task_set, path_data, exp_info['expt'], target_info, vector_stim,
                             0, [], fb_set['fb_bool'], fb_cal, strc_mask, a, base_val_seed)

    if motor_run:
        check_motor_behavior(task_set, path_data, 3, exp_info['expt'], False, False)

if __name__ == "__main__":
    main()