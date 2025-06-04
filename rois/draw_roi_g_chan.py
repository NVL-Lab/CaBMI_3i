import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import PolygonSelector
from matplotlib.path import Path

from roi_bin_cell2center_radius import roi_bin_cell2center_radius
from roi_data2chan import roi_data2chan
from dex.draw_rois import draw_rois

def draw_roi_g_chan(plot_images, roi_data):
    # Show the red and green channels
    plt.close('all')
    for plot_image in plot_images:
        im_plot = plot_image['im']
        im_title = plot_image['label']
        plt.figure()
        plt.imshow(im_plot, cmap='bone')
        plt.axis('square')
        plt.title(im_title)

    print('Adding ROIs to image!')
    roi_complete_bool = False
    while not roi_complete_bool:
        # Close figures if open
        try:
            plt.close(h0)
        except:
            pass
        try:
            plt.close(h1)
        except:
            pass

        print(f"Current Roi Image, Num Rois: {roi_data['num_rois']}")
        h0 = plt.figure()
        plt.imshow(roi_data['im_roi'], cmap='bone')
        plt.clim([-0, np.nanmedian(roi_data['im_roi']) * 20])
        plt.axis('square')
        plt.title(f"Num ROIs added: {roi_data['num_rois']}  Add ROI? y/n")
        in_str = input('Want to Add ROI? y/n:   ').strip().lower()

        if in_str == '' or in_str == 'y':
            print('Draw the ROI (click, hold click, draw on image)...')
            plt.title('Draw ROI')
            numArea = 1

            draw_complete = False
            while not draw_complete:
                draw_rois(numArea)  # custom

                rois = []
                hF = plt.gcf()
                hP = [obj for obj in hF.get_children() if getattr(obj, 'get_label', lambda: '')() == 'ROIPatch']
                for rr in range(len(hP)):
                    rois.append(getUD(hP[rr], 'binroi'))  # custom
                if rois:
                    draw_complete = True

            Im_roi_i = roi_data['im_bg'].copy()
            Im_roi_i[:, :, 2] = rois[0]  # assume one ROI drawn
            h1 = plt.figure()
            plt.imshow(Im_roi_i, cmap='bone')
            plt.clim([-0, np.nanmedian(roi_data['im_roi']) * 20])
            plt.axis('square')
            plt.title(f"Added Candidate Roi # {roi_data['num_rois']+1} Keep? y/n")
            in_str = input('Keep ROI? y/n:   ').strip().lower()

            if in_str == '' or in_str == 'y':
                roi_data['num_rois'] += 1
                roi_data['roi_bin_cell'].append(rois[0])
                roi_ctr = roi_bin_cell2center_radius([rois[0]])  # custom
                roi_data['x'].append(roi_ctr['x'])
                roi_data['y'].append(roi_ctr['y'])
                roi_data['r'].append(roi_ctr['r'])

                roi_idxs = np.where(rois[0])
                roi_data['roi_mask'][roi_idxs] = roi_data['num_rois']
                roi_data['roi_mask_bin'][roi_idxs] = 1
                roi_data['im_roi'][:, :, 2] = roi_data['roi_mask_bin']

                chan_selected_bool = False
                while not chan_selected_bool:
                    chan_vec = [0, 1]
                    roi_data['chan_logical'].append(chan_vec)
                    g_mod = roi_data['im_roi_rg'][:, :, 1]
                    g_mod[roi_idxs] = 1
                    roi_data['im_roi_rg'][:, :, 1] = g_mod
                    chan_selected_bool = True
        else:
            roi_complete_bool = True
            print('done')
            try:
                plt.close(h0)
            except:
                pass
            try:
                plt.close(h1)
            except:
                pass

            roi_data = roi_data2chan(roi_data)  # custom

            plt.figure()
            plt.imshow(roi_data['im_roi_rg'], cmap='bone')
            plt.clim([-0, np.nanmedian(roi_data['im_roi']) * 20])
            plt.axis('square')
            plt.title(f"ROI addition complete! Num ROIs: {roi_data['num_rois']}")

            plt.figure()
            plt.imshow(roi_data['im_roi'], cmap='bone')
            plt.clim([-0, 1000])
            plt.axis('square')
            plt.title(f"ROI addition complete! Num ROIs: {roi_data['num_rois']}")

    return roi_data