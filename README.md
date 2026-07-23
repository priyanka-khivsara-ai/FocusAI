# FocusAI 🎯

**Zero-Trust Edge AI Attention Tracking for Online Education & Proctoring**

FocusAI is a highly advanced, privacy-first computer vision architecture designed to monitor user attention and detect cheating in real-time. By utilizing **Edge AI**, the system runs heavy computer vision models directly in the user's web browser, ensuring that **raw video never leaves the device**.

![FocusAI Architecture](https://img.shields.io/badge/Architecture-Edge_AI-blue)
![Next.js](https://img.shields.io/badge/Frontend-Next.js_15-black)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![MediaPipe](https://img.shields.io/badge/AI-MediaPipe_FaceMesh-orange)

## 🚀 Key Features

* **Zero-Trust Privacy Model:** 100% of video processing happens on the user's local GPU/CPU via WebAssembly. Only highly compressed, anonymized 3D mathematical feature vectors (less than 1KB/sec) are streamed to the backend over WebSocket.
* **Robust 4-Directional Gaze Tracking:** Implements a mathematically advanced Normalized Grid Model that perfectly maps the pupil to the eye socket. It flawlessy detects when a user looks **Up, Down, Left, or Right**, automatically adjusting for any face shape or eye asymmetry.
* **3D Head Pose Estimation:** Calculates true Pitch, Yaw, and Roll using a mathematically decomposed 4x4 transformation matrix to detect if a user turns their head away from the screen.
* **Micro-Sleep & Blink Detection:** Utilizes real-time Eye Aspect Ratio (EAR) calculations to track blinks and detect drowsiness or closed eyes.
* **Asynchronous Python Engine:** A blazing fast FastAPI backend that processes incoming biometric telemetry via WebSockets and calculates real-time overall focus scores.

## 🛠️ Tech Stack

* **Frontend:** Next.js 15, React, Tailwind CSS, TypeScript
* **Backend:** Python, FastAPI, Uvicorn, NumPy
* **AI/ML:** Google MediaPipe (Face Mesh), WebAssembly (Wasm)

## 💻 How to Run Locally

### Prerequisites
* Node.js (v18+)
* Python 3.9+

### 1. Start the FastAPI Backend
Open a terminal and run the following commands to start the Python telemetry server:
```bash
cd backend
pip install -r requirements.txt
python main.py
```
*The backend will start running securely on `ws://localhost:8000`.*

### 2. Start the Next.js Frontend
We have included a 1-click startup script for Windows users. 
Simply double-click the **`START_PROJECT.bat`** file located in the root directory.

Alternatively, start it manually:
```bash
cd frontend
npm install
npm run dev
```
*The UI will be available at `http://localhost:3000`.*

## 🧠 The Math Behind the Gaze Tracking
Standard gaze tracking algorithms suffer from immense jitter because they rely on dynamic eyelid landmarks or unstable Z-axis depth coordinates. 

FocusAI solves this by anchoring a rigid mathematical bounding box directly to the tear duct and outer eye corner (which are physically anchored to the skull). The precise X and Y coordinates of the Iris are extracted, and displacement is normalized perfectly against the absolute width of the eye, creating a flawless `[-0.5 to 0.5]` detection grid that operates entirely independently of facial depth or camera angle.

---
*Built by Priyanka Khivsara.*
