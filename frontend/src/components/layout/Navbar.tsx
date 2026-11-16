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
import { ROLE_DEFINITIONS } from "@/lib/rbac";
import { RoleLimitsModal } from "@/components/auth/RoleLimitsModal";
import { clsx } from "clsx";

interface NavbarProps {
  onOpenUploadRx?: () => void;
  onNavigateTab?: (tab: string) => void;
  activeTab?: string;
}

export function Navbar({ onOpenUploadRx, onNavigateTab, activeTab = "catalogue" }: NavbarProps) {
  const { user, activeRole, switchRole, isLoading } = useAuthStore();
  const { cart, setIsOpen } = useCartStore();
  const [showRoleLimitsModal, setShowRoleLimitsModal] = useState(false);

  const cartItemCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const currentRoleDef = ROLE_DEFINITIONS[activeRole] || ROLE_DEFINITIONS.customer;

  const handleRoleSwitched = (role: RoleType) => {
    const targetDef = ROLE_DEFINITIONS[role];
    if (onNavigateTab && targetDef) {
      onNavigateTab(targetDef.defaultTab);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 dark:border-slate-800/80 bg-white/90 dark:bg-slate-950/90 backdrop-blur-md">
      {/* Top Clinical Trust Bar */}
      <div className="hidden lg:flex items-center justify-between px-6 py-1.5 bg-slate-100 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 text-xs tracking-tight">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 font-medium text-slate-800 dark:text-slate-200">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            Licensed Pharmacy Network
          </span>
          <span className="text-slate-300 dark:text-slate-700">•</span>
          <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
            <ThermometerSnowflake className="h-3.5 w-3.5 text-cyan-600 dark:text-cyan-400" />
            Cold-Chain Monitored
          </span>
          <span className="text-slate-300 dark:text-slate-700">•</span>
          <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
            <Truck className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
            45-Min Express Delivery
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="text-slate-600 dark:text-slate-400">Helpline: <strong className="text-slate-800 dark:text-slate-200">1800-200-MEDI</strong></span>
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

        {/* Central Navigation Tabs (RBAC Filtered) */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-100/70 dark:bg-slate-900/70 p-1 rounded-xl border border-slate-200 dark:border-slate-800">
          {currentRoleDef.allowedTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onNavigateTab && onNavigateTab(tab.id)}
              className={clsx(
                "px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer",
                activeTab === tab.id
                  ? "bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Right Action Cluster */}
        <div className="flex items-center gap-2.5">
          {/* Theme Switcher */}
          <ThemeToggle />

          {/* Rx Quick Upload Button (Customer Only) */}
          {currentRoleDef.canUploadRx && onOpenUploadRx && (
            <button
              onClick={onOpenUploadRx}
              type="button"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-sky-300 dark:border-sky-800/80 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 text-xs font-semibold hover:bg-sky-100 dark:hover:bg-sky-900/60 transition-all cursor-pointer"
            >
              <FileText className="h-4 w-4 text-sky-500" />
              <span>Upload Rx</span>
            </button>
          )}

          {/* Cart Trigger (Customer Only) */}
          {currentRoleDef.canAccessCart && (
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
          )}

          {/* Role Identity & Limits Trigger */}
          <button
            onClick={() => setShowRoleLimitsModal(true)}
            type="button"
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-white border border-slate-200 dark:border-slate-700 text-xs font-medium shadow-xs transition-all cursor-pointer"
            title="View Auth0 Role Limits & Permissions"
          >
            <KeyRound className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
            <span className="capitalize font-semibold">{currentRoleDef.label}</span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
          </button>
        </div>
      </div>

      {/* Role Limits & RBAC Modal */}
      <RoleLimitsModal
        isOpen={showRoleLimitsModal}
        onClose={() => setShowRoleLimitsModal(false)}
        onRoleSwitched={handleRoleSwitched}
      />
    </header>
  );
}
