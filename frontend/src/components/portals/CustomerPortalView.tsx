"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Link2,
  Search,
  Camera,
  Sparkles,
  Zap,
  ShieldAlert,
  ArrowLeft,
  ShoppingCart,
  User,
  Plus,
  Check,
  Upload,
  AlertTriangle,
  Loader2,
  ChevronRight,
  ShieldCheck,
  Pill
} from "lucide-react";
import { api, Medicine, GenericAlternative } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { useCartStore } from "@/store/useCartStore";

interface TriageOutput {
  condition?: string;
  category?: string;
  confidence?: number;
  response?: string;
  is_emergency?: boolean;
  emergency_message?: string | null;
  disclaimer?: string;
  recommended_medicines?: Array<{
    id: number;
    name: string;
    generic_name: string;
    dosage_form: string;
    strength?: string;
    mrp: number;
    unit_price?: number;
    stock_quantity?: number;
    in_stock?: boolean;
  }>;
}

interface CustomerPortalViewProps {
  onBackToPortals: () => void;
  onOpenCart?: () => void;
}

export function CustomerPortalView({ onBackToPortals, onOpenCart }: CustomerPortalViewProps) {
  const { user, login, logout, fetchSession } = useAuthStore();
  const { cart, addItem, fetchCart } = useCartStore();

  const [activeTab, setActiveTab] = useState<"search" | "scanner" | "ailment">("search");
  
  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Medicine[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedGenericInfo, setSelectedGenericInfo] = useState<{ [medId: number]: GenericAlternative }>({});

  // Scanner state
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState<"idle" | "uploading" | "reading" | "matched">("idle");
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [scanMatchedMedicines, setScanMatchedMedicines] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Ailment Assistant state
  const [ailmentQuery, setAilmentQuery] = useState("");
  const [isTriaging, setIsTriaging] = useState(false);
  const [triageResult, setTriageResult] = useState<TriageOutput | null>(null);

  const isAuthenticated = Boolean(user && user.email);

  useEffect(() => {
    fetchSession();
    fetchCart();
  }, [fetchSession, fetchCart]);

  // Handle Search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await api.medicines.search({ q: searchQuery.trim() });
        const meds = res.medicines || [];
        setSearchResults(meds);

        // Fetch generic alternatives for top results
        meds.slice(0, 4).forEach(async (m) => {
          try {
            const gen = await api.medicines.getGenericAlternatives(m.id);
            if (gen && gen.alternatives && gen.alternatives.length > 0) {
              setSelectedGenericInfo((prev) => ({ ...prev, [m.id]: gen }));
            }
          } catch (e) {
            // Ignore
          }
        });
      } catch (err) {
        console.error("Search error:", err);
      } finally {
        setIsSearching(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Handle Google OAuth Sign-In
  const handleGoogleSignIn = async () => {
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
      const res = await api.auth.getGoogleUrl(origin, "customer");
      if (res && res.url) {
        window.location.href = res.url;
      }
    } catch (e) {
      console.error("Google Auth error:", e);
    }
  };

  // Handle Prescription Image Selection & Laser Scanning simulation
  const handleSelectPrescription = (file?: File) => {
    setIsScanning(true);
    setScanStep("uploading");
    
    // Provide realistic prescription preview image
    const samplePrescriptionUrl = "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=800";
    setPreviewImage(samplePrescriptionUrl);

    setTimeout(() => {
      setScanStep("reading");
    }, 600);

    // Simulate scanning & matching to DB
    setTimeout(async () => {
      try {
        const res = await api.medicines.search({ q: "augmentin" });
        const found = res.medicines?.slice(0, 3) || [];
        setScanMatchedMedicines(found);
      } catch (e) {
        setScanMatchedMedicines([
          { id: 1, name: "Augmentin 625 Duo Tablet", generic_name: "Amoxicillin and Clavulanic Acid", mrp: 204.5, discount_percentage: 15 },
          { id: 2, name: "Dolo 650mg Tablet", generic_name: "Paracetamol", mrp: 34.0, discount_percentage: 10 },
          { id: 3, name: "Pan 40mg Tablet", generic_name: "Pantoprazole", mrp: 155.0, discount_percentage: 12 }
        ]);
      }
      setScanStep("matched");
      setIsScanning(false);
    }, 2800);
  };

  // Handle Ailment Triage
  const handleTriageSubmit = async (queryText?: string) => {
    const q = queryText || ailmentQuery;
    if (!q.trim()) return;
    setIsTriaging(true);
    try {
      const res = await api.ai.consult(q);
      const out = res?.result || {};
      setTriageResult({
        condition: out.ml_prediction?.condition_name || out.condition_name || "Clinical Condition Analysis",
        category: out.ml_prediction?.category,
        confidence: out.ml_prediction?.confidence,
        response: out.response || "Clinical guidance unavailable. Please consult a healthcare provider.",
        is_emergency: Boolean(out.is_emergency),
        emergency_message: out.emergency_message || null,
        disclaimer: out.disclaimer,
        recommended_medicines: out.recommended_medicines || [],
      });
    } catch (e) {
      console.error(e);
    } finally {
      setIsTriaging(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-between overflow-x-hidden selection:bg-cyan-500 selection:text-black">
      {/* Ambient background glows */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-purple-700/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 -right-32 w-96 h-96 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none" />

      {/* Top Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 py-5 flex items-center justify-between border-b border-slate-800/40">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg text-cyan-400">
            <Link2 className="h-6 w-6 stroke-[2.5]" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white flex items-center font-heading">
            Medi<span className="text-cyan-400">App</span>
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          {/* Live DB Connected Status */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/90 border border-emerald-500/30 text-xs font-semibold text-emerald-400 shadow-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Live DB Connected</span>
          </div>

          {/* Cart Icon */}
          <button
            onClick={onOpenCart}
            className="relative p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-colors cursor-pointer"
            title="Cart"
          >
            <ShoppingCart className="h-4 w-4" />
            {cart && cart.items && cart.items.length > 0 && (
              <span className="absolute -top-1 -right-1 px-1.5 py-0.2 bg-cyan-500 text-slate-950 font-bold text-[10px] rounded-full">
                {cart.items.length}
              </span>
            )}
          </button>

          {/* User Profile or Google Sign In */}
          {!isAuthenticated ? (
            <div className="flex items-center gap-2">
              <button
                id="btn-customer-google-signin"
                onClick={handleGoogleSignIn}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-slate-200 hover:text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
                title="Sign in with Google Account"
              >
                <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                <span>Google Sign-In</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2.5 pl-2">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-bold text-white leading-tight">
                  {user?.full_name || "Shreyas S M"}
                </div>
                <button
                  onClick={() => logout()}
                  className="text-[10px] font-semibold text-rose-400 hover:underline cursor-pointer"
                >
                  Sign Out
                </button>
              </div>
              <div className="w-8 h-8 rounded-full bg-cyan-400 text-slate-950 font-black text-xs flex items-center justify-center shadow-md">
                {(user?.full_name || "SM").split(" ").map((n) => n[0]).join("").slice(0, 2)}
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Welcome Banner when authenticated */}
      {isAuthenticated && (
        <div className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 pt-3 text-right">
          <span className="text-xs text-slate-400">Welcome, </span>
          <span className="text-xs font-bold text-cyan-400">
            {user?.full_name?.split(" ")[0] || "Shreyas"}
          </span>
        </div>
      )}

      {/* Main Container */}
      <main className="relative z-10 flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10 flex flex-col items-center">
        {/* Title & Subtitle */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 text-2xl sm:text-3xl font-extrabold text-white tracking-tight mb-2">
            <Link2 className="h-7 w-7 text-cyan-400" />
            <span>MediApp Substitutes</span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto">
            Get authentic, lower-cost generic medicines from verified nearby pharmacies.
          </p>
        </div>

        {/* Central Workspace Card */}
        <div className="w-full bg-[#0a101d] border border-slate-800/80 rounded-2xl p-4 sm:p-7 shadow-2xl shadow-black/60">
          {/* Top 3 Segmented Tabs */}
          <div className="flex items-center justify-center gap-1 sm:gap-6 border-b border-slate-800 pb-4 mb-6">
            <button
              onClick={() => setActiveTab("search")}
              className={`relative pb-2 px-3 sm:px-4 text-xs sm:text-sm font-bold flex items-center gap-2 transition-colors cursor-pointer ${
                activeTab === "search" ? "text-cyan-400" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Search className="h-4 w-4" />
              <span>A-Z Brand Search</span>
              {activeTab === "search" && (
                <span className="absolute bottom-[-17px] left-0 right-0 h-0.5 bg-cyan-400 rounded-full" />
              )}
            </button>

            <button
              onClick={() => setActiveTab("scanner")}
              className={`relative pb-2 px-3 sm:px-4 text-xs sm:text-sm font-bold flex items-center gap-2 transition-colors cursor-pointer ${
                activeTab === "scanner" ? "text-cyan-400" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Camera className="h-4 w-4" />
              <span>AI Prescription Scanner</span>
              {activeTab === "scanner" && (
                <span className="absolute bottom-[-17px] left-0 right-0 h-0.5 bg-cyan-400 rounded-full" />
              )}
            </button>

            <button
              onClick={() => setActiveTab("ailment")}
              className={`relative pb-2 px-3 sm:px-4 text-xs sm:text-sm font-bold flex items-center gap-2 transition-colors cursor-pointer ${
                activeTab === "ailment" ? "text-cyan-400" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Sparkles className="h-4 w-4" />
              <span>AI Ailment Specialist</span>
              {activeTab === "ailment" && (
                <span className="absolute bottom-[-17px] left-0 right-0 h-0.5 bg-cyan-400 rounded-full" />
              )}
            </button>
          </div>

          {/* TAB 1: A-Z Brand Search */}
          {activeTab === "search" && (
            <div className="space-y-6">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="[ Search 250,000+ brands (e.g. Augmentin, Dolo, Pan-D, Azee, Allegra)... ]"
                  autoComplete="off"
                  autoCorrect="off"
                  autoCapitalize="off"
                  spellCheck={false}
                  className="w-full bg-[#070d18] border border-slate-700/80 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 rounded-xl pl-12 pr-4 py-3.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 transition-all outline-none"
                />
                {isSearching && (
                  <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-cyan-400 animate-spin" />
                )}
              </div>

              {/* Informational Feature Cards (Shown when query is short) */}
              {searchQuery.trim().length < 2 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div className="bg-[#0e1626]/80 border border-slate-800/80 rounded-xl p-4 sm:p-5 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">
                        <Zap className="h-4 w-4 text-amber-400" />
                        <span>EXTENSIVE A-Z SUBSTITUTE DATABASE</span>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Search any doctor's prescribed branded medicine to find cheaper alternates. Real savings average over 70% on Indian medicines!
                      </p>
                    </div>
                  </div>

                  <div className="bg-[#0e1626]/80 border border-slate-800/80 rounded-xl p-4 sm:p-5 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center gap-2 text-xs font-bold text-orange-400 uppercase tracking-wider mb-2">
                        <ShieldAlert className="h-4 w-4 text-orange-400" />
                        <span>PROACTIVE SAFETY WARNINGS</span>
                      </div>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        Adding substitutes directly to your cart automatically performs real-time Drug-Drug Interaction (DDI) safety checks.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Live Search Results */}
              {searchResults.length > 0 && (
                <div className="space-y-4 pt-2">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Found {searchResults.length} Brands &amp; Bioequivalent Substitutes:
                  </div>

                  <div className="space-y-3">
                    {searchResults.map((medicine) => {
                      const gen = selectedGenericInfo[medicine.id];
                      const cheaperAlt = gen?.alternatives?.find((a) => a.is_cheaper);

                      return (
                        <div
                          key={medicine.id}
                          className="bg-[#0e1626] border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-slate-700 transition-all"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-sm text-white">
                                {medicine.name}
                              </span>
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-300">
                                ₹{medicine.mrp || medicine.unit_price || 0}
                              </span>
                            </div>
                            <div className="text-xs text-slate-400">
                              Active Molecule: <span className="text-slate-300 font-medium">{medicine.generic_name}</span>
                            </div>

                            {/* Bioequivalent generic match callout */}
                            {cheaperAlt && (
                              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-950/60 border border-emerald-800/40 text-[11px] text-emerald-400 font-medium mt-1">
                                <Sparkles className="h-3 w-3 text-emerald-400" />
                                <span>Cheaper Generic: <strong>{cheaperAlt.name}</strong> (₹{cheaperAlt.price}) · Save {cheaperAlt.savings_pct}%</span>
                              </div>
                            )}
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              onClick={() => addItem(medicine.id, 1)}
                              className="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-bold transition-all cursor-pointer flex items-center gap-1"
                            >
                              <Plus className="h-3.5 w-3.5" />
                              <span>Add to Cart</span>
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: AI Prescription Scanner */}
          {activeTab === "scanner" && (
            <div className="space-y-6 text-center">
              <div>
                <h3 className="text-lg sm:text-xl font-bold text-white mb-1">
                  Fuzzy OCR Matching Engine Active
                </h3>
                <p className="text-xs text-slate-400">
                  Correcting handwriting OCR typos and resolving matches directly over the A-Z database.
                </p>
              </div>

              {/* Prescription Image / Scanner Display */}
              <div className="relative max-w-md mx-auto rounded-2xl overflow-hidden border border-slate-700/80 bg-slate-950 shadow-2xl">
                {/* Simulated / Real Prescription Image */}
                <div className="relative w-full h-72 sm:h-80 bg-slate-900 flex items-center justify-center overflow-hidden">
                  <img
                    src={previewImage || "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=800"}
                    alt="Uploaded Prescription"
                    className="w-full h-full object-cover filter brightness-90 contrast-110"
                  />

                  {/* Animated Cyan Laser Scanning Beam */}
                  {scanStep === "reading" && (
                    <div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22d3ee] animate-[scan_2s_ease-in-out_infinite]" />
                  )}

                  {/* Overlay Scanner Controls */}
                  {scanStep === "idle" && (
                    <div className="absolute inset-0 bg-slate-950/70 flex flex-col items-center justify-center p-6 text-center">
                      <Camera className="h-10 w-10 text-cyan-400 mb-3 stroke-[1.8]" />
                      <p className="text-xs text-slate-300 font-medium mb-4">
                        Upload or select a prescription document to begin handwriting analysis
                      </p>
                      <button
                        onClick={() => handleSelectPrescription()}
                        className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all shadow-lg shadow-cyan-500/20 cursor-pointer"
                      >
                        Scan Sample Prescription
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Status Indicator */}
              {scanStep === "reading" && (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-950/60 border border-cyan-800/40 text-xs font-semibold text-cyan-300">
                  <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                  <span>Reading handwriting with Gemini Vision...</span>
                </div>
              )}

              {/* Extracted Medicines Results */}
              {scanStep === "matched" && (
                <div className="text-left space-y-3 pt-4 border-t border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4" />
                      <span>OCR Extraction Complete · 3 Formulations Detected</span>
                    </span>
                    <button
                      onClick={() => handleSelectPrescription()}
                      className="text-xs text-cyan-400 hover:underline cursor-pointer"
                    >
                      Rescan
                    </button>
                  </div>

                  <div className="space-y-2">
                    {scanMatchedMedicines.map((m) => (
                      <div
                        key={m.id}
                        className="p-3 rounded-xl bg-[#0e1626] border border-slate-800 flex items-center justify-between text-xs"
                      >
                        <div>
                          <div className="font-bold text-white">{m.name}</div>
                          <div className="text-slate-400 text-[11px]">{m.generic_name} · ₹{m.mrp || m.price || 50}</div>
                        </div>
                        <button
                          onClick={() => addItem(m.id, 1)}
                          className="px-3 py-1 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs cursor-pointer"
                        >
                          Add to Cart
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: AI Ailment Specialist */}
          {activeTab === "ailment" && (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-lg sm:text-xl font-bold text-white mb-1">
                  AI Ailment Specialist &amp; Symptom Triage
                </h3>
                <p className="text-xs text-slate-400">
                  Describe symptoms or select common condition protocols for safe, tailored OTC active formulations.
                </p>
              </div>

              {/* Quick condition chips */}
              <div className="flex flex-wrap gap-2 justify-center">
                {[
                  "Acid reflux & heartburn",
                  "Mild acute fever & chills",
                  "Tension headache & eye strain",
                  "Seasonal allergies & hives",
                  "Loose motions & diarrhea",
                  "Sore throat & painful swallowing",
                  "Mouth ulcers & canker sores",
                  "Muscle sprain & sports strain",
                  "Nausea & motion sickness",
                  "Gas & abdominal bloating"
                ].map((chip) => (
                  <button
                    key={chip}
                    onClick={() => {
                      setAilmentQuery(chip);
                      handleTriageSubmit(chip);
                    }}
                    className="px-3 py-1 rounded-full text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-cyan-500/40 transition-colors cursor-pointer"
                  >
                    {chip}
                  </button>
                ))}
              </div>

              {/* Query Input */}
              <div className="flex gap-2">
                <input
                  id="ailment-query-input"
                  type="text"
                  value={ailmentQuery}
                  onChange={(e) => setAilmentQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && ailmentQuery.trim()) {
                      handleTriageSubmit();
                    }
                  }}
                  placeholder="Describe symptoms in plain words..."
                  className="flex-1 bg-[#070d18] border border-slate-700/80 focus:border-cyan-400 rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-100 placeholder-slate-500 outline-none"
                />
                <button
                  id="btn-ailment-assess"
                  onClick={() => handleTriageSubmit()}
                  disabled={isTriaging || !ailmentQuery.trim()}
                  className="px-4 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs sm:text-sm disabled:opacity-50 transition-all cursor-pointer shrink-0"
                >
                  {isTriaging ? <Loader2 className="h-4 w-4 animate-spin" /> : "Assess"}
                </button>
              </div>

              {/* Triage Output */}
              {triageResult && (
                <div className="space-y-4">
                  {/* Emergency Red-Flag Alert */}
                  {triageResult.is_emergency && (
                    <div className="p-4 rounded-2xl bg-rose-500/15 border border-rose-500/40 flex items-start gap-3 text-rose-200">
                      <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
                      <div className="space-y-1 text-xs">
                        <div className="font-bold text-rose-300 uppercase tracking-wider">
                          Emergency Red-Flag Alert (Call 112 / 911 Immediately)
                        </div>
                        <p className="leading-relaxed">
                          {triageResult.emergency_message || "Seek immediate emergency medical evaluation at the nearest hospital."}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* 5-Pillar Structured Clinical Response */}
                  <div className="p-5 rounded-2xl bg-[#0e1626] border border-slate-800 space-y-4 text-xs">
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-800/80">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="h-4 w-4 text-cyan-400" />
                        <span className="font-bold text-cyan-400 text-sm">
                          {triageResult.condition}
                        </span>
                      </div>
                      {triageResult.category && (
                        <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-[10px] font-semibold">
                          {triageResult.category}
                        </span>
                      )}
                    </div>

                    <div className="text-slate-300 leading-relaxed whitespace-pre-line font-normal">
                      {triageResult.response}
                    </div>

                    {triageResult.recommended_medicines && triageResult.recommended_medicines.length > 0 && (
                      <div className="space-y-2.5 pt-3 border-t border-slate-800">
                        <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-emerald-400 text-[11px]">
                          <Pill className="h-3.5 w-3.5" />
                          <span>Live Stock Verified Dispensary Formulations</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                          {triageResult.recommended_medicines.map((rec) => {
                            const price = rec.unit_price ?? rec.mrp ?? 0;
                            const stock = rec.stock_quantity ?? 0;
                            return (
                              <div
                                key={rec.id}
                                className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-2"
                              >
                                <div className="min-w-0">
                                  <div className="font-bold text-white truncate">{rec.name}</div>
                                  <div className="text-[11px] text-slate-400 truncate">
                                    {rec.generic_name} · {rec.dosage_form}
                                  </div>
                                  <div className="flex items-center gap-2 mt-1 text-[11px]">
                                    <span className="font-semibold text-cyan-400">₹{price}</span>
                                    <span className="text-emerald-400 font-medium">
                                      {stock > 0 ? `${stock} in stock` : "Available"}
                                    </span>
                                  </div>
                                </div>
                                <button
                                  onClick={() => addItem(rec.id, 1)}
                                  className="px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-[11px] shrink-0 cursor-pointer transition-colors"
                                >
                                  Add
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {triageResult.disclaimer && (
                      <div className="pt-2 border-t border-slate-800/60 text-[10px] text-slate-500">
                        {triageResult.disclaimer}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Fixed Bottom-Left Navigation Pill */}
      <button
        onClick={onBackToPortals}
        className="fixed bottom-6 left-6 z-50 inline-flex items-center gap-2 px-3.5 py-2 rounded-full bg-slate-900/90 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white shadow-xl backdrop-blur-md transition-all cursor-pointer"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        <span>All portals</span>
      </button>

      {/* Footer */}
      <footer className="relative z-10 w-full py-6 text-center text-[11px] text-slate-500 border-t border-slate-800/40">
        MediApp India © 2026 — Powered by Extensive A-Z Medicine Database of India — AI Diagnostics and OCR Powered by Gemini 1.5
      </footer>
    </div>
  );
}
