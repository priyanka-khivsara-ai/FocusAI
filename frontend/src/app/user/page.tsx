"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import WebcamTracker from "@/components/WebcamTracker";
import { Suspense } from "react";

function UserPortalContent() {
  const searchParams = useSearchParams();
  const [meetingCode, setMeetingCode] = useState("");
  const [joined, setJoined] = useState(false);

  useEffect(() => {
    const code = searchParams.get("code");
    if (code) {
      setMeetingCode(code);
      setJoined(true);
    }
  }, [searchParams]);

  const handleJoin = (e: React.FormEvent) => {
    e.preventDefault();
    if (meetingCode.trim()) {
      setJoined(true);
    }
  };

  if (joined && meetingCode) {
    return (
      <main className="flex min-h-screen flex-col items-center py-12 px-4 bg-slate-100">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-black text-slate-900 mb-2">
            FocusAI <span className="text-emerald-600">Secure Node</span>
          </h1>
          <p className="text-slate-500 font-medium">Room: {meetingCode.toUpperCase()}</p>
        </div>
        <WebcamTracker sessionId={meetingCode.toUpperCase()} />
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center py-12 px-4 bg-slate-100">
      <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full border border-slate-200">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-black text-slate-900 mb-2">Join Meeting</h1>
          <p className="text-slate-500 font-medium">Enter your session code to connect</p>
        </div>
        
        <form onSubmit={handleJoin} className="space-y-6">
          <div className="flex flex-col">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Meeting Code</label>
            <input 
              type="text"
              value={meetingCode}
              onChange={(e) => setMeetingCode(e.target.value)}
              placeholder="e.g. AI-101"
              className="bg-slate-50 border border-slate-200 text-slate-700 font-semibold py-3 px-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all uppercase"
              required
            />
          </div>
          <button 
            type="submit"
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-6 rounded-xl transition-colors shadow-lg shadow-emerald-600/30"
          >
            Connect to Session
          </button>
        </form>
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-100 flex items-center justify-center">Loading...</div>}>
      <UserPortalContent />
    </Suspense>
  );
}
