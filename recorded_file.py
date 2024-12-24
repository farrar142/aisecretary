from io import BytesIO
import numpy as np
import wave

import pyaudio


class RecordedFile:
    def __init__(
        self,
        p: pyaudio.PyAudio,
        ndarray: np.ndarray,
        file_name: str,
        rate: int,
        channels: int,
    ):
        self.p = p
        self.ndarray = ndarray
        self.file_name = file_name
        self.rate = rate
        self.channels = channels

    def translate_16_to_32(self):
        return self.ndarray.astype(np.float32) / 32768.0

    def to_file(self):
        io = BytesIO()
        io.name = self.file_name
        with wave.open(io, "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wav_file.setframerate(self.rate)
            wav_file.writeframes(self.ndarray.tobytes())
        io.seek(0)
        with open(self.file_name, "wb") as f:
            f.write(io.read())
        io.seek(0)
        return io
