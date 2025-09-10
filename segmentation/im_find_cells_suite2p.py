import numpy as np
import matplotlib.pyplot as plt
import suite2p

def im_find_cells(image):
    roi_mask = np.zeros((image.shape[1], image.shape[0]), dtype=np.float64)
    image = np.array([image])

    ops = suite2p.default_ops()
    ops['anatomical_only'] = 2
    ops['roidetect'] = True
    ops['nbinned'] = 1
    ops['fs'] = 1

    _, stat = suite2p.detection_wrapper(f_reg=image, ops=ops, classfile=suite2p.classification.builtin_classfile)
    iscell = suite2p.classification.classify(stat, suite2p.classification.builtin_classfile)

    cell_count = 0
    for i, roi in enumerate(stat):
        if iscell[i, 0]:
            cell_count += 1
            roi_mask[roi['ypix'], roi['xpix']] += cell_count  # * roi['lam']

    plt.figure()
    plt.imshow(roi_mask, cmap='nipy_spectral')
    plt.title(f'{cell_count} Neurons')
    plt.colorbar(label="Label index")
    plt.show()
    plt.close()

    return roi_mask