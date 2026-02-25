author_= 'Saul Gurgua Lopez'

import numpy as np
import sounddevice as sd

def make_stream(sr:int=44100):
    return sd.OutputStream(
        samplerate=sr,
        channels=1,
        dtype='float32',
        blocksize=64,#512,
        latency=0#'low'
    )

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
    wave = vol * np.sin(2 * np.pi * freq * t).astype(np.float32)
    sd.play(wave, sr)
    sd.wait()

def get_tone(freq, duration, amplitude=0.2, sr:int=44100):
    n_samples = int(sr * duration)
    t = np.arange(n_samples) / sr
    tone = amplitude * np.sin(2 * np.pi * freq * t)

    return np.float32(tone)