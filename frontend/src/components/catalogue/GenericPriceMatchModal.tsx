"use client";

import React from "react";
import { Sparkles, ArrowRight, ShieldCheck, Check, X, AlertCircle } from "lucide-react";
import { GenericAlternative } from "@/lib/api";
import { useCartStore } from "@/store/useCartStore";

interface GenericPriceMatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: GenericAlternative | null;
}

export function GenericPriceMatchModal({ isOpen, onClose, data }: GenericPriceMatchModalProps) {
  const addItem = useCartStore((s) => s.addItem);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !data) {
    return null;
  }

  // Extract from backend DDIService structure
  const target = data.target_medicine || {
    id: data.brand_id || 0,
    name: data.brand_name || "Branded Formulation",
    generic_name: data.generic_name || "Active Molecule",
    mrp: data.brand_price || 0,
  };

  const cheaperAlternative =
    data.alternatives?.find((a) => a.is_cheaper) ||
    (data.generic_alternative
      ? {
          id: data.generic_alternative.id,
          name: data.generic_alternative.name,
          generic_name: data.generic_alternative.generic_name,
          dosage_form: data.generic_alternative.dosage_form,
          strength: data.generic_alternative.strength,
          price: data.generic_alternative.unit_price,
          manufacturer: data.generic_alternative.manufacturer,
          is_cheaper: true,
          savings_pct: data.savings_percentage || 0,
          savings_amount: data.savings_amount || 0,
          match_type: "Certified Bioequivalent Generic",
        }
      : null);

  const hasSavings = Boolean(cheaperAlternative);

  const handleSelectGeneric = async () => {
    if (cheaperAlternative) {
      await addItem(cheaperAlternative.id, 1);
      onClose();
    }
  };

  const handleKeepBrand = async () => {
    await addItem(target.id, 1);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-2xl border border-sky-200 dark:border-sky-900 bg-white dark:bg-slate-900 shadow-2xl p-6 overflow-hidden">
        {/* Top Accent Gradient */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-sky-500 via-emerald-500 to-teal-400" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-2 text-sky-600 dark:text-sky-400 font-semibold text-xs tracking-wider uppercase mb-1">
          <Sparkles className="h-4 w-4" />
          <span>Bioequivalent Generic Price-Match</span>
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
          {hasSavings
            ? `Save ${cheaperAlternative?.savings_pct}% with Certified Generic`
            : "No Cheaper Generic Needed"}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-5">
          {hasSavings
            ? `Both medications contain the identical active pharmaceutical ingredient (${target.generic_name}) and clinical potency.`
            : `This formulation (${target.name}) is already offered at the most competitive clinical price.`}
        </p>

        {hasSavings && cheaperAlternative ? (
          <>
            {/* Comparison Grid */}
            <div className="grid grid-cols-2 gap-3 p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 mb-5">
              {/* Brand Product */}
              <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block mb-1">
                  Prescribed Formulation
                </span>
                <div className="font-bold text-slate-800 dark:text-slate-200 truncate">{target.name}</div>
                <div className="text-xs text-slate-500 dark:text-slate-400 truncate">{target.generic_name}</div>
                <div className="mt-3 text-lg font-bold text-slate-700 dark:text-slate-300">
                  ₹{target.mrp.toFixed(2)}
                </div>
              </div>

              {/* Bioequivalent Generic */}
              <div className="p-3 rounded-lg border border-emerald-300 dark:border-emerald-800 bg-emerald-500/5 dark:bg-emerald-950/20 relative">
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full mb-1">
                  <ShieldCheck className="h-3 w-3" /> Save ₹{cheaperAlternative.savings_amount.toFixed(2)}
                </span>
                <div className="font-bold text-slate-900 dark:text-slate-100 truncate">
                  {cheaperAlternative.name}
                </div>
                <div className="text-xs text-emerald-600 dark:text-emerald-400 truncate">
                  {cheaperAlternative.manufacturer}
                </div>
                <div className="mt-3 text-lg font-extrabold text-emerald-600 dark:text-emerald-400">
                  ₹{cheaperAlternative.price.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Clinical Quality Guarantee */}
            <div className="flex items-start gap-2.5 p-3 rounded-lg bg-sky-50 dark:bg-sky-950/30 border border-sky-100 dark:border-sky-900/40 text-xs text-sky-800 dark:text-sky-300 mb-6">
              <ShieldCheck className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                <strong>Licensed Pharmacist Guarantee:</strong> Identical therapeutic molecule ({target.generic_name}) and clinical bioavailability. Manufactured under strict CDSCO & WHO-GMP regulatory oversight.
              </span>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-2.5">
              <button
                onClick={handleSelectGeneric}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-md transition-all cursor-pointer"
              >
                <Check className="h-4 w-4" />
                <span>Switch to Generic (₹{cheaperAlternative.price.toFixed(2)})</span>
              </button>
              <button
                onClick={handleKeepBrand}
                className="inline-flex items-center justify-center px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs transition-all cursor-pointer"
              >
                Keep Selected Item
              </button>
            </div>
          </>
        ) : (
          <div className="space-y-4">
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-center space-y-2">
              <ShieldCheck className="h-8 w-8 text-emerald-500 mx-auto" />
              <div className="font-bold text-sm text-slate-800 dark:text-slate-200">{target.name}</div>
              <p className="text-xs text-slate-500">
                This item is already optimized at ₹{target.mrp.toFixed(2)}. No lower-cost bioequivalent substitute exists.
              </p>
            </div>
            <button
              onClick={handleKeepBrand}
              className="w-full py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs shadow-xs"
            >
              Add {target.name} to Cart
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
