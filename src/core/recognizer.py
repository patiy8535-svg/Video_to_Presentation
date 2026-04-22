"""Recognizer — turns a stream of frames into unique slides.

Flow (see docx/SequenceDiagram_ProcessVideo.puml):
    1. For each incoming frame: detect the slide region and crop to it.
    2. Compare the cropped frame to the last accepted slide.
    3. Keep only frames that differ enough — those are new unique slides.
"""
from __future__ import annotations

from typing import List, Optional

from .border_detector import BorderDetector
from .models import Frame, Slide
from .slide_comparator import SlideComparator


class Recognizer:
    """Produces a list of unique Slide objects from a list of Frames."""

    def __init__(
        self,
        border_detector: Optional[BorderDetector] = None,
        comparator: Optional[SlideComparator] = None,
    ) -> None:
        self.border_detector = border_detector or BorderDetector()
        self.comparator = comparator or SlideComparator()

    def recognize(self, frames: List[Frame]) -> List[Slide]:
        unique: List[Slide] = []
        last_frame: Optional[Frame] = None

        for frame in frames:
            bounds = self.border_detector.detect_borders(frame)
            cropped = self.border_detector.crop_to_slide(frame, bounds)

            if last_frame is None or not self.comparator.are_similar(last_frame, cropped):
                slide = Slide(index=len(unique), image=cropped.get_image())
                unique.append(slide)
                last_frame = cropped

        return unique
