from datetime import datetime


def get_exp_info(protocol: str = 'bmi', user: str = None) -> dict:
    # Experiment directories
    exp_info = {
        'user': user,
        'project': 'PFF',
        'animal': 'mouse0',
        'experiment': protocol, # 'bmi_stim'
        'date': datetime.today().strftime('%Y%m%d'),
        'day': 'D0',

        #'sldy_dir': '~/Downloads/bmi_sim',
    }

    # exp_info['recording_3i_dir'] = 'F:/cabmi_rg_pmts/bmi_test/slidebook/capture_slide.dir/capture_test-1768411287-992.imgdir/ImageData_Ch1_TP0000000.npy'
    if protocol == 'sim_3i_onedrive_win':
        exp_info['recording'] = 'C:/Users/Saul/OneDrive - UAB - The University of Alabama at Birmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.dir/Capture 2-1721345967-598.imgdir/quality_ImageData_Ch0_TP0000000.npy'
    if protocol == 'sim_3i_onedrive_mac':
        exp_info['recording'] = '/Users/saulglopez/Library/CloudStorage/OneDrive-UAB-TheUniversityofAlabamaatBirmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.dir/Capture 2-1721345967-598.imgdir/quality_ImageData_Ch0_TP0000000.npy'
    elif protocol == 'sim_bruker':
        exp_info['roi_data_mat'] = '~/Scripts/uab/nvl_lab/CaBMI/data/HoloBMI/Raw/190930/NVI12/D5/roi_data.mat'
        exp_info['bdata_mat'] = '~/Scripts/uab/nvl_lab/CaBMI/data/HoloBMI/Raw/190930/NVI12/D5/BaselineOnline190930T1show32923.mat'
        exp_info['bmi_mat'] = '~/Scripts/uab/nvl_lab/CaBMI/data/HoloBMI/Raw/190930/NVI12/D5/BMI_online190930T152419.mat'
    elif protocol == 'bmi':
        exp_info['save_base_dir'] = 'F:/cabmi/bmi_test2'
        if user:
            exp_info['sldy_name'] = (
                f'{exp_info["date"]}_{exp_info["animal"]}_'
                f'{exp_info["experiment"]}_{exp_info["user"]}.sldy'
            )
        else:
            exp_info['sldy_name'] = f'{exp_info["animal"]}_{exp_info["date"]}.sldy'
    else:
        raise ValueError(f"Unknown experiment type: {protocol}")

    return exp_info