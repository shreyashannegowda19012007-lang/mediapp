# MediApp Clinical Design System & Component Guidelines

This document outlines persistent architectural, design, and coding standards for all frontend and UI components generated within the **MediApp Healthcare Network** repository.

---

## 1. Clinical Trust Color Palette & Tokens

Always adhere to clinical-grade, high-trust color tokens:
- **Canvas & Elevation**:
  - Light: Canvas `#F8FAFC` (slate-50), Surface/Cards `#FFFFFF`, Borders `#E2E8F0` (slate-200)
  - Dark: Canvas `#070D1A`, Surface/Cards `#0F172A` (slate-900), Borders `#1E293B` (slate-800)
- **Primary Brand / Action**:
  - Sky Blue `#0284C7` (sky-600) / `#38BDF8` (sky-400 in dark mode)
- **Clinical Emerald (OTC Approved / Verified / Nominal)**:
  - Badge Background: `bg-emerald-500/10`, Text: `text-emerald-700 dark:text-emerald-400`, Border: `border-emerald-500/20`
- **Clinical Amber (Prescription Rx Required / Caution)**:
  - Badge Background: `bg-amber-500/10`, Text: `text-amber-800 dark:text-amber-400`, Border: `border-amber-500/30`
- **Clinical Cyan (Cold-Chain 2°C - 8°C Monitored)**:
  - Badge Background: `bg-cyan-500/10`, Text: `text-cyan-800 dark:text-cyan-400`, Border: `border-cyan-500/30`
- **Clinical Crimson (Rejection / Critical Restock)**:
  - Badge Background: `bg-rose-500/10`, Text: `text-rose-700 dark:text-rose-400`, Border: `border-rose-500/20`

---

## 2. Zero-Emoji Invariant

**Never use unicode emojis in code, templates, or component labels.**
- All visual metaphors must use **Lucide React** clinical vector icons (`Pill`, `ShieldCheck`, `ThermometerSnowflake`, `Sparkles`, `Truck`, `FileText`, `CheckCircle2`, `Clock`, `AlertTriangle`).
- Maintains clean, enterprise-grade hospital and clinical credibility.

---

## 3. Data Representation Standards

1. **Formulation Details**:
   - Always display both the commercial brand name and the active generic chemical molecule (e.g. *Aciloc 150mg* • *Ranitidine Hydrochloride*).
   - Display dosage form and strength (`Tablet • 150mg`).
   - Display manufacturer license identity.
2. **Pricing & Generic Savings**:
   - Display current unit price with MRP strikethrough when discounted.
   - When a cheaper bioequivalent exists, provide the `Generic Price Match` trigger calculating exact ₹ and % savings.
3. **Logistics & Cold-Chain**:
   - For insulin, vaccines, and biologics, always render the Cold-Chain Temperature Guarantee badge (`2°C - 8°C Nominal IoT Monitored`).
   - Include patient delivery OTP handoff verification to prevent medication diversion.

---

## 4. Layout & Breakpoint Guidelines

- **Container**: Use `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`.
- **Card Grids**:
  - Mobile (< 640px): 1 column
  - Tablet (640px - 1024px): 2 columns
  - Desktop (> 1024px): 3 or 4 columns
- **Dark Mode Support**:
  - Support seamless Dark, Light, and System Default toggling via `next-themes` and `.dark` class attributes.
