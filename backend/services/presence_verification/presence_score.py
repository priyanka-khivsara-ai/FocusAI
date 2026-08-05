from __future__ import annotations


class PresenceScore:
    """Combines independent passive liveness signals into a transparent 0-100 score."""

    @staticmethod
    def calculate(metrics: dict[str, float], frozen_seconds: float) -> float:
        motion_score = min(100.0, metrics["facial_motion"] / 0.003 * 100.0)
        head_score = min(100.0, metrics["head_motion"] / 2.0 * 100.0)
        gaze_score = min(100.0, metrics["gaze_motion"] / 0.01 * 100.0)
        lip_score = min(100.0, metrics["lip_motion"] * 400.0)
        diversity_score = min(100.0, metrics["frame_diversity"] / 0.0008 * 100.0)
        score = (
            0.20 * metrics["blink_score"]
            + 0.25 * motion_score
            + 0.15 * head_score
            + 0.10 * gaze_score
            + 0.10 * lip_score
            + 0.10 * diversity_score
            + 0.10 * min(100.0, metrics["optical_flow"])
        )
        if frozen_seconds >= 5.0:
            score = min(score, 15.0)
        return round(max(0.0, min(100.0, score)), 1)
