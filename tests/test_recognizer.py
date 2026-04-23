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
    assert detector.process_calls == [0]


def test_calibration_runs_before_processing():
    recognizer, detector, _ = _build()
    frames = [make_frame(i) for i in range(4)]

    recognizer.recognize(frames)

    # calibrate() must be invoked exactly once with all frames before per-frame work.
    assert detector.calibrate_calls == [4]


def test_distinct_frames_produce_distinct_slides():
    # Every pair treated as different → every frame becomes a slide.
    recognizer, _, comparator = _build(predicate=lambda a, b: False)
    frames = [make_frame(i, color=i * 20) for i in range(4)]

    slides = recognizer.recognize(frames)

    assert [s.index for s in slides] == [0, 1, 2, 3]
    # Frame 0 is accepted without comparison; frame k is compared against all k
    # previously accepted slides. 0 + 1 + 2 + 3 = 6.
    assert len(comparator.calls) == 6


def test_duplicate_frames_are_collapsed():
    # All frames treated as similar → only the first becomes a slide.
    recognizer, _, _ = _build(predicate=lambda a, b: True)
    frames = [make_frame(i) for i in range(5)]

    slides = recognizer.recognize(frames)

    assert len(slides) == 1
    assert slides[0].index == 0


def test_revisited_slide_is_not_duplicated():
    """If the presenter returns to an earlier slide, it must NOT be added twice."""
    # Colors: 0 → 1 → 0 → 1 → 0 → 1. Same color = same slide.
    frames = [make_frame(i, color=i % 2) for i in range(6)]
    predicate = lambda a, b: int(a.image[0, 0, 0]) == int(b.image[0, 0, 0])

    recognizer, _, _ = _build(predicate=predicate)
    slides = recognizer.recognize(frames)

    # Only two unique colors → exactly two slides, even though each repeats 3 times.
    assert len(slides) == 2


def test_comparison_checks_all_previously_accepted_slides():
    # 6 frames with 3 distinct colors in pairs: [0,0,1,1,2,2].
    frames = [make_frame(i, color=i // 2) for i in range(6)]
    predicate = lambda a, b: int(a.image[0, 0, 0]) == int(b.image[0, 0, 0])

    recognizer, _, comparator = _build(predicate=predicate)
    slides = recognizer.recognize(frames)

    assert len(slides) == 3
    # Expected comparisons (short-circuits on match):
    #   f0: accept, 0 comparisons
    #   f1: match vs 0 → 1 comparison
    #   f2: diff vs 0, accept → 1
    #   f3: diff vs 0, match vs 2 → 2
    #   f4: diff vs 0, diff vs 2, accept → 2
    #   f5: diff vs 0, diff vs 2, match vs 4 → 3
    #   Total: 1 + 1 + 2 + 2 + 3 = 9
    assert len(comparator.calls) == 9


def test_border_detector_is_invoked_per_frame():
    recognizer, detector, _ = _build(predicate=lambda a, b: False)
    frames = [make_frame(i) for i in range(3)]

    recognizer.recognize(frames)

    assert detector.process_calls == [0, 1, 2]


def test_slide_indices_are_sequential_after_dedup():
    frames = [make_frame(i, color=i % 2) for i in range(6)]
    predicate = lambda a, b: int(a.image[0, 0, 0]) == int(b.image[0, 0, 0])

    recognizer, _, _ = _build(predicate=predicate)
    slides = recognizer.recognize(frames)

    assert [s.index for s in slides] == list(range(len(slides)))


def test_default_dependencies_are_instantiated_when_not_provided():
    r = Recognizer()
    assert r.border_detector is not None
    assert r.comparator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
