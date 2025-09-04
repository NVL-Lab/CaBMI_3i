from pathlib import Path
from datetime import datetime

def save_files_3i(save_path, pl, expt_str):
    """
    Function to set the paths for saving files.

    Parameters:
        path (str): the base path where files will be saved.
        pl:
        expt (str):
    """
    # Create the experiment directories
    save_path_3i = save_path / 'im'
    #save_path_3i.mkdir(parents=True, exist_ok=True)

    save_path_base_3i = save_path_3i / expt_str
    #save_path_base_3i.mkdir(parents=True, exist_ok=True)


    '''
    save_command = f"-p {save_path_base_3i}"
    pl.SendScriptCommands(save_command)

    timestamp = datetime.now().strftime('%y%m%dT%H%M%S')
    save_file_3i = f"-fn Tseries {expt_str}_{timestamp}"
    pl.SendScriptCommands(save_file_3i)
    '''