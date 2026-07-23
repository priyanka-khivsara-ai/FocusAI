# main.py
# FastAPI backend for Attention Detection System
from fastapi import FastAPI, WebSocket
import uvicorn
import numpy as np
import math

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


# Initialize the backend application
app = FastAPI(title="Attention Detection Backend")

@app.get("/")
async def root():
    return {"message": "FocusAI Backend is running securely."}

# WebSocket endpoint to receive video frames from the student's browser
@app.websocket("/ws/student")
async def student_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Student connected securely via WebSocket.")
    try:
        while True:
            # Receive the JSON Feature Vectors from the Edge AI Browser
            data = await websocket.receive_json()
            attention_score = "No Face Detected"
            
            if data and data.get("no_face"):
                score = int(sum(history_window) / len(history_window)) if history_window else 0
                attention_score = f"User Not Found | Overall Focus: {score}%"
            elif data and "right_eye" in data:
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
            
            # Send the attention score back to the frontend
            await websocket.send_json({"attention_score": attention_score})
    except Exception as e:
        print(f"Student disconnected: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
