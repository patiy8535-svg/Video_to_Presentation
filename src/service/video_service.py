"""VideoService — orchestrates the pipeline from video file to presentation.

The flow (see docx/SequenceDiagram_ProcessVideo.puml):
    PENDING -> PROCESSING -> extract frames -> recognize slides ->
    generate presentation -> COMPLETED (or FAILED on error).
"""
from __future__ import annotations

import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Optional

from ..core.border_detector import BorderDetector
from ..core.frame_extractor import FrameExtractor
from ..core.models import Job, JobStatus, OutputFormat, VideoFile
from ..core.recognizer import Recognizer
from ..core.slide_comparator import SlideComparator
from ..generator.presentation_generator import PresentationGenerator
from ..repository.job_repository import JobRepository

logger = logging.getLogger(__name__)


class VideoService:
    """Coordinates frame extraction, recognition and presentation generation."""

    def __init__(
        self,
        job_repository: JobRepository,
        output_dir: str,
        frame_extractor: Optional[FrameExtractor] = None,
        recognizer: Optional[Recognizer] = None,
        generator: Optional[PresentationGenerator] = None,
        cleanup_source: bool = True,
    ) -> None:
        self.job_repository = job_repository
        self.output_dir = output_dir
        self.frame_extractor = frame_extractor or FrameExtractor(frame_rate=1.0)
        self.recognizer = recognizer or Recognizer(BorderDetector(), SlideComparator())
        self.generator = generator or PresentationGenerator()
        self.cleanup_source = cleanup_source
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def process_video(
        self,
        video_path: str,
        output_format: OutputFormat = OutputFormat.MARP,
        async_run: bool = True,
    ) -> Job:
        """Create a Job and kick off processing (async by default)."""
        job = Job(
            id=str(uuid.uuid4()),
            status=JobStatus.PENDING,
            progress=0,
            source_path=video_path,
            output_format=output_format,
        )
        self.job_repository.save(job)

        if async_run:
            thread = threading.Thread(target=self._run_pipeline, args=(job,), daemon=True)
            thread.start()
        else:
            self._run_pipeline(job)

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.job_repository.find_by_id(job_id)

    def _run_pipeline(self, job: Job) -> None:
        try:
            job.update_status(JobStatus.PROCESSING)
            job.update_progress(5)
            self.job_repository.save(job)

            video = VideoFile(path=job.source_path or "")
            frames = self.frame_extractor.extract_frames(video)
            logger.info("Extracted %d frames from %s", len(frames), video.path)
            job.update_progress(40)
            self.job_repository.save(job)

            slides = self.recognizer.recognize(frames)
            logger.info("Recognized %d unique slides", len(slides))
            job.update_progress(75)
            self.job_repository.save(job)

            self.generator.output_format = job.output_format
            presentation = self.generator.generate(
                slides=slides,
                output_dir=self.output_dir,
                name=f"job_{job.id}",
            )
            job.result_path = str(Path(self.output_dir) / f"job_{job.id}.md")
            job.update_progress(100)
            job.update_status(JobStatus.COMPLETED)
            self.job_repository.save(job)
            logger.info("Job %s completed → %s", job.id, job.result_path)

        except Exception as exc:
            logger.exception("Job %s failed", job.id)
            job.error = str(exc)
            job.update_status(JobStatus.FAILED)
            self.job_repository.save(job)
        finally:
            if self.cleanup_source and job.source_path and os.path.isfile(job.source_path):
                try:
                    os.remove(job.source_path)
                except OSError:
                    logger.warning("Could not remove source file %s", job.source_path)
