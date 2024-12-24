import os
from typing import Any
import openai
import pyaudio
import numpy as np
import whisper
from returns.maybe import Maybe, maybe
from returns.result import Result, safe, attempt
from dotenv import load_dotenv

from stt import STT, STTResult

load_dotenv()

from audio_recorder import AudioStream
from tts import TTS

OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
SECRETARY_NAMES = os.getenv("SECRETARY_NAMES", "비서").split(",")
openai.api_key = OPEN_AI_KEY
# TODO:
# WHISPER 서버를 이용한 음성 인식 기능 추가
# 컨텍스트 기억 기능 추가
# 디스코드 웹훅 기능 추가


def list_audio_devices(p: pyaudio.PyAudio):
    print("사용 가능한 오디오 디바이스 목록:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"{i}: {info['name']}")


# 오디오 -> 텍스트
def audio_to_text(model: whisper.Whisper):
    def inner(d: np.ndarray) -> dict[str, Any]:
        return model.transcribe(d, fp16=False, language="ko")

    return inner


def get_text(data: STTResult):
    return str(data["text"]).strip()


# 텍스트 필터링
@safe(exceptions=(Exception,))
def is_ai_call(prompt: str):
    target = next(filter(lambda x: prompt.startswith(x), SECRETARY_NAMES), None)
    if target:
        return prompt.removeprefix(target)
    raise Exception


def send_prompt_to_ai(text: str, model_name: str = "gpt-3.5-turbo") -> str:
    response = openai.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text},
        ],
    )
    translated_text = (response.choices[0].message.content or "").strip()
    return translated_text


def text_to_speach(tts: TTS):
    def inner(text: str):
        tts.run(text)

    return inner


@safe(exceptions=(KeyboardInterrupt, Exception))  # type:ignore
def loop(p: pyaudio.PyAudio, device_index: int):
    tts = TTS.XTTS(p)
    stt = STT.RemoteSTT()
    with AudioStream(p, device_index) as stream:
        print("\n실시간 음성 입력을 녹음하고 변환합니다.\n")
        while True:
            audio_data = stream.detect_audio()
            # 오디오 데이터를 텍스트로 변환
            text = audio_data.map(stt.run).value_or("").strip()
            print(f"{text=}")
            if not text:
                continue
            response = is_ai_call(text).map(send_prompt_to_ai)
            # 응답을 tts로 출력해야됨
            response.map(print)
            response.map(text_to_speach(tts))


def main():
    p = pyaudio.PyAudio()
    list_audio_devices(p)
    result = loop(p, 2)
    print(result.failure())
    print("프로그램 종료.")
    p.terminate()


if __name__ == "__main__":
    main()
