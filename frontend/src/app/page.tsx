"use client";

import React, { useState, useEffect } from "react";
import { PortalLandingView } from "@/components/portals/PortalLandingView";
import { CustomerPortalView } from "@/components/portals/CustomerPortalView";
import { PharmacyPortalView } from "@/components/portals/PharmacyPortalView";
import { AdminPortalView } from "@/components/portals/AdminPortalView";
import { DeliveryPortalView } from "@/components/portals/DeliveryPortalView";
import { CartDrawer } from "@/components/cart/CartDrawer";
import { RxUploadModal } from "@/components/prescriptions/RxUploadModal";
import { useAuthStore } from "@/store/useAuthStore";
import { useCartStore } from "@/store/useCartStore";

export type PortalType = "landing" | "customer" | "pharmacy" | "admin" | "delivery";

export default function Home() {
  const [currentPortal, setCurrentPortal] = useState<PortalType>("landing");
  const [isRxModalOpen, setIsRxModalOpen] = useState(false);
  const [authNotice, setAuthNotice] = useState<string | null>(null);
  const { fetchSession, switchRole } = useAuthStore();
  const { fetchCart, isOpen: isCartOpen, setIsOpen: setIsCartOpen } = useCartStore();

  useEffect(() => {
    // Check for Google OAuth callback parameters
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const loginSuccess = params.get("login_success");
      const token = params.get("token");
      const role = params.get("role");
      const authError = params.get("auth_error");

      if (token) {
        localStorage.setItem("mediapp_token", token);
      }

      if (loginSuccess) {
        if (role === "customer" || !role) {
          setCurrentPortal("customer");
        } else if (role === "pharmacy" || role === "delivery" || role === "admin") {
          setCurrentPortal(role as PortalType);
        }
        fetchSession();
        fetchCart();
        window.history.replaceState({}, document.title, window.location.pathname);
      } else if (authError) {
        setAuthNotice(authError);
        console.warn("MediApp Auth Notice:", authError);
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }

    fetchSession();
    fetchCart();
  }, [fetchSession, fetchCart]);

  const handleSelectPortal = async (portal: "customer" | "pharmacy" | "admin" | "delivery") => {
    setCurrentPortal(portal);
    // Align active role in auth store
    try {
      await switchRole(portal);
    } catch (e) {
      // Ignore
    }
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 font-sans">
      {authNotice && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-lg w-full px-4">
          <div className="bg-[#0f172a]/95 border border-amber-500/40 text-amber-200 px-4 py-3 rounded-xl shadow-2xl flex items-center justify-between text-xs font-semibold backdrop-blur-md">
            <span>Authentication Notice: {authNotice}</span>
            <button
              onClick={() => setAuthNotice(null)}
              className="text-slate-400 hover:text-white ml-3 text-sm font-bold cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>
      )}
      {/* 1. Landing Page with 4 Portal Cards */}
      {currentPortal === "landing" && (
        <PortalLandingView onSelectPortal={handleSelectPortal} />
      )}

      {/* 2. Customer Portal (A-Z Brand Search, AI Scanner, AI Ailment Specialist) */}
      {currentPortal === "customer" && (
        <CustomerPortalView
          onBackToPortals={() => setCurrentPortal("landing")}
          onOpenCart={() => setIsCartOpen(true)}
        />
      )}

      {/* 3. Pharmacy Partner Portal (Live GPS Orders, Stepper & Daily Inventory) */}
      {currentPortal === "pharmacy" && (
        <PharmacyPortalView onBackToPortals={() => setCurrentPortal("landing")} />
      )}

      {/* 4. Admin Portal (Live Feed, Stats, Partner Pharmacies List & Management) */}
      {currentPortal === "admin" && (
        <AdminPortalView onBackToPortals={() => setCurrentPortal("landing")} />
      )}

      {/* 5. Delivery Partner Portal (Pending Deliveries, OTP Verification & Earnings Chart) */}
      {currentPortal === "delivery" && (
        <DeliveryPortalView onBackToPortals={() => setCurrentPortal("landing")} />
      )}

      {/* Slide-over Cart Drawer for Customer Checkout */}
      {currentPortal === "customer" && (
        <CartDrawer
          onOrderPlaced={() => {
            setIsCartOpen(false);
          }}
          onOpenUploadRx={() => setIsRxModalOpen(true)}
        />
      )}

      {/* Prescription Upload Modal */}
      {isRxModalOpen && (
        <RxUploadModal
          isOpen={isRxModalOpen}
          onClose={() => setIsRxModalOpen(false)}
          onUploadSuccess={() => {
            setIsRxModalOpen(false);
          }}
        />
      )}
    </div>
  );
}
