from contextlib import contextmanager
import uuid
from gtts import gTTS
import pyaudio
from playsound import playsound
import requests


class TTS:
    def __init__(self, p: pyaudio.PyAudio, *args, **kwargs):
        self.p = p

    def run(self, text: str): ...
    @staticmethod
    def XTTS(p: pyaudio.PyAudio) -> "TTS":
        return XTTS(p=p)

    @staticmethod
    def GTTS(p: pyaudio.PyAudio) -> "TTS":
        return GTTS(p=p)


class XTTS(TTS):
    def run(self, text: str):
        with self.player() as stream:
            r = requests.get(
                "http://localhost:8020/tts_stream",
                headers={"Content-Type": "application/json"},
                params={
                    "text": text,
                    "speaker_wav": "calm_female.wav",
                    "language": "ko",
                },
                stream=True,
            )
            with r:
                for chunk in r.iter_content(chunk_size=1024):
                    stream.write(chunk)

    @contextmanager
    def player(self):
        try:
            stream = self.p.open(
                format=pyaudio.paInt16, channels=1, rate=int(24000), output=True
            )
            yield stream
        finally:
            stream.start_stream()
            stream.close()


class GTTS(TTS):
    def __init__(self, *args, **kwargs):
        self.file_name = uuid.uuid4().hex + ".mp3"
        super().__init__(*args, **kwargs)

    def run(self, text: str):
        tts = gTTS(text, lang="ko", slow=False)
        tts.save(self.file_name)
        self.player()

    def player(self):
        playsound(self.file_name)
