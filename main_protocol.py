author_= 'Saul Gurgua Lopez'

import sys
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.ndimage import label
#import suite2p

#from scipy.io import savemat #maybe change to save numpy
#from scipy.io import loadmat

from params.define_exp_path import get_exp_info
from params.define_bmi_task_settings import get_bmi_settings
from params.define_fb_audio_settings import get_fb_settings
from SBReadFile22.SBReadFile import *
from rois.scale_im_interactive import scale_im_interactive
from segmentation.im_find_cells_tm import im_find_cells_tm
from rois.get_center import get_center
from rois.label_mask2roi_data_single_channel import label_mask2roi_data_single_channel
from rois.delete_roi_2chan import delete_roi_2chan
from rois.draw_roi_g_chan import draw_roi_g_chan
from baseline_acqnvs_3i import baseline_acqnvs_3i



#from plots.plot_neurons_baseline import plot_neurons_baseline
#from plots.plot_neurons_ensemble import plot_neurons_ensemble
#from rois.select_roi_data import select_roi_data
#from calibration.baseline2target import baseline2target
#from params.create_vector_random_stim import get_random_stim

#import bmi_acqnvs_3i

#/Users/saulglopez/Library/CloudStorage/OneDrive-UAB-TheUniversityofAlabamaatBirmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.sldy

if __name__ == '__main__':
    sldy_dir = sys.argv[1] # Do not convert dir to a Path object -> error with 3i code
    exp_info = get_exp_info()
    save_path = Path(f"{exp_info['folder']}/{exp_info['animal']}/{exp_info['date']}/{exp_info['day']}")
    #save_path.mkdir(parents=True, exist_ok=True)

    fb_set = get_fb_settings()
    task_set = get_bmi_settings()
    path_data = {
        'baseline_env': task_set['baseline_env'],
        'bmi_env': task_set['bmi_env'],
        'save_path': save_path,
        'im': save_path / 'im'
    }
    print(path_data)

    SBFileReader = SBReadFile()
    if not SBFileReader.Open(sldy_dir):
        print('.sldy file not found')
        exit(1)

    '''
    print(SBFileReader.GetNumCaptures())
    print(SBFileReader.GetNumXColumns(0))
    print(SBFileReader.GetNumYRows(0))
    print(SBFileReader.GetNumChannels(0))
    print(SBFileReader.GetChannelName(0,1))
    print(SBFileReader.GetAuxSerializedData(0,0,0))
    '''

    # Get first image to obtain rois
    im_summary = SBFileReader.ReadImagePlaneBuf(0,0,0,0,0,True)

    # Scale image to see ROIs better
    '''
        Why save them all?
        num_im_sc will not be used
        only necessary paramater is im_summary
    '''
    print('Image Scaling')
    print('----------------------------------------')
    im_sc_struct, _ = scale_im_interactive(im_summary, [],0)
    im_bg = im_sc_struct[-1]['im']
    plt.figure()
    plt.imshow(im_bg, cmap='bone', vmin=0, vmax=4 * np.nanmean(im_bg)) # why the nanmean
    plt.title('Background for tseROI Identification')
    plt.show()
    print('----------------------------------------')

    # PLOT_IMAGES data
    # 'plot_images' contains a set of images so user can tell if ROI selection is appropriate
    plot_images = [{'im': None, 'label': ''} for _ in range(2)]
    plot_images[0]['im'] = im_summary # check if it's the same as im_bg
    plot_images[0]['label'] = 'green mean'
    plot_images[1]['im'] = im_bg
    plot_images[1]['label'] = 'scaled'

    # we may want 10 hits per 5 min (every 60 to 90 sec)
    # show more of a range of hits for cursor
    # A T = 0.3 or 0.4 (OR 3 or 4) (we want 0.5 to 1) might be noise so we wouldn't want that
    # Want a Gaussian distribtuion of T, if not a bit flatter overall
    # Calibration may be wrong if no hits happen in the first 5 min
    print('Cell Identification')
    print('----------------------------------------')
    mask_intermediate, _ = im_find_cells_tm(im_bg, task_set['roi']['template_diam'],task_set['roi']['thres'], task_set['roi']['cell_diam'], task_set['roi']['finemode'], task_set['roi']['temmode'] )
    init_roi_mask = label(mask_intermediate)
    x_center, y_center = get_center(init_roi_mask[0], im_bg, True)
    roi_data = label_mask2roi_data_single_channel(im_bg, init_roi_mask[0], task_set['im']['chan_data'])

    '''
    print('Detecting Cells')
    ops, stat = suite2p.detection_wrapper(f_reg=im_bg, ops=suite2p.default_ops(), classfile=suite2p.classification.builtin_classfile) # im_bg must be npy file
    iscell = suite2p.detection.classify(stat, suite2p.classification.builtin_classfile )
    roi_mask = np.zeros((ops['Ly'], ops['Lx']), dtype=np.uint32)
    cell_count = 0
    for i, roi in enumerate(stat):
        if iscell[i]:
            cell_count += 1
            roi_mask[roi['ypix'], roi['xpix']] = cell_count * roi['lam']
    print(f"{cell_count} cells detected.")
    plt.figure()
    plt.imshow(roi_mask, cmap='nipy_spectral')
    plt.title("ROI Neurons")
    plt.colorbar(label="Label index")
    plt.show()
    roi_data = label_mask2roi_data_single_channel(im_bg, roi_mask[0], task_set['im']['chan_data'])
    '''

    # Visualize
    plt.figure()
    plt.imshow(roi_data['im_roi'], cmap='bone', vmin=0, vmax=1)
    plt.title('ROI footprint overlay in blue')
    plt.show()

    plt.figure()
    plt.imshow(roi_data['roi_mask'], cmap='bone', vmin=0, vmax=1)
    plt.title('ROI Mask')
    plt.show()
    print('----------------------------------------')

    # Delete ROI if needed
    print('Deleting ROIs from image!')
    roi_data = delete_roi_2chan(plot_images, roi_data)
    plt.close('all')

    # Add ROI if needed
    '''
    print('Adding ROIs to image!')
    roi_data = draw_roi_g_chan(plot_images, roi_data)
    plt.close('all')
    '''

    # See ROI if needed
    see_roi_data_flag = True
    if see_roi_data_flag:
        #screen_size = plt.get_current_fig_manager().window.wm_maxsize()
        #fig1 = plt.figure(figsize=(screen_size[0]/200, screen_size[1]/200))
        plt.figure()
        plt.imshow(roi_data['roi_mask'], cmap='gray')
        plt.title(f'roi_mask num roi: {roi_data["num_rois"]}')
        plt.show()

        #fig2 = plt.figure(figsize=(screen_size[0]/200, screen_size[1]/200))
        plt.figure()
        plt.imshow(roi_data['im_roi'], cmap='gray')
        plt.title(f'ROI footprint overlay in blue. Num ROI: {roi_data["num_rois"]}')
        plt.show()

    # Save roi_data
    '''
    roi_data_file = os.path.join(save_path, 'roi_data.mat')
    savemat(roi_data_file, {'plot_images': plot_images, 'roi_data': roi_data})
    '''
    # Baseline acquisition
    # remove a and fb_set.arduino.pin)
    base_mat_path = baseline_acqnvs_3i(path_data, roi_data['roi_mask'], task_set, a, fb_set.arduino.pin)
    #base_mat = loadmat(base_mat_path)[0][0];
    exit()

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

    target_info_path, target_cal_all_path, fb_cal = baseline2target(n_f_file, roi_data_file, e1_base, e2_base, frames_per_reward_range, task_set, save_path, fb_set)

    # Define the experiment length based on frame rate
    experiment_length = 30 * 60 * task_set['im']['frame_rate']

    # Generate vector_stim and ISI
    vector_stim, isi = get_random_stim(task_set['im']['frameRate'], experiment_length, task_set['rs']['IHSImean'], task_set['rs']['IHSIrange'], False)

    # Set the seed for baseline
    seedBase = 0
    if not seedBase:
        vector_stim += task_set.f0_win

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
        # This will be implemented from computer
        #playTone(a, fbset['arduino']['pin'], fb_freq_i, fbset['arduino']['duration']) # This will be changed and will use the MiceBall/RATBALL code, which has tone code

    # Set up base_val_seed for the BMI experiment
    base_val_seed = np.ones(len(e1_base) + len(e2_base)) * np.nan

    # Close all plots and display the background image
    plt.close('all')
    plt.imshow(im_bg)

    # Define the type of experiment and run the BMI acquisition
    bmi_acqnvs_3i(path_data, expt_str, target_info_path, task_set, vector_stim, 0, [], base_val_seed, fb_set['fb_bool'], fb_cal, a)

    # D0:
    # 1) Save the workspace in folder
    # 2) Save this protocol script in the folder (savePath)

    # If motor behavior experiment, run this
    #STOPPED HERE
    check_motor_behavior(a, path_data, task_set, expt_str, fb_set['arduino']['pin'])
