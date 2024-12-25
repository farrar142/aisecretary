from collections import deque
from typing import Any
import pyaudio
import numpy as np
from returns.maybe import maybe, Maybe
from returns.result import safe, Result

from fixed_queue import FixedQueue
from recorded_file import RecordedFile

AudioChunk = np.ndarray[Any, np.dtype[np.int16]]


def get_volume(audio_chunk: np.ndarray):
    return np.max(np.abs(audio_chunk))


class AudioStream:
    CHUNK = 1000
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000  # Whisper는 16kHz 샘플링 레이트 사용
    THRESHOLD = 500  # 소음 임계값
    SILENCE_DURATION = 2  # 소리가 없어진 후 종료까지의 시간 (초)

    def __init__(self, p: pyaudio.PyAudio, device_index: int):
        self.p = p
        self.stream = p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.CHUNK,
        )
        self.device_index = device_index

    def read(self, size: int = CHUNK) -> np.ndarray[Any, np.dtype[np.int16]]:
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


class ThresholdExceed(Exception): ...


class RecordingSession:
    @property
    def STAND_BY_TIME(self):
        return self.stream.SILENCE_DURATION * self.stream.RATE / self.stream.CHUNK

    def __init__(self, stream: AudioStream):
        self.stream = stream
        self.THRESHOLD = stream.THRESHOLD
        self.silent_frames = 0
        self.is_record_started = False
        self.main_frames: list[AudioChunk] = []
        self.pre_frames = deque[AudioChunk]([], maxlen=int(self.STAND_BY_TIME / 2))
        self.pop_noise_check_queue: FixedQueue[float] = FixedQueue(
            [], int(self.STAND_BY_TIME / 2)
        )

    def to_recorded_file(self) -> RecordedFile:
        frames = np.hstack(list(self.pre_frames) + self.main_frames)
        return RecordedFile(
            self.stream.p,
            ndarray=frames,
            file_name="recorded.wav",
            rate=self.stream.RATE,
            channels=self.stream.CHANNELS,
        )

    @staticmethod
    def get_max_volume(audio_chunk: AudioChunk):
        return np.max(np.abs(audio_chunk))

    @maybe
    def handle_silent_frames(self, audio_chunk: AudioChunk):
        # 현재 청크의 최대 진폭 계산
        vol: int = self.get_max_volume(audio_chunk)
        if vol < self.THRESHOLD:
            self.silent_frames += 1
            return True
        self.silent_frames = 0
        return None

    def handle_start_recording(self):
        if self.is_record_started:
            return
        self.is_record_started = True
        print("레코딩 시작")

    def handle_frames(self, audio_chunk: AudioChunk):
        if not self.is_record_started:
            self.pre_frames.append(audio_chunk)
        else:
            self.main_frames.append(audio_chunk)

            self.pop_noise_check_queue.append(self.get_max_volume(audio_chunk))

    def handle_pop_noise(self):
        if self.pop_noise_check_queue.is_full:
            if np.mean(self.pop_noise_check_queue) <= self.THRESHOLD:
                self.clear()
                print("low volume")
                return True
        return False

    def clear(self):
        self.silent_frames = 0
        self.is_record_started = False
        self.main_frames.clear()
        self.pop_noise_check_queue.clear()

    def record(self) -> RecordedFile:
        while True:
            audio_chunk = self.stream.read()
            self.handle_silent_frames(audio_chunk).or_else_call(
                self.handle_start_recording
            )
            # 오디오 청크 어레이에 데이터 추가
            self.handle_frames(audio_chunk)
            if not self.is_record_started:
                continue
            if self.handle_pop_noise():
                self.clear()
                continue
            # 소리가 없어진 후 지정된 시간만큼 대기
            if self.silent_frames > self.STAND_BY_TIME:
                break
        return self.to_recorded_file()
