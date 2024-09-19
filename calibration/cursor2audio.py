import numpy as np

def cursor2audio(cursor, fb_cal) -> float:
    """
    Converts the neural control signal (cursor) to an auditory feedback frequency.

    Parameters:
    cursor (float): Neural control signal.
    fb_cal (dict): Dictionary containing calibration parameters:
                   - 'settings': Dictionary with settings such as 'target_low_freq'.
                   - 'cursor_min': Minimum value of the cursor.
                   - 'cursor_max': Maximum value of the cursor.
                   - 'a': Frequency scaling factor.
                   - 'b': Exponential scaling factor.

    Returns:
    float: The calculated auditory feedback frequency.
    """

    # Handle target to frequency conversion
    if fb_cal['settings']['target_low_freq'] == 1:
        # If cursor up makes frequency go down
        cursor = -cursor
        cursor_min = -fb_cal['cursor_max']
        cursor_max = -fb_cal['cursor_min']
    else:
        # If cursor up makes frequency go up
        cursor_min = fb_cal['cursor_min']
        cursor_max = fb_cal['cursor_max']

    # Truncate cursor within the defined range
    cursor_trunc = max(cursor, cursor_min)
    cursor_trunc = min(cursor_trunc, cursor_max)

    # Calculate the frequency using the exponential formula
    freq = fb_cal['a'] * np.exp(fb_cal['b'] * (cursor_trunc - cursor_min))
    
    return float(freq)

