"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Sparkles, AlertTriangle, ShieldCheck, ArrowRight, Loader2, HeartPulse, Plus, Check } from "lucide-react";
import { api } from "@/lib/api";
import { useCartStore } from "@/store/useCartStore";

interface AITriageModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AITriageModal({ isOpen, onClose }: AITriageModalProps) {
  const [mounted, setMounted] = useState(false);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cartError, setCartError] = useState<string | null>(null);
  const [addedIds, setAddedIds] = useState<Record<string | number, boolean>>({});

  const addItem = useCartStore((s) => s.addItem);

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

  const handleConsult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setIsLoading(true);
      setError(null);
      const res = await api.ai.consult(query);
      setResult(res.result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Clinical consult failed");
    } finally {
      setIsLoading(false);
    }
  };

  const sampleQueries = [
    "Acid reflux and burning chest sensation after dinner",
    "Seasonal allergies, sneezing, and itchy hives",
    "Acute loose motions and watery diarrhea",
    "Sore throat and pain on swallowing",
    "Tension headache and low-grade fever",
    "Painful mouth ulcers and burning tongue",
  ];

  return createPortal(
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs overflow-y-auto animate-in fade-in duration-150"
    >
      <div className="relative w-full max-w-xl my-auto rounded-2xl border border-sky-200 dark:border-sky-900 bg-white dark:bg-slate-900 shadow-2xl p-6 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Top Accent Gradient */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-sky-500 via-indigo-500 to-cyan-400" />

        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close AI clinical triage modal"
          className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="mb-4">
          <div className="flex items-center gap-1.5 text-sky-600 dark:text-sky-400 font-bold text-xs uppercase tracking-wider">
            <HeartPulse className="h-4 w-4" />
            <span>AI Clinical Health Assistant</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            Symptom Assessment & Emergency Triage
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Describe symptoms for preliminary OTC recommendations, dosage guidance, or emergency red-flag screening.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleConsult} className="space-y-3">
          <div className="relative">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Acid indigestion, sore throat, mild joint stiffness..."
              rows={3}
              className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 p-3 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="flex flex-wrap gap-1.5">
            <span className="text-[10px] text-slate-400 font-medium self-center mr-1">Quick prompts:</span>
            {sampleQueries.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(q)}
                className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-sky-50 dark:hover:bg-sky-950/40 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors"
              >
                {q.slice(0, 32)}...
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold shadow-xs transition-all cursor-pointer disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Screening Symptoms...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Run Clinical Triage Screening</span>
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-medium text-rose-700 dark:text-rose-400">
            {error}
          </div>
        )}

        {/* Results Viewport */}
        {result && (
          <div className="mt-4 overflow-y-auto space-y-3 pr-1 flex-1">
            {/* Emergency Alert */}
            {result.is_emergency && (
              <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/30 flex items-start gap-2.5 text-rose-800 dark:text-rose-300">
                <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
                <div className="text-xs space-y-1">
                  <div className="font-extrabold uppercase tracking-wider text-[11px]">
                    Emergency Warning Flag Detected
                  </div>
                  <p>{result.emergency_message || "Symptoms indicate potential critical illness. Please seek immediate in-person emergency hospital care."}</p>
                </div>
              </div>
            )}

            {/* Assessment */}
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                <span>Clinical Triage Findings</span>
              </div>
              <div className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-line leading-relaxed">
                {result.advice || result.response || result.summary || JSON.stringify(result, null, 2)}
              </div>
            </div>

            {/* OTC Formulations */}
            {result.recommended_medicines && result.recommended_medicines.length > 0 && (
              <div className="p-3.5 rounded-xl bg-sky-50/50 dark:bg-sky-950/30 border border-sky-100 dark:border-sky-900/60 space-y-2">
                <div className="text-xs font-bold text-sky-800 dark:text-sky-300">
                  Recommended OTC Formulations
                </div>
                <div className="space-y-1.5">
                  {result.recommended_medicines.map((m: any, idx: number) => {
                    const medId = m.id || idx;
                    const isAdded = Boolean(addedIds[medId]);
                    const medName = m.name || (typeof m === "string" ? m : "OTC Formulation");
                    return (
                      <div key={idx} className="flex items-center justify-between text-xs bg-white dark:bg-slate-900 p-2.5 rounded-xl border border-slate-100 dark:border-slate-800">
                        <div>
                          <span className="font-semibold text-slate-800 dark:text-slate-200">
                            {medName}
                          </span>
                          {m.dosage && (
                            <span className="text-[11px] text-slate-500 block">{m.dosage}</span>
                          )}
                        </div>
                        {m.id && (
                          <button
                            type="button"
                            onClick={async () => {
                              try {
                                await addItem(m.id, 1);
                                setAddedIds((prev) => ({ ...prev, [medId]: true }));
                                setTimeout(() => setAddedIds((prev) => ({ ...prev, [medId]: false })), 2000);
                              } catch (err: unknown) {
                                setCartError(err instanceof Error ? err.message : "Failed to add to cart");
                                setTimeout(() => setCartError(null), 3000);
                              }
                            }}
                            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                              isAdded ? "bg-emerald-600 text-white" : "bg-sky-600 hover:bg-sky-700 text-white"
                            }`}
                          >
                            {isAdded ? <Check className="h-3 w-3" /> : <Plus className="h-3 w-3" />}
                            <span>{isAdded ? "Added" : "Add"}</span>
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {cartError && (
              <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs font-semibold text-rose-700 dark:text-rose-400">
                {cartError}
              </div>
            )}

            <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-800 dark:text-amber-400">
              Disclaimer: AI Triage Assistant provides informational guidance under Drugs and Cosmetics Rules. It does not constitute formal medical diagnosis.
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold transition-all cursor-pointer"
              >
                Close Assistant
              </button>
            </div>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}
