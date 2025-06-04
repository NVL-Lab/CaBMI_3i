import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from params import define_bmi_task_settings, define_fb_audio_settings

def run_experiment_simulation(df, folder_list):
    """
    Function to run the simulations both ways from a dataframe df that contains
    info about the experiments (normally obtained posthoc with Python analysis).
    """
    
    tset = define_bmi_task_settings()
    fbset = define_fb_audio_settings()
    frames_per_reward_range = tset['cb']['sec_per_reward_range'] * tset['im']['frameRate']
    simulations_went_wrong = []
    
    # Iterate through all the mice
    for _, row in df.iterrows():
        print(f"Processing row: {row['session_path']}")
        
        # Obtain the correct folders where the data is stored
        data_path = find_data_path(folder_list, row['mice_name'])
        folder_raw = os.path.join(data_path, 'raw', row['session_path'])
        folder_process = os.path.join(data_path, 'process', row['session_path'])
        
        n_f_file = os.path.join(folder_raw, row['Baseline_online'])
        roi_data_file = os.path.join(folder_raw, row['roi_data'])
        folder_save = os.path.join(folder_process, 'simulation')
        os.makedirs(folder_save, exist_ok=True)
        
        # Obtain and clean the raw data
        bmi_raw_data = clean_bmi_raw_data(os.path.join(folder_raw, row['BMI_online']))
        if 'frame' not in bmi_raw_data['data']:
            continue
        
        # Run simulation of T1 using the same target file
        simulated_data_T1 = BMI_simulation(bmi_raw_data['data']['bmiAct'], tset, bmi_raw_data['bData'])
        
        if simulated_data_T1['selfTargetCounter'] != bmi_raw_data['data']['selfTargetCounter']:
            print("Something went wrong, simulated data is not the same as raw data")
            simulations_went_wrong.append(row['session_path'])
        
        data = simulated_data_T1
        bData = bmi_raw_data['bData']
        save_path_T1 = os.path.join(folder_save, f"simulated_data_T1_{datetime.now().strftime('%y%m%dT%H%M%S')}.pkl")
        pd.to_pickle({'data': data, 'bData': bData}, save_path_T1)
        
        # Obtain a target file for T2 based on baseline
        target_info_path, _, _ = baseline2target(n_f_file, roi_data_file,  
            bmi_raw_data['bData']['E2_base'], bmi_raw_data['bData']['E1_base'], 
            frames_per_reward_range, tset, folder_save, fbset)
        
        target_info_T2 = pd.read_pickle(target_info_path)
        
        # Run simulation of T2
        bmiAct_T2 = np.vstack((bmi_raw_data['data']['bmiAct'][2:4, :], bmi_raw_data['data']['bmiAct'][0:2, :]))
        simulated_data_T2 = BMI_simulation(bmiAct_T2, tset, target_info_T2)
        
        data = simulated_data_T2
        bData = target_info_T2
        save_path_T2 = os.path.join(folder_save, f"simulated_data_T2_{datetime.now().strftime('%y%m%dT%H%M%S')}.pkl")
        pd.to_pickle({'data': data, 'bData': bData}, save_path_T2)
    
    return simulations_went_wrong
