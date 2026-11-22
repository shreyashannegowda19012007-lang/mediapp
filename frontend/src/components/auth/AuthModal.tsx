"use client";

import React, { useState } from "react";
import { X, Lock, Mail, User, Phone, MapPin, CheckCircle2, ShieldCheck, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore, RoleType } from "@/store/useAuthStore";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { setActiveRole } = useAuthStore();
  const dialogRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!isOpen) return;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  React.useEffect(() => {
    if (!isOpen || !dialogRef.current) return;
    const el = dialogRef.current;
    const focusableElements = el.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    firstElement?.focus();

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement?.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement?.focus();
          e.preventDefault();
        }
      }
    };

    window.addEventListener("keydown", handleTabKey);
    return () => window.removeEventListener("keydown", handleTabKey);
  }, [isOpen, mode]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      if (mode === "login") {
        const res = await api.auth.login({ email, password });
        setActiveRole((res.user?.role as RoleType) || "customer");
        setSuccess("Authentication successful! Welcome back.");
      } else {
        await api.auth.register({
          email,
          password,
          full_name: fullName,
          phone,
          address,
        });
        setActiveRole("customer");
        setSuccess("Patient account registered and activated! Welcome to MediApp.");
      }
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication request failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
        className="relative w-full max-w-md rounded-2xl border border-sky-200 dark:border-sky-900 bg-white dark:bg-slate-900 shadow-2xl p-6 overflow-hidden"
      >
        {/* Accent Bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-sky-500 via-emerald-500 to-teal-400" />

        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close authentication modal"
          className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="mb-5">
          <div className="flex items-center gap-1.5 text-sky-600 dark:text-sky-400 font-bold text-xs uppercase tracking-wider">
            <ShieldCheck className="h-4 w-4" />
            <span>Encrypted Clinical Access</span>
          </div>
          <h2 id="auth-modal-title" className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {mode === "login" ? "Patient / Staff Sign In" : "Register Patient Account"}
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {mode === "login"
              ? "Sign in with your verified credentials to access prescriptions and orders."
              : "Create a verified patient record with express delivery address."}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl mb-4 text-xs font-semibold">
          <button
            type="button"
            onClick={() => {
              setMode("login");
              setError(null);
            }}
            className={`py-1.5 rounded-lg transition-all ${
              mode === "login"
                ? "bg-white dark:bg-slate-900 text-sky-600 dark:text-sky-400 shadow-xs"
                : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("register");
              setError(null);
            }}
            className={`py-1.5 rounded-lg transition-all ${
              mode === "register"
                ? "bg-white dark:bg-slate-900 text-sky-600 dark:text-sky-400 shadow-xs"
                : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            Create Patient Account
          </button>
        </div>

        {error && (
          <div className="mb-3 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-semibold text-rose-700 dark:text-rose-400">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-3 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          {mode === "register" && (
            <>
              <div>
                <label htmlFor="auth-fullname" className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <User className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="auth-fullname"
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
                <label htmlFor="auth-phone" className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Phone Number
                </label>
                <div className="relative">
                  <Phone className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="auth-phone"
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
                <label htmlFor="auth-address" className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                  Default Delivery Address
                </label>
                <div className="relative">
                  <MapPin className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    id="auth-address"
                    type="text"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="Flat 201, Lakeview Apts, Bellandur, Bengaluru"
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label htmlFor="auth-email" className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                id="auth-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="patient@example.com"
                className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 pl-9 pr-3 py-2 text-slate-900 dark:text-slate-100"
              />
            </div>
          </div>

          <div>
            <label htmlFor="auth-password" className="text-[11px] font-semibold text-slate-700 dark:text-slate-300 block mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                id="auth-password"
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
              <span>{mode === "login" ? "Sign In to MediApp" : "Create Patient Account"}</span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
