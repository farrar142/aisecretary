from contextlib import contextmanager
from io import BytesIO
import uuid
from gtts import gTTS
import pyaudio
from playsound import playsound
import requests
from returns.result import safe


class TTS:
    def __init__(self, p: pyaudio.PyAudio, *args, **kwargs):
        self.p = p

    def get_response(self, text: str): ...

    def run(self, text: str):
        return safe(self.get_response)(text)

    @staticmethod
    def XTTS(p: pyaudio.PyAudio) -> "TTS":
        return XTTSStream(p=p)

    @staticmethod
    def GTTS(p: pyaudio.PyAudio) -> "TTS":
        return GTTS(p=p)


class XTTSFile(TTS):
    def get_response(self, text: str):
        r = requests.post(
            "http://localhost:8020/tts_to_audio",
            headers={"Content-Type": "application/json"},
            json={
                "text": text,
                "speaker_wav": "calm_female",
                "language": "ko",
            },
        )
        with self.player() as stream:
            stream.write(r.content)

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


class XTTSStream(TTS):
    def get_response(self, text: str):
        with self.player() as stream:
            r = requests.get(
                "http://localhost:8020/tts_stream",
                headers={"Content-Type": "application/json"},
                params={
                    "text": text,
                    "speaker_wav": "calm_female",
                    "language": "ko",
                },
                stream=True,
            )
            with BytesIO() as io:
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

    def get_response(self, text: str):
        tts = gTTS(text, lang="ko", slow=False)
        tts.save(self.file_name)
        self.player()

    def player(self):
        playsound(self.file_name)
