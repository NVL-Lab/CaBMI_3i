author_= 'Saul Gurgua Lopez'

import os
from pathlib import Path
import numpy as np
from scipy.io import savemat #maybe change to save numpy
from scipy.ndimage import label
import matplotlib.pyplot as plt
from scipy.io import loadmat
#from pyfirmata import Arduino, util

from save_path import get_exp_info
from params.define_bmi_task_settings import get_bmi_settings
from params.define_fb_audio_settings import get_fb_settings
from segmentation.im_find_cells_tm import im_find_cells_tm
from rois.get_center import get_center
from rois.label_mask2roi_data_single_channel import label_mask2roi_data_single_channel
from rois.delete_roi_2chan import delete_roi_2chan
from rois.draw_roi_g_chan import draw_roi_g_chan
from baseline_acqnvs_3i import baseline_acqnvs_3i
from plots.plot_neurons_baseline import plot_neurons_baseline
from plots.plot_neurons_ensemble import plot_neurons_ensemble
from rois.select_roi_data import select_roi_data
from calibration.baseline2target import baseline2target

# Line 373 to get the BMIAcqn function    
if __name__ == '__main__':
    path_data = {}

    tset = get_bmi_settings()
    fbset = get_fb_settings()

    # board = Arduino('COM3')
    # How will audio be heard?

    exp_info = get_exp_info()
    save_path = Path(f"{exp_info['folder']}/{exp_info['animal']}/{exp_info['date']}/{exp_info['day']}")
    if save_path.exists():
        print(f'{save_path} exists.')
    else:
        print(f'{save_path} does not exist.')

    path_data['baseline_env'] = tset['baseline_env']
    path_data['bmi_env'] = tset['bmi_env']
    path_data['save_path'] = save_path
    path_data['im'] = save_path / 'im'
    print(path_data)

    # Get pixel values from 3i
    """
    pl = actxserver('PrairieLink.Application');
    pl.Connect(); 
    disp('Connecting to prairie...');
    """

    # Prairie variables
    """
    px = pl.PixelsPerLine(); % px = 512;
    py = pl.LinesPerFrame(); % py = 512;
    micronsPerPixel.x = str2double(pl.GetState('micronsPerPixel', 'XAxis')); 
    micronsPerPixel.y = str2double(pl.GetState('micronsPerPixel', 'YAxis')); 
    pl.Disconnect();
    disp('Disconnected from prairie');
    """

    chan_num = len(tset['im']['chan_data'])

    # May not be necessary
    # Get first image to obtain rois
    """
    pl = actxserver('PrairieLink.Application');
    pl.Connect();
    disp('Connecting to prairie')
    pause(2);    
    ** im_summary  = pl.GetImage_2(2, px, py); #2 is a channel
    pl.Disconnect();
    """

    # Scale image to see ROIs better
    """
    im_scale_ops = {'im': [],
                    'minmax_perc': [],
                    'minmax': [],
                    'min': [],
                    'min_perc': [],
                    'max': [],
                    'max_perc': []}
    im_scale_info = scale_im_interactive(im_summary, im_scale_ops ,0)
    """

    # Each channel is green and red
    # im_bg is roi_data file    

    # ROI Visualization
    '''
    im_bg = im_sc_struct(end).im;
    h = figure;
    imagesc(im_bg), colormap bone, caxis([-0 nanmean(nanmean(im_bg(:)))*4])
    axis square
    title('selected background image for identifying tseROI');
    plot_images = struct('im', [], 'label', '');
    plot_images(1).im = im_summary;
    plot_images(1).label = 'green mean';
    plot_images(2).im = im_bg;
    plot_images(2).label = 'scaled';
    '''

    mask_intermediate = im_find_cells_tm(im_bg, tset)
    init_roi_mask = label(mask_intermediate)
    get_center(init_roi_mask, im_bg)
    roi_data = label_mask2roi_data_single_channel(im_bg, init_roi_mask, tset.im.chan_data)    

    # Visualize
    # get() is from matlab and may be simulated in python with tkinter
    """
    screen_size = get(0,'ScreenSize');
    h = figure('Position', [screen_size(3)/2 1 screen_size(3)/2 screen_size(4)]);
    hold on;
    imagesc(roi_data.im_roi); %colormap('gray');  
    axis square;
    title('ROI footprint overlay in blue'); 
    % scatter(roi_data.x, roi_data.y, pi*roi_data.r.^2, 'r'); 

    %
    h = figure('Position', [screen_size(3)/2 1 screen_size(3)/2 screen_size(4)]);
    % hold on;
    imagesc(roi_data.roi_mask); %colormap('gray');  
    axis square;
    title('ROI Mask'); 
    % scatter(roi_data.x, roi_data.y, pi*roi_data.r.^2, 'r');
    """

    # Delete ROI if needed
    print('Deleting ROIs from image!')
    roi_data = delete_roi_2chan(plot_images, roi_data)
    plt.close('all')

    # Add ROI if needed
    print('Adding ROIs to image!')
    roi_data = draw_roi_g_chan(plot_images, roi_data)
    plt.close('all')

    # See ROI if needed
    see_roi_data_flag = True
    if see_roi_data_flag:
        screen_size = plt.get_current_fig_manager().window.wm_maxsize()
        fig1 = plt.figure(figsize=(screen_size[0]/200, screen_size[1]/200))
        plt.imshow(roi_data['roi_mask'], cmap='gray')
        plt.axis('square')
        plt.title(f'roi_mask num roi: {roi_data["num_rois"]}')
        plt.show()

        fig2 = plt.figure(figsize=(screen_size[0]/200, screen_size[1]/200))
        plt.imshow(roi_data['im_roi'], cmap='gray')
        plt.axis('square')
        plt.title(f'ROI footprint overlay in blue. Num ROI: {roi_data["num_rois"]}')
        plt.show()

    # Save roi_data
    roi_data_file = os.path.join(save_path, 'roi_data.mat')
    savemat(roi_data_file, {'plot_images': plot_images, 'roi_data': roi_data})

    # Baseline acquisition
    base_mat_path = baseline_acqnvs_3i(path_data, roi_data.roi_mask, tset, a, fbset.arduino.pin)
    base_mat = loadmat(base_mat_path)[0][0];

    # Plot neurons from baseline
    plot_neurons_baseline(base_mat['base_activity'], [], [], np.max(roi_data['num_rois']))
    e1_base = sorted([11, 12])
    e2_base = sorted([4, 13])

    ensemble_neurons = e1_base + e2_base
    plot_neurons_ensemble(base_mat['base_activity'], ensemble_neurons, [1] * len(e1_base) + [2] * len(e2_base))
    select_roi_data(roi_data, list(set(e2_base) | set(e1_base)))

    # Assumining this will be a loadmat type file
    # Check is base_mat exists (renamed from base_file) - logic matfile line 280
    n_f_file = base_mat_path;
    ndata = loadmat(base_mat_path)[0][0];
    num_base_samples = np.sum(~np.isnan(ndata['base_activity'][0, :]))
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

    target_info_path, target_cal_all_path, fb_cal = baseline2target(n_f_file, roi_data_file, e1_base, e2_base, frames_per_reward_range, tset, save_path, fbset)

    # Define the experiment length based on frame rate
    experiment_length = 30 * 60 * tset['im']['frame_rate']

    # Generate vector_stim and ISI
    #STOPPED HERE
    vector_stim, isi = get_random_stim(tset['im']['frameRate'], experiment_length, tset['rs']['IHSImean'], tset['rs']['IHSIrange'], False)

    # Set the seed for baseline
    seedBase = 0
    if not seedBase:
        vector_stim += tset.f0_win

    # Run BMI (Brain-Machine Interface) Experiment
    # --------------------------------------------------
    # DO!!!
    # Rename the file on the jetball computer!
    # Optionally load base_val_seed from previous BMI

    # Example of loading pretraining data
    pretrain_file = 'BMI_online190524T131817.npy'
    pretrain_data = np.load(os.path.join(savePath, pretrain_file), allow_pickle=True).item()

    # Handle pretrain_base and base_val_seed
    pretrain_base = pretrain_data['baseVector']
    pretrain_base = pretrain_base[:, ~np.isnan(pretrain_base[0, :])]
    base_val_seed = pretrain_base[:, -1] if pretrain_base.size > 0 else None

    # Test Feedback (FB)
    if fbset['fb_bool']:
        fb_freq_i = 7000
        fbset['arduino']['duration'] = 1
        playTone(a, fbset['arduino']['pin'], fb_freq_i, fbset['arduino']['duration']) # This will be changed and will use the MiceBall/RATBALL code, which has tone code

    # Set up base_val_seed for the BMI experiment
    base_val_seed = np.ones(len(e1_base) + len(e2_base)) * np.nan

    # Close all plots and display the background image
    plt.close('all')
    plt.imshow(im_bg)

    # Define the type of experiment and run the BMI acquisition
    bmi_acqnvs_3i(path_data, expt_str, target_info_path, tset, vector_stim, 0, [], base_val_seed, fbset['fb_bool'], fb_cal, a)

    # D0:
    # 1) Save the workspace in folder
    # 2) Save this protocol script in the folder (savePath)

    # If motor behavior experiment, run this
    check_motor_behavior(a, path_data, tset, expt_str, fbset['arduino']['pin'])
