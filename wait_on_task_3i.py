from SBReadFile22.SBReadFile import *
import time

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
            # Issue with keyboard interrupt
            while reader.GetNumCaptures() <= capture:
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
        if file_path.exists():
            try:
                reader = SBReadFile()
                reader.Open(str(file_path), All=False)
                return reader
            except FileNotFoundError:
                print(f"Attempt {attempt + 1}: file not ready, retrying...")
        else:
            if attempt == 0:
                print(
                    f"{file_path} does not exist. Retrying for up to {wait_seconds} seconds\n"
                    "Press Ctrl+C to exit."
                )
        time.sleep(1)
    print("Giving up.")
    exit(1)

def wait_for_capture(file_path, reader, capture):
    # ~33-40 frames to start recording
    try:
        while reader.GetNumCaptures() < capture + 1:
            print("Finding Capture...")
            reader = SBReadFile()
            reader.Open(str(file_path), All=False)
    except KeyboardInterrupt:
        print('Exiting...')

    return reader