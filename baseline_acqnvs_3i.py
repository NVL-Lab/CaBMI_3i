from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from wait_on_task_3i import *
from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from params.play_tone import play_tone
from recording_acqnvs_3i import recording_acqnvs_3i, baseline_acqnvs_sim_3i

@contextmanager
def on_cleanup(bdata_path, base_activity):
    try:
        yield
    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    finally:
        print('Cleaning...')
        # consider storing everything under an npz
        #np.save(bdata_path, base_activity, allow_pickle=True)

def baseline_acqnvs_3i(task_set, path_data, roi_mask, default_run=False, run=False, sim=False) -> np.ndarray:
    # Save path
    base_name = 'baseline_online'
    if not run:
        try:
            if sim:
                recording_path = Path(path_data['test_dir'])
                bdata = baseline_acqnvs_sim_3i(roi_mask, task_set, recording_path)
                print('Simulating baseline data...')
            else:
                matches = [path for path in path_data['save_path'].rglob('*') if base_name in path.name]
                bdata = np.load(matches[-1], allow_pickle=True)
                print(f'Loading {matches[-1].name}...')
            return bdata
        except FileNotFoundError:
            print('Baseline data not found. Please run baseline_acqnvs_3i.')
            exit(1)

    # Creates an instance of slidebook reader
    sb_file_reader, task_set['cb']['baseline_capture'] = wait_for_reader_with_latest_capture(path_data['sldy_path'])
    task_set = get_recording_settings(sb_file_reader, task_set['roi']['capture'], task_set, default_run)
    bdata_path = path_data['save_path'] / f'{base_name}_{datetime.now().strftime("%y%m%dt%H%M%S")}.npy'

    save_path_expt = path_data['save_path'] / 'im' / 'baseline'
    if task_set['save']:
        save_path_expt.mkdir(parents=True, exist_ok=True)

    dilation_factor = 1 # 2
    #expected_length = int(np.ceil(task_set['cb']['baseline_len'] * task_set['im']['frame_rate'] * dilation_factor))
    task_set['cb']['baseline_frames'] = 1100

    # Initialize baseline variables
    number_neurons = int(np.max(roi_mask))
    strc_mask = obtain_strc_mask_from_mask(roi_mask)
    base_activity = np.full((number_neurons, task_set['cb']['baseline_frames']), np.nan)
    base_activity = recording_acqnvs_3i(base_activity, task_set['cb']['baseline_frames'], task_set, sb_file_reader, bdata_path, task_set['cb']['baseline_capture'], {'type': 'baseline', 'strc_mask': strc_mask})

    print('Finished baseline acquisition')
    play_tone(7000, 1)
    return base_activity