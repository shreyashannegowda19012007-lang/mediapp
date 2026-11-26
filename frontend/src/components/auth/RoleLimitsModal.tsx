"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  ShieldCheck,
  User,
  Building,
  Truck,
  Activity,
  Lock,
  CheckCircle2,
  X,
  ExternalLink,
  KeyRound,
  AlertTriangle,
} from "lucide-react";
import { useAuthStore, RoleType } from "@/store/useAuthStore";
import { ROLE_DEFINITIONS } from "@/lib/rbac";
import { clsx } from "clsx";

interface RoleLimitsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRoleSwitched?: (role: RoleType) => void;
}

export function RoleLimitsModal({ isOpen, onClose, onRoleSwitched }: RoleLimitsModalProps) {
  const [mounted, setMounted] = useState(false);
  const { user, activeRole, switchRole, isLoading } = useAuthStore();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !mounted) return null;

  const currentDef = ROLE_DEFINITIONS[activeRole];

  const handleSelectRole = async (role: RoleType) => {
    if (role === activeRole) return;
    await switchRole(role);
    onRoleSwitched?.(role);
    onClose();
  };

  const roleIcons: Record<RoleType, React.ReactNode> = {
    customer: <User className="h-5 w-5 text-sky-500" />,
    pharmacy: <Building className="h-5 w-5 text-amber-500" />,
    delivery: <Truck className="h-5 w-5 text-cyan-500" />,
    admin: <Activity className="h-5 w-5 text-emerald-500" />,
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 sm:p-8 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Top Accent Gradient */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-sky-500 via-emerald-500 to-teal-400" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="p-3 rounded-2xl bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20">
            <KeyRound className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black text-slate-900 dark:text-slate-100">
                Role-Based Access Control
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                Auth0 RBAC
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Strict principle of least privilege. Each role is shown only authorized clinical data and workspaces.
            </p>
          </div>
        </div>

        {/* Active Authenticated Identity Badge */}
        <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
              Active Authenticated User
            </span>
            <div className="font-bold text-sm text-slate-900 dark:text-slate-100">
              {user?.full_name || "Healthcare User"} •{" "}
              <span className="text-sky-600 dark:text-sky-400">{user?.email}</span>
            </div>
            <div className="text-xs text-slate-500 mt-0.5 flex flex-wrap items-center gap-1.5">
              <span>Authorized Scopes:</span>
              {currentDef.scopes.map((scope) => (
                <span
                  key={scope}
                  className="px-1.5 py-0.5 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px] font-mono text-slate-700 dark:text-slate-300"
                >
                  {scope}
                </span>
              ))}
            </div>
          </div>
          <div className="px-3 py-1.5 rounded-xl bg-sky-50 dark:bg-sky-950/50 border border-sky-200 dark:border-sky-900/60 text-sky-700 dark:text-sky-300 text-xs font-bold shrink-0 flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span>{currentDef.badge}</span>
          </div>
        </div>

        {/* Role Selector Grid */}
        <div className="overflow-y-auto pr-1 space-y-3 flex-1">
          <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
            Select Persona to Switch Verified Access:
          </div>

          {(Object.keys(ROLE_DEFINITIONS) as RoleType[]).map((rKey) => {
            const rDef = ROLE_DEFINITIONS[rKey];
            const isCurrent = rKey === activeRole;

            return (
              <div
                key={rKey}
                onClick={() => handleSelectRole(rKey)}
                className={clsx(
                  "p-4 rounded-2xl border transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3",
                  isCurrent
                    ? "border-sky-500 dark:border-sky-500/80 bg-sky-50/50 dark:bg-sky-950/30 shadow-xs"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 hover:border-slate-300 dark:hover:border-slate-700"
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 shrink-0 mt-0.5">
                    {roleIcons[rKey]}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                        {rDef.label}
                      </span>
                      <span className="text-[11px] font-semibold text-slate-400">
                        ({rDef.roleTitle})
                      </span>
                      {isCurrent && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-600 text-white">
                          Current Active
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                      {rDef.description}
                    </p>
                    <div className="flex flex-wrap items-center gap-1.5 mt-2">
                      <span className="text-[10px] text-slate-400 font-semibold">Visible Tabs:</span>
                      {rDef.allowedTabs.map((t) => (
                        <span
                          key={t.id}
                          className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                        >
                          {t.label}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="shrink-0 self-end sm:self-center">
                  {isCurrent ? (
                    <span className="inline-flex items-center gap-1 text-xs font-bold text-sky-600 dark:text-sky-400">
                      <CheckCircle2 className="h-4 w-4" /> Active
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectRole(rKey);
                      }}
                      disabled={isLoading}
                      className="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold transition-all cursor-pointer"
                    >
                      Switch Persona
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Security Invariant Footer */}
        <div className="pt-4 mt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1">
            <Lock className="h-3.5 w-3.5 text-emerald-500" />
            Zero-Trust Isolation • All API requests guarded by server-side session checks
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-900 font-bold text-xs transition-all cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
