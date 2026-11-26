"use client";

import React, { useState, useEffect } from "react";
import {
  Link2,
  RefreshCw,
  Search,
  Check,
  CheckCircle2,
  Clock,
  Package,
  Truck,
  ArrowLeft,
  Plus,
  Minus,
  Sparkles
} from "lucide-react";
import { api, Order } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

interface PharmacyPortalViewProps {
  onBackToPortals: () => void;
}

interface InventoryItem {
  id: number;
  name: string;
  generic_name: string;
  category: string;
  price: number;
  stock: number;
  is_stocked: boolean;
}

export function PharmacyPortalView({ onBackToPortals }: PharmacyPortalViewProps) {
  const { user, logout, fetchSession } = useAuthStore();
  const [orders, setOrders] = useState<any[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [searchFilter, setSearchFilter] = useState("");
  const [isLoadingOrders, setIsLoadingOrders] = useState(false);
  const [activeStep, setActiveStep] = useState<number>(3); // 1: Accepted, 2: Packing, 3: Ready for pickup, 4: Picked up

  const handleGoogleSignIn = async () => {
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
      const res = await api.auth.getGoogleUrl(origin, "pharmacy");
      if (res && res.url) {
        window.location.href = res.url;
      }
    } catch (e) {
      console.error("Google Auth error:", e);
    }
  };

  // Initial Mock / Seed Inventory items from Screenshot 4
  const defaultInventory: InventoryItem[] = [
    { id: 101, name: "Amlong 5", generic_name: "Amlodipine 5mg", category: "Antihypertensive", price: 42, stock: 40, is_stocked: true },
    { id: 102, name: "Mox 500", generic_name: "Amoxicillin 500mg", category: "Antibiotic", price: 60, stock: 25, is_stocked: true },
    { id: 103, name: "Ecosprin 75", generic_name: "Aspirin 75mg", category: "Antiplatelet", price: 12, stock: 0, is_stocked: true },
    { id: 104, name: "Atorva 10", generic_name: "Atorvastatin 10mg", category: "Lipid-lowering", price: 56, stock: 60, is_stocked: true },
    { id: 105, name: "Augmentin 625 Duo", generic_name: "Amoxicillin + Clavulanate", category: "Antibiotic", price: 204.5, stock: 18, is_stocked: true },
    { id: 106, name: "Dolo 650mg", generic_name: "Paracetamol", category: "Antipyretic", price: 34, stock: 120, is_stocked: true },
  ];

  const fetchOrders = async () => {
    setIsLoadingOrders(true);
    try {
      const res = await api.orders.list();
      if (res && res.orders && res.orders.length > 0) {
        setOrders(res.orders);
      } else {
        // High fidelity sample order from Screenshot 4
        setOrders([
          {
            id: "MEDI306374",
            customer_name: "Shreyas S M",
            location: "rr nagar",
            distance: "2.5 km",
            items_count: 4,
            total_amount: 549.5,
            status: "READY_FOR_PICKUP"
          }
        ]);
      }
    } catch (err) {
      setOrders([
        {
          id: "MEDI306374",
          customer_name: "Shreyas S M",
          location: "rr nagar",
          distance: "2.5 km",
          items_count: 4,
          total_amount: 549.5,
          status: "READY_FOR_PICKUP"
        }
      ]);
    } finally {
      setIsLoadingOrders(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    setInventory(defaultInventory);
  }, []);

  // Inventory Stock Stepper Handlers
  const handleStockChange = (id: number, delta: number) => {
    setInventory(prev =>
      prev.map(item => {
        if (item.id === id) {
          const newStock = Math.max(0, item.stock + delta);
          return { ...item, stock: newStock };
        }
        return item;
      })
    );
  };

  const handleStockToggle = (id: number) => {
    setInventory(prev =>
      prev.map(item => {
        if (item.id === id) {
          return { ...item, is_stocked: !item.is_stocked };
        }
        return item;
      })
    );
  };

  const filteredInventory = inventory.filter(item =>
    item.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    item.generic_name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    item.category.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="relative min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-between overflow-x-hidden selection:bg-purple-500 selection:text-white">
      {/* Top Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 py-5 flex items-center justify-between border-b border-slate-800/40">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Link2 className="h-6 w-6 text-cyan-400 stroke-[2.5]" />
            <span className="text-xl font-bold tracking-tight text-white font-heading">
              MediApp
            </span>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-purple-950/80 text-purple-400 border border-purple-800/50">
            PHARMACY PARTNER
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span>Online</span>
            <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500 inline-block" />
          </div>
          {user?.email ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
              <div className="text-right hidden sm:block">
                <span className="font-semibold text-white block text-xs">{user.full_name || "Anne medical stores"}</span>
                <span className="text-[10px] text-emerald-400 block">{user.email}</span>
              </div>
              <button
                onClick={() => logout()}
                className="px-2.5 py-1 rounded-lg border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 font-semibold text-[11px] transition-colors cursor-pointer"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2.5">
              <div className="text-slate-400 hidden sm:block">
                <span className="font-semibold text-white">Anne medical stores</span>
                <span className="text-slate-500 text-[11px] block text-right">rr nagar</span>
              </div>
              <button
                id="btn-pharmacy-google-signin"
                onClick={handleGoogleSignIn}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-slate-200 hover:text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
                title="Sign in with Pharmacy Google Account"
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
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-7">
        {/* 4 Metric KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              ORDERS SEEN
            </span>
            <span className="text-2xl sm:text-3xl font-extrabold text-white">
              {orders.length}
            </span>
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              ACCEPTED
            </span>
            <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
              {orders.length > 0 ? "1" : "0"}
            </span>
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              MISSED
            </span>
            <span className="text-2xl sm:text-3xl font-extrabold text-rose-500">
              0
            </span>
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              REVENUE
            </span>
            <span className="text-2xl sm:text-3xl font-extrabold text-purple-400">
              ₹549.5
            </span>
          </div>
        </div>

        {/* SECTION 1: Live Orders */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white">
                Live orders
              </span>
              <span className="text-xs text-slate-400 font-normal">
                nearest to your GPS
              </span>
            </div>
            <button
              onClick={fetchOrders}
              className="px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-purple-600/20 cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isLoadingOrders ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>

          {/* Active Order Card */}
          {orders.map((ord, idx) => (
            <div
              key={ord.id || idx}
              className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-5 space-y-4 shadow-xl"
            >
              <div className="flex items-center justify-between text-xs sm:text-sm">
                <span className="font-bold text-white">
                  Order #{ord.id} · <span className="text-slate-400 font-normal">{ord.distance || "2.5 km"}</span>
                </span>
                <span className="text-xs text-slate-300 font-semibold">
                  {ord.items_count || 4} items · <strong className="text-white">₹{ord.total_amount || 549.5}</strong>
                </span>
              </div>

              <div className="text-xs text-slate-400">
                {ord.customer_name || "Shreyas S M"} · {ord.location || "rr nagar"}
              </div>

              {/* 4-Step Milestone Stepper */}
              <div className="flex items-center gap-2 sm:gap-4 overflow-x-auto py-2">
                {/* Step 1: Accepted */}
                <button
                  onClick={() => setActiveStep(1)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer transition-all shrink-0 ${
                    activeStep >= 1
                      ? "bg-indigo-600 text-white border border-indigo-500"
                      : "bg-slate-900 text-slate-500 border border-slate-800"
                  }`}
                >
                  <Check className="h-3.5 w-3.5 stroke-[3]" />
                  <span>Accepted</span>
                </button>

                {/* Step 2: Packing */}
                <button
                  onClick={() => setActiveStep(2)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer transition-all shrink-0 ${
                    activeStep >= 2
                      ? "bg-indigo-600 text-white border border-indigo-500"
                      : "bg-slate-900 text-slate-500 border border-slate-800"
                  }`}
                >
                  <Check className="h-3.5 w-3.5 stroke-[3]" />
                  <span>Packing</span>
                </button>

                {/* Step 3: Ready for pickup */}
                <button
                  onClick={() => setActiveStep(3)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer transition-all shrink-0 ${
                    activeStep >= 3
                      ? "bg-indigo-600 text-white border border-indigo-500"
                      : "bg-slate-900 text-slate-500 border border-slate-800"
                  }`}
                >
                  <Check className="h-3.5 w-3.5 stroke-[3]" />
                  <span>Ready for pickup</span>
                </button>

                {/* Step 4: Picked up */}
                <button
                  onClick={() => setActiveStep(4)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer transition-all shrink-0 ${
                    activeStep >= 4
                      ? "bg-indigo-600 text-white border border-indigo-500"
                      : "bg-slate-900 text-slate-500 border border-slate-800"
                  }`}
                >
                  <span className="w-3.5 h-3.5 rounded-full border border-slate-500 inline-block" />
                  <span>Picked up</span>
                </button>
              </div>

              {/* Status Note */}
              <div className="text-xs font-semibold text-emerald-400">
                Ready - visible to delivery partners
              </div>
            </div>
          ))}
        </div>

        {/* SECTION 2: Daily Inventory */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white">
                Daily inventory
              </span>
              <span className="text-xs text-slate-400 font-normal">
                A-Z medicine database
              </span>
            </div>
            <span className="text-xs text-slate-400">
              Not yet submitted today
            </span>
          </div>

          {/* Search Box */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search medicines (brand or generic)..."
              className="w-full bg-[#0b1220] border border-slate-800 rounded-xl pl-11 pr-4 py-3 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-purple-500 transition-colors"
            />
          </div>

          {/* Inventory Items List */}
          <div className="bg-[#0b1220] border border-slate-800 rounded-2xl divide-y divide-slate-800/80 overflow-hidden">
            {filteredInventory.map((item) => (
              <div
                key={item.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs hover:bg-[#0e1628] transition-colors"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-white">
                      {item.name}
                    </span>
                    <span className="text-slate-400 text-xs">
                      ₹{item.price}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {item.generic_name} · <span className="text-slate-500">{item.category}</span>
                  </div>
                </div>

                <div className="flex items-center gap-4 self-end sm:self-auto">
                  {/* Stepper */}
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleStockChange(item.id, -1)}
                      className="p-1 rounded-md bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 cursor-pointer"
                    >
                      <Minus className="h-3 w-3" />
                    </button>
                    <span
                      className={`min-w-9 py-1 px-2 text-center rounded-md text-xs font-mono font-bold ${
                        item.stock === 0
                          ? "bg-rose-950/40 text-rose-400 border border-rose-500/80"
                          : "bg-slate-900 text-slate-100 border border-slate-800"
                      }`}
                    >
                      {item.stock}
                    </span>
                    <button
                      onClick={() => handleStockChange(item.id, 1)}
                      className="p-1 rounded-md bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 cursor-pointer"
                    >
                      <Plus className="h-3 w-3" />
                    </button>
                  </div>

                  {/* Stocked Checkbox */}
                  <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={item.is_stocked}
                      onChange={() => handleStockToggle(item.id)}
                      className="rounded border-slate-700 text-purple-600 focus:ring-0 cursor-pointer"
                    />
                    <span className="text-[11px] font-medium">Stocked</span>
                  </label>
                </div>
              </div>
            ))}
          </div>
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
      <footer className="relative z-10 w-full py-5 text-center text-[11px] text-slate-600 border-t border-slate-800/40">
        MediApp Pharmacy Fulfillment Engine · A-Z Dispensary Management
      </footer>
    </div>
  );
}
