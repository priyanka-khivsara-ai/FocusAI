"use client";

import React, { useEffect, useRef, useState } from "react";
import { FilesetResolver, FaceLandmarker } from "@mediapipe/tasks-vision";

function FeatureRow({
  label,
  value,
  highlight = false,
  warn = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  warn?: boolean;
}) {
  return (
    <div className="flex flex-col bg-white rounded-lg border border-slate-100 px-3 py-2">
      <span className="text-[10px] uppercase tracking-wider text-slate-400">{label}</span>
      <span
        className={
          "font-bold " +
          (warn ? "text-amber-600" : highlight ? "text-indigo-600" : "text-slate-700")
        }
      >
        {value}
      </span>
    </div>
  );
}

export default function WebcamTracker() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [status, setStatus] = useState("Initializing Edge AI...");
  const [score, setScore] = useState<string>("--");

  // Extended facial-feature telemetry coming back from the backend
  type Features = {
    eyebrows: string;
    lip_movement: boolean;
    yawning: boolean;
    smile: string;
    facial_tension: boolean;
    tension_score: number;
    mood: string;
    emotion_changed_at?: number;
    previous_mood?: string;
  };
  type EmotionEvent = { emotion: string; previous_emotion: string | null; timestamp: number };

  const [features, setFeatures] = useState<Features | null>(null);
  const [emotionHistory, setEmotionHistory] = useState<EmotionEvent[]>([]);

  useEffect(() => {
    let faceLandmarker: FaceLandmarker;
    let ws: WebSocket;
    let animationFrameId: number;

    const setupAI = async () => {
      setStatus("Downloading AI Model to Edge...");
      const vision = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
      );
      
      // Next.js intercepts console.error and blocks the screen.
      // MediaPipe logs its success message (XNNPACK) to console.error by mistake.
      // We temporarily mute it here to prevent the red screen of death!
      const originalError = console.error;
      console.error = (...args) => {
        if (typeof args[0] === 'string' && args[0].includes('XNNPACK')) return;
        originalError(...args);
      };
      
      faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
          delegate: "GPU"
        },
        outputFaceBlendshapes: true,
        outputFacialTransformationMatrixes: true,
        runningMode: "VIDEO",
        numFaces: 1
      });
      
      console.error = originalError; // Restore normal errors

      setStatus("Connecting to Backend Server...");
      const savedUserId = localStorage.getItem("focusai_user_id") || "user_1";
      ws = new WebSocket(`ws://localhost:8000/ws/user/${savedUserId}`);
      
      ws.onmessage = (event) => {
        // We receive data from backend but WE DO NOT SHOW IT in the User Portal for privacy!
      };

      ws.onopen = async () => {
        setStatus("Accessing Camera...");
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.onloadedmetadata = () => {
              setStatus("");
              videoRef.current?.play();
              predictLoop();
            };
          }
        } catch (e) {
          setStatus("Camera Access Denied.");
        }
      };
      
      ws.onerror = () => {
         setStatus("Backend Server is Offline. Start FastAPI.");
      }
    };

    let lastVideoTime = -1;
    
    const predictLoop = () => {
      if (
        videoRef.current && 
        videoRef.current.readyState >= 2 &&
        videoRef.current.currentTime !== lastVideoTime &&
        faceLandmarker
      ) {
        lastVideoTime = videoRef.current.currentTime;
        try {
          const results = faceLandmarker.detectForVideo(videoRef.current, performance.now());
          
          if (ws && ws.readyState === WebSocket.OPEN) {
            if (results.faceLandmarks.length > 0) {
              // Privacy Feature: Send ONLY numerical feature vectors to backend, NOT video!
              // We extract the 12 eye landmarks needed for EAR, the 4x4 pose matrix, and the 2 Iris centers.
              const rightEyeIndices = [33, 160, 158, 133, 153, 144];
              const leftEyeIndices = [362, 385, 387, 263, 373, 380];

              // Eyebrow indices, ordered outer -> inner (last point = closest to nose bridge,
              // matching what calculate_eyebrow_position / detect_facial_tension expect on the backend)
              const leftEyebrowIndices = [70, 63, 105, 66, 107];
              const rightEyebrowIndices = [336, 296, 334, 293, 300];

              // Mouth indices, ordered [left_corner, right_corner, top_outer, bottom_outer, top_inner, bottom_inner]
              const mouthIndices = [61, 291, 0, 17, 13, 14];
              
              const rawLandmarks = results.faceLandmarks[0];
              const payload = {
                right_eye: rightEyeIndices.map(i => rawLandmarks[i]),
                left_eye: leftEyeIndices.map(i => rawLandmarks[i]),
                left_eyebrow: leftEyebrowIndices.map(i => rawLandmarks[i]),
                right_eyebrow: rightEyebrowIndices.map(i => rawLandmarks[i]),
                mouth: mouthIndices.map(i => rawLandmarks[i]),
                irises: rawLandmarks.length > 470 ? [rawLandmarks[468], rawLandmarks[473]] : null,
                matrix: results.facialTransformationMatrixes?.[0] ? Array.from(results.facialTransformationMatrixes[0].data) : null
              };
              
              ws.send(JSON.stringify(payload));
            } else {
              ws.send(JSON.stringify({ no_face: true }));
            }
          }
        } catch (error) {
           console.warn("MediaPipe processing skipped a frame", error);
        }
      }
      animationFrameId = requestAnimationFrame(predictLoop);
    };

    setupAI();

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      if (ws) ws.close();
      if (faceLandmarker) faceLandmarker.close();
      if (videoRef.current?.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
        tracks.forEach(t => t.stop());
      }
    };
  }, []);

  return (
    <div className="flex flex-col items-center bg-white p-6 rounded-2xl shadow-xl border border-slate-100 max-w-2xl w-full">
      <div className="w-full flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-slate-800">Edge Tracker</h2>
        <span className="px-3 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded-full">
          Zero-Trust Privacy Mode
        </span>
      </div>
      
      <div className="relative w-full aspect-video bg-slate-900 rounded-xl overflow-hidden mb-6 shadow-inner">
        <video 
          ref={videoRef} 
          className="absolute inset-0 w-full h-full object-cover transform -scale-x-100 opacity-80" 
          playsInline
          muted
        />
        {status && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none bg-slate-900/40 backdrop-blur-sm">
            <div className="px-4 py-2 bg-slate-800 rounded-lg text-white font-mono text-sm shadow-lg border border-slate-700">
               {status}
            </div>
          </div>
        )}
      </div>

      <div className="w-full bg-slate-50 rounded-xl p-6 border border-slate-200 flex items-center justify-center gap-3">
        <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.8)]"></div>
        <p className="text-sm font-bold text-slate-700 uppercase tracking-wider">Secure Telemetry Active</p>
      </div>
      
      <p className="mt-4 text-xs text-slate-400 text-center">
        Video never leaves your device. Only highly-compressed feature vectors are streamed to the secure analysis server.
      </p>
    </div>
  );
}