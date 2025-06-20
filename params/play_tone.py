author_= 'Saul Gurgua Lopez'

import numpy as np
import sounddevice as sd

def play_tone(freq:float, dur:float, vol:float=0.5, sr:int=44100) -> None:
    """
        Play a tone through default computer speakers

        Parameters:
            freq: frequency in Hz
            dur: duration in seconds
            vol: volume from 0.0 (silent) to 1.0 (max)
            sr: sample rate (default 44100 Hz)
    """
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    wave = vol * np.sin(2 * np.pi * freq * t)
    sd.play(wave, sr)
    sd.wait()  # Wait until sound is done