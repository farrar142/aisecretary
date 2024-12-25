import os
from typing import Any
import openai
import pyaudio
import numpy as np
import requests
import whisper
from returns.maybe import Maybe, maybe
from returns.result import Result, safe, attempt
from dotenv import load_dotenv

from audio_recorder import AudioStream
from stt import STT, STTResult
from tts import TTS

OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
SECRETARY_NAMES = os.getenv("SECRETARY_NAMES", "비서").split(",")
DISCORD_WEB_HOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

load_dotenv()


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


def discord_webhook(content: str):
    if not DISCORD_WEB_HOOK_URL:
        return content
    requests.post(
        DISCORD_WEB_HOOK_URL,
        json=dict(content=content),
        headers={"Content-Type": "application/json"},
    )
    return content


@safe(exceptions=(KeyboardInterrupt, Exception))  # type:ignore
def loop(p: pyaudio.PyAudio, device_index: int, stt: STT, tts: TTS):
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
            response.map(discord_webhook).map(text_to_speach(tts))
