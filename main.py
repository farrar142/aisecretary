import argparse
import pyaudio
from returns.result import safe

from ai.ai import AI
from utils import (
    discord_webhook,
    get_record_device,
    is_ai_call,
)
from converters.stt import STT
from converters.tts import TTS
from recorder.audio_recorder import AudioStream
from settings import Setting
from client_loaders import tts_loader, stt_loader, ai_loader

# TODO:
# [O] WHISPER 서버를 이용한 음성 인식 기능 추가
# [O] 디스코드 웹훅 기능 추가
# [O] 컨텍스트 기억 기능 추가
# [X] AI 성격 추가


@safe(exceptions=(KeyboardInterrupt, Exception))  # type:ignore
def loop(p: pyaudio.PyAudio, device_index: int, stt: STT, tts: TTS, ai: AI):
    from g2pk import G2p

    g2p = G2p()

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
            response.map(lambda response: print(f"{response=}"))
            response.map(discord_webhook(prompt))
            response.bind(safe(g2p)).map(tts.run)


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
