"use client";

import React from "react";
import { ShieldAlert, ArrowLeft, KeyRound, Lock } from "lucide-react";
import { RoleType } from "@/store/useAuthStore";
import { ROLE_DEFINITIONS } from "@/lib/rbac";

interface AccessRestrictedProps {
  attemptedTab: string;
  currentRole: RoleType;
  onResetToDefault: () => void;
  onOpenRoleModal: () => void;
}

export function AccessRestricted({
  attemptedTab,
  currentRole,
  onResetToDefault,
  onOpenRoleModal,
}: AccessRestrictedProps) {
  const currentDef = ROLE_DEFINITIONS[currentRole];

  return (
    <div className="min-h-[500px] flex items-center justify-center p-6">
      <div className="max-w-md w-full text-center p-8 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl space-y-5">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center justify-center">
          <ShieldAlert className="h-8 w-8" />
        </div>

        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20">
            <Lock className="h-3 w-3" /> Access Restricted (403 Forbidden)
          </div>
          <h2 className="text-xl font-black text-slate-900 dark:text-slate-100">
            Permission Required
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            Your active role <strong className="text-slate-900 dark:text-slate-100 capitalize">({currentRole})</strong> is not authorized to access the <span className="font-semibold text-slate-800 dark:text-slate-200">{attemptedTab}</span> workspace under Drugs and Cosmetics clinical confidentiality rules.
          </p>
        </div>

        <div className="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 text-left text-xs space-y-1">
          <div className="font-bold text-slate-700 dark:text-slate-300">Active Permissions:</div>
          <div className="flex flex-wrap gap-1">
            {currentDef.scopes.map((s) => (
              <span
                key={s}
                className="px-1.5 py-0.5 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-mono text-[10px] text-slate-600 dark:text-slate-400"
              >
                {s}
              </span>
            ))}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-2.5 pt-2">
          <button
            onClick={onResetToDefault}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs transition-all cursor-pointer shadow-xs"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Return to My Workspace</span>
          </button>
          <button
            onClick={onOpenRoleModal}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold text-xs hover:bg-slate-50 dark:hover:bg-slate-700 transition-all cursor-pointer"
          >
            <KeyRound className="h-4 w-4 text-sky-500" />
            <span>Switch Role</span>
          </button>
        </div>
      </div>
    </div>
  );
}
