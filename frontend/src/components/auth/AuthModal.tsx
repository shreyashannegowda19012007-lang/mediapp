"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  X,
  Lock,
  Mail,
  User,
  Phone,
  MapPin,
  CheckCircle2,
  ShieldCheck,
  Loader2,
  Building,
  Truck,
  Activity,
  KeyRound,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess?: () => void;
}

const DEMO_ACCOUNTS = [
  {
    role: "Customer",
    email: "customer@mediapp.local",
    pass: "Customer@123",
    icon: User,
    badgeColor: "border-sky-500/30 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300",
  },
  {
    role: "Pharmacist",
    email: "pharmacy@mediapp.local",
    pass: "Pharmacy@123",
    icon: Building,
    badgeColor: "border-amber-500/30 bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300",
  },
  {
    role: "Courier",
    email: "delivery@mediapp.local",
    pass: "Delivery@123",
    icon: Truck,
    badgeColor: "border-cyan-500/30 bg-cyan-50 dark:bg-cyan-950/40 text-cyan-700 dark:text-cyan-300",
  },
  {
    role: "Admin",
    email: "admin@mediapp.local",
    pass: "Admin@123",
    icon: Activity,
    badgeColor: "border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300",
  },
];

export function AuthModal({ isOpen, onClose, onAuthSuccess }: AuthModalProps) {
  const [mounted, setMounted] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { setActiveRole, fetchSession } = useAuthStore();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !mounted) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      if (mode === "login") {
        const res = await api.auth.login({ email, password });
        setActiveRole((res.user?.role as any) || "customer");
        setSuccess("Authentication successful! Welcome back.");
      } else {
        if (password !== confirmPassword) {
          setError("Passwords do not match. Please ensure both passwords match.");
          setIsLoading(false);
          return;
        }
        if (password.length < 6) {
          setError("Password must be at least 6 characters long.");
          setIsLoading(false);
          return;
        }
        const res = await api.auth.register({
          email,
          password,
          full_name: fullName,
          phone,
          address,
        });
        setActiveRole("customer");
        setSuccess("Patient account registered and activated! Welcome to MediApp.");
      }
      await fetchSession();
      onAuthSuccess?.();
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication request failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectDemo = (accEmail: string, accPass: string) => {
    setMode("login");
    setEmail(accEmail);
    setPassword(accPass);
    setError(null);
  };

  const handleGoogleAuth = async () => {
    setError(null);
    setIsGoogleLoading(true);
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
      const res = await api.auth.getGoogleUrl(origin, "customer");
      if (res && res.url) {
        window.location.href = res.url;
      } else {
        throw new Error("Unable to retrieve Google OAuth authorization URL.");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate Google OAuth");
      setIsGoogleLoading(false);
    }
  };

  const modalContent = (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-xs flex min-h-full items-start justify-center p-4 sm:p-6 text-center animate-in fade-in duration-150"
    >
      <div
        id="auth-modal"
        className="relative w-full max-w-md my-6 sm:my-auto flex flex-col rounded-3xl border border-sky-300 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 text-left overflow-y-auto max-h-[calc(100vh-3rem)]"
      >
        {/* Accent Top Bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-sky-500 via-emerald-500 to-teal-400 rounded-t-3xl" />

        {/* Prominent High-Visibility Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close authentication modal"
          className="absolute top-4 right-4 z-20 p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all cursor-pointer shadow-xs"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Modal Header */}
        <div className="mb-4 pr-8">
          <div className="flex items-center gap-1.5 text-sky-600 dark:text-sky-400 font-bold text-xs uppercase tracking-wider">
            <ShieldCheck className="h-4 w-4" />
            <span>Encrypted Clinical Access</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {mode === "login" ? "Patient / Staff Sign In" : "Register Patient Account"}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {mode === "login"
              ? "Sign in with your verified credentials or select a one-click demo account below."
              : "Create a verified patient record with express delivery address."}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl mb-4 text-xs font-semibold shrink-0">
          <button
            id="tab-btn-signin"
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
              setConfirmPassword("");
            }}
            className={`py-1.5 rounded-lg transition-all cursor-pointer ${
              mode === "login"
                ? "bg-white dark:bg-slate-900 text-sky-600 dark:text-sky-400 shadow-xs"
                : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            Sign In
          </button>
          <button
            id="tab-btn-register"
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`py-1.5 rounded-lg transition-all cursor-pointer ${
              mode === "register"
                ? "bg-white dark:bg-slate-900 text-sky-600 dark:text-sky-400 shadow-xs"
                : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            Register Patient
          </button>
        </div>

        {/* Google OAuth 2.0 Direct Button */}
        <div className="mb-4 shrink-0">
          <button
            id="btn-modal-google-signin"
            type="button"
            onClick={handleGoogleAuth}
            disabled={isGoogleLoading}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-100 text-xs font-semibold shadow-xs transition-all cursor-pointer disabled:opacity-50"
          >
            {isGoogleLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin text-sky-500" />
                <span>Connecting to Google...</span>
              </>
            ) : (
              <>
                <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                <span>Continue with Google</span>
              </>
            )}
          </button>
          <div className="flex items-center gap-3 my-3">
            <div className="flex-1 border-t border-slate-200 dark:border-slate-800" />
            <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">or sign in with password</span>
            <div className="flex-1 border-t border-slate-200 dark:border-slate-800" />
          </div>
        </div>

        {/* One-Click Demo Credentials Pill Selector (Login Mode) */}
        {mode === "login" && (
          <div className="mb-4 p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800 shrink-0">
            <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 dark:text-slate-400 mb-2">
              <span className="flex items-center gap-1">
                <KeyRound className="h-3 w-3 text-sky-500" />
                <span>One-Click Demo Accounts</span>
              </span>
              <span className="text-[10px] text-slate-400">Click to autofill</span>
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {DEMO_ACCOUNTS.map((acc) => {
                const IconComponent = acc.icon;
                const isSelected = email === acc.email;
                return (
                  <button
                    key={acc.role}
                    type="button"
                    onClick={() => handleSelectDemo(acc.email, acc.pass)}
                    className={`flex items-center gap-1.5 p-2 rounded-lg border text-left text-xs transition-all cursor-pointer ${
                      isSelected
                        ? "border-sky-500 bg-sky-50 dark:bg-sky-950/50 shadow-xs"
                        : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700"
                    }`}
                  >
                    <IconComponent className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                    <div className="truncate">
                      <div className="font-semibold text-slate-800 dark:text-slate-200 text-[11px] leading-tight">
                        {acc.role}
                      </div>
                      <div className="text-[9px] text-slate-400 font-mono truncate">{acc.email}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Feedback Alerts */}
        {error && (
          <div className="toast-error mb-3 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-semibold text-rose-700 dark:text-rose-400 shrink-0">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-3 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-2 shrink-0">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit} className="space-y-3 overflow-y-auto pr-1">
          {mode === "register" && (
            <>
              <div>
                <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <User className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="reg-name"
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Dr. Rajesh Sharma"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="reg-phone"
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Default Delivery Address
                </label>
                <div className="relative">
                  <MapPin className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="reg-address"
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="Flat 201, Lakeview Apts, Bellandur, Bengaluru"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="reg-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="customer@mediapp.local"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="reg-password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="reg-confirm-password"
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <button
                id="btn-submit-register"
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold shadow-xs transition-all cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Registering...</span>
                  </>
                ) : (
                  <span>Create Patient Account</span>
                )}
              </button>
            </>
          )}

          {mode === "login" && (
            <>
              <div>
                <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="signin-email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="customer@mediapp.local"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Password
                </label>
                <div className="relative">
                  <Lock className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="signin-password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>

              <button
                id="btn-submit-signin"
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold shadow-xs transition-all cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Authorizing...</span>
                  </>
                ) : (
                  <span>Sign In to MediApp</span>
                )}
              </button>
            </>
          )}
        </form>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
