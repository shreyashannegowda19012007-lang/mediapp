"use client";

import React from "react";
import { Link2, Sparkles, Box, Shield, Bike, ArrowRight, User } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

interface PortalLandingViewProps {
  onSelectPortal: (portal: "customer" | "pharmacy" | "admin" | "delivery") => void;
}

export function PortalLandingView({ onSelectPortal }: PortalLandingViewProps) {
  const { user, logout } = useAuthStore();

  const handleGoogleSignIn = async () => {
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
      const res = await api.auth.getGoogleUrl(origin, "customer");
      if (res && res.url) {
        window.location.href = res.url;
      }
    } catch (e) {
      console.error("Google Auth error:", e);
    }
  };
  return (
    <div className="relative min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-between overflow-hidden selection:bg-cyan-500 selection:text-black">
      {/* Ambient background glow orbs */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-purple-700/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/4 -right-32 w-96 h-96 bg-emerald-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-1/3 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 pt-8 pb-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg text-cyan-400">
            <Link2 className="h-6 w-6 stroke-[2.5]" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5 font-heading">
            Medi <span className="text-cyan-400">App</span>
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-xs text-slate-400 font-medium tracking-wide hidden sm:block">
            Hyperlocal medicine delivery · India
          </div>
          {user?.email ? (
            <div className="flex items-center gap-2.5 pl-2">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-bold text-white leading-tight">
                  {user.full_name || user.email}
                </div>
                <button
                  onClick={() => logout()}
                  className="text-[10px] font-semibold text-rose-400 hover:underline cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
              <div className="w-8 h-8 rounded-full bg-cyan-400 text-slate-950 font-black text-xs flex items-center justify-center shadow-md">
                {(user.full_name || "US").split(" ").map((n) => n[0]).join("").slice(0, 2)}
              </div>
            </div>
          ) : (
            <button
              id="btn-landing-google-signin"
              onClick={handleGoogleSignIn}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-slate-200 hover:text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
              title="Sign in with Google Account"
            >
              <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span>Continue with Google</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Hero & Portal Grid Container */}
      <main className="relative z-10 flex-1 w-full max-w-7xl mx-auto px-6 sm:px-8 py-8 flex flex-col items-center justify-center text-center">
        {/* Prescription pill badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs text-slate-300 shadow-lg mb-8 backdrop-blur-md">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
          <span>Prescription first · Safety-checked · Delivered fast</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight max-w-4xl leading-[1.15] mb-5">
          Medicines delivered from <br />
          <span className="text-cyan-400">pharmacies near you</span>
        </h1>

        {/* Subtitle */}
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto mb-14 leading-relaxed font-normal">
          One platform for customers, pharmacies, admins and delivery partners — with AI prescription reading and drug-interaction safety built in.
        </p>

        {/* Section Overline */}
        <div className="w-full text-center mb-6">
          <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400">
            CHOOSE YOUR PORTAL
          </span>
        </div>

        {/* 4 Portals Grid */}
        <div className="w-full max-w-6xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 text-left">
          {/* 1. Customer */}
          <div
            id="portal-card-customer"
            onClick={() => onSelectPortal("customer")}
            className="group relative bg-[#0b1220]/90 hover:bg-[#0e172a] border border-slate-800/80 hover:border-cyan-500/50 rounded-2xl p-6 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl shadow-black/40 hover:shadow-cyan-500/10"
          >
            <div>
              <div className="w-12 h-12 rounded-xl bg-cyan-950/60 border border-cyan-800/40 text-cyan-400 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
                <Link2 className="h-6 w-6 stroke-[2.2]" />
              </div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 mb-1">
                ORDER MEDICINES
              </div>
              <h2 className="text-xl font-bold text-white mb-2">
                Customer
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed mb-6">
                Upload a prescription, get OCR + drug interaction safety checks, and doorstep delivery.
              </p>
            </div>
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-cyan-400 group-hover:gap-2.5 transition-all">
              <span>Enter</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* 2. Pharmacy Partner */}
          <div
            id="portal-card-pharmacy"
            onClick={() => onSelectPortal("pharmacy")}
            className="group relative bg-[#0b1220]/90 hover:bg-[#0e172a] border border-slate-800/80 hover:border-indigo-500/50 rounded-2xl p-6 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl shadow-black/40 hover:shadow-indigo-500/10"
          >
            <div>
              <div className="w-12 h-12 rounded-xl bg-indigo-950/60 border border-indigo-800/40 text-indigo-400 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
                <Box className="h-6 w-6 stroke-[2.2]" />
              </div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-400 mb-1">
                FULFIL ORDERS
              </div>
              <h2 className="text-xl font-bold text-white mb-2">
                Pharmacy Partner
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed mb-6">
                Manage daily stock from the A-Z medicine database and accept nearby orders in real-time.
              </p>
            </div>
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-400 group-hover:gap-2.5 transition-all">
              <span>Enter</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* 3. Admin */}
          <div
            id="portal-card-admin"
            onClick={() => onSelectPortal("admin")}
            className="group relative bg-[#0b1220]/90 hover:bg-[#0e172a] border border-slate-800/80 hover:border-rose-500/50 rounded-2xl p-6 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl shadow-black/40 hover:shadow-rose-500/10"
          >
            <div>
              <div className="w-12 h-12 rounded-xl bg-rose-950/60 border border-rose-800/40 text-rose-400 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
                <Shield className="h-6 w-6 stroke-[2.2]" />
              </div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-rose-400 mb-1">
                OPERATE PLATFORM
              </div>
              <h2 className="text-xl font-bold text-white mb-2">
                Admin
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed mb-6">
                Restricted console: manage pharmacies, monitor &amp; cancel orders, and view analytics.
              </p>
            </div>
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-rose-400 group-hover:gap-2.5 transition-all">
              <span>Enter</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>

          {/* 4. Delivery Partner */}
          <div
            id="portal-card-delivery"
            onClick={() => onSelectPortal("delivery")}
            className="group relative bg-[#0b1220]/90 hover:bg-[#0e172a] border border-slate-800/80 hover:border-amber-500/50 rounded-2xl p-6 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-xl shadow-black/40 hover:shadow-amber-500/10"
          >
            <div>
              <div className="w-12 h-12 rounded-xl bg-amber-950/60 border border-amber-800/40 text-amber-400 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
                <Bike className="h-6 w-6 stroke-[2.2]" />
              </div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-amber-400 mb-1">
                EARN ON THE GO
              </div>
              <h2 className="text-xl font-bold text-white mb-2">
                Delivery Partner
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed mb-6">
                See pending deliveries nearby, track expected payouts, and manage your earnings.
              </p>
            </div>
            <div className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-400 group-hover:gap-2.5 transition-all">
              <span>Enter</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </div>
          </div>
        </div>
      </main>

      {/* Footer spacer */}
      <footer className="relative z-10 w-full py-6 text-center text-xs text-slate-600">
        MediApp Clinical Healthcare Network · Real-Time Decentralized Pharmacy System
      </footer>
    </div>
  );
}
