from SBReadFile22.SBReadFile import *
import time

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

def wait_for_capture(file_path, reader, capture, wait_seconds=500):
    # ~45 frames to start recording
    # may need to change 3i code
    for attempt in range(wait_seconds):
        if reader.GetNumCaptures() < capture + 1:
            try:
                print("Reopening sldy...")
                reader = SBReadFile()
                reader.Open(str(file_path), All=False)
                reader.Refresh(capture)
                return reader
            except Exception as e:
                #print(f"Attempt {attempt + 1}: capture not available, retrying...")
                print('hello')
        else:
            return reader
        #time.sleep(0.0001)
    print("Giving up.")
    exit(1)