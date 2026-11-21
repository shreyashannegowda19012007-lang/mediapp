"use client";

import React, { useState } from "react";
import { Plus, Check, Sparkles, Building2, Pill } from "lucide-react";
import { Medicine, GenericAlternative, api } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useCartStore } from "@/store/useCartStore";
import { GenericPriceMatchModal } from "./GenericPriceMatchModal";

interface MedicineCardProps {
  medicine: Medicine;
}

export function MedicineCard({ medicine }: MedicineCardProps) {
  const addItem = useCartStore((s) => s.addItem);
  const [isAdding, setIsAdding] = useState(false);
  const [genericData, setGenericData] = useState<GenericAlternative | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [checkingGeneric, setCheckingGeneric] = useState(false);

  const [authError, setAuthError] = useState<string | null>(null);

  const isColdChain =
    medicine.category.toLowerCase().includes("insulin") ||
    medicine.category.toLowerCase().includes("vaccine") ||
    medicine.category.toLowerCase().includes("biological") ||
    medicine.name.toLowerCase().includes("insulin");

  const price = medicine.unit_price ?? medicine.mrp;
  const hasDiscount = medicine.mrp > price;
  const isOutOfStock = (medicine.stock_quantity ?? 10) <= 0 || medicine.is_available === 0;
  const cleanGenericName = medicine.generic_name ? medicine.generic_name.split("|")[0].trim() : "";

  const handleAddToCart = async () => {
    try {
      setIsAdding(true);
      setAuthError(null);
      await addItem(medicine.id, 1);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to add to cart";
      if (msg.toLowerCase().includes("auth") || msg.toLowerCase().includes("sign in") || msg.toLowerCase().includes("401")) {
        setAuthError("Sign-in required: Please select a demo role or sign in to add medicines.");
      } else {
        setAuthError(msg);
      }
      setTimeout(() => setAuthError(null), 4000);
    } finally {
      setTimeout(() => setIsAdding(false), 500);
    }
  };

  const handleInspectGenericMatch = async () => {
    try {
      setCheckingGeneric(true);
      const res = await api.medicines.getGenericAlternatives(medicine.id);
      setGenericData(res);
      setIsModalOpen(true);
    } catch (err) {
      console.error(err);
    } finally {
      setCheckingGeneric(false);
    }
  };

  return (
    <>
      <div className="group relative flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-5 shadow-xs hover:shadow-lg hover:border-sky-300 dark:hover:border-sky-700/60 transition-all duration-200">
        <div>
          {/* Status Badges Row */}
          <div className="flex flex-wrap items-center gap-1.5 mb-3">
            {medicine.prescription_required ? (
              <StatusBadge type="rx" size="sm" />
            ) : (
              <StatusBadge type="otc" size="sm" />
            )}

            {isColdChain && <StatusBadge type="cold-chain" size="sm" />}
          </div>

          {/* Medicine Title & Generic Formula */}
          <div className="mb-2">
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">
              {medicine.name}
            </h3>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
              <Pill className="h-3 w-3 text-sky-500 shrink-0" />
              <span className="truncate">{cleanGenericName || medicine.generic_name}</span>
            </p>
          </div>

          {/* Clinical Specifications */}
          <div className="grid grid-cols-2 gap-2 text-xs py-2 my-2 border-y border-slate-100 dark:border-slate-800/80 text-slate-600 dark:text-slate-400">
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 block">
                Form & Strength
              </span>
              <span className="font-medium text-slate-800 dark:text-slate-200">
                {medicine.dosage_form} • {medicine.strength || "Standard"}
              </span>
            </div>
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 block">
                Manufacturer
              </span>
              <span className="font-medium text-slate-800 dark:text-slate-200 truncate flex items-center gap-1">
                <Building2 className="h-3 w-3 text-slate-400" />
                <span className="truncate">{medicine.manufacturer || "Licensed Pharma"}</span>
              </span>
            </div>
          </div>

          {/* Category Tag */}
          <div className="text-[11px] text-slate-500 dark:text-slate-400 mb-3">
            Category: <span className="font-medium text-slate-700 dark:text-slate-300">{medicine.category}</span>
          </div>

          {/* Generic Price Match Trigger */}
          <button
            type="button"
            onClick={handleInspectGenericMatch}
            disabled={checkingGeneric}
            aria-label={`Check generic bioequivalent alternatives for ${medicine.name}`}
            className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-sky-200 dark:border-sky-900/60 bg-sky-50/70 dark:bg-sky-950/20 text-sky-700 dark:text-sky-300 text-xs font-semibold hover:bg-sky-100 dark:hover:bg-sky-900/40 transition-all cursor-pointer mb-4"
          >
            <span className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-sky-500" />
              <span>Generic Price Match</span>
            </span>
            <span className="text-[11px] underline">Check Bioequivalent</span>
          </button>
        </div>

        {/* Pricing & Cart Action */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-lg font-extrabold text-slate-900 dark:text-slate-100">
                ₹{price.toFixed(2)}
              </span>
              {hasDiscount && (
                <span className="text-xs text-slate-400 line-through">₹{medicine.mrp.toFixed(2)}</span>
              )}
            </div>
            {isOutOfStock ? (
              <span className="text-[10px] text-rose-600 dark:text-rose-400 font-semibold block">
                Out of Stock
              </span>
            ) : (
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold block">
                In Stock & Ready
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={handleAddToCart}
            disabled={isAdding || isOutOfStock}
            aria-label={isOutOfStock ? `${medicine.name} is currently out of stock` : `Add ${medicine.name} to cart`}
            className={`inline-flex items-center gap-1 px-3.5 py-2 rounded-xl text-xs font-semibold shadow-xs transition-all ${
              isOutOfStock
                ? "bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                : "bg-sky-600 hover:bg-sky-700 active:scale-95 text-white hover:shadow-md cursor-pointer disabled:opacity-50"
            }`}
          >
            {isAdding ? <Check className="h-4 w-4" /> : isOutOfStock ? null : <Plus className="h-4 w-4" />}
            <span>{isAdding ? "Added" : isOutOfStock ? "Unavailable" : "Add to Cart"}</span>
          </button>
        </div>

        {authError && (
          <div className="mt-2.5 p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-[11px] font-medium text-rose-700 dark:text-rose-400">
            {authError}
          </div>
        )}
      </div>

      <GenericPriceMatchModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        data={genericData}
      />
    </>
  );
}
