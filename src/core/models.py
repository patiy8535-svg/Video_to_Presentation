"""Domain models for the Video to Presentation Service.

Mirrors the structure defined in docx/ClassDiagram.puml.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Any


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OutputFormat(str, Enum):
    MARKDOWN = "MARKDOWN"
    MARP = "MARP"


@dataclass
class Rectangle:
    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass
class VideoFile:
    path: str
    format: str = ""
    duration: float = 0.0

    def exists(self) -> bool:
        return Path(self.path).is_file()


@dataclass
class Frame:
    index: int
    timestamp: float
    image: Any  # numpy.ndarray in runtime, Any to keep core importable without cv2

    def get_image(self) -> Any:
        return self.image


@dataclass
class Slide:
    index: int
    image: Any
    title: str = ""
    caption: str = ""

    def set_title(self, title: str) -> None:
        self.title = title

    def set_caption(self, caption: str) -> None:
        self.caption = caption


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    result_path: Optional[str] = None
    error: Optional[str] = None
    source_path: Optional[str] = None
    output_format: OutputFormat = OutputFormat.MARP

    def update_status(self, status: JobStatus) -> None:
        self.status = status

    def update_progress(self, value: int) -> None:
        self.progress = max(0, min(100, int(value)))
