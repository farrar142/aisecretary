from collections import deque
import pyaudio
import numpy as np
from returns.maybe import maybe, Maybe
from returns.result import safe


def get_volume(audio_chunk: np.ndarray):
    return np.max(np.abs(audio_chunk))


class AudioStream:
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000  # Whisper는 16kHz 샘플링 레이트 사용
    THRESHOLD = 500  # 소음 임계값
    SILENCE_DURATION = 2  # 소리가 없어진 후 종료까지의 시간 (초)

    def __init__(self, p: pyaudio.PyAudio, device_index: int):
        self.stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.CHUNK,
        )
        self.device_index = device_index

    def read(self, size: int = CHUNK) -> np.ndarray:
        data = self.stream.read(size)
        audio_chunk = np.frombuffer(data, dtype=np.int16)
        return audio_chunk

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @safe
    def detect_audio(self):
        return RecordingSession(self).record()

    @staticmethod
    def translate_16_to_32(audio_data: np.ndarray):
        # 오디오 데이터를 부동소수점으로 변환 및 정규화
        return audio_data.astype(np.float32) / 32768.0


class ThresholdNotExceeded(Exception):
    pass


class RecordingSession:
    @property
    def STAND_BY_TIME(self):
        return self.stream.SILENCE_DURATION * self.stream.RATE / self.stream.CHUNK

    def __init__(self, stream: AudioStream):
        self.stream = stream
        self.silent_frames = 0
        self.is_record_started = False
        self.frames = []
        self.pre_frames = deque([], maxlen=int(self.STAND_BY_TIME / 2))

    def get_audio_frames(self):
        frames = list(self.pre_frames) + self.frames
        return np.hstack(frames)

    def start_record(self, dummy: None):
        if not self.is_record_started:
            self.is_record_started = True
            print("레코딩 시작")

    @safe(exceptions=(ThresholdNotExceeded,))
    def is_volume_over_threshold(self, audio_chunk: np.ndarray):
        # 현재 청크의 최대 진폭 계산
        if get_volume(audio_chunk) < self.stream.THRESHOLD:
            self.silent_frames += 1
            raise ThresholdNotExceeded
        self.silent_frames = 0

    def append_frames(self, audio_chunk: np.ndarray):
        if not self.is_record_started:
            self.pre_frames.append(audio_chunk)
        else:
            self.frames.append(audio_chunk)

    def record(self):
        while True:
            audio_chunk = self.stream.read()
            self.is_volume_over_threshold(audio_chunk).map(self.start_record)
            self.append_frames(audio_chunk)
            if not self.is_record_started:
                continue
            # 소리가 없어진 후 지정된 시간만큼 대기
            if self.silent_frames > self.STAND_BY_TIME:
                break
        return self.get_audio_frames()
