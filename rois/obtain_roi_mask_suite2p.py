import numpy as np
import matplotlib.pyplot as plt
import suite2p
import subprocess

def create_roi_mask(image, stat, iscell):
    roi_mask = np.zeros((image.shape[1], image.shape[2]), dtype=np.float32) #(Lx, Ly)
    roi_mask_false = roi_mask.copy()

    #cell_count = 0
    #false_cell_count = 0

    cell_indexes = np.where(iscell[:, 0] == 1)[0].tolist()
    false_cell_indexes = np.where(iscell[:, 0] == 0)[0].tolist()
    cell_count = len(cell_indexes)
    false_cell_count =  len(false_cell_indexes)

    j=1
    for i in cell_indexes:
        roi_mask[stat[i]['ypix'], stat[i]['xpix']] = j# + stat[i]['lam']
        j=j+1
    j=1
    for i in false_cell_indexes:
        roi_mask_false[stat[i]['ypix'], stat[i]['xpix']] = j# + stat[i]['lam']
        j=j+1

    '''
    for i, roi in enumerate(stat): # Check stat, see how it is shaped
        if i in cell_indexes: #if iscell[i, 0]:
            #cell_count += 1
            #roi_mask[roi['ypix'], roi['xpix']] += cell_count
            # Intensities: roi['lam']
            roi_mask[roi['ypix'], roi['xpix']] = i + roi['lam']
        else:
            #false_cell_count += 1
            roi_mask_false[roi['ypix'], roi['xpix']] = i + roi['lam']#j
    '''

    fig, axes = plt.subplots(1, 2)
    axes[0].imshow(image[0], cmap='bone')
    cells = axes[0].imshow(roi_mask, cmap='nipy_spectral', alpha=0.7)
    axes[0].set_title(f'ROI Mask: {cell_count} Neurons')
    fig.colorbar(cells, ax=axes[0], label="ROI Label Index")
    axes[1].imshow(image[0], cmap='bone')
    false_cells = axes[1].imshow(roi_mask_false, cmap='nipy_spectral', alpha=0.7)
    axes[1].set_title(f'{false_cell_count} ROIs are not cells')
    fig.colorbar(false_cells, ax=axes[1], label="ROI Label Index")

    plt.show()
    plt.close()

    '''
    plt.figure()
    plt.imshow(image[0], cmap='bone')
    plt.imshow(roi_mask, cmap='nipy_spectral', alpha=0.7)
    plt.title(f'ROI Mask: {cell_count} Neurons')
    plt.colorbar(label="ROI Label Index")
    plt.show()
    plt.close()
    '''

    return roi_mask#, cell_count, false_cell_count

def get_roi_mask(image, save_path):
    image = np.array([image]) # suite2p expects several frames (Lx, Ly, Lz)

    ops = suite2p.default_ops()
    '''
        In order to run cellpose (anatomical) with gpu (cpu execution is slow) remove the following pip packages:
            torch, torchvision, torchaudio
        Install the latest versions via pip or conda (specify pytorch-cuda)
    '''
    ops['anatomical_only'] = 2
    ops['nbinned'] = 1
    ops['fs'] = 1
    #ops['cellpose_use_gpu'] = True # need to have cellpose run with gpu for fast processing
    #ops['verbose'] = True # optional
    print('Detecting ROIs...')
    ops, stat = suite2p.detection_wrapper(f_reg=image, ops=ops, classfile=suite2p.classification.builtin_classfile)
    print('Classifying cells...')
    iscell = suite2p.classification.classify(stat, suite2p.classification.builtin_classfile) # Typically ran after extraction

    roi_mask = create_roi_mask(image, stat, iscell)

    edit_resp = input('Would you like to edit the amount of ROIs shown? (y/n)   ').strip().lower()
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

        # Runs additional steps of pipeline
        im_path = suite2p_path / 'im_bg.npy'
        np.save(im_path, image)
        # Needed for the extraction and addition of ROIs
        print('Binarizing data...')
        _ = suite2p.io.BinaryFile(Ly=image.shape[1], Lx=image.shape[2], filename=im_path)  # reads in data from npy
        _ = suite2p.io.BinaryFile(Ly=image.shape[1], Lx=image.shape[2], filename=suite2p_path / 'data.bin',
                                  n_frames=image.shape[0])  # writes data into a bin file

        # The following will not work on pollen data or could just be because it's a simple capture
        print('Extracting neuronal data...')
        # The following is from suite2p.pipeline(image, run_registration=False, ops=ops, stat=stat)
        # TODO: Auxiliary file info is not extracted as expected in the GUI and may want to check why (extraction ran before classification causes null classification)
        stat, F, Fneu, _, _ = suite2p.extraction.extraction_wrapper(stat, image, f_reg_chan2=None, ops=ops)
        dF = F.copy() - ops['neucoeff'] * Fneu
        dF = suite2p.extraction.preprocess(F=dF, baseline=ops['baseline'],
                                           win_baseline=ops['win_baseline'],
                                           sig_baseline=ops['sig_baseline'],
                                           fs=ops['fs'],
                                           prctile_baseline=ops['prctile_baseline'])
        spks = suite2p.extraction.oasis(F=dF, batch_size=ops['batch_size'],
                                        tau=ops['tau'], fs=ops['fs'])

        # Suite2p gui needs the following files to open ROI mask
        np.save(suite2p_path / 'stat.npy', stat)
        np.save(suite2p_path / 'iscell.npy', iscell)
        # Auxiliary files
        np.save(suite2p_path / 'ops.npy', ops)
        np.save(suite2p_path / 'F.npy', F)
        np.save(suite2p_path / 'Fneu.npy', Fneu)
        np.save(suite2p_path / 'spks.npy', spks)

        # Runs suite2p GUI
        print('Running suite2p...')
        subprocess.run('suite2p')

        roi_mask = create_roi_mask(image, np.load(suite2p_path / 'stat.npy', allow_pickle=True), np.load(suite2p_path / 'iscell.npy'))

    return roi_mask