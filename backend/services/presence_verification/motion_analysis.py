from __future__ import annotations

import math
from typing import Sequence

from .temporal_buffer import PresenceFrame


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _standard_deviation(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return math.sqrt(_mean([(value - mean) ** 2 for value in values]))


class MotionAnalysis:
    """Uses landmark displacement as an optical-flow proxy without transmitting pixels."""

    @staticmethod
    def metrics(frames: Sequence[PresenceFrame]) -> dict[str, float]:
        if len(frames) < 2:
            return {
                "facial_motion": 0.0, "head_motion": 0.0, "gaze_motion": 0.0,
                "lip_motion": 0.0, "frame_diversity": 0.0,
            }

        landmark_deltas: list[float] = []
        for previous, current in zip(frames, frames[1:]):
            if len(previous.landmarks) != len(current.landmarks) or not current.landmarks:
                continue
            squared = sum((a - b) ** 2 for a, b in zip(previous.landmarks, current.landmarks))
            landmark_deltas.append(math.sqrt(squared / len(current.landmarks)))

        head_values = [abs(frame.pitch) + abs(frame.yaw) + abs(frame.roll) for frame in frames]
        gaze_values = [math.sqrt(frame.gaze_x ** 2 + frame.gaze_y ** 2) for frame in frames]
        return {
            "facial_motion": _mean(landmark_deltas),
            "head_motion": _standard_deviation(head_values),
            "gaze_motion": _standard_deviation(gaze_values),
            "lip_motion": sum(1 for frame in frames if frame.lip_movement) / len(frames),
            "frame_diversity": _standard_deviation(landmark_deltas),
        }
