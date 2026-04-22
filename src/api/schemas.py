"""Request/response schemas for the REST API."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from ..core.models import JobStatus, OutputFormat


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    error: Optional[str] = None
    result_path: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str


class ServiceInfo(BaseModel):
    name: str = "Video to Presentation Service"
    version: str = "1.0.0"
    default_format: OutputFormat = OutputFormat.MARP
