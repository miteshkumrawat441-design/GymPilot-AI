import os
import cv2
import av
import numpy as np
import mediapipe as mp
import threading
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.squat import SquatDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curl import BicepsCurlDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.lunges import LungesDetector
from services.config.workout_config import POSE_CONNECTIONS


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"

        model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")
        base_option = python.BaseOptions(model_asset_path=model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_option,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        self._detectors = {
            "Squats": SquatDetector(),
            "Push-ups": PushUpDetector(),
            "Biceps Curls (Dumbbell)": BicepsCurlDetector(),
            "Shoulder Press": ShoulderPressDetector(),
            "Lunges": LungesDetector(),
        }

        self._frame_timestamps_ms = 0
    
    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()
        
    def set_exercise(self, exercise_type):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self):
        with self._lock:
            return self._exercise_type

    def _draw_joint_angle_badge(self, img, x, y, angle_val, label=""):
        h, w = img.shape[:2]
        px = max(50, min(w - 70, int(x)))
        py = max(35, min(h - 30, int(y)))
        
        text = f"{int(angle_val)}°" if label == "" else f"{label} {int(angle_val)}°"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)

        # Draw dark background badge
        cv2.rectangle(
            img,
            (px - 6, py - th - 6),
            (px + tw + 6, py + 6),
            (10, 15, 25),
            -1
        )
        # Green border
        cv2.rectangle(
            img,
            (px - 6, py - th - 6),
            (px + tw + 6, py + 6),
            (34, 197, 94),
            1
        )
        # Green text
        cv2.putText(
            img,
            text,
            (px, py),
            font,
            font_scale,
            (74, 222, 128),
            thickness,
            cv2.LINE_AA
        )
        
    def _draw_skeleton(self, img, landmarks):
        h, w = img.shape[:2]

        # Draw connecting skeleton lines
        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                p1 = landmarks[start_idx]
                p2 = landmarks[end_idx]

                v1 = getattr(p1, 'visibility', 1.0)
                v2 = getattr(p2, 'visibility', 1.0)
                v1 = 1.0 if v1 is None else v1
                v2 = 1.0 if v2 is None else v2

                if v1 > 0.35 and v2 > 0.35:
                    cv2.line(
                        img,
                        (int(p1.x * w), int(p1.y * h)),
                        (int(p2.x * w), int(p2.y * h)),
                        (34, 197, 94),  # Athletic Green
                        3,
                        cv2.LINE_AA
                    )
        
        # Draw joint dots
        for lm in landmarks:
            v = getattr(lm, 'visibility', 1.0)
            v = 1.0 if v is None else v
            if v > 0.35:
                cx, cy = int(lm.x * w), int(lm.y * h)
                # Outer white circle
                cv2.circle(img, (cx, cy), 7, (255, 255, 255), 1, cv2.LINE_AA)
                # Inner green dot
                cv2.circle(img, (cx, cy), 5, (74, 222, 128), -1, cv2.LINE_AA)

    def _draw_joint_angles(self, img, landmarks, metrics, ex_type):
        h, w = img.shape[:2]

        if ex_type == "Squats":
            # Knee Angle badge at the knee joint
            knee_angle = metrics.get("knee_angle", 0)
            # Pick left or right knee (index 25 or 26)
            l_knee = landmarks[25]
            r_knee = landmarks[26]
            knee = l_knee if (getattr(l_knee, 'visibility', 1.0) or 0) >= (getattr(r_knee, 'visibility', 1.0) or 0) else r_knee
            if knee:
                self._draw_joint_angle_badge(img, knee.x * w + 15, knee.y * h, knee_angle, "KNEE")

            # Back angle badge at hip
            back_angle = metrics.get("back_angle", 0)
            l_hip = landmarks[23]
            r_hip = landmarks[24]
            hip = l_hip if (getattr(l_hip, 'visibility', 1.0) or 0) >= (getattr(r_hip, 'visibility', 1.0) or 0) else r_hip
            if hip:
                self._draw_joint_angle_badge(img, hip.x * w + 15, hip.y * h, back_angle, "BACK")

        elif ex_type in ["Push-ups", "Biceps Curls (Dumbbell)", "Shoulder Press"]:
            # Elbow angle badge
            elbow_angle = metrics.get("elbow_angle", 0)
            l_elbow = landmarks[13]
            r_elbow = landmarks[14]
            elbow = l_elbow if (getattr(l_elbow, 'visibility', 1.0) or 0) >= (getattr(r_elbow, 'visibility', 1.0) or 0) else r_elbow
            if elbow:
                self._draw_joint_angle_badge(img, elbow.x * w + 15, elbow.y * h, elbow_angle, "ELBOW")

        elif ex_type == "Lunges":
            front_knee_angle = metrics.get("front_knee_angle", 0)
            l_knee = landmarks[25]
            r_knee = landmarks[26]
            knee = l_knee if (getattr(l_knee, 'visibility', 1.0) or 0) >= (getattr(r_knee, 'visibility', 1.0) or 0) else r_knee
            if knee:
                self._draw_joint_angle_badge(img, knee.x * w + 15, knee.y * h, front_knee_angle, "KNEE")
            
    def _draw_no_pose_warnings(self, img):
        h, w = img.shape[:2]
        # Dark banner
        cv2.rectangle(img, (20, 20), (320, 90), (10, 15, 25), -1)
        cv2.rectangle(img, (20, 20), (320, 90), (0, 0, 255), 2)
        cv2.putText(
            img,
            "NO POSE DETECTED",
            (35, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 100, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            img,
            "STEP INTO CAMERA FRAME",
            (35, 78),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )

    def _draw_overlays(self, img, metrics, ex_type):
        h, w = img.shape[:2]

        # Top HUD Bar: Exercise Name & Reps
        reps = metrics.get("reps", 0)
        top_bar_text = f"{ex_type.upper()} | REPS: {reps}"
        cv2.rectangle(img, (15, 15), (min(w - 15, 340), 55), (10, 15, 25), -1)
        cv2.rectangle(img, (15, 15), (min(w - 15, 340), 55), (34, 197, 94), 1)
        cv2.putText(
            img,
            top_bar_text,
            (25, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        # Bottom HUD Bar: Form status
        status_text = ""
        if ex_type == "Squats":
            status_text = f"DEPTH: {metrics.get('depth_status', 'N/A')}"
        elif ex_type == "Push-ups":
            status_text = f"BODY: {metrics.get('body_alignment', 'N/A')} | HIP: {metrics.get('hip_status', 'N/A')}"
        elif ex_type == "Biceps Curls (Dumbbell)":
            status_text = f"SWING: {metrics.get('swing_status', 'N/A')} | SHOULDER: {metrics.get('shoulder_status', 'N/A')}"
        elif ex_type == "Shoulder Press":
            status_text = f"EXT: {metrics.get('extension_status', 'N/A')} | ARCH: {metrics.get('back_arch_status', 'N/A')}"
        elif ex_type == "Lunges":
            status_text = f"BALANCE: {metrics.get('balance_status', 'N/A')}"

        if status_text:
            cv2.rectangle(img, (15, h - 50), (min(w - 15, 460), h - 15), (10, 15, 25), -1)
            cv2.rectangle(img, (15, h - 50), (min(w - 15, 460), h - 15), (34, 197, 94), 1)
            cv2.putText(
                img,
                status_text,
                (25, h - 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (74, 222, 128),
                2,
                cv2.LINE_AA
            )

    def recv(self, frame):
        image = np.asarray(
            cv2.flip(frame.to_ndarray(format="bgr24"), 1),
            dtype=np.uint8
        )

        # Convert correctly from BGR to RGB for MediaPipe
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        )

        self._frame_timestamps_ms += 33
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]

            # 1. Draw joint dots and skeleton lines
            self._draw_skeleton(image, landmarks)

            ex_type = self.get_exercise()
            detector = self._detectors.get(ex_type)

            if detector:
                metrics = detector.process(landmarks)
                metrics["pose_detected"] = True

                # 2. Draw live angles directly on active joints
                self._draw_joint_angles(image, landmarks, metrics, ex_type)

                # 3. Draw top & bottom HUD overlays
                self._draw_overlays(image, metrics, ex_type)

                self.set_latest_metrics(metrics)
        else:
            self._draw_no_pose_warnings(image)
            
            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                else:
                    self._latest_metrics = {"pose_detected": False}

        return av.VideoFrame.from_ndarray(image, format="bgr24")