# Product Backlog

## Video to Presentation Service

**Version:** 1.0
**Status:** Active

---

## 1. Overview

This backlog contains all user stories and tasks required to deliver the Video to Presentation Service — a system that converts video recordings into Markdown/Marp presentations.

Items are grouped by epic and prioritized using the MoSCoW method:
- **M** — Must have
- **S** — Should have
- **C** — Could have
- **W** — Won't have (this release)

Estimates are given in Story Points (SP) using a Fibonacci scale.

---

## 2. Epics

| ID | Epic | Description |
|----|------|-------------|
| E1 | Requirements & Design | Requirements collection and system design |
| E2 | Video Processing Core | Frame extraction and slide recognition |
| E3 | Presentation Generation | Markdown/Marp output generation |
| E4 | REST API | External interface for the service |
| E5 | Testing | Unit and integration tests |
| E6 | Deployment | Docker containerization and delivery |

---

## 3. Backlog Items

### Epic E1 — Requirements & Design

| ID | User Story | Priority | SP | Status |
|----|------------|----------|----|--------|
| US-01 | As an analyst, I want to prepare an SRS document so that the team shares a common understanding of the requirements. | M | 5 | Done |
| US-02 | As a product owner, I want to maintain a backlog so that work is prioritized and visible. | M | 2 | Done |
| US-03 | As a designer, I want to create a Use Case diagram so that actors and system scenarios are clearly defined. | M | 3 | Done |
| US-04 | As a designer, I want to build a UI prototype so that stakeholders can preview the user interface. | S | 5 | Done |
| US-05 | As an architect, I want to draw 3 sequence diagrams so that key interaction flows are documented. | M | 5 | Done |
| US-06 | As an architect, I want to create a class diagram so that the internal structure of the system is clear. | M | 5 | Done |

### Epic E2 — Video Processing Core

| ID | User Story | Priority | SP | Status |
|----|------------|----------|----|--------|
| US-07 | As a developer, I want to implement frame reading from a video file so that frames can be processed further. | M | 5 | Done |
| US-08 | As a developer, I want to detect the presentation area on a frame so that only the slide region is analyzed. | M | 8 | Done |
| US-09 | As a developer, I want to implement the Recognizer module so that unique slides are identified. | M | 8 | In Progress |
| US-10 | As a developer, I want to filter out duplicate frames so that the output contains only unique slides. | M | 5 | To Do |
| US-11 | As a developer, I want to make frame extraction rate configurable so that processing can be tuned. | S | 3 | To Do |

### Epic E3 — Presentation Generation

| ID | User Story | Priority | SP | Status |
|----|------------|----------|----|--------|
| US-12 | As a user, I want each unique slide to appear as a separate page in the output so that the presentation is well structured. | M | 5 | To Do |
| US-13 | As a user, I want the output to be a valid Markdown/Marp file so that I can open it in any Marp-compatible viewer. | M | 5 | To Do |
| US-14 | As a user, I want to add titles and captions to slides so that the presentation is more informative. | C | 5 | To Do |
| US-15 | As a user, I want to choose the output theme so that the presentation matches my style. | C | 3 | To Do |

### Epic E4 — REST API

| ID | User Story | Priority | SP | Status |
|----|------------|----------|----|--------|
| US-16 | As a client, I want to upload a video via REST API so that it can be processed by the service. | M | 5 | To Do |
| US-17 | As a client, I want to check the processing status so that I know when the result is ready. | M | 3 | To Do |
| US-18 | As a client, I want to download the generated presentation so that I can use it. | M | 3 | To Do |
| US-19 | As a developer, I want OpenAPI/Swagger documentation so that the API is easy to integrate. | S | 3 | To Do |
| US-20 | As an administrator, I want the service to validate file size and format so that invalid input is rejected early. | M | 3 | To Do |

### Epic E5 — Testing

| ID | User Story | Priority | SP | Status |
|----|------------|----------|----|--------|
| US-21 | As a developer, I want mock classes for external dependencies so that components can be tested in isolation. | M | 3 | Done |
| US-22 | As a developer, I want unit tests for the Recognizer so that its behavior is verified. | M | 5 | Done |
| US-23 | As a developer, I want integration tests for the REST API so that end-to-end flows are validated. | S | 5 | To Do |
| US-24 | As a developer, I want a sample test video set so that tests are reproducible. | S | 2 | To Do |

### Epic E6 — Deployment

| ID | User Story | Priority | SP | Status |
|----|------------|----------|----|--------|
| US-25 | As an administrator, I want a Dockerfile so that the service can be built as a container. | M | 3 | Done |
| US-26 | As an administrator, I want a docker-compose configuration so that the service can be launched with one command. | S | 3 | To Do |
| US-27 | As an administrator, I want centralized logging so that I can monitor service behavior. | S | 3 | To Do |
| US-28 | As an administrator, I want uploaded videos to be cleaned up after processing so that disk usage stays under control. | M | 2 | To Do |

---

## 4. Definition of Done

A backlog item is considered done when:
- code is written and reviewed;
- unit tests are written and pass;
- the feature is documented (README / API docs);
- the feature is deployed to the test environment;
- acceptance criteria are met.

---

## 5. Release Plan

| Release | Scope | Goal |
|---------|-------|------|
| MVP (R1) | E1, E2, E3 (core), E4, E6 | Working service that accepts a video and returns a Marp presentation |
| R2 | E3 (themes, captions), E5 (full coverage) | Quality and usability improvements |
| R3 | Performance optimizations, advanced recognition | Scaling and quality enhancements |
