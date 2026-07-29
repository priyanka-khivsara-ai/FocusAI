# FocusAI: Cognitive Telemetry Engine 🧠

FocusAI is an advanced **Agentic AI** platform designed for high-frequency, real-time extraction of human cognitive states using **Deep Learning (DL)** and **Computer Vision**. By deploying a highly optimized Edge AI vision pipeline directly in the browser, the system transforms raw video into a continuous stream of lightweight, multi-modal biometric telemetry (Eye Aspect Ratios, 3D Pose, Facial Tension, and Emotion Vectors). 

This telemetry is asynchronously streamed to a fast Python backend and permanently persisted in a **TimescaleDB** time-series database. The stored cognitive telemetry acts as the foundation for **Retrieval-Augmented Generation (RAG)**, allowing LLM Agents to query the database, analyze human engagement, and generate powerful natural-language insights over historical sessions.

![FocusAI Architecture](https://img.shields.io/badge/Architecture-Edge_AI-blue)
![Deep Learning](https://img.shields.io/badge/AI-Deep_Learning_%28DL%29-orange)
![PostgreSQL](https://img.shields.io/badge/Database-TimescaleDB-009688)

## 🚀 Enterprise Architecture

* **Edge AI Vision Pipeline (WASM):** 100% of the Deep Learning Face Mesh processing happens on the client GPU/CPU via WebAssembly. The raw video is instantly discarded, and only mathematically compressed 3D feature vectors are streamed to the backend.
* **Multi-Modal Behavioral Engine:** The Python backend parses the raw 3D vectors to calculate precise true Pitch/Yaw/Roll, Gaze direction, Lip Compression, Brow Furrowing (Facial Tension), and Eye Aspect Ratio (EAR) for Micro-Sleep detection.
* **Agentic AI & RAG Layer (WIP):** Cognitive state telemetry is persisted to a time-series database. Specialized Autonomous Agents use RAG and Information Retrieval to query this historical data, generating human-readable behavioral insights and automated anomaly reports.

## 🛠️ Technology Stack

* **Edge Node:** Next.js 15, React, TypeScript, WebAssembly, MediaPipe
* **Telemetry Server:** Python, FastAPI, Uvicorn, NumPy
* **Data Persistence:** PostgreSQL, TimescaleDB, SQLAlchemy, asyncpg

## 💻 Getting Started

### Prerequisites
* Node.js (v18+)
* Python 3.9+
* Docker Desktop (or OrbStack)

### 1. Boot up the TimescaleDB Database (Docker)
The system requires TimescaleDB to handle the high-frequency time-series telemetry.
```bash
docker-compose up -d
```
*Note: You can connect a GUI client like DBeaver using:*
`Host: localhost` | `Port: 5432` | `DB: focus_db` | `User: focus_user` | `Pass: focus_password`

### 2. Start the Telemetry Backend
Open a terminal and start the async Python server:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
*The backend will run on `ws://localhost:8000`.*

### 3. Start the Edge Node (Frontend)
Open a new terminal to start the Next.js UI:
```bash
cd frontend
npm install
npm run dev
```
*The dashboard will be available at `http://localhost:3000`.*

## 🧠 The Mathematics of the Gaze Pipeline
Standard gaze tracking algorithms suffer from immense jitter because they rely on dynamic eyelid landmarks. FocusAI solves this by anchoring a rigid mathematical bounding box directly to the tear duct and outer eye corner (which are physically anchored to the skull). The precise X and Y coordinates of the Iris are extracted, and displacement is normalized perfectly against the absolute width of the eye, creating a flawless `[-0.5 to 0.5]` detection grid that operates entirely independently of facial depth or camera angle.
