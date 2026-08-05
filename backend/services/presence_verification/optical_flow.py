from __future__ import annotations

from typing import Sequence

from .temporal_buffer import PresenceFrame
from .motion_analysis import MotionAnalysis


class LandmarkOpticalFlow:
    """Privacy-preserving optical-flow approximation from existing landmark vectors."""

    @staticmethod
    def score(frames: Sequence[PresenceFrame]) -> float:
        motion = MotionAnalysis.metrics(frames)["facial_motion"]
        # Typical normalized landmark displacement is very small; cap to a stable 0-100 scale.
        return min(100.0, motion / 0.003 * 100.0)
