import numpy as np
from scipy.ndimage import grey_dilation

def im_dilate2(img, diam):
    """
    Dilate an image using a circular structuring element of given diameter.

    Parameters:
        img (ndarray): Input image (binary or grayscale)
        diam (float): Diameter of circular structuring element

    Returns:
        out (ndarray): Dilated image
    """
    radius = diam / 2
    dim = int(np.ceil(radius)) * 2 + 1
    center = int(np.ceil(radius))

    # Create a circular structuring element
    y, x = np.ogrid[:dim, :dim]
    mask = ((x - center) ** 2 + (y - center) ** 2) <= radius ** 2

    # Use binary dilation or grey dilation depending on input
    if img.dtype == bool or set(np.unique(img)) <= {0, 1}:
        from scipy.ndimage import binary_dilation
        return binary_dilation(img, structure=mask)
    else:
        return grey_dilation(img, footprint=mask)