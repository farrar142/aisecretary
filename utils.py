import pyaudio
import requests
from returns.result import safe
from returns.maybe import Maybe

from consts import *
from ai.ai import AI
from recorder.audio_recorder import AudioStream
from converters.stt import STT, STTResult
from converters.tts import TTS


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
def loop(p: pyaudio.PyAudio, device_index: int, stt: STT, tts: TTS, ai: AI):
    from g2pk import G2p

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
            response = is_ai_call(prompt).bind(ai.run)
            # 응답을 tts로 출력해야됨
            response.map(print)
            response.bind(discord_webhook(prompt))
            response.bind(safe(G2p())).bind(tts.run)
