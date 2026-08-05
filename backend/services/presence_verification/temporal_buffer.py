from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Sequence


@dataclass(frozen=True)
class PresenceFrame:
    timestamp: float
    ear: float
    mar: float
    pitch: float
    yaw: float
    roll: float
    gaze_x: float
    gaze_y: float
    lip_movement: bool
    landmarks: tuple[float, ...]


class TemporalBuffer:
    """A bounded rolling window. It stores numerical telemetry only, never frames."""

    def __init__(self, window_seconds: float = 8.0) -> None:
        self.window_seconds = window_seconds
        self.frames: Deque[PresenceFrame] = deque()

    def append(self, frame: PresenceFrame) -> None:
        self.frames.append(frame)
        cutoff = frame.timestamp - self.window_seconds
        while self.frames and self.frames[0].timestamp < cutoff:
            self.frames.popleft()

    def values(self) -> Sequence[PresenceFrame]:
        return tuple(self.frames)

    @property
    def duration(self) -> float:
        if len(self.frames) < 2:
            return 0.0
        return self.frames[-1].timestamp - self.frames[0].timestamp
