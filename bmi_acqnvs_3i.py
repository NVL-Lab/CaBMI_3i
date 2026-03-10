from datetime import datetime
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

from scipy.io import loadmat

from wait_on_task_3i import *
from rois.obtain_roi import get_roi
from calibration.dff2cursor_target import dff2cursor_target
from calibration.cursor2audio import cursor2audio
from expt2bmi_flags import get_flags
from params.play_tone import *

@contextmanager
def on_cleanup(save_path, bmi_info, task_set):
    try:
        yield
    finally:
        print('Cleaning...')
        if task_set['expt']['bmi']['save']:
            np.savez_compressed(save_path, **bmi_info)

def bmi_acqnvs_3i(task_set, path_data, expt_str, bdata, vector_stim, debug_bool, debug_input, fb_bool, fb_cal, strc_info, base_val: Optional[np.ndarray]=None, run=''):
    # base_val_seed are values to add to "initialize the baseline" instead of starting with ones or nans.
    # Save path
    base_name = 'bmi_online'
    task_set['bmi_frames'] = int(np.ceil(task_set['bmi_len'] * task_set['im']['frame_rate']))
    expected_expt_length = task_set['bmi_frames']
    relaxation_frames = round(task_set['relaxation_time'] * task_set['im']['frame_rate'])
    print(f'BMI recording will consist of {task_set["bmi_frames"]} frames')

    if task_set['expt']['bmi']['load']:
        try:
            matches = [path for path in path_data['save_path'].rglob('*') if base_name in path.name]
            bdata = np.load(matches[-1], allow_pickle=True)
            print(f'Loading {matches[-1].name}')
        except FileNotFoundError:
            print('BMI data not found. Please run bmi_acqnvs_3i.')
            exit(1)
        return bdata
    elif task_set['expt']['bmi']['sim']:
        recording_path = path_data['test_dir']
        print('Simulating bmi...')
        bdata = bmi_acqnvs_sim_3i(recording_path, task_set, path_data, expt_str, bdata, vector_stim, debug_bool,
                                  debug_input, fb_bool, fb_cal, strc_info, base_val)
        return bdata

    # Creates an instance of slidebook reader
    sb_file_reader, capture = wait_for_reader_with_latest_capture(path_data['sldy_path'])
    task_set = get_recording_settings(sb_file_reader, capture, task_set)
    bmi_data_path = path_data['save_path'] / f'{base_name}_{datetime.now().strftime("%y%m%dT%H%M%S")}.npz'
    task_set['capture'] = capture

    # Load flag configuration file
    flags = get_flags()[expt_str]

    # Values of parameters in frames

    back2base = 1/2*bdata['t1']

    # ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** *
    # ** ** ** ** ** ** ** ** ** Initialization of BMI acquisition ** ** ** ** ** ** ** ** ** ** ** ** ** ** *
    # ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** *

    number_neurons = len(bdata['e_id'])

    # Pre-allocating arrays
    fbuffer = np.full((number_neurons, task_set['dff_win']), np.nan, dtype=np.float64)

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

    trial_flag = True #1
    # TODO: decide the non_buffer_update_counter is worth keeping or not. Don't keep it at 0
    # Nuria explanation: this buffer was to "drop" the first images to avoid artifacts
    # Me: Could be worth dropping
    #: TODO: Nuria changed the following to remove the 0 back to the tset value
    non_buffer_update_counter = 0  # Counter when we don't want to update the buffer
    # TODO: Nuria changed this back from the 0 back to the value of the non-buffer-update
    init_frame_base = task_set['prefix_win']
    # Beginning of experiment and VTA stim
    buffer_update_counter = 0

    deliver_stim = 0  # Light stimulation
    deliver_water = 0 # Reward feedback

    back2base_counter = 0
    back2baseline_flag = False #0

    base_buffer_full = False

    channel = task_set['im']['chan_data']['recording_chan']
    data['frame'] = 0 #1
    counter_same = 0
    temp_time_point = 0
    frame_interval = 1 / (task_set['im']['frame_rate'] * 1.2)
    plane_count = sb_file_reader.GetNumZPlanes(capture)
    z_plane = int(plane_count / 2)
    bmi_info = {}

    # save_files_3i(path_data['save_path'], pl = None, expt_str)
    '''
    if task_set['save']:
        save_path_expt = path_data['save_path'] / 'im' / expt_str
        save_path_expt.mkdir(parents=True, exist_ok=True)
        strc_mask = np.load(path_data['save_path'] / 'strc_info.npz', allow_pickle=True)['strc_mask'] ##.item()
    else:
        strc_mask = strc_info['strc_mask']
    '''

    # Give random reward to trigger the jetball
    '''
    a.write_digital("D9", 1)
    time.sleep(1)
    a.write_digital("D9", 0)
    '''

    print('STARTING RECORDING!!!')
    print('baseBuffer filling!...')
    # Upon termination (including interruption) of the following code, data will be saved
    with on_cleanup(bmi_data_path, bmi_info, task_set):
        while counter_same < 1000 and data['frame'] < expected_expt_length:
            sb_file_reader.Refresh(capture)  # Takes ~4ms
            curr_time_point = sb_file_reader.GetNumTimepoints(capture)

            print(f'*** Time Point: {curr_time_point}')
            # capture (0-n), position ( not montage = 0), timepoint, zplane num, channel, True for 2d array return
            image = sb_file_reader.ReadImagePlaneBuf(capture, 0, curr_time_point - 1, z_plane,
                                                     task_set['im']['chan_data'][channel],
                                                     True)

            # Code will only run when in current time point
            if curr_time_point == temp_time_point: #  and curr_time_point <= non_buffer_update_counter
                counter_same += 1
                continue

            if non_buffer_update_counter < init_frame_base:
                non_buffer_update_counter += 1
                data = move_frame(data, task_set, start_time, frame_interval)
                counter_same = 0
                continue

            temp_time_point = curr_time_point
            print(f'*** Frames captured: {data["frame"]+1}')
            start_time = time.perf_counter()

            print('Extracting ROI Mask...')
            unit_vals = get_roi(image, strc_mask)  # obtain roi values
            data['bmi_act'][:, data['frame']] = unit_vals

            fbuffer[:, :-1] = fbuffer[:, 1:]
            fbuffer[:, -1] = unit_vals

            print('Calculating Baseline Buffer...')
            if not base_buffer_full:
                if data['frame'] == init_frame_base:
                    if not np.all(np.isnan(base_val)):
                        base_buffer_full = True
                        print('baseBuffer seeded!')
                    else:
                        base_val = np.ones(number_neurons, dtype=np.float64) * unit_vals / task_set['f0_win']
                elif data['frame'] < (init_frame_base+task_set['f0_win']):
                    base_val += unit_vals / task_set['f0_win']
                elif data['frame'] == (init_frame_base+task_set['f0_win']):
                    base_val += unit_vals / task_set['f0_win']
                    base_buffer_full = True
                    print('baseBuffer FULL!')
            else:
                print('Rolling base buffer...')
                base_val = (base_val * (task_set['f0_win'] - 1) + unit_vals) / task_set['f0_win']

            data['base_vector'][:, data['frame']] = base_val

            fs_smooth = np.nanmean(fbuffer, axis=1, dtype=np.float64)

            if base_buffer_full:
                dff = (fs_smooth - base_val) / base_val
                _, cursor_i, target_hit, c1_bool, c2_val, c2_bool, c3_val, c3_bool = dff2cursor_target(
                    dff, bdata, task_set['cursor_zscore_bool'])

                print(f'Cursor: {cursor_i}')
                data['cursor'][data['frame']] = cursor_i

                fb_freq_i = cursor2audio(cursor_i, fb_cal, fb_cal['settings']) #fb_cal['settings'].item()
                data['fb_freq'][data['frame']] = fb_freq_i

                if fb_bool:
                    #play_tone(fb_freq_i, fb_cal['settings']['arduino']['duration'])
                    print('TONE PLAYED!')

                if buffer_update_counter == 0:
                    if trial_flag and not back2baseline_flag:
                        data['trial_start'][data['frame']] = 1
                        data['trial_counter'] += 1
                        trial_flag = False
                        print('New Trial!')

                    if back2baseline_flag:
                        if data['cursor'][data['frame']] <= back2base:
                            back2base_counter += 1
                        if back2base_counter >= task_set['back2base_frame_thresh']:
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

            if buffer_update_counter > 0:
                buffer_update_counter -= 1

            # TODO: get water delivery setup
            if deliver_water:
                #play_tone(9000, 1)
                '''
                a.write_digital("D9", 1)
                time.sleep(1)
                a.write_digital("D9", 0)
                '''
                deliver_water = 0
                print('water delivered!')

            if deliver_stim:
                if task_set['delay_flag']:
                    time.sleep(task_set['delay_time'])
                #play_tone(5000, 0.2)
                #play_tone(3000, 1)
                '''
                a.write_digital("D5", 1)
                time.sleep(0.2)
                a.write_digital("D5", 0)
                a.write_digital("D3", 1)
                time.sleep(1)
                a.write_digital("D3", 0)
                '''
                deliver_stim = 0
                print('stim delivered!')

            data = move_frame(data, task_set, start_time, frame_interval)
            counter_same = 0

    return bmi_info

def bmi_acqnvs_sim_3i(bmi_path, task_set, path_data, expt_str, bdata, vector_stim, debug_bool, debug_input, fb_bool, fb_cal, strc_mask, base_val: Optional[np.ndarray]=None):
    #target_info = loadmat(
    #    '/Users/saulglopez/Scripts/uab/nvl_lab/CaBMI/data/HoloBMI/Raw/190930/NVI12/D5/BMI_online190930T152419.mat')

    record_raw = np.load(bmi_path, mmap_mode='r')
    record_frames = task_set['bmi_frames']
    #record_frame_limit = task_set['cb']['baseline_frames']+record_frames
    record_frame_limit = record_raw.shape[0]
    record = record_raw[record_frame_limit-record_frames-1:record_frame_limit]
    record_frames = len(record) # Recording being used does not have enough frames
    #record_frames = len(bdata['bmi_act'][0]) #FOR TESTING

    task_set['resolution'] = (record.shape[2], record.shape[1])

    # Load flag configuration file
    flags = get_flags()[expt_str]

    relaxation_frames = round(task_set['relaxation_time'] * task_set['im']['frame_rate'])

    back2base = 1 / 2 * bdata['t1']

    # ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** *
    # ** ** ** ** ** ** ** ** ** Initialization of BMI acquisition ** ** ** ** ** ** ** ** ** ** ** ** ** ** *
    # ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** ** *

    number_neurons = len(bdata['e_id'])
    print('Number of Neurons: ', number_neurons)

    # Pre-allocating arrays
    fbuffer = np.full((number_neurons, task_set['dff_win']), np.nan, dtype=np.float64)

    data = {
        'self_hits': np.zeros(record_frames, dtype=np.float64),
        'self_dr_stim': np.zeros(record_frames, dtype=np.float64),
        'vector_water': np.zeros(record_frames, dtype=np.float64),
        'random_dr_stim': np.zeros(record_frames, dtype=np.float64),
        'trial_start': np.zeros(record_frames, dtype=np.float64),

        'cursor': np.full(record_frames, np.nan, dtype=np.float64),
        'fb_freq': np.full(record_frames, np.nan, dtype=np.float32),
        'time_vector': np.full(record_frames, np.nan, dtype=np.float64),

        'bmi_act': np.full((number_neurons, record_frames), np.nan, dtype=np.float64),
        'base_vector': np.full((number_neurons, record_frames), np.nan, dtype=np.float64),

        # Debug, TODO: Remove after debugging
        'vector_stim': vector_stim,

        # Counters
        'self_target_counter': 0,
        'self_target_dr_stim_counter': 0,
        'water_counter': 0,
        'trial_counter': 0,  # TODO: Remove one

        # Flags
        'sched_random_stim': 0,
    }

    trial_flag = True  # 1
    # TODO: decide the non_buffer_update_counter is worth keeping or not. Don't keep it at 0
    # Nuria explanation: this buffer was to "drop" the first images to avoid artifacts
    # Me: Could be worth dropping
    #: TODO: Nuria changed the following to remove the 0 back to the tset value
    #non_buffer_update_counter = task_set['prefix_win']  # Counter when we don't want to update the buffer
    non_buffer_update_counter = 0  # Counter when we don't want to update the buffer
    # TODO: Nuria changed this back from the 0 back to the value of the non-buffer-update
    #init_frame_base = non_buffer_update_counter + 1
    init_frame_base = task_set['prefix_win']
    # Beginning of experiment and VTA stim
    buffer_update_counter = 0

    deliver_stim = 0  # Light stimulation
    deliver_water = 0  # Reward feedback

    back2base_counter = 0
    back2baseline_flag = False  # 0

    base_buffer_full = False

    frame_interval = 1 / (task_set['im']['frame_rate'] * 1.2)

    # save_files_3i(path_data['save_path'], pl = None, expt_str)
    '''
    if task_set['expt']['bmi']['load']:
        save_path_expt = path_data['save_path'] / 'im' / expt_str
        save_path_expt.mkdir(parents=True, exist_ok=True)
        strc_mask = np.load(path_data['save_path'] / 'strc_info.npz').item()['strc_mask']
    else:
        strc_mask = strc_info['strc_mask']
    '''

    # Give random reward to trigger the jetball
    '''
    a.write_digital("D9", 1)
    time.sleep(1)
    a.write_digital("D9", 0)
    '''

    bmi_data_path = path_data['save_path'] / f'bmi_online_{datetime.now().strftime("%y%m%dT%H%M%S")}.npz'
    bmi_info = {}
    print('STARTING RECORDING!!!')
    print('baseBuffer filling!...')
    if not np.all(np.isnan(base_val)):
        base_buffer_full = True
        print('baseBuffer seeded!')
    #stream = make_stream()
    #stream.start()
    #player = TonePlayer()
    # Upon termination (including interruption) of the following code, data will be saved
    data['frame'] = 0
    with on_cleanup(bmi_data_path, bmi_info, task_set):
        for frame in range(record_frames):
            print(f'*** Frame: {frame}')
            start_time = time.perf_counter()

            if non_buffer_update_counter < init_frame_base:
                non_buffer_update_counter += 1
                data = move_frame(data, task_set, start_time, frame_interval)
                continue

            # For 'sim'
            image = record[frame]

            print('Extracting ROI Mask...')
            # For 'sim'
            unit_vals = get_roi(image, strc_mask)  # obtain roi values
            data['bmi_act'][:, frame] = unit_vals

            # For 'sim_mat'
            #unit_vals = bdata['bmi_act'][:, frame]
            #data['bmi_act'][:, frame] = unit_vals

            # Update buffer
            fbuffer[:, :-1] = fbuffer[:, 1:]
            fbuffer[:, -1] = unit_vals

            if not base_buffer_full:
                if frame == init_frame_base:
                    base_val = np.ones(number_neurons, dtype=np.float64) * unit_vals / task_set['f0_win']
                    print('base_buffer initialized!')
                elif frame < (init_frame_base+task_set['f0_win']):
                    base_val += unit_vals / task_set['f0_win']
                    print('base_buffer updating...')
                elif frame == (init_frame_base+task_set['f0_win']):
                    base_val += unit_vals / task_set['f0_win']
                    base_buffer_full = True
                    print('base_buffer FULL!')
            else:
                print('Rolling base buffer...')
                base_val = (base_val * (task_set['f0_win'] - 1) + unit_vals) / task_set['f0_win']

            data['base_vector'][:, frame] = base_val

            fs_smooth = np.nanmean(fbuffer, axis=1, dtype=np.float64)

            if base_buffer_full:
                dff = (fs_smooth - base_val) / base_val
                print(base_val)
                _, cursor_i, target_hit, c1_bool, c2_val, c2_bool, c3_val, c3_bool = dff2cursor_target(
                    dff, bdata, task_set['cursor_zscore_bool'])

                print(f'Cursor: {cursor_i}')
                data['cursor'][frame] = cursor_i

                fb_freq_i = cursor2audio(cursor_i, fb_cal, fb_cal['settings'])
                data['fb_freq'][frame] = fb_freq_i

                if fb_bool:
                    #play_tone(fb_freq_i, fb_cal['settings']['arduino']['duration'])
                    #stream.write(data['fb_freq'][frame])
                    #tone = get_tone(data['fb_freq'][frame], fb_cal['settings']['arduino']['duration'])
                    #stream.write(tone.reshape(-1, 1))
                    print('TONE PLAYED!')

                if buffer_update_counter == 0:
                    if trial_flag and not back2baseline_flag:
                        data['trial_start'][frame] = 1
                        data['trial_counter'] += 1
                        trial_flag = False
                        print('New Trial!')

                    if back2baseline_flag:
                        if data['cursor'][frame] <= back2base:
                            back2base_counter += 1
                        if back2base_counter >= task_set['back2base_frame_thresh']:
                            back2baseline_flag = False
                            back2base_counter = 0
                            print('back to baseline')
                    else:
                        if target_hit:
                            print('target hit')
                            data['self_target_counter'] += 1
                            data['self_hits'][frame] = 1
                            print(f'Trial: {data["trial_counter"]}, Num Self Hits: {data["self_target_counter"]}')
                            #play_tone(fb_freq_i, fb_cal['settings']['arduino']['duration'])

                            if flags['bmi_stim']:
                                if flags['dr_stim']:
                                    deliver_stim = 1
                                    data['self_target_dr_stim_counter'] += 1
                                    data['self_dr_stim'][frame] = 1
                                    print(
                                        f'Trial: {data["trial_counter"]}, DR STIMS: {data["self_target_dr_stim_counter"]}')
                                if flags['water']:
                                    deliver_water = 1
                                    data['water_counter'] += 1
                                    data['vector_water'][frame] = 1
                                    print(f'Trial: {data["trial_counter"]}, Water: {data["water_counter"]}')

                                print('Target Achieved! (self-target)')

                                print('RewardTone delivery!')
                                buffer_update_counter = relaxation_frames
                                back2baseline_flag = True
                                trial_flag = True
                        if not trial_flag and flags['stim_random']:
                            if frame in data['vector_stim']:
                                deliver_stim = 1
                                print('SCHEDULED DR STIM')
                                data['sched_random_stim'] += 1
                                data['random_dr_stim'][frame] = 1

            if buffer_update_counter > 0:
                buffer_update_counter -= 1

            # TODO: get water delivery setup
            if deliver_water:
                #play_tone(9000, 1)
                '''
                a.write_digital("D9", 1)
                time.sleep(1)
                a.write_digital("D9", 0)
                '''
                deliver_water = 0
                print('water delivered!')

            if deliver_stim:
                if task_set['delay_flag']:
                    time.sleep(task_set['delay_time'])
                #play_tone(5000, 0.2)
                #play_tone(3000, 1)
                '''
                a.write_digital("D5", 1)
                time.sleep(0.2)
                a.write_digital("D5", 0)
                a.write_digital("D3", 1)
                time.sleep(1)
                a.write_digital("D3", 0)
                '''
                deliver_stim = 0
                print('stim delivered!')

            data = move_frame(data, task_set, start_time, frame_interval)

    bmi_info['bdata'] = bdata
    bmi_info['data'] = data

    return bmi_info

def move_frame(data, task_set, start_time, frame_interval):
    print('Moving Frame...')
    #data['frame'] += 1  # data['time_vector'] begins at second index (do i want this?)
    data['time_vector'][data['frame']] = time.perf_counter() - start_time
    print(f'Execution time: {data["time_vector"][data["frame"]]} seconds')

    if data['time_vector'][data['frame']] < 1 / (
            task_set['im']['frame_rate'] * 1.2):
        time.sleep(1 / (task_set['im']['frame_rate'] * 1.2) - data['time_vector'][data['frame']])

    elapsed_time = time.perf_counter() - start_time
    # print(f'Execution time: {elapsed_time} seconds')
    if elapsed_time < frame_interval:
        time.sleep(frame_interval - elapsed_time)
    data['frame'] += 1  # data['time_vector'] begins at second index (do i want this?)

    return data