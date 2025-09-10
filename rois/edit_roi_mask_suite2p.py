import numpy as np
import matplotlib.pyplot as plt
import suite2p
import subprocess

def create_roi_mask(image, stat, iscell):
    roi_mask = np.zeros((image.shape[2], image.shape[1]), dtype=np.int64) #(Lx, Ly)

    cell_count = 0
    for i, roi in enumerate(stat):
        if iscell[i, 0]:
            cell_count += 1
            roi_mask[roi['ypix'], roi['xpix']] += cell_count  # * roi['lam'] # Intensities

    plt.figure()
    plt.imshow(roi_mask, cmap='nipy_spectral')
    plt.title(f'ROI Mask: {cell_count} Neurons')
    plt.colorbar(label="Label index")
    plt.show()
    plt.close()

    return roi_mask

def edit_roi_mask(image, save_path):
    image = np.array([image]) # suite2p expects several frames (Lx, Ly, Lz)

    ops = suite2p.default_ops()
    ops['anatomical_only'] = 2
    ops['nbinned'] = 1
    ops['fs'] = 1

    ops, stat = suite2p.detection_wrapper(f_reg=image, ops=ops, classfile=suite2p.classification.builtin_classfile)
    iscell = suite2p.classification.classify(stat, suite2p.classification.builtin_classfile) # Typically ran after extraction

    roi_mask = create_roi_mask(image, stat, iscell)

    edit_resp = input('Would you like to edit the amount of ROIs shown? (y/n)  ').strip().lower()
    if edit_resp == 'y' or edit_resp == '':
        # Needed for suite2p GUI
        suite2p_path = save_path / 'suite2p_roi_detection'
        suite2p_path.mkdir(parents=True, exist_ok=True)

        # Ops for pipeline run
        ops['save_path'] = suite2p_path
        ops['reg_file'] = suite2p_path
        ops['ops_path'] = suite2p_path / 'ops.npy'
        ops['batch_size'] = 1
        ops['Ly'] = image.shape[1]
        ops['Lx'] = image.shape[2]

        '''
        # Runs additional steps of pipeline
        # The following is from suite2p.run_s2p.pipeline(image, run_registration=False, ops=ops)
        # TODO: Auxiliary file info is not extracted as expected in the GUI and may want to check why (extraction ran before classification causes bad classification)
        stat, F, Fneu, _, _ = suite2p.extraction.extraction_wrapper(stat, image, f_reg_chan2=None, ops=ops)
        dF = F.copy() - ops['neucoeff'] * Fneu
        dF = suite2p.extraction.preprocess(F=dF, baseline=ops['baseline'],
                                           win_baseline=ops['win_baseline'],
                                           sig_baseline=ops['sig_baseline'],
                                           fs=ops['fs'],
                                           prctile_baseline=ops['prctile_baseline'])
        spks = suite2p.extraction.oasis(F=dF, batch_size=ops['batch_size'],
                                        tau=ops['tau'], fs=ops['fs'])

        # Suite2p gui needs the following files to open mask
        np.save(suite2p_path / 'stat.npy', stat)
        np.save(suite2p_path / 'iscell.npy', iscell)
        # Auxiliary files
        np.save(suite2p_path / 'ops.npy', ops)
        np.save(suite2p_path / 'F.npy', F)
        np.save(suite2p_path / 'Fneu.npy', Fneu)
        np.save(suite2p_path / 'spks.npy', spks)

        np.save(suite2p_path / 'stat_orig.npy', stat)
        '''

        # Runs suite2p pipeline
        suite2p.pipeline(image, run_registration=False, ops=ops, stat=stat)

        # Saves original iscell file in place of pipeline one, which is wrong
        # TODO: fix pipeline iscell
        np.save(suite2p_path / 'iscell.npy', iscell)

        # Runs suite2p GUI
        subprocess.run('suite2p')

        roi_mask = create_roi_mask(image, np.load(suite2p_path / 'stat.npy', allow_pickle=True), np.load(suite2p_path / 'iscell.npy'))

    return roi_mask