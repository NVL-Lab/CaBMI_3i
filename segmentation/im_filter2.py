import numpy as np
from scipy.signal import convolve2d

def im_filter2(ker, img):
    """
    Normalized 2D convolution that avoids edge underestimation.

    Parameters:
        ker (ndarray): 2D filter kernel
        img (ndarray): 2D input image

    Returns:
        out (ndarray): Filtered output image
    """
    img = img.astype(float)
    kernel = ker.astype(float)

    # Convolve image
    out = convolve2d(img, kernel, mode='same', boundary='fill', fillvalue=0)

    # Normalize by convolving a matrix of ones
    normalization = convolve2d(np.ones_like(img), kernel, mode='same', boundary='fill', fillvalue=0)

    # Avoid division by zero
    normalization[normalization == 0] = 1
    out = out / normalization

    return out