import argparse
import openai
import pyaudio

from ai.ai import AI
from programs import (
    get_record_device,
    loop,
)
from converters.stt import STT
from converters.tts import TTS
from settings import Setting

openai.api_key = Setting.OPEN_AI_KEY
# TODO:
# [O] WHISPER 서버를 이용한 음성 인식 기능 추가
# [O] 디스코드 웹훅 기능 추가
# [O] 컨텍스트 기억 기능 추가
# [X] AI 성격 추가


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


def main(parser: argparse.ArgumentParser):
    p = pyaudio.PyAudio()
    args = parser.parse_args()
    tts = tts_loader(p, args.tts)
    stt = stt_loader(args.stt)
    ai = ai_loader()
    device = get_record_device(p)
    result = device.bind(lambda x: loop(p, x, tts=tts, stt=stt, ai=ai))
    print(result.failure())
    print("프로그램 종료.")
    p.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tts", default="xtts")
    parser.add_argument("--stt", default="local")
    main(parser)
