"""Presentation border selection.

Detects the region of a frame that contains the presentation slide and crops the
frame to it (FR-6, FR-7). Uses classical CV: grayscale, blur, Canny edges,
contour extraction, then picks the largest contour with near-rectangular shape.
Falls back to the full frame when no reliable border is found.
"""
from __future__ import annotations

import cv2
import numpy as np

from .models import Frame, Rectangle


class BorderDetector:
    """Finds the slide rectangle on a frame and crops to it."""

    def __init__(self, min_area_ratio: float = 0.15, epsilon_ratio: float = 0.02) -> None:
        """
        :param min_area_ratio: minimum fraction of the frame area that a valid slide must cover.
        :param epsilon_ratio: contour approximation tolerance (fraction of perimeter).
        """
        self.min_area_ratio = min_area_ratio
        self.epsilon_ratio = epsilon_ratio

    def detect_borders(self, frame: Frame) -> Rectangle:
        image = frame.get_image()
        if image is None:
            raise ValueError("Frame has no image")

        h, w = image.shape[:2]
        full = Rectangle(0, 0, w, h)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return full

        frame_area = float(w * h)
        best: Rectangle | None = None
        best_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area / frame_area < self.min_area_ratio:
                continue
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, self.epsilon_ratio * peri, True)
            if len(approx) < 4:
                continue
            x, y, cw, ch = cv2.boundingRect(approx)
            if cw * ch > best_area:
                best_area = cw * ch
                best = Rectangle(x, y, cw, ch)

        return best if best is not None else full

    def crop_to_slide(self, frame: Frame, bounds: Rectangle) -> Frame:
        image = frame.get_image()
        h, w = image.shape[:2]
        x1 = max(0, bounds.x)
        y1 = max(0, bounds.y)
        x2 = min(w, bounds.x + bounds.width)
        y2 = min(h, bounds.y + bounds.height)
        cropped = image[y1:y2, x1:x2]
        return Frame(index=frame.index, timestamp=frame.timestamp, image=cropped)
