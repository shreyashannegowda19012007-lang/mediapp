"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Activity,
  ShieldCheck,
  ShoppingBag,
  FileText,
  User,
  ChevronDown,
  ChevronRight,
  ThermometerSnowflake,
  Truck,
  Building,
  KeyRound,
  Menu,
  X,
  HeartPulse,
  LogOut,
  Sparkles,
} from "lucide-react";
import { useAuthStore, RoleType } from "@/store/useAuthStore";
import { useCartStore } from "@/store/useCartStore";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { ROLE_DEFINITIONS } from "@/lib/rbac";
import { RoleLimitsModal } from "@/components/auth/RoleLimitsModal";
import { AITriageModal } from "@/components/clinical/AITriageModal";
import { AuthModal } from "@/components/auth/AuthModal";
import { clsx } from "clsx";

interface NavbarProps {
  onOpenUploadRx?: () => void;
  onNavigateTab?: (tab: string) => void;
  activeTab?: string;
}

function getUserInitials(name?: string): string {
  if (!name) return "U";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return parts[0].slice(0, 2).toUpperCase();
}

const ROLE_BADGE_STYLES: Record<RoleType, { bg: string; text: string; border: string }> = {
  customer: {
    bg: "bg-sky-50 dark:bg-sky-950/40",
    text: "text-sky-700 dark:text-sky-300",
    border: "border-sky-500/20",
  },
  pharmacy: {
    bg: "bg-amber-50 dark:bg-amber-950/40",
    text: "text-amber-800 dark:text-amber-400",
    border: "border-amber-500/30",
  },
  delivery: {
    bg: "bg-cyan-50 dark:bg-cyan-950/40",
    text: "text-cyan-800 dark:text-cyan-400",
    border: "border-cyan-500/30",
  },
  admin: {
    bg: "bg-emerald-50 dark:bg-emerald-950/40",
    text: "text-emerald-700 dark:text-emerald-400",
    border: "border-emerald-500/20",
  },
};

export function Navbar({ onOpenUploadRx, onNavigateTab, activeTab = "catalogue" }: NavbarProps) {
  const { user, activeRole, switchRole, logout, isLoading } = useAuthStore();
  const { cart, setIsOpen } = useCartStore();
  const [showRoleLimitsModal, setShowRoleLimitsModal] = useState(false);
  const [showAITriageModal, setShowAITriageModal] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const userMenuRef = useRef<HTMLDivElement>(null);

  const cartItemCount = cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const currentRoleDef = ROLE_DEFINITIONS[activeRole] || ROLE_DEFINITIONS.customer;
  const roleBadgeStyle = ROLE_BADGE_STYLES[activeRole] || ROLE_BADGE_STYLES.customer;

  const isAuthenticated = Boolean(user && (user.email || user.full_name));

  // Close user dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    if (userMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [userMenuOpen]);

  const handleRoleSwitched = (role: RoleType) => {
    const targetDef = ROLE_DEFINITIONS[role];
    if (onNavigateTab && targetDef) {
      onNavigateTab(targetDef.defaultTab);
    }
  };

  const handleSignOut = async () => {
    setUserMenuOpen(false);
    setMobileMenuOpen(false);
    await logout();
    if (onNavigateTab) {
      onNavigateTab("catalogue");
    }
  };

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 dark:border-slate-800/80 bg-white/95 dark:bg-slate-950/95 backdrop-blur-md shadow-xs">
        {/* Top Clinical Trust Bar */}
        <div className="hidden lg:flex items-center justify-between px-6 py-1.5 bg-slate-100/80 dark:bg-slate-900/80 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 text-xs tracking-tight">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 font-medium text-slate-800 dark:text-slate-200">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
              Licensed Clinical Pharmacy Network
            </span>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
              <ThermometerSnowflake className="h-3.5 w-3.5 text-cyan-600 dark:text-cyan-400" />
              Cold-Chain Monitored (2°C - 8°C)
            </span>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400">
              <Truck className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
              45-Min Express Doorstep Delivery
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className="text-slate-600 dark:text-slate-400">
              Clinical Helpline:{" "}
              <strong className="text-slate-800 dark:text-slate-200 font-mono">1800-200-MEDI</strong>
            </span>
          </div>
        </div>

        {/* Main Command Bar */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3 lg:gap-6">
          {/* Brand Identity */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => onNavigateTab && onNavigateTab("catalogue")}
              className="flex items-center gap-2.5 text-left cursor-pointer group"
            >
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform shrink-0">
                <Activity className="h-6 w-6" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5 leading-none">
                  <span className="text-lg font-black tracking-tight text-slate-900 dark:text-slate-100">
                    Medi<span className="text-sky-600 dark:text-sky-400">App</span>
                  </span>
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20">
                    Clinical
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 font-medium mt-0.5 hidden sm:block">
                  Licensed Healthcare Network
                </span>
              </div>
            </button>
          </div>

          {/* Central Workspace Navigation Tabs (RBAC Filtered) */}
          <nav className="hidden lg:flex items-center gap-1 bg-slate-100/80 dark:bg-slate-900/80 p-1 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs shrink-0">
            {currentRoleDef.allowedTabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onNavigateTab && onNavigateTab(tab.id)}
                  className={clsx(
                    "px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer",
                    isActive
                      ? "bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 shadow-xs font-bold"
                      : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-white/50 dark:hover:bg-slate-800/50"
                  )}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Right Action Cluster */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
            {/* AI Clinical Health Assistant Trigger */}
            <button
              onClick={() => (onNavigateTab ? onNavigateTab("symptom-triage") : setShowAITriageModal(true))}
              type="button"
              aria-label="Open AI Clinical Health Assistant"
              className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-indigo-200 dark:border-indigo-900/80 bg-indigo-50/70 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-xs font-semibold hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition-all cursor-pointer shadow-xs"
            >
              <HeartPulse className="h-4 w-4 text-indigo-500 animate-pulse" />
              <span>AI Triage</span>
            </button>

            {/* Quick Rx Upload Button (Customer Only) */}
            {currentRoleDef.canUploadRx && (
              <button
                onClick={() => (onNavigateTab ? onNavigateTab("prescriptions") : onOpenUploadRx?.())}
                type="button"
                className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-sky-300 dark:border-sky-800/80 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 text-xs font-semibold hover:bg-sky-100 dark:hover:bg-sky-900/60 transition-all cursor-pointer shadow-xs"
              >
                <FileText className="h-4 w-4 text-sky-500" />
                <span>Upload Rx</span>
              </button>
            )}

            {/* Cart Trigger (Customer Only) */}
            {currentRoleDef.canAccessCart && (
              <button
                id="btn-cart-toggle"
                onClick={() => setIsOpen(true)}
                type="button"
                className="relative p-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-700 dark:text-slate-300 transition-all cursor-pointer"
                title="Open prescription cart"
                aria-label={`Open prescription cart (${cartItemCount} items)`}
              >
                <ShoppingBag className="h-5 w-5" />
                {cartItemCount > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-sky-600 text-[10px] font-bold text-white shadow-xs">
                    {cartItemCount}
                  </span>
                )}
              </button>
            )}

            {/* Compact Theme Toggle */}
            <ThemeToggle />

            {/* Role Switcher Pill (Always accessible for verified persona limits) */}
            <button
              onClick={() => setShowRoleLimitsModal(true)}
              type="button"
              disabled={isLoading}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 text-xs font-medium transition-all cursor-pointer"
              title="View Auth0 Role Limits & Permissions"
            >
              <KeyRound className="h-3.5 w-3.5 text-sky-600 dark:text-sky-400" />
              <span className="capitalize hidden xl:inline">{currentRoleDef.label}</span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            </button>

            {/* Authenticated User Account Menu vs Guest Sign In */}
            {isAuthenticated && user ? (
              <div className="relative" ref={userMenuRef}>
                <button
                  id="btn-user-badge"
                  type="button"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 pl-1.5 pr-2.5 py-1 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-100 text-xs font-medium transition-all cursor-pointer shadow-xs"
                  aria-expanded={userMenuOpen}
                  aria-haspopup="true"
                >
                  <div className="h-7 w-7 rounded-lg bg-sky-600 text-white flex items-center justify-center font-bold text-[11px] shrink-0 shadow-xs">
                    {getUserInitials(user.full_name || user.email)}
                  </div>
                  <div className="hidden xl:flex flex-col text-left leading-tight">
                    <span className="font-semibold text-xs truncate max-w-[110px]">
                      {user.full_name || user.email.split("@")[0]}
                    </span>
                    <span className="text-[10px] text-slate-400 capitalize">
                      {currentRoleDef.label}
                    </span>
                  </div>
                  <ChevronDown
                    className={clsx(
                      "h-3.5 w-3.5 text-slate-400 transition-transform",
                      userMenuOpen && "rotate-180"
                    )}
                  />
                </button>

                {/* Account Menu Dropdown */}
                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-64 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl p-3 z-50 animate-in fade-in zoom-in-95 duration-100">
                    {/* User Identity Header */}
                    <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-100 dark:border-slate-800 mb-2">
                      <div className="font-bold text-xs text-slate-900 dark:text-slate-100 truncate">
                        {user.full_name || "Clinical User"}
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate font-mono">
                        {user.email}
                      </div>
                      <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                        <ShieldCheck className="h-3 w-3" />
                        <span>Verified {currentRoleDef.label}</span>
                      </div>
                    </div>

                    {/* Menu Actions */}
                    <div className="space-y-1 text-xs">
                      <button
                        type="button"
                        onClick={() => {
                          setShowRoleLimitsModal(true);
                          setUserMenuOpen(false);
                        }}
                        className="w-full flex items-center justify-between p-2 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left cursor-pointer"
                      >
                        <span className="flex items-center gap-2">
                          <KeyRound className="h-4 w-4 text-sky-500" />
                          <span>Switch Role & Permissions</span>
                        </span>
                        <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setShowAuthModal(true);
                          setUserMenuOpen(false);
                        }}
                        className="w-full flex items-center justify-between p-2 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left cursor-pointer"
                      >
                        <span className="flex items-center gap-2">
                          <User className="h-4 w-4 text-indigo-500" />
                          <span>Switch Account</span>
                        </span>
                      </button>

                      <div className="pt-1 mt-1 border-t border-slate-100 dark:border-slate-800">
                        <button
                          type="button"
                          onClick={handleSignOut}
                          className="w-full flex items-center gap-2 p-2 rounded-lg text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors text-left cursor-pointer font-semibold"
                        >
                          <LogOut className="h-4 w-4 text-rose-500" />
                          <span>Sign Out</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* Sign In CTA */
              <button
                id="btn-header-login"
                onClick={() => setShowAuthModal(true)}
                type="button"
                aria-label="Sign in or register customer account"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-sky-300 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/40 hover:bg-sky-100 dark:hover:bg-sky-900/60 text-sky-700 dark:text-sky-300 text-xs font-semibold shadow-xs transition-all cursor-pointer"
              >
                <User className="h-4 w-4 text-sky-500" />
                <span>Sign In</span>
              </button>
            )}

            {/* Mobile Hamburger Menu Toggle */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900 transition-all cursor-pointer"
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-950/95 p-4 sm:p-5 space-y-4 backdrop-blur-xl shadow-2xl animate-in slide-in-from-top-2 duration-150">
            {/* User Account / Sign In Status */}
            {isAuthenticated && user ? (
              <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="h-9 w-9 rounded-xl bg-sky-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
                    {getUserInitials(user.full_name || user.email)}
                  </div>
                  <div className="text-left">
                    <div className="font-bold text-xs text-slate-900 dark:text-slate-100 truncate">
                      {user.full_name || "Clinical User"}
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono truncate">
                      {user.email}
                    </div>
                    <span className="text-[10px] font-semibold text-sky-600 dark:text-sky-400 capitalize">
                      {currentRoleDef.label}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="p-2 rounded-xl text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-xs font-semibold flex items-center gap-1 cursor-pointer"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setShowAuthModal(true);
                  setMobileMenuOpen(false);
                }}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-sky-600 text-white text-xs font-semibold shadow-xs cursor-pointer"
              >
                <User className="h-4 w-4" />
                <span>Sign In or Register Patient Account</span>
              </button>
            )}

            {/* Navigation Tabs */}
            <div className="space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Workspace Tabs
              </span>
              <div className="flex flex-col gap-1">
                {currentRoleDef.allowedTabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => {
                      if (onNavigateTab) onNavigateTab(tab.id);
                      setMobileMenuOpen(false);
                    }}
                    className={clsx(
                      "flex items-center justify-between p-2.5 text-xs font-semibold rounded-xl text-left transition-all cursor-pointer",
                      activeTab === tab.id
                        ? "bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 font-bold"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-900"
                    )}
                  >
                    <span>{tab.label}</span>
                    {activeTab === tab.id && <span className="h-1.5 w-1.5 rounded-full bg-sky-500" />}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Actions Grid */}
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
              <button
                type="button"
                onClick={() => {
                  setShowAITriageModal(true);
                  setMobileMenuOpen(false);
                }}
                className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50/80 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-xs font-semibold cursor-pointer"
              >
                <HeartPulse className="h-4 w-4 text-indigo-500" />
                <span>AI Triage</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setShowRoleLimitsModal(true);
                  setMobileMenuOpen(false);
                }}
                className="flex items-center justify-center gap-1.5 py-2.5 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-semibold cursor-pointer"
              >
                <KeyRound className="h-4 w-4 text-slate-500" />
                <span>Role Limits</span>
              </button>
            </div>

            {currentRoleDef.canUploadRx && onOpenUploadRx && (
              <button
                onClick={() => {
                  onOpenUploadRx();
                  setMobileMenuOpen(false);
                }}
                type="button"
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-sky-300 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 text-xs font-semibold cursor-pointer"
              >
                <FileText className="h-4 w-4 text-sky-500" />
                <span>Upload Doctor Prescription</span>
              </button>
            )}

            {/* Helpline and Verification Footer */}
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 flex justify-between items-center">
              <span>Helpline: 1800-200-MEDI</span>
              <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Licensed Network</span>
              </span>
            </div>
          </div>
        )}
      </header>

      {/* Role Limits & RBAC Modal (Mounted via Portal) */}
      <RoleLimitsModal
        isOpen={showRoleLimitsModal}
        onClose={() => setShowRoleLimitsModal(false)}
        onRoleSwitched={handleRoleSwitched}
      />

      {/* AI Clinical Triage Modal (Mounted via Portal) */}
      <AITriageModal
        isOpen={showAITriageModal}
        onClose={() => setShowAITriageModal(false)}
      />

      {/* Patient Auth0/Credential Sign In & Register Modal (Mounted via Portal) */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </>
  );
}
