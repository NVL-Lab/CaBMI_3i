from datetime import datetime

def get_exp_info(exp_type: str = '3i') -> dict:
    # Experiment directories
    exp_info = {
        'animal': 'mouse0',  # ago23
        'day': 'D0',  # DF
        'date': 260124, #datetime.today().strftime('%y%m%d'),
        'expt': 'bmi_stim'  # bmi_stim
    }

    if exp_type == '3i':
        exp_info['save_base_dir'] = 'F:cabmi/bmi_test'
        exp_info['sldy_dir'] = 'F:cabmi/bmi_test/slidebook'
        exp_info['sldy_name'] = 'capture_slide.sldy'
        exp_info['recording_3i_dir'] = ''
        exp_info['recording_onedrive_mac_dir'] = ''
        exp_info['recording_onedrive_win_dir'] = ''
    elif exp_type == 'testing':
        exp_info['save_base_dir'] = '~/Downloads/bmi_test'
        exp_info['sldy_dir'] = '~/Downloads/slidebook'
        exp_info['sldy_name'] = 'capture_slide.sldy'
        exp_info['recording_3i_dir'] = 'F:/cabmi_rg_pmts/bmi_test/slidebook/capture_slide.dir/capture_test-1768411287-992.imgdir/ImageData_Ch1_TP0000000.npy'
        exp_info['recording_onedrive_mac_dir'] = '/Users/saulglopez/Library/CloudStorage/OneDrive-UAB-TheUniversityofAlabamaatBirmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.dir/Capture 2-1721345967-598.imgdir/quality_ImageData_Ch0_TP0000000.npy'
        exp_info['recording_onedrive_win_dir'] = 'C:/Users/Saul/OneDrive - UAB - The University of Alabama at Birmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.dir/Capture 2-1721345967-598.imgdir/quality_ImageData_Ch0_TP0000000.npy'

    return exp_info