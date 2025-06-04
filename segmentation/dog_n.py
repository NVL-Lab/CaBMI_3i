import numpy as np

def gaussian2d(size, sigma):
    """Create a 2D Gaussian kernel."""
    ax = np.arange(-size // 2 + 1, size // 2 + 1)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2. * sigma**2))
    return kernel / np.sum(kernel)

def dog_n(r):
    r1 = r / 1.9227
    r2 = r1 * 2
    dim = int(np.ceil(r2 * 5))

    # Ensure odd size for symmetry
    if dim % 2 == 0:
        dim += 1

    g1 = gaussian2d(dim, r1)
    g2 = gaussian2d(dim, r2)

    return g1 - g2