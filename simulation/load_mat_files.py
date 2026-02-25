from scipy.io import loadmat
from pathlib import Path

def load_target_info(task_set, exp_info):
    target_info_mat = loadmat(Path(exp_info['bmi_mat']).expanduser().resolve())
    # Those transversed were vertical arrays in matlab
    target_info = {
        'e1_base': target_info_mat['bData']['E1_base'][0][0][0] - 1,
        'e2_base': target_info_mat['bData']['E2_base'][0][0][0] - 1,
        'e_id': target_info_mat['bData']['E_id'][0][0].T[0],
        'e1_sel_idxs': target_info_mat['bData']['E1_sel_idxs'][0][0].T[0] - 1,
        'e2_sel_idxs': target_info_mat['bData']['E1_sel_idxs'][0][0].T[0] - 1,
        'decoder': target_info_mat['bData']['decoder'][0][0].T[0],
        'n_mean': target_info_mat['bData']['n_mean'][0][0][0],
        'n_std': target_info_mat['bData']['n_std'][0][0][0],
        'e1_std': target_info_mat['bData']['E1_std'][0][0][0][0],
        'e2_subord_mean': target_info_mat['bData']['E2_subord_thresh'][0][0].T[0],
        'e2_subord_std': target_info_mat['bData']['E2_subord_std'][0][0].T[0],
        'e2_coeff': target_info_mat['bData']['E2_coeff'][0][0][0][0],
        'e2_subord_thresh': target_info_mat['bData']['E2_subord_thresh'][0][0].T[0],
        'e1_coeff': target_info_mat['bData']['E1_coeff'][0][0][0][0],
        'e1_thresh': target_info_mat['bData']['E1_thresh'][0][0][0][0],
        't1': target_info_mat['bData']['T1'][0][0][0][0],

        'bmi_act': target_info_mat['data']['bmiAct'][0][0]
    }
    # target_info['e1_base'] -= 1
    # target_info['e2_base'] -= 1
    # target_info['e1_sel_idxs'] -= 1
    # target_info['e2_sel_idxs'] -= 1
    task_set = get_task_updates(task_set)
    return target_info, task_set

def load_base_activity(task_set, exp_info):
    bdata_mat = loadmat(Path(exp_info['bdata_mat']).expanduser().resolve())
    base_activity = bdata_mat['baseActivity']
    task_set = get_task_updates(task_set)
    return base_activity, task_set

def load_roi_info(task_set, exp_info):
    roi_data_mat = loadmat(Path(exp_info['roi_data_mat']).expanduser().resolve())
    if roi_data_mat['roi_data']['chan'][0][0]['label'][0][0][0].size == 0:
        chan_label = ''
    else:
        chan_label = roi_data_mat['roi_data']['chan'][0][0]['label'][0][0][0]

    roi_info = {
        'im_sc_struct': {
            'im': roi_data_mat['im_sc_struct']['im'][0][0],  # 512x512
            'minmax_perc': roi_data_mat['im_sc_struct']['minmax_perc'][0][0][0],
            'minmax': roi_data_mat['im_sc_struct']['minmax'][0][0][0],
            'min': roi_data_mat['im_sc_struct']['min'][0][0][0][0],
            'min_perc': roi_data_mat['im_sc_struct']['min_perc'][0][0][0][0],
            'max': roi_data_mat['im_sc_struct']['max'][0][0][0][0],
            'max_perc': roi_data_mat['im_sc_struct']['max_perc'][0][0][0][0]
        },
        'plot_images': {
            # this is structured different than original
            roi_data_mat['plot_images']['label'][0][0][0]: roi_data_mat['plot_images']['im'][0][0],
            roi_data_mat['plot_images']['label'][0][1][0]: roi_data_mat['plot_images']['im'][0][1]
        },
        'roi_data': {
            'num_chan': roi_data_mat['roi_data']['num_chan'][0][0][0][0],
            'im_bg': roi_data_mat['roi_data']['im_bg'][0][0],
            'num_rows': roi_data_mat['roi_data']['num_rows'][0][0][0][0],
            'num_cols': roi_data_mat['roi_data']['num_cols'][0][0][0][0],
            'num_rois': roi_data_mat['roi_data']['num_rois'][0][0][0][0],
            'roi_mask': roi_data_mat['roi_data']['roi_mask'][0][0],
            'roi_mask_bin': roi_data_mat['roi_data']['roi_mask'][0][0],
            'roi_bin_cell': roi_data_mat['roi_data']['roi_bin_cell'][0][0][0],
            'chan_logical': roi_data_mat['roi_data']['chan_logical'][0][0],
            'x': roi_data_mat['roi_data']['x'][0][0][0],
            'y': roi_data_mat['roi_data']['y'][0][0][0],
            'r': roi_data_mat['roi_data']['r'][0][0][0],
            'im_roi': roi_data_mat['roi_data']['im_roi'][0][0],
            'im_roi_rg': roi_data_mat['roi_data']['im_roi_rg'][0][0],
            'chan': {
                chan_label: {
                    'num_rois': roi_data_mat['roi_data']['chan'][0][0]['num_rois'][0][0][0][0],
                    'idxs': roi_data_mat['roi_data']['chan'][0][0]['idxs'][0][0][0],
                    'im_roi': roi_data_mat['roi_data']['chan'][0][0]['im_roi'][0][0],
                    'roi_mask': roi_data_mat['roi_data']['chan'][0][0]['roi_mask'][0][0],
                    'roi_mask_bin': roi_data_mat['roi_data']['chan'][0][0]['roi_mask_bin'][0][0]
                },
                roi_data_mat['roi_data']['chan'][0][0]['label'][0][1][0]: {
                    'num_rois': roi_data_mat['roi_data']['chan'][0][0]['num_rois'][0][1][0][0],
                    'idxs': roi_data_mat['roi_data']['chan'][0][0]['idxs'][0][1][0],
                    'im_roi': roi_data_mat['roi_data']['chan'][0][0]['im_roi'][0][1],
                    'roi_mask': roi_data_mat['roi_data']['chan'][0][0]['roi_mask'][0][1],
                    'roi_mask_bin': roi_data_mat['roi_data']['chan'][0][0]['roi_mask_bin'][0][1]
                },
                # 'roi_mask': roi_data_mat['roi_mask']
            }
        },
        'roi_mask': roi_data_mat['roi_mask']
    }
    task_set = get_task_updates(task_set)

    return roi_info, task_set

def load_roi_bg(task_set, exp_info):
    roi_data_mat = loadmat(Path(exp_info['roi_data_mat']).expanduser().resolve())
    task_set = get_task_updates(task_set)
    return roi_data_mat['im_sc_struct']['im'][0][0], task_set

def get_task_updates(task_set):
    task_set['f0_win'] = 1800  # for mat sim
    task_set['im']['chan_data']['R PMT'] = 0
    task_set['roi']['capture'] = 0

    # task_set['cb']['baseline_len'] = 45 * 60
    task_set['cb']['baseline_frames'] = 80971
    task_set['cb']['baseline_capture'] = 1

    return task_set

def load_mats(task_set, exp_info):
    # load here to check everything
    roi_data_mat = loadmat(Path(exp_info['roi_data_mat']).expanduser().resolve())
    if roi_data_mat['roi_data']['chan'][0][0]['label'][0][0][0].size == 0:
        chan_label = ''
    else:
        chan_label = roi_data_mat['roi_data']['chan'][0][0]['label'][0][0][0]

    roi_info = {
        'im_sc_struct': {
            'im': roi_data_mat['im_sc_struct']['im'][0][0],  # 512x512
            'minmax_perc': roi_data_mat['im_sc_struct']['minmax_perc'][0][0][0],
            'minmax': roi_data_mat['im_sc_struct']['minmax'][0][0][0],
            'min': roi_data_mat['im_sc_struct']['min'][0][0][0][0],
            'min_perc': roi_data_mat['im_sc_struct']['min_perc'][0][0][0][0],
            'max': roi_data_mat['im_sc_struct']['max'][0][0][0][0],
            'max_perc': roi_data_mat['im_sc_struct']['max_perc'][0][0][0][0]
        },
        'plot_images': {
            # this is structured different than original
            roi_data_mat['plot_images']['label'][0][0][0]: roi_data_mat['plot_images']['im'][0][0],
            roi_data_mat['plot_images']['label'][0][1][0]: roi_data_mat['plot_images']['im'][0][1]
        },
        'roi_data': {
            'num_chan': roi_data_mat['roi_data']['num_chan'][0][0][0][0],
            'im_bg': roi_data_mat['roi_data']['im_bg'][0][0],
            'num_rows': roi_data_mat['roi_data']['num_rows'][0][0][0][0],
            'num_cols': roi_data_mat['roi_data']['num_cols'][0][0][0][0],
            'num_rois': roi_data_mat['roi_data']['num_rois'][0][0][0][0],
            'roi_mask': roi_data_mat['roi_data']['roi_mask'][0][0],
            'roi_mask_bin': roi_data_mat['roi_data']['roi_mask'][0][0],
            'roi_bin_cell': roi_data_mat['roi_data']['roi_bin_cell'][0][0][0],
            'chan_logical': roi_data_mat['roi_data']['chan_logical'][0][0],
            'x': roi_data_mat['roi_data']['x'][0][0][0],
            'y': roi_data_mat['roi_data']['y'][0][0][0],
            'r': roi_data_mat['roi_data']['r'][0][0][0],
            'im_roi': roi_data_mat['roi_data']['im_roi'][0][0],
            'im_roi_rg': roi_data_mat['roi_data']['im_roi_rg'][0][0],
            'chan': {
                chan_label: {
                    'num_rois': roi_data_mat['roi_data']['chan'][0][0]['num_rois'][0][0][0][0],
                    'idxs': roi_data_mat['roi_data']['chan'][0][0]['idxs'][0][0][0],
                    'im_roi': roi_data_mat['roi_data']['chan'][0][0]['im_roi'][0][0],
                    'roi_mask': roi_data_mat['roi_data']['chan'][0][0]['roi_mask'][0][0],
                    'roi_mask_bin': roi_data_mat['roi_data']['chan'][0][0]['roi_mask_bin'][0][0]
                },
                roi_data_mat['roi_data']['chan'][0][0]['label'][0][1][0]: {
                    'num_rois': roi_data_mat['roi_data']['chan'][0][0]['num_rois'][0][1][0][0],
                    'idxs': roi_data_mat['roi_data']['chan'][0][0]['idxs'][0][1][0],
                    'im_roi': roi_data_mat['roi_data']['chan'][0][0]['im_roi'][0][1],
                    'roi_mask': roi_data_mat['roi_data']['chan'][0][0]['roi_mask'][0][1],
                    'roi_mask_bin': roi_data_mat['roi_data']['chan'][0][0]['roi_mask_bin'][0][1]
                },
            #'roi_mask': roi_data_mat['roi_mask']
            }
        },
        'roi_mask': roi_data_mat['roi_mask']
    }

    bdata_mat = loadmat(Path(exp_info['bdata_mat']).expanduser().resolve())
    bdata = bdata_mat['baseActivity']

    target_info_mat = loadmat(Path(exp_info['bmi_mat']).expanduser().resolve())
    # Those transversed were vertical arrays in matlab
    target_info = {
        'e1_base': target_info_mat['bData']['E1_base'][0][0][0]-1,
        'e2_base': target_info_mat['bData']['E2_base'][0][0][0]-1,
        'e_id': target_info_mat['bData']['E_id'][0][0].T[0],
        'e1_sel_idxs': target_info_mat['bData']['E1_sel_idxs'][0][0].T[0]-1,
        'e2_sel_idxs': target_info_mat['bData']['E1_sel_idxs'][0][0].T[0]-1,
        'decoder': target_info_mat['bData']['decoder'][0][0].T[0],
        'n_mean': target_info_mat['bData']['n_mean'][0][0][0],
        'n_std': target_info_mat['bData']['n_std'][0][0][0],
        'e1_std': target_info_mat['bData']['E1_std'][0][0][0][0],
        'e2_subord_mean': target_info_mat['bData']['E2_subord_thresh'][0][0].T[0],
        'e2_subord_std': target_info_mat['bData']['E2_subord_std'][0][0].T[0],
        'e2_coeff': target_info_mat['bData']['E2_coeff'][0][0][0][0],
        'e2_subord_thresh': target_info_mat['bData']['E2_subord_thresh'][0][0].T[0],
        'e1_coeff': target_info_mat['bData']['E1_coeff'][0][0][0][0],
        'e1_thresh': target_info_mat['bData']['E1_thresh'][0][0][0][0],
        't1': target_info_mat['bData']['T1'][0][0][0][0],

        'bmi_act': target_info_mat['data']['bmiAct'][0][0]
    }
    #target_info['e1_base'] -= 1
    #target_info['e2_base'] -= 1
    #target_info['e1_sel_idxs'] -= 1
    #target_info['e2_sel_idxs'] -= 1

    task_set['f0_win'] = 1800 # for mat sim
    task_set['im']['chan_data']['R PMT'] = 0
    task_set['roi']['capture'] = 0

    # task_set['cb']['baseline_len'] = 45 * 60
    task_set['cb']['baseline_frames'] = 80971
    task_set['cb']['baseline_capture'] = 1

    return roi_info, bdata, target_info, task_set