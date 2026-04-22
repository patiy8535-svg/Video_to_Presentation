"""Unit tests for the Recognizer module (US-22).

Uses mock BorderDetector and SlideComparator from tests/mocks.py so the
Recognizer is exercised in isolation from OpenCV-heavy detection logic.
"""
from __future__ import annotations

import pytest

from src.core.recognizer import Recognizer

from .mocks import MockBorderDetector, MockSlideComparator, make_frame


def _build(predicate=None) -> tuple[Recognizer, MockBorderDetector, MockSlideComparator]:
    detector = MockBorderDetector()
    comparator = MockSlideComparator(predicate=predicate)
    recognizer = Recognizer(border_detector=detector, comparator=comparator)
    return recognizer, detector, comparator


def test_empty_input_returns_no_slides():
    recognizer, _, _ = _build()
    assert recognizer.recognize([]) == []


def test_single_frame_produces_single_slide():
    recognizer, detector, _ = _build()
    frames = [make_frame(0, color=10)]

    slides = recognizer.recognize(frames)

    assert len(slides) == 1
    assert slides[0].index == 0
    assert detector.detect_calls == [0]
    assert detector.crop_calls == [0]


def test_distinct_frames_produce_distinct_slides():
    # Every pair of frames is treated as different → every frame becomes a slide.
    recognizer, _, comparator = _build(predicate=lambda a, b: False)
    frames = [make_frame(i, color=i * 20) for i in range(4)]

    slides = recognizer.recognize(frames)

    assert [s.index for s in slides] == [0, 1, 2, 3]
    # One comparison per subsequent frame (frames 1..3 compared with previous).
    assert len(comparator.calls) == 3


def test_duplicate_frames_are_collapsed():
    # All frames treated as similar → only the first one becomes a slide.
    recognizer, _, _ = _build(predicate=lambda a, b: True)
    frames = [make_frame(i) for i in range(5)]

    slides = recognizer.recognize(frames)

    assert len(slides) == 1
    assert slides[0].index == 0


def test_comparison_uses_last_accepted_slide_not_previous_frame():
    """Recognizer must compare each frame with the last accepted slide,
    otherwise a slow drift across near-duplicates would produce extra slides."""
    # Pairs of identical colors: 0,0,1,1,2,2.
    frames = [make_frame(i, color=i // 2) for i in range(6)]
    # "Similar" iff same color.
    predicate = lambda a, b: int(a.image[0, 0, 0]) == int(b.image[0, 0, 0])

    recognizer, _, comparator = _build(predicate=predicate)
    slides = recognizer.recognize(frames)

    # Expected unique slides: color 0, 1, 2 → 3 slides.
    assert len(slides) == 3
    # First frame is accepted without comparison; remaining 5 are compared once each.
    assert len(comparator.calls) == 5


def test_border_detector_is_invoked_per_frame():
    recognizer, detector, _ = _build(predicate=lambda a, b: False)
    frames = [make_frame(i) for i in range(3)]

    recognizer.recognize(frames)

    assert detector.detect_calls == [0, 1, 2]
    assert detector.crop_calls == [0, 1, 2]


def test_slide_indices_are_sequential_after_dedup():
    # Drop every second frame via "similar" predicate tied to parity.
    frames = [make_frame(i, color=i % 2) for i in range(6)]
    predicate = lambda a, b: int(a.image[0, 0, 0]) == int(b.image[0, 0, 0])

    recognizer, _, _ = _build(predicate=predicate)
    slides = recognizer.recognize(frames)

    assert [s.index for s in slides] == list(range(len(slides)))


def test_default_dependencies_are_instantiated_when_not_provided():
    r = Recognizer()
    # Sanity: default objects are in place and callable.
    assert r.border_detector is not None
    assert r.comparator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
