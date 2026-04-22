"""Slide comparison via perceptual hashing.

Two frames are considered similar when the normalized Hamming distance between
their perceptual hashes falls below a configurable threshold (FR-8).
"""
from __future__ import annotations

import cv2
import numpy as np

from .models import Frame


class SlideComparator:
    """Decides whether two frames show the same slide."""

    def __init__(self, threshold: float = 0.12, hash_size: int = 16) -> None:
        """
        :param threshold: max normalized Hamming distance [0..1] to call frames similar.
        :param hash_size: side of the dHash grid. 16 → 16*15 = 240-bit hash.
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0,1]")
        if hash_size < 4:
            raise ValueError("hash_size must be >= 4")
        self.threshold = threshold
        self.hash_size = hash_size

    def phash(self, image: np.ndarray) -> np.ndarray:
        """Difference hash: robust to scale/compression, cheap to compute."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        resized = cv2.resize(gray, (self.hash_size + 1, self.hash_size), interpolation=cv2.INTER_AREA)
        diff = resized[:, 1:] > resized[:, :-1]
        return diff.flatten()

    def are_similar(self, a: Frame, b: Frame) -> bool:
        return self.distance(a, b) <= self.threshold

    def distance(self, a: Frame, b: Frame) -> float:
        ha = self.phash(a.get_image())
        hb = self.phash(b.get_image())
        if ha.size != hb.size:
            raise ValueError("Incompatible hash sizes")
        return float(np.count_nonzero(ha != hb)) / ha.size
