from datetime import datetime
from contextlib import contextmanager
import numpy as np
from scipy.io import loadmat
import time
import nidaqmx # may be for s = nidaqmx.Task()

import save_files_3i
from rois.obtain_roi import get_roi
from calibration.dff2cursor_target import dff2cursor_target
from calibration.cursor2audio import cursor2audio
from expt2bmi_flags import get_flags

@contextmanager
def on_cleanup(save_path, bData, debug_bool):
    try:
        yield
    finally:
        # The following is the clean_me_up():
        global pl, baseActivity
        print('cleaning')
        # Should be equivalent to the mat files but in npz format (multiple arrays)
        np.savez(f'{save_path}/BMI_online{datetime.now().strftime("%y%m%dT%H%M%S")}.npz', data=data, bData=bData)
        if not debug_bool:
            if pl.Connected():
                pl.Disconnect()

def bmi_acqnvs_3i(path_data, expt_str, baseline_calib_file, tset, vector_stim, debug_bool, debug_input, base_val_seed, fb_bool, fb_cal, a) -> None:
    # Load flag configuration file
    flags = get_flags()[expt_str]
    flag_bmi = flags['BMI_stim']
    flag_dr_stim = flags['DRstim']
    flag_stim_random = flags['StimRandom']
    flag_water = flags['Water']

    '''
    tset = define_BMI_task_settings();
    fbset = define_fb_audio_settings();
    a = arduino(fbset.arduino.com, fbset.arduino.label);
    '''

    '''
    Path to save information
    Lines 29-68
    '''

    # Connect to i3 Application
    '''
    Lines 88 - 116 
    Get image

    Lines 117 - 217
    Get ROIs
    '''

    # BMI parameters 
    tset['im']['frame_rate'] = 30
    relaxation_time = 0

    experiment_length = 60*30*tset['im']['frame_rate']
    relaxation_frames = round(relaxation_time*tset['im']['frame_rate'])
    
    #bdata = load(fullfile(baseline_calib_file)) - assuming this is a mat file
    bdata = loadmat(baseline_calib_file)
    back2base = 1/2*bdata['t1'];

    global pl, data

    number_neurons = len(bdata['E_id'])

    # Pre-allocating arrays
    fbuffer = np.full((number_neurons, tset['dff_win']), np.nan, dtype=np.float32)

    data = {}
    expected_length_experiment = int(np.ceil(experiment_length))

    data['cursor'] = np.full(experiment_length, np.nan, dtype=np.float32)
    data['fb_freq'] = np.full(experiment_length, np.nan, dtype=np.float32)
    data['bmi_act'] = np.full((number_neurons, experiment_length), np.nan, dtype=np.float32)
    data['base_vector'] = np.full((number_neurons, experiment_length), np.nan, dtype=np.float32)
    data['self_hits'] = np.zeros(experiment_length, dtype=np.float32)
    data['self_dr_stim'] = np.zeros(experiment_length, dtype=np.float32)
    data['vector_stim'] = vector_stim
    data['vector_water'] = np.zeros(experiment_length, dtype=np.float32)
    data['random_dr_stim'] = np.zeros(experiment_length, dtype=np.float32)
    data['trial_start'] = np.zeros(experiment_length, dtype=np.float32)
    # To debug, TODO: Remove after debugging
    data['time_vector'] = np.full(experiment_length, np.nan, dtype=np.float32)

    if debug_bool:
        data['fsmooth'] = np.full((number_neurons, experiment_length), np.nan, dtype=np.float32)
        data['dff'] = np.full((number_neurons, experiment_length), np.nan, dtype=np.float32)
        data['c1_bool'] = np.full(experiment_length, np.nan, dtype=np.float32)
        data['c2_val'] = np.full(experiment_length, np.nan, dtype=np.float32)
        data['c2_bool'] = np.full(experiment_length, np.nan, dtype=np.float32)
        data['c3_val'] = np.full(experiment_length, np.nan, dtype=np.float32)
        data['c3_bool'] = np.full(experiment_length, np.nan, dtype=np.float32)

    # Initializing general flags and counters
    data['self_target_counter'] = 0
    data['self_target_dr_stim_counter'] = 0
    data['sched_random_stim'] = 0
    data['water_counter'] = 0

    data['trial_counter'] = 0  # TODO: Remove one
    trial_flag = 1
    non_buffer_update_counter = tset['prefix_win']  # Counter when we don't want to update the buffer
    init_frame_base = non_buffer_update_counter + 1
    # Beginning of experiment and VTA stim
    buffer_update_counter = 0

    deliver_water = 0
    deliver_stim = 0

    back2base_counter = 0
    back2baseline_flag = 0

    # Cleaning 
    with on_cleanup(path_data['save_path'], bdata, debug_bool):
        if not debug_bool:
            # Clear the previous session if it exists
            try:
                s.close()
            except:
                pass

            s = nidaqmx.Task()  # Create a new DAQmx task
            s.do_channels.add_do_chan('Dev6/port0/line0:2', line_grouping=LineGrouping.CHAN_PER_LINE)

            ni_out = [0, 0, 0]
            s.write(ni_out)  # Set the initial state
            ni_getimage = [0, 1, 0]

        # Prepare for 3i
        if not debug_bool:
            # The following connection to 3i might not exist
            # Connection to Prairie
            pl = win32com.client.Dispatch('PrairieLink.Application')
            pl.Connect()
            time.sleep(2)  # Pause is needed to give time to Prairie to connect

            # Prairie variables
            px = pl.PixelsPerLine()
            py = pl.LinesPerFrame()

            # Prairie commands
            pl.SendScriptCommands('-srd True 0')
            pl.SendScriptCommands('-lbs True 0')

            # Set the environment for the Time Series in PrairieView
            load_command = f'-tsl {path_data["bmi_env"]}'
            pl.SendScriptCommands(load_command)

            # Set the path where to store the imaging data - SetSavePath (-p) "path" ["addDateTime"]
            save_files_3i(path_data["save_path"], pl, expt_str)
        else:
            px = 512
            py = 512

        last_frame = np.zeros((px, py))

        # Load masks
        if not debug_bool:
            strc_mask = np.load(f'{path_data["save_path"]}/strc_mask.npy', allow_pickle=True).item()

        if not debug_bool:
            time.sleep(2)
            pl.SendScriptCommands('-ts')
            time.sleep(2)  # Empirically discovered time for the Prairie to start gears

        data["frame"] = 1

        # Give random reward to trigger the jetball
        a.write_digital("D9", 1)
        time.sleep(1)
        a.write_digital("D9", 0)

        print('STARTING RECORDING!!!')

        counter_same = 0  # Counts how many frames are the same as the past
        counter_same_thresh = 500
        base_buffer_full = False  # Boolean indicating if the fbuffer is filled

        print('baseBuffer filling!...')
        while (not debug_bool and counter_same < counter_same_thresh) or (debug_bool and data['frame'] <= debug_input.shape[1]):
            if not debug_bool:
                im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
            else:
                im = np.zeros((px, py))

            if not np.array_equal(im, last_frame) or debug_bool:
                start_time = time.time()  # Start timing to see the length of an iteration
                if not debug_bool:
                    last_frame = im  # Comparison and assignment takes ~4ms
                    s.write(ni_getimage)
                    time.sleep(0.001)
                    s.write([0, 0, 0])

                if non_buffer_update_counter == 0:
                    if not debug_bool:
                        unit_vals = get_roi(im, strc_mask)  # Function to obtain Rois values
                    else:
                        unit_vals = debug_input[:, data['frame']]
                    data['bmi_act'][:, data['frame']] = unit_vals

                    fbuffer[:, :-1] = fbuffer[:, 1:]
                    fbuffer[:, -1] = unit_vals

                    if data['frame'] == init_frame_base:
                        if not np.isnan(np.sum(base_val_seed)):
                            base_buffer_full = True
                            base_val = base_val_seed
                            print('baseBuffer seeded!')
                        else:
                            base_val = np.ones(number_neurons, dtype=np.float32) * unit_vals / tset['f0_win']
                    elif not base_buffer_full and data['frame'] <= (init_frame_base + tset['f0_win']):
                        base_val += unit_vals / tset['f0_win']
                        if data['frame'] == (init_frame_base + tset['f0_win']):
                            base_buffer_full = True
                            print('baseBuffer FULL!')
                    else:
                        base_val = (base_val * (tset['f0_win'] - 1) + unit_vals) / tset['f0_win']

                    data['base_vector'][:, data['frame']] = base_val

                    fs_mooth = np.nanmean(fbuffer, axis=1, dtype=np.float32)

                    if debug_bool:
                        data['fsmooth'][:, data['frame']] = fs_mooth

                    if base_buffer_full:
                        dff = (fs_mooth - base_val) / base_val
                        cursor_i, target_hit, c1_bool, c2_val, c2_bool, c3_val, c3_bool = dff2cursor_target(
                            dff, bdata, tset['cursor_zscore_bool'])
                        print(f'Cursor: {cursor_i}')
                        data['cursor'][data['frame']] = cursor_i

                        if debug_bool:
                            data['dff'][:, data['frame']] = dff
                            data['c1_bool'][data['frame']] = c1_bool
                            data['c2_val'][data['frame']] = c2_val
                            data['c2_bool'][data['frame']] = c2_bool
                            data['c3_val'][data['frame']] = c3_val
                            data['c3_bool'][data['frame']] = c3_bool

                        fb_freq_i = cursor2audio(cursor_i, fb_cal)
                        data['fb_freq'][data['frame']] = fb_freq_i

                        if fb_bool and not debug_bool:
                            # This will be from the computer
                            playTone(a, fb_cal['settings']['arduino']['pin'], fb_freq_i, fb_cal['settings']['arduino']['duration'])

                        if buffer_update_counter == 0 and base_buffer_full:
                            if trial_flag and not back2baseline_flag:
                                data['trialStart'][data['frame']] = 1
                                data['trialCounter'] += 1
                                trial_flag = False
                                print('New Trial!')

                            if back2baseline_flag:
                                if data['cursor'][data['frame']] <= back2base:
                                    back2base_counter += 1
                                if back2base_counter >= tset['back2base_frame_thresh']:
                                    back2baseline_flag = False
                                    back2base_counter = 0
                                    print('back to baseline')
                            else:
                                if target_hit:
                                    print('target hit')
                                    data['self_target_counter'] += 1
                                    data['self_hits'][data['frame']] = 1
                                    print(f'Trial: {data["trial_counter"]}, Num Self Hits: {data["self_target_counter"]}')

                                    if flag_bmi:
                                        if flag_dr_stim:
                                            deliver_stim = 1
                                            data['self_target_dr_stim_counter'] += 1
                                            data['self_dr_stim'][data['frame']] = 1
                                            print(f'Trial: {data["trial_counter"]}, DR STIMS: {data["self_target_dr_stim_counter"]}')
                                        if flag_water:
                                            deliver_water = 1
                                            data['water_counter'] += 1
                                            data['vector_water'][data['frame']] = 1
                                            print(f'Trial: {data["trial_counter"]}, Water: {data["water_counter"]}')

                                        print('Target Achieved! (self-target)')

                                        if not debug_bool:
                                            print('RewardTone delivery!')
                                        buffer_update_counter = relaxation_frames
                                        back2baseline_flag = True
                                        trial_flag = True
                                if not trial_flag and flag_stim_random:
                                    if data['frame'] in data['vector_stim']:
                                        deliver_stim = 1
                                        print('SCHEDULED DR STIM')
                                        data['sched_random_stim'] += 1
                                        data['random_dr_stim'][data['frame']] = 1
                        else:
                            if buffer_update_counter > 0:
                                buffer_update_counter -= 1
                    else:
                        if non_buffer_update_counter > 0:
                            non_buffer_update_counter -= 1

                    if deliver_water:
                        if not debug_bool:
                            a.write_digital("D9", 1)
                            time.sleep(1)
                            a.write_digital("D9", 0)
                        deliver_water = 0
                        print('water delivered!')

                    if deliver_stim:
                        if tset['delay_flag']:
                            time.sleep(tset['delay_time'])
                        if not debug_bool:
                            a.write_digital("D5", 1)
                            time.sleep(0.2)
                            a.write_digital("D5", 0)
                            a.write_digital("D3", 1)
                            time.sleep(1)
                            a.write_digital("D3", 0)
                        deliver_stim = 0
                        print('stim delivered!')

                    data['frame'] += 1
                    data['time_vector'][data['frame']] = time.time() - start_time
                    counter_same = 0

                    if not debug_bool and data['time_vector'][data['frame']] < 1 / (tset['im']['frame_rate'] * 1.2):
                        time.sleep(1 / (tset['im']['frame_rate'] * 1.2) - data['time_vector'][data['frame']])
                else:
                    counter_same += 1

def clean_me_up(save_path, b_data, debug_bool, pl, data):
    """
    Cleans up the environment, saves necessary data, and disconnects the PrairieLink connection if needed.

    Parameters:
    save_path (str): The path where the data should be saved.
    b_data (dict): The bData to be saved.
    debug_bool (bool): Whether the script is running in debug mode.
    pl (object): The PrairieLink object for managing the connection.
    data (dict): The data to be saved.
    """
    print('cleaning')

    # Saving the global variables
    now_str = datetime.datetime.now().strftime('%y%m%dT%H%M%S')
    save_filename = f'{save_path}/BMI_online_{now_str}.mat'
    
    # Save the data using scipy.io.savemat
    # May want to not do this anymore
    savemat(save_filename, {'data': data, 'bData': b_data})
    
    if not debug_bool:
        if pl.Connected():
            pl.Disconnect()
