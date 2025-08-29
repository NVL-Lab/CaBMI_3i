from datetime import datetime
from contextlib import contextmanager
import numpy as np
import time

from save_files_3i import save_files_3i
from rois.obtain_roi import get_roi
from calibration.dff2cursor_target import dff2cursor_target
from calibration.cursor2audio import cursor2audio
from expt2bmi_flags import get_flags
from params.play_tone import play_tone

from SBReadFile22.SBReadFile import *

@contextmanager
def on_cleanup(save_path, data, bData):
    try:
        yield
    finally:
        print('Cleaning...')
        np.savez(save_path, data=data, bData=bData)

def allocate(shape, fill, dtype):
    if fill == "nan":
        return np.full(shape, np.nan, dtype=dtype)
    elif fill == "zero":
        return np.zeros(shape, dtype=dtype)
    else:
        raise ValueError(f"Unknown fill type: {fill}")

def init_data(expected_expt_length, number_neurons, vector_stim, debug_bool=False):
    data = {}
    # --- schema for arrays ---
    schema = {
        # name       : (shape, fill, dtype)
        "cursor"    : ((expected_expt_length,), "nan", np.float32),
        "fb_freq"   : ((expected_expt_length,), "nan", np.float32),
        "bmi_act"   : ((number_neurons, expected_expt_length), "nan", np.float32),
        "base_vector":((number_neurons, expected_expt_length), "nan", np.float32),
        "self_hits" : ((expected_expt_length,), "zero", np.float32),
        "self_dr_stim":((expected_expt_length,), "zero", np.float32),
        "vector_water":((expected_expt_length,), "zero", np.float32),
        "random_dr_stim":((expected_expt_length,), "zero", np.float32),
        "trial_start":((expected_expt_length,), "zero", np.float32),
        "time_vector":((expected_expt_length,), "nan", np.float32),  # debugging
    }
    # --- schema for debug arrays ---
    debug_schema = {
        "fsmooth"   : ((number_neurons, expected_expt_length), "nan", np.float32),
        "dff"       : ((number_neurons, expected_expt_length), "nan", np.float32),
        "c1_bool"   : ((expected_expt_length,), "nan", np.float32),
        "c2_val"    : ((expected_expt_length,), "nan", np.float32),
        "c2_bool"   : ((expected_expt_length,), "nan", np.float32),
        "c3_val"    : ((expected_expt_length,), "nan", np.float32),
        "c3_bool"   : ((expected_expt_length,), "nan", np.float32),
    }

    # fill main arrays
    for key, (shape, fill, dtype) in schema.items():
        data[key] = allocate(shape, fill, dtype)
    # fill debug arrays if enabled
    if debug_bool:
        for key, (shape, fill, dtype) in debug_schema.items():
            data[key] = allocate(shape, fill, dtype)

    # attach external vector
    data["vector_stim"] = vector_stim # To debug, TODO: Remove after debugging
    # counters and flags
    data.update({
        "self_target_counter": 0,
        "self_target_dr_stim_counter": 0,
        "sched_random_stim": 0,
        "water_counter": 0,
        "trial_counter": 0,  # TODO: Remove one
    })

    return data

def bmi_acqnvs_3i(sb_file_reader, capture, path_data, expt_str, baseline_calib_file, tset, vector_stim, debug_bool, debug_input, base_val_seed, fb_bool, fb_cal) -> None:
    # Load flag configuration file
    flags = get_flags()[expt_str]

    # BMI parameters
    tset['im']['frame_rate'] = 30
    relaxation_time = 0 # there can't be another hit in this many sec

    # Values of parameters in frames
    expected_expt_length = 60*30*tset['im']['frame_rate'] # in frames
    relaxation_frames = round(relaxation_time*tset['im']['frame_rate'])
    
    bdata = np.load(baseline_calib_file, allow_pickle=True)
    back2base = 1/2*bdata['t1']

    # ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** *
    # ** ** ** ** ** ** ** ** ** Initialization of BMI acquisition ** ** ** ** ** ** ** ** ** ** ** ** ** ** *
    # ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** *

    number_neurons = len(bdata['E_id'])

    # Pre-allocating arrays
    fbuffer = np.full((number_neurons, tset['dff_win']), np.nan, dtype=np.float32)
    data = init_data(expected_expt_length, number_neurons, vector_stim, debug_bool=True)

    '''
    data = {}
    data['cursor'] = np.full(expected_expt_length, np.nan, dtype=np.float32)
    data['fb_freq'] = np.full(expected_expt_length, np.nan, dtype=np.float32)
    data['bmi_act'] = np.full((number_neurons, expected_expt_length), np.nan, dtype=np.float32)
    data['base_vector'] = np.full((number_neurons, expected_expt_length), np.nan, dtype=np.float32)
    data['self_hits'] = np.zeros(expected_expt_length, dtype=np.float32)
    data['self_dr_stim'] = np.zeros(expected_expt_length, dtype=np.float32)
    data['vector_stim'] = vector_stim
    data['vector_water'] = np.zeros(expected_expt_length, dtype=np.float32)
    data['random_dr_stim'] = np.zeros(expected_expt_length, dtype=np.float32)
    data['trial_start'] = np.zeros(expected_expt_length, dtype=np.float32)
    # To debug, TODO: Remove after debugging
    data['time_vector'] = np.full(expected_expt_length, np.nan, dtype=np.float32)

    if debug_bool:
        data['fsmooth'] = np.full((number_neurons, expected_expt_length), np.nan, dtype=np.float32)
        data['dff'] = np.full((number_neurons, expected_expt_length), np.nan, dtype=np.float32)
        data['c1_bool'] = np.full(expected_expt_length, np.nan, dtype=np.float32)
        data['c2_val'] = np.full(expected_expt_length, np.nan, dtype=np.float32)
        data['c2_bool'] = np.full(expected_expt_length, np.nan, dtype=np.float32)
        data['c3_val'] = np.full(expected_expt_length, np.nan, dtype=np.float32)
        data['c3_bool'] = np.full(expected_expt_length, np.nan, dtype=np.float32)

    # Initializing general flags and counters
    data['self_target_counter'] = 0
    data['self_target_dr_stim_counter'] = 0
    data['sched_random_stim'] = 0
    data['water_counter'] = 0

    data['trial_counter'] = 0  # TODO: Remove one
    '''
    trial_flag = 1
    non_buffer_update_counter = tset['prefix_win']  # Counter when we don't want to update the buffer
    init_frame_base = non_buffer_update_counter + 1
    # Beginning of experiment and VTA stim
    buffer_update_counter = 0

    deliver_stim = 0  # Light stimulation
    deliver_water = 0 # Reward feedback

    back2base_counter = 0
    back2baseline_flag = 0

    # Save path
    bmi_data_path = path_data['save_path'] / f'BMI_online{datetime.now().strftime("%y%m%dT%H%M%S")}.npz'

    #counter_same = 0  # Counts how many frames are the same as the past
    #counter_same_thresh = 500
    data['frame'] = 1
    base_buffer_full = False  # Boolean indicating if the fbuffer is filled
    max_wait = 5  # seconds
    # Upon termination (including interruption) of the following code, data will be saved
    with on_cleanup(bmi_data_path, data, bdata):
        if not debug_bool:
            #sb_file_reader = wait_for_reader(sldy_path)
            save_files_3i(path_data['save_path'], '', expt_str)
            strc_mask = np.load(path_data['save_path'] / 'strc_mask.npy', allow_pickle=True).item()

        # Give random reward to trigger the jetball
        '''
        a.write_digital("D9", 1)
        time.sleep(1)
        a.write_digital("D9", 0)
        '''

        init_time_point = 0
        sleep_time = 0.001  # 10 ms (consider no sleep)
        #capture = sb_file_reader.GetNumCaptures() - 1 # 2 - This capture should be the third within the slide
        time_point_count = sb_file_reader.GetNumTimepoints(capture)
        plane_count = sb_file_reader.GetNumZPlanes(capture)
        z_plane = int(plane_count/2)

        print('STARTING RECORDING!!!')
        print('baseBuffer filling!...')

        for the_retry in range(0, 500):  # Will run for 500 frames
            for time_point in range(init_time_point, time_point_count):
                # Loop exit condition
                if debug_bool and data['frame'] > debug_input.shape[1]:
                    break

                start_time = time.perf_counter()
                image = sb_file_reader.ReadImagePlaneBuf(capture, 0, time_point, z_plane, tset['im']['chan_data']['chan_idx'], True)

                # ---- ROI extraction ----
                unit_vals = debug_input[:, data['frame']] if debug_bool else get_roi(image, strc_mask)
                data['bmi_act'][:, data['frame']] = unit_vals

                # Efficient ring buffer (no manual shifting)
                fbuffer = np.roll(fbuffer, -1, axis=1)
                fbuffer[:, -1] = unit_vals

                # ---- Baseline calculation ----
                if data['frame'] == init_frame_base:
                    if not np.isnan(np.sum(base_val_seed)):
                        base_val = base_val_seed.copy()
                        base_buffer_full = True
                        print("baseBuffer seeded!")
                    else:
                        base_val = np.ones(number_neurons, dtype=np.float32) * unit_vals / tset['f0_win']

                elif not base_buffer_full and data['frame'] <= (init_frame_base + tset['f0_win']):
                    base_val += unit_vals / tset['f0_win']
                    if data['frame'] == (init_frame_base + tset['f0_win']):
                        base_buffer_full = True
                        print("baseBuffer FULL!")

                else:
                    # rolling baseline
                    base_val = (base_val * (tset['f0_win'] - 1) + unit_vals) / tset['f0_win']

                data['base_vector'][:, data['frame']] = base_val

                # ---- Signal processing ----
                fsmooth = np.nanmean(fbuffer, axis=1, dtype=np.float32)
                if debug_bool:
                    data['fsmooth'][:, data['frame']] = fsmooth

                if base_buffer_full:
                    dff = (fsmooth - base_val) / base_val
                    cursor_i, target_hit, c1_bool, c2_val, c2_bool, c3_val, c3_bool = dff2cursor_target(
                        dff, bdata, tset['cursor_zscore_bool']
                    )
                    data['cursor'][data['frame']] = cursor_i
                    print(f"Cursor: {cursor_i}")

                    if debug_bool:
                        data['dff'][:, data['frame']] = dff
                        data['c1_bool'][data['frame']] = c1_bool
                        data['c2_val'][data['frame']] = c2_val
                        data['c2_bool'][data['frame']] = c2_bool
                        data['c3_val'][data['frame']] = c3_val
                        data['c3_bool'][data['frame']] = c3_bool

                    # feedback frequency
                    fb_freq_i = cursor2audio(cursor_i, fb_cal)
                    data['fb_freq'][data['frame']] = fb_freq_i

                    if fb_bool and not debug_bool:
                        play_tone(fb_freq_i, fb_cal['settings']['arduino']['duration'])

                    # ---- Trial logic ----
                    if buffer_update_counter == 0:
                        if trial_flag and not back2baseline_flag:
                            data['trialStart'][data['frame']] = 1
                            data['trialCounter'] += 1
                            trial_flag = False
                            print("New Trial!")

                        if back2baseline_flag:
                            if data['cursor'][data['frame']] <= back2base:
                                back2base_counter += 1
                            if back2base_counter >= tset['back2base_frame_thresh']:
                                back2baseline_flag = False
                                back2base_counter = 0
                                print("back to baseline")
                        elif target_hit:
                            print("target hit")
                            data['self_target_counter'] += 1
                            data['self_hits'][data['frame']] = 1
                            print(f"Trial: {data['trial_counter']}, Num Self Hits: {data['self_target_counter']}")

                            if flags['BMI_stim']:
                                if flags['DRstim']:
                                    deliver_stim = 1
                                    data['self_target_dr_stim_counter'] += 1
                                    data['self_dr_stim'][data['frame']] = 1
                                    print(
                                        f"Trial: {data['trial_counter']}, DR STIMS: {data['self_target_dr_stim_counter']}")

                                if flags['Water']:
                                    deliver_water = 1
                                    data['water_counter'] += 1
                                    data['vector_water'][data['frame']] = 1
                                    print(f"Trial: {data['trial_counter']}, Water: {data['water_counter']}")

                                print("Target Achieved! (self-target)")

                                if not debug_bool:
                                    print("RewardTone delivery!")
                        buffer_update_counter = relaxation_frames
                        back2baseline_flag = True
                        trial_flag = True

                    elif not trial_flag and flags['StimRandom'] and data['frame'] in data['vector_stim']:
                        deliver_stim = 1
                        print("SCHEDULED DR STIM")
                        data['sched_random_stim'] += 1
                        data['random_dr_stim'][data['frame']] = 1
                    else:
                        buffer_update_counter -= 1

                # ---- Reward delivery ----
                if deliver_water:
                    print('Delivering water...') # With custom thing, which should be controlled by computer
                    if not debug_bool:
                        #a.write_digital("D9", 1)
                        time.sleep(1)
                        #a.write_digital("D9", 0)
                    deliver_water = 0
                    print('Water delivered!')

                if deliver_stim:
                    print('Stimulating...')
                    if tset['delay_flag']:
                        time.sleep(tset['delay_time'])
                    if not debug_bool:
                        # Blue light
                        #a.write_digital("D5", 1)
                        time.sleep(0.2)
                        #a.write_digital("D5", 0)
                        # UV light
                        #a.write_digital("D3", 1)
                        time.sleep(1)
                        #a.write_digital("D3", 0)
                    deliver_stim = 0
                    print('Light stimulation delivered!')

                # ---- Advance frame ----
                data['frame'] += 1
                data['time_vector'][data['frame']] = time.time() - start_time

                # ---- Timing sync ----
                if not debug_bool:
                    target_dt = 1 / (tset['im']['frame_rate'] * 1.2)
                    sleep_dur = target_dt - data['time_vector'][data['frame']]
                    if sleep_dur > 0:
                        time.sleep(sleep_dur)

                # Check for new timepoints
                sb_file_reader.Refresh(capture)
                if init_time_point == time_point_count:
                    no_progress_counter += 1
                else:
                    no_progress_counter = 0
                time.sleep(sleep_time)
                print(no_progress_counter)

                # If we have waited too long, quit
                if no_progress_counter * sleep_time > max_wait:
                    break

                # Loop again
                init_time_point = time_point_count
                time_point_count = sb_file_reader.GetNumTimepoints(capture)

    return np.load(bmi_data_path)
'''
        while (not debug_bool and counter_same < counter_same_thresh) or (debug_bool and data['frame'] <= debug_input.shape[1]):
            if not debug_bool:
                #im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
                im = sb_file_reader.ReadImagePlaneBuf(capture, 0, 0, z_plane, tset['im']['chan_data']['chan_idx'], True)
            else:
                im = np.zeros((px, py))

            if not np.array_equal(im, last_frame) or debug_bool:
                #start_time = time.time()  # Start timing to see the length of an iteration
                start_time = time.perf_counter()

                # What is this for?
                #if not debug_bool:
                #    last_frame = im  # Comparison and assignment takes ~4ms
                #    s.write(ni_getimage)
                #    time.sleep(0.001)
                #    s.write([0, 0, 0])

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
                            #playTone(a, fb_cal['settings']['arduino']['pin'], fb_freq_i, fb_cal['settings']['arduino']['duration'])
                            play_tone(fb_freq_i, fb_cal['settings']['arduino']['duration'])

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

                                    if flags['BMI_stim']:
                                        if flags['DRstim']:
                                            deliver_stim = 1
                                            data['self_target_dr_stim_counter'] += 1
                                            data['self_dr_stim'][data['frame']] = 1
                                            print(f'Trial: {data["trial_counter"]}, DR STIMS: {data["self_target_dr_stim_counter"]}')
                                        if flags['Water']:
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
                                if not trial_flag and flags['StimRandom']:
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
'''