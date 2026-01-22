#from datetime import datetime

def get_exp_info() -> dict:
    return {
        # Actual directories
        'save_base_dir': 'F:cabmi/bmi_test',
        'sldy_dir': 'F:cabmi/bmi_test/slidebook',
        'sldy_name': 'capture_slide.sldy',

        # Test directories
        'testing': {
            '3i_drive':{
                'rg_pmts':'F:/cabmi_rg_pmts/bmi_test/slidebook/capture_slide.dir/capture_test-1768411287-992.imgdir/ImageData_Ch1_TP0000000.npy'
            },
            'onedrive': {
                'mac_dir': '/Users/saulglopez/Library/CloudStorage/OneDrive-UAB-TheUniversityofAlabamaatBirmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.dir/Capture 2-1721345967-598.imgdir/quality_ImageData_Ch0_TP0000000.npy',
                'win_dir': 'C:/Users/Saul/OneDrive - UAB - The University of Alabama at Birmingham/Research/NVL (Llopis)/3i/test_results/Slide3-testing.dir/Capture 2-1721345967-598.imgdir/quality_ImageData_Ch0_TP0000000.npy'
            }
        },

        # Experiment directories
        'animal': 'mouse0', # ago23
        'day': 'D0',        # DF
        'date': '040925',   # datetime.today().strftime('%d%m%y') 230423
        'expt': 'bmi_stim'  # bmi_stim
    }
