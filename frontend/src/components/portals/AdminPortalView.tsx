"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  RefreshCw,
  Plus,
  ShoppingCart,
  Store,
  ArrowLeft,
  X,
  MapPin,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

interface AdminPortalViewProps {
  onBackToPortals: () => void;
}

interface PharmacyShop {
  id: string;
  name: string;
  location: string;
  orders_count: number;
  gps: string;
  is_online: boolean;
  status: "active" | "inactive";
}

export function AdminPortalView({ onBackToPortals }: AdminPortalViewProps) {
  const { user, logout } = useAuthStore();
  const [stats, setStats] = useState({
    live_orders: 15,
    order_revenue: 2188.5,
    active_pharmacies: 6,
    total_pharmacies: 7,
    pending: 1
  });

  const handleGoogleSignIn = async () => {
    try {
      const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
      const res = await api.auth.getGoogleUrl(origin, "admin");
      if (res && res.url) {
        window.location.href = res.url;
      }
    } catch (e) {
      console.error("Google Auth error:", e);
    }
  };

  const [pharmacies, setPharmacies] = useState<PharmacyShop[]>([
    {
      id: "s3",
      name: "Wellness Forever — BTM",
      location: "BTM 2nd Stage, Bengaluru",
      orders_count: 57,
      gps: "12.917,77.610",
      is_online: true,
      status: "active"
    },
    {
      id: "s4",
      name: "Sri Sai Medicals — Jayanagar",
      location: "4th Block, Jayanagar, Bengaluru",
      orders_count: 63,
      gps: "12.931,77.584",
      is_online: false,
      status: "inactive"
    },
    {
      id: "s04bce527744",
      name: "Green Cross Pharmacy",
      location: "Indiranagar 100 Feet Rd",
      orders_count: 0,
      gps: "12.978,77.641",
      is_online: true,
      status: "active"
    },
    {
      id: "s44f964be3cf",
      name: "Anne medical stores",
      location: "rr nagar",
      orders_count: 0,
      gps: "12.923,77.501",
      is_online: true,
      status: "active"
    },
    {
      id: "sc4d4c0542b7",
      name: "apollo",
      location: "rv college",
      orders_count: 0,
      gps: "no GPS",
      is_online: true,
      status: "active"
    },
    {
      id: "s6062c310ca6",
      name: "anne medical",
      location: "rr nagar",
      orders_count: 0,
      gps: "no GPS",
      is_online: true,
      status: "active"
    },
    {
      id: "s44be59c92f",
      name: "Rv medicals",
      location: "Current Location (12.9235, 77.5011)",
      orders_count: 0,
      gps: "no GPS",
      is_online: true,
      status: "active"
    }
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newShopName, setNewShopName] = useState("");
  const [newShopLocation, setNewShopLocation] = useState("");
  const [newShopGps, setNewShopGps] = useState("");

  const refreshData = async () => {
    setIsRefreshing(true);
    try {
      const res = await api.admin.getAnalytics();
      if (res && res.metrics) {
        setStats({
          live_orders: res.metrics.total_orders || 15,
          order_revenue: res.metrics.total_revenue || 2188.5,
          active_pharmacies: pharmacies.filter(p => p.status === "active").length,
          total_pharmacies: pharmacies.length,
          pending: res.metrics.low_stock_alerts || 1
        });
      }
    } catch (e) {
      // Keep state
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  const handleToggleStatus = (id: string) => {
    setPharmacies(prev =>
      prev.map(p => {
        if (p.id === id) {
          const newStatus = p.status === "active" ? "inactive" : "active";
          return {
            ...p,
            status: newStatus,
            is_online: newStatus === "active"
          };
        }
        return p;
      })
    );
  };

  const handleRemovePharmacy = (id: string) => {
    setPharmacies(prev => prev.filter(p => p.id !== id));
  };

  const handleAddPharmacy = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newShopName.trim()) return;

    const newShop: PharmacyShop = {
      id: "s" + Math.random().toString(36).substring(2, 9),
      name: newShopName.trim(),
      location: newShopLocation.trim() || "Bengaluru",
      orders_count: 0,
      gps: newShopGps.trim() || "12.971,77.594",
      is_online: true,
      status: "active"
    };

    setPharmacies(prev => [newShop, ...prev]);
    setShowAddModal(false);
    setNewShopName("");
    setNewShopLocation("");
    setNewShopGps("");
  };

  const activeCount = pharmacies.filter(p => p.status === "active").length;

  return (
    <div className="relative min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-between overflow-x-hidden selection:bg-rose-500 selection:text-white">
      {/* Top Header */}
      <header className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-8 py-5 flex items-center justify-between border-b border-slate-800/40">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-rose-500 fill-rose-500/20 stroke-[2.2]" />
            <span className="text-xl font-bold tracking-tight text-white font-heading">
              Medi <span className="text-rose-500">App</span>
            </span>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-rose-950/80 text-rose-400 border border-rose-800/50">
            ADMIN
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-4 text-xs">
          {user?.email ? (
            <div className="flex items-center gap-3">
              <span className="text-slate-300 font-semibold">{user.email}</span>
              <button
                onClick={() => logout()}
                className="text-rose-400 font-semibold hover:underline cursor-pointer"
              >
                Sign out
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2.5">
              <button
                id="btn-admin-google-signin"
                onClick={handleGoogleSignIn}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700/80 hover:border-slate-600 text-slate-200 hover:text-white text-xs font-semibold transition-all cursor-pointer shadow-xs"
                title="Sign in with Hospital Admin Google Account"
              >
                <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                <span>Google Sign-In</span>
              </button>
              <button
                onClick={onBackToPortals}
                className="text-rose-400 font-semibold hover:underline cursor-pointer"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Container */}
      <main className="relative z-10 flex-1 w-full max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-7">
        {/* Subtitle & Refresh */}
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Live feed from backend store
          </span>
          <button
            onClick={refreshData}
            className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-md shadow-rose-600/20 cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* 4 Metric KPI Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5 flex items-start justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                LIVE ORDERS
              </span>
              <span className="text-2xl sm:text-3xl font-extrabold text-white">
                {stats.live_orders}
              </span>
            </div>
            <ShoppingCart className="h-5 w-5 text-cyan-500 mt-1" />
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5 flex items-start justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                ORDER REVENUE
              </span>
              <span className="text-2xl sm:text-3xl font-extrabold text-white">
                ₹{stats.order_revenue.toLocaleString()}
              </span>
            </div>
            <ShoppingCart className="h-5 w-5 text-emerald-500 mt-1" />
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5 flex items-start justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                PHARMACIES
              </span>
              <span className="text-2xl sm:text-3xl font-extrabold text-white">
                {activeCount}/{pharmacies.length}
              </span>
            </div>
            <Store className="h-5 w-5 text-purple-400 mt-1" />
          </div>

          <div className="bg-[#0b1220] border border-slate-800/80 rounded-2xl p-4 sm:p-5 flex items-start justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                PENDING
              </span>
              <span className="text-2xl sm:text-3xl font-extrabold text-white">
                {stats.pending}
              </span>
            </div>
            <Shield className="h-5 w-5 text-rose-500 mt-1" />
          </div>
        </div>

        {/* SECTION: Pharmacies Management */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-bold text-white">
              Pharmacies <span className="text-xs text-slate-400 font-normal">includes newly registered partner shops</span>
            </span>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center gap-1 transition-all shadow-md shadow-rose-600/20 cursor-pointer"
            >
              <Plus className="h-3.5 w-3.5 stroke-[3]" />
              <span>Add pharmacy</span>
            </button>
          </div>

          {/* List of Pharmacies */}
          <div className="bg-[#0b1220] border border-slate-800 rounded-2xl divide-y divide-slate-800/80 overflow-hidden shadow-xl">
            {pharmacies.map((shop) => (
              <div
                key={shop.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs hover:bg-[#0e1628] transition-colors"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-white">
                      {shop.name}
                    </span>
                    {shop.is_online ? (
                      <span className="text-[10px] font-semibold text-emerald-400">online</span>
                    ) : (
                      <span className="text-[10px] font-semibold text-slate-500">(inactive) · offline</span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {shop.location} · {shop.orders_count} orders · GPS: {shop.gps} · <span className="text-slate-500">id: {shop.id}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto">
                  <button
                    onClick={() => handleToggleStatus(shop.id)}
                    className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 font-medium text-xs cursor-pointer transition-colors"
                  >
                    {shop.status === "active" ? "Deactivate" : "Activate"}
                  </button>
                  <button
                    onClick={() => handleRemovePharmacy(shop.id)}
                    className="px-3 py-1 rounded-lg bg-rose-950/40 border border-rose-900/50 hover:bg-rose-900/50 text-rose-400 font-medium text-xs cursor-pointer transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Add Pharmacy Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs">
          <div className="bg-[#0b1220] border border-slate-800 rounded-2xl p-6 w-full max-w-md space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-base text-white">Add Partner Pharmacy</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAddPharmacy} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Pharmacy Name</label>
                <input
                  type="text"
                  required
                  value={newShopName}
                  onChange={(e) => setNewShopName(e.target.value)}
                  placeholder="e.g. MedPlus Clinic"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-rose-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Address / Area</label>
                <input
                  type="text"
                  value={newShopLocation}
                  onChange={(e) => setNewShopLocation(e.target.value)}
                  placeholder="e.g. Koramangala 5th Block, Bengaluru"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-rose-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">GPS Coordinates</label>
                <input
                  type="text"
                  value={newShopGps}
                  onChange={(e) => setNewShopGps(e.target.value)}
                  placeholder="e.g. 12.935, 77.614"
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-900 text-slate-400 hover:text-white cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold cursor-pointer"
                >
                  Add Shop
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
        MediApp Administrative Command &amp; Network Health Console
      </footer>
    </div>
  );
}
