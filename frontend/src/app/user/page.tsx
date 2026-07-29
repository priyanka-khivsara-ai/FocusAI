import WebcamTracker from "@/components/WebcamTracker";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center py-12 px-4 bg-slate-100">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-black text-slate-900 mb-2">FocusAI <span className="text-emerald-600">Secure Node</span></h1>
        <p className="text-slate-500 font-medium">Real-time Privacy-First Engagement Tracking</p>
      </div>
      <WebcamTracker />
    </main>
  );
}
