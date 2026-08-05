import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.presence_verification.motion_analysis import MotionAnalysis
from services.presence_verification.presence_service import PresenceService
from services.presence_verification.replay_detection import ReplayDetection
from services.presence_verification.temporal_buffer import PresenceFrame


def frame(timestamp, position=0.0, ear=0.3):
    return PresenceFrame(timestamp, ear, 0.2, position * 10, 0, 0, position, 0,
                         position > 0.002, (position, position + 0.1, 0.0) * 12)


class PresenceVerificationTests(unittest.TestCase):
    def test_landmark_motion_distinguishes_live_stream(self):
        metrics = MotionAnalysis.metrics([frame(0, 0), frame(1, 0.01), frame(2, 0.02)])
        self.assertGreater(metrics["facial_motion"], 0.001)
        self.assertGreater(metrics["head_motion"], 0)

    def test_static_photo_stream_is_marked_frozen(self):
        frames = [frame(float(second), 0.0) for second in range(7)]
        replay = ReplayDetection.analyse(frames, facial_motion=0.0)
        self.assertGreaterEqual(replay["frozen_seconds"], 6.0)
        self.assertFalse(replay["replay_pattern"])

    def test_service_classifies_a_long_static_stream_as_photo_spoof(self):
        service = PresenceService(window_seconds=8)
        with patch("services.presence_verification.presence_service.time.time", side_effect=range(7)):
            result = None
            alerts = []
            for _ in range(7):
                result = service.evaluate("student", "ROOM-101", ear=0.3, landmarks=(0.1, 0.2, 0.0) * 12)
                alerts.append(result.spoof_alert)
        self.assertEqual(result.status, "PHOTO_SPOOF")
        self.assertTrue(any(alerts))

    def test_no_face_is_unknown_not_a_spoof_accusation(self):
        result = PresenceService().evaluate("student", "ROOM-101", no_face=True)
        self.assertEqual(result.status, "UNKNOWN")
        self.assertFalse(result.spoof_alert)


if __name__ == "__main__":
    unittest.main()
