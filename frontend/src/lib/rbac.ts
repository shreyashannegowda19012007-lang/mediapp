export type RoleType = "customer" | "pharmacy" | "delivery" | "admin";

export interface AllowedTab {
  id: string;
  label: string;
}

export interface RoleDefinition {
  id: RoleType;
  label: string;
  roleTitle: string;
  badge: string;
  description: string;
  scopes: string[];
  allowedTabs: AllowedTab[];
  defaultTab: string;
  canAccessCart: boolean;
  canUploadRx: boolean;
  canViewHero: boolean;
}

export const ROLE_DEFINITIONS: Record<RoleType, RoleDefinition> = {
  customer: {
    id: "customer",
    label: "Customer / Patient",
    roleTitle: "Healthcare Consumer",
    badge: "Patient Account",
    description: "Browse verified medicines, view bioequivalent generic savings, upload personal prescriptions, and track deliveries.",
    scopes: ["read:catalogue", "write:cart", "create:prescription", "read:own_orders"],
    allowedTabs: [
      { id: "catalogue", label: "Medicine Catalogue" },
      { id: "logistics", label: "My Orders & Tracking" },
    ],
    defaultTab: "catalogue",
    canAccessCart: true,
    canUploadRx: true,
    canViewHero: true,
  },
  pharmacy: {
    id: "pharmacy",
    label: "Clinical Pharmacist",
    roleTitle: "Licensed Pharmacist",
    badge: "Dispensary Station #04",
    description: "Audit prescription documents, verify active molecules and dosages, approve or reject prescriptions with clinical rationale, and inspect formulary stock.",
    scopes: ["read:prescriptions", "verify:prescription", "reject:prescription", "read:inventory"],
    allowedTabs: [
      { id: "pharmacist-desk", label: "Pharmacist Verification Desk" },
      { id: "catalogue", label: "Formulary Lookup" },
    ],
    defaultTab: "pharmacist-desk",
    canAccessCart: false,
    canUploadRx: false,
    canViewHero: false,
  },
  delivery: {
    id: "delivery",
    label: "Delivery Rider",
    roleTitle: "Cold-Chain Fleet Courier",
    badge: "Fleet Unit #CC-842",
    description: "Access assigned transit dispatches, inspect IoT temperature telemetry (2°C - 8°C), and verify patient OTP for medication handoff.",
    scopes: ["read:delivery_queue", "verify:otp_handoff", "read:temperature_telemetry"],
    allowedTabs: [
      { id: "logistics", label: "Delivery Fleet & Tracking" },
    ],
    defaultTab: "logistics",
    canAccessCart: false,
    canUploadRx: false,
    canViewHero: false,
  },
  admin: {
    id: "admin",
    label: "Hospital HQ Admin",
    roleTitle: "Executive Oversight",
    badge: "Hospital HQ",
    description: "Monitor hospital fulfillment KPIs, dispatch velocity, cold-chain regulatory compliance, generic cost savings impact, and partner dispensaries.",
    scopes: ["read:hospital_analytics", "manage:network", "read:audit_logs", "read:all_telemetry"],
    allowedTabs: [
      { id: "admin-dashboard", label: "Hospital Analytics & Oversight" },
      { id: "catalogue", label: "Network Formulary" },
    ],
    defaultTab: "admin-dashboard",
    canAccessCart: false,
    canUploadRx: false,
    canViewHero: false,
  },
};

export function isTabAllowedForRole(tabId: string, role: RoleType): boolean {
  const def = ROLE_DEFINITIONS[role];
  if (!def) return false;
  return def.allowedTabs.some((t) => t.id === tabId);
}
