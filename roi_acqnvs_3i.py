import matplotlib.pyplot as plt
import socket
from slidebook.SBAccess import *

from wait_on_task_3i import *
from rois.scale_im_interactive import scale_im_interactive
from rois.label_mask2roi_data_single_channel import label_mask2roi_data_single_channel
from rois.obtain_roi_mask_suite2p import get_roi_mask
from recording_acqnvs_3i import recording_acqnvs_3i, recording_acqnvs_3i_sbaccess

from pathlib import Path

def get_roi_bg(task_set, path_data, run=''):
    """
        Records region of interest and extracts the regions of interest (ROIs)

        Parameters:
            task_set: dictionary with bmi parameters
            path_data: paths to experiment data
            capture: integer denoting the desired capture within 3i .sldy file
            channel: type of channel
            roi_chan_data: list with channel and ROI data
            see_roi_data_flag: bool used to determine if ROIs should be plotted
            run: bool used to determine if the code should be run (typically ran unless code has been ran already)

        Returns:
            test_info: dictionary containing dataframes with voltage data.
    """
    base_name = 'roi_bg'
    task_set['roi']['recording_frames'] = int(np.ceil(task_set['im']['frame_rate'] * task_set['roi']['recording_len'])) # Actual microscope fps seems to be halved
    roi_bg_path = path_data['save_path'] / f'{base_name}_{task_set["im"]["chan_data"]["recording_chan"].lower().replace(" ", "")}.npy'
    print(f'ROI recording will consist of {task_set["roi"]["recording_frames"]} frames')

    if task_set['expt']['bg']['load']:
        try:
            matches = [path for path in path_data['save_path'].rglob('*') if base_name in path.name]
            roi_bg = np.load(matches[-1], allow_pickle=True)
            print(f'Loading {matches[-1].name}...')
        except FileNotFoundError:
            print('ROI data not found. Please run roi_acqnvs_3i')
            exit(1)
        return roi_bg, task_set

    # Creates an instance of slidebook reader
    sb_file_reader, task_set['roi']['capture'] = wait_for_reader_with_latest_capture(path_data['sldy_path'])
    task_set = get_recording_settings(sb_file_reader, task_set['roi']['capture'], task_set)

    roi_bg = np.full((task_set['roi']['recording_frames'], task_set['im']['resolution'][1], task_set['im']['resolution'][0]), np.nan)

    return recording_acqnvs_3i(roi_bg, task_set['roi']['recording_frames'], task_set, sb_file_reader, roi_bg_path, task_set['roi']['capture'], {'type': 'default'})


def get_roi_bg_sbaccess_old(task_set, path_data, sb_access):
    """
        Records region of interest and extracts the regions of interest (ROIs)

        Parameters:
            task_set: dictionary with bmi parameters
            path_data: paths to experiment data
            capture: integer denoting the desired capture within 3i .sldy file
            channel: type of channel
            roi_chan_data: list with channel and ROI data
            see_roi_data_flag: bool used to determine if ROIs should be plotted
            run: bool used to determine if the code should be run (typically ran unless code has been ran already)

        Returns:
            test_info: dictionary containing dataframes with voltage data.
    """
    base_name = 'roi_bg'
    #task_set['roi']['recording_frames'] = int(np.ceil(task_set['im']['frame_rate'] * task_set['roi']['recording_len'])) # Actual microscope fps seems to be halved
    task_set['roi']['recording_frames'] = 100
    roi_bg_path = path_data['save_path'] / f'{base_name}_{task_set["im"]["chan_data"]["recording_chan"].lower().replace(" ", "")}.npy'
    print(f'ROI recording will consist of {task_set["roi"]["recording_frames"]} frames')

    if task_set['expt']['bg']['load']:
        try:
            matches = [path for path in path_data['save_path'].rglob('*') if base_name in path.name]
            roi_bg = np.load(matches[-1], allow_pickle=True)
            print(f'Loading {matches[-1].name}...')
        except FileNotFoundError:
            print('ROI data not found. Please run roi_acqnvs_3i')
            exit(1)
        return roi_bg, task_set

    # Creates an instance of slidebook reader
    #task_set['roi']['capture'] = wait_for_latest_capture(sb_access) #may not be needed if sb_access is already connected to the correct capture
    task_set = get_recording_settings(sb_access, task_set['roi']['capture'], task_set)

    roi_bg = np.full((task_set['roi']['recording_frames'], task_set['im']['resolution'][1], task_set['im']['resolution'][0]), np.nan)
    #roi_bg = np.full((task_set['roi']['recording_frames'], 386, 400), np.nan)

    return recording_acqnvs_3i_sbaccess(roi_bg, task_set['roi']['recording_frames'], task_set, sb_access, roi_bg_path, task_set['roi']['capture'], {'type': 'default'})

def get_roi_data(image_data, path_data, task_set, plot=False, run=''):
    roi_data_path = path_data['save_path'] / 'roi_info.npz'
    # Checks if ROI file already exists
    if task_set['expt']['rois']['load']:
        try:
            roi_data = np.load(roi_data_path, allow_pickle=True)
            print(f'Loading {roi_data_path.name}...')
            return roi_data
        except FileNotFoundError:
            print('ROI data not found. Please run roi_acqnvs_3i')
            exit(1)

    # Check suite2p's way of creating the mean image and use that method.
    #image_data = np.load('F:cabmi/bmi_test/slidebook/capture_slide.dir/Streamtodisk-1765822852-121.imgdir/ImageData_Ch0_TP0000000.npy')
    # Don't create a mean. Pass to suite2p frame by frame
    im_raw = np.nanmean(image_data, axis=0)
    #im_raw = image_data

    # Single image is used to locate ROIs (Old method)
    #im_raw = sb_file_reader.ReadImagePlaneBuf(capture, 0, 0, 0, task_set['im']['chan_data']['green']['fp_idx'], True)
    #im_raw = path_data['test_data'][99]

    # Scale image to see ROIs better
    print('\nImage Scaling')
    print('----------------------------------------')
    im_sc_struct, _ = scale_im_interactive(im_raw, [],0)
    im_bg = im_sc_struct[-1]['im']
    plt.figure()
    plt.imshow(im_bg, cmap='bone', vmin=0, vmax=4 * np.nanmean(im_bg))
    plt.title('Background for tseROI Identification')
    plt.show()
    plt.close()
    print('----------------------------------------')

    plot_images = [{'im': None, 'label': ''} for _ in range(2)]
    plot_images[0]['im'] = im_raw # raw image
    plot_images[0]['label'] = 'green mean'
    plot_images[1]['im'] = im_bg # scaled image
    plot_images[1]['label'] = 'scaled'

    print('Obtaining ROI mask!')
    print('----------------------------------------')
    roi_mask = get_roi_mask(im_bg, path_data['save_path']) # must save suite2p files
    roi_chan_data = [{}]
    roi_data = label_mask2roi_data_single_channel(im_bg, roi_mask, roi_chan_data, task_set['im']['chan_data']['recording_chan'])

    # See ROI if needed
    if plot:
        plt.figure()
        plt.imshow(roi_data['roi_mask'], cmap='gray')
        plt.title(f'ROI Mask. Num Roi: {roi_data["num_rois"]}')
        plt.show()
        plt.close()

        plt.figure()
        plt.imshow(roi_data['im_roi'], cmap='gray')
        plt.title(f'ROI footprint overlay in blue. Num ROI: {roi_data["num_rois"]}')
        plt.show()
        plt.close()
    print('----------------------------------------')

    roi_info = {
        'plot_images': plot_images,
        'im_sc_struct': im_sc_struct,
        'roi_data': roi_data
    }

    if task_set['expt']['rois']['save']:
        np.savez_compressed(roi_data_path, **roi_info)

    return roi_info

def get_roi_bg_sbaccess_all_pmts(task_set, path_data, sb_access):
    frame_limit = 100
    frame_counter = 0
    channel_count = 2
    sb_rec_frames = 1  # The number of frames Slidebook will record per acquisition.
    save = True
    print('STARTING RECORDING!!!')
    sb_access.FocusWindowStreamSetNumberFrames(sb_rec_frames)
    capture = sb_access.StartStreaming()
    streaming = True

    try:
        # Assures that the streaming has started and that the first frame has been captured
        while True:
            res = sb_access.IsStreaming()
            last_capture = sb_access.GetLastImageStreamed(capture)
            if (res and last_capture >= 0):
                break

        # Assures that the number of channels in the capture matches the expected number of channels
        sb_channel_count = sb_access.GetNumChannels(capture)
        if sb_channel_count != channel_count:
            raise RuntimeError(
                "Incorrect number of channels; "
                f"Expected {channel_count}, got {sb_channel_count}"
            )

        # Creates a list of numpy arrays to store the image data for each channel
        rows = sb_access.GetNumYRows(capture)
        cols = sb_access.GetNumXColumns(capture)
        # image_data = [np.full((frame_limit, rows, cols), np.nan) for _ in range(sb_channel_count)]
        image_data = {sb_access.GetChannelName(capture, channel_index).lower().replace(" ", ""): np.full(
            (frame_limit, rows, cols), np.nan) for channel_index in range(sb_channel_count)}
        channel_names = image_data.keys()
        capture_indexes = []

        # Assures that the number of frames captured matches the expected number of frames
        while last_capture < frame_limit:
            prev_capture = last_capture
            last_capture = sb_access.GetLastImageStreamed(capture)

            # Captures have to be sequential
            if last_capture == prev_capture:
                continue
            capture_indexes.append(last_capture)
            # just take into account the red channel and gather the corresponding green channel data for the same frame
            if 'rpmt' in channel_names:
                image_data['rpmt'][frame_counter] = sb_access.ReadImagePlaneBuf(capture, 0, last_capture, 0,
                                                                                channel_names.index('rpmt'), True)
            else:
                raise RuntimeError(
                    "Channel 'rpmt' not found in SlideBook capture; "
                    f"Available channels: {channel_names}"
                )
            # Need to make sure capture of each frame is the same, otherwise, the frame counter will be off and the data will be misaligned
            # for channel_index in range(sb_channel_count):
            #    image_data[channel_index][frame_counter] = sb_access.ReadImagePlaneBuf(capture, 0, last_capture, 0, channel_index,True)
            frame_counter += 1
            print(f'*** Countdown: {frame_limit - frame_counter}')

    except KeyboardInterrupt:
        print('Keyboard Interrupt')
    finally:
        if save:
            for channel_index in range(sb_channel_count):
                np.save(path_data[
                            'save_path'] / f'roi_bg_{sb_access.GetChannelName(capture, channel_index).lower().replace(" ", "")}.npy',
                        image_data[channel_index], allow_pickle=True)
        if streaming:
            sb_access.StopStreaming()

def get_roi_bg_sbaccess(task_set, path_data, sb_access):
    frame_limit = int(np.ceil(task_set['im']['fs'] * task_set['im']['time_sec']))
    roi_channel = np.ceil(task_set['im']['roi_channel'])
    roi_bg_path = path_data['save_path'] / f'roi_bg_{roi_channel.lower().replace(" ", "")}.npy'
    save = task_set['im']['save'] # need to add
    frame_counter = 0

    print('STARTING RECORDING!!!')
    sb_access.FocusWindowStreamSetNumberFrames(task_set['im']['frames_to_average'])
    capture = sb_access.StartStreaming()
    streaming = True

    try:
        # Assures that the streaming has started and that the first frame has been captured
        while True:
            res = sb_access.IsStreaming()
            last_capture = sb_access.GetLastImageStreamed(capture)
            if (res and last_capture >= 0):
                break

        # Assures that the red channel is present in the capture
        sb_channel_count = sb_access.GetNumChannels(capture)
        channel_names = [
            sb_access.GetChannelName(capture, channel_index)
            for channel_index in range(sb_channel_count)
        ]
        if roi_channel not in channel_names:
            raise RuntimeError(
                f"'{roi_channel}' not found in SlideBook capture; "
                f"Available channels: {channel_names}"
            )

        # Creates a list of numpy arrays to store the image data for each channel
        rows = sb_access.GetNumYRows(capture)
        cols = sb_access.GetNumXColumns(capture)
        image_data = np.full((frame_limit, rows, cols), np.nan)

        # Assures that the number of frames captured matches the expected number of frames
        while last_capture < frame_limit:
            prev_capture = last_capture
            last_capture = sb_access.GetLastImageStreamed(capture)

            # Captures have to be sequential
            if last_capture == prev_capture:
                continue

            image_data[frame_counter] = sb_access.ReadImagePlaneBuf(capture, 0, last_capture, 0, channel_names.index(roi_channel), True)

            frame_counter += 1
            print(f'*** Countdown: {frame_limit - frame_counter}')
            print(f'Elapsed time: {sb_access.GetElapsedTime(capture, last_capture)} msec')  # This is just to ensure that the elapsed time is being updated
    finally:
        if streaming:
            sb_access.StopStreaming()
        if save:
            np.save(roi_bg_path, image_data, allow_pickle=True)

    n = sb_access.GetNumTimepoints(capture)
    fps = (n-1) / ((sb_access.GetElapsedTime(capture, n - 1) - sb_access.GetElapsedTime(capture, 0))/1000.0)
    print("Actual frame rate: ", fps)

    task_set['im']['capture'] = capture
    task_set['im']['shape'] = image_data.shape

    return image_data, task_set