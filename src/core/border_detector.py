"""Presentation border selection with perspective correction and calibration.

Finds the slide region on a frame as a quadrilateral (4 corners) and dewarps
it into a flat rectangular image (FR-6, FR-7). Works in two phases:

    1. `calibrate(frames)` — scans a sample of frames, runs strict quad
       detection on each and keeps the single largest successful detection
       across the whole sample. The rationale: the biggest well-formed
       rectangle present in any sampled frame is almost always the outer
       slide border. Smaller detections are typically inner sub-elements
       (text blocks, logos) or crops occluded by a moving presenter.

    2. `process(frame)` — applies the calibrated quadrilateral to warp every
       frame to a flat rectangle, giving a pixel-stable crop across the clip.
       If calibration wasn't performed or produced nothing, falls back to
       per-frame detection. If that also fails, returns the original frame
       untouched (better to keep context than to over-crop to garbage).

Detection pipeline (per frame):
    · grayscale → bilateral filter (preserves edges, kills noise)
    · Canny → morphological close (joins gaps in the slide border)
    · strictly 4-corner, convex contour with an aspect ratio close to a
      common screen ratio (16:9, 16:10, 4:3, 3:2, 1:1) — within ±35%.
    · order corners → `cv2.getPerspectiveTransform` → `cv2.warpPerspective`.
"""
from __future__ import annotations

from typing import List, Optional

import cv2
import numpy as np

from .models import Frame, Rectangle


class BorderDetector:
    """Finds the slide quadrilateral and returns a perspective-corrected crop."""

    _COMMON_ASPECTS = (16 / 9, 16 / 10, 4 / 3, 3 / 2, 1.0)

    def __init__(
        self,
        min_area_ratio: float = 0.15,
        max_area_ratio: float = 0.85,
        epsilon_ratio: float = 0.02,
        aspect_tolerance: float = 0.35,
    ) -> None:
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio
        self.epsilon_ratio = epsilon_ratio
        self.aspect_tolerance = aspect_tolerance
        self._calibrated_quad: Optional[np.ndarray] = None

    # ----- public API ------------------------------------------------------

    def calibrate(self, frames: List[Frame], max_samples: int = 30) -> None:
        """Lock in the slide region by picking the biggest well-formed quad
        across a sample of frames."""
        self._calibrated_quad = None
        if not frames:
            return

        step = max(1, len(frames) // max_samples)
        sample = frames[::step][:max_samples]

        best_quad: Optional[np.ndarray] = None
        best_area = 0.0

        for frame in sample:
            quad = self._find_quad(frame.get_image())
            if quad is None:
                continue
            area = self._quad_area(quad)
            if area > best_area:
                best_area = area
                best_quad = quad

        if best_quad is not None:
            self._calibrated_quad = best_quad

    def process(self, frame: Frame) -> Frame:
        """Crop a frame to the slide region and dewarp to a flat rectangle."""
        image = frame.get_image()
        if image is None:
            raise ValueError("Frame has no image")

        quad = self._calibrated_quad
        if quad is None:
            quad = self._find_quad(image)

        if quad is not None:
            warped = self._warp_to_rect(image, quad)
            return Frame(index=frame.index, timestamp=frame.timestamp, image=warped)

        # No confident detection — leave the frame untouched so the user sees
        # context rather than an arbitrary over-crop.
        return Frame(index=frame.index, timestamp=frame.timestamp, image=image)

    def detect_borders(self, frame: Frame) -> Rectangle:
        """Legacy API — axis-aligned bounding rectangle for the slide."""
        image = frame.get_image()
        if image is None:
            raise ValueError("Frame has no image")

        h, w = image.shape[:2]
        quad = self._find_quad(image)
        if quad is not None:
            xs, ys = quad[:, 0], quad[:, 1]
            x, y = int(xs.min()), int(ys.min())
            return Rectangle(x, y, int(xs.max()) - x, int(ys.max()) - y)
        return Rectangle(0, 0, w, h)

    def crop_to_slide(self, frame: Frame, bounds: Rectangle) -> Frame:
        """Legacy API — crop by an axis-aligned rectangle."""
        image = frame.get_image()
        h, w = image.shape[:2]
        x1, y1 = max(0, bounds.x), max(0, bounds.y)
        x2 = min(w, bounds.x + bounds.width)
        y2 = min(h, bounds.y + bounds.height)
        cropped = image[y1:y2, x1:x2]
        return Frame(index=frame.index, timestamp=frame.timestamp, image=cropped)

    # ----- internals -------------------------------------------------------

    def _find_quad(self, image: np.ndarray) -> Optional[np.ndarray]:
        h, w = image.shape[:2]
        frame_area = float(w * h)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        edges = cv2.Canny(gray, 50, 180)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        best_quad: Optional[np.ndarray] = None
        best_area = 0.0

        for contour in contours:
            area = cv2.contourArea(contour)
            ratio = area / frame_area
            # Too small → noise / inner sub-element. Too big → the image
            # border itself, not a real slide.
            if ratio < self.min_area_ratio or ratio > self.max_area_ratio:
                continue

            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, self.epsilon_ratio * peri, True)

            # Strict: the slide must approximate to a convex 4-gon. No
            # minAreaRect fallback — it was too permissive and produced
            # tight crops that cut off parts of real slides.
            if len(approx) != 4 or not cv2.isContourConvex(approx):
                continue

            pts = self._order_points(approx.reshape(4, 2).astype(np.float32))
            if not self._aspect_plausible(pts):
                continue

            if area > best_area:
                best_area = area
                best_quad = pts

        return best_quad

    def _aspect_plausible(self, pts: np.ndarray) -> bool:
        tl, tr, br, bl = pts
        w = max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))
        h = max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))
        if h < 1:
            return False
        aspect = w / h
        for ideal in self._COMMON_ASPECTS:
            if abs(aspect - ideal) / ideal <= self.aspect_tolerance:
                return True
        return False

    @staticmethod
    def _quad_area(quad: np.ndarray) -> float:
        """Shoelace area of a quadrilateral."""
        x = quad[:, 0]
        y = quad[:, 1]
        return 0.5 * abs(
            x[0] * y[1] - x[1] * y[0]
            + x[1] * y[2] - x[2] * y[1]
            + x[2] * y[3] - x[3] * y[2]
            + x[3] * y[0] - x[0] * y[3]
        )

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        """Return points ordered as TL, TR, BR, BL."""
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        d = np.diff(pts, axis=1).ravel()
        rect[1] = pts[np.argmin(d)]
        rect[3] = pts[np.argmax(d)]
        return rect

    @staticmethod
    def _warp_to_rect(image: np.ndarray, quad: np.ndarray) -> np.ndarray:
        tl, tr, br, bl = quad
        target_w = int(round(max(np.linalg.norm(tr - tl), np.linalg.norm(br - bl))))
        target_h = int(round(max(np.linalg.norm(bl - tl), np.linalg.norm(br - tr))))
        target_w = max(target_w, 2)
        target_h = max(target_h, 2)
        dst = np.array(
            [[0, 0], [target_w - 1, 0], [target_w - 1, target_h - 1], [0, target_h - 1]],
            dtype=np.float32,
        )
        matrix = cv2.getPerspectiveTransform(quad.astype(np.float32), dst)
        return cv2.warpPerspective(image, matrix, (target_w, target_h))
