"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { HeroSection } from "@/components/layout/HeroSection";
import { MedicineCatalogue } from "@/components/catalogue/MedicineCatalogue";
import { PharmacistReviewDesk } from "@/components/clinical/PharmacistReviewDesk";
import { OrderTrackingTimeline } from "@/components/logistics/OrderTrackingTimeline";
import { AnalyticsDashboard } from "@/components/admin/AnalyticsDashboard";
import { RxUploadModal } from "@/components/prescriptions/RxUploadModal";
import { CartDrawer } from "@/components/cart/CartDrawer";
import { useAuthStore } from "@/store/useAuthStore";
import { useCartStore } from "@/store/useCartStore";
import { ShieldCheck, HeartHandshake, Phone, Mail, MapPin } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState("catalogue");
  const [isRxModalOpen, setIsRxModalOpen] = useState(false);
  const { fetchSession, activeRole } = useAuthStore();
  const { fetchCart } = useCartStore();

  useEffect(() => {
    fetchSession();
    fetchCart();
  }, [fetchSession, fetchCart]);

  // Synchronize tab if user changes role via header dropdown
  useEffect(() => {
    if (activeRole === "pharmacy") setActiveTab("pharmacist-desk");
    else if (activeRole === "delivery") setActiveTab("logistics");
    else if (activeRole === "admin") setActiveTab("admin-dashboard");
  }, [activeRole]);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Command Bar */}
      <Navbar
        activeTab={activeTab}
        onNavigateTab={(tab) => setActiveTab(tab)}
        onOpenUploadRx={() => setIsRxModalOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
        {/* Render Hero Section only on Catalogue view for clean executive focus */}
        {activeTab === "catalogue" && (
          <HeroSection
            onOpenUploadRx={() => setIsRxModalOpen(true)}
            onNavigateTab={(tab) => setActiveTab(tab)}
          />
        )}

        {/* Tab Workspace Router */}
        {activeTab === "catalogue" && <MedicineCatalogue />}
        {activeTab === "pharmacist-desk" && <PharmacistReviewDesk />}
        {activeTab === "logistics" && <OrderTrackingTimeline />}
        {activeTab === "admin-dashboard" && <AnalyticsDashboard />}
      </main>

      {/* Slide-over Cart Drawer */}
      <CartDrawer onOrderPlaced={() => setActiveTab("logistics")} />

      {/* Prescription Upload Modal */}
      <RxUploadModal
        isOpen={isRxModalOpen}
        onClose={() => setIsRxModalOpen(false)}
        onUploadSuccess={() => setActiveTab("pharmacist-desk")}
      />

      {/* Clinical Platform Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-950/70 mt-16 text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-bold text-sm">
              <ShieldCheck className="h-5 w-5 text-sky-500" />
              <span>MediApp Healthcare Network</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              Licensed clinical pharmacy and cold-chain distribution platform adhering to CDSCO regulations and WHO Good Distribution Practices.
            </p>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider text-[11px]">
              Clinical Services
            </h4>
            <ul className="space-y-1 text-[11px]">
              <li>Bioequivalent Generic Price-Match</li>
              <li>Doctor Prescription OCR Verification</li>
              <li>Cold-Chain Biologics Fulfillment (2°C - 8°C)</li>
              <li>Hyperlocal Express Dispatch (45 Min)</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider text-[11px]">
              Licensed Dispensaries
            </h4>
            <ul className="space-y-1 text-[11px]">
              <li>Apollo Clinical Hub (Central Bengaluru)</li>
              <li>MedPlus Pharmacy Station (Indiranagar)</li>
              <li>Fortis Hospital Partner Dispensary</li>
              <li>Manipal Cold-Chain Distribution Depot</li>
            </ul>
          </div>

          <div className="space-y-2">
            <h4 className="font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider text-[11px]">
              Clinical Emergency Contact
            </h4>
            <div className="space-y-1 text-[11px]">
              <div className="flex items-center gap-1.5">
                <Phone className="h-3.5 w-3.5 text-sky-500" />
                <span>Helpline: 1800-200-MEDI (24/7 Toll Free)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Mail className="h-3.5 w-3.5 text-sky-500" />
                <span>clinical.care@mediapp.local</span>
              </div>
              <div className="flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-sky-500" />
                <span>HAL Old Airport Rd, Bengaluru, Karnataka 560038</span>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-200/60 dark:border-slate-800/60 py-4 text-center text-[10px] text-slate-400">
          MediApp Clinical Architecture • All trademarks and pharmaceutical brands are property of their respective manufacturers.
        </div>
      </footer>
    </div>
  );
}
