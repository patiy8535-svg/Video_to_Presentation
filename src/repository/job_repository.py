"""JobRepository — in-memory store for processing jobs.

Mirrors the JobRepository interface from the class diagram. Kept intentionally
simple; could be swapped for a Redis/DB-backed implementation without touching
the service layer.
"""
from __future__ import annotations

from threading import RLock
from typing import Dict, Optional

from ..core.models import Job


class JobRepository:
    """Thread-safe in-memory repository for Job objects."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = RLock()

    def save(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def find_by_id(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def delete(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)

    def all(self) -> Dict[str, Job]:
        with self._lock:
            return dict(self._jobs)
