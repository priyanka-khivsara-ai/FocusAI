# FocusAI: Technical Architecture & Core Mechanisms

This document explains exactly **how** FocusAI works from start to finish, detailing the exact AI models used, the mathematical logic behind the scoring, and the LangChain agent architecture.

---

## 1. Edge AI & Computer Vision Model
Rather than streaming heavy video feeds to the server (which is slow, expensive, and violates privacy), FocusAI uses **Edge AI**.

*   **The Model:** We use Google's **MediaPipe FaceLandmarker**.
*   **How it runs:** The model is compiled to WebAssembly (WASM) and runs directly on the student's CPU/GPU inside their web browser.
*   **What it does:** For every single frame of video (30 times a second), the model maps exactly **478 3D facial landmarks** (coordinates for the eyes, irises, lips, eyebrows, and jaw).
*   **The Payload:** The frontend extracts only the coordinates for specific features (e.g., 12 points for the eyes, 6 points for the mouth) and a 4x4 Transformation Matrix (representing the angle of the head). It sends this tiny JSON payload to the backend via **WebSockets**.

---

## 2. The Attention Scoring Mathematics
When the FastAPI backend receives the 3D coordinates via WebSocket, it passes them to `scorer.py` and `analyzer.py` to calculate biometric heuristics.

### Feature Extraction
1.  **Eye Aspect Ratio (EAR):** Calculates the distance between the top/bottom eyelids. If EAR drops below `0.22`, the system registers a blink or closed eyes.
2.  **Mouth Aspect Ratio (MAR):** Calculates the distance between the top and bottom lips to detect yawning or talking.
3.  **Head Pose (Pitch, Yaw, Roll):** Uses the 4x4 Transformation Matrix to calculate exactly where the head is pointing in 3D space.

### The Focus Score Algorithm
The Focus Score is calculated per frame in `scorer.py`. It starts at **100%** and deducts points based on strict rules:
*   **Eyes Closed (`EAR < 0.22`):** -50 points.
*   **Looking Left/Right (`Yaw > 25°`):** -40 points.
*   **Looking Up/Down (`Pitch > 20°`):** -30 points.
*   **Gaze Distraction (Irises shifted):** -40 points.

*Smoothing:* Because humans naturally blink and shift their heads, a single bad frame would cause the score to jump wildly. We use a **50-frame rolling window** (a `deque` array). The final Focus Score you see on the dashboard is the *average* score over the last ~5 seconds.

---

## 3. The Database Engine
We use two different database architectures simultaneously to handle the data:
*   **PostgreSQL:** Handles relational data like Users, Roles, and Passwords.
*   **TimescaleDB:** A specialized time-series extension for Postgres. We convert standard tables into **Hypertables**. Instead of storing one massive list of telemetry, TimescaleDB partitions the data into "time chunks". This allows us to insert thousands of biometric frames per second without locking the database, and query historical data instantly using SQL `LEFT JOIN`s.

---

## 4. The LangChain Master Agent
The "Chat with AI" feature on the Admin Dashboard is powered by a ReAct (Reasoning and Acting) Agent built with **LangGraph** and **LangChain**.

*   **The LLM:** We use **Llama 3.1 (8B Instant)** hosted on **Groq**. Groq uses specialized LPU hardware, making the AI respond in milliseconds.
*   **The Architecture:** The agent is constructed using `create_react_agent()`. This gives the LLM the ability to "think" about a user's question, decide if it needs more information, and execute Python functions.
*   **The Custom Tools:** We built a custom Python tool called `@tool query_recent_telemetry`. If an Admin asks, *"How is Shubham doing?"*, the Llama 3 model realizes it doesn't know. It autonomously executes the `query_recent_telemetry` tool, which runs a raw SQL query against the TimescaleDB database, fetches Shubham's latest Focus Scores and Moods, feeds that data back to the LLM, and finally generates a natural language summary for the Admin.
