import numpy as np
import matplotlib.pyplot as plt
import suite2p
from suite2p.run_s2p import pipeline as suite2p_pipeline
import subprocess

def edit_roi_mask(image, save_path, ly, lx):
    roi_mask = np.zeros((image.shape[1], image.shape[0]), dtype=np.float64)
    image = np.array([image])

    suite2p_path = save_path / 'suite2p'
    suite2p_path.mkdir(parents=True, exist_ok=True)
    ops = suite2p.default_ops()
    ops['anatomical_only'] = 2
    ops['roidetect'] = True
    ops['nbinned'] = 1
    ops['fs'] = 1
    ops['reg_file'] = suite2p_path
    ops['save_path'] = suite2p_path
    ops['ops_path'] = suite2p_path / 'ops.npy'
    ops['Ly'] = ly
    ops['Lx'] = lx

    im_path = suite2p_path / 'im_bg.npy'
    np.save(im_path, image)
    _ = suite2p.io.BinaryFile(Ly=image.shape[1], Lx=image.shape[2], filename=im_path)  # reads in data from npy
    _ = suite2p.io.BinaryFile(Ly=image.shape[1], Lx=image.shape[2], filename=suite2p_path / 'data.bin',  n_frames=image.shape[0]) # writes data into a bin file

    suite2p_pipeline(image, run_registration=False, ops=ops) # Runs pipeline
    subprocess.run('suite2p')

    stat = np.load(suite2p_path / 'stat.npy', allow_pickle=True)
    #iscell = np.load(save_path / 'iscell.npy')

    cell_count = 0
    for i, roi in enumerate(stat):
        # if iscell[i, 0]:
        cell_count += 1
        roi_mask[roi['ypix'], roi['xpix']] += cell_count # * roi['lam']

    plt.figure()
    plt.imshow(roi_mask, cmap='nipy_spectral')
    plt.title(f'{cell_count} Neurons')
    plt.colorbar(label="Label index")
    plt.show()

    return roi_mask