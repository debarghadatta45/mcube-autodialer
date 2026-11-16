"use client";

import React, { useState } from "react";
import Image from "next/image";
import {
  PhoneCall,
  CheckCircle2,
  AlertTriangle,
  Download,
  Users,
  ShieldCheck,
  Send,
  ExternalLink,
  Laptop,
  Apple,
  TrendingUp,
  Award,
  Sparkles,
  Bug,
  Mail,
  Phone
} from "lucide-react";

function LinkedInIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.25c-.96 0-1.74.78-1.74 1.74s.78 1.74 1.74 1.74 1.74-.78 1.74-1.74-.78-1.74-1.74-1.74Z" />
    </svg>
  );
}

export default function Home() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    role: "Academic Counselor / Sales",
    os: "Windows"
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
  const [isRegistered, setIsRegistered] = useState(false);
  const [registeredUser, setRegisteredUser] = useState<any>(null);
  const [selectedOS, setSelectedOS] = useState<"Windows" | "macOS">("Windows");

  // Bug report state
  const [bugData, setBugData] = useState({
    name: "",
    email: "",
    category: "LeadSquared CRM Lag",
    message: ""
  });
  const [bugLoading, setBugLoading] = useState(false);
  const [bugMessage, setBugMessage] = useState<string | null>(null);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    const emailTrimmed = formData.email.trim().toLowerCase();
    const isAuthorized = emailTrimmed.endsWith("@vedantu.com") || emailTrimmed === "dadeb349@gmail.com";
    if (!isAuthorized) {
      setMessage({
        text: "Access restricted: Only official @vedantu.com email IDs are permitted.",
        type: "error"
      });
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...formData, email: emailTrimmed })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Registration failed");
      }

      setMessage({ text: data.message, type: "success" });
      setIsRegistered(true);
      setRegisteredUser(data.user);
      if (formData.os) {
        setSelectedOS(formData.os as "Windows" | "macOS");
      }
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleBugSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBugLoading(true);
    setBugMessage(null);

    try {
      const res = await fetch("/api/report-bug", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bugData)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to submit report");

      setBugMessage(data.message);
      setBugData({ name: "", email: "", category: "LeadSquared CRM Lag", message: "" });
    } catch (err: any) {
      setBugMessage("Could not submit: " + err.message);
    } finally {
      setBugLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-orange-500 selection:text-white font-sans antialiased">
      {/* Background Glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[500px] bg-orange-600/15 blur-[140px] rounded-full" />
        <div className="absolute top-[40%] -left-32 w-[500px] h-[500px] bg-blue-600/10 blur-[130px] rounded-full" />
        <div className="absolute bottom-10 right-0 w-[550px] h-[500px] bg-emerald-600/10 blur-[140px] rounded-full" />
      </div>

      {/* Top Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-orange-600 to-amber-500 flex items-center justify-center font-bold text-white shadow-lg shadow-orange-500/20">
              <PhoneCall className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight text-white flex items-center gap-2">
                MCUBE Auto-Dialer
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-400 font-semibold border border-orange-500/30">
                  Vedantu Internal
                </span>
              </span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
            <a href="#story" className="hover:text-orange-400 transition">
              The Story
            </a>
            <a href="#proof" className="hover:text-orange-400 transition">
              Calling Proof
            </a>
            <a href="#download" className="hover:text-orange-400 transition">
              Download App
            </a>
            <a href="#contact" className="hover:text-orange-400 transition">
              Contact & Bugs
            </a>
          </nav>

          <a
            href="#download"
            className="text-xs md:text-sm px-4 py-2 rounded-lg bg-orange-500 hover:bg-orange-600 font-semibold text-white transition shadow-md shadow-orange-500/25 flex items-center gap-1.5"
          >
            <Download className="w-4 h-4" /> Get App
          </a>
        </div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 max-w-6xl mx-auto px-4 py-12 md:py-16 space-y-20">
        {/* HERO SECTION */}
        <section className="text-center space-y-6 pt-4">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/70 text-xs font-medium text-slate-300 backdrop-blur">
            <Sparkles className="w-4 h-4 text-orange-400" />
            Empowering 200+ Daily Connects for Vedantu Sales
          </div>

          <h1 className="text-4xl md:text-6xl font-black tracking-tight text-white max-w-4xl mx-auto leading-tight">
            From <span className="text-red-400 line-through">35 Calls</span> to{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-amber-300 to-emerald-400">
              278+ Dials Daily.
            </span>
          </h1>

          <p className="text-lg md:text-xl text-slate-300 max-w-3xl mx-auto font-normal leading-relaxed">
            Engineered by <span className="text-white font-semibold underline decoration-orange-400">Debargha Datta</span> —
            solving CRM lag, MCUBE WebRTC non-presence errors, and eliminating 5 manual clicks per lead for the entire sales team.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <a
              href="#download"
              className="px-6 py-3.5 rounded-xl bg-orange-500 hover:bg-orange-600 font-bold text-white shadow-lg shadow-orange-500/30 transition flex items-center gap-2 text-base"
            >
              <Download className="w-5 h-5" /> Download for Windows & macOS
            </a>
            <a
              href="#proof"
              className="px-6 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 font-medium text-slate-200 border border-slate-700 transition flex items-center gap-2 text-base"
            >
              <TrendingUp className="w-5 h-5 text-emerald-400" /> View Calling Metrics
            </a>
          </div>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto pt-8">
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur text-center">
              <div className="text-2xl md:text-3xl font-black text-white">278</div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mt-1">Single Day Peak</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur text-center">
              <div className="text-2xl md:text-3xl font-black text-emerald-400">89</div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mt-1">Connected Calls / Day</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur text-center">
              <div className="text-2xl md:text-3xl font-black text-amber-400">1,055+</div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mt-1">4-Day Total Calls</div>
            </div>
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur text-center">
              <div className="text-2xl md:text-3xl font-black text-cyan-400">0 Clicks</div>
              <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold mt-1">100% Automated Dialing</div>
            </div>
          </div>
        </section>

        {/* SECTION: THE STORY & PROBLEM STATEMENT */}
        <section id="story" className="scroll-mt-24 space-y-6">
          <div className="p-8 md:p-10 rounded-3xl bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-slate-950 border border-slate-800 relative overflow-hidden shadow-2xl">
            <div className="absolute -top-12 -right-12 w-48 h-48 bg-orange-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="flex items-center gap-3 text-orange-400 font-bold text-sm tracking-wide uppercase mb-3">
              <Award className="w-5 h-5" /> The Origin & Problem Statement
            </div>

            <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight mb-6">
              &quot;My certification was put on hold despite scoring highest marks... so I solved the bottleneck for everyone.&quot;
            </h2>

            <div className="space-y-4 text-slate-300 text-base md:text-lg leading-relaxed border-l-2 border-orange-500/50 pl-6 my-6 italic">
              <p>
                &quot;I scored the highest marks in my batch. Yet, my certification was held back with feedback citing
                &apos;not having sales intent&apos; and being told to &apos;prove myself&apos; simply because calling volume
                targets weren&apos;t met on manual dialing.&quot;
              </p>
              <p>
                &quot;Instead of complaining or just building a personal shortcut for myself, as a true engineer and problem solver,
                I analyzed the root cause affecting <strong>the entire sales team</strong>: reps could not cross 200+ dials because
                LeadSquared CRM was lagging, MCUBE soft-phone threw non-presence errors, manual confirmation popups wasted seconds per lead,
                and returning to the grid frequently reset to Page 1.&quot;
              </p>
              <p>
                &quot;I built this auto-dialer to automate every click, filter out invalid leads, handle WebRTC tracking, and give our
                team the tool they needed to crush their daily numbers consistently.&quot;
              </p>
            </div>

            {/* Core Bottlenecks Overcome */}
            <div className="grid md:grid-cols-3 gap-4 pt-4">
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-center gap-2 text-rose-400 font-bold text-sm mb-2">
                  <AlertTriangle className="w-4 h-4" /> Non-Presence & MCUBE Errors
                </div>
                <p className="text-xs text-slate-400 leading-normal">
                  Soft-phone popups failing to register presence. Fixed via direct Chrome DevTools Protocol (CDP) WebSocket binding.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-center gap-2 text-amber-400 font-bold text-sm mb-2">
                  <AlertTriangle className="w-4 h-4" /> 5 Manual Clicks per Lead
                </div>
                <p className="text-xs text-slate-400 leading-normal">
                  Click Opportunity &rarr; wait for modal &rarr; click phone &rarr; click &quot;Yes&quot; &rarr; log disposition &rarr; return. Fully automated.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm mb-2">
                  <CheckCircle2 className="w-4 h-4" /> Smart Stage Filter
                </div>
                <p className="text-xs text-slate-400 leading-normal">
                  Automatically skips leads marked <em>Invalid Lead</em> or <em>Not Interested</em>, saving hundreds of minutes of wasted ringing.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION: DAY-WISE CALLING DATA PROOF */}
        <section id="proof" className="scroll-mt-24 space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-2xl md:text-3xl font-black text-white">The Undeniable Calling Data</h2>
            <p className="text-slate-400 text-sm md:text-base max-w-xl mx-auto">
              Real analytics directly from LeadSquared CRM showing the exact day the auto-dialer went live.
            </p>
          </div>

          <div className="rounded-3xl bg-slate-900 border border-slate-800 p-6 md:p-8 space-y-8 shadow-2xl">
            {/* Image Preview Container */}
            <div className="rounded-2xl overflow-hidden border border-slate-700 bg-white/5 relative group">
              <Image
                src="/calling-data.png"
                alt="LeadSquared Day-wise Calling Data Report"
                width={1200}
                height={600}
                className="w-full h-auto object-cover rounded-xl"
                priority
              />
              <div className="p-3 bg-slate-950/90 border-t border-slate-800 text-xs text-slate-400 flex items-center justify-between">
                <span>Verified LeadSquared CRM Report (ec=12000)</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> High-Performing Outbound Output
                </span>
              </div>
            </div>

            {/* Daily Breakdown Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950 text-slate-400 uppercase text-xs font-semibold border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Day</th>
                    <th className="py-3 px-4">Total Calls</th>
                    <th className="py-3 px-4">Outbound Dials</th>
                    <th className="py-3 px-4">Connected Calls</th>
                    <th className="py-3 px-4">Status / Performance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  <tr className="bg-slate-950/40">
                    <td className="py-3.5 px-4 font-semibold text-slate-300">Tuesday</td>
                    <td className="py-3.5 px-4 font-bold text-white">108</td>
                    <td className="py-3.5 px-4 text-slate-300">104</td>
                    <td className="py-3.5 px-4 text-slate-300">23</td>
                    <td className="py-3.5 px-4">
                      <span className="text-xs px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium">
                        Manual Dialing (Below 200 Target)
                      </span>
                    </td>
                  </tr>
                  <tr className="bg-slate-950/40">
                    <td className="py-3.5 px-4 font-semibold text-slate-300">Wednesday</td>
                    <td className="py-3.5 px-4 font-bold text-white">35</td>
                    <td className="py-3.5 px-4 text-slate-300">34</td>
                    <td className="py-3.5 px-4 text-slate-300">11</td>
                    <td className="py-3.5 px-4">
                      <span className="text-xs px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium">
                        Heavy System Lag & Bottlenecks
                      </span>
                    </td>
                  </tr>
                  <tr className="bg-emerald-950/20 border-l-4 border-l-emerald-500">
                    <td className="py-3.5 px-4 font-bold text-emerald-400">Thursday 🚀</td>
                    <td className="py-3.5 px-4 font-black text-xl text-white">256</td>
                    <td className="py-3.5 px-4 font-semibold text-emerald-300">243</td>
                    <td className="py-3.5 px-4 font-bold text-emerald-400">66</td>
                    <td className="py-3.5 px-4">
                      <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                        Auto-Dialer Deployed (Exceeded Target)
                      </span>
                    </td>
                  </tr>
                  <tr className="bg-emerald-950/20 border-l-4 border-l-emerald-500">
                    <td className="py-3.5 px-4 font-bold text-emerald-400">Friday 🔥</td>
                    <td className="py-3.5 px-4 font-black text-xl text-white">278</td>
                    <td className="py-3.5 px-4 font-semibold text-emerald-300">273</td>
                    <td className="py-3.5 px-4 font-bold text-emerald-400">89</td>
                    <td className="py-3.5 px-4">
                      <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                        Peak Performance (All-Time Record)
                      </span>
                    </td>
                  </tr>
                  <tr className="bg-emerald-950/20 border-l-4 border-l-emerald-500">
                    <td className="py-3.5 px-4 font-bold text-emerald-400">Saturday ⚡</td>
                    <td className="py-3.5 px-4 font-black text-xl text-white">265</td>
                    <td className="py-3.5 px-4 font-semibold text-emerald-300">260</td>
                    <td className="py-3.5 px-4 font-bold text-emerald-400">85</td>
                    <td className="py-3.5 px-4">
                      <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                        Consistent 260+ Dials Daily
                      </span>
                    </td>
                  </tr>
                  <tr className="bg-emerald-950/20 border-l-4 border-l-emerald-500">
                    <td className="py-3.5 px-4 font-bold text-emerald-400">Sunday 🏆</td>
                    <td className="py-3.5 px-4 font-black text-xl text-white">256</td>
                    <td className="py-3.5 px-4 font-semibold text-emerald-300">249</td>
                    <td className="py-3.5 px-4 font-bold text-emerald-400">85</td>
                    <td className="py-3.5 px-4">
                      <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-semibold">
                        Zero Rep Fatigue / Auto-Paging Active
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* SECTION: REGISTRATION & APP DOWNLOAD */}
        <section id="download" className="scroll-mt-24 space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-2xl md:text-3xl font-black text-white">Get the Auto-Dialer App</h2>
            <p className="text-slate-400 text-sm md:text-base max-w-lg mx-auto">
              Register with your Vedantu email address to immediately unlock direct download links for Windows and macOS.
            </p>
          </div>

          <div className="max-w-2xl mx-auto rounded-3xl bg-slate-900 border border-slate-800 p-6 md:p-10 shadow-2xl">
            {!isRegistered ? (
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="flex items-center gap-2 text-orange-400 font-semibold text-sm mb-2">
                  <ShieldCheck className="w-5 h-5" /> Vedantu Employee Authentication
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-slate-400 font-bold mb-1.5">
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Debargha Datta"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none text-white text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs uppercase tracking-wider text-slate-400 font-bold mb-1.5">
                    Official Vedantu Email (@vedantu.com only)
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="your.name@vedantu.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none text-white text-sm"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs uppercase tracking-wider text-slate-400 font-bold mb-1.5">
                      Phone / WhatsApp Number
                    </label>
                    <input
                      type="tel"
                      placeholder="e.g. 9635473667"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none text-white text-sm"
                    />
                  </div>

                  <div>
                    <label className="block text-xs uppercase tracking-wider text-slate-400 font-bold mb-1.5">
                      Your OS
                    </label>
                    <select
                      value={formData.os}
                      onChange={(e) => setFormData({ ...formData, os: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none text-white text-sm"
                    >
                      <option value="Windows">Windows (Standalone .exe)</option>
                      <option value="macOS">macOS (App Bundle & .command)</option>
                    </select>
                  </div>
                </div>

                {message && (
                  <div
                    className={`p-3.5 rounded-xl text-sm font-medium ${
                      message.type === "success"
                        ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                        : "bg-rose-500/10 border border-rose-500/20 text-rose-400"
                    }`}
                  >
                    {message.text}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 font-bold text-white shadow-lg shadow-orange-500/20 transition flex items-center justify-center gap-2 mt-4 text-base disabled:opacity-50"
                >
                  {loading ? "Authenticating with MongoDB..." : "Register & Unlock Direct Download"}
                </button>
              </form>
            ) : (
              /* UNLOCKED DOWNLOAD DASHBOARD */
              <div className="space-y-6">
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
                  <div>
                    <span className="font-bold">Access Granted:</span> Welcome,{" "}
                    <strong>{registeredUser?.name || "Vedantite"}</strong> ({registeredUser?.email}).
                  </div>
                </div>

                {/* Source Code Protection Notice */}
                <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <strong>Code Security:</strong> Pre-compiled binary release. No Python source code exposed.
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">v4.0.0 Production</span>
                </div>

                {/* OS Toggle Selector */}
                <div className="flex items-center justify-center gap-2 p-1 rounded-2xl bg-slate-950 border border-slate-800 max-w-sm mx-auto">
                  <button
                    type="button"
                    onClick={() => setSelectedOS("Windows")}
                    className={`flex-1 py-2 px-3 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition ${
                      selectedOS === "Windows"
                        ? "bg-cyan-600 text-white shadow-md shadow-cyan-600/30"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Laptop className="w-4 h-4" /> Windows Version
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedOS("macOS")}
                    className={`flex-1 py-2 px-3 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition ${
                      selectedOS === "macOS"
                        ? "bg-amber-600 text-white shadow-md shadow-amber-600/30"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <Apple className="w-4 h-4" /> macOS Version
                  </button>
                </div>

                {/* Targeted OS Download Presentation */}
                {selectedOS === "Windows" ? (
                  <div className="p-6 rounded-2xl bg-slate-950 border border-cyan-500/30 shadow-xl space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 text-cyan-400 font-black text-lg mb-1">
                          <Laptop className="w-5 h-5" /> Windows Standalone App (.exe)
                        </div>
                        <p className="text-xs text-slate-400 leading-relaxed max-w-md">
                          Double-clickable <code>MCUBE_AutoDialer.exe</code>. Fully packaged with internal runtime, auto-reconnect, and built-in Chrome launcher — no Python or coding setup required.
                        </p>
                      </div>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        .EXE Standalone
                      </span>
                    </div>

                    <div className="pt-2 space-y-2">
                      <a
                        href={`/api/download?email=${encodeURIComponent(registeredUser?.email || formData.email)}&os=windows`}
                        className="w-full py-3.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-extrabold text-base flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 transition"
                      >
                        <Download className="w-5 h-5" /> Download Windows App (.exe)
                      </a>
                      <div className="flex items-center justify-center gap-4 text-xs text-slate-400 pt-1">
                        <a
                          href="https://github.com/debarghadatta45/mcube-autodialer/releases/download/v4.0.0/MCUBE_AutoDialer.exe"
                          target="_blank"
                          rel="noreferrer"
                          className="hover:text-slate-200 inline-flex items-center gap-1 transition"
                        >
                          Direct Mirror (.exe) <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 rounded-2xl bg-slate-950 border border-amber-500/30 shadow-xl space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 text-amber-400 font-black text-lg mb-1">
                          <Apple className="w-5 h-5" /> macOS Disk Image (.dmg)
                        </div>
                        <p className="text-xs text-slate-400 leading-relaxed max-w-md">
                          Native Apple Disk Image <code>MCUBE_AutoDialer.dmg</code>. Double-click to mount and launch <code>MCUBE Auto-Dialer.app</code> directly or drag into Applications.
                        </p>
                      </div>
                      <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                        .DMG Disk Image
                      </span>
                    </div>

                    <div className="pt-2 space-y-2">
                      <a
                        href={`/api/download?email=${encodeURIComponent(registeredUser?.email || formData.email)}&os=mac`}
                        className="w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white font-extrabold text-base flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20 transition"
                      >
                        <Download className="w-5 h-5" /> Download macOS App (.dmg)
                      </a>
                      <div className="text-center">
                        <a
                          href="https://github.com/debarghadatta45/mcube-autodialer/releases/download/v4.0.0/MCUBE_AutoDialer.dmg"
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-slate-500 hover:text-slate-300 inline-flex items-center gap-1 transition"
                        >
                          Direct Mirror (.dmg) <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </div>
                  </div>
                )}

                {/* 3-Step Setup Instructions */}
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 space-y-2">
                  <div className="font-bold text-white text-sm mb-1">⚡ Quick Setup Guide:</div>
                  <ol className="list-decimal list-inside space-y-1 text-slate-400">
                    <li>Launch <code>MCUBE_AutoDialer.exe</code> (Windows) or double-click <code>MCUBE_AutoDialer.dmg</code> (macOS).</li>
                    <li>The always-on-top Mini-Controller appears with live statistics, Chrome launch controls, and page navigation.</li>
                    <li>Google Chrome will auto-launch with port 9222. Sign into LeadSquared and MCUBE once, and dialing begins!</li>
                  </ol>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* SECTION: BUG REPORTING & CREATOR CONTACT */}
        <section id="contact" className="scroll-mt-24 space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl md:text-3xl font-black text-white">Direct Support & Bug Reporting</h2>
            <p className="text-slate-400 text-sm md:text-base max-w-lg mx-auto">
              Facing any issues with LeadSquared DOM changes, soft-phone disconnects, or new feature requests? Connect directly.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 items-start">
            {/* Contact Card */}
            <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-6 shadow-xl">
              <div>
                <span className="text-xs uppercase tracking-wider text-orange-400 font-bold">Created & Maintained By</span>
                <h3 className="text-2xl font-black text-white mt-1">Debargha Datta</h3>
                <p className="text-sm text-slate-400">Vedantu Sales & Engineering Solutions</p>
              </div>

              <div className="space-y-4">
                <a
                  href="tel:9635473667"
                  className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-orange-500/50 transition group"
                >
                  <div className="w-10 h-10 rounded-lg bg-orange-500/10 text-orange-400 flex items-center justify-center font-bold">
                    <Phone className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Phone / WhatsApp Call</div>
                    <div className="text-sm font-bold text-white group-hover:text-orange-400 transition">
                      +91 9635473667
                    </div>
                  </div>
                </a>

                <a
                  href="mailto:debargha.datta@vedantu.com"
                  className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-orange-500/50 transition group"
                >
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold">
                    <Mail className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Official Vedantu Email</div>
                    <div className="text-sm font-bold text-white group-hover:text-blue-400 transition">
                      debargha.datta@vedantu.com
                    </div>
                  </div>
                </a>

                <a
                  href="https://www.linkedin.com/in/debargha-datta-9119521b0/"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-950 border border-slate-800 hover:border-cyan-500/50 transition group"
                >
                  <div className="w-10 h-10 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center font-bold">
                    <LinkedInIcon className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">Professional Profile</div>
                    <div className="text-sm font-bold text-white group-hover:text-cyan-400 transition flex items-center gap-1">
                      LinkedIn Profile <ExternalLink className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </a>
              </div>
            </div>

            {/* Bug Submission Box */}
            <div className="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4 shadow-xl">
              <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
                <Bug className="w-4 h-4" /> Report an Auto-Dialer Bug / Request
              </div>

              <form onSubmit={handleBugSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs uppercase text-slate-400 font-semibold mb-1">Your Name</label>
                  <input
                    type="text"
                    required
                    placeholder="Your Name"
                    value={bugData.name}
                    onChange={(e) => setBugData({ ...bugData, name: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm outline-none focus:border-rose-500"
                  />
                </div>

                <div>
                  <label className="block text-xs uppercase text-slate-400 font-semibold mb-1">Vedantu Email</label>
                  <input
                    type="email"
                    required
                    placeholder="name@vedantu.com"
                    value={bugData.email}
                    onChange={(e) => setBugData({ ...bugData, email: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm outline-none focus:border-rose-500"
                  />
                </div>

                <div>
                  <label className="block text-xs uppercase text-slate-400 font-semibold mb-1">Issue Category</label>
                  <select
                    value={bugData.category}
                    onChange={(e) => setBugData({ ...bugData, category: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm outline-none focus:border-rose-500"
                  >
                    <option value="LeadSquared DOM Change">LeadSquared Button / DOM Change</option>
                    <option value="MCUBE WebRTC Disconnect">MCUBE Soft-Phone Disconnect</option>
                    <option value="Grid Pagination Issue">Grid Pagination Stuck</option>
                    <option value="Sub-Stage Filter Request">Sub-Stage Filter Addition</option>
                    <option value="Feature Request">New Feature Request</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs uppercase text-slate-400 font-semibold mb-1">Issue Details</label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Describe what happened or what page you were on..."
                    value={bugData.message}
                    onChange={(e) => setBugData({ ...bugData, message: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm outline-none focus:border-rose-500"
                  />
                </div>

                {bugMessage && (
                  <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs">
                    {bugMessage}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={bugLoading}
                  className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm transition flex items-center justify-center gap-2 border border-slate-700 disabled:opacity-50"
                >
                  <Send className="w-4 h-4" /> {bugLoading ? "Submitting..." : "Send to Debargha Datta"}
                </button>
              </form>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="pt-12 pb-6 border-t border-slate-900 text-center text-xs text-slate-500 space-y-2">
          <p>
            MCUBE + LeadSquared Auto-Dialer &copy; 2026. Built with engineering excellence by Debargha Datta for Vedantu.
          </p>
          <p className="text-slate-600">
            Automating OpportunityManagement (ec=12000) & MCUBE Soft-Phone WebRTC.
          </p>
        </footer>
      </main>
    </div>
  );
}
