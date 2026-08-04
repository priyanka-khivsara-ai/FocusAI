"use client";
import { useEffect, useState, useRef } from "react";
import ReactECharts from "echarts-for-react";
import { LayoutDashboard, Users, Activity, Bot, Upload, LogOut, FileText, CheckCircle } from "lucide-react";
import { useRouter } from "next/navigation";

export default function AdminDashboard() {
  const router = useRouter();
  const [role, setRole] = useState("Admin");
  const [activeTab, setActiveTab] = useState("monitoring");
  
  // Data States
  const [activeSessionId, setActiveSessionId] = useState("");
  const [data, setData] = useState([]);
  const [latestData, setLatestData] = useState([]);
  const [selectedUser, setSelectedUser] = useState("all");
  
  // Chat Agent State
  const [query, setQuery] = useState("");
  const [chatLog, setChatLog] = useState<{role: string, content: string}[]>([]);
  const [loading, setLoading] = useState(false);

  // Bulk Upload State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadRole, setUploadRole] = useState("User");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [registeredUsers, setRegisteredUsers] = useState<any[]>([]);

  useEffect(() => {
    const savedRole = localStorage.getItem("focusai_role");
    if (!savedRole) {
      router.push("/");
      return;
    }
    
    setRole(savedRole);
    if (savedRole === "Host") {
      setActiveTab("monitoring");
    } else {
      setActiveTab("analytics");
    }
  }, [router]);

  // Polling for Timeseries Charts (Admin only)
  useEffect(() => {
    if (role !== "Admin" || activeTab !== "analytics") return;
    const fetchData = async () => {
      if (!activeSessionId) return;
      try {
        const res = await fetch(`http://${window.location.hostname}:8000/api/telemetry?session_id=${activeSessionId}&user_id=${selectedUser}`);
        const json = await res.json();
        setData(json);
      } catch (e) {
        console.error("Failed to fetch telemetry:", e);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [role, activeTab, selectedUser, activeSessionId]);

  // Polling for Live Monitoring Table
  useEffect(() => {
    if (activeTab !== "monitoring" || !activeSessionId) return;
    const fetchLatest = async () => {
      try {
        const res = await fetch(`http://${window.location.hostname}:8000/api/telemetry/latest?session_id=${activeSessionId}`);
        const json = await res.json();
        setLatestData(json);
      } catch (e) {
        console.error("Failed to fetch latest telemetry:", e);
      }
    };
    fetchLatest();
    const interval = setInterval(fetchLatest, 1000);
    return () => clearInterval(interval);
  }, [activeTab, activeSessionId]);

  // Fetch Registered Users
  useEffect(() => {
    if (activeTab !== "users") return;
    const fetchUsers = async () => {
      try {
        const res = await fetch(`http://${window.location.hostname}:8000/api/users/list`);
        const json = await res.json();
        setRegisteredUsers(json.users || []);
      } catch (e) {
        console.error("Failed to fetch users:", e);
      }
    };
    fetchUsers();
  }, [activeTab]);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !activeSessionId) return;
    
    const userMessage = query;
    setChatLog(prev => [...prev, { role: "user", content: userMessage }]);
    setQuery("");
    setLoading(true);
    
    try {
      const res = await fetch(`http://${window.location.hostname}:8000/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, user_id: selectedUser, session_id: activeSessionId })
      });
      const json = await res.json();
      setChatLog(prev => [...prev, { role: "agent", content: json.response }]);
    } catch (err) {
      setChatLog(prev => [...prev, { role: "agent", content: "Error: Could not connect to AI Agent." }]);
    }
    
    setLoading(false);
  };

  const handleBulkUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("role_name", uploadRole);

    try {
      const res = await fetch(`http://${window.location.hostname}:8000/api/users/bulk-upload`, {
        method: "POST",
        body: formData
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || "Upload failed");
      setUploadResult(json);
    } catch (err: any) {
      alert("Error: " + err.message);
    }
    setUploading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("focusai_role");
    localStorage.removeItem("focusai_token");
    router.push("/");
  };

  const handleCreateMeeting = async () => {
    try {
      const res = await fetch(`http://${window.location.hostname}:8000/api/sessions/create`, { method: "POST" });
      const data = await res.json();
      setActiveSessionId(data.session_id);
      alert(`✅ Created Meeting: ${data.session_id}\n\nShare this link with students:\nhttp://${window.location.hostname}:3000/user?code=${data.session_id}`);
    } catch (e) {
      alert("Error creating meeting");
    }
  };

  // --- ECharts Options ---
  const times = data.map((d: any) => new Date(d.timestamp).toLocaleTimeString());
  const scores = data.map((d: any) => d.focus_score);
  
  const scoreOption = {
    tooltip: { trigger: "axis", backgroundColor: "rgba(15, 23, 42, 0.9)", textStyle: {color: '#fff'}, borderColor: "transparent" },
    grid: { left: "3%", right: "3%", bottom: "5%", top: "10%", containLabel: true },
    xAxis: { type: "category", data: times, boundaryGap: false, axisLine: { lineStyle: { color: "#e2e8f0" } }, axisLabel: { color: "#64748b" } },
    yAxis: { type: "value", max: 100, min: 0, splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } }, axisLabel: { color: "#64748b" } },
    series: [{
      name: "Focus Score", data: scores, type: "line", smooth: true, showSymbol: false,
      lineStyle: { color: "#3b82f6", width: 3 },
      areaStyle: {
        color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: "rgba(59, 130, 246, 0.2)" }, { offset: 1, color: "rgba(59, 130, 246, 0)" }] }
      }
    }]
  };

  const moodCounts = data.reduce((acc: any, curr: any) => {
    acc[curr.mood] = (acc[curr.mood] || 0) + 1;
    return acc;
  }, {});
  
  const moodOption = {
    tooltip: { trigger: "item", backgroundColor: "rgba(15, 23, 42, 0.9)", textStyle: {color: '#fff'} },
    legend: { bottom: "0%", left: "center", itemStyle: {borderWidth: 0} },
    series: [{
      type: "pie", radius: ["50%", "70%"], avoidLabelOverlap: false,
      itemStyle: { borderRadius: 8, borderColor: "#fff", borderWidth: 2 },
      label: { show: false },
      data: Object.keys(moodCounts).length > 0 ? Object.keys(moodCounts).map(k => ({name: k, value: moodCounts[k]})) : [{ name: "No Data", value: 1 }],
      color: ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
    }]
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-900">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col shadow-2xl z-10">
        <div className="p-6 border-b border-slate-800">
          <h1 className="text-2xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            FocusAI
          </h1>
          <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest">{role} Portal</p>
        </div>

        <div className="p-4 border-b border-slate-800">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Meeting Code</label>
          <input 
            type="text"
            placeholder="e.g. AI-101"
            value={activeSessionId}
            onChange={(e) => setActiveSessionId(e.target.value.toUpperCase())}
            className="w-full bg-slate-800 border border-slate-700 text-white font-semibold py-2 px-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all uppercase mb-3"
          />
          <button 
            onClick={handleCreateMeeting}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-xl transition-all shadow-md text-sm"
          >
            + Create New Meeting
          </button>
        </div>
        
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {role === "Admin" && (
            <button onClick={() => setActiveTab("analytics")} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'analytics' ? 'bg-blue-600 shadow-lg shadow-blue-900/50 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>
              <LayoutDashboard size={18} />
              <span className="font-semibold text-sm">Analytics</span>
            </button>
          )}
          
          <button onClick={() => setActiveTab("monitoring")} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'monitoring' ? 'bg-blue-600 shadow-lg shadow-blue-900/50 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>
            <Activity size={18} />
            <span className="font-semibold text-sm">Live Monitoring</span>
          </button>
          
          {role === "Admin" && (
            <>
              <button onClick={() => setActiveTab("agent")} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'agent' ? 'bg-blue-600 shadow-lg shadow-blue-900/50 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>
                <Bot size={18} />
                <span className="font-semibold text-sm">AI Analyst</span>
              </button>
              
              <button onClick={() => setActiveTab("users")} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'users' ? 'bg-blue-600 shadow-lg shadow-blue-900/50 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>
                <Users size={18} />
                <span className="font-semibold text-sm">User Provisioning</span>
              </button>
            </>
          )}
        </nav>
        
        <div className="p-4 border-t border-slate-800">
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-all">
            <LogOut size={18} />
            <span className="font-semibold text-sm">Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-8 relative">
        <div className="max-w-6xl mx-auto space-y-8">
          
          {/* Header */}
          <header className="flex justify-between items-end pb-6 border-b border-slate-200">
            <div>
              <h2 className="text-3xl font-black tracking-tight text-slate-800 capitalize">
                {activeTab.replace("-", " ")}
              </h2>
              <p className="text-slate-500 font-medium mt-1">
                {activeTab === 'analytics' && "System-wide cognitive insights and trends."}
                {activeTab === 'monitoring' && "Real-time biometric telemetry stream."}
                {activeTab === 'agent' && "Chat with the LangGraph RAG Assistant."}
                {activeTab === 'users' && "Bulk upload and manage user access."}
              </p>
            </div>
            
            {(activeTab === 'analytics' || activeTab === 'agent') && (
               <select 
                 value={selectedUser}
                 onChange={(e) => setSelectedUser(e.target.value)}
                 className="bg-white border-2 border-slate-200 text-slate-700 font-bold py-2.5 px-4 rounded-xl focus:outline-none focus:border-blue-500 shadow-sm outline-none transition-colors"
               >
                 <option value="all">System Average</option>
                 <option value="user1">User: user1</option>
                 <option value="user2">User: user2</option>
               </select>
            )}
          </header>

          {/* Tab Contents */}
          {activeTab === "analytics" && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
                <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse"></span>
                  Focus Trend
                </h3>
                {data.length > 0 ? (
                  <ReactECharts option={scoreOption} style={{ height: "350px", width: "100%" }} />
                ) : (
                  <div className="h-[350px] flex items-center justify-center text-slate-400 bg-slate-50 rounded-2xl border border-dashed border-slate-200">Awaiting telemetry data...</div>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                 <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100">
                    <h3 className="font-bold text-slate-800 mb-4">Mood Distribution</h3>
                    <ReactECharts option={moodOption} style={{ height: "250px", width: "100%" }} />
                 </div>
              </div>
            </div>
          )}

          {activeTab === "monitoring" && (
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100 text-xs uppercase tracking-widest text-slate-500">
                      <th className="p-4 font-bold pl-6">User ID</th>
                      <th className="p-4 font-bold">Status</th>
                      <th className="p-4 font-bold">Focus</th>
                      <th className="p-4 font-bold">Mood</th>
                      <th className="p-4 font-bold">Tense</th>
                      <th className="p-4 font-bold">Eyebrows</th>
                      <th className="p-4 font-bold">Yawning</th>
                      <th className="p-4 font-bold">Speaking/Lips</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {latestData.length === 0 ? (
                       <tr><td colSpan={8} className="p-12 text-center text-slate-400 bg-slate-50/50">No active streams.</td></tr>
                    ) : (
                      latestData.map((row: any, i) => (
                        <tr key={i} className="hover:bg-slate-50 transition-colors group">
                          <td className="p-4 pl-6 font-bold flex items-center gap-3 text-slate-700">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 group-hover:animate-ping"></span>
                            {row.user_id}
                          </td>
                          <td className="p-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold ${row.status === 'Attentive' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                              {row.status}
                            </span>
                          </td>
                          <td className="p-4 font-black text-slate-800">{row.focus_score}%</td>
                          <td className="p-4 font-medium text-slate-600">{row.mood}</td>
                          <td className="p-4">
                            {row.is_tense ? <span className="bg-amber-100 text-amber-700 px-2 py-1 rounded-md text-xs font-bold">Yes</span> : <span className="text-slate-400 text-sm">No</span>}
                          </td>
                          <td className="p-4 text-slate-600 font-medium">
                            {row.eyebrows}
                          </td>
                          <td className="p-4">
                            {row.yawning ? <span className="bg-rose-100 text-rose-700 px-2 py-1 rounded-md text-xs font-bold">Yes</span> : <span className="text-slate-400 text-sm">No</span>}
                          </td>
                          <td className="p-4">
                            {row.lip_movement ? <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded-md text-xs font-bold">Moving</span> : <span className="text-slate-400 text-sm">Still</span>}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "agent" && (
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-6 flex flex-col h-[600px] animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
                {chatLog.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-50">
                    <Bot size={48} className="mb-4" />
                    <p>Ask about engagement trends, focus drops, or cognitive stats.</p>
                  </div>
                ) : (
                  chatLog.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] rounded-2xl px-5 py-3 text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-500/20' : 'bg-slate-100 text-slate-800 rounded-bl-none'}`}>
                        {msg.content}
                      </div>
                    </div>
                  ))
                )}
                {loading && (
                   <div className="flex justify-start">
                      <div className="bg-slate-100 text-slate-500 rounded-2xl rounded-bl-none px-5 py-3 text-sm flex gap-1">
                        <span className="animate-bounce">.</span><span className="animate-bounce delay-75">.</span><span className="animate-bounce delay-150">.</span>
                      </div>
                   </div>
                )}
              </div>
              <form onSubmit={handleChatSubmit} className="relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Query the TimescaleDB..."
                  className="w-full bg-slate-50 border-2 border-slate-200 rounded-2xl pl-5 pr-14 py-4 focus:outline-none focus:border-blue-500 focus:bg-white transition-all text-slate-700 font-medium"
                />
                <button type="submit" disabled={loading || !query.trim()} className="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-xl transition-colors disabled:opacity-50">
                  <Bot size={20} />
                </button>
              </form>
            </div>
          )}

          {activeTab === "users" && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
              
              <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-8">
                <div className="max-w-2xl mx-auto">
                  <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <Upload className="text-blue-600" size={32} />
                    </div>
                    <h3 className="text-2xl font-black text-slate-800">Bulk Provisioning</h3>
                    <p className="text-slate-500 mt-2">Upload an Excel (.xlsx), CSV, or PDF file to automatically extract names and emails and generate secure credentials.</p>
                  </div>
                  
                  <form onSubmit={handleBulkUpload} className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <label className={`border-2 rounded-2xl p-4 cursor-pointer transition-all ${uploadRole === 'User' ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}`}>
                        <input type="radio" name="role" value="User" checked={uploadRole === 'User'} onChange={() => setUploadRole("User")} className="hidden" />
                        <div className="font-bold text-slate-800">User Role</div>
                        <div className="text-xs text-slate-500 mt-1">Standard tracking participant</div>
                      </label>
                      <label className={`border-2 rounded-2xl p-4 cursor-pointer transition-all ${uploadRole === 'Host' ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}`}>
                        <input type="radio" name="role" value="Host" checked={uploadRole === 'Host'} onChange={() => setUploadRole("Host")} className="hidden" />
                        <div className="font-bold text-slate-800">Host Role</div>
                        <div className="text-xs text-slate-500 mt-1">Access to live monitoring</div>
                      </label>
                    </div>

                    <div className="border-2 border-dashed border-slate-300 rounded-3xl p-10 text-center hover:bg-slate-50 transition-colors relative">
                      <input 
                        type="file" 
                        accept=".xlsx,.xls,.csv,.pdf" 
                        onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                      />
                      <FileText size={48} className="mx-auto text-slate-300 mb-4" />
                      <p className="font-bold text-slate-700 text-lg">
                        {uploadFile ? uploadFile.name : "Drag & drop file or click to browse"}
                      </p>
                      <p className="text-sm text-slate-400 mt-1">Supports Excel, CSV, and PDF formats.</p>
                    </div>

                    <button 
                      type="submit" 
                      disabled={!uploadFile || uploading}
                      className="w-full py-4 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-2xl transition-all shadow-xl shadow-slate-900/20 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                      {uploading ? <span className="animate-pulse">Processing Upload...</span> : "Generate Credentials"}
                    </button>
                  </form>
                </div>
              </div>

              {/* Results Table */}
              {uploadResult && uploadResult.users && (
                <div className="bg-emerald-50 rounded-3xl border border-emerald-200 p-8 animate-in fade-in slide-in-from-top-4">
                  <div className="flex items-center gap-3 mb-6">
                    <CheckCircle className="text-emerald-600" size={28} />
                    <h3 className="text-xl font-black text-emerald-900">{uploadResult.message}</h3>
                  </div>
                  
                  <div className="bg-white rounded-2xl overflow-hidden border border-emerald-100">
                    <table className="w-full text-left border-collapse text-sm">
                      <thead className="bg-emerald-50/50 text-emerald-800 font-bold">
                        <tr>
                          <th className="p-4 border-b border-emerald-100 pl-6">Username</th>
                          <th className="p-4 border-b border-emerald-100">Email</th>
                          <th className="p-4 border-b border-emerald-100">Generated Password</th>
                          <th className="p-4 border-b border-emerald-100">Role</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-emerald-50">
                        {uploadResult.users.map((u: any, i: number) => (
                          <tr key={i} className="hover:bg-emerald-50/30">
                            <td className="p-4 pl-6 font-semibold text-slate-700">{u.username}</td>
                            <td className="p-4 text-slate-600">{u.email}</td>
                            <td className="p-4 font-mono text-emerald-600 font-bold bg-emerald-50/50 rounded inline-block my-2 ml-4 px-2">{u.password}</td>
                            <td className="p-4"><span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded font-bold text-xs">{u.role}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-emerald-700 text-sm mt-4 font-medium flex justify-end">
                    Please copy or download these credentials now, they cannot be retrieved later.
                  </p>
                </div>
              )}

              {/* Registered Users Table */}
              <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-8 mt-8">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-black text-slate-800">All Registered Users</h3>
                  <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-bold text-sm">{registeredUsers.length} Users</span>
                </div>
                
                <div className="overflow-x-auto rounded-2xl border border-slate-100">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead className="bg-slate-50 text-slate-500 uppercase tracking-widest text-xs">
                      <tr>
                        <th className="p-4 font-bold pl-6 border-b border-slate-100">Username</th>
                        <th className="p-4 font-bold border-b border-slate-100">Email</th>
                        <th className="p-4 font-bold border-b border-slate-100">Password</th>
                        <th className="p-4 font-bold border-b border-slate-100">Role</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {registeredUsers.length === 0 ? (
                        <tr><td colSpan={4} className="p-12 text-center text-slate-400">No users found.</td></tr>
                      ) : (
                        registeredUsers.map((u: any, i: number) => (
                          <tr key={i} className="hover:bg-slate-50 transition-colors">
                            <td className="p-4 pl-6 font-bold text-slate-700">{u.username}</td>
                            <td className="p-4 text-slate-500 font-medium">{u.email}</td>
                            <td className="p-4 font-mono text-slate-500 bg-slate-100 rounded px-2 py-1 my-2 inline-block text-xs">{u.password || "Hidden"}</td>
                            <td className="p-4">
                              <span className={`px-2 py-1 rounded font-bold text-xs ${u.role === 'Admin' ? 'bg-amber-100 text-amber-700' : u.role === 'Host' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'}`}>
                                {u.role}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}
        </div>
      </main>
    </div>
  );
}
