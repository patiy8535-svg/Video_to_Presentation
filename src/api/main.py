"""REST API — FastAPI application that exposes the pipeline.

Endpoints (see docx/SRS.md §5.2):
    POST /api/videos                         — upload a video, start processing
    GET  /api/videos/{job_id}/status         — get processing status
    GET  /api/videos/{job_id}/presentation   — download the generated .md file
    GET  /                                   — service info / UI prototype
    GET  /health                             — liveness probe

OpenAPI/Swagger (NFR-5) is served at /docs automatically by FastAPI.
"""
from __future__ import annotations

import logging
import os
import shutil
import uuid
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import FastAPI, File, Form, HTTPException, Path as PathParam, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

from ..core.models import JobStatus, OutputFormat
from ..repository.job_repository import JobRepository
from ..service.video_service import VideoService
from .schemas import JobResponse, ServiceInfo, StatusResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 500 * 1024 * 1024))  # 500 MB
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/tmp/v2p/uploads"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/tmp/v2p/output"))
UI_DIR = Path(__file__).resolve().parent.parent.parent / "ui"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Video to Presentation Service",
    version="1.0.0",
    description="Converts video recordings into Markdown/Marp presentations.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = JobRepository()
service = VideoService(job_repository=repository, output_dir=str(OUTPUT_DIR))


def _validate_upload(file: UploadFile) -> None:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> HTMLResponse:
    index_html = UI_DIR / "index.html"
    if index_html.exists():
        return HTMLResponse(index_html.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Video to Presentation Service</h1><p>See /docs.</p>")


@app.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/info", response_model=ServiceInfo, tags=["service"])
def info() -> ServiceInfo:
    return ServiceInfo()


@app.post("/api/videos", response_model=JobResponse, status_code=202, tags=["videos"])
async def upload_video(
    file: UploadFile = File(..., description="Video file (mp4/avi/mov/mkv/webm)"),
    output_format: OutputFormat = Form(OutputFormat.MARP),
) -> JobResponse:
    """Upload a video and start asynchronous processing."""
    _validate_upload(file)

    upload_id = str(uuid.uuid4())
    target = UPLOAD_DIR / f"{upload_id}{Path(file.filename or '').suffix.lower()}"

    size = 0
    with target.open("wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                target.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large")
            out.write(chunk)

    if size == 0:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty file")

    job = service.process_video(str(target), output_format=output_format, async_run=True)
    return JobResponse(job_id=job.id, status=job.status)


@app.get("/api/videos/{job_id}/status", response_model=StatusResponse, tags=["videos"])
def get_status(job_id: str = PathParam(..., description="Job identifier")) -> StatusResponse:
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return StatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        error=job.error,
        result_path=job.result_path,
    )


@app.get("/api/videos/{job_id}/presentation", tags=["videos"])
def get_presentation(
    job_id: str = PathParam(..., description="Job identifier"),
    bundle: bool = True,
):
    """Download the generated presentation.

    By default returns a ZIP archive containing `presentation.md` and the
    `assets/` folder with all slide images, so the presentation is self-
    contained. Pass `bundle=false` to get the raw `.md` file (image links will
    only resolve if the assets folder is retrieved separately).
    """
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=409, detail=f"Job is not completed (status={job.status})")
    if not job.result_path or not Path(job.result_path).is_file():
        raise HTTPException(status_code=500, detail="Presentation file missing")

    md_path = Path(job.result_path)
    assets_dir = md_path.parent / f"{md_path.stem}_assets"

    if not bundle:
        return FileResponse(
            md_path,
            media_type="text/markdown",
            filename=f"presentation_{job.id}.md",
        )

    # Rewrite image paths to point to assets/ so the zipped markdown is portable.
    md_content = md_path.read_text(encoding="utf-8").replace(f"{assets_dir.name}/", "assets/")

    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as zf:
        zf.writestr("presentation.md", md_content)
        if assets_dir.is_dir():
            for img in sorted(assets_dir.iterdir()):
                if img.is_file():
                    zf.write(img, arcname=f"assets/{img.name}")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="presentation_{job.id}.zip"'},
    )


@app.delete("/api/videos/{job_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["videos"])
def delete_job(job_id: str = PathParam(..., description="Job identifier")):
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.result_path:
        md = Path(job.result_path)
        assets = md.with_suffix("").parent / f"{md.stem}_assets"
        md.unlink(missing_ok=True)
        if assets.is_dir():
            shutil.rmtree(assets, ignore_errors=True)
    repository.delete(job_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
