
import os
from datetime import datetime

def save_files_3i(path, pl, expt) -> None:
    """
    Function to set the paths for saving files.

    Parameters:
        path (str): the base path where files will be saved.
        pl: 
        expt (str):
    """

    # Create the experiment directory
    save_path = os.path.join(path, 'im', expt)
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Construct and send the save command
    save_command = f'-p {save_base_path}'
    #pl.SendScriptCommands(save_command)

    # Construct the filename with a timestamp and send the command
    timestamp = datetime.now().strftime('%y%m%dT%H%M%S')
    save_file = f'-fn Tseries {expt}_{timestamp}'
    #pl.SendScriptCommands(save_file)
