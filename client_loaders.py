from functools import cache
import pyaudio
from converters.tts import TTS
from converters.stt import STT
from ai.ai import AI
from settings import Setting


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


@cache
def openai_loader():
    from openai import OpenAI

    return OpenAI(api_key=Setting.OPEN_AI_KEY)


@cache
def whisper_loader():
    import whisper

    return whisper.load_model(
        name=Setting.WHISPER_MODEL_NAME, device=Setting.WHISPER_DEVICE
    )
