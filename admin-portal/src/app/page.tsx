"use client";
import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";

export default function AdminDashboard() {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/telemetry");
        const json = await res.json();
        setData(json);
      } catch (e) {
        console.error("Failed to fetch telemetry:", e);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

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

  return (
    <div className="p-8 pb-20 min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">Super Admin Dashboard</h1>
          <p className="text-slate-500 font-medium mt-1">Multi-tenant Cognitive Telemetry Access</p>
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
      </div>
    </div>
  );
}
