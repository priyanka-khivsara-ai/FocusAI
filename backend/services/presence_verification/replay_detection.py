from __future__ import annotations

from typing import Sequence

from .temporal_buffer import PresenceFrame


class ReplayDetection:
    """Detects frozen landmark streams and a simple repeated-motion signature."""

    FROZEN_DELTA = 0.00008

    @staticmethod
    def analyse(frames: Sequence[PresenceFrame], facial_motion: float) -> dict[str, float | bool]:
        if len(frames) < 2:
            return {"frozen_seconds": 0.0, "replay_pattern": False}

        frozen_from = frames[-1].timestamp
        for previous, current in zip(reversed(frames[:-1]), reversed(frames[1:])):
            if not current.landmarks or len(previous.landmarks) != len(current.landmarks):
                break
            delta = sum(abs(a - b) for a, b in zip(previous.landmarks, current.landmarks)) / len(current.landmarks)
            if delta > ReplayDetection.FROZEN_DELTA:
                break
            frozen_from = previous.timestamp
        frozen_seconds = frames[-1].timestamp - frozen_from

        # A repeated clip often recreates an earlier pose vector after meaningful movement.
        replay_pattern = False
        if len(frames) >= 30 and facial_motion > ReplayDetection.FROZEN_DELTA:
            current = frames[-1].landmarks
            for prior in frames[:-15]:
                if len(prior.landmarks) != len(current):
                    continue
                distance = sum(abs(a - b) for a, b in zip(prior.landmarks, current)) / len(current)
                if distance < ReplayDetection.FROZEN_DELTA:
                    replay_pattern = True
                    break
        return {"frozen_seconds": frozen_seconds, "replay_pattern": replay_pattern}
