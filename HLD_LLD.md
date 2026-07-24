I think your project has evolved beyond a typical "attention detection" system. Based on everything you've described, I would define the final architecture as an **Enterprise Edge-AI + Agentic AI Analytics Platform**.

## Final Tech Stack

| Layer                   | Technology                          |
| ----------------------- | ----------------------------------- |
| Frontend                | React + TypeScript + Tailwind CSS   |
| Real-time Communication | WebSocket                           |
| Backend                 | FastAPI (Modular Monolith)          |
| CV Framework            | MediaPipe Face Mesh, Iris, Pose     |
| ML Framework            | PyTorch + ONNX Runtime              |
| Emotion Model           | Fine-tuned CNN/ViT + Temporal Model |
| Attention Engine        | Multi-modal Rule + ML Hybrid        |
| Agent Framework         | LangGraph / PydanticAI (optional)   |
| Structured Database     | PostgreSQL                          |
| Time-Series Database    | TimescaleDB Extension               |
| Cache                   | Redis                               |
| Authentication          | JWT                                 |
| Dashboard               | React + Recharts                    |
| Deployment              | Docker Compose                      |

> **Note:** TimescaleDB is a PostgreSQL extension, so the architecture uses a single PostgreSQL server with TimescaleDB enabled.

---

# Final High Level Design (Production HLD)

```text
                                    ┌────────────────────────────────────┐
                                    │         Student Browser            │
                                    │────────────────────────────────────│
                                    │ Webcam                             │
                                    │ React UI                           │
                                    │ MediaPipe Face Mesh                │
                                    │ MediaPipe Iris                     │
                                    │ MediaPipe Pose                     │
                                    │ Landmark Extraction                │
                                    │ Frame Compression                  │
                                    └───────────────┬────────────────────┘
                                                    │
                                         Secure WebSocket
                                                    │
══════════════════════════════════════════════════════════════════════════════════════
                         FastAPI MODULAR MONOLITH
══════════════════════════════════════════════════════════════════════════════════════

    Session Manager
            │
            ▼
    Face Validation Module
            │
            ├── Face Present?
            ├── Multiple Faces?
            ├── Face Quality?
            └── Occlusion Detection
            │
            ▼
    Liveness Verification Module
            │
            ├── Raise Left Hand
            ├── Raise Right Hand
            ├── Look Left
            ├── Look Right
            ├── Blink Twice
            ├── Smile
            ├── Nod
            └── Challenge Verification
            │
            ▼
    Multi-modal Feature Extraction
            │
            ├── Eyes
            ├── Iris
            ├── Eyebrows
            ├── Mouth
            ├── Facial Action Units (FACS)
            ├── Head Pose
            ├── Body Pose
            └── Temporal Motion
            │
            ▼
    Temporal Feature Fusion
            │
            ├── Sliding Window
            ├── Motion History
            ├── Smoothing
            ├── Statistical Features
            └── Feature Buffer
            │
            ▼
    Attention Scoring Engine
            │
            ▼
    Emotion Classification Engine
            │
            ├── Interested
            ├── Confused
            └── Bored
            │
            ▼
    Event Detection Engine
            │
            ├── Yawn
            ├── Blink Burst
            ├── Eyes Closed
            ├── Looking Away
            ├── Head Turn
            ├── Smile
            ├── Genuine Smile
            ├── Fake Smile
            ├── Contempt
            ├── Drooping Lips
            ├── No Face
            └── Spoof Warning
            │
            ▼
    Agent Layer
            │
            ├── Attention Agent
            ├── Emotion Agent
            ├── Engagement Agent
            ├── Explainability Agent
            ├── Analytics Agent
            └── Report Generation Agent
            │
            ▼
    Analytics Service
            │
            ▼
 PostgreSQL + TimescaleDB
            │
            ▼
 Instructor Dashboard
```

---

# Final Low Level Design (LLD)

```text
Camera Frame
      │
      ▼
Frame Receiver
      │
      ▼
MediaPipe Pipeline
      │
      ├── Face Mesh
      ├── Iris
      └── Pose
      │
      ▼
Landmark Validation
      │
      ▼
Face Validation
      │
      ├── Face Missing
      ├── Multiple Faces
      ├── Blur Detection
      ├── Occlusion
      └── Confidence Check
      │
      ▼
Liveness Engine
      │
      ├── Random Challenge Generator
      ├── Pose Matching
      ├── Hand Verification
      ├── Blink Verification
      ├── Smile Verification
      └── Challenge Scoring
      │
      ▼
Feature Extraction Engine
      │
      ├── Eye Aspect Ratio (EAR)
      ├── Mouth Aspect Ratio (MAR)
      ├── Blink Rate
      ├── Iris Gaze
      ├── Eye Fixation
      ├── Head Pitch
      ├── Head Roll
      ├── Head Yaw
      ├── Shoulder Angle
      ├── Hand Position
      ├── Eyebrow Raise
      ├── Brow Lower
      ├── Smile Intensity
      ├── Smile Symmetry
      ├── AU6
      ├── AU12
      ├── AU14
      ├── Lip Compression
      ├── Mouth Asymmetry
      ├── Drooping Lips
      └── Facial Symmetry
      │
      ▼
Temporal Buffer
      │
      ├── 5-second Window
      ├── Motion History
      ├── Feature Smoothing
      ├── Trend Detection
      └── Moving Statistics
      │
      ▼
Attention Engine
      │
      ▼
Emotion Engine
      │
      ▼
Event Engine
      │
      ▼
Agent Layer
      │
      ▼
Analytics Storage
      │
      ▼
Dashboard
```

---

# Agent Architecture

```text
                  Structured Feature Stream
                             │
     ┌───────────────────────┼────────────────────────┐
     │                       │                        │
     ▼                       ▼                        ▼
Attention Agent        Emotion Agent          Event Agent
     │                       │                        │
     └───────────────┬───────────────┬────────────────┘
                     ▼               ▼
            Explainability      Engagement Agent
                   Agent              │
                     │                │
                     └────────┬───────┘
                              ▼
                  Report Generation Agent
                              │
                              ▼
                 Instructor Dashboard / API
```

---



---

# Attention Score Model

Rather than relying on a single metric, compute attention as a weighted fusion of multiple modalities.

| Feature                   | Weight |
| ------------------------- | -----: |
| Eye Gaze                  |    20% |
| Head Pose                 |    15% |
| Eye Openness (EAR)        |    10% |
| Blink Pattern             |     5% |
| Eyebrow Activity          |    10% |
| Smile / Facial Engagement |    10% |
| Body Posture              |    15% |
| Yawning / Fatigue         |    10% |
| Facial Motion Consistency |     5% |
| Temporal Stability        |    10% |

The weights should be validated experimentally using annotated engagement datasets and refined during model evaluation rather than treated as fixed scientific values.

---

# Processing Pipeline

```
Camera
   │
   ▼
Face Detection
   │
   ▼
Liveness Verification
   │
   ▼
Feature Extraction
   │
   ▼
Temporal Feature Fusion
   │
   ▼
Attention Score
   │
   ▼
Emotion Classification
   │
   ▼
Event Detection
   │
   ▼
Agent Reasoning
   │
   ▼
Database
   │
   ▼
Dashboard
```

---

# Project Folder Structure

```text
focusai/
│
├── frontend/
│
├── backend/
│   ├── api/
│   ├── websocket/
│   ├── services/
│   │     ├── face_validation/
│   │     ├── liveness/
│   │     ├── attention/
│   │     ├── emotion/
│   │     ├── events/
│   │     ├── analytics/
│   │     └── agents/
│   │
│   ├── models/
│   ├── database/
│   ├── schemas/
│   └── utils/
│
├── models/
│   ├── attention/
│   ├── emotion/
│   └── liveness/
│
├── docker/
├── docs/
└── tests/
```

## Why this design is strong

This architecture cleanly separates **real-time perception** (computer vision), **temporal reasoning** (feature fusion and event detection), **AI inference** (attention and emotion models), and **higher-level reasoning** (agent layer). It is deployable as a **single FastAPI modular monolith**, while remaining easy to evolve into microservices if the project grows. Using **PostgreSQL with the TimescaleDB extension** provides one transactional database for both relational entities and high-volume time-series analytics, avoiding the complexity of synchronizing multiple databases. This design is appropriate for a capstone project and reflects production-oriented engineering practices.
