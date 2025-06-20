import matplotlib.pyplot as plt
#import tkinter as tk
import numpy as np
from .scale_im import scale_im

def scale_im_interactive(im, im_sc_struct, num_im_sc):
    # Get screen size using tkinter - is this needed?
    '''
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    # Define figure size and position (right half of the screen)
    fig_width = int(screen_width / 2)
    fig_height = screen_height
    x_pos = int(screen_width / 2)
    y_pos = 0
    '''

    scale_complete_bool = False
    param_vec = [0, 100]
    while not scale_complete_bool:
        print('Current [min_perc max_perc]:')
        print(param_vec)
        param_vec = input('Enter [min_perc max_perc]: ')
        param_vec = list(map(float, param_vec.strip().split()))
        while len(param_vec) != 2:
            print('Error in input!')
            param_vec = input('enter [ min_perc max_perc]: ')
            param_vec = list(map(float, param_vec.strip().split()))

        min_perc, max_perc = param_vec
        im_sc, im_min, im_max = scale_im(im, min_perc, max_perc)

        '''
        fig = plt.figure(figsize=(fig_width / 100, fig_height / 100))  # size in inches
        manager = plt.get_current_fig_manager()
        manager.window.wm_geometry(f"{fig_width}x{fig_height}+{x_pos}+{y_pos}")
        '''
        plt.figure()
        plt.imshow(im_sc, cmap='bone', vmin=0, vmax=1)
        plt.title(f'min prc: {min_perc}; max prc: {max_perc}')
        plt.show()

        already_added = False
        in_store = input('Want to Store this Scaling? y/n:   ').strip().lower()
        if in_store == '' or in_store == 'y':
            for i in range(num_im_sc):
                if np.array_equal(im_sc_struct[i]['minmax'], param_vec):
                    already_added = True
                    print('already saved it!')
                    break
            if not already_added:
                num_im_sc += 1
                im_sc_struct.append({
                    'im': im_sc,
                    'minmax_perc': param_vec,
                    'minmax': [im_min, im_max],
                    'min': im_min,
                    'max': im_max,
                    'min_perc': min_perc,
                    'max_perc': max_perc
                })

        in_continue = input('Want to Continue More Scalings? y/n:   ').strip().lower()
        if in_continue == 'n':
            scale_complete_bool = True

    return im_sc_struct, num_im_sc