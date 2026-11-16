"use client";

import React, { useState } from "react";
import {
  Activity,
  ShieldCheck,
  ShoppingBag,
  FileText,
  User,
  MapPin,
  ChevronDown,
  Layers,
  ThermometerSnowflake,
  Truck,
  Building,
  KeyRound,
} from "lucide-react";
import { useAuthStore, RoleType } from "@/store/useAuthStore";
import { useCartStore } from "@/store/useCartStore";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { clsx } from "clsx";

interface NavbarProps {
  onOpenUploadRx?: () => void;
  onNavigateTab?: (tab: string) => void;
  activeTab?: string;
}

export function Navbar({ onOpenUploadRx, onNavigateTab, activeTab = "catalogue" }: NavbarProps) {
  const { user, activeRole, switchRole, isLoading } = useAuthStore();
  const { cart, setIsOpen } = useCartStore();
  const [showRoleDropdown, setShowRoleDropdown] = useState(false);

  const cartItemCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;

  const roles: Array<{ id: RoleType; label: string; desc: string; icon: React.ReactNode }> = [
    { id: "customer", label: "Customer", desc: "Browse catalogue, cart & order tracking", icon: <User className="h-4 w-4" /> },
    { id: "pharmacy", label: "Pharmacist Desk", desc: "Split-screen Rx review & dispensary pack", icon: <Building className="h-4 w-4" /> },
    { id: "delivery", label: "Delivery Fleet", desc: "Cold-chain transit & OTP verification", icon: <Truck className="h-4 w-4" /> },
    { id: "admin", label: "Admin HQ", desc: "System analytics, hospital fulfillment rates", icon: <Activity className="h-4 w-4" /> },
  ];

  const handleRoleSelect = async (role: RoleType) => {
    await switchRole(role);
    setShowRoleDropdown(false);
    if (onNavigateTab) {
      if (role === "pharmacy") onNavigateTab("pharmacist-desk");
      else if (role === "delivery") onNavigateTab("logistics");
      else if (role === "admin") onNavigateTab("admin-dashboard");
      else onNavigateTab("catalogue");
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 dark:border-slate-800/80 bg-white/90 dark:bg-slate-950/90 backdrop-blur-md">
      {/* Top Clinical Trust Bar */}
      <div className="hidden lg:flex items-center justify-between px-6 py-1.5 bg-slate-100 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 text-xs tracking-tight">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-1.5 font-medium text-slate-800 dark:text-slate-200">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            Licensed Partner Pharmacies & WHO-GMP Manufacturers
          </span>
          <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
            <ThermometerSnowflake className="h-3.5 w-3.5 text-cyan-600 dark:text-cyan-400" />
            Guaranteed Cold-Chain Logistics (2°C - 8°C Monitored)
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1 text-slate-700 dark:text-slate-300">
            <MapPin className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
            Express Dispatch: <strong>Bengaluru 560038</strong> (45 Min)
          </span>
          <span className="text-slate-300 dark:text-slate-600">|</span>
          <span className="text-slate-600 dark:text-slate-400">Clinical Helpline: 1800-200-MEDI (24/7)</span>
        </div>
      </div>

      {/* Main Command Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigateTab && onNavigateTab("catalogue")}
            className="flex items-center gap-2.5 text-left cursor-pointer group"
          >
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
              <Activity className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-lg font-black tracking-tight text-slate-900 dark:text-slate-100">
                  Medi<span className="text-sky-600 dark:text-sky-400">App</span>
                </span>
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20">
                  Clinical
                </span>
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block -mt-0.5 font-medium">
                Licensed Healthcare Network
              </span>
            </div>
          </button>
        </div>

        {/* Central Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-100/70 dark:bg-slate-900/70 p-1 rounded-xl border border-slate-200 dark:border-slate-800">
          <button
            onClick={() => onNavigateTab && onNavigateTab("catalogue")}
            className={clsx(
              "px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer",
              activeTab === "catalogue"
                ? "bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
            )}
          >
            Medicine Catalogue
          </button>
          <button
            onClick={() => onNavigateTab && onNavigateTab("pharmacist-desk")}
            className={clsx(
              "px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer",
              activeTab === "pharmacist-desk"
                ? "bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
            )}
          >
            Pharmacist Desk
          </button>
          <button
            onClick={() => onNavigateTab && onNavigateTab("logistics")}
            className={clsx(
              "px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer",
              activeTab === "logistics"
                ? "bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
            )}
          >
            Logistics & Orders
          </button>
          <button
            onClick={() => onNavigateTab && onNavigateTab("admin-dashboard")}
            className={clsx(
              "px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer",
              activeTab === "admin-dashboard"
                ? "bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
            )}
          >
            Hospital Analytics
          </button>
        </nav>

        {/* Right Action Cluster */}
        <div className="flex items-center gap-2.5">
          {/* Theme Switcher */}
          <ThemeToggle />

          {/* Rx Quick Upload Button */}
          {onOpenUploadRx && (
            <button
              onClick={onOpenUploadRx}
              type="button"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-sky-300 dark:border-sky-800/80 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 text-xs font-semibold hover:bg-sky-100 dark:hover:bg-sky-900/60 transition-all cursor-pointer"
            >
              <FileText className="h-4 w-4 text-sky-500" />
              <span>Upload Rx</span>
            </button>
          )}

          {/* Cart Trigger */}
          <button
            onClick={() => setIsOpen(true)}
            type="button"
            className="relative p-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-700 dark:text-slate-300 transition-all cursor-pointer"
            title="Open prescription cart"
          >
            <ShoppingBag className="h-5 w-5" />
            {cartItemCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-sky-600 text-[10px] font-bold text-white shadow-xs">
                {cartItemCount}
              </span>
            )}
          </button>

          {/* Role Switcher Menu */}
          <div className="relative">
            <button
              onClick={() => setShowRoleDropdown(!showRoleDropdown)}
              type="button"
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-white border border-slate-200 dark:border-slate-700 text-xs font-medium shadow-xs transition-all cursor-pointer"
            >
              <KeyRound className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
              <span className="capitalize font-semibold">{activeRole}</span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
            </button>

            {showRoleDropdown && (
              <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-2 z-50 animate-in fade-in duration-150">
                <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                  Switch Active Role Workspace
                </div>
                <div className="space-y-1 mt-1">
                  {roles.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => handleRoleSelect(r.id)}
                      className={clsx(
                        "w-full flex items-start gap-2.5 p-2 rounded-xl text-left transition-all cursor-pointer",
                        activeRole === r.id
                          ? "bg-sky-50 dark:bg-sky-950/40 text-sky-800 dark:text-sky-300 font-semibold"
                          : "hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300"
                      )}
                    >
                      <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 mt-0.5">
                        {r.icon}
                      </div>
                      <div>
                        <div className="text-xs font-bold">{r.label}</div>
                        <div className="text-[10px] text-slate-500 dark:text-slate-400">{r.desc}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
