"""Frame reading module.

Extracts frames from a video file at a configurable rate (FR-4, FR-5).
"""
from __future__ import annotations

from typing import Iterator, List

import cv2

from .models import Frame, VideoFile


class FrameExtractor:
    """Reads frames from a VideoFile at a configurable sampling rate (fps)."""

    def __init__(self, frame_rate: float = 1.0) -> None:
        """
        :param frame_rate: how many frames per second of source video to sample.
                           1.0 means one frame every second, 0.5 means one frame every two seconds.
        """
        if frame_rate <= 0:
            raise ValueError("frame_rate must be positive")
        self.frame_rate = frame_rate

    def extract_frames(self, video: VideoFile) -> List[Frame]:
        return list(self.iter_frames(video))

    def iter_frames(self, video: VideoFile) -> Iterator[Frame]:
        if not video.exists():
            raise FileNotFoundError(f"Video not found: {video.path}")

        cap = cv2.VideoCapture(video.path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {video.path}")

        try:
            source_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            video.duration = total_frames / source_fps if source_fps else 0.0

            step = max(1, int(round(source_fps / self.frame_rate)))
            index = 0
            frame_idx = 0
            while True:
                ret, image = cap.read()
                if not ret:
                    break
                if frame_idx % step == 0:
                    timestamp = frame_idx / source_fps
                    yield Frame(index=index, timestamp=timestamp, image=image)
                    index += 1
                frame_idx += 1
        finally:
            cap.release()
