import os
import math
import numpy as np

def get_baseline(path, roi_data['roi_mask'], tset, a, fbset.arduino.pin) -> tuple[str, np.array]:
    try:
        experiment_length = math.ceil(tset['cb']['baseline_len']*tset['im']['frame_rate']*2) # Dialation factor = 2
        #mat_path = fullfile(path_data.savePath, ['BaselineOnline' datestr(datetime('now'), 'yymmddTHHMMSS') '.mat']);
        
        finishup = lambda: cleanMeUp(mat_path)

        # Prepare NIDAQ
        '''
        s = daq.createSession('ni');
        addDigitalChannel(s,'dev6','Port0/Line0:2','OutputOnly');
        ni_out = [0 0 0];
        outputSingleScan(s,ni_out);%set
        ni_getimage = [0 1 0];
        '''

        # Prepare 3i
        '''
        % connection to Prairie
        pl = actxserver('PrairieLink.Application');
        pl.Connect()

        % pause needed for prairie to respond
        pause(2)

        % Prairie variables
        px = pl.PixelsPerLine();
        py = pl.LinesPerFrame();

        % Prairie commands
        pl.SendScriptCommands("-srd True 0");
        pl.SendScriptCommands("-lbs True 0");
        '''

        # Define the path where the files will be saved
        save_path_3i = os.path.join(path['savePath'], 'im')

        # Check if the directory exists, and if not, create it
        if not os.path.exists(save_path_3i):
            os.makedirs(save_path_3i)

        # Call the savePrairieFiles function (assuming it's defined elsewhere)
        save_files_3i(path['savePath'], pl, 'baseline')

        '''
        lastFrame = zeros(px, py); % to compare with new incoming frames

        # set the environment for the Time Series in PrairieView
        pl.SendScriptCommands(f'-tsl {path_data["baseline_env"]}');
        '''

        base_activity = np.full((np.max(roi_mask), experiment_length), np.nan)

        # Prepare the Arduino
        if a is not None:
            a.writeDigitalPin("D9", 1)
            time.sleep(1)
            a.writeDigitalPin("D9", 0)

        # Run the acquisition
        frame = 1  # Initialize frame count
        time.sleep(2)
        pl.SendScriptCommands("-ts")
        print('Sent -ts, pausing')
        time.sleep(5)  # Empirical pause time for Prairie to start gears
        counter_same = 0
        print('Starting baseline acquisition')

        while counter_same < 500:
            im = pl.GetImage_2(tset['im']['chan_data']['chan_idx'], px, py)
            if not np.array_equal(im, lastFrame):
                start_time = time.time()
                lastFrame = im.copy()
                s.outputSingleScan(ni_getimage)
                time.sleep(0.001)
                s.outputSingleScan([0, 0, 0])
                unitVals = obtain_Roi(im, get_mask(roi_mask))
                base_activity[:, frame] = unitVals
                frame += 1
                counter_same = 0
                elapsed_time = time.time() - start_time
                if elapsed_time < 1 / (tset['im']['frameRate'] * 1.2):
                    time.sleep(1 / (tset['im']['frameRate'] * 1.2) - elapsed_time)
            else:
                counter_same += 1

        print('Finished baseline')
        playTone(a, apin, 7000, 1)
    finally:
        finishup()  # Ensure cleanup is called even if there's an exception

    return path, base_activity
