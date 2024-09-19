import numpy as np
import matplotlib.pyplot as plt
from skimage.draw import polygon

def draw_roi_g_chan(plot_images, roi_data):
    """
    Allows user to draw shapes onto an image and adds them as ROIs to roi_data.
    """
    # Show the red and green channels
    plt.close('all')
    for plot_image in plot_images:
        im_plot = plot_image['im']
        im_title = plot_image['label']
        plt.figure(figsize=(10, 8))
        plt.imshow(im_plot, cmap='bone')
        plt.title(im_title)
        plt.axis('square')
        plt.show()

    print('Adding ROIs to image!')
    roi_complete_bool = False
    while not roi_complete_bool:
        # Display the current ROI image and ask if the user wants to add more ROIs
        print(f"Current ROI Image, Num ROIs: {roi_data['num_rois']}")
        plt.figure(figsize=(10, 8))
        plt.imshow(roi_data['im_roi'], cmap='bone')
        plt.title(f'Num ROIs added: {roi_data["num_rois"]}  Add ROI? y/n')
        plt.axis('square')
        plt.show()

        in_input = input('Want to Add ROI? y/n:   ').strip().lower()
        if not in_input or in_input == 'y':
            print('Draw the ROI (click, hold click, draw on image)...')
            plt.figure(figsize=(10, 8))
            plt.imshow(roi_data['im_roi'], cmap='bone')
            plt.title('Draw ROI')
            plt.axis('square')
            
            # User draws a polygon (ROI)
            points = plt.ginput(n=-1, timeout=0)  # Collect user clicks
            plt.close()
            points = np.array(points, dtype=np.int32)
            if len(points) > 2:  # Ensure we have a valid polygon
                rr, cc = polygon(points[:, 1], points[:, 0], roi_data['im_roi'].shape[:2])
                rois = np.zeros_like(roi_data['im_roi'][:, :, 2])
                rois[rr, cc] = 1

                Im_roi_i = roi_data['im_bg'].copy()
                Im_roi_i[:, :, 2] = rois
                plt.figure(figsize=(10, 8))
                plt.imshow(Im_roi_i, cmap='bone')
                plt.title(f'Added Candidate ROI # {roi_data["num_rois"] + 1} Keep? y/n')
                plt.axis('square')
                plt.show()

                # Check whether to keep ROI
                in_input = input('Keep ROI? y/n:   ').strip().lower()
                if not in_input or in_input == 'y':
                    # Update general information
                    roi_data['num_rois'] += 1
                    roi_data['roi_bin_cell'].append(rois)

                    # Update x, y, r
                    roi_ctr = roi_bin_cell2center_radius([rois])
                    roi_data['x'].append(roi_ctr['x'])
                    roi_data['y'].append(roi_ctr['y'])
                    roi_data['r'].append(roi_ctr['r'])

                    roi_idxs = np.where(rois)
                    roi_data['roi_mask'][roi_idxs] = roi_data['num_rois']
                    roi_data['roi_mask_bin'][roi_idxs] = 1
                    roi_data['im_roi'][:, :, 2] = roi_data['roi_mask_bin']

                    # Update channel information
                    chan_selected_bool = False
                    while not chan_selected_bool:
                        chan_vec = [0, 1]
                        roi_data['chan_logical'] = np.hstack((roi_data['chan_logical'], np.array(chan_vec).reshape(-1, 1)))
                        g_mod = roi_data['im_roi_rg'][:, :, 1].copy()
                        g_mod[roi_idxs] = 1
                        roi_data['im_roi_rg'][:, :, 1] = g_mod
                        chan_selected_bool = True

        else:
            roi_complete_bool = True
            print('done')

            # Close figures
            plt.close('all')

            # Channel-specific information
            roi_data = roi_data2chan(roi_data)

            plt.figure(figsize=(10, 8))
            plt.imshow(roi_data['im_roi_rg'], cmap='bone')
            plt.title(f'ROI addition complete! Num ROIs: {roi_data["num_rois"]}')
            plt.axis('square')
            plt.show()

            plt.figure(figsize=(10, 8))
            plt.imshow(roi_data['im_roi'], cmap='bone')
            plt.title(f'ROI addition complete! Num ROIs: {roi_data["num_rois"]}')
            plt.axis('square')
            plt.show()

    return roi_data
