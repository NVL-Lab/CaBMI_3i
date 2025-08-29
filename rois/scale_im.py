import numpy as np

def scale_im(im, min_perc, max_perc):

    '''
    Rescales the pixel intensities of the image so that values between two specified percentiles ( min_perc and max_perc) are stretched to the range [0, 1].
    This enhances contrast while suppressing extreme outliers.

    :param im:
    :param min_perc:
    :param max_perc:
    :return:
    '''

    min_val = np.percentile(im, min_perc)
    im_s = im - min_val
    im_s[im_s < 0] = 0
    max_val = np.percentile(im_s, max_perc)
    im_s[im_s > max_val] = max_val
    im_s = im_s.astype(float) / float(max_val)

    min_val_return = min_val
    max_val_return = max_val + min_val

    return im_s, min_val_return, max_val_return