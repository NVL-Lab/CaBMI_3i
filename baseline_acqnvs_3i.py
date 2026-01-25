from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from wait_on_task_3i import *
from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from params.play_tone import play_tone
from recording_acqnvs_3i import recording_acqnvs_3i, baseline_acqnvs_sim_3i

def baseline_acqnvs_3i(task_set, path_data, roi_mask, default_run=False, run=False, sim=False):
    # Save path
    base_name = 'baseline_online'
    dilation_factor = 1 # 2
    task_set['cb']['baseline_frames'] = int(np.ceil(task_set['cb']['baseline_len'] * task_set['im']['frame_rate'] * dilation_factor))
    print(f'Baseline recording will consist of {task_set["cb"]["baseline_frames"]} frames')

    if not run:
        if sim:
            recording_path = path_data['test_dir']
            bdata = baseline_acqnvs_sim_3i(roi_mask, task_set, recording_path)
            print('Simulating baseline data...')
        else:
            try:
                matches = [path for path in path_data['save_path'].rglob('*') if base_name in path.name]
                bdata = np.load(matches[-1], allow_pickle=True)
                print(f'Loading {matches[-1].name}...')
            except FileNotFoundError:
                print('Baseline data not found. Please run baseline_acqnvs_3i.')
                exit(1)
        return bdata

    # Creates an instance of slidebook reader
    sb_file_reader, task_set['cb']['baseline_capture'] = wait_for_reader_with_latest_capture(path_data['sldy_path'])
    task_set = get_recording_settings(sb_file_reader, task_set['roi']['capture'], task_set, default_run)
    bdata_path = path_data['save_path'] / f'{base_name}_{datetime.now().strftime("%y%m%dt%H%M%S")}.npy'

    save_path_expt = path_data['save_path'] / 'im' / 'baseline'
    if task_set['save']:
        save_path_expt.mkdir(parents=True, exist_ok=True)

    # Initialize baseline variables
    number_neurons = int(np.max(roi_mask))
    strc_mask = obtain_strc_mask_from_mask(roi_mask)
    base_activity = np.full((number_neurons, task_set['cb']['baseline_frames']), np.nan)
    base_activity, task_set = recording_acqnvs_3i(base_activity, task_set['cb']['baseline_frames'], task_set, sb_file_reader, bdata_path, task_set['cb']['baseline_capture'], {'type': 'baseline', 'strc_mask': strc_mask})

    print('Finished baseline acquisition')
    play_tone(7000, 1)
    return base_activity, task_set