import numpy as np
#from pygments.formatters import img
from scipy.ndimage import gaussian_filter, label
from skimage.morphology import disk, binary_dilation
from skimage.feature import match_template
import cv2 # installed via pip on windows
from .im_filter2 import im_filter2
from .dog_n import dog_n
from .dog_n2 import dog_n2
from .im_dilate2 import im_dilate2

import matplotlib.pyplot as plt

def im_find_cells_tm(img, template_diam, r_threshold=0.5, cell_diam=None, finemode=0, temmode=1):
    """
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
    print('applying gaussian filter...')
    #hp_filter = gaussian_filter(img, sigma=template_diam)
    gk = cv2.getGaussianKernel(int(np.ceil(template_diam * 5)), template_diam)
    hp_filter = gk @ gk.T  # outer product to make 2D kernel

    # ⛔️ Custom function
    filtered = im_filter2(hp_filter, img)
    hp_img = img / filtered  # Placeholder

    # === Template Matching ===
    print('template matching...')

    # ⛔️ Custom function
    if temmode == 1:
        print('running dog_n2...')
        template = dog_n2(template_diam / 2)
    else:
        print('running dog_n...')
        template = dog_n(template_diam / 2)

    #plt.figure()
    #plt.imshow(template, cmap='bone')
    #plt.show()

    if finemode == 1:
        # Custom disk for masking
        print('creating custom disk...')
        # mask = makeDisk(template_diam, template.shape[0])
        # this part of the code was written by using Onki paper - paper sent by nuria
        #corr_map = imTemplateMatch(hp_img, template, mask)
        corr_map = match_template(hp_img, template, pad_input=True)
    else:
        #corr_map = normxcorr2sm(hp_img, template)
        hp_img = hp_img.astype(np.float32)
        template = template.astype(np.float32)

        # Get template size
        corr_map = cv2.matchTemplate(hp_img, template, cv2.TM_CCOEFF_NORMED)
        rh, rw = corr_map.shape

        # Compute padding to center result inside a full-size image
        pad_top = (hp_img.shape[0] - rh) // 2
        pad_bottom = hp_img.shape[0] - rh - pad_top
        pad_left = (hp_img.shape[1] - rw) // 2
        pad_right = hp_img.shape[1] - rw - pad_left

        # Pad with zeros though am unsure if this is correct
        corr_map = np.pad(corr_map, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='constant', constant_values=0)

    # FOR TESTING - check if i can find the shape/size as well, not just the center
    # May want to use OpenCV Feature-Based Matchers to return the exact shapes of the circle.
    # Create another testing with the kernel used in random areas. Make the different sizes and then compress from one side to see if the matching works
    # An issue might be that there might be two neurons that may be so close that they will look like one weird neuron
    # I will need to erode (shrink), label, and dilate (make bigger again) to for sure have different neurons labeled

    # Try suite2p and run 100 tifs of an image to detect neurons. look at stat.npy ['xpix'] and ['ypix'] to create the mask
    # need the default ops and use on holo data
    # would only need to run registration and roi detection... actually just run the detection wrapper from the link nuria sent
    # take arecording of 4 seconds (~120 frames) of the pollen with default ops and see if it can identify the pollen as neurons
    # make ops['anatomical_only'] to 0
    # once i can find the neurons, then i can zip the xoff and yoff to create the maski

    '''
    hp_img = hp_img.astype(float)
    template = template.astype(float)
    th, tw = template.shape
    base_shape = hp_img.shape
    base_img = np.zeros(base_shape, dtype=float)
    positions = [(30, 40), (100, 120), (50, 160)]
    for y, x in positions:
        if y + th <= base_shape[0] and x + tw <= base_shape[1]:
            print(y, th, x, tw)
            base_img[y:y + th, x:x + tw] = template
            print(base_img[y:y + th, x:x + tw])
        else:
            print(f"Skipping position {(y, x)} — would overflow image bounds.")
    result = match_template(base_img, template, pad_input=True)
    threshold = 0.95
    match_locations = np.where(result > threshold)
    print('result')
    print(result)
    print(result[30, 40])
    print(match_locations)
    plt.figure()
    plt.imshow(result, cmap='gray')
    plt.title("Template Matches")
    plt.show()
    '''



    exit()
    # === Detect Cells ===
    cells = corr_map > r_threshold
    labeled_cells, _ = label(cells)
    print(f"{labeled_cells.max()} cells detected.")

    # ⛔️ Custom function used here (not defined): imDilate2
    label_img = im_dilate2(labeled_cells, cell_diam)

    return label_img, hp_img

'''
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

# try opencv and skycit match_template
# Use the dogn2 template and put it in a random place
# Then use that template of different radius to see if the template matching is accurate

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
'''