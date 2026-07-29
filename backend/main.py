# main.py
# FastAPI backend for Attention Detection System
from fastapi import FastAPI, WebSocket
import uvicorn
import numpy as np
import math
import os
import time
from database import SessionLocal
from models import TelemetryRecord
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agent import get_agent

# Helper to extract Pitch, Yaw, and Roll from transformation matrix
def calculate_head_pose(transformation_matrix):
    # Standard decomposition of 3x3 rotation matrix using pure numpy/math
    # (Since we removed cv2 to make the server blazing fast)
    rmat = transformation_matrix[:3, :3]
    sy = math.sqrt(rmat[0,0] * rmat[0,0] + rmat[1,0] * rmat[1,0])
    singular = sy < 1e-6
    if not singular:
        x = math.atan2(rmat[2,1], rmat[2,2])
        y = math.atan2(-rmat[2,0], sy)
        z = math.atan2(rmat[1,0], rmat[0,0])
    else:
        x = math.atan2(-rmat[1,2], rmat[1,1])
        y = math.atan2(-rmat[2,0], sy)
        z = 0
    # Convert to degrees
    return math.degrees(x), math.degrees(y), math.degrees(z)

import collections

# Rolling window for temporal smoothing (last 50 frames ~ 5 seconds at 10fps)
history_window = collections.deque(maxlen=50)

# --- Global state for the new detectors -------------------------------------------------

# Auto-calibration baseline for eyebrow resting height (first N frames after connect)
eyebrow_calibration = {"samples": [], "baseline": None, "calibrated": False}

# Smoothing windows for mouth aspect ratio (yawn) and lip gap (talking / movement)
mar_window = collections.deque(maxlen=15)
lip_gap_window = collections.deque(maxlen=10)

# Yawn state machine: tracks how long the mouth has been open above threshold
yawn_state = {"start_time": None, "yawning": False}

# No-face tracking: consecutive missing-face frames + when it started
no_face_state = {"consecutive": 0, "since": None}

# Emotion history: list of {"emotion": str, "timestamp": float} recorded on every change
emotion_history = []
current_emotion = {"label": None}

def calculate_final_score(avg_ear, pitch, yaw, gaze_distracted=False):
    frame_score = 100
    if avg_ear < 0.22: frame_score -= 50
    if abs(yaw) > 25: frame_score -= 40
    if abs(pitch) > 20: frame_score -= 30
    if gaze_distracted: frame_score -= 40 # Pupil tracking
    
    frame_score = max(0, frame_score)
    history_window.append(frame_score)
    
    # Smooth score over time
    return int(sum(history_window) / len(history_window))

# Euclidean distance for 3D points
def calculate_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

# Calculate Eye Aspect Ratio (EAR)
def calculate_ear(eye_landmarks):
    v1 = calculate_distance(eye_landmarks[1], eye_landmarks[5])
    v2 = calculate_distance(eye_landmarks[2], eye_landmarks[4])
    h = calculate_distance(eye_landmarks[0], eye_landmarks[3])
    return (v1 + v2) / (2.0 * h) if h != 0 else 0

# MediaPipe Eye Landmark Indices
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

def get_eye_center(eye_landmarks):
    # Index 0 and 3 are the outer and inner corners. These are anchored to the skull
    # and DO NOT move when you look up or down, providing a perfectly rigid center!
    x = (eye_landmarks[0].x + eye_landmarks[3].x) / 2.0
    y = (eye_landmarks[0].y + eye_landmarks[3].y) / 2.0
    return x, y

def get_eye_dimensions(eye_landmarks):
    xs = [pt.x for pt in eye_landmarks]
    ys = [pt.y for pt in eye_landmarks]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    return width, height

# ---------------------------------------------------------------------------------------
# EYEBROW UP / DOWN DETECTION
# ---------------------------------------------------------------------------------------
def calculate_eyebrow_position(left_eyebrow, right_eyebrow, left_eye, right_eye):
    """
    Measures how raised or lowered the eyebrows are relative to the eyes.
    Normalized by eye width (a rigid, scale-stable reference) so it works
    regardless of distance from the camera.

    Returns:
        raw_ratio (float): avg vertical gap between eyebrow midpoint and eye midpoint,
                            normalized by eye width.
        state (str): "Raised", "Lowered", or "Neutral" relative to the auto-calibrated
                      baseline captured during the first few seconds of the session.
    """
    def brow_to_eye_gap(eyebrow_pts, eye_pts):
        brow_y = sum(p.y for p in eyebrow_pts) / len(eyebrow_pts)
        eye_cx, eye_cy = get_eye_center(eye_pts)
        eye_width = abs(eye_pts[3].x - eye_pts[0].x)
        if eye_width == 0:
            return 0
        # In image coordinates, smaller y = higher on screen = more "raised"
        return (eye_cy - brow_y) / eye_width

    left_gap = brow_to_eye_gap(left_eyebrow, left_eye)
    right_gap = brow_to_eye_gap(right_eyebrow, right_eye)
    raw_ratio = (left_gap + right_gap) / 2.0

    # Auto-calibrate baseline from the first 30 frames (resting eyebrow position)
    if not eyebrow_calibration["calibrated"]:
        eyebrow_calibration["samples"].append(raw_ratio)
        if len(eyebrow_calibration["samples"]) >= 30:
            eyebrow_calibration["baseline"] = sum(eyebrow_calibration["samples"]) / len(eyebrow_calibration["samples"])
            eyebrow_calibration["calibrated"] = True
        # Not calibrated yet, assume neutral
        return raw_ratio, "Neutral"

    baseline = eyebrow_calibration["baseline"]
    delta = raw_ratio - baseline

    if delta > 0.06:
        state = "Raised"       # surprise / interest / questioning
    elif delta < -0.04:
        state = "Lowered"      # frowning / concentration / confusion / anger
    else:
        state = "Neutral"

    return raw_ratio, state


def detect_gaze(iris, eye_landmarks):
    center_x, center_y = get_eye_center(eye_landmarks)
    
    # We use WIDTH to normalize BOTH X and Y because the eye width is a rigid bone structure.
    # The eye height expands/contracts when looking up/down, which would ruin the math!
    width = abs(eye_landmarks[3].x - eye_landmarks[0].x)
    if width == 0: return 0, 0
        
    dx = iris.x - center_x
    dy = iris.y - center_y
    
    ratio_x = dx / width
    ratio_y = dy / width
    
    return ratio_x, ratio_y


# ---------------------------------------------------------------------------------------
# MOUTH ASPECT RATIO (shared helper for yawn + lip movement + smile)
# ---------------------------------------------------------------------------------------
def calculate_mouth_aspect_ratio(mouth_landmarks):
    """
    mouth_landmarks expected order: [left_corner, right_corner, top_outer, bottom_outer,
                                      top_inner, bottom_inner]
    MAR = vertical opening / horizontal mouth width. Used for yawn detection.
    """
    left_corner, right_corner, top_outer, bottom_outer, top_inner, bottom_inner = mouth_landmarks[:6]
    width = calculate_distance(left_corner, right_corner)
    if width == 0:
        return 0
    vertical = calculate_distance(top_inner, bottom_inner)
    return vertical / width


# ---------------------------------------------------------------------------------------
# LIP MOVEMENT DETECTION (talking / mouth activity, independent of yawning)
# ---------------------------------------------------------------------------------------
def detect_lip_movement(mouth_landmarks):
    """
    Tracks frame-to-frame variance in mouth opening to flag active lip movement
    (e.g. talking, muttering) as distinct from a static open/closed mouth.
    Returns (is_moving: bool, movement_amount: float)
    """
    mar = calculate_mouth_aspect_ratio(mouth_landmarks)
    lip_gap_window.append(mar)

    if len(lip_gap_window) < 3:
        return False, 0.0

    # Movement = how much the MAR is fluctuating recently (std-dev-like spread)
    avg = sum(lip_gap_window) / len(lip_gap_window)
    variance = sum((v - avg) ** 2 for v in lip_gap_window) / len(lip_gap_window)
    movement_amount = math.sqrt(variance)

    is_moving = movement_amount > 0.015  # empirical threshold for active lip motion
    return is_moving, movement_amount


# ---------------------------------------------------------------------------------------
# YAWN DETECTION (sustained wide mouth opening over time, not just one frame)
# ---------------------------------------------------------------------------------------
def detect_yawn(mouth_landmarks, min_duration_sec=1.2):
    """
    A yawn = MAR stays above threshold continuously for min_duration_sec.
    Single-frame wide-mouth (e.g. talking/laughing) will not trigger this.
    """
    mar = calculate_mouth_aspect_ratio(mouth_landmarks)
    mar_window.append(mar)
    smoothed_mar = sum(mar_window) / len(mar_window)

    YAWN_MAR_THRESHOLD = 0.55
    now = time.time()

    if smoothed_mar > YAWN_MAR_THRESHOLD:
        if yawn_state["start_time"] is None:
            yawn_state["start_time"] = now
        elapsed = now - yawn_state["start_time"]
        if elapsed >= min_duration_sec:
            yawn_state["yawning"] = True
    else:
        yawn_state["start_time"] = None
        yawn_state["yawning"] = False

    return yawn_state["yawning"], smoothed_mar


# ---------------------------------------------------------------------------------------
# SMILE DETECTION: genuine (Duchenne) vs fake/social smile
# ---------------------------------------------------------------------------------------
def detect_smile(mouth_landmarks, left_eye, right_eye):
    """
    Real (Duchenne) smiles involve the muscles around the eyes (orbicularis oculi),
    which visibly narrows/squints the eyes. Fake/social smiles only move the mouth
    corners and leave the eyes largely unaffected.

    Returns: (is_smiling: bool, smile_type: str) where smile_type is one of
              "None", "Fake/Social", "Genuine"
    """
    left_corner, right_corner, top_outer, bottom_outer = mouth_landmarks[:4]
    mouth_width = calculate_distance(left_corner, right_corner)
    mouth_center_y = (top_outer.y + bottom_outer.y) / 2.0

    # Mouth corners pulled UP and OUTWARD relative to center = smile shape
    corner_lift = mouth_center_y - ((left_corner.y + right_corner.y) / 2.0)
    # Normalize by mouth width for scale independence
    smile_shape_ratio = corner_lift / mouth_width if mouth_width else 0

    is_smiling = smile_shape_ratio > 0.08

    if not is_smiling:
        return False, "None"

    # Eye-involvement check: genuine smiles compress the eye vertically (EAR drops)
    avg_ear = (calculate_ear(left_eye) + calculate_ear(right_eye)) / 2.0

    # Empirical threshold: eyes noticeably squinted alongside the smile = genuine
    # Raised to 0.32 so that very slight natural eye wrinkling triggers Genuine
    if avg_ear < 0.32:
        return True, "Genuine"
    else:
        return True, "Fake/Social"


# ---------------------------------------------------------------------------------------
# FACIAL TENSION DETECTION (brow furrow + jaw/lip clench)
# ---------------------------------------------------------------------------------------
def detect_facial_tension(left_eyebrow, right_eyebrow, mouth_landmarks, is_smiling=False):
    """
    Tension shows up as: eyebrows drawn together/down (furrow) and lips pressed
    thin/tight. Combines inner-brow distance with mouth compression.
    Returns (is_tense: bool, tension_score: float 0-100)
    """
    # Calculate minimum possible gap between any point on left brow and right brow
    # This prevents failures caused by landmark index ordering from the frontend
    brow_gap = min(calculate_distance(pl, pr) for pl in left_eyebrow for pr in right_eyebrow)

    left_corner, right_corner, top_outer, bottom_outer = mouth_landmarks[:4]
    mouth_width = calculate_distance(left_corner, right_corner)
    lip_thickness = calculate_distance(top_outer, bottom_outer)

    # Thin lips relative to mouth width = pressed/tight lips
    lip_compression = 1 - (lip_thickness / mouth_width) if mouth_width else 0

    tension_score = 0
    
    # A wide smile mathematically stretches the mouth width and lips, which fakes a tense brow and lip compression.
    if is_smiling:
        return False, 0

    # Narrow brow gap (relative to mouth width as a stable face-scale reference)
    if mouth_width and (brow_gap / mouth_width) < 0.50:
        tension_score += 50
    # Lowered the lip compression threshold from 0.85 to 0.65 for more sensitivity
    if lip_compression > 0.65:
        tension_score += 50

    is_tense = tension_score >= 50
    return is_tense, tension_score


# ---------------------------------------------------------------------------------------
# EMOTION / MOOD DETECTION (3 labels: Bored, Interested, Confused)
# ---------------------------------------------------------------------------------------
def detect_emotion(avg_ear, pitch, yaw, eyebrow_state, is_tense, smile_type, is_yawning):
    """
    Combines the lower-level signals into one of three high-level mood labels.
    This is a rule-based classifier layered on top of the per-feature detectors,
    kept intentionally separate so it can later be swapped for a trained model.
    """
    # Yawning or heavy eye-closure + neutral/lowered brow = disengaged
    if is_yawning or avg_ear < 0.20:
        return "Bored"

    # Furrowed brow / tension without a smile = struggling to understand
    if is_tense and eyebrow_state == "Lowered" and smile_type == "None":
        return "Confused"

    # Raised eyebrows + head steady + genuine smile = engaged
    if eyebrow_state == "Raised" or smile_type == "Genuine":
        return "Interested"

    # Large head movement away from the screen with low brow activity = bored
    if abs(yaw) > 25 or abs(pitch) > 20:
        return "Bored"

    # Default: mild lowered brow with no other strong signal -> leaning confused,
    # otherwise treat sustained neutral attentiveness as interested.
    if eyebrow_state == "Lowered":
        return "Confused"

    return "Interested"


def record_emotion_change(label):
    """
    Logs a timestamped entry to emotion_history ONLY when the emotion label
    actually changes from the previous frame, so the history stays a clean
    timeline of transitions rather than one entry per frame.
    """
    if current_emotion["label"] != label:
        entry = {
            "emotion": label,
            "previous_emotion": current_emotion["label"],
            "timestamp": time.time(),
        }
        emotion_history.append(entry)
        current_emotion["label"] = label
        return entry
    return None


# ---------------------------------------------------------------------------------------
# NO-FACE WARNING TRACKING
# ---------------------------------------------------------------------------------------
def handle_no_face():
    """
    Tracks consecutive no-face frames and produces an escalating warning once the
    face has been missing for a meaningful duration (not just a single dropped frame).
    """
    no_face_state["consecutive"] += 1
    if no_face_state["since"] is None:
        no_face_state["since"] = time.time()

    elapsed = time.time() - no_face_state["since"]
    warning = None
    if elapsed >= 3:
        warning = f"WARNING: No face detected for {elapsed:.1f}s"
    return warning, elapsed


def reset_no_face_state():
    no_face_state["consecutive"] = 0
    no_face_state["since"] = None


# Initialize the backend application
app = FastAPI(title="Attention Detection Backend")

# Allow the Next.js frontend to make HTTP requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/telemetry")
async def get_telemetry():
    try:
        async with SessionLocal() as db:
            result = await db.execute(
                select(TelemetryRecord).order_by(TelemetryRecord.timestamp.desc()).limit(100)
            )
            records = result.scalars().all()
            
            # Reverse so the oldest is first, making it perfect for ECharts timeline
            return [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "focus_score": r.focus_score,
                    "status": r.status,
                    "mood": r.mood,
                    "is_tense": r.is_tense,
                }
                for r in reversed(records)
            ]
    except Exception as e:
        print(f"Error fetching telemetry: {e}")
        return []

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        agent = get_agent()
        messages = [HumanMessage(content=req.message)]
        
        # Run the LangGraph state machine with the user's prompt
        result = await agent.ainvoke({"messages": messages})
        
        # The agent's final response is the last message in the state
        final_message = result["messages"][-1].content
        return {"response": final_message}
    except Exception as e:
        return {"response": f"AI Error: Make sure your GROQ_API_KEY is valid! Details: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "FocusAI Backend is running securely."}

# WebSocket endpoint to receive video frames from the user's browser
@app.websocket("/ws/user")
async def user_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("User connected securely via WebSocket.")
    
    try:
        while True:
            # Receive the JSON Feature Vectors from the Edge AI Browser
            data = await websocket.receive_json()
            attention_score = "No Face Detected"
            
            if data and data.get("no_face"):
                score = int(sum(history_window) / len(history_window)) if history_window else 0
                warning, elapsed = handle_no_face()
                attention_score = f"User Not Found | Overall Focus: {score}%"
                if warning:
                    attention_score = f"{warning} | Last Focus: {score}%"
            elif data and "right_eye" in data:
                # Face is present again — clear the no-face tracker
                reset_no_face_state()

                # 1. Reconstruct landmarks from the JSON payload
                class FakePoint:
                    def __init__(self, d):
                        self.x = d['x']
                        self.y = d['y']
                        self.z = d.get('z', 0)
                
                right_eye = [FakePoint(pt) for pt in data['right_eye']]
                left_eye = [FakePoint(pt) for pt in data['left_eye']]
                
                # 2. Calculate the average Eye Aspect Ratio (EAR)
                avg_ear = (calculate_ear(right_eye) + calculate_ear(left_eye)) / 2.0
                
                # 3. Calculate 4-Directional Pupil Gaze
                gaze_distracted = False
                if data.get('irises'):
                    iris_a = FakePoint(data['irises'][0])
                    iris_b = FakePoint(data['irises'][1])
                    
                    # Bulletproof Iris Assignment: Match the iris to the closest eye
                    right_eye_center_x, _ = get_eye_center(right_eye)
                    if abs(iris_a.x - right_eye_center_x) < abs(iris_b.x - right_eye_center_x):
                        right_iris, left_iris = iris_a, iris_b
                    else:
                        right_iris, left_iris = iris_b, iris_a
                    
                    r_rx, r_ry = detect_gaze(right_iris, right_eye)
                    l_rx, l_ry = detect_gaze(left_iris, left_eye)
                    
                    avg_rx = (r_rx + l_rx) / 2.0
                    avg_ry = (r_ry + l_ry) / 2.0
                    
                    # Threshold: 22% horizontally, 15% vertically (since the eye is shorter than it is wide)
                    if abs(avg_rx) > 0.22 or abs(avg_ry) > 0.15:
                        gaze_distracted = True
                
                # 4. Get Head Pose (Pitch, Yaw, Roll)
                pitch, yaw, roll = 0, 0, 0
                if data.get('matrix'):
                    # Convert the flat 16-element array back to a 4x4 matrix
                    flat_matrix = data['matrix']
                    matrix = np.array(flat_matrix).reshape(4, 4)
                    pitch, yaw, roll = calculate_head_pose(matrix)
                
                # 5. Attention Logic
                final_score = calculate_final_score(avg_ear, pitch, yaw, gaze_distracted)
                
                if avg_ear < 0.22:
                    status = "Blinking / Eyes Closed"
                elif abs(yaw) > 25 or abs(pitch) > 20: 
                    status = "Distracted" # Head turned away
                elif gaze_distracted:
                    status = "Distracted" # Looking away with pupils
                else:
                    status = "Attentive"
                    
                attention_score = f"{status} | Overall Focus: {final_score}%"
                score = final_score

                # 6. Extended facial-feature detectors (eyebrows, lips, smile, tension, yawn)
                # These only run if the frontend sends the extra landmark groups; each is
                # independently optional so missing data never breaks the core score above.
                eyebrow_state = "Neutral"
                is_moving_lips, lip_movement_amount = False, 0.0
                is_yawning, mar = False, 0.0
                is_smiling, smile_type = False, "None"
                is_tense, tension_score = False, 0

                if data.get('left_eyebrow') and data.get('right_eyebrow'):
                    left_eyebrow = [FakePoint(pt) for pt in data['left_eyebrow']]
                    right_eyebrow = [FakePoint(pt) for pt in data['right_eyebrow']]
                    _, eyebrow_state = calculate_eyebrow_position(left_eyebrow, right_eyebrow, left_eye, right_eye)

                if data.get('mouth'):
                    mouth = [FakePoint(pt) for pt in data['mouth']]
                    is_moving_lips, lip_movement_amount = detect_lip_movement(mouth)
                    is_yawning, mar = detect_yawn(mouth)
                    is_smiling, smile_type = detect_smile(mouth, left_eye, right_eye)
                    if data.get('left_eyebrow') and data.get('right_eyebrow'):
                        is_tense, tension_score = detect_facial_tension(left_eyebrow, right_eyebrow, mouth, is_smiling)

                # 7. High-level mood classification + timestamped change log
                mood = detect_emotion(avg_ear, pitch, yaw, eyebrow_state, is_tense, smile_type, is_yawning)
                emotion_change = record_emotion_change(mood)

                extra_features = {
                    "eyebrows": eyebrow_state,
                    "lip_movement": is_moving_lips,
                    "yawning": is_yawning,
                    "smile": smile_type,
                    "facial_tension": is_tense,
                    "tension_score": tension_score,
                    "mood": mood,
                }
                if emotion_change:
                    extra_features["emotion_changed_at"] = emotion_change["timestamp"]
                    extra_features["previous_mood"] = emotion_change["previous_emotion"]
            
            # 8. Save telemetry to TimescaleDB
            try:
                async with SessionLocal() as db:
                    record = TelemetryRecord(
                        session_id=f"session_{id(websocket)}",
                        focus_score=score,
                        status=status,
                        mood=mood,
                        is_tense=is_tense
                    )
                    db.add(record)
                    await db.commit()
            except Exception as db_err:
                print(f"Database insert error: {db_err}")

            # Send the attention score + extended features back to the frontend
            payload = {"attention_score": attention_score}
            if data and "right_eye" in data:
                payload["features"] = extra_features
                payload["emotion_history"] = emotion_history[-10:]  # last 10 transitions
            await websocket.send_json(payload)
    except Exception as e:
        print(f"User disconnected: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)