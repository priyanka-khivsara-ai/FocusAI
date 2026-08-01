import math
import time
import collections
from utils.math import calculate_distance, get_eye_center, calculate_ear

# --- Global state for the new detectors -------------------------------------------------

# Auto-calibration baseline for eyebrow resting height (first N frames after connect)
eyebrow_calibration = {"samples": [], "baseline": None, "calibrated": False}

# Smoothing windows for mouth aspect ratio (yawn) and lip gap (talking / movement)
mar_window = collections.deque(maxlen=15)
lip_gap_window = collections.deque(maxlen=10)

# Yawn state machine: tracks how long the mouth has been open above threshold
yawn_state = {"start_time": None, "yawning": False}

# Emotion history: list of {"emotion": str, "timestamp": float} recorded on every change
emotion_history = []
current_emotion = {"label": None}

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
