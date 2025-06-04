import numpy as np
#from scipy.ndimage import gaussian_laplace

def log2d(x, y, sigma):
    r2 = x ** 2 + y ** 2
    return (-1 / (np.pi * sigma ** 4)) * (1 - r2 / (2 * sigma ** 2)) * np.exp(-r2 / (2 * sigma ** 2))

def dog_n2(r):
    r1 = r / 1.9227
    r2 = r1 * 2
    dim = int(np.ceil(r2 * 5))

    # Ensure odd dimension for symmetry
    if dim % 2 == 0:
        dim += 1

    x = np.arange(-dim // 2 + 1, dim // 2 + 1)
    X, Y = np.meshgrid(x, x)

    log1 = log2d(X, Y, r1)
    log2 = log2d(X, Y, r2) * 1.1 * 15

    ker = log1 - log2
    return ker
