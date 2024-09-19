import os
import math 

def get_bmi_settings(fr=29.752) -> dict:
    return {
        'bl_env': os.path.join('E:','Nuria','utils', 'Tseries_baseline_15.env'),
        'bmi_env': os.path.join('E:','Nuria','utils', 'Tseries_BMI_30.env'),
        
        # Imaging
        'im': {
            'frame_rate': fr, # Value might change with 3i
            'zoom': 1.5,          # Zoom to obtain cells
            'posz': 0,            # Position of Z if known
            'chan_data': {        # RGB; G is 2nd
                'label': 'g',
                'chan_idx': 2
            }                 
        },

        # Regions of Interest (ROIs)
        'roi': {
            'template_diam': 11,  # Diamter of difference of Gaussians in pixels
            'thres': 0.4,         # Cell detection threshold as correlation coefficient
            'cell_diam': 7,       # CELL_DIAM is diameter used for dilation.
            'fine_mode': 1,       # imTemplateMatch will be used instead of normxcorr2. It will be slower.
            'tem_mode': True      # false is for full circle (soma); true is for donuts (membrane)
        },

        # Calibration
        'cb': {
            'reward_range': [70, 50], # [100 70]; [120 90] a range on how many frames (per sec) should elapse before a reward is expected.  Used to calibrate the target patterns.
            'bl_len': 15*60,          # Seconds
            'f0_win_bool': True,      # During cb, if true, estimate f0 with a window of activity.  if false, estimate f0 using the full baseline,
            'dff_win_bool': True,
            'f0_init_slide': False,   # During cb, if 0, f0 is only used after f0_win samples. If 1, f0 is adapted in the window from 0 to f0_win samples.
            'E2mE1_prctile': 98       # It is the lowest acceptable E2mE1_prctile for deciding the target threshold.
        },

        # Random Stim
        'rs': {
            'ihsi_mean': 60,
            'ihsi_range': 55
        },

        # BMI
        'bmi_len': 30*60,            # Seconds
        'prefix_win': 40,
        'f0_win': 1*60*math.ceil(fr),
        'dff_win': 10,
        'range_norm': True,
        'cursor_zscore': False,
        'reward_delay_frames': 10,
        'back2BaseFrameThresh': 2,   #2 frames of back2base
        'relaxationTime': 0,         # Period after a hit to stop the BMI
        'b2base_coeff': 0.5,

    
        # Stim Delay
        'delay_flag': 0,
        'delay_time': 1  # Seconds 
    }
