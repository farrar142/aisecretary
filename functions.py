from collections import deque
import os
from typing import Callable, Iterable, Union
import openai
import pyaudio
import requests
from returns.result import safe
from returns.maybe import Maybe
from dotenv import load_dotenv
from g2pk import G2p

from audio_recorder import AudioStream
from stt import STT, STTResult
from tts import TTS
from context_memorizer import System, Message, memorize_context, memorize_context_json

load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
SECRETARY_NAMES = os.getenv("SECRETARY_NAMES", "비서").split(",")
DISCORD_WEB_HOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
RECORD_DEVICE = os.getenv("RECORD_DEVICE", None)


def list_audio_devices(p: pyaudio.PyAudio):
    print("사용 가능한 오디오 디바이스 목록:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"{i}: {info['name']}")


@safe
def get_record_device(p: pyaudio.PyAudio):
    def select_device():
        list_audio_devices(p)
        selected = input("디바이스 선택: ")
        return int(selected)

    return Maybe.from_optional(RECORD_DEVICE).map(int).or_else_call(select_device)


def get_text(data: STTResult):
    return str(data["text"]).strip()


# 텍스트 필터링
@safe(exceptions=(Exception,))
def is_ai_call(prompt: str):
    target = next(filter(lambda x: prompt.startswith(x), SECRETARY_NAMES), None)
    if target:
        return prompt.removeprefix(target)
    raise Exception


@memorize_context_json
# @memorize_context
def send_prompt_to_ai(
    context: Iterable[Message], model_name: str = "gpt-3.5-turbo"
) -> str:
    total_context: list[Message] = [
        System(content="You are a helpful assistant"),
    ]
    total_context.extend(context)
    response = openai.chat.completions.create(
        model=model_name,
        messages=total_context,
    )
    return (response.choices[0].message.content or "").strip()


def discord_webhook(text: str):
    @safe
    def inner(content: str):
        if not DISCORD_WEB_HOOK_URL:
            return content
        requests.post(
            DISCORD_WEB_HOOK_URL,
            json=dict(content=text + "\n" + content),
            headers={"Content-Type": "application/json"},
        )
        return content

    return inner


@safe(exceptions=(KeyboardInterrupt, Exception))  # type:ignore
def loop(p: pyaudio.PyAudio, device_index: int, stt: STT, tts: TTS):
    with AudioStream(p, device_index) as stream:
        print("\n실시간 음성 입력을 녹음하고 변환합니다.\n")
        while True:
            # 오디오 데이터 반환
            audio_data = stream.detect_audio()
            # 오디오 데이터를 텍스트로 변환
            prompt = audio_data.map(stt.run).value_or("").strip()
            print(f"{prompt=}")
            if not prompt:
                continue
            # 텍스트로 ai 응답 생성
            response = is_ai_call(prompt).bind(send_prompt_to_ai)
            # 응답을 tts로 출력해야됨
            response.map(print)
            response.bind(discord_webhook(prompt))
            response.bind(safe(G2p())).bind(tts.text_to_speech)
