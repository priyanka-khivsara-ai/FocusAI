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

def calculate_final_score(avg_ear, pitch, yaw):
    frame_score = 100
    if avg_ear < 0.22: frame_score -= 50
    if abs(yaw) > 25: frame_score -= 40
    if abs(pitch) > 20: frame_score -= 30
    
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
            
            if data and "right_eye" in data:
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
                
                # 3. Get Head Pose (Pitch, Yaw, Roll)
                pitch, yaw, roll = 0, 0, 0
                if data.get('matrix'):
                    # Convert the flat 16-element array back to a 4x4 matrix
                    flat_matrix = data['matrix']
                    matrix = np.array(flat_matrix).reshape(4, 4)
                    pitch, yaw, roll = calculate_head_pose(matrix)
                
                # 4. Attention Logic
                final_score = calculate_final_score(avg_ear, pitch, yaw)
                
                if avg_ear < 0.22:
                    status = "Eyes Closed"
                elif abs(yaw) > 25 or abs(pitch) > 20: 
                    status = "Distracted"
                else:
                    status = "Attentive"
                    
                attention_score = f"{status} | Overall Focus: {final_score}%"
            
            # Send the attention score back to the frontend
            await websocket.send_json({"attention_score": attention_score})
    except Exception as e:
        print(f"Student disconnected: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
