"use client";

import React from "react";
import {
  FileText,
  Sparkles,
  ShieldCheck,
  ThermometerSnowflake,
  ArrowRight,
  Clock,
  Pill,
} from "lucide-react";

interface HeroSectionProps {
  onOpenUploadRx: () => void;
  onNavigateTab: (tab: string) => void;
  onExploreCatalogue?: () => void;
}

export function HeroSection({
  onOpenUploadRx,
  onNavigateTab,
  onExploreCatalogue,
}: HeroSectionProps) {
  const handleExplore = () => {
    if (onExploreCatalogue) {
      onExploreCatalogue();
    } else {
      onNavigateTab("catalogue");
      setTimeout(() => {
        const el = document.getElementById("medicine-catalogue");
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
        const searchInput = document.getElementById("search-medicines-input");
        if (searchInput) {
          searchInput.focus();
        }
      }, 50);
    }
  };
  return (
    <div className="relative rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-sky-50/70 via-white to-slate-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900 text-slate-900 dark:text-white p-6 sm:p-10 shadow-lg dark:shadow-2xl">
      {/* Background Subtle Gradient Glow */}
      <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 rounded-full bg-sky-500/10 blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -mb-12 -ml-12 w-80 h-80 rounded-full bg-teal-500/10 blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-4xl space-y-6">
        {/* Network Tag */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-sky-100/80 dark:bg-white/10 text-sky-800 dark:text-sky-300 border border-sky-200 dark:border-white/10 backdrop-blur-md">
          <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          <span>Licensed Healthcare Delivery Network</span>
        </div>

        {/* Main Headline */}
        <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight text-slate-900 dark:text-white">
          Authentic Medicines & Clinical Care,{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-600 via-teal-600 to-emerald-600 dark:from-sky-400 dark:via-teal-300 dark:to-emerald-400">
            Delivered Fast.
          </span>
        </h1>

        <p className="text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
          Order authentic prescription medicines and healthcare essentials with licensed pharmacist verification, cold-chain tracking, and generic savings.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3 pt-2">
          <button
            onClick={onOpenUploadRx}
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-bold text-sm shadow-lg shadow-sky-500/25 transition-all hover:scale-[1.02] cursor-pointer"
          >
            <FileText className="h-4 w-4" />
            <span>Upload Prescription</span>
            <ArrowRight className="h-4 w-4" />
          </button>

          <button
            onClick={handleExplore}
            id="btn-explore-catalogue"
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white dark:bg-white/10 hover:bg-slate-50 dark:hover:bg-white/15 active:scale-[0.98] text-slate-800 dark:text-slate-200 font-semibold text-sm border border-slate-200 dark:border-white/10 backdrop-blur-md transition-all cursor-pointer hover:border-sky-400/50 hover:text-sky-600 dark:hover:text-white shadow-xs"
          >
            <Pill className="h-4 w-4 text-sky-500 dark:text-sky-400" />
            <span>Explore Medicines</span>
          </button>
        </div>

        {/* 4 Clinical Pillars Visual Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-6 border-t border-slate-200 dark:border-white/10">
          <div className="p-3 rounded-xl bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/5 space-y-1 shadow-xs">
            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-400">
              <ShieldCheck className="h-4 w-4" />
              <span>100% Genuine</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Verified manufacturers</div>
          </div>

          <div className="p-3 rounded-xl bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/5 space-y-1 shadow-xs">
            <div className="flex items-center gap-1.5 text-xs font-bold text-sky-700 dark:text-sky-400">
              <Clock className="h-4 w-4" />
              <span>Fast Review</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Pharmacist validated</div>
          </div>

          <div className="p-3 rounded-xl bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/5 space-y-1 shadow-xs">
            <div className="flex items-center gap-1.5 text-xs font-bold text-cyan-700 dark:text-cyan-400">
              <ThermometerSnowflake className="h-4 w-4" />
              <span>Cold-Chain Safe</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">2°C - 8°C monitored</div>
          </div>

          <div className="p-3 rounded-xl bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/5 space-y-1 shadow-xs">
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-700 dark:text-amber-400">
              <Sparkles className="h-4 w-4" />
              <span>Generic Savings</span>
            </div>
            <div className="text-[11px] text-slate-500 dark:text-slate-400">Save up to 70%</div>
          </div>
        </div>
      </div>
    </div>
  );
}
