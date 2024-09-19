import numpy as np

def scale_im_interactive(im) -> list:
    ims = []
    while input("Continue scaling? (y/n): ").lower() == 'y':
        percs = input('Enter [min_perc max_perc]: ')
        while len(percs) != 2:
            print('Incorrect input');
            percs = input('Enter [min_perc max_perc]: ')

        # IM Scaling
        im_min = np.percentile(im, percs[0])
        im_max = np.percentile(im, percs[1])
        im_s = im-min_val
        im_s = [min(max(0, x), im_max) for x in im_s]
        im_s = double(im_s)/double(im_max);
        im_max = im_max + im_min
        
        # Create Figure
        '''
        h = figure('Position', [screen_size(3)/2 1 screen_size(3)/2 screen_size(4)]);
        imagesc(im_sc), colormap bone
        axis square
        title(['min prc: ' num2str(min_perc) '; max prc: ' num2str(max_perc)]);
        '''

        if input("Store scaling? (y/n): ").lower() == 'y':
            for im_idx in len(ims)-1:
                if ims[im_idx+1] == ims[im_idx]:
                    print('Scaling previously saved')
                    break
            if im_idx == len(ims)-1:
                ims.append({
                    'im': im_s,
                    'minmax_perc': percs,
                    'minmax': [im_min im_max],
                })
    return im_sc
