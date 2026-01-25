import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import zscore
from scipy.signal import convolve
from rois.get_mask import get_mask
from .cursor2audio import cursor2audio
from plots.plot_cursor_e1_e2_activity import plot_cursor_e1_e2_activity
from plots.calc_psth import calc_psth
from datetime import datetime

# Define decoder (placeholders)
def def_decoder(num_neurons, e1_sel, e2_sel):
    e1_proj = np.zeros(num_neurons)
    e1_proj[e1_sel] = 1
    e1_norm = np.sum(e1_sel)  # Can replace with np.linalg.norm(E1_sel) if needed
    e1_proj /= e1_norm

    e2_proj = np.zeros(num_neurons)
    e2_proj[e2_sel] = 1
    e2_norm = np.sum(e2_sel)
    e2_proj /= e2_norm

    decoder = e2_proj - e1_proj
    return decoder, e1_proj, e2_proj, e1_norm, e2_norm

def define_fb_calibration(cursor_obs, fbset, t):
    fb_cal = {}

    fb_cal['settings'] = fbset

    # Calculate percentiles
    cursor_min = np.percentile(cursor_obs, fbset['min_perctile'])
    cursor_max = t
    cursor_range = cursor_max - cursor_min

    fb_cal['cursor_min'] = cursor_min
    fb_cal['cursor_max'] = cursor_max
    fb_cal['cursor_range'] = cursor_range

    # Calculate a and b
    a = fbset['freq_min']
    b = (np.log(fbset['freq_max']) - np.log(a)) / cursor_range

    fb_cal['a'] = a
    fb_cal['b'] = b

    return fb_cal

def baseline2target(f_base, roi_data, e1_base, e2_base, frames_per_reward_range, tset, save_path, fbset, run=False):
    fb_cal_name = 'fb_cal'
    cal_all_name = 'target_calibration_all'
    target_info_name = 'bmi_target_info'
    if not run:
        try:
            target_matches = [path for path in save_path.rglob('*') if target_info_name in path.name]
            cal_matches = [path for path in save_path.rglob('*') if cal_all_name in path.name]
            fb_matches = [path for path in save_path.rglob('*') if fb_cal_name in path.name]
            target_data = np.load(target_matches[-1], allow_pickle=True)
            cal_data = np.load(cal_matches[-1], allow_pickle=True)
            fb_data = np.load(fb_matches[-1], allow_pickle=True)
            print(f'Loading {target_matches[-1].name}, {cal_matches[-1].name}, and {fb_matches[-1].name}')
            return target_data, cal_data, fb_data
        except FileNotFoundError:
            print('Data not found. Please run baseline2target.')
            exit(1)

    # Define colors for plotting
    plot_b = (0, 0.4470, 0.7410)  # Blue-ish
    plot_o = (0.8500, 0.3250, 0.0980)  # Orange-ish
    e_color = [plot_b, plot_o]

    # Plot flags
    plot_raw_bool = True
    plot_f0_bool = True
    plot_smooth_bool = True
    plot_dff_bool = True
    plot_cov_bool = True

    # Define the path for saving plots
    plot_path = save_path / 'plots'

    # Create the directory if it does not exist
    if tset['save']:
        plot_path.mkdir(parents=True, exist_ok=True)

    # Load data
    #data = loadmat(n_f_file)
    #f_base = data['base_activity']
    f_base = np.delete(f_base, np.isnan(f_base[0, :]), axis=1).T  # Remove NaNs and transpose

    # Extract relevant columns for E1 and E2
    e1_temp = f_base[:, e1_base]
    e2_temp = f_base[:, e2_base]
    f = np.hstack((e1_temp, e2_temp))

    # Throw out prefix frames
    prefix_win = tset['prefix_win']
    #prefix_win = 5 # set fpr test
    e1_raw = f_base[prefix_win:, e1_base]
    e2_raw = f_base[prefix_win:, e2_base]
    f_raw = np.hstack((e1_raw, e2_raw))

    num_e1 = len(e1_base)
    num_e2 = len(e2_base)
    num_neurons = num_e1 + num_e2

    e_id = np.concatenate((np.ones(num_e1, dtype=int), np.ones(num_e2, dtype=int) * 2))
    e1_sel = (e_id == 1)
    e1_sel_idxs = np.where(e1_sel)[0]
    e2_sel = (e_id == 2)
    e2_sel_idxs = np.where(e2_sel)[0]

    # Load ROI data
    #roi_data = loadmat(roi_data_file)['roi_data']
    roi_mask = roi_data['roi_mask']

    ensemble_mask = np.zeros_like(roi_mask)
    for indn in range(num_e1):
        auxmask = np.where(roi_mask == e1_base[indn], indn + 1, 0)
        ensemble_mask += auxmask

    for indn in range(num_e2):
        auxmask = np.where(roi_mask == e2_base[indn], indn + num_e1 + 1, 0)
        ensemble_mask += auxmask

    strc_mask = get_mask(ensemble_mask)

    strc_info = {
        'strc_mask': strc_mask,
        'e_base_sel': np.hstack((e1_base, e2_base)),
        'e_id': e_id
    }

    if tset['save']:
        np.savez_compressed(save_path / 'strc_info.npz', **strc_info)

    decoder, e1_proj, e2_proj, e1_norm, e2_norm = def_decoder(num_neurons, e1_sel, e2_sel)

    # Process f0
    f0_win_bool = tset['cb']['f0_win_bool']
    f0_win = tset['f0_win'] #int(tset['roi']['recording_frames'] / 2) #tset['f0_win'] is correct
    f0_init_slide = tset['cb']['f0_init_slide']
    
    if f0_win_bool:
        num_samples = f_raw.shape[0]
        if f0_init_slide:
            f0 = np.zeros((num_samples, num_neurons))
            for i in range(num_samples):
                if i == 0:
                    f0[i, :] = f_raw[i, :]
                elif i < f0_win:
                    f0[i, :] = (f0[i-1, :] * (i-1) + f_raw[i, :]) / i
                else:
                    f0[i, :] = (f0[i-1, :] * (f0_win - 1) + f_raw[i, :]) / f0_win
        else:
            f0 = np.zeros((num_samples - f0_win + 1, num_neurons))
            f0[0, :] = np.mean(f_raw[:f0_win, :], axis=0)
            for i in range(1, len(f0)):
                f0[i, :] = f0[i-1, :] * ((f0_win - 1) / f0_win) + f_raw[i + f0_win - 1, :] / f0_win
        f_postf0 = f_raw[f0_win - 1:, :]
        f0_mean = np.nanmean(f_postf0, axis=0)
        f0_mean = np.tile(f0_mean, (f_postf0.shape[0], 1))
    else:
        f_postf0 = f_raw
        f0_mean = np.tile(np.nanmean(f_postf0, axis=0), (f_postf0.shape[0], 1))
        f0 = f0_mean

    # Plot raw data
    if plot_raw_bool:
        t_plot = np.arange(len(f_postf0))
        plt.figure()
        plt.plot(t_plot, f_postf0)
        plt.xlabel('frame')
        plt.ylabel('fluorescence')
        plt.title('Raw fluorescence in baseline')
        if tset['save']:
            plt.savefig(save_path/'plots'/'baseline_fraw.png')

    # Compare f0win to f0mean
    if plot_f0_bool:
        plt.figure()
        plt.plot(f_postf0[:, 0], label='fraw')
        plt.plot(f0_mean[:, 0], 'k', linewidth=5, label='f0mean')
        plt.plot(f0[:, 0], 'r', linewidth=5, label='f0win')
        plt.xlabel('frame')
        plt.ylabel('fluorescence')
        plt.title('F0 for one neuron')
        plt.legend()
        if tset['save']:
            plt.savefig(save_path/'plots'/'f0.png')

    # Smooth f
    dff_win_bool = tset['cb']['dff_win_bool']
    dff_win = tset['dff_win']
    
    if dff_win_bool:
        smooth_filt = np.ones(dff_win) / dff_win
        f_smooth = np.zeros_like(f_postf0)
        for i in range(num_neurons):
            f_smooth[:, i] = convolve(f_postf0[:, i], smooth_filt, mode='same')
    else:
        f_smooth = f_postf0

    # Plot smoothed data
    if plot_smooth_bool and dff_win_bool:
        plt.figure()
        plt.plot(f_postf0[:, 0], label='f')
        plt.plot(f_smooth[:, 0], label='f smooth')
        plt.xlabel('frame')
        plt.ylabel('F')
        plt.title('F vs smoothed F')
        plt.legend()
        if tset['save']:
            plt.savefig(f"{save_path}/plots/f_smooth.png")

    # Compute dff and dff_z
    dff = (f_smooth - f0) / f0
    dff_mean = np.nanmean(dff, axis=0)
    dff_centered = dff - dff_mean
    dff_std = np.nanstd(dff_centered, axis=0)
    dff_z = dff_centered / dff_std

    # Plot dff
    if plot_dff_bool:
        t_plot = np.arange(len(dff))
        plt.figure()
        plt.plot(t_plot, dff)
        plt.xlabel('frame')
        plt.ylabel('dff')
        plt.title('dff')
        if tset['save']:
            plt.savefig(f"{save_path}/plots/dff.png")

        plt.figure()
        plt.plot(t_plot, dff_z)
        plt.xlabel('frame')
        plt.ylabel('dff_z')
        plt.title('zscore dff')
        if tset['save']:
            plt.savefig(f"{save_path}/plots/dffz.png")

    # Analysis
    cursor_zscore_bool = tset['cursor_zscore_bool']
    n_analyze = dff_z if cursor_zscore_bool else dff
    valid_idxs = ~np.isnan(n_analyze[:, 0])
    n_analyze = n_analyze[valid_idxs, :]
    analyze_cov = np.cov(n_analyze, rowvar=False)
    analyze_mean = np.nanmean(n_analyze, axis=0)

    # Plot covariance
    if plot_cov_bool:
        plt.figure()
        plt.imshow(analyze_cov, cmap='viridis', aspect='auto')
        plt.colorbar()
        plt.title('Neural Covariance')
        if tset['save']:
            plt.savefig(f"{save_path}/plots/cov_mat_baseline.png")

        u, s, v = np.linalg.svd(analyze_cov)
        s_cumsum = np.cumsum(s) / np.sum(s)
        plt.figure()
        plt.plot(s_cumsum, '.-', markersize=20)
        plt.xlabel('PC')
        plt.ylabel('Fraction of Variance Explained')
        plt.title('DFF Smooth PCA Covariance')
        if tset['save']:
            plt.savefig(f"{save_path}/plots/cov_pca_baseline.png")

    # Cursor Cov
    cursor_cov = decoder.T @ analyze_cov @ decoder

    # Target calibration
    #min_prctile = tset['cb']['e2me1_prctile']
    #T0 = np.max(cursor_zscore_bool)  # Placeholder
    #min_set = T0 * min_prctile / 100
    # Placeholder for cursor calculation
    # cursor = calculate_cursor()

    reward_per_frame_range = 1.0 / frames_per_reward_range
    e1_mean = np.mean(analyze_mean[e1_sel])
    e1_std = np.sqrt(np.dot(np.dot(e1_sel/num_e1, analyze_cov), e1_sel/num_e1))
    e2_subord_mean = np.zeros(num_e2)
    e2_subord_std = np.zeros(num_e2)
    e1_analyze = n_analyze[:, e1_sel]
    e2_analyze = n_analyze[:, e2_sel]

    for e2_i in range(num_e2):
        subord_sel = e2_sel.copy()
        subord_sel[e2_sel_idxs[e2_i]] = 0
        e2_subord_mean[e2_i] = np.mean(analyze_mean[subord_sel])
        var_i = np.dot(np.dot(subord_sel.T, analyze_cov), subord_sel)
        e2_subord_std[e2_i] = np.sqrt(var_i)

    e2_sum_analyze = np.sum(e2_analyze, axis=1)

    cursor_obs = np.dot(n_analyze, decoder)
    e1_mean_analyze = np.mean(e1_analyze, axis=1)
    e2_mean_analyze = np.mean(e2_analyze, axis=1)
    e1_mean_max = np.max(e1_mean_analyze)
    e2_dom_samples = np.max(e2_analyze, axis=1)
    e2_dom_sel = np.argmax(e2_analyze, axis=1)
    e2_subord_mean_analyze = (e2_sum_analyze - e2_dom_samples) / (num_e2 - 1)

    min_prctile = tset['cb']['e2me1_prctile']
    t0 = np.max(cursor_obs)
    t = t0
    t_min = np.percentile(cursor_obs, min_prctile)

    e2_coeff0 = 0.5
    e2_coeff = e2_coeff0
    e2_coeff_min = 0.05
    e2_subord_thresh = e2_subord_mean + e2_subord_std * e2_coeff

    e1_coeff0 = 0.0
    e1_coeff = e1_coeff0
    e1_thresh = e1_mean + e1_coeff * e1_std

    t_delta = 0.05
    e2_coeff_delta = 0.05
    e1_coeff_delta = 0.05
    task_complete = False

    t_vec = []
    e2_coeff_vec = []
    e1_coeff_vec = []

    reward_per_frame_vec = []

    max_iter = 10000
    iter_count = 0

    rand_num_samples = 500000

    while not task_complete:
        t_vec.append(t)
        e2_coeff_vec.append(e2_coeff)
        e1_coeff_vec.append(e1_coeff)

        # 1) e2-e1 > alpha
        c1 = np.where(cursor_obs >= t)[0]
        # 2) e1 < mu
        c2 = np.where(e1_mean_analyze <= e1_thresh)[0]
        # 3) e2_subord > mu
        c3 = np.where(e2_subord_mean_analyze >= e2_subord_thresh[e2_dom_sel])[0]
        hit_idxs_no_b2base = c1  # np.intersect1d(np.intersect1d(c1, c2), c3)

        # Remove hits that fall in a back2base
        b2base_thresh = 0.5 * t
        hits_valid = np.ones(len(hit_idxs_no_b2base))
        if len(hit_idxs_no_b2base) > 1:
            for i in range(1, len(hit_idxs_no_b2base)):
                b2base_bool = np.sum(cursor_obs[hit_idxs_no_b2base[i-1]:hit_idxs_no_b2base[i]] <= b2base_thresh) >= tset['back2base_frame_thresh']
                hits_valid[i] = b2base_bool

        hit_idxs_b2base = hit_idxs_no_b2base[hits_valid.astype(bool)]
        valid_hit_idxs = hit_idxs_b2base
        reward_prob_per_frame = np.sum(hits_valid) / len(n_analyze)

        reward_per_frame_vec.append(reward_prob_per_frame)

        # Update T
        if reward_per_frame_range[0] <= reward_prob_per_frame <= reward_per_frame_range[1]:
            task_complete = True
            print("Target calibration complete!")
        elif reward_prob_per_frame > reward_per_frame_range[1]:
            # Task too easy, make T harder
            t += t_delta
        elif reward_prob_per_frame < reward_per_frame_range[0]:
            # Task too hard, make T easier
            t -= t_delta

        iter_count += 1
        if iter_count == max_iter:
            task_complete = True
            print("Max Iter reached, check reward rate / baseline data")
    plt.figure()
    plt.plot(t_vec, '.-', markersize=7)
    plt.xlabel('alg iteration')
    plt.ylabel('target')
    plt.title('Target Value over Calibration')
    if tset['save']:
        plt.savefig(plot_path / 'target_val_over_calibration.png')
    plt.close()

    print(f'T: {t}')
    print('valid hits', valid_hit_idxs)

    num_c1 = len(c1)
    print(f'num E2-E1 >= T: {num_c1}')

    num_c2 = len(c2)
    print(f'E1 >= b: {num_c2}')

    num_c3 = len(c3)
    print(f'E2 subord >= c: {num_c3}')

    num_cursor_hits = len(c1)
    print(f'num cursor target hits (wo E1<thr, E2sub>thr): {num_cursor_hits}')

    num_hits_no_b2base = len(hit_idxs_no_b2base)
    print(f'num baseline hits WITHOUT B2BASE: {num_hits_no_b2base}')

    num_valid_hits = len(valid_hit_idxs)
    print(f'num valid hits (WITH B2BASE): {num_valid_hits}')

    cursor_amp = max(cursor_obs) - min(cursor_obs)
    cursor_offset = cursor_amp / 10
    max_cursor = max(cursor_obs)

    fb_cal = define_fb_calibration(cursor_obs, fbset, t)

    plot_cursor = np.linspace(min(cursor_obs), max(cursor_obs), 1000)
    plot_freq = cursor2audio(plot_cursor, fb_cal, fb_cal['settings'])

    plt.figure()
    plt.plot(plot_cursor, plot_freq)
    plt.xlabel('Cursor E2-E1')
    plt.ylabel('Auditory Freq')
    plt.axvline(x=t, color='r')
    if tset['save']:
        plt.savefig(plot_path / 'cursor2freq.png')
    plt.close()

    fb_obs = cursor2audio(cursor_obs, fb_cal, fb_cal['settings'])
    num_fb_bins = 100

    plt.figure()
    plt.hist(fb_obs, num_fb_bins)
    plt.xlabel('audio freq')
    plt.ylabel('baseline counts')
    if tset['save']:
        plt.savefig(plot_path / 'base_freq_hist.png')
    plt.close()

    plt.figure()
    plt.scatter(c1, np.ones(len(c1)) * max_cursor + cursor_offset, c='r', s=15)
    plt.scatter(c2, np.ones(len(c2)) * max_cursor + 2 * cursor_offset, c='g', s=15)
    plt.scatter(c3, np.ones(len(c3)) * max_cursor + 3 * cursor_offset, c='b', s=15)
    plt.plot(cursor_obs)
    plt.axhline(y=t, color='r')
    plt.plot(e1_mean_analyze - cursor_amp)
    plt.plot(e2_subord_mean_analyze - 2 * cursor_amp)
    plt.xlabel('frame')
    plt.title(f'hits with b2base: {num_valid_hits}')
    plt.legend(['c1', 'c2 - E1 cond', 'c3 - E2 cond', 'cursor', 'E1 mean', 'E2 subord mean'])
    #plt.axvline(x=valid_hit_idxs, color='r')
    ymin, ymax = plt.ylim()
    plt.vlines(x=valid_hit_idxs, ymin=ymin, ymax=ymax, color='r')
    if tset['save']:
        plt.savefig(plot_path / 'cursor_hit_ts.png')
    plt.close()

    offset = 0
    fig, ax = plot_cursor_e1_e2_activity(cursor_obs, e1_mean_analyze, e2_mean_analyze, n_analyze, e_id, e_color, offset)
    plt.axhline(y=t, color='gray', linestyle='--')  # Add threshold line
    if tset['save']:
        fig.savefig(plot_path / 'cursor_E1_E2_ts.png')

    # Update cursor_obs
    cursor_obs = n_analyze * decoder

    # Plot histogram of cursor observations
    fig, ax = plt.subplots()
    ax.hist(cursor_obs, bins=50)
    plt.axvline(x=t, color='gray', linestyle='--')  # Add vertical line for threshold

    # Customize plot
    ax.set_xlabel('Cursor')
    ax.set_ylabel('Number of Observations')
    ax.set_title(f'E2-E1 thr on E2-E1 hist, num valid hits: {num_valid_hits} '
                 f'num hits no b2base: {num_hits_no_b2base} '
                 f'num cursor hits: {num_cursor_hits}')
    if tset['save']:
        fig.savefig(f'{plot_path}/cursor_dist_t.png')

    psth_win = [-30 * 3, 30 * 3]
    psth_mean, psth_sem, psth_mat = calc_psth(n_analyze, valid_hit_idxs, psth_win)

    plt.figure()
    offset = 0
    for i in range(num_neurons):
        y_plot = psth_mean[:, i] - min(psth_mean[:, i])
        y_amp = max(y_plot)
        offset += y_amp
        y_sem = psth_sem[:, i] - min(psth_mean[:, i])
        plt.plot(y_plot - offset, color=e_color[e_id[i]-1])
        plt.errorbar(range(len(y_plot)), y_plot - offset, yerr=y_sem, color=e_color[e_id[i]-1])

    plt.xlabel('frame')
    plt.title('PSTH of Baseline Activity Locked to Target Hit')
    if tset['save']:
        plt.savefig(plot_path / 'psth_locked_to_hit_baseline.png')
    plt.close()

    date_str = datetime.now().strftime('%Y%m%dT%H%M%S')
    fb_cal_path = save_path / f'fb_cal_{date_str}.npz'
    if tset['save']:
        np.savez_compressed(fb_cal_path, **fb_cal, allow_pickle=True)

    cal_all = {k: v for k, v in locals().items() if not k.startswith('__') and not callable(v)}
    target_cal_all_path = save_path / f'target_calibration_all_{date_str}.npz' # Would save all variables but would need to create a dictionary with all the variables
    if tset['save']:
        np.savez_compressed(target_cal_all_path, **cal_all, allow_pickle=True)

    target_info_path = save_path / f'bmi_target_info_{date_str}.npz'

    t1 = t
    target_info = {
        'n_mean': dff_mean,
        'n_std': dff_std,
        'decoder': decoder,
        'e_id': e_id,
        'e1_sel_idxs': e1_sel_idxs,
        'e2_sel_idxs': e2_sel_idxs,
        'e1_base': e1_base,
        'e2_base': e2_base,
        't1': t1,
        'e1_thresh': e1_thresh,
        'e1_coeff': e1_coeff,
        'e1_std': e1_std,
        'e2_subord_thresh': e2_subord_thresh,
        'e2_coef': e2_coeff,
        'e2_subord_mean': e2_subord_mean,
        'e2_subord_std': e2_subord_std
    }

    print(f'T {t}')

    if tset['save']:
        np.savez_compressed(target_info_path, **target_info, allow_pickle=True)

    return target_info, cal_all, fb_cal, strc_info
