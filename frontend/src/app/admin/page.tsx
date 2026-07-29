"use client";
import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";

export default function AdminDashboard() {
  const [role, setRole] = useState("Super Admin");
  const [data, setData] = useState([]);
  const [latestData, setLatestData] = useState([]);
  
  // Multi-Tenant State
  const [selectedUser, setSelectedUser] = useState("all");
  
  // Chat Agent State
  const [query, setQuery] = useState("");
  const [chatLog, setChatLog] = useState<{role: string, content: string}[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const savedRole = localStorage.getItem("focusai_role") || "Super Admin";
    setRole(savedRole);
  }, []);

  // --- SUPER ADMIN: Polling for Timeseries Charts ---
  useEffect(() => {
    if (role !== "Super Admin") return;
    const fetchData = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/telemetry?user_id=${selectedUser}`);
        const json = await res.json();
        setData(json);
      } catch (e) {
        console.error("Failed to fetch telemetry:", e);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [role, selectedUser]);

  // --- ADMIN: Polling for Real-Time Monitoring Table ---
  useEffect(() => {
    if (role !== "Admin") return;
    const fetchLatest = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/telemetry/latest`);
        const json = await res.json();
        setLatestData(json);
      } catch (e) {
        console.error("Failed to fetch latest telemetry:", e);
      }
    };
    
    fetchLatest();
    const interval = setInterval(fetchLatest, 1000);
    return () => clearInterval(interval);
  }, [role]);

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    const userMessage = query;
    setChatLog(prev => [...prev, { role: "user", content: userMessage }]);
    setQuery("");
    setLoading(true);
    
    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, user_id: selectedUser })
      });
      const json = await res.json();
      setChatLog(prev => [...prev, { role: "agent", content: json.response }]);
    } catch (err) {
      setChatLog(prev => [...prev, { role: "agent", content: "Error: Could not connect to AI Agent." }]);
    }
    
    setLoading(false);
  };

  const times = data.map((d: any) => new Date(d.timestamp).toLocaleTimeString());
  const scores = data.map((d: any) => d.focus_score);
  
  const scoreOption = {
    tooltip: { trigger: "axis", backgroundColor: "rgba(255, 255, 255, 0.95)", borderColor: "#e2e8f0" },
    grid: { left: "5%", right: "5%", bottom: "10%", top: "10%" },
    xAxis: { type: "category", data: times, boundaryGap: false, axisLine: { lineStyle: { color: "#cbd5e1" } }, axisLabel: { color: "#64748b" } },
    yAxis: { type: "value", max: 100, min: 0, splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } }, axisLabel: { color: "#64748b" } },
    series: [{
      name: "Focus Score",
      data: scores,
      type: "line",
      smooth: true,
      showSymbol: false,
      lineStyle: { color: "#059669", width: 4 },
      areaStyle: {
        color: {
          type: "linear", x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: "rgba(5, 150, 105, 0.4)" }, { offset: 1, color: "rgba(5, 150, 105, 0.0)" }]
        }
      }
    }]
  };
  
  const tensions = data.map((d: any) => d.is_tense ? 1 : 0);
  const tensionOption = {
    tooltip: { trigger: "axis", formatter: (params: any) => `${params[0].name}<br/>Tension Spike: ${params[0].value === 1 ? 'Yes' : 'No'}` },
    grid: { left: "5%", right: "5%", bottom: "10%", top: "10%" },
    xAxis: { type: "category", data: times, show: false },
    yAxis: { type: "value", max: 1, min: 0, show: false },
    series: [{
      name: "Tension Spikes",
      data: tensions,
      type: "bar",
      barWidth: "40%",
      itemStyle: { color: "#ef4444", borderRadius: [4, 4, 0, 0] },
    }]
  };

  const moodCounts = data.reduce((acc: any, curr: any) => {
    acc[curr.mood] = (acc[curr.mood] || 0) + 1;
    return acc;
  }, {});
  
  const moodData = Object.keys(moodCounts).map(key => ({
    name: key,
    value: moodCounts[key]
  }));

  const moodOption = {
    tooltip: { trigger: "item" },
    legend: { bottom: "0%", left: "center" },
    series: [
      {
        name: "Mood Distribution",
        type: "pie",
        radius: ["40%", "70%"],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: "#fff", borderWidth: 2 },
        label: { show: false, position: "center" },
        emphasis: { label: { show: true, fontSize: 20, fontWeight: "bold" } },
        labelLine: { show: false },
        data: moodData.length > 0 ? moodData : [{ name: "No Data", value: 1 }],
        color: ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
      }
    ]
  };

  // --- ADMIN VIEW (Monitoring Table) ---
  if (role === "Admin") {
    return (
      <div className="p-8 min-h-screen bg-slate-50">
        <div className="max-w-7xl mx-auto space-y-8">
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight">Admin Live Monitoring</h1>
            <p className="text-slate-500 font-medium mt-1">Real-time facial states and cognitive focus across all students.</p>
          </div>
          
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">User ID</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Focus Score</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Mood / Smile</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Eyebrows</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Yawning</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Talking</th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Tense</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {latestData.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-6 py-12 text-center text-slate-400 font-medium">Waiting for students to connect...</td>
                  </tr>
                )}
                {latestData.map((row: any, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-900 flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                      {row.user_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">
                      <span className={`px-3 py-1 rounded-full text-xs ${row.status === 'Attentive' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-black text-slate-700">{row.focus_score}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-600">{row.mood}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{row.eyebrows || 'Neutral'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {row.yawning ? <span className="text-rose-600 font-bold bg-rose-50 px-2 py-1 rounded">Yes</span> : <span className="text-slate-400">No</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {row.lip_movement ? <span className="text-blue-600 font-bold bg-blue-50 px-2 py-1 rounded">Active</span> : <span className="text-slate-400">Still</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {row.is_tense ? <span className="text-amber-600 font-bold bg-amber-50 px-2 py-1 rounded">Tense</span> : <span className="text-slate-400">Relaxed</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // --- SUPER ADMIN VIEW (ECharts Dashboard) ---
  return (
    <div className="p-8 pb-20 min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight">Super Admin Dashboard</h1>
            <p className="text-slate-500 font-medium mt-1">Multi-tenant Cognitive Telemetry Access</p>
          </div>
          
          <div className="flex flex-col">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">View Telemetry For:</label>
            <select 
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="bg-white border border-slate-300 text-slate-700 font-semibold py-2 px-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
            >
              <option value="all">Super Admin (System Average)</option>
              <option value="user_1">User 1</option>
            </select>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
           <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
             <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
             Real-Time Focus Trend
           </h2>
           {data.length > 0 ? (
             <ReactECharts option={scoreOption} style={{ height: "400px", width: "100%" }} />
           ) : (
             <div className="h-[400px] flex items-center justify-center text-slate-400 font-medium">Waiting for data...</div>
           )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 mb-2">Facial Tension Spikes</h2>
              <p className="text-sm text-slate-500 mb-6">Frequency of brow furrowing and lip compression.</p>
              <ReactECharts option={tensionOption} style={{ height: "250px", width: "100%" }} />
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 mb-2">Mood Distribution</h2>
              <p className="text-sm text-slate-500 mb-6">Breakdown of cognitive emotional states.</p>
              <ReactECharts option={moodOption} style={{ height: "250px", width: "100%" }} />
            </div>
        </div>

        {/* Autonomous Agent Chat Interface */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mt-8">
           <h2 className="text-xl font-bold text-slate-800 mb-2 flex items-center gap-2">
             <span className="w-4 h-4 rounded-full bg-blue-500"></span>
             Agentic AI Analyst (RAG)
           </h2>
           <p className="text-sm text-slate-500 mb-6">Ask the Autonomous Agent questions about the TimescaleDB telemetry data.</p>
           
           <div className="bg-slate-50 rounded-xl p-4 h-64 overflow-y-auto mb-4 border border-slate-100 flex flex-col gap-3">
              {chatLog.length === 0 ? (
                <div className="text-slate-400 text-sm text-center mt-auto mb-auto">Try asking: "Did the user get distracted in the last 5 minutes?"</div>
              ) : (
                chatLog.map((msg, idx) => (
                  <div key={idx} className={`p-3 rounded-lg max-w-[80%] text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white self-end rounded-br-none' : 'bg-white text-slate-800 border border-slate-200 self-start rounded-bl-none shadow-sm'}`}>
                    <span className="font-bold block mb-1 text-xs opacity-75">{msg.role === 'user' ? 'Admin' : 'AI Agent'}</span>
                    {msg.content}
                  </div>
                ))
              )}
              {loading && <div className="text-slate-400 text-sm animate-pulse">Agent is thinking and querying TimescaleDB...</div>}
           </div>

           <form onSubmit={handleChatSubmit} className="flex gap-2">
             <input
               type="text"
               value={query}
               onChange={(e) => setQuery(e.target.value)}
               placeholder="Ask the AI about the cognitive data..."
               className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
               disabled={loading}
             />
             <button
               type="submit"
               disabled={loading}
               className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors disabled:opacity-50"
             >
               Send
             </button>
           </form>
        </div>
      </div>
    </div>
  );
}
