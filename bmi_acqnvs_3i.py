import matplotlib.pyplot as plt
from datetime import datetime
from contextlib import contextmanager
import numpy as np
import time

from wait_on_reader_3i import wait_for_reader
from rois.obtain_roi import get_roi
from calibration.dff2cursor_target import dff2cursor_target
from calibration.cursor2audio import cursor2audio
from expt2bmi_flags import get_flags
from params.play_tone import play_tone

@contextmanager
def on_cleanup(save_path, data, bdata):
    try:
        yield
    finally:
        print('Cleaning...')
        np.savez(save_path, data=data, bdata=bdata)

def bmi_acqnvs_3i(tset, path_data, capture, expt_str, bdata, vector_stim, debug_bool, debug_input, base_val_seed, fb_bool, fb_cal, plot=False, run=False) -> np.ndarray:
    bname = 'bmi_online'
    if not run:
        try:
            matches = [path for path in path_data['save_path'].rglob('*') if bname in path.name]
            bdata = np.load(matches[-1], allow_pickle=True)
            print(f'Loading {matches[-1].name}')
            return bdata
        except FileNotFoundError:
            print('Baseline data not found. Please run baseline_acqnvs_3i.')
            exit(1)

    # Save path
    bmi_data_path = path_data['save_path'] / f'bmi_online_{datetime.now().strftime("%y%m%dT%H%M%S")}.npz'
    sb_file_reader = wait_for_reader(path_data['sldy_path'])
    while sb_file_reader.GetNumCaptures() < capture + 1:
        capture = int(input('Did you start the desired capture? If not, enter new capture number and press enter: '))
        sb_file_reader.Refresh(capture)

    # Load flag configuration file
    flags = get_flags()[expt_str]

    # BMI parameters
    relaxation_time = 1 #0 # there can't be another hit in this many sec

    # Values of parameters in frames
    expected_expt_length = int(np.ceil(tset['bmi_len']*tset['im']['frame_rate'])) # in frames
    relaxation_frames = round(relaxation_time*tset['im']['frame_rate'])
    
    #bdata = np.load(baseline_calib_file, allow_pickle=True)
    back2base = 1/2*bdata['t1']

    # ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** *
    # ** ** ** ** ** ** ** ** ** Initialization of BMI acquisition ** ** ** ** ** ** ** ** ** ** ** ** ** ** *
    # ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** *

    number_neurons = len(bdata['e_id'])

    # Pre-allocating arrays
    fbuffer = np.full((number_neurons, tset['dff_win']), np.nan, dtype=np.float64)
    #data = init_data(expected_expt_length, number_neurons, vector_stim, debug_bool=True)

    data = {
        'self_hits'     : np.zeros(expected_expt_length, dtype=np.float64),
        'self_dr_stim'  : np.zeros(expected_expt_length, dtype=np.float64),
        'vector_water'  : np.zeros(expected_expt_length, dtype=np.float64),
        'random_dr_stim': np.zeros(expected_expt_length, dtype=np.float64),
        'trial_start'   : np.zeros(expected_expt_length, dtype=np.float64),

        'cursor'        : np.full(expected_expt_length, np.nan, dtype=np.float64),
        'fb_freq'       : np.full(expected_expt_length, np.nan, dtype=np.float64),
        'time_vector'   : np.full(expected_expt_length, np.nan, dtype=np.float64),

        'bmi_act'       : np.full((number_neurons, expected_expt_length), np.nan, dtype=np.float64),
        'base_vector'   : np.full((number_neurons, expected_expt_length), np.nan, dtype=np.float64),

        # Debug, TODO: Remove after debugging
        'vector_stim'   : vector_stim,

        # Counters
        'self_target_counter'        : 0,
        'self_target_dr_stim_counter': 0,
        'water_counter': 0,
        'trial_counter': 0, # TODO: Remove one

        # Flags
        'sched_random_stim': 0,
    }
    if debug_bool:
        data.update({
            'fsmooth': np.full((number_neurons, expected_expt_length), np.nan, dtype=np.float64),
            'dff'    : np.full((number_neurons, expected_expt_length), np.nan, dtype=np.float64),

            'c1_bool': np.full(expected_expt_length, np.nan, dtype=np.float64),
            'c2_val' : np.full(expected_expt_length, np.nan, dtype=np.float64),
            'c2_bool': np.full(expected_expt_length, np.nan, dtype=np.float64),
            'c3_val' : np.full(expected_expt_length, np.nan, dtype=np.float64),
            'c3_bool': np.full(expected_expt_length, np.nan, dtype=np.float64)
        })

    trial_flag = True #1
    non_buffer_update_counter = 0 #tset['prefix_win']  # Counter when we don't want to update the buffer
    init_frame_base = 0 # non_buffer_update_counter + 1
    # Beginning of experiment and VTA stim
    buffer_update_counter = 0

    deliver_stim = 0  # Light stimulation
    deliver_water = 0 # Reward feedback

    back2base_counter = 0
    back2baseline_flag = False #0

    data['frame'] = 0 #1
    base_buffer_full = False
    max_wait = 5  # seconds

    # Upon termination (including interruption) of the following code, data will be saved
    with on_cleanup(bmi_data_path, data, bdata):
        if not debug_bool:
            # save_files_3i(path_data['save_path'], pl = None, expt_str)
            save_path_expt = path_data['save_path'] / 'im' / expt_str
            save_path_expt.mkdir(parents=True, exist_ok=True)
            strc_mask = np.load(path_data['save_path'] / 'strc_mask.npz', allow_pickle=True)['strc_mask'].item()

        # Give random reward to trigger the jetball
        '''
        a.write_digital("D9", 1)
        time.sleep(1)
        a.write_digital("D9", 0)
        '''

        #init_time_point = 0
        init_time_point = 8925
        sleep_time = 0.001  # 10 ms (consider no sleep)
        #capture = sb_file_reader.GetNumCaptures() - 1 # 2 - This capture should be the third within the slide
        #time_point_count = sb_file_reader.GetNumTimepoints(capture)
        time_point_count = 26778 # 18077 actual frames difference
        plane_count = sb_file_reader.GetNumZPlanes(capture)
        z_plane = int(plane_count/2)

        print('STARTING RECORDING!!!')
        print('baseBuffer filling!...')
        read_break = False

        if plot:
            fig = plt.figure(0)
            title = 'Timepoint: {tp:6d}'

        for the_retry in range(0, 500):  # Will run for 500 frames (0, 500)
            for time_point in range(init_time_point, time_point_count):
                if debug_bool and data['frame'] > debug_input.shape[1]: # debug_input.shape[1] or maybe len if 1D list
                    break

                print(f'*** Time Point: {time_point + 1}')

                if not debug_bool:
                    image = sb_file_reader.ReadImagePlaneBuf(capture, 0, time_point, z_plane, tset['im']['chan_data']['chan_idx'], True)
                    image = path_data['test_data'][time_point]
                    if image.shape[0] == 0:
                        break

                start_time = time.perf_counter()

                if not debug_bool and plot:
                    if time_point == 0:
                        img_artist = plt.imshow(image)
                    elif time_point % 2 == 0:
                        img_artist.set_data(image)
                        plt.draw()
                        fig.canvas.flush_events()
                        plt.title(title.format(tp=time_point), loc='left')
                        try:
                            plt.pause(0.01)
                        except KeyboardInterrupt:
                            print("Keyboard Interrupt")
                            exit()

                if non_buffer_update_counter == 0:
                    print('Extracting ROI Mask...')
                    if not debug_bool:
                        unit_vals = get_roi(image, strc_mask)  # Function to obtain Rois values
                    else:
                        unit_vals = debug_input[:, data['frame']]
                    data['bmi_act'][:, data['frame']] = unit_vals

                    fbuffer[:, :-1] = fbuffer[:, 1:]
                    fbuffer[:, -1] = unit_vals

                    print('Calculating Baseline Buffer...')
                    if data['frame'] == init_frame_base:
                        if not np.isnan(np.sum(base_val_seed)):
                            base_buffer_full = True
                            base_val = base_val_seed
                            print('baseBuffer seeded!')
                        else:
                            base_val = np.ones(number_neurons, dtype=np.float64) * unit_vals / tset['f0_win']
                    elif not base_buffer_full and data['frame'] <= (init_frame_base + tset['f0_win']):
                        base_val += unit_vals / tset['f0_win']
                        if data['frame'] == (init_frame_base + tset['f0_win']):
                            base_buffer_full = True
                            print('baseBuffer FULL!')
                    else:
                        print('Rolling base buffer...')
                        base_val = (base_val * (tset['f0_win'] - 1) + unit_vals) / tset['f0_win']

                    data['base_vector'][:, data['frame']] = base_val

                    print('Processing...')
                    fs_mooth = np.nanmean(fbuffer, axis=1, dtype=np.float64)

                    if debug_bool:
                        data['fsmooth'][:, data['frame']] = fs_mooth

                    if base_buffer_full:
                        dff = (fs_mooth - base_val) / base_val
                        _, cursor_i, target_hit, c1_bool, c2_val, c2_bool, c3_val, c3_bool = dff2cursor_target(
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

                        fb_freq_i = cursor2audio(cursor_i, fb_cal, fb_cal['settings'].item())
                        data['fb_freq'][data['frame']] = fb_freq_i

                        if fb_bool and not debug_bool:
                            play_tone(fb_freq_i, fb_cal['settings'].item()['arduino']['duration'])

                        if buffer_update_counter == 0 and base_buffer_full:
                            if trial_flag and not back2baseline_flag:
                                data['trial_start'][data['frame']] = 1
                                data['trial_counter'] += 1
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

                                    if flags['bmi_stim']:
                                        if flags['dr_stim']:
                                            deliver_stim = 1
                                            data['self_target_dr_stim_counter'] += 1
                                            data['self_dr_stim'][data['frame']] = 1
                                            print(f'Trial: {data["trial_counter"]}, DR STIMS: {data["self_target_dr_stim_counter"]}')
                                        if flags['water']:
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
                                if not trial_flag and flags['stim_random']:
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
                            #a.write_digital("D9", 1)
                            time.sleep(1)
                            #a.write_digital("D9", 0)
                        deliver_water = 0
                        print('water delivered!')

                    if deliver_stim:
                        if tset['delay_flag']:
                            time.sleep(tset['delay_time'])
                        if not debug_bool:
                            # a.write_digital("D5", 1)
                            time.sleep(0.2)
                            # a.write_digital("D5", 0)
                            # a.write_digital("D3", 1)
                            time.sleep(1)
                            # a.write_digital("D3", 0)
                        deliver_stim = 0
                        print('stim delivered!')

                    print('Moving Frame...')
                    data['frame'] += 1
                    data['time_vector'][data['frame']] = time.perf_counter() - start_time
                    print(f'Execution time: {data["time_vector"][data["frame"]]} seconds')

                    if not debug_bool and data['time_vector'][data['frame']] < 1 / (
                            tset['im']['frame_rate'] * 1.2):
                        time.sleep(1 / (tset['im']['frame_rate'] * 1.2) - data['time_vector'][data['frame']])

            # Check for new timepoints
            sb_file_reader.Refresh(capture)  # Takes ~4ms
            n_time_point_count = sb_file_reader.GetNumTimepoints(capture)
            # Checks refreshing > 1 sec then refreshing stops
            refresh_start = time.perf_counter()
            while n_time_point_count == time_point_count:
                sb_file_reader.Refresh(capture)
                n_time_point_count = sb_file_reader.GetNumTimepoints(capture)
                if time.perf_counter() - refresh_start > max_wait:
                    read_break = True
                    break
            # If refreshing was halted, acquisition stops entirely
            if read_break:
                break

            # Loop again
            init_time_point = time_point_count
            time_point_count = sb_file_reader.GetNumTimepoints(capture)
            break

    return np.load(bmi_data_path, allow_pickle=True)