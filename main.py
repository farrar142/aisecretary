import argparse
import os
import sys
from typing import Any
import openai
import pyaudio

from functions import OPEN_AI_KEY, list_audio_devices, loop, text_to_speach
from stt import STT
from tts import TTS

openai.api_key = OPEN_AI_KEY
# TODO:
# [O] WHISPER 서버를 이용한 음성 인식 기능 추가
# [O] 디스코드 웹훅 기능 추가
# [O] 컨텍스트 기억 기능 추가
# [X] AI 성격 추가


def tts_loader(p: pyaudio.PyAudio, tts: str):
    if tts == "xtts":
        return TTS.XTTS(p)
    return TTS.GTTS(p)


def stt_loader(stt: str):
    if stt == "local":
        return STT.LocalSTT()
    return STT.RemoteSTT()


def a(s: str):
    return s


def main(parser: argparse.ArgumentParser):
    p = pyaudio.PyAudio()
    args = parser.parse_args()
    tts = tts_loader(p, args.tts)
    stt = stt_loader(args.stt)
    list_audio_devices(p)
    result = loop(p, 2, tts=tts, stt=stt)
    print(result.failure())
    print("프로그램 종료.")
    p.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tts", default="xtts")
    parser.add_argument("--stt", default="local")

    # while True:
    #     runner = text_to_speach(tts)
    #     input("지문을 입력해주세요: ")
    #     runner("위키미디어 송년회가 12월 28일 신도림역 가온회의실에서 개최됩니다.")

    main(parser)
