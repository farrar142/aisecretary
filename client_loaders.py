import pyaudio
from converters.tts import TTS
from converters.stt import STT
from ai.ai import AI


def tts_loader(p: pyaudio.PyAudio, tts: str):
    if tts == "gtts":
        return TTS.GTTS(p)
    return TTS.XTTS(p)


def stt_loader(stt: str):
    if stt == "remote":
        return STT.RemoteSTT()
    return STT.LocalSTT()


def ai_loader():
    return AI.ChatGPT()
