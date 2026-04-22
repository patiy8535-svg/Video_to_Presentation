"""Mock classes used to isolate components under test (US-21).

These doubles replace BorderDetector and SlideComparator in Recognizer tests so
that the Recognizer is exercised without depending on OpenCV-heavy logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

import numpy as np

from src.core.models import Frame, Rectangle


@dataclass
class MockBorderDetector:
    """A BorderDetector stub that returns the full frame as its bounds."""

    detect_calls: List[int] = field(default_factory=list)
    crop_calls: List[int] = field(default_factory=list)

    def detect_borders(self, frame: Frame) -> Rectangle:
        self.detect_calls.append(frame.index)
        h, w = frame.image.shape[:2]
        return Rectangle(0, 0, w, h)

    def crop_to_slide(self, frame: Frame, bounds: Rectangle) -> Frame:
        self.crop_calls.append(frame.index)
        return frame


@dataclass
class MockSlideComparator:
    """A SlideComparator stub that decides similarity via a supplied predicate.

    The predicate takes two frames and returns True iff they should be treated
    as identical. Defaults to "everything is unique".
    """

    predicate: Optional[Callable[[Frame, Frame], bool]] = None
    calls: List[tuple] = field(default_factory=list)

    def are_similar(self, a: Frame, b: Frame) -> bool:
        self.calls.append((a.index, b.index))
        if self.predicate is None:
            return False
        return bool(self.predicate(a, b))


def make_frame(index: int, color: int = 0, size: int = 8) -> Frame:
    """Produce a tiny uniform-color frame for tests (no cv2 needed)."""
    image = np.full((size, size, 3), color, dtype=np.uint8)
    return Frame(index=index, timestamp=float(index), image=image)
