from fastapi import APIRouter, WebSocket
import numpy as np
from sqlalchemy import text

from database.connection import SessionLocal
from models.timescale import AttentionTimeline, EmotionTimeline, FacialMetrics, PresenceTimeline, Event
from utils.math import calculate_head_pose, detect_gaze, calculate_ear, get_eye_center
from services.emotion.analyzer import (
    calculate_eyebrow_position, detect_lip_movement, detect_yawn, detect_smile,
    detect_facial_tension, detect_emotion, record_emotion_change, emotion_history
)
from services.attention.scorer import calculate_final_score, handle_no_face, reset_no_face_state, history_window
from services.presence_verification import PresenceService

router = APIRouter()
presence_service = PresenceService(window_seconds=8.0)


def flatten_landmarks(data):
    """Create a compact motion vector from landmarks already sent by the browser."""
    vector = []
    for field in ("right_eye", "left_eye", "left_eyebrow", "right_eyebrow", "mouth", "irises"):
        for point in data.get(field) or []:
            vector.extend((float(point.get("x", 0)), float(point.get("y", 0)), float(point.get("z", 0))))
    return tuple(vector)

@router.websocket("/ws/user/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str):
    await websocket.accept()
    print(f"[{user_id}] Connected to AI Telemetry stream.")
    
    try:
        while True:
            data = await websocket.receive_json()
            attention_score = "No Face Detected"
            
            if data and data.get("no_face"):
                score = 0
                warning, elapsed = handle_no_face()
                attention_score = "User Not Found"
                
                # Initialize defaults so DB can record the absence
                avg_ear, mar, pitch, yaw, roll = 0.0, 0.0, 0.0, 0.0, 0.0
                eyebrow_state = "Neutral"
                is_moving_lips, is_yawning, is_tense = False, False, False
                smile_type = "None"
                mood = "Absent"
                gaze_x, gaze_y = 0.0, 0.0
                presence_landmarks = ()
                
            elif data and "right_eye" in data:
                reset_no_face_state()

                class FakePoint:
                    def __init__(self, d):
                        self.x = d['x']
                        self.y = d['y']
                        self.z = d.get('z', 0)
                
                right_eye = [FakePoint(pt) for pt in data['right_eye']]
                left_eye = [FakePoint(pt) for pt in data['left_eye']]
                
                avg_ear = (calculate_ear(right_eye) + calculate_ear(left_eye)) / 2.0
                
                gaze_distracted = False
                gaze_x, gaze_y = 0.0, 0.0
                if data.get('irises'):
                    iris_a = FakePoint(data['irises'][0])
                    iris_b = FakePoint(data['irises'][1])
                    
                    right_eye_center_x, _ = get_eye_center(right_eye)
                    if abs(iris_a.x - right_eye_center_x) < abs(iris_b.x - right_eye_center_x):
                        right_iris, left_iris = iris_a, iris_b
                    else:
                        right_iris, left_iris = iris_b, iris_a
                    
                    r_rx, r_ry = detect_gaze(right_iris, right_eye)
                    l_rx, l_ry = detect_gaze(left_iris, left_eye)
                    
                    avg_rx = (r_rx + l_rx) / 2.0
                    avg_ry = (r_ry + l_ry) / 2.0
                    gaze_x, gaze_y = avg_rx, avg_ry
                    
                    # Increased sensitivity: a ratio of > 0.12 means the iris has moved significantly off-center horizontally
                    if abs(avg_rx) > 0.12 or abs(avg_ry) > 0.08:
                        gaze_distracted = True
                
                pitch, yaw, roll = 0, 0, 0
                if data.get('matrix'):
                    flat_matrix = data['matrix']
                    matrix = np.array(flat_matrix).reshape(4, 4)
                    pitch, yaw, roll = calculate_head_pose(matrix)
                
                # MOOD IS NOW CALCULATED FIRST SO IT CAN BE PASSED TO THE SCORER
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

                mood = detect_emotion(avg_ear, pitch, yaw, eyebrow_state, is_tense, smile_type, is_yawning)
                emotion_change = record_emotion_change(mood)
                
                final_score = calculate_final_score(avg_ear, pitch, yaw, gaze_distracted, mood)
                
                if avg_ear < 0.22:
                    status = "Blinking / Eyes Closed"
                elif abs(yaw) > 25 or abs(pitch) > 20: 
                    status = "Distracted"
                elif gaze_distracted:
                    status = "Distracted"
                elif mood == "Bored":
                    status = "Bored (Focus Dropping)"
                else:
                    status = "Attentive"
                    
                # CALIBRATION: Fetch ground truth offset
                offset = 0
                try:
                    async with SessionLocal() as db:
                        cal_res = await db.execute(text("""
                            SELECT c.base_offset FROM calibrations c 
                            JOIN users u ON c.user_id = u.id 
                            WHERE u.username = :uid
                        """), {"uid": user_id})
                        cal_row = cal_res.fetchone()
                        if cal_row: offset = cal_row.base_offset
                except Exception as e:
                    pass
                
                final_score = max(0, min(100, final_score + offset))
                
                attention_score = f"{status} | Overall Focus: {final_score}%"
                score = final_score

                extra_features = {
                    "eyebrows": eyebrow_state,
                    "lip_movement": is_moving_lips,
                    "yawning": is_yawning,
                    "smile": smile_type,
                    "facial_tension": is_tense,
                    "tension_score": tension_score if 'tension_score' in locals() else 0,
                    "mood": mood,
                }
                presence_landmarks = flatten_landmarks(data)
                if 'emotion_change' in locals() and emotion_change:
                    extra_features["emotion_changed_at"] = emotion_change["timestamp"]
                    extra_features["previous_mood"] = emotion_change["previous_emotion"]
            
            presence_result = presence_service.evaluate(
                user_id, session_id,
                no_face=bool(data and data.get("no_face")),
                ear=avg_ear, mar=mar, pitch=pitch, yaw=yaw, roll=roll,
                gaze_x=gaze_x, gaze_y=gaze_y, lip_movement=is_moving_lips,
                landmarks=presence_landmarks,
            )

            try:
                async with SessionLocal() as db:
                    s_id = session_id
                    
                    att_rec = AttentionTimeline(
                        session_id=s_id,
                        user_id=user_id,
                        attention_score=round(score, 1),
                        confidence=1.0
                    )
                    
                    emo_rec = EmotionTimeline(
                        session_id=s_id,
                        user_id=user_id,
                        emotion=mood,
                        confidence=1.0
                    )
                    
                    face_rec = FacialMetrics(
                        session_id=s_id,
                        user_id=user_id,
                        ear=avg_ear,
                        mar=mar,
                        smile_type=smile_type,
                        eyebrow_raise=1.0 if eyebrow_state == "Raised" else 0.0,
                        eyebrow_lower=1.0 if eyebrow_state == "Lowered" else 0.0,
                        head_pitch=pitch,
                        head_roll=roll,
                        head_yaw=yaw,
                        is_tense=is_tense,
                        yawning=is_yawning,
                        lip_movement=is_moving_lips
                    )
                    presence_rec = PresenceTimeline(
                        session_id=s_id,
                        user_id=user_id,
                        presence_score=presence_result.score,
                        presence_status=presence_result.status,
                        confidence=presence_result.confidence,
                        blink_count=presence_result.blink_count,
                        facial_motion=presence_result.facial_motion,
                        optical_flow=presence_result.optical_flow,
                        frozen_seconds=presence_result.frozen_seconds,
                        replay_detected=presence_result.replay_detected,
                    )
                    
                    db.add_all([att_rec, emo_rec, face_rec, presence_rec])
                    if presence_result.spoof_alert:
                        db.add(Event(
                            session_id=s_id, user_id=user_id,
                            event_type="presence_spoof_alert",
                            confidence=presence_result.confidence,
                            metadata_info={"status": presence_result.status, "score": presence_result.score},
                        ))
                    await db.commit()
            except Exception as db_err:
                print(f"Database insert error: {db_err}")

            payload = {"attention_score": attention_score, "presence": presence_result.as_dict()}
            if data and "right_eye" in data:
                payload["features"] = extra_features
                payload["emotion_history"] = emotion_history[-10:]
            await websocket.send_json(payload)
    except Exception as e:
        print(f"User disconnected: {e}")
