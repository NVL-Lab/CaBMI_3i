from datetime import datetime

def get_exp_info(exp_type: str = '') -> dict:
    # Experiment directories
    exp_info = {
        'animal': 'mouse0',
        'day': 'D0',
        'date': 260317,#datetime.today().strftime('%y%m%d'),
        'expt': 'bmi_stim'
    }

    if exp_type == 'sim':
        exp_info['save_base_dir'] = '~/Downloads/bmi_sim'
        exp_info['recording_3i_dir'] = 'F:/cabmi_rg_pmts/bmi_test/slidebook/capture_slide.dir/capture_test-1768411287-992.imgdir/ImageData_Ch1_TP0000000.npy'
        exp_info['recording_onedrive_mac_dir'] = '/Users/saulglopez/Library/CloudStorage/OneDrive-UAB-TheUniversityofAlabamaatBirmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.dir/Capture 2-1721345967-598.imgdir/quality_ImageData_Ch0_TP0000000.npy'
        exp_info['recording_onedrive_win_dir'] = 'C:/Users/Saul/OneDrive - UAB - The University of Alabama at Birmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.dir/Capture 2-1721345967-598.imgdir/quality_ImageData_Ch0_TP0000000.npy'
    elif exp_type == 'sim_mat':
        exp_info['save_base_dir'] = '~/Downloads/bmi_sim_mat'
        exp_info['roi_data_mat'] = '~/Scripts/uab/nvl_lab/CaBMI/data/HoloBMI/Raw/190930/NVI12/D5/roi_data.mat'
        exp_info['bdata_mat'] = '~/Scripts/uab/nvl_lab/CaBMI/data/HoloBMI/Raw/190930/NVI12/D5/BaselineOnline190930T132923.mat'
        exp_info['bmi_mat'] = '~/Scripts/uab/nvl_lab/CaBMI/data/HoloBMI/Raw/190930/NVI12/D5/BMI_online190930T152419.mat'
    else:
        exp_info['save_base_dir'] = 'F:cabmi/bmi_test'
        exp_info['sldy_name'] = f'{exp_info["animal"]}_{exp_info["date"]}'

    return exp_info