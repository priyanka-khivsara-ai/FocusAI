from __future__ import annotations

import time
from dataclasses import asdict, dataclass

from .blink_analysis import BlinkAnalysis
from .motion_analysis import MotionAnalysis
from .optical_flow import LandmarkOpticalFlow
from .presence_score import PresenceScore
from .replay_detection import ReplayDetection
from .temporal_buffer import PresenceFrame, TemporalBuffer


@dataclass
class PresenceResult:
    score: float
    status: str
    confidence: float
    blink_count: int
    facial_motion: float
    optical_flow: float
    frozen_seconds: float
    replay_detected: bool
    spoof_alert: bool

    def as_dict(self) -> dict:
        return asdict(self)


class PresenceService:
    """Stateful service keyed by participant; appropriate for one FastAPI worker."""

    def __init__(self, window_seconds: float = 8.0) -> None:
        self.window_seconds = window_seconds
        self._buffers: dict[tuple[str, str], TemporalBuffer] = {}
        self._last_status: dict[tuple[str, str], str] = {}

    def evaluate(self, user_id: str, session_id: str, *, no_face: bool = False,
                 ear: float = 0.0, mar: float = 0.0, pitch: float = 0.0,
                 yaw: float = 0.0, roll: float = 0.0, gaze_x: float = 0.0,
                 gaze_y: float = 0.0, lip_movement: bool = False,
                 landmarks: tuple[float, ...] = ()) -> PresenceResult:
        key = (session_id, user_id)
        if no_face:
            return self._result(key, 0.0, "UNKNOWN", 0.0, 0, 0.0, 0.0, 0.0, False)

        buffer = self._buffers.setdefault(key, TemporalBuffer(self.window_seconds))
        buffer.append(PresenceFrame(time.time(), ear, mar, pitch, yaw, roll, gaze_x, gaze_y, lip_movement, landmarks))
        frames = buffer.values()
        blink = BlinkAnalysis.metrics(frames)
        motion = MotionAnalysis.metrics(frames)
        motion["blink_score"] = blink["blink_score"]
        motion["optical_flow"] = LandmarkOpticalFlow.score(frames)
        replay = ReplayDetection.analyse(frames, motion["facial_motion"])
        score = PresenceScore.calculate(motion, float(replay["frozen_seconds"]))
        confidence = min(1.0, buffer.duration / 5.0)

        if float(replay["frozen_seconds"]) >= 5.0:
            status = "PHOTO_SPOOF"
        elif bool(replay["replay_pattern"]) and confidence >= 0.8:
            status = "VIDEO_REPLAY"
        elif confidence < 0.7:
            status = "LOW_CONFIDENCE"
        elif score >= 55.0:
            status = "LIVE"
        else:
            status = "LOW_CONFIDENCE"
        return self._result(key, score, status, confidence, int(blink["blink_count"]), motion["facial_motion"], motion["optical_flow"], float(replay["frozen_seconds"]), bool(replay["replay_pattern"]))

    def _result(self, key: tuple[str, str], score: float, status: str, confidence: float,
                blink_count: int, facial_motion: float, optical_flow: float,
                frozen_seconds: float, replay_detected: bool) -> PresenceResult:
        previous = self._last_status.get(key)
        self._last_status[key] = status
        spoof_alert = status in {"PHOTO_SPOOF", "VIDEO_REPLAY", "SCREEN_REPLAY"} and status != previous
        return PresenceResult(score, status, confidence, blink_count, round(facial_motion, 6), round(optical_flow, 1), round(frozen_seconds, 2), replay_detected, spoof_alert)
