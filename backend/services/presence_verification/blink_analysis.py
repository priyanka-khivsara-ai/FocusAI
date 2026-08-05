from __future__ import annotations

import math
from typing import Sequence

from .temporal_buffer import PresenceFrame


class BlinkAnalysis:
    """Detects blink transitions and whether their timing has natural variation."""

    CLOSED_EAR = 0.22

    @staticmethod
    def metrics(frames: Sequence[PresenceFrame]) -> dict[str, float]:
        if len(frames) < 3:
            return {"blink_count": 0.0, "blink_score": 50.0, "blink_randomness": 0.0}

        starts: list[float] = []
        was_closed = False
        for frame in frames:
            closed = frame.ear > 0 and frame.ear < BlinkAnalysis.CLOSED_EAR
            if closed and not was_closed:
                starts.append(frame.timestamp)
            was_closed = closed

        duration = max(frames[-1].timestamp - frames[0].timestamp, 0.1)
        rate_per_minute = len(starts) * 60.0 / duration
        # A short observation window should not penalize a participant for not blinking yet.
        if duration < 5.0:
            blink_score = 55.0
        elif 2.0 <= rate_per_minute <= 35.0:
            blink_score = 100.0
        elif rate_per_minute == 0:
            blink_score = 20.0
        else:
            blink_score = 55.0

        intervals = [b - a for a, b in zip(starts, starts[1:])]
        if len(intervals) < 2:
            randomness = 0.5
        else:
            mean = sum(intervals) / len(intervals)
            deviation = math.sqrt(sum((value - mean) ** 2 for value in intervals) / len(intervals))
            randomness = min(1.0, deviation / max(mean, 0.1))
        return {
            "blink_count": float(len(starts)),
            "blink_score": blink_score,
            "blink_randomness": randomness,
        }
