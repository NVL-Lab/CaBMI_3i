import numpy as np
from scipy.ndimage import gaussian_filter, label
from skimage.morphology import disk, binary_dilation
from im_filter2 import im_filter2
from dog_n import dog_n
from dog_n2 import dog_n2
from im_dilate2 import im_dilate2

def im_find_cells_tm(img, template_diam, r_threshold=0.5, cell_diam=None, finemode=0, temmode=1):
    """
    Python version of imFindCellsTM from MATLAB.
    Template matching based cell segmentation.

    Parameters:
        img (ndarray): input image
        template_diam (float): diameter for DoG filter
        r_threshold (float): correlation threshold
        cell_diam (float): diameter for dilation
        finemode (int): use finer template match
        temmode (int): template mode

    Returns:
        labelimg (ndarray): labeled segmented image
        hp_img (ndarray): high-pass filtered image
    """
    if cell_diam is None:
        cell_diam = template_diam

    img = img.astype(float)

    # === High-pass filtering ===
    hp_filter = gaussian_filter(img, sigma=template_diam)

    # ⛔️ Custom function
    filtered = im_filter2(hp_filter, img)
    hp_img = img / filtered  # Placeholder

    # === Template Matching ===
    print("template matching....")

    # ⛔️ Custom function
    if temmode == 1:
        raise NotImplementedError("DOG_N2 is not defined. Please provide its implementation.")
        template = dog_n2(template_diam / 2)
    else:
        raise NotImplementedError("DOG_N is not defined. Please provide its implementation.")
        template = dog_n(template_diam / 2)

    if finemode == 1:
        # Custom disk for masking
        mask = makeDisk(template_diam, template.shape[0])
        corr_map = imTemplateMatch(hp_img, template, mask)
    else:
        corr_map = normxcorr2sm(hp_img, template)

    # === Detect Cells ===
    cells = corr_map > r_threshold
    labeled_cells, _ = label(cells)
    print(f"{labeled_cells.max()} cells detected.")

    # ⛔️ Custom function used here (not defined): imDilate2
    labelimg = im_dilate2(labeled_cells, cell_diam)

    return labelimg, hp_img


def makeDisk(radius, dim):
    """Generate a binary disk mask."""
    center = dim // 2
    y, x = np.ogrid[:dim, :dim]
    mask = (x - center) ** 2 + (y - center) ** 2 < radius ** 2
    return mask.astype(float)


def normxcorr2sm(template, image):
    """Normalized cross-correlation with valid output (like conv2 in 'valid' mode)."""
    from scipy.signal import correlate2d

    imsiz = image.shape
    corr_full = correlate2d(image, template, mode='same')
    # This is an approximation, real normxcorr2 does mean-normalization
    return corr_full / (np.std(image) * np.std(template) * template.size)


def imTemplateMatch(image, template, mask=None):
    """Custom masked template matching."""
    h, w = image.shape
    th, tw = template.shape
    mh, mw = mask.shape if mask is not None else template.shape
    mh2, mw2 = mh // 2, mw // 2

    if mask is None:
        mask = np.ones_like(template)

    out = np.zeros_like(image)

    # Padding
    padded = np.pad(image, ((mh2, mh2), (mw2, mw2)), mode='constant')

    for i in range(h):
        for j in range(w):
            patch = padded[i:i + mh, j:j + mw]
            region = patch * mask
            t_norm = (template * mask) - np.mean(template * mask)
            r_norm = region - np.mean(region)
            denom = np.linalg.norm(t_norm) * np.linalg.norm(r_norm)
            if denom != 0:
                out[i, j] = np.sum(t_norm * r_norm) / denom
            else:
                out[i, j] = 0
    return out