"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginScreen() {
  const [role, setRole] = useState("User");
  const [userId, setUserId] = useState("user_1");
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Store user ID in localStorage for the tracker to pick up
    localStorage.setItem("focusai_user_id", role === "Super Admin" ? "all" : userId);
    // Store role so Dashboards can route features appropriately
    localStorage.setItem("focusai_role", role);
    
    if (role === "User") {
      router.push("/user");
    } else {
      router.push("/admin");
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl shadow-2xl max-w-md w-full border border-slate-100">
        <h1 className="text-3xl font-black text-slate-900 text-center tracking-tight mb-2">FocusAI Portal</h1>
        <p className="text-slate-500 text-center font-medium mb-8">Unified Cognitive Intelligence</p>
        
        <form onSubmit={handleLogin} className="space-y-5">
          <div className="flex flex-col">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Select Your Role</label>
            <select 
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-slate-700 font-semibold py-3 px-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            >
              <option value="User">Student / User</option>
              <option value="Admin">Administrator</option>
              <option value="Super Admin">Super Administrator</option>
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">User ID</label>
            <input 
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              disabled={role === "Super Admin"}
              className="bg-slate-50 border border-slate-200 text-slate-700 font-semibold py-3 px-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all disabled:opacity-50"
            />
            {role === "Super Admin" && <span className="text-xs text-slate-400 mt-2">Super Admins have global system access.</span>}
          </div>

          <button 
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl transition-colors mt-4 shadow-lg shadow-blue-600/30"
          >
            Authenticate
          </button>
        </form>
      </div>
    </div>
  );
}
