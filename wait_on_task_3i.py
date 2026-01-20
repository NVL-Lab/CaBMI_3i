from SBReadFile22.SBReadFile import *
import time

def wait_for_reader_with_latest_capture(file_path, wait_seconds=500):
    for attempt in range(wait_seconds):
        if not file_path.exists():
            print(
                f"{file_path} does not exist. Retrying for up to {wait_seconds} seconds.\n"
                "Press Ctrl+C to exit."
            )
            time.sleep(1)
            continue

        try:
            reader = SBReadFile()
            reader.Open(str(file_path), All=False)
            curr_capture = reader.GetNumCaptures()-1
            capture = curr_capture
            for capture_look in range(wait_seconds):
                if capture <= curr_capture:
                    print('Finding Capture...')
                    reader = SBReadFile()
                    reader.Open(str(file_path), All=False)
                    capture = reader.GetNumCaptures()-1
                else:
                    return reader, capture
        except Exception as e:
            print(f'Unexpected error: {e}')
            print('Exiting...')
            break
    print("Giving up.")
    exit(1)

def wait_for_reader_with_capture(file_path, capture, wait_seconds=500):
    for attempt in range(wait_seconds):
        if not file_path.exists():
            print(
                f"{file_path} does not exist. Retrying for up to {wait_seconds} seconds.\n"
                "Press Ctrl+C to exit."
            )
            time.sleep(1)
            continue

        try:
            reader = SBReadFile()
            reader.Open(str(file_path), All=False)
            for capture_look in range(wait_seconds):
                if reader.GetNumCaptures() <= capture:
                    print('Finding Capture...')
                    reader = SBReadFile()
                    reader.Open(str(file_path), All=False)
            return reader
        except Exception as e:
            print(f'Unexpected error: {e}')
            print('Exiting...')
            break
    print("Giving up.")
    exit(1)

def wait_for_reader(file_path, wait_seconds=500):
    for attempt in range(wait_seconds):
        if not file_path.exists():
            print(
                f"{file_path} does not exist. Retrying for up to {wait_seconds} seconds.\n"
                "Press Ctrl+C to exit."
            )
            time.sleep(1)
            continue

        try:
            reader = SBReadFile()
            reader.Open(str(file_path), All=False)
            return reader
        except FileNotFoundError:
                print(f"Attempt {attempt + 1}: file not ready, retrying...")
    print("Giving up.")
    exit(1)

def wait_for_capture(file_path, reader, capture, wait_seconds=500):
    # ~33-40 frames to start recording
    # ~20 if no captures are available before
    try:
        for capture_look in range(wait_seconds):
            if reader.GetNumCaptures() <= capture:
                print("Finding Capture...")
                reader = SBReadFile()
                reader.Open(str(file_path), All=False)
    except KeyboardInterrupt:
        print('Exiting...')

    return reader

def get_recording_settings(sb_file_reader, capture, task_set, default_run):
    channel_count = sb_file_reader.GetNumChannels(capture)
    print(f'*** Number of channels in Capture {capture}: {channel_count}')

    channels_available = []
    for channel_index in range(channel_count):
        channel_name = sb_file_reader.GetChannelName(capture, channel_index)
        task_set['im']['chan_data'][channel_name] = channel_index
        channels_available.append(channel_name)

    if channel_count > 1:
        if default_run:
            channel_name = 'R PMT'
            channel_index = channels_available.index(channel_name)
        else:
            channel_index = int(input(f'Select which channel to image from: {channels_available} (Type 0 to n-1)'))
            channel_name = channels_available[channel_index]
    else:
        channel_index = 0
        channel_name = channels_available[channel_index]
    task_set['im']['chan_data']['recording_chan'] = channel_name

    print(f'Recording from {channel_name} in the following capture: {sb_file_reader.GetImageName(channel_index)}...')
    '''
            if channel == 'green':
                task_set['im']['chan_data'][channel]['pmt_idx'] = 0
            else:  # channel == 'red'
                task_set['im']['chan_data'][channel]['pmt_idx'] = 1
    '''

    task_set['im']['resolution'] = (sb_file_reader.GetNumXColumns(channel_index),
                                    sb_file_reader.GetNumYRows(channel_index))

    return task_set