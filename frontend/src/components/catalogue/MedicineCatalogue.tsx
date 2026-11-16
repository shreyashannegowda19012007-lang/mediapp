"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Search, Filter, AlertCircle, RefreshCw, X, Pill, ShieldCheck, ThermometerSnowflake, Sparkles } from "lucide-react";
import { Medicine, api } from "@/lib/api";
import { MedicineCard } from "./MedicineCard";
import { clsx } from "clsx";

export function MedicineCatalogue() {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [categories, setCategories] = useState<Array<{ category: string; count: number }>>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");
  const [rxFilter, setRxFilter] = useState<number | undefined>(undefined);
  const [coldChainOnly, setColdChainOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);

  const fetchMedicines = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await api.medicines.search({
        q: searchQuery,
        category: selectedCategory,
        rx: rxFilter,
        limit: 36,
      });

      let items = res.medicines || [];
      if (coldChainOnly) {
        items = items.filter(
          (m) =>
            m.category.toLowerCase().includes("insulin") ||
            m.category.toLowerCase().includes("vaccine") ||
            m.name.toLowerCase().includes("insulin")
        );
      }
      setMedicines(items);
      setTotalCount(res.pagination?.total_count || items.length);
    } catch (err) {
      console.error("Failed to load medicines:", err);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, selectedCategory, rxFilter, coldChainOnly]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchMedicines();
    }, 250);
    return () => clearTimeout(timer);
  }, [fetchMedicines]);

  useEffect(() => {
    api.medicines
      .getCategories()
      .then((res) => setCategories(res.categories || []))
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      {/* Omni-Search Hero Bar */}
      <div className="relative rounded-3xl border border-sky-100 dark:border-slate-800 bg-gradient-to-b from-sky-500/10 via-sky-500/5 to-transparent p-6 sm:p-8 backdrop-blur-xs">
        <div className="max-w-3xl mx-auto space-y-4">
          <div className="text-center space-y-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/15 text-sky-800 dark:text-sky-300 border border-sky-500/20">
              <ShieldCheck className="h-3.5 w-3.5" />
              Verified Dispensary Network & Bioequivalent Price Match
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
              Clinical Medicine Catalogue
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Search by brand name, active generic molecule (e.g. <em>Ranitidine, Paracetamol, Metformin</em>), or clinical indication.
            </p>
          </div>

          {/* Omni Search Input */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
              <Search className="h-5 w-5" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search 1,250+ medicines, generic molecules, ailments..."
              className="w-full pl-12 pr-10 py-3.5 rounded-2xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 shadow-lg text-sm focus:outline-hidden focus:ring-2 focus:ring-sky-500 transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Visual Filter Badges */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            <button
              onClick={() => {
                setRxFilter(undefined);
                setColdChainOnly(false);
              }}
              className={clsx(
                "px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer",
                rxFilter === undefined && !coldChainOnly
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 border-transparent shadow-xs"
                  : "bg-white/80 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300"
              )}
            >
              All Items ({totalCount})
            </button>

            <button
              onClick={() => {
                setRxFilter(0);
                setColdChainOnly(false);
              }}
              className={clsx(
                "inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer",
                rxFilter === 0
                  ? "bg-emerald-600 text-white border-transparent shadow-xs"
                  : "bg-white/80 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-emerald-700 dark:text-emerald-400 hover:border-emerald-300"
              )}
            >
              <span>OTC Only</span>
            </button>

            <button
              onClick={() => {
                setRxFilter(1);
                setColdChainOnly(false);
              }}
              className={clsx(
                "inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer",
                rxFilter === 1
                  ? "bg-amber-600 text-white border-transparent shadow-xs"
                  : "bg-white/80 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-amber-700 dark:text-amber-400 hover:border-amber-300"
              )}
            >
              <span>Prescription (Rx)</span>
            </button>

            <button
              onClick={() => setColdChainOnly(!coldChainOnly)}
              className={clsx(
                "inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all cursor-pointer",
                coldChainOnly
                  ? "bg-cyan-600 text-white border-transparent shadow-xs"
                  : "bg-white/80 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-cyan-700 dark:text-cyan-400 hover:border-cyan-300"
              )}
            >
              <ThermometerSnowflake className="h-3 w-3" />
              <span>Cold-Chain Monitored</span>
            </button>
          </div>
        </div>
      </div>

      {/* Category Horizontal Carousel */}
      {categories.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          <button
            onClick={() => setSelectedCategory("")}
            className={clsx(
              "px-3 py-1.5 text-xs font-medium rounded-xl whitespace-nowrap border transition-all cursor-pointer",
              selectedCategory === ""
                ? "bg-sky-600 text-white border-sky-600 shadow-xs"
                : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
            )}
          >
            All Therapeutic Categories
          </button>
          {categories.map((cat) => (
            <button
              key={cat.category}
              onClick={() => setSelectedCategory(cat.category === selectedCategory ? "" : cat.category)}
              className={clsx(
                "px-3 py-1.5 text-xs font-medium rounded-xl whitespace-nowrap border transition-all cursor-pointer",
                selectedCategory === cat.category
                  ? "bg-sky-600 text-white border-sky-600 shadow-xs"
                  : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
              )}
            >
              {cat.category} ({cat.count})
            </button>
          ))}
        </div>
      )}

      {/* Medicines Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="h-64 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 p-5 animate-pulse space-y-4"
            >
              <div className="h-4 w-24 bg-slate-200 dark:bg-slate-800 rounded-md" />
              <div className="h-6 w-48 bg-slate-200 dark:bg-slate-800 rounded-md" />
              <div className="h-3 w-32 bg-slate-100 dark:bg-slate-800 rounded-md" />
              <div className="h-16 bg-slate-100 dark:bg-slate-800/60 rounded-xl" />
              <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded-xl" />
            </div>
          ))}
        </div>
      ) : medicines.length === 0 ? (
        <div className="text-center py-16 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/20 space-y-3">
          <Pill className="h-12 w-12 text-slate-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
            No clinical formulations found
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            Try adjusting your search query, or clear your therapeutic category filters.
          </p>
          <button
            onClick={() => {
              setSearchQuery("");
              setSelectedCategory("");
              setRxFilter(undefined);
              setColdChainOnly(false);
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-sky-600 text-white text-xs font-semibold hover:bg-sky-700 transition-all cursor-pointer"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Reset All Filters</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {medicines.map((med) => (
            <MedicineCard key={med.id} medicine={med} />
          ))}
        </div>
      )}
    </div>
  );
}
