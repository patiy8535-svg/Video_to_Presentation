"""Presentation generation — builds Markdown/Marp output from recognized slides.

Each unique slide becomes its own page (FR-10, FR-11). Titles and captions are
supported (FR-12). Slide images are written as PNG files next to the Markdown
output and referenced by relative path.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2

from ..core.models import OutputFormat, Slide


@dataclass
class Presentation:
    slides: List[Slide]
    format: OutputFormat
    content: str
    assets_dir: str

    def save_to_file(self, path: str) -> None:
        Path(path).write_text(self.content, encoding="utf-8")


class PresentationGenerator:
    """Converts a list of Slide objects into a Markdown/Marp document."""

    def __init__(self, theme: str = "default", output_format: OutputFormat = OutputFormat.MARP) -> None:
        self.theme = theme
        self.output_format = output_format

    def generate(self, slides: List[Slide], output_dir: str, name: str = "presentation") -> Presentation:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        assets = out / f"{name}_assets"
        assets.mkdir(exist_ok=True)

        image_paths: List[str] = []
        for slide in slides:
            img_path = assets / f"slide_{slide.index:03d}.png"
            cv2.imwrite(str(img_path), slide.image)
            image_paths.append(f"{assets.name}/{img_path.name}")

        if self.output_format == OutputFormat.MARP:
            content = self._to_marp(slides, image_paths)
        else:
            content = self._to_markdown(slides, image_paths)

        md_path = out / f"{name}.md"
        md_path.write_text(content, encoding="utf-8")

        return Presentation(
            slides=slides,
            format=self.output_format,
            content=content,
            assets_dir=str(assets),
        )

    def _marp_header(self) -> str:
        return (
            "---\n"
            "marp: true\n"
            f"theme: {self.theme}\n"
            "paginate: true\n"
            "size: 16:9\n"
            "---\n\n"
        )

    def _to_marp(self, slides: List[Slide], image_paths: List[str]) -> str:
        parts = [self._marp_header()]
        for slide, img in zip(slides, image_paths):
            parts.append(self._render_slide(slide, img))
        return "\n---\n\n".join(parts).rstrip() + "\n"

    def _to_markdown(self, slides: List[Slide], image_paths: List[str]) -> str:
        parts = [f"# {self.theme.capitalize()} Presentation\n\n"]
        for slide, img in zip(slides, image_paths):
            parts.append(self._render_slide(slide, img))
        return "\n---\n\n".join(parts).rstrip() + "\n"

    @staticmethod
    def _render_slide(slide: Slide, image_path: str) -> str:
        title = slide.title or f"Slide {slide.index + 1}"
        lines = [f"## {title}\n", f"![slide {slide.index + 1}]({image_path})\n"]
        if slide.caption:
            lines.append(f"\n_{slide.caption}_\n")
        return "\n".join(lines)
