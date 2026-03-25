def get_fb_settings(tlf=True, fmin=6000, fmax=19000) -> dict:
    '''
        Added 11.5.19 to have feedback dependent on E1, E2 state
        target_buffer: how much frequency separation there should be between
        feedback for target achievement vs intermediate feedback
        The following frequencies are arbitrarily decided, could be chosen with principle
    '''
    if tlf:
        tfb = 1000
        tfnt = fmin+tfb
        tfe1s = 9000
    else:
        tfb = 2000
        tfnt = fmax-tfb
        tfe1s = 15000

    return {
        'fb_bool': True,           # True: feedback, 0: silence
        'target_low_freq': tlf,
        
        #Set the target cursor value to be the low frequency
        'freq_min': 6000,
        'freq_max': 19000,
        'min_perctile': 90,
        'target_freq_buffer': tfb,
        'trunc_freq_non_target':tfnt,
        'trunc_freq_E1_state': tfe1s,
        'arduino':{
            'com': 'COM11', #'COM15'
            'baudrate': 115200,
            'label': 'Uno',     # Might not be necessary in Python arduino module
            'pin': 'D11',
            'duration': 0.3     # ms, tones update at rate of BMI code, this is the longest a tone will play for
        },

        # Added by Nuria to solve an error:
        'lambda_e2_e1': 0.5,
        'lambda_e1': 0.25,
        'lambda_e2': 0.25,

        'min_prctile': 10,      # The lowest percentile allowed for E2 minus E1
        'max_prctile':100,      # The lowest percentile allowed for E2 minus E1
        'middle_prctile': 50,
        'obj_max_perctile': 90
    }
