"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Lock,
  Mail,
  Users,
  Download,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  LogOut,
  ArrowLeft,
  Search,
  Filter,
  Check,
  Clock,
  Sparkles,
  Phone,
  Building
} from "lucide-react";

interface UserItem {
  id: string;
  name: string;
  email: string;
  department: string;
  registeredAt: string;
  downloads: number;
}

interface BugItem {
  id: string;
  name: string;
  email: string;
  phone: string;
  bugCategory: string;
  message: string;
  submittedAt: string;
  status: string;
}

interface AdminStats {
  totalUsers: number;
  totalDownloads: number;
  totalBugs: number;
  openBugs: number;
}

export default function AdminPage() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [emailInput, setEmailInput] = useState("debargha.datta@vedantu.com");
  const [passwordInput, setPasswordInput] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState("");

  const [activeTab, setActiveTab] = useState<"users" | "bugs">("users");
  const [dataLoading, setDataLoading] = useState(false);
  const [stats, setStats] = useState<AdminStats>({
    totalUsers: 0,
    totalDownloads: 0,
    totalBugs: 0,
    openBugs: 0,
  });
  const [users, setUsers] = useState<UserItem[]>([]);
  const [bugs, setBugs] = useState<BugItem[]>([]);

  // Search & filter states
  const [userSearch, setUserSearch] = useState("");
  const [bugCategoryFilter, setBugCategoryFilter] = useState("All");
  const [bugStatusFilter, setBugStatusFilter] = useState("All");
  const [togglingBugId, setTogglingBugId] = useState<string | null>(null);

  // Fetch admin data
  const fetchAdminData = async () => {
    setDataLoading(true);
    try {
      const res = await fetch("/api/admin/data");
      if (res.status === 401) {
        setIsAuthenticated(false);
        setDataLoading(false);
        return;
      }
      const data = await res.json();
      if (data.success) {
        setStats(data.stats);
        setUsers(data.users);
        setBugs(data.bugReports);
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
      }
    } catch {
      setIsAuthenticated(false);
    } finally {
      setDataLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  // Handle Login
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    setLoginError("");

    try {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailInput, password: passwordInput }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setIsAuthenticated(true);
        fetchAdminData();
      } else {
        setLoginError(data.error || "Invalid admin credentials");
      }
    } catch {
      setLoginError("Failed to authenticate. Please try again.");
    } finally {
      setLoginLoading(false);
    }
  };

  // Handle Logout
  const handleLogout = async () => {
    await fetch("/api/admin/logout", { method: "POST" });
    setIsAuthenticated(false);
    setPasswordInput("");
  };

  // Toggle Bug Status
  const toggleBugStatus = async (id: string, currentStatus: string) => {
    setTogglingBugId(id);
    const newStatus = currentStatus === "Resolved" ? "Open" : "Resolved";
    try {
      const res = await fetch("/api/admin/bug-status", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, status: newStatus }),
      });
      if (res.ok) {
        setBugs((prev) =>
          prev.map((b) => (b.id === id ? { ...b, status: newStatus } : b))
        );
        setStats((prev) => ({
          ...prev,
          openBugs: newStatus === "Resolved" ? prev.openBugs - 1 : prev.openBugs + 1,
        }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setTogglingBugId(null);
    }
  };

  // Filter users
  const filteredUsers = users.filter(
    (u) =>
      u.name.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.email.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.department.toLowerCase().includes(userSearch.toLowerCase())
  );

  // Filter bugs
  const filteredBugs = bugs.filter((b) => {
    const matchesCategory =
      bugCategoryFilter === "All" || b.bugCategory === bugCategoryFilter;
    const matchesStatus =
      bugStatusFilter === "All" || b.status === bugStatusFilter;
    return matchesCategory && matchesStatus;
  });

  // ----------------------------------------------------
  // LOGIN FORM COMPONENT
  // ----------------------------------------------------
  if (isAuthenticated === false) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center px-4 relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl shadow-2xl backdrop-blur-xl p-8 relative z-10">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 mb-4">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Admin Portal Login</h1>
            <p className="text-xs text-slate-400 mt-2">
              Authorized access for <span className="text-emerald-400 font-mono">debargha.datta@vedantu.com</span>
            </p>
          </div>

          {loginError && (
            <div className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Admin Email ID
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all font-mono"
                  placeholder="admin@vedantu.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Security Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="password"
                  required
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loginLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-slate-950 font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-50"
            >
              {loginLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Verifying Credentials...
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  Sign In to Dashboard
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-800/80 text-center">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Return to Main Portal
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // LOADING STATE
  // ----------------------------------------------------
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin" />
          <p className="text-sm text-slate-400">Loading Admin Dashboard...</p>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // AUTHENTICATED DASHBOARD
  // ----------------------------------------------------
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-slate-800"
              title="Return to portal"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="h-6 w-px bg-slate-800" />
            <div className="flex items-center gap-2">
              <span className="p-1 rounded-md bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <ShieldCheck className="w-4 h-4" />
              </span>
              <span className="font-bold text-white text-sm sm:text-base tracking-tight">
                MCUBE Auto-Dialer <span className="text-emerald-400 font-semibold">Admin Panel</span>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>debargha.datta@vedantu.com</span>
            </div>

            <button
              onClick={fetchAdminData}
              disabled={dataLoading}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors text-xs flex items-center gap-1.5"
              title="Refresh Data"
            >
              <RefreshCw className={`w-4 h-4 ${dataLoading ? "animate-spin" : ""}`} />
              <span className="hidden md:inline">Refresh</span>
            </button>

            <button
              onClick={handleLogout}
              className="p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 transition-colors text-xs flex items-center gap-1.5"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden md:inline">Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* KPI Cards Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 relative overflow-hidden group hover:border-emerald-500/40 transition-all">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Registered Users
              </span>
              <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">{stats.totalUsers}</div>
            <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <Check className="w-3 h-3 text-emerald-400" /> Authorized @vedantu.com reps
            </p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 relative overflow-hidden group hover:border-blue-500/40 transition-all">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Total Downloads
              </span>
              <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Download className="w-4 h-4" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">{stats.totalDownloads}</div>
            <p className="text-[11px] text-slate-500 mt-1">Windows (.exe) & Mac (.dmg)</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 relative overflow-hidden group hover:border-amber-500/40 transition-all">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Bug Reports
              </span>
              <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-white tracking-tight">{stats.totalBugs}</div>
            <p className="text-[11px] text-slate-500 mt-1">Total submitted feedback</p>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 relative overflow-hidden group hover:border-rose-500/40 transition-all">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Open Tickets
              </span>
              <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-rose-400 tracking-tight">{stats.openBugs}</div>
            <p className="text-[11px] text-slate-500 mt-1">Requiring engineering attention</p>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
          <button
            onClick={() => setActiveTab("users")}
            className={`px-4 py-2 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 transition-all ${
              activeTab === "users"
                ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20"
                : "bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800"
            }`}
          >
            <Users className="w-4 h-4" />
            Registered Users ({users.length})
          </button>

          <button
            onClick={() => setActiveTab("bugs")}
            className={`px-4 py-2 rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-2 transition-all ${
              activeTab === "bugs"
                ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/20"
                : "bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800"
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            Bug Reports & Feedback ({bugs.length})
            {stats.openBugs > 0 && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-rose-500 text-white font-bold ml-1">
                {stats.openBugs}
              </span>
            )}
          </button>
        </div>

        {/* ==================================================== */}
        {/* TAB 1: REGISTERED USERS                              */}
        {/* ==================================================== */}
        {activeTab === "users" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search by name, email, or department..."
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-all"
                />
              </div>
              <div className="text-xs text-slate-400 flex items-center gap-2">
                Showing <span className="font-bold text-white">{filteredUsers.length}</span> of{" "}
                <span className="font-bold text-white">{users.length}</span> users
              </div>
            </div>

            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider font-semibold border-b border-slate-800">
                    <tr>
                      <th className="py-3.5 px-4 sm:px-6">User</th>
                      <th className="py-3.5 px-4 sm:px-6">Department</th>
                      <th className="py-3.5 px-4 sm:px-6">Registered On</th>
                      <th className="py-3.5 px-4 sm:px-6 text-center">Downloads</th>
                      <th className="py-3.5 px-4 sm:px-6 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-slate-500">
                          No registered users found matching &quot;{userSearch}&quot;
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map((u) => (
                        <tr key={u.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-4 px-4 sm:px-6">
                            <div className="font-semibold text-white">{u.name}</div>
                            <div className="text-slate-400 text-xs font-mono">{u.email}</div>
                          </td>
                          <td className="py-4 px-4 sm:px-6 text-slate-300">
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 text-xs">
                              <Building className="w-3 h-3 text-slate-400" />
                              {u.department}
                            </span>
                          </td>
                          <td className="py-4 px-4 sm:px-6 text-slate-400 text-xs">
                            {new Date(u.registeredAt).toLocaleDateString("en-IN", {
                              day: "numeric",
                              month: "short",
                              year: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                          <td className="py-4 px-4 sm:px-6 text-center">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs font-bold font-mono">
                              <Download className="w-3 h-3" />
                              {u.downloads}
                            </span>
                          </td>
                          <td className="py-4 px-4 sm:px-6 text-right">
                            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[11px] font-medium">
                              <CheckCircle2 className="w-3 h-3" /> Active
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

        {/* ==================================================== */}
        {/* TAB 2: BUG REPORTS & FEEDBACK                        */}
        {/* ==================================================== */}
        {activeTab === "bugs" && (
          <div className="space-y-4">
            {/* Filters Row */}
            <div className="flex flex-wrap gap-3 items-center justify-between">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Filter className="w-3.5 h-3.5" /> Category:
                </span>
                {["All", "LeadSquared Grid", "MCUBE Softphone", "Audio / Call Flow", "General"].map(
                  (cat) => (
                    <button
                      key={cat}
                      onClick={() => setBugCategoryFilter(cat)}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        bugCategoryFilter === cat
                          ? "bg-slate-700 text-white border border-slate-600"
                          : "bg-slate-900 text-slate-400 hover:text-white"
                      }`}
                    >
                      {cat}
                    </button>
                  )
                )}
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Status:</span>
                {["All", "Open", "Resolved"].map((st) => (
                  <button
                    key={st}
                    onClick={() => setBugStatusFilter(st)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                      bugStatusFilter === st
                        ? "bg-slate-700 text-white border border-slate-600"
                        : "bg-slate-900 text-slate-400 hover:text-white"
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            {/* Bug Cards List */}
            {filteredBugs.length === 0 ? (
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center text-slate-500">
                <CheckCircle2 className="w-10 h-10 text-emerald-400/40 mx-auto mb-3" />
                <p>No bug reports found matching the selected filters.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredBugs.map((bug) => (
                  <div
                    key={bug.id}
                    className={`bg-slate-900/60 border rounded-2xl p-5 transition-all ${
                      bug.status === "Resolved"
                        ? "border-slate-800/80 opacity-75"
                        : "border-slate-800 hover:border-amber-500/40 shadow-lg"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                      <div className="flex items-center gap-3">
                        <span
                          className={`px-2.5 py-1 rounded-md text-xs font-bold border ${
                            bug.bugCategory.includes("MCUBE")
                              ? "bg-purple-500/10 text-purple-400 border-purple-500/30"
                              : bug.bugCategory.includes("LeadSquared")
                              ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                              : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                          }`}
                        >
                          {bug.bugCategory}
                        </span>

                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            bug.status === "Resolved"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                          }`}
                        >
                          {bug.status === "Resolved" ? (
                            <>
                              <CheckCircle2 className="w-3 h-3" /> Resolved
                            </>
                          ) : (
                            <>
                              <Clock className="w-3 h-3" /> Open
                            </>
                          )}
                        </span>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="text-xs text-slate-500">
                          {new Date(bug.submittedAt).toLocaleDateString("en-IN", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>

                        <button
                          onClick={() => toggleBugStatus(bug.id, bug.status)}
                          disabled={togglingBugId === bug.id}
                          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all border ${
                            bug.status === "Resolved"
                              ? "bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700"
                              : "bg-emerald-500 hover:bg-emerald-600 text-slate-950 border-emerald-400 font-bold"
                          }`}
                        >
                          {togglingBugId === bug.id ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : bug.status === "Resolved" ? (
                            "Re-open Ticket"
                          ) : (
                            "Mark Resolved"
                          )}
                        </button>
                      </div>
                    </div>

                    <p className="text-sm text-slate-200 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80 font-normal leading-relaxed whitespace-pre-wrap">
                      {bug.message}
                    </p>

                    <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                      <div>
                        Reported by: <span className="text-white font-medium">{bug.name}</span>
                      </div>
                      <div className="font-mono text-emerald-400/90">{bug.email}</div>
                      {bug.phone && (
                        <div className="flex items-center gap-1 text-slate-400">
                          <Phone className="w-3 h-3" /> {bug.phone}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-4 text-center text-xs text-slate-500">
        MCUBE Auto-Dialer Internal Administration &bull; Engineered by Debargha Datta &bull; Vedantu Edtech
      </footer>
    </div>
  );
}
