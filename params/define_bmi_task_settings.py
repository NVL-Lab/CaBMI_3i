from typing import Tuple, Dict
from pathlib import Path
import math 

def get_bmi_settings(save: bool = False, fr: float = 38.6, res: Tuple[int, int] = (403, 390)) -> Dict:
    #fr = 29.752 # Prairie
    return {
        'baseline_env': Path('utils/Tseries_baseline_15.env'),
        'bmi_env': Path('utils/Tseries_BMI_30.env'),
        'save': save,

        # Imaging
        'im': {
            'resolution': res,    # Standard, but subject to change based on microscope operation
            'frame_rate': fr,
            'zoom': 1.5,          # Zoom to obtain cells
            'posz': 0,            # Position of Z if known
            'chan_data': {
                'recording_chan': 'R PMT' # Standard, but subject to change based on microscope operation
            }
        },

        # Regions of Interest (ROIs)
        'roi': {
            'recording_len': 60,  # sec
            'template_diam': 3,  # Diameter of difference of Gaussians in pixels
            'thres': 0.5,        # Cell detection threshold as correlation coefficient
            'cell_diam': 17,     # CELL_DIAM is diameter used for dilation.
            'finemode': 1,       # imTemplateMatch will be used instead of normxcorr2. It will be slower.
            'temmode': True      # false is for full circle (soma); true is for donuts (membrane)
        },

        # Calibration
        'cb': {
            'sec_per_reward_range': [70, 50], # [100 70]; [120 90] a range on how many frames (per sec) should elapse before a reward is expected.  Used to calibrate the target patterns.
            'baseline_len': 10*60,          # Seconds (15*60) #20
            'f0_win_bool': True,      # During cb, if true, estimate f0 with a window of activity.  if false, estimate f0 using the full baseline,
            'dff_win_bool': True,
            'f0_init_slide': False,   # During cb, if 0, f0 is only used after f0_win samples. If 1, f0 is adapted in the window from 0 to f0_win samples.
            'e2me1_prctile': 98       # It is the lowest acceptable E2mE1_prctile for deciding the target threshold.
        },

        # Random Stim
        'rs': {
            'ihsi_mean': 60,
            'ihsi_range': 55
        },

        # BMI
        'bmi_len': 10*60, # Seconds (30x60)
        'prefix_win': 40,
        'f0_win': 1*60*math.ceil(fr),
        'dff_win': 10, # dff is calculated with last n frames
        'range_norm_bool': True,
        'cursor_zscore_bool': False,
        'reward_delay_frames': 10,
        'back2base_frame_thresh': 2,   #2 frames of back2base
        'relaxation_time': 0,         #1 Period after a hit to stop the BMI (there can't be another hit in this many sec)
        'b2base_coeff': 0.5,

        # Stim Delay
        'delay_flag': 0,
        'delay_time': 1  # Seconds 
    }

'''
        # Imaging
        'im': {
            'resolution': res,
            'frame_rate': fr,
            'zoom': 1.5,          # Zoom to obtain cells
            'posz': 0,            # Position of Z if known
            'chan_data': {
                'green': {
                    'label': 'g',
                    'fp_idx': 0#, # in windows its 0; last time 1
                    #'pmt_idx': 1 #0 if capture with red # ChannelRecord.yaml has info about PMT type but only comes after start
                },
                'red': {
                    'label': 'r',
                    'fp_idx': 1#, #0
                    #'pmt_idx': 0
                }
            }
        },
'''