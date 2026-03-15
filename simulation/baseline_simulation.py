import numpy as np
import time
from datetime import datetime

from rois.obtain_strc_mask_from_mask import obtain_strc_mask_from_mask
from rois.obtain_roi import get_roi
from params.play_tone import play_tone

def baseline_acqnvs_sim_3i(roi_mask, task_set, path_data):
    base_name = 'baseline_online'
    dilation_factor = 1  # 2
    task_set['cb']['baseline_frames'] = int(np.ceil(task_set['cb']['baseline_len'] * task_set['im']['frame_rate'] * dilation_factor))

    if task_set['expt']['baseline']['load']:
        try:
            matches = [path for path in path_data['save_path'].rglob('*') if base_name in path.name]
            base_activity = np.load(matches[-1], allow_pickle=True)
            print(f'Loading {matches[-1].name}...')
            return base_activity, task_set
        except FileNotFoundError:
            print('ROI data not found. Please run roi_acqnvs_3i')
            exit(1)

    bdata_path = path_data['save_path'] / f'{base_name}_{datetime.now().strftime("%y%m%dt%H%M%S")}.npy'

    record_raw = np.load(path_data['test_dir'], mmap_mode='r')
    record_frames = task_set['cb']['baseline_frames']
    record_frame_limit = task_set['roi']['recording_frames']+record_frames
    record = record_raw[task_set['roi']['recording_frames']-1:record_frame_limit]

    task_set['im']['resolution'] = (record.shape[2], record.shape[1])

    number_neurons = int(np.max(roi_mask))
    strc_mask = obtain_strc_mask_from_mask(roi_mask)
    base_activity = np.full((number_neurons, record_frames), np.nan)
    frame_counter = 0
    frame_interval = 1 / (task_set['im']['frame_rate'] * 1.2)
    total_process_time = 0

    print('STARTING RETRIEVAL!!!')
    print('Retrieving...')
    for frame in range(record_frames):
        image = record[frame]
        start_time = time.perf_counter()

        # Store ROI data
        unit_vals = get_roi(image, strc_mask)
        base_activity[:, frame_counter] = unit_vals
        frame_counter += 1
        #print(f'*** Frames captured: {frame_counter}')

        elapsed_time = time.perf_counter() - start_time
        total_process_time += elapsed_time
        #print(f'Execution time: {elapsed_time} seconds')

        if elapsed_time < frame_interval:
            time.sleep(frame_interval - elapsed_time)

    print('Finished baseline acquisition')
    print('Total processing time: {:.2f} seconds'.format(total_process_time))
    play_tone(7000, 1)

    if task_set['expt']['baseline']['save']:
        print(f'Saving baseline data to {bdata_path}...')
        np.save(bdata_path, base_activity, allow_pickle=True)

    return base_activity, task_set
