"use client";

import React, { useState } from "react";
import {
  HeartPulse,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Pill,
  Plus,
  Check,
  Loader2,
  Building2,
  ArrowRight,
  Search,
  Activity,
  Info,
} from "lucide-react";
import { api, Medicine } from "@/lib/api";
import { useCartStore } from "@/store/useCartStore";
import { useAuthStore } from "@/store/useAuthStore";
import { AuthModal } from "@/components/auth/AuthModal";
import { clsx } from "clsx";

interface PatientMedicalConditionsViewProps {
  onNavigateToCatalogue?: (searchQuery?: string) => void;
}

export function PatientMedicalConditionsView({
  onNavigateToCatalogue,
}: PatientMedicalConditionsViewProps) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [addedIds, setAddedIds] = useState<Record<number, boolean>>({});
  const [showAuthModal, setShowAuthModal] = useState(false);

  const addItem = useCartStore((s) => s.addItem);
  const { user } = useAuthStore();
  const isAuthenticated = Boolean(user && (user.email || user.full_name));

  const sampleQueries = [
    "Acid reflux and burning chest sensation after dinner",
    "Mild acute fever with body ache and chills",
    "Tension headache and eye strain after long screen time",
    "Seasonal allergies, runny nose, and frequent sneezing",
    "Acute loose motions and watery diarrhea",
    "Dry tickling cough and throat irritation",
    "Sore throat and severe pain on swallowing",
    "Painful mouth ulcers and burning tongue blisters",
    "Acute toothache and swollen tender gum",
    "Muscle sprain, cramp, and sports strain",
    "Stomach gas, bloating, and abdominal colic",
    "Nausea, vomiting, and food poisoning queasiness",
  ];

  const handleConsult = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      setIsLoading(true);
      setError(null);
      const res = await api.ai.consult(query);
      setResult(res.result);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Clinical triage failed. Please retry.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToCart = async (med: any) => {
    if (!isAuthenticated) {
      setShowAuthModal(true);
      return;
    }
    try {
      await addItem(med.id, 1);
      setAddedIds((prev) => ({ ...prev, [med.id]: true }));
      setTimeout(() => {
        setAddedIds((prev) => ({ ...prev, [med.id]: false }));
      }, 2000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to add medicine to cart";
      if (msg.toLowerCase().includes("auth") || msg.toLowerCase().includes("sign in") || msg.toLowerCase().includes("401")) {
        setShowAuthModal(true);
      } else {
        setError(msg);
        setTimeout(() => setError(null), 4000);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Clinical Trust Banner */}
      <div className="relative rounded-3xl border border-sky-100 dark:border-slate-800 bg-gradient-to-b from-sky-500/10 via-sky-500/5 to-transparent p-6 sm:p-8 backdrop-blur-xs">
        <div className="max-w-3xl mx-auto space-y-3 text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20">
            <HeartPulse className="h-3.5 w-3.5 text-sky-500 animate-pulse" />
            <span>AI Clinical Health Assistant • Triage & Live Stock Engine</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900 dark:text-slate-100">
            Describe Your Medical Conditions & Symptoms
          </h2>

          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Describe your ailments or symptoms below. Our clinical guidance engine screens for acute red flags, provides evidence-based self-care advice, and connects you directly with live inventory stock across licensed dispensaries.
          </p>
        </div>

        {/* Interactive Query Form */}
        <form onSubmit={handleConsult} className="max-w-3xl mx-auto mt-6 space-y-3">
          <div className="relative">
            <textarea
              id="medical-condition-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Acid indigestion and burning chest sensation after dinner, or mild fever with shivering..."
              rows={3}
              className="w-full text-sm rounded-2xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 p-4 shadow-sm focus:outline-hidden focus:ring-2 focus:ring-sky-500 transition-all resize-none"
            />
          </div>

          {/* Prompt Chips */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-xs text-slate-400 font-medium mr-1">Common conditions:</span>
            {sampleQueries.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(q)}
                className="text-xs px-2.5 py-1 rounded-xl bg-white dark:bg-slate-800 hover:bg-sky-50 dark:hover:bg-sky-950/40 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-sky-300 transition-all cursor-pointer shadow-2xs"
              >
                {q.length > 36 ? `${q.slice(0, 34)}...` : q}
              </button>
            ))}
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="text-[11px] text-slate-400 flex items-center gap-1">
              <Info className="h-3.5 w-3.5 text-slate-400" />
              <span>Compliant with Drugs and Cosmetics Rules for informational triage</span>
            </div>

            <button
              id="btn-submit-triage"
              type="submit"
              disabled={isLoading || !query.trim()}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-sky-600 hover:bg-sky-700 active:scale-[0.98] text-white text-xs font-bold transition-all cursor-pointer shadow-md disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Screening Condition & Stock...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Analyze Symptoms & Get Medicines</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-xs font-medium text-rose-700 dark:text-rose-400 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Workspace */}
      {result && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
          {/* Emergency Alert Banner */}
          {result.is_emergency && (
            <div className="p-5 rounded-2xl bg-rose-500/15 border border-rose-500/30 flex items-start gap-3.5 text-rose-800 dark:text-rose-300 shadow-sm">
              <AlertTriangle className="h-6 w-6 text-rose-600 shrink-0 mt-0.5" />
              <div className="space-y-1 text-xs sm:text-sm">
                <div className="font-extrabold uppercase tracking-wider text-xs text-rose-700 dark:text-rose-400">
                  Critical Emergency Warning Flag Detected
                </div>
                <p className="leading-relaxed font-semibold">
                  {result.response || result.emergency_message || "Symptoms indicate potential life-threatening emergency. Call 112 or visit an emergency room immediately."}
                </p>
                <div className="text-xs pt-1 text-rose-600 dark:text-rose-400">
                  Do not rely on online triage for acute coronary, stroke, or severe respiratory distress symptoms.
                </div>
              </div>
            </div>
          )}

          {/* Clinical Assessment Card */}
          {!result.is_emergency && (
            <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-bold text-sm">
                  <ShieldCheck className="h-5 w-5 text-emerald-500" />
                  <span>Clinical Assessment & Symptom Guidance</span>
                </div>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                  Preliminary Screening
                </span>
              </div>

              <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                {result.response || result.advice || result.summary}
              </div>
            </div>
          )}

          {/* Recommended Medicines with LIVE STOCK Card */}
          {result.recommended_medicines && result.recommended_medicines.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <Pill className="h-5 w-5 text-sky-500" />
                    <span>Recommended Medicines in Live Stock</span>
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Formulations matching your described condition with real-time dispensary stock verification.
                  </p>
                </div>

                {onNavigateToCatalogue && (
                  <button
                    onClick={() => onNavigateToCatalogue()}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-sky-600 dark:text-sky-400 hover:underline cursor-pointer"
                  >
                    <span>Browse Full Catalogue</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              {/* Medicines Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.recommended_medicines.map((med: any) => {
                  const isAdded = Boolean(addedIds[med.id]);
                  const inStock = med.in_stock ?? (med.stock_quantity > 0);

                  return (
                    <div
                      key={med.id}
                      className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-xs hover:shadow-md hover:border-sky-300 dark:hover:border-sky-700/60 transition-all flex flex-col justify-between"
                    >
                      <div>
                        {/* Status Badges */}
                        <div className="flex items-center justify-between gap-1.5 mb-2.5">
                          {med.prescription_required ? (
                            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-800 dark:text-amber-400 border border-amber-500/30">
                              Rx Required
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                              OTC Approved
                            </span>
                          )}

                          {inStock ? (
                            <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                              <span>In Stock ({med.stock_quantity} units)</span>
                            </span>
                          ) : (
                            <span className="text-[10px] font-semibold text-rose-600 dark:text-rose-400">
                              Out of Stock
                            </span>
                          )}
                        </div>

                        {/* Title & Generic Formula */}
                        <h4 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                          {med.name}
                        </h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 truncate">
                          {med.generic_name}
                        </p>

                        <div className="text-[11px] text-slate-400 mt-2">
                          {med.dosage_form} • {med.strength || "Standard"}
                        </div>
                      </div>

                      {/* Pricing & Add to Cart */}
                      <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                        <div>
                          <div className="flex items-baseline gap-1">
                            <span className="text-base font-black text-slate-900 dark:text-slate-100">
                              ₹{(med.unit_price || med.mrp || 0).toFixed(2)}
                            </span>
                            {med.mrp > (med.unit_price || med.mrp) && (
                              <span className="text-xs text-slate-400 line-through">
                                ₹{med.mrp.toFixed(2)}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-400 block">Unit MRP</span>
                        </div>

                        <div className="flex items-center gap-1.5">
                          {onNavigateToCatalogue && (
                            <button
                              type="button"
                              onClick={() => onNavigateToCatalogue(med.name)}
                              title="Inspect in Catalogue"
                              className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            >
                              <Search className="h-4 w-4" />
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={() => handleAddToCart(med)}
                            disabled={!inStock}
                            className={clsx(
                              "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-xs",
                              isAdded
                                ? "bg-emerald-600 text-white"
                                : inStock
                                ? "bg-sky-600 hover:bg-sky-700 text-white"
                                : "bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                            )}
                          >
                            {isAdded ? (
                              <>
                                <Check className="h-3.5 w-3.5" />
                                <span>Added</span>
                              </>
                            ) : (
                              <>
                                <Plus className="h-3.5 w-3.5" />
                                <span>Add to Cart</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Regulatory Disclaimer */}
          <div className="p-3.5 rounded-2xl bg-slate-100/70 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 text-[11px] leading-relaxed">
            <strong>Clinical Safety Disclaimer:</strong> This symptom guidance engine is an automated informational triage aid. It does not replace clinical consultation with a licensed physician. Prescription (Rx) formulations require an authorized doctor's prescription verified by our licensed dispensary pharmacists prior to dispatch.
          </div>
        </div>
      )}

      {showAuthModal && (
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
        />
      )}
    </div>
  );
}
