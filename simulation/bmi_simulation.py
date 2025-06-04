import numpy as np
from calibration.dff2cursor_target import dff2cursor_target

def bmi_simulation(bmi_act, tset, target_info):
    """
    Function to simulate the BMI
    args:
        bmiAct: a variable within BMI online file
        tset: parameters/define_BMI_task_settings.m
        target_info: bmi online target info file

    return:
    """
    # BMI parameters
    relaxation_time = 0  # there can't be another hit in this many sec
    non_buffer_update_counter = tset['prefix_win']  # counter when we don't want to update the buffer
    init_frame_base = non_buffer_update_counter + 1
    
    # Values of parameters in frames
    expected_length_experiment = bmi_act.shape[1]  # in frames
    relaxation_frames = round(relaxation_time * tset['im']['frame_rate'])
    
    # Define BMI parameters from baseline calibration
    back2base = 0.5 * target_info['T1']  # cursor must be under this value to hit again
    number_neurons = len(target_info['E_id'])
    
    # INITIALIZE
    fbuffer = np.full((number_neurons, tset['dff_win']), np.nan, dtype=np.float32)  # Define a windows buffer
    
    data = {
        'cursor': np.full((1, int(np.ceil(expected_length_experiment))), np.nan, dtype=np.float32),
        'baseVector': np.full((number_neurons, int(np.ceil(expected_length_experiment))), np.nan, dtype=np.float32),
        'trialStart': np.zeros((1, int(np.ceil(expected_length_experiment))), dtype=np.float32),
        'selfHits': np.zeros((1, int(np.ceil(expected_length_experiment))), dtype=np.float32),
        'selfTargetCounter': 0,
        'trialCounter': 0,
        'bmiAct': bmi_act,
        'frame': 1
    }
    
    buffer_update_counter = 0
    back2base_counter = 0
    
    # Initializing flags
    trial_flag = 1
    back2base_flag = 0
    base_buffer_full = False  # Boolean indicating whether the fbuffer is filled
   
    # SIMULATION
    for i in range(expected_length_experiment):
        if non_buffer_update_counter == 0:
            # Obtain value of the neurons' fluorescence
            unit_vals = bmi_act[:, data['frame'] - 1]
            
            # Update F buffer
            fbuffer[:, :-1] = fbuffer[:, 1:]
            fbuffer[:, -1] = unit_vals
            
            # Calculate F0 baseline activity
            if data['frame'] == init_frame_base:
                baseval = np.ones(number_neurons, dtype=np.float32) * unit_vals / tset['f0_win']
            elif not base_buffer_full and data['frame'] <= (init_frame_base + tset['f0_win']):
                baseval += unit_vals / tset['f0_win']
                if data['frame'] == (init_frame_base + tset['f0_win']):
                    base_buffer_full = True
            else:
                baseval = (baseval * (tset['f0_win'] - 1) + unit_vals) / tset['f0_win']
            
            data['baseVector'][:, data['frame'] - 1] = baseval
            
            # Smooth F
            fsmooth = np.nanmean(fbuffer, axis=1).astype(np.float32)

            if base_buffer_full:
                # Calculate (smoothed) DFF
                dff = (fsmooth - baseval) / baseval
                # Passing smoothed dff to "decoder"
                dff2cursor_data = dff2cursor_target(dff, target_info, tset['cursor_zscore_bool'])
                cursor_i = dff2cursor_data[1]
                target_hit = dff2cursor_data[2]
                data['cursor'][0, data['frame'] - 1] = cursor_i
            
            if buffer_update_counter == 0 and base_buffer_full:
                if trial_flag and not back2base_flag:
                    data['trialStart'][0, data['frame'] - 1] = 1
                    data['trialCounter'] += 1
                    trial_flag = 0
                
                if back2base_flag:
                    if data['cursor'][0, data['frame'] - 1] <= back2base:
                        back2base_counter += 1
                    if back2base_counter >= tset['back2BaseFrameThresh']:
                        back2base_flag = 0
                        back2base_counter = 0
                else:
                    if target_hit:
                        data['selfTargetCounter'] += 1
                        data['selfHits'][0, data['frame'] - 1] = 1
                        buffer_update_counter = relaxation_frames
                        back2base_flag = 1
                        trial_flag = 1
            else:
                if buffer_update_counter > 0:
                    buffer_update_counter -= 1
        else:
            if non_buffer_update_counter > 0:
                non_buffer_update_counter -= 1
        
        data['frame'] += 1
    return data