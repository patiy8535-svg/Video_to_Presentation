"""Recognizer — turns a stream of frames into a list of unique slides.

Flow (see docx/SequenceDiagram_ProcessVideo.puml):
    1. Calibrate BorderDetector on a sample of frames to lock in a stable
       slide quadrilateral (robust to occlusions like a moving presenter).
    2. For each frame: crop + dewarp to the slide region.
    3. Compare the cropped frame against EVERY already-accepted slide.
       Accept it only if it's different from all of them. This also handles
       the case where the presenter revisits an earlier slide — the revisit
       is not stored as a second copy.
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
        # Stabilize the slide region across the whole clip, so the same pixels
        # are cropped from every frame. Essential for reliable dedup.
        calibrate = getattr(self.border_detector, "calibrate", None)
        if callable(calibrate):
            calibrate(frames)

        accepted: List[Frame] = []
        slides: List[Slide] = []

        for frame in frames:
            cropped = self.border_detector.process(frame)
            if any(self.comparator.are_similar(existing, cropped) for existing in accepted):
                continue
            slides.append(Slide(index=len(slides), image=cropped.get_image()))
            accepted.append(cropped)

        return slides
