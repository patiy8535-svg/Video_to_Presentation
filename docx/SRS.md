# Software Requirements Specification (SRS)

## Video to Presentation Service

**Version:** 1.0  
**Date:** 2026  
**Status:** Draft

---

## 1. Purpose

The **Video to Presentation Service** converts lecture, talk, and presentation videos into structured **Markdown/Marp** slide decks.

It is intended for:
- teachers and students working with recorded lectures;
- speakers who want to restore slides from recorded talks;
- educational content creators who need fast slide-based summaries from video.

---

## 2. Product Overview

The service is a standalone server application running in a **Docker container** and exposing a **REST API**.

Core capabilities:
- upload a video file;
- extract frames at a configurable rate;
- detect and crop the slide area;
- identify unique slides and remove duplicates;
- generate a **Markdown/Marp** presentation;
- return the result to the user.

Supported roles:
- **End user** — uploads a video and receives a presentation;
- **Developer/Integrator** — uses the REST API in external systems;
- **Administrator** — deploys and maintains the service.

Constraints:
- supported input formats: **MP4, AVI, MOV**;
- maximum file size is configurable;
- output quality depends on source video quality;
- the service runs in an isolated Docker environment.

Dependencies:
- **FFmpeg** and **OpenCV** must be available;
- clients must be able to send HTTP requests;
- the source video must contain a clearly visible presentation area.

---

## 3. Functional Requirements

### 3.1 Video Upload
- The system shall accept video upload via **POST REST API**.
- The system shall validate file format and size.
- The system shall return clear error messages for invalid files.

### 3.2 Frame Processing
- The system shall extract frames from the video.
- The frame extraction rate shall be configurable.

### 3.3 Slide Detection
- The system shall automatically detect slide boundaries in each frame.
- The system shall crop frames to the detected slide area.

### 3.4 Slide Recognition
- The system shall compare frames and remove duplicates.
- The system shall keep only unique slides in the output.

### 3.5 Presentation Generation
- The system shall generate output in **Markdown/Marp** format.
- Each unique slide shall become a separate presentation page.
- The system should support optional titles and captions for slides.

### 3.6 Result Delivery
- The system shall return the generated presentation via REST API.
- The system shall provide processing status tracking.

---

## 4. Non-Functional Requirements

### Performance
- A **10-minute video** should be processed in **no more than 3 minutes** on recommended hardware.
- The system should support multiple concurrent processing tasks.

### Reliability
- The service shall handle invalid input without crashing.
- The system shall log key processing events.

### Usability
- The API shall be documented using **OpenAPI/Swagger**.
- Error messages shall be informative.

### Portability
- The service shall run in Docker on **Linux, macOS, and Windows**.
- No manual dependency installation shall be required beyond Docker.

### Security
- Uploaded video files shall be deleted after processing.
- The system shall protect against excessively large uploads.

### Maintainability
- Key modules, especially the recognizer, shall be covered by unit tests.
- The architecture should follow **SOLID** principles and support extension.

---

## 5. External Interfaces

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/videos` | Upload a video and start processing |
| GET | `/api/videos/{id}/status` | Get processing status |
| GET | `/api/videos/{id}/presentation` | Download the generated presentation |

### Communication
- Client-server communication shall use **HTTP/HTTPS**.

### Hardware
- No special hardware is required beyond sufficient **CPU/RAM** for video processing.

---

## 6. Acceptance Criteria

The product is accepted if:
- all functional requirements are implemented;
- unit tests for the recognizer and key modules pass;
- the service starts with a single `docker run` command;
- a valid Markdown/Marp file is generated from a test video;
- API documentation is available and up to date.

---

## 7. Appendices

- Use case diagram;
- sequence diagrams;
- class diagram;
- UI prototype;
- backlog.