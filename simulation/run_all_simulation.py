import os
import sys
import pandas as pd
from scipy.io import loadmat

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

# Functions
from run_experiment_simulation import run_experiment_simulation
from bmi_simulation import bmi_simulation
from params.define_bmi_task_settings import get_bmi_settings

'''
Chain of command:
    <this> -> 'run_experiment_simulation' -> 'bmi_simulation'
'''

def main():
    """
    Script to run all the simulations.
    """
    folder_list = {'FA': 'D:/data', 'FB': 'F:/data', 'FC': 'G:/data'}
    folder_df = 'C:/Users/Nuria/Documents/DATA/D1exp/df_data'
    
    # Unsure what these are these?
    df_control = pd.read_parquet(os.path.join(folder_df, 'df_CONTROL.parquet'))
    df_control_ago = pd.read_parquet(os.path.join(folder_df, 'df_CONTROL_AGO.parquet'))
    df_control_light = pd.read_parquet(os.path.join(folder_df, 'df_CONTROL_LIGHT.parquet'))
    df_d1act = pd.read_parquet(os.path.join(folder_df, 'df_D1act.parquet'))
    df_random = pd.read_parquet(os.path.join(folder_df, 'df_RANDOM.parquet'))
    df_delay = pd.read_parquet(os.path.join(folder_df, 'df_DELAY.parquet'))
    df_no_audio = pd.read_parquet(os.path.join(folder_df, 'df_NO_AUDIO.parquet'))
    
    simulations_wrong = []
    
    for df in [df_d1act, df_control, df_control_ago, df_control_light, df_random, df_delay, df_no_audio]:
        simulations_wrong.extend(run_experiment_simulation(df, folder_list))
    
    print(simulations_wrong)

if __name__ == '__main__':
    #main()
    #args = sys.argv[1:]
    bmi_data = loadmat('/Users/saulglopez/Scripts/uab/nvl_lab/CaBMI/data/m13_221112_D01_bmi/BMI_online221112T103553.mat')
    tset = get_bmi_settings()
    data = bmi_simulation(bmi_data['data']['bmiAct'][0][0], tset, bmi_data['bData'][0][0]) #target_info
    # Check for correctness
    for var in data:
        print(f'{var}:')
        print(data[var])
