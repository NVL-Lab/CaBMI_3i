from pathlib import Path
import math 

def get_bmi_settings(fr = 29.752) -> dict:
    # Prairie: 29.752
    return {
        #'baseline_env': Path('~/Scripts/uab/nvl_lab/CaBMI-3i/utils/Tseries_baseline_15.env'),
        #'bmi_env': Path('~/Scripts/uab/nvl_lab/CaBMI-3i/utils/Tseries_BMI_30.env'),
        'baseline_env': Path('utils/Tseries_baseline_15.env'),
        'bmi_env': Path('utils/Tseries_BMI_30.env'),

        # Imaging
        'im': {
            'frame_rate': fr,     # Copy from PrairieValue (might change with 3i)
            'zoom': 1.5,          # Zoom to obtain cells
            'posz': 0,            # Position of Z if known
            'chan_data': {        # RGB; G is 1st and R is 2nd
                'label': 'g',
                'chan_idx': 0 #2
            }                 
        },

        # Regions of Interest (ROIs)
        'roi': {
            'template_diam': 3,  # Diameter of difference of Gaussians in pixels
            'thres': 0.5,         # Cell detection threshold as correlation coefficient
            'cell_diam': 17,       # CELL_DIAM is diameter used for dilation.
            'finemode': 1,       # imTemplateMatch will be used instead of normxcorr2. It will be slower.
            'temmode': True      # false is for full circle (soma); true is for donuts (membrane)
        },

        # Calibration
        'cb': {
            'sec_per_reward_range': [70, 50], # [100 70]; [120 90] a range on how many frames (per sec) should elapse before a reward is expected.  Used to calibrate the target patterns.
            'baseline_len': 5*60,          # Seconds (15*60)
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
        'relaxationTime': 0,         # Period after a hit to stop the BMI
        'b2base_coeff': 0.5,

        # Stim Delay
        'delay_flag': 0,
        'delay_time': 1  # Seconds 
    }
