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
import { ROLE_DEFINITIONS, isTabAllowedForRole } from "@/lib/rbac";
import { AccessRestricted } from "@/components/auth/AccessRestricted";
import { RoleLimitsModal } from "@/components/auth/RoleLimitsModal";

export default function Home() {
  const [activeTab, setActiveTab] = useState("catalogue");
  const [isRxModalOpen, setIsRxModalOpen] = useState(false);
  const [isRoleLimitsModalOpen, setIsRoleLimitsModalOpen] = useState(false);
  const { fetchSession, activeRole } = useAuthStore();
  const { fetchCart } = useCartStore();

  const currentRoleDef = ROLE_DEFINITIONS[activeRole] || ROLE_DEFINITIONS.customer;

  useEffect(() => {
    fetchSession();
    fetchCart();
  }, [fetchSession, fetchCart]);

  // Synchronize tab if user changes role or if current tab is not allowed
  useEffect(() => {
    const targetDef = ROLE_DEFINITIONS[activeRole];
    if (targetDef && !isTabAllowedForRole(activeTab, activeRole)) {
      setActiveTab(targetDef.defaultTab);
    }
  }, [activeRole, activeTab]);

  const handleExploreCatalogue = () => {
    setActiveTab("catalogue");
    setTimeout(() => {
      const section = document.getElementById("medicine-catalogue");
      if (section) {
        section.scrollIntoView({ behavior: "smooth", block: "start" });
      }
      const searchInput = document.getElementById("search-medicines-input");
      if (searchInput) {
        searchInput.focus();
      }
    }, 50);
  };

  const isCurrentTabAllowed = isTabAllowedForRole(activeTab, activeRole);

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
        {/* Zero-Trust RBAC Guard */}
        {!isCurrentTabAllowed ? (
          <AccessRestricted
            attemptedTab={activeTab}
            currentRole={activeRole}
            onResetToDefault={() => setActiveTab(currentRoleDef.defaultTab)}
            onOpenRoleModal={() => setIsRoleLimitsModalOpen(true)}
          />
        ) : (
          <>
            {/* Render Hero Section only on Catalogue view for customers */}
            {activeTab === "catalogue" && currentRoleDef.canViewHero && (
              <HeroSection
                onOpenUploadRx={() => setIsRxModalOpen(true)}
                onNavigateTab={(tab) => setActiveTab(tab)}
                onExploreCatalogue={handleExploreCatalogue}
              />
            )}

            {/* Tab Workspace Router */}
            {activeTab === "catalogue" && <MedicineCatalogue />}
            {activeTab === "pharmacist-desk" && <PharmacistReviewDesk />}
            {activeTab === "logistics" && <OrderTrackingTimeline />}
            {activeTab === "admin-dashboard" && <AnalyticsDashboard />}
          </>
        )}
      </main>

      {/* Slide-over Cart Drawer (Customer Only) */}
      {currentRoleDef.canAccessCart && (
        <CartDrawer onOrderPlaced={() => setActiveTab("logistics")} />
      )}

      {/* Prescription Upload Modal (Customer Only) */}
      {currentRoleDef.canUploadRx && (
        <RxUploadModal
          isOpen={isRxModalOpen}
          onClose={() => setIsRxModalOpen(false)}
          onUploadSuccess={() => setActiveTab("pharmacist-desk")}
        />
      )}

      {/* Role Limits Modal (for 403 trigger fallback) */}
      <RoleLimitsModal
        isOpen={isRoleLimitsModalOpen}
        onClose={() => setIsRoleLimitsModalOpen(false)}
        onRoleSwitched={(newRole) => {
          const targetDef = ROLE_DEFINITIONS[newRole];
          if (targetDef) setActiveTab(targetDef.defaultTab);
        }}
      />

      {/* Clinical Platform Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-950/70 mt-16 text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-bold text-sm">
            <ShieldCheck className="h-4 w-4 text-sky-500" />
            <span>MediApp Healthcare Network</span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Licensed clinical pharmacy and cold-chain medicine delivery.
          </p>
          <div className="flex items-center gap-4 text-xs">
            <span className="flex items-center gap-1 text-slate-700 dark:text-slate-300">
              <Phone className="h-3.5 w-3.5 text-sky-500" />
              1800-200-MEDI
            </span>
            <span>Bengaluru 560038</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
