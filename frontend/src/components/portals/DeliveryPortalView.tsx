"use client";

import React, { useState, useEffect } from "react";
import {
  Bike,
  RefreshCw,
  Star,
  Wallet,
  ArrowLeft,
  KeyRound,
  CheckCircle2,
  Package,
  MapPin,
  Clock,
  ShieldCheck
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

interface DeliveryPortalViewProps {
  onBackToPortals: () => void;
}

export function DeliveryPortalView({ onBackToPortals }: DeliveryPortalViewProps) {
  const { user, logout } = useAuthStore();
  const [metrics, setMetrics] = useState({
    deliveries: 0,
    today_payout: 0,
    total_earnings: 0,
    rating: 4.8
  });

  const handleGoogleSignIn = async () => {
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
      const res = await api.auth.getGoogleUrl(origin, "delivery");
      if (res && res.url) {
        window.location.href = res.url;
      }
    } catch (e) {
      console.error("Google Auth error:", e);
    }
  };

  const [availableDeliveries, setAvailableDeliveries] = useState<any[]>([]);
  const [activeOrder, setActiveOrder] = useState<any | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [otpInput, setOtpInput] = useState("");
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);
  const [otpFeedback, setOtpFeedback] = useState<string | null>(null);

  const fetchDeliveries = async () => {
    setIsRefreshing(true);
    try {
      const avail = await api.delivery.getAvailableRuns();
      setAvailableDeliveries(avail.orders || []);
    } catch (e) {
      // Keep state
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDeliveries();
  }, []);

  const handleClaim = async (orderId: string) => {
    try {
      await api.delivery.acceptRun(orderId);
      await fetchDeliveries();
    } catch (e) {
      console.error(e);
    }
  };

  const handlePickup = async (orderId: string) => {
    try {
      await api.delivery.pickup(orderId);
      await fetchDeliveries();
    } catch (e) {
      console.error(e);
    }
  };

  const handleStartTransit = async (orderId: string) => {
    try {
      await api.delivery.markInTransit(orderId);
      await fetchDeliveries();
    } catch (e) {
      console.error(e);
    }
  };

  const handleVerifyHandoff = async () => {
    if (!activeOrder || !otpInput.trim()) return;
    setIsVerifyingOtp(true);
    setOtpFeedback(null);
    try {
      await api.delivery.verifyHandoff(activeOrder.id, otpInput.trim());
      setOtpFeedback("Delivery Handover Verified Successfully! ₹75 Payout Added.");
      setMetrics(prev => ({
        ...prev,
        deliveries: prev.deliveries + 1,
        today_payout: prev.today_payout + 75,
        total_earnings: prev.total_earnings + 75
      }));
      setOtpInput("");
      await fetchDeliveries();
    } catch (err: any) {
      setOtpFeedback(err.message || "Invalid OTP code. Please ask the patient for the 6-digit verification code.");
    } finally {
      setIsVerifyingOtp(false);
    }
  };

  // Weekly earnings bars (Mon to Sun)
  const days = [
    { name: "Mon", amount: 0, height: 10 },
    { name: "Tue", amount: 0, height: 10 },
    { name: "Wed", amount: 0, height: 10 },
    { name: "Thu", amount: 0, height: 10 },
    { name: "Fri", amount: 0, height: 10 },
    { name: "Sat", amount: 0, height: 10 },
    { name: "Sun", amount: 0, height: 10 }
  ];

  return (
    <div className="relative min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-between overflow-x-hidden selection:bg-amber-500 selection:text-black">
      {/* Top Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 py-5 flex items-center justify-between border-b border-slate-800/40">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Bike className="h-6 w-6 text-amber-500 stroke-[2.2]" />
            <span className="text-xl font-bold tracking-tight text-white font-heading">
              Medi <span className="text-amber-500">App</span>
            </span>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-amber-950/80 text-amber-400 border border-amber-800/50">
            DELIVERY
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span>Online</span>
            <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500 inline-block" />
          </div>
          {user?.email ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
              <div className="text-right hidden sm:block">
                <span className="font-semibold text-white block text-xs">{user.full_name || "Delivery Courier"}</span>
                <span className="text-[10px] text-amber-400 block">{user.email}</span>
              </div>
              <button
                onClick={() => logout()}
                className="px-2.5 py-1 rounded-lg border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 font-semibold text-[11px] transition-colors cursor-pointer"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              id="btn-delivery-google-signin"
              onClick={handleGoogleSignIn}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-slate-200 hover:text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
              title="Sign in with Delivery Partner Google Account"
            >
              <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span>Google Sign-In</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-7">
        {/* 4 Metric KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              DELIVERIES
            </span>
            <span className="text-2xl sm:text-3xl font-extrabold text-white">
              {metrics.deliveries}
            </span>
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              TODAY'S PAYOUT
            </span>
            <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
              ₹{metrics.today_payout}
            </span>
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              TOTAL EARNINGS
            </span>
            <span className="text-2xl sm:text-3xl font-extrabold text-amber-500">
              ₹{metrics.total_earnings}
            </span>
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              RATING
            </span>
            <div className="flex items-center gap-1 text-2xl sm:text-3xl font-extrabold text-amber-400">
              <span>{metrics.rating}</span>
              <Star className="h-5 w-5 fill-amber-400 text-amber-400" />
            </div>
          </div>
        </div>

        {/* SECTION 1: Pending deliveries nearby */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-white">
              Pending deliveries nearby
            </span>
            <button
              onClick={fetchDeliveries}
              className="px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-amber-600/20 cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>

          {/* Active Assigned Mission Card (if in transit) */}
          {activeOrder ? (
            <div className="bg-[#0b1220] border border-amber-500/40 rounded-2xl p-5 space-y-4 shadow-xl">
              <div className="flex items-center justify-between text-xs sm:text-sm">
                <span className="font-bold text-white flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
                  <span>Active Mission: Order #{activeOrder.id}</span>
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-amber-950 text-amber-400 border border-amber-800 text-[10px] font-bold uppercase">
                  {activeOrder.status || activeOrder.order_status}
                </span>
              </div>

              <div className="text-xs text-slate-300">
                Doorstep Destination: <strong className="text-white">{activeOrder.delivery_address || "Bengaluru"}</strong>
              </div>

              {/* Action buttons */}
              {activeOrder.order_status === "DELIVERY_ASSIGNED" && (
                <button
                  onClick={() => handlePickup(activeOrder.id)}
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all cursor-pointer"
                >
                  Confirm Package Pickup at Pharmacy
                </button>
              )}

              {activeOrder.order_status === "IN_TRANSIT" && (
                <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                  <div className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <KeyRound className="h-4 w-4 text-cyan-400" />
                    <span>Enter Patient 6-Digit Doorstep Handover OTP</span>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      maxLength={6}
                      value={otpInput}
                      onChange={(e) => setOtpInput(e.target.value)}
                      placeholder="Enter 6-digit OTP (e.g. 582194)"
                      className="flex-1 bg-[#070b14] border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono tracking-widest text-center text-white outline-none focus:border-amber-400"
                    />
                    <button
                      onClick={handleVerifyHandoff}
                      disabled={isVerifyingOtp || !otpInput.trim()}
                      className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all disabled:opacity-50 cursor-pointer"
                    >
                      {isVerifyingOtp ? "Verifying..." : "Verify OTP"}
                    </button>
                  </div>
                  {otpFeedback && (
                    <div className="text-[11px] font-medium text-emerald-400">{otpFeedback}</div>
                  )}
                </div>
              )}
            </div>
          ) : (
            /* Empty State Card from Screenshot 6 */
            <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-8 text-center shadow-lg">
              <p className="text-xs sm:text-sm text-slate-400 leading-relaxed font-normal">
                No ready pickups yet — pharmacy must Accept -&gt; Pack -&gt; Mark ready.
              </p>
            </div>
          )}
        </div>

        {/* SECTION 2: Earnings Chart */}
        <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-5 space-y-6 shadow-xl">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Wallet className="h-4 w-4 text-amber-500" />
            <span>Earnings</span>
          </div>

          {/* Bar Chart Area */}
          <div className="pt-4 pb-2 px-2 flex items-end justify-between gap-2 h-44 border-b border-slate-800/80">
            {days.map((day) => (
              <div key={day.name} className="flex-1 flex flex-col items-center gap-2 group">
                <span className="text-[10px] text-slate-500 font-mono">₹{day.amount}</span>
                <div className="w-full max-w-[40px] bg-slate-900 group-hover:bg-amber-500/20 rounded-t-md transition-colors flex items-end justify-center h-28">
                  <div
                    className="w-full bg-amber-500/80 rounded-t-md transition-all"
                    style={{ height: `${day.height}%` }}
                  />
                </div>
                <span className="text-[11px] text-slate-400 font-medium">{day.name}</span>
              </div>
            ))}
          </div>

          <div className="text-right text-xs text-slate-400">
            Session earnings <span className="font-bold text-white">₹{metrics.today_payout}</span>
          </div>
        </div>
      </main>

      {/* Fixed Bottom-Left Navigation Pill */}
      <button
        onClick={onBackToPortals}
        className="fixed bottom-6 left-6 z-50 inline-flex items-center gap-2 px-3.5 py-2 rounded-full bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white shadow-xl backdrop-blur-md transition-all cursor-pointer"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        <span>All portals</span>
      </button>

      {/* Footer */}
      <footer className="relative z-10 w-full py-5 text-center text-[11px] text-slate-500 border-t border-slate-800/40">
        Live delivery feed - orders appear when pharmacy marks ready
      </footer>
    </div>
  );
}
