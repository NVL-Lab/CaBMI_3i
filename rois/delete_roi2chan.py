import numpy as np
import matplotlib.pyplot as plt

def delete_roi2chan(plot_images, roi_data) -> list:
    """
    Function to delete ROIs from the image.
    """
    screen_size = plt.get_current_fig_manager().window.wm_maxsize()
    
    # Show the red and green channels
    plt.close('all')
    for plot_img in plot_images:
        im_plot = plot_img['im']
        im_title = plot_img['label']
        plt.figure(figsize=(screen_size[0] / 200, screen_size[1] / 200))
        plt.imshow(im_plot, cmap='gray')
        plt.axis('square')
        plt.title(im_title)
        plt.show()

    # Ask for user input on idxs to delete and update the roi_data
    complete_bool = False
    while not complete_bool:
        # Show images
        plt.figure(figsize=(screen_size[0] / 200, screen_size[1] / 200))
        plt.imshow(roi_data['im_roi_rg'])
        plt.axis('square')
        plt.title('roi colored by rg')
        plt.show()
        
        plt.figure(figsize=(screen_size[0] / 200, screen_size[1] / 200))
        plt.imshow(roi_data['roi_mask'])
        plt.axis('square')
        plt.title('roi idxs')
        plt.show()

        del_idxs = list(map(int, input('Enter ROI idxs to delete in vector [roi_1 roi_2 ... ]: ').strip().split()))
        del_data = delete_rois(roi_data, del_idxs)

        # Show new images
        plt.figure(figsize=(screen_size[0] / 200, screen_size[1] / 200))
        plt.imshow(del_data['im_roi_rg'])
        plt.axis('square')
        plt.title('roi colored by rg, AFTER DELETION')
        plt.show()
        
        plt.figure(figsize=(screen_size[0] / 200, screen_size[1] / 200))
        plt.imshow(del_data['roi_mask'])
        plt.axis('square')
        plt.title('roi idxs, AFTER DELETION')
        plt.show()

        undo = input('UNDO? y/n:   ').strip().lower()
        if undo == 'n':
            roi_data = del_data

        done_deleting = input('Done Deleting? y/n:   ').strip().lower()
        if done_deleting == 'y':
            complete_bool = True

    plt.close('all')
    return roi_data


def delete_rois(roi_data, del_idxs):
    """
    Function to delete specific ROIs and rebuild the data.
    """
    del_data = roi_data.copy()
    del_data['roi_bin_cell'] = [roi for i, roi in enumerate(roi_data['roi_bin_cell']) if i not in del_idxs]
    del_data['chan_logical'] = np.delete(roi_data['chan_logical'], del_idxs, axis=1)
    del_data['x'] = np.delete(roi_data['x'], del_idxs)
    del_data['y'] = np.delete(roi_data['y'], del_idxs)
    del_data['r'] = np.delete(roi_data['r'], del_idxs)
    del_data['num_rois'] = len(del_data['roi_bin_cell'])

    # Rebuild images
    del_data['im_roi'] = del_data['im_bg'].copy()
    del_data['im_roi_rg'] = del_data['im_bg'].copy()
    del_data['roi_mask'] = np.zeros((del_data['num_rows'], del_data['num_cols']))
    del_data['roi_mask_bin'] = np.zeros((del_data['num_rows'], del_data['num_cols']))

    for i, roi_i in enumerate(del_data['roi_bin_cell']):
        roi_idxs = np.nonzero(roi_i)
        
        del_data['roi_mask'][roi_idxs] = i + 1
        del_data['roi_mask_bin'][roi_idxs] = 1
        
        chan_idx = np.nonzero(del_data['chan_logical'][:, i])[0]
        for idx in chan_idx:
            del_data['im_roi_rg'][:, :, idx][roi_idxs] = 1

    del_data['im_roi'][:, :, 2] = del_data['roi_mask_bin']

    # Update channel information
    del_data = roi_data2chan(del_data)

    return del_data
