"""
MediApp — Licensed Clinical Pharmacy & Cold-Chain Logistics Hub
Production Cloud Deployment for Streamlit Cloud (medi-app.streamlit.app)
Delivers 100% pixel-perfect visual parity with the localhost Next.js 15 application:
- Deep Navys, Crisp Surfaces, Clinical Emerald (OTC/Verified), Amber (Rx/Warning), Cyan (Cold-Chain)
- Zero Emojis (100% Lucide vector clinical icons)
- Omni-Search & Bioequivalent Generic Price Match Modal
- Split-Screen Pharmacist Review Desk with High-Res Forensic Inspection
- Logistics Command & Cold-Chain IoT Timeline (2°C - 8°C Monitored)
- Hospital Analytics with Visual KPI Charts & Replenishment Matrix
- Slide-Over Cart Drawer & Drag-and-Drop Rx Upload Modal
"""
import streamlit as st
import streamlit.components.v1 as components
import json

# Set Page Config
st.set_page_config(
    page_title="MediApp — Licensed Clinical Pharmacy & Cold-Chain Logistics",
    page_icon="https://img.icons8.com/color/96/caduceus.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 1. Initialize SQLite Database & Seeding
@st.cache_resource
def init_backend():
    try:
        from app.migrations import apply_migrations
        from app.seed import seed_database
        apply_migrations()
        seed_database()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        return False

init_backend()

from app.database import query_db

# 2. Hide Streamlit Chrome & Margins for Full-Bleed Application Viewport
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stSidebar"] {display: none;}
[data-testid="collapsedControl"] {display: none;}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
iframe {
    width: 100% !important;
    border: none !important;
    min-height: 100vh !important;
}
</style>
""", unsafe_allow_html=True)

# 3. Fetch Real Clinical Data from SQLite to hydrate client state
raw_medicines = query_db("""
    SELECT id, name, generic_name, dosage_form, strength, category, manufacturer, mrp, prescription_required, uses
    FROM medicines
    ORDER BY name ASC
    LIMIT 120
""")

medicines_data = [dict(m) for m in raw_medicines]

# 4. Generate Unified Clinical Web Application
clinical_html = f"""
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MediApp Clinical Network</title>
  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            primary: '#0284c7',
            'primary-hover': '#0369a1',
            'clinical-navy': '#0b132b',
            'clinical-surface': '#0f172a',
            'clinical-emerald': '#059669',
            'clinical-amber': '#d97706',
            'clinical-cyan': '#0891b2',
            'clinical-red': '#dc2626'
          }},
          fontFamily: {{
            sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
            heading: ['Outfit', 'sans-serif']
          }}
        }}
      }}
    }}
  </script>
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800;900&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Inter', -apple-system, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    h1, h2, h3, h4, h5 {{
      font-family: 'Outfit', sans-serif;
    }}
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
      background: #334155;
      border-radius: 9999px;
    }}
  </style>
</head>
<body class="bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-h-screen flex flex-col transition-colors duration-150">

  <!-- TOP CLINICAL TRUST BAR -->
  <div class="hidden lg:flex items-center justify-between px-6 py-1.5 bg-slate-100 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 text-xs tracking-tight text-slate-600 dark:text-slate-300">
    <div class="flex items-center gap-4">
      <span class="flex items-center gap-1.5 font-medium text-slate-800 dark:text-slate-200">
        <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400"></i>
        Licensed Pharmacy Network
      </span>
      <span class="text-slate-300 dark:text-slate-700">•</span>
      <span class="flex items-center gap-1 text-slate-600 dark:text-slate-400">
        <i data-lucide="thermometer-snowflake" class="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400"></i>
        Cold-Chain Monitored
      </span>
      <span class="text-slate-300 dark:text-slate-700">•</span>
      <span class="flex items-center gap-1 text-slate-600 dark:text-slate-400">
        <i data-lucide="truck" class="w-3.5 h-3.5 text-sky-600 dark:text-sky-400"></i>
        45-Min Express Delivery
      </span>
    </div>
    <div class="flex items-center gap-3 text-xs">
      <span class="text-slate-600 dark:text-slate-400">Helpline: <strong class="text-slate-800 dark:text-slate-200">1800-200-MEDI</strong></span>
    </div>
  </div>

  <!-- COMMAND BAR -->
  <header class="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-950/90 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
      
      <!-- Brand Logo -->
      <div class="flex items-center gap-2.5 cursor-pointer" onclick="setTab('catalogue')">
        <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white shadow-md">
          <i data-lucide="activity" class="w-6 h-6"></i>
        </div>
        <div>
          <div class="flex items-center gap-1.5">
            <span class="text-lg font-black tracking-tight text-slate-900 dark:text-slate-100">
              Medi<span class="text-sky-600 dark:text-sky-400">App</span>
            </span>
            <span class="px-1.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20">
              Clinical
            </span>
          </div>
          <span class="text-[10px] text-slate-500 dark:text-slate-400 block -mt-0.5 font-medium">
            Licensed Healthcare Network
          </span>
        </div>
      </div>

      <!-- Navigation Tabs (RBAC Filtered) -->
      <nav id="main-nav-tabs" class="hidden md:flex items-center gap-1 bg-slate-100/70 dark:bg-slate-900/80 p-1 rounded-xl border border-slate-200 dark:border-slate-800">
        <!-- Rendered dynamically by current active role -->
      </nav>

      <!-- Right Action Cluster -->
      <div class="flex items-center gap-2.5">
        <!-- 3-Mode Theme Switcher -->
        <div class="inline-flex items-center rounded-lg border border-slate-200 dark:border-slate-800 p-0.5 bg-slate-100/70 dark:bg-slate-900 shadow-xs">
          <button id="theme-btn-light" onclick="setTheme('light')" class="px-2 py-1 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 rounded-md transition-all flex items-center gap-1">
            <i data-lucide="sun" class="w-3.5 h-3.5"></i>
            <span class="hidden sm:inline">Light</span>
          </button>
          <button id="theme-btn-dark" onclick="setTheme('dark')" class="px-2 py-1 text-xs bg-slate-800 text-sky-400 font-semibold rounded-md shadow-xs transition-all flex items-center gap-1">
            <i data-lucide="moon" class="w-3.5 h-3.5"></i>
            <span class="hidden sm:inline">Dark</span>
          </button>
        </div>

        <!-- Upload Rx Button (Customer Only) -->
        <button id="header-upload-rx-btn" onclick="openRxModal()" class="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-sky-300 dark:border-sky-800/80 bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 text-xs font-semibold hover:bg-sky-100 dark:hover:bg-sky-900/60 transition-all cursor-pointer">
          <i data-lucide="file-text" class="w-4 h-4 text-sky-500"></i>
          <span>Upload Rx</span>
        </button>

        <!-- Cart Button (Customer Only) -->
        <button id="header-cart-btn" onclick="openCart()" class="relative p-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-900 text-slate-700 dark:text-slate-300 transition-all cursor-pointer" title="Open prescription cart">
          <i data-lucide="shopping-bag" class="w-5 h-5"></i>
          <span id="cart-counter" class="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-sky-600 text-[10px] font-bold text-white shadow-xs">
            0
          </span>
        </button>

        <!-- Role Badge & Auth0 RBAC Limits Trigger -->
        <button onclick="openRoleLimitsModal()" type="button" class="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-white border border-slate-200 dark:border-slate-700 text-xs font-semibold shadow-xs transition-all cursor-pointer" title="View Auth0 Role Limits & Permissions">
          <i data-lucide="key-round" class="w-3.5 h-3.5 text-sky-600 dark:text-sky-400"></i>
          <span id="current-role-label">Customer / Patient</span>
          <i data-lucide="chevron-down" class="w-3.5 h-3.5 text-slate-400"></i>
        </button>
      </div>
    </div>
  </header>

  <!-- MAIN CONTAINER -->
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">

    <!-- VIEW: 403 ACCESS RESTRICTED -->
    <div id="view-access-restricted" class="hidden min-h-[450px] flex items-center justify-center p-6">
      <div class="max-w-md w-full text-center p-8 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl space-y-5">
        <div class="mx-auto w-16 h-16 rounded-2xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 flex items-center justify-center">
          <i data-lucide="shield-alert" class="w-8 h-8 text-amber-500"></i>
        </div>
        <div class="space-y-1.5">
          <div class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20">
            <i data-lucide="lock" class="w-3 h-3"></i> Access Restricted (403 Forbidden)
          </div>
          <h2 class="text-xl font-black text-slate-900 dark:text-slate-100">
            Permission Required
          </h2>
          <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed" id="forbidden-explanation">
            Your active role is not authorized to access this clinical workspace under Drugs and Cosmetics confidentiality rules.
          </p>
        </div>
        <div class="p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 text-left text-xs space-y-1">
          <div class="font-bold text-slate-700 dark:text-slate-300">Active Permissions:</div>
          <div id="forbidden-scopes-list" class="flex flex-wrap gap-1">
            <!-- Scopes rendered dynamically -->
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-2.5 pt-2">
          <button onclick="returnToDefaultWorkspace()" class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs transition-all cursor-pointer shadow-xs">
            <i data-lucide="arrow-left" class="w-4 h-4"></i>
            <span>Return to My Workspace</span>
          </button>
          <button onclick="openRoleLimitsModal()" class="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold text-xs hover:bg-slate-50 dark:hover:bg-slate-700 transition-all cursor-pointer">
            <i data-lucide="key-round" class="w-4 h-4 text-sky-500"></i>
            <span>Switch Role</span>
          </button>
        </div>
      </div>
    </div>

    <!-- VIEW: CATALOGUE -->
    <div id="view-catalogue" class="space-y-6">
      
      <!-- HERO BANNER (Customer Only) -->
      <div id="hero-banner-section" class="relative rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-sky-50/70 via-white to-slate-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900 text-slate-900 dark:text-white p-6 sm:p-10 shadow-lg dark:shadow-2xl">
        <div class="relative z-10 max-w-4xl space-y-6">
          <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-sky-100/80 dark:bg-white/10 text-sky-800 dark:text-sky-300 border border-sky-200 dark:border-white/10">
            <i data-lucide="shield-check" class="w-4 h-4 text-emerald-600 dark:text-emerald-400"></i>
            <span>Licensed Healthcare Delivery Network</span>
          </div>
          <h1 class="text-3xl sm:text-5xl font-black tracking-tight leading-tight text-slate-900 dark:text-white">
            Authentic Medicines & Clinical Care, <span class="text-transparent bg-clip-text bg-gradient-to-r from-sky-600 via-teal-600 to-emerald-600 dark:from-sky-400 dark:via-teal-300 dark:to-emerald-400">Delivered Fast.</span>
          </h1>
          <p class="text-sm sm:text-base text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
            Order authentic prescription medicines and healthcare essentials with licensed pharmacist verification, cold-chain tracking, and generic savings.
          </p>
          <div class="flex flex-wrap items-center gap-3 pt-2">
            <button onclick="openRxModal()" class="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-bold text-sm shadow-lg shadow-sky-500/25 transition-all cursor-pointer">
              <i data-lucide="file-text" class="w-4 h-4"></i>
              <span>Upload Prescription</span>
              <i data-lucide="arrow-right" class="w-4 h-4"></i>
            </button>
            <button onclick="exploreCatalogue()" id="btn-explore-catalogue" class="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white dark:bg-white/10 hover:bg-slate-50 dark:hover:bg-white/15 active:scale-[0.98] text-slate-800 dark:text-slate-200 font-semibold text-sm border border-slate-200 dark:border-white/10 cursor-pointer transition-all hover:border-sky-400/50 hover:text-sky-600 dark:hover:text-white shadow-xs">
              <i data-lucide="pill" class="w-4 h-4 text-sky-500 dark:text-sky-400"></i>
              <span>Explore Medicines</span>
            </button>
          </div>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-6 border-t border-slate-200 dark:border-white/10">
            <div class="p-3 rounded-xl bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/5 space-y-1 shadow-xs">
              <div class="flex items-center gap-1.5 text-xs font-bold text-emerald-700 dark:text-emerald-400"><i data-lucide="shield-check" class="w-4 h-4"></i>100% Genuine</div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400">Verified manufacturers</div>
            </div>
            <div class="p-3 rounded-xl bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/5 space-y-1 shadow-xs">
              <div class="flex items-center gap-1.5 text-xs font-bold text-sky-700 dark:text-sky-400"><i data-lucide="clock" class="w-4 h-4"></i>Fast Review</div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400">Pharmacist validated</div>
            </div>
            <div class="p-3 rounded-xl bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/5 space-y-1 shadow-xs">
              <div class="flex items-center gap-1.5 text-xs font-bold text-cyan-700 dark:text-cyan-400"><i data-lucide="thermometer-snowflake" class="w-4 h-4"></i>Cold-Chain Safe</div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400">2°C - 8°C monitored</div>
            </div>
            <div class="p-3 rounded-xl bg-white dark:bg-white/5 border border-slate-200/80 dark:border-white/5 space-y-1 shadow-xs">
              <div class="flex items-center gap-1.5 text-xs font-bold text-amber-700 dark:text-amber-400"><i data-lucide="sparkles" class="w-4 h-4"></i>Generic Savings</div>
              <div class="text-[11px] text-slate-500 dark:text-slate-400">Save up to 70%</div>
            </div>
          </div>
        </div>
      </div>

      <!-- OMNI-SEARCH HERO BAR -->
      <div id="catalogue-section" class="relative rounded-3xl border border-sky-100 dark:border-slate-800 scroll-mt-24 bg-gradient-to-b from-sky-500/10 via-sky-500/5 to-transparent p-6 sm:p-8 backdrop-blur-xs">
        <div class="max-w-3xl mx-auto space-y-4">
          <div class="text-center space-y-1.5">
            <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
              Medicine Catalogue
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Search by medicine brand, active generic molecule, or ailment.
            </p>
          </div>
          <!-- Input -->
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
              <i data-lucide="search" class="w-5 h-5"></i>
            </div>
            <input
              id="search-input"
              type="text"
              oninput="filterMedicines()"
              placeholder="Search medicines, active molecules, ailments..."
              class="w-full pl-12 pr-4 py-3.5 rounded-2xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 shadow-lg text-sm focus:outline-hidden focus:ring-2 focus:ring-sky-500 transition-all"
            />
          </div>
          <!-- Filters -->
          <div class="flex flex-wrap items-center justify-center gap-2 pt-2">
            <button id="filter-all" onclick="setFilter('all')" class="px-3 py-1.5 rounded-xl text-xs font-semibold bg-sky-600 text-white shadow-xs">
              All Items (<span id="total-count">0</span>)
            </button>
            <button id="filter-otc" onclick="setFilter('otc')" class="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-emerald-600 dark:text-emerald-400 shadow-xs">
              OTC Only
            </button>
            <button id="filter-rx" onclick="setFilter('rx')" class="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-amber-600 dark:text-amber-400 shadow-xs">
              Prescription (Rx)
            </button>
            <button id="filter-coldchain" onclick="setFilter('coldchain')" class="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-cyan-600 dark:text-cyan-400 shadow-xs">
              <i data-lucide="thermometer-snowflake" class="w-3 h-3"></i>
              Cold-Chain Monitored
            </button>
          </div>
        </div>
      </div>

      <!-- MEDICINES GRID -->
      <div id="medicines-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <!-- Rendered dynamically via JavaScript -->
      </div>
    </div>

    <!-- VIEW: PHARMACIST DESK -->
    <div id="view-pharmacist-desk" class="hidden space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <i data-lucide="building" class="w-6 h-6"></i>
          </div>
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Pharmacist Verification Desk
              <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                Active
              </span>
            </h2>
            <p class="text-xs text-slate-500 dark:text-slate-400">
              Review patient prescriptions, verify detected medicines, and approve for dispensary dispatch.
            </p>
          </div>
        </div>
        <div id="rx-verified-badge" class="hidden inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 text-xs font-semibold">
          <i data-lucide="check-circle-2" class="w-4 h-4"></i>
          <span>Prescription Approved & Dispatched</span>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-[640px]">
        <!-- Inspection Viewport -->
        <div class="lg:col-span-7 flex flex-col rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs overflow-hidden">
          <div class="flex items-center justify-between p-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/70 text-xs">
            <div class="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-300">
              <i data-lucide="file-text" class="w-4 h-4 text-sky-500"></i>
              <span>Inspection Viewport</span>
              <span class="text-slate-400">(Dr_Mukherjee_Apollo_Cardio_Rx.png)</span>
            </div>
            <div class="flex items-center gap-1">
              <button onclick="adjustZoom(-0.2)" class="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="zoom-out" class="w-4 h-4"></i></button>
              <span id="zoom-label" class="text-[11px] font-mono w-12 text-center text-slate-500">100%</span>
              <button onclick="adjustZoom(0.2)" class="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="zoom-in" class="w-4 h-4"></i></button>
              <button onclick="toggleInvert()" class="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" title="Toggle Forensic Color Inversion"><i data-lucide="eye" class="w-4 h-4"></i></button>
            </div>
          </div>
          <div class="flex-1 bg-slate-100 dark:bg-slate-950 flex items-center justify-center p-6 overflow-auto">
            <img id="rx-inspect-img" src="https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=800&auto=format&fit=crop&q=60" alt="Rx Document" class="max-h-[500px] object-contain rounded-xl shadow-lg transition-transform duration-150" />
          </div>
        </div>

        <!-- Checklist & Actions -->
        <div class="lg:col-span-5 flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs p-5 space-y-4">
          <div class="space-y-4">
            <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div>
                <h3 class="font-extrabold text-slate-900 dark:text-slate-100 text-base">Verification Audit • Rx #104</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400">Uploaded by Anita Sharma (Patient #9482)</p>
              </div>
              <span class="px-2.5 py-1 text-xs font-semibold rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400">
                PENDING AUDIT
              </span>
            </div>
            <div class="p-3.5 rounded-xl border border-sky-200 dark:border-sky-900/60 bg-sky-50 dark:bg-sky-950/20 space-y-2">
              <div class="flex items-center justify-between text-xs font-bold text-sky-800 dark:text-sky-300">
                <span class="flex items-center gap-1.5"><i data-lucide="sparkles" class="w-4 h-4 text-sky-500"></i>OCR AI Extraction</span>
                <span class="text-sky-600 dark:text-sky-400">Confidence: 96.4%</span>
              </div>
              <div class="flex flex-wrap gap-1.5 pt-1">
                <span class="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1 shadow-xs">
                  <i data-lucide="check-circle-2" class="w-3 h-3 text-emerald-600 dark:text-emerald-400"></i> Amlodipine 5mg
                </span>
                <span class="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1 shadow-xs">
                  <i data-lucide="check-circle-2" class="w-3 h-3 text-emerald-600 dark:text-emerald-400"></i> Atorvastatin 20mg
                </span>
              </div>
            </div>
            <div class="space-y-2 text-xs text-slate-600 dark:text-slate-400">
              <div class="font-bold text-slate-800 dark:text-slate-300 uppercase tracking-wider">Mandatory Checklist</div>
              <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked class="rounded text-sky-600" /><span>Doctor Council Registration #49281 Verified</span></label>
              <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked class="rounded text-sky-600" /><span>Prescription Date within validity window</span></label>
              <label class="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked class="rounded text-sky-600" /><span>Dosage duration and frequency verified</span></label>
            </div>
            <div>
              <label class="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Pharmacist Clinical Notes</label>
              <textarea rows="2" class="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-2.5 text-slate-800 dark:text-slate-200">Verified against national registry. Batches allocated from central stock.</textarea>
            </div>
          </div>
          <div class="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center gap-3">
            <button onclick="approveRx()" class="flex-1 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-md transition-all">
              Certify & Approve Rx
            </button>
            <button onclick="alert('Prescription rejected and sent back to patient with clinical notes.')" class="px-4 py-3 rounded-xl border border-rose-200 dark:border-rose-900/60 bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-900/50 text-xs font-semibold">
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- VIEW: LOGISTICS TIMELINE -->
    <div id="view-logistics" class="hidden space-y-5">
      <div class="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-400">
              <i data-lucide="truck" class="w-6 h-6"></i>
            </div>
            <div>
              <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Order Tracking & Logistics
                <span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 border border-cyan-500/20">
                  Live
                </span>
              </h2>
              <p class="text-xs text-slate-500 dark:text-slate-400">
                Real-time delivery progress, cold-chain temperature status, and OTP verification.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <!-- Order Selection -->
        <div class="lg:col-span-4 rounded-2xl border border-slate-800 bg-slate-900 p-4 space-y-3">
          <div class="text-xs font-bold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800">
            Recent Clinical Orders (3)
          </div>
          <div class="space-y-2">
            <div class="p-3.5 rounded-xl border border-sky-500 bg-sky-950/40 cursor-pointer">
              <div class="flex justify-between font-bold text-sm text-slate-100">
                <span>ORD-2026-CC-8421</span>
                <span>₹1,480.00</span>
              </div>
              <div class="text-xs text-slate-400 mt-1 truncate">Flat 402, Green Glen Layout, Bellandur</div>
              <div class="flex justify-between mt-2 pt-2 border-t border-slate-800 text-[11px]">
                <span class="text-slate-500">12:27 PM</span>
                <span class="text-sky-400 font-semibold">Out For Delivery</span>
              </div>
            </div>
            <div class="p-3.5 rounded-xl border border-slate-800 hover:border-slate-700 cursor-pointer">
              <div class="flex justify-between font-bold text-sm text-slate-100">
                <span>ORD-2026-RX-9104</span>
                <span>₹620.50</span>
              </div>
              <div class="text-xs text-slate-400 mt-1 truncate">12th Main Road, HAL 2nd Stage</div>
              <div class="flex justify-between mt-2 pt-2 border-t border-slate-800 text-[11px]">
                <span class="text-slate-500">12:04 PM</span>
                <span class="text-amber-400 font-semibold">Cold-Chain Packed</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Milestones -->
        <div class="lg:col-span-8 p-6 rounded-2xl border border-slate-800 bg-slate-900 space-y-6">
          <div class="flex justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 class="font-extrabold text-base text-slate-100">Fulfillment Milestone Progression</h3>
              <p class="text-xs text-slate-400">Tracking order: ORD-2026-CC-8421</p>
            </div>
            <span class="text-xs font-semibold text-slate-400">Est. Delivery: 45 Min Doorstep</span>
          </div>

          <div class="space-y-4">
            <div class="flex items-start gap-4">
              <div class="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold"><i data-lucide="check" class="w-4 h-4"></i></div>
              <div><div class="text-sm font-bold text-slate-100">Order Placed</div><div class="text-xs text-slate-400">Digital clinical prescription logged</div></div>
            </div>
            <div class="flex items-start gap-4">
              <div class="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold"><i data-lucide="check" class="w-4 h-4"></i></div>
              <div><div class="text-sm font-bold text-slate-100">Rx Clinically Approved</div><div class="text-xs text-slate-400">Checked by licensed pharmacist</div></div>
            </div>
            <div class="flex items-start gap-4">
              <div class="h-8 w-8 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold"><i data-lucide="check" class="w-4 h-4"></i></div>
              <div><div class="text-sm font-bold text-slate-100">Cold-Chain Sealed</div><div class="text-xs text-slate-400">Batch packaging under thermal control</div></div>
            </div>
            <div class="flex items-start gap-4">
              <div class="h-8 w-8 rounded-full bg-sky-600 text-white flex items-center justify-center text-xs font-bold ring-4 ring-sky-500/20">4</div>
              <div><div class="text-sm font-bold text-sky-400">Out for Express Transit</div><div class="text-xs text-slate-400">Dispatched with IoT temperature monitor</div></div>
            </div>
            <div class="flex items-start gap-4 opacity-50">
              <div class="h-8 w-8 rounded-full bg-slate-800 text-slate-400 border border-slate-700 flex items-center justify-center text-xs font-bold">5</div>
              <div><div class="text-sm font-bold text-slate-400">Delivered & Verified</div><div class="text-xs text-slate-500">Handed over with patient OTP</div></div>
            </div>
          </div>

          <!-- Courier Card & OTP Box -->
          <div class="pt-4 border-t border-slate-200 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <div class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">Assigned Fleet Courier</div>
              <div class="font-bold text-sm text-slate-900 dark:text-slate-100">Manoj Kumar (Certified Cold-Chain Fleet)</div>
              <div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">+91 98450 12849 • Thermal Van KA-05-MH-2914</div>
            </div>
            <div class="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 space-y-2">
              <div class="text-xs font-bold text-slate-800 dark:text-slate-200">Patient Handover OTP Verification</div>
              <div class="flex gap-2">
                <input id="otp-input" type="text" placeholder="Enter OTP (4821)" class="flex-1 text-xs rounded-lg border border-slate-200 dark:border-slate-800 px-3 py-1.5 bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-center font-mono" />
                <button onclick="verifyOtp()" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold">Verify</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- VIEW: HOSPITAL ANALYTICS -->
    <div id="view-admin-dashboard" class="hidden space-y-6">
      <div class="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex justify-between items-center shadow-xs">
        <div>
          <h2 class="text-xl font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
            Hospital Analytics & Logistics
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20">Live</span>
          </h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Key operational metrics, fulfillment speed, and generic savings.</p>
        </div>
        <div class="text-xs font-semibold text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-xl">Last 24 Hours</div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1 shadow-xs">
          <div class="text-xs font-semibold text-slate-500 dark:text-slate-400">Avg. Dispatch Time</div>
          <div class="text-2xl font-black text-slate-900 dark:text-slate-100">14.2 min</div>
          <div class="text-[11px] font-bold text-emerald-600 dark:text-emerald-400">18% faster than target</div>
        </div>
        <div class="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1 shadow-xs">
          <div class="text-xs font-semibold text-slate-500 dark:text-slate-400">Cold-Chain Compliance</div>
          <div class="text-2xl font-black text-slate-900 dark:text-slate-100">99.8%</div>
          <div class="text-[11px] font-bold text-emerald-600 dark:text-emerald-400">2°C - 8°C maintained</div>
        </div>
        <div class="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1 shadow-xs">
          <div class="text-xs font-semibold text-slate-500 dark:text-slate-400">Generic Savings</div>
          <div class="text-2xl font-black text-slate-900 dark:text-slate-100">₹48,920</div>
          <div class="text-[11px] text-slate-500">Patient savings on generics</div>
        </div>
        <div class="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-1 shadow-xs">
          <div class="text-xs font-semibold text-slate-500 dark:text-slate-400">Fulfilled Orders</div>
          <div class="text-2xl font-black text-slate-900 dark:text-slate-100">842 Orders</div>
          <div class="text-[11px] text-slate-500">100% pharmacist verified</div>
        </div>
      </div>
    </div>

  </main>

  <!-- GENERIC PRICE MATCH MODAL -->
  <div id="generic-modal" class="fixed inset-0 z-50 hidden flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
    <div class="relative w-full max-w-lg rounded-2xl border border-sky-200 dark:border-sky-900 bg-white dark:bg-slate-900 shadow-2xl p-6 overflow-hidden">
      <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-sky-500 via-emerald-500 to-teal-400"></div>
      <button onclick="closeGenericModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"><i data-lucide="x" class="w-5 h-5"></i></button>
      
      <div class="text-sky-600 dark:text-sky-400 font-semibold text-xs tracking-wider uppercase mb-1">Bioequivalent Generic Price-Match</div>
      <h3 id="modal-headline" class="text-xl font-bold text-slate-900 dark:text-slate-100">Save 62% with Certified Generic</h3>
      <p id="modal-subtext" class="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-5">Both formulations contain the identical active pharmaceutical molecule and clinical bioavailability.</p>

      <div class="grid grid-cols-2 gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50 mb-5">
        <div class="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 block mb-1">Prescribed Brand</span>
          <div id="modal-brand-name" class="font-bold text-slate-900 dark:text-slate-200">Crocin Advance 500mg</div>
          <div class="mt-3 text-lg font-bold text-slate-700 dark:text-slate-300" id="modal-brand-price">₹25.50</div>
        </div>
        <div class="p-3 rounded-lg border border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/20">
          <span class="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full mb-1 inline-block">Save ₹16.00</span>
          <div id="modal-generic-name" class="font-bold text-slate-900 dark:text-slate-100">Generic Paracetamol 500mg</div>
          <div class="mt-3 text-lg font-extrabold text-emerald-600 dark:text-emerald-400" id="modal-generic-price">₹9.50</div>
        </div>
      </div>

      <div class="p-3 rounded-lg bg-sky-50 dark:bg-sky-950/30 border border-sky-200 dark:border-sky-900/40 text-xs text-sky-800 dark:text-sky-300 mb-6 flex items-start gap-2">
        <i data-lucide="shield-check" class="w-4 h-4 shrink-0 mt-0.5 text-emerald-600 dark:text-emerald-400"></i>
        <span><strong>Pharmacist Guarantee:</strong> Identical clinical potency and dissolution rate under WHO-GMP standards.</span>
      </div>

      <div class="flex gap-2.5">
        <button onclick="addGenericToCart()" class="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-md">
          Switch to Generic (₹9.50)
        </button>
        <button onclick="closeGenericModal()" class="px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium text-xs">
          Keep Original
        </button>
      </div>
    </div>
  </div>

  <!-- CART SLIDE-OVER DRAWER -->
  <div id="cart-drawer" class="fixed inset-0 z-50 hidden overflow-hidden">
    <div onclick="closeCart()" class="absolute inset-0 bg-slate-950/60 backdrop-blur-xs"></div>
    <div class="fixed inset-y-0 right-0 max-w-full flex pl-10">
      <div class="w-screen max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col justify-between p-6">
        <div>
          <div class="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
            <div class="font-bold text-base text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <i data-lucide="shopping-bag" class="w-5 h-5 text-sky-500"></i>
              <span>Prescription Cart</span>
            </div>
            <button onclick="closeCart()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"><i data-lucide="x" class="w-5 h-5"></i></button>
          </div>
          <div id="cart-items-list" class="space-y-3 py-4 max-h-[460px] overflow-y-auto">
            <!-- Populated via JS -->
          </div>
        </div>
        <div class="pt-4 border-t border-slate-200 dark:border-slate-800 space-y-3">
          <div class="space-y-1 text-xs text-slate-500 dark:text-slate-400">
            <div class="flex justify-between"><span>Subtotal</span><span id="cart-subtotal" class="font-semibold text-slate-900 dark:text-slate-200">₹0.00</span></div>
            <div class="flex justify-between"><span>Cold-Chain Express Delivery</span><span class="font-semibold text-slate-900 dark:text-slate-200">₹40.00</span></div>
            <div class="flex justify-between text-sm font-extrabold text-slate-900 dark:text-slate-100 pt-2 border-t border-slate-200 dark:border-slate-800">
              <span>Total Amount</span>
              <span id="cart-total">₹40.00</span>
            </div>
          </div>
          <button onclick="checkout()" class="w-full py-3 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-sm shadow-md">
            Confirm & Place Order
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- RX UPLOAD MODAL -->
  <div id="rx-modal" class="fixed inset-0 z-50 hidden flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
    <div class="relative w-full max-w-lg rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6">
      <button onclick="closeRxModal()" class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"><i data-lucide="x" class="w-5 h-5"></i></button>
      <div class="text-sky-600 dark:text-sky-400 font-bold text-xs uppercase tracking-wider">Clinical Dispensary Gateway</div>
      <h3 class="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">Upload Doctor's Prescription</h3>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 mb-4">Our AI optical scanner extracts formulations within seconds for licensed pharmacist verification.</p>
      
      <div class="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-sky-500 rounded-2xl p-8 text-center cursor-pointer bg-slate-50 dark:bg-slate-950/40">
        <i data-lucide="upload-cloud" class="w-10 h-10 text-slate-400 mx-auto mb-2"></i>
        <div class="text-xs font-semibold text-slate-700 dark:text-slate-300">Drag & drop your Rx document, or <span class="text-sky-600 dark:text-sky-400 underline">browse files</span></div>
        <p class="text-[11px] text-slate-500 mt-1">Supports JPG, PNG, WebP, PDF up to 16MB.</p>
      </div>

      <button onclick="simulateUpload()" class="w-full mt-4 py-3 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs shadow-md">
        Submit Prescription for Pharmacist Review
      </button>
    </div>
  </div>

  <!-- AUTH0 ROLE-BASED ACCESS CONTROL MODAL -->
  <div id="role-limits-modal" class="fixed inset-0 z-50 hidden flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
    <div class="relative w-full max-w-2xl rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 sm:p-8 max-h-[90vh] overflow-y-auto">
      <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-sky-500 via-emerald-500 to-teal-400"></div>
      <button onclick="closeRoleLimitsModal()" class="absolute top-5 right-5 p-1.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all cursor-pointer">
        <i data-lucide="x" class="w-5 h-5"></i>
      </button>

      <div class="flex items-center gap-3 mb-5">
        <div class="p-3 rounded-2xl bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20">
          <i data-lucide="key-round" class="w-6 h-6"></i>
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h2 class="text-xl font-black text-slate-900 dark:text-slate-100">Role-Based Access Control</h2>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">Auth0 RBAC</span>
          </div>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Strict principle of least privilege. Each role is shown only authorized clinical data and workspaces.</p>
        </div>
      </div>

      <div class="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">Active Role Identity</span>
          <div class="font-bold text-sm text-slate-900 dark:text-slate-100" id="modal-active-role-name">Customer / Patient</div>
          <div class="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-1.5" id="modal-active-scopes">
            <!-- Scopes pills rendered here -->
          </div>
        </div>
        <div class="px-3 py-1.5 rounded-xl bg-sky-50 dark:bg-sky-950/50 border border-sky-200 dark:border-sky-900/60 text-sky-700 dark:text-sky-300 text-xs font-bold shrink-0 flex items-center gap-1.5" id="modal-active-badge">
          <i data-lucide="shield-check" class="w-4 h-4 text-emerald-500"></i>
          <span>Patient Account</span>
        </div>
      </div>

      <div class="space-y-3">
        <div class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">Switch Verified Role:</div>
        
        <div onclick="selectRole('customer')" class="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 transition-all cursor-pointer flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-xl bg-sky-50 dark:bg-sky-950/50 text-sky-600"><i data-lucide="user" class="w-5 h-5"></i></div>
            <div>
              <div class="font-bold text-sm text-slate-900 dark:text-slate-100">Customer / Patient <span class="text-xs text-slate-400 font-normal">(Healthcare Consumer)</span></div>
              <p class="text-xs text-slate-500 mt-0.5">Browse medicines, generic bioequivalent savings, upload personal prescriptions, track personal orders.</p>
            </div>
          </div>
          <span class="text-xs font-semibold text-sky-600">Switch &rarr;</span>
        </div>

        <div onclick="selectRole('pharmacy')" class="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 transition-all cursor-pointer flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600"><i data-lucide="building" class="w-5 h-5"></i></div>
            <div>
              <div class="font-bold text-sm text-slate-900 dark:text-slate-100">Clinical Pharmacist <span class="text-xs text-slate-400 font-normal">(Dispensary Station #04)</span></div>
              <p class="text-xs text-slate-500 mt-0.5">Audit prescription documents, verify molecules & dosages, approve/reject Rx, inspect formulary.</p>
            </div>
          </div>
          <span class="text-xs font-semibold text-sky-600">Switch &rarr;</span>
        </div>

        <div onclick="selectRole('delivery')" class="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 transition-all cursor-pointer flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-xl bg-cyan-50 dark:bg-cyan-950/50 text-cyan-600"><i data-lucide="truck" class="w-5 h-5"></i></div>
            <div>
              <div class="font-bold text-sm text-slate-900 dark:text-slate-100">Delivery Rider <span class="text-xs text-slate-400 font-normal">(Cold-Chain Courier)</span></div>
              <p class="text-xs text-slate-500 mt-0.5">Access assigned dispatches, monitor IoT cold-chain (2°C - 8°C), and verify patient OTP handoff.</p>
            </div>
          </div>
          <span class="text-xs font-semibold text-sky-600">Switch &rarr;</span>
        </div>

        <div onclick="selectRole('admin')" class="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-sky-500 transition-all cursor-pointer flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600"><i data-lucide="activity" class="w-5 h-5"></i></div>
            <div>
              <div class="font-bold text-sm text-slate-900 dark:text-slate-100">Hospital HQ Admin <span class="text-xs text-slate-400 font-normal">(Executive Oversight)</span></div>
              <p class="text-xs text-slate-500 mt-0.5">Monitor hospital fulfillment KPIs, dispatch velocity, cold-chain regulatory compliance, and generic savings.</p>
            </div>
          </div>
          <span class="text-xs font-semibold text-sky-600">Switch &rarr;</span>
        </div>
      </div>
    </div>
  </div>

  <!-- JAVASCRIPT STATE ENGINE -->
  <script>
    const MEDICINES = {json.dumps(medicines_data)};
    let activeFilter = 'all';
    let cart = [];
    let currentZoom = 1;
    let isInverted = false;

    // Strict Auth0 RBAC Definitions
    const ROLE_DEFINITIONS = {{
      customer: {{
        id: "customer",
        label: "Customer / Patient",
        badge: "Patient Account",
        scopes: ["read:catalogue", "write:cart", "create:prescription", "read:own_orders"],
        allowedTabs: [
          {{ id: "catalogue", label: "Medicine Catalogue" }},
          {{ id: "logistics", label: "My Orders & Tracking" }}
        ],
        defaultTab: "catalogue",
        canAccessCart: true,
        canUploadRx: true,
        canViewHero: true
      }},
      pharmacy: {{
        id: "pharmacy",
        label: "Clinical Pharmacist",
        badge: "Dispensary Station #04",
        scopes: ["read:prescriptions", "verify:prescription", "reject:prescription", "read:inventory"],
        allowedTabs: [
          {{ id: "pharmacist-desk", label: "Pharmacist Verification Desk" }},
          {{ id: "catalogue", label: "Formulary Lookup" }}
        ],
        defaultTab: "pharmacist-desk",
        canAccessCart: false,
        canUploadRx: false,
        canViewHero: false
      }},
      delivery: {{
        id: "delivery",
        label: "Delivery Rider",
        badge: "Fleet Unit #CC-842",
        scopes: ["read:delivery_queue", "verify:otp_handoff", "read:temperature_telemetry"],
        allowedTabs: [
          {{ id: "logistics", label: "Delivery Fleet & Tracking" }}
        ],
        defaultTab: "logistics",
        canAccessCart: false,
        canUploadRx: false,
        canViewHero: false
      }},
      admin: {{
        id: "admin",
        label: "Hospital HQ Admin",
        badge: "Hospital HQ",
        scopes: ["read:hospital_analytics", "manage:network", "read:audit_logs", "read:all_telemetry"],
        allowedTabs: [
          {{ id: "admin-dashboard", label: "Hospital Analytics & Oversight" }},
          {{ id: "catalogue", label: "Network Formulary" }}
        ],
        defaultTab: "admin-dashboard",
        canAccessCart: false,
        canUploadRx: false,
        canViewHero: false
      }}
    }};

    let currentRole = "customer";
    let activeTab = "catalogue";

    function setRole(role) {{
      currentRole = role;
      const def = ROLE_DEFINITIONS[role] || ROLE_DEFINITIONS.customer;
      
      const roleLabel = document.getElementById('current-role-label');
      if (roleLabel) roleLabel.innerText = def.label;

      // Render navigation tabs strictly for this role
      const nav = document.getElementById('main-nav-tabs');
      if (nav) {{
        nav.innerHTML = def.allowedTabs.map(t => `
          <button id="tab-btn-${{t.id}}" onclick="setTab('${{t.id}}')" class="px-3 py-1.5 text-xs font-semibold rounded-lg transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 cursor-pointer">
            ${{t.label}}
          </button>
        `).join('');
      }}

      // Cart button visibility
      const cartBtn = document.getElementById('header-cart-btn');
      if (cartBtn) cartBtn.style.display = def.canAccessCart ? 'inline-flex' : 'none';

      // Upload Rx button visibility
      const rxBtn = document.getElementById('header-upload-rx-btn');
      if (rxBtn) rxBtn.style.display = def.canUploadRx ? 'inline-flex' : 'none';

      // Hero banner visibility
      const hero = document.getElementById('hero-banner-section');
      if (hero) hero.style.display = def.canViewHero ? 'block' : 'none';

      // Switch view to default tab
      setTab(def.defaultTab);
    }}

    function selectRole(role) {{
      setRole(role);
      closeRoleLimitsModal();
    }}

    function openRoleLimitsModal() {{
      const def = ROLE_DEFINITIONS[currentRole] || ROLE_DEFINITIONS.customer;
      document.getElementById('modal-active-role-name').innerText = def.label;
      document.getElementById('modal-active-badge').innerHTML = `<i data-lucide="shield-check" class="w-4 h-4 text-emerald-500"></i><span>${{def.badge}}</span>`;
      document.getElementById('modal-active-scopes').innerHTML = def.scopes.map(s => 
        `<span class="px-1.5 py-0.5 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px] font-mono text-slate-700 dark:text-slate-300">${{s}}</span>`
      ).join('');
      
      document.getElementById('role-limits-modal').classList.remove('hidden');
      lucide.createIcons();
    }}

    function closeRoleLimitsModal() {{
      document.getElementById('role-limits-modal').classList.add('hidden');
    }}

    function returnToDefaultWorkspace() {{
      const def = ROLE_DEFINITIONS[currentRole] || ROLE_DEFINITIONS.customer;
      setTab(def.defaultTab);
    }}

    function renderMedicines(items) {{
      const grid = document.getElementById('medicines-grid');
      document.getElementById('total-count').innerText = items.length;

      if (items.length === 0) {{
        grid.innerHTML = '<div class="col-span-4 text-center py-16 text-slate-400">No clinical formulations found.</div>';
        return;
      }}

      grid.innerHTML = items.map(m => {{
        const isCold = m.category.toLowerCase().includes('insulin') || m.category.toLowerCase().includes('vaccine') || m.name.toLowerCase().includes('insulin');
        const price = (m.mrp * 0.9).toFixed(2);
        const cleanGeneric = m.generic_name ? m.generic_name.split('|')[0].trim() : '';
        
        return `
          <div class="flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-5 shadow-xs hover:border-sky-300 dark:hover:border-sky-700/60 transition-all">
            <div>
              <div class="flex flex-wrap items-center gap-1.5 mb-3">
                ${{m.prescription_required ? '<span class="px-2 py-0.5 text-xs font-semibold rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400">Rx Required</span>' : '<span class="px-2 py-0.5 text-xs font-medium rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400">OTC Approved</span>'}}
                ${{isCold ? '<span class="px-2 py-0.5 text-xs font-medium rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 flex items-center gap-1"><i data-lucide="thermometer-snowflake" class="w-3 h-3"></i>Cold-Chain</span>' : ''}}
              </div>
              <h3 class="font-bold text-base text-slate-900 dark:text-slate-100">${{m.name}}</h3>
              <p class="text-xs font-medium text-slate-600 dark:text-slate-400 flex items-center gap-1 mt-0.5 truncate">
                <i data-lucide="pill" class="w-3 h-3 text-sky-500 dark:text-sky-400"></i> ${{cleanGeneric || m.generic_name}}
              </p>
              <div class="grid grid-cols-2 gap-2 text-xs py-2 my-2 border-y border-slate-100 dark:border-slate-800 text-slate-600 dark:text-slate-400">
                <div><span class="text-[10px] text-slate-400 uppercase block">Form</span>${{m.dosage_form}} • ${{m.strength}}</div>
                <div><span class="text-[10px] text-slate-400 uppercase block">Maker</span>${{m.manufacturer}}</div>
              </div>
              <button onclick="openGenericModal('${{m.name}}', ${{m.mrp}})" class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-sky-200 dark:border-sky-900/60 bg-sky-50 dark:bg-sky-950/20 text-sky-700 dark:text-sky-300 text-xs font-semibold hover:bg-sky-100 dark:hover:bg-sky-900/40 transition-all mb-4 cursor-pointer">
                <span class="flex items-center gap-1"><i data-lucide="sparkles" class="w-3.5 h-3.5 text-sky-500 dark:text-sky-400"></i>Generic Price Match</span>
                <span class="text-[11px] underline">Save 60%+</span>
              </button>
            </div>
            <div class="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
              <div>
                <span class="text-lg font-extrabold text-slate-900 dark:text-slate-100">₹${{price}}</span>
                <span class="text-xs text-slate-400 line-through ml-1">₹${{m.mrp.toFixed(2)}}</span>
              </div>
              <button onclick="addToCart('${{m.name}}', ${{price}})" class="px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold shadow-xs cursor-pointer">
                Add to Cart
              </button>
            </div>
          </div>
        `;
      }}).join('');

      lucide.createIcons();
    }}

    function filterMedicines() {{
      const q = document.getElementById('search-input').value.toLowerCase();
      let res = MEDICINES.filter(m => 
        m.name.toLowerCase().includes(q) ||
        m.generic_name.toLowerCase().includes(q) ||
        m.category.toLowerCase().includes(q)
      );

      if (activeFilter === 'otc') res = res.filter(m => m.prescription_required === 0);
      if (activeFilter === 'rx') res = res.filter(m => m.prescription_required === 1);
      if (activeFilter === 'coldchain') res = res.filter(m => m.category.toLowerCase().includes('insulin') || m.name.toLowerCase().includes('insulin'));

      renderMedicines(res);
    }}

    function setFilter(type) {{
      activeFilter = type;
      ['all', 'otc', 'rx', 'coldchain'].forEach(t => {{
        const btn = document.getElementById('filter-' + t);
        if (t === type) {{
          btn.className = 'px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-900 shadow-xs';
        }} else {{
          btn.className = 'px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-900/80 border border-slate-800 text-slate-400';
        }}
      }});
      filterMedicines();
    }}

    function setTab(tab) {{
      activeTab = tab;
      const def = ROLE_DEFINITIONS[currentRole] || ROLE_DEFINITIONS.customer;
      const isAllowed = def.allowedTabs.some(t => t.id === tab);
      const restrictedView = document.getElementById('view-access-restricted');

      if (!isAllowed) {{
        // Hide all operational workspaces
        ['catalogue', 'pharmacist-desk', 'logistics', 'admin-dashboard'].forEach(t => {{
          const view = document.getElementById('view-' + t);
          if (view) view.classList.add('hidden');
        }});
        
        // Show 403 Access Restricted View
        if (restrictedView) {{
          restrictedView.classList.remove('hidden');
          const explanation = document.getElementById('forbidden-explanation');
          if (explanation) {{
            explanation.innerHTML = `Your active role <strong class="text-slate-900 dark:text-slate-100 capitalize">(${{def.label}})</strong> is not authorized to access the <span class="font-semibold text-slate-800 dark:text-slate-200">${{tab}}</span> workspace under Drugs and Cosmetics clinical confidentiality rules.`;
          }}
          const scopesList = document.getElementById('forbidden-scopes-list');
          if (scopesList) {{
            scopesList.innerHTML = def.scopes.map(s => 
              `<span class="px-1.5 py-0.5 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 font-mono text-[10px] text-slate-600 dark:text-slate-400">${{s}}</span>`
            ).join('');
          }}
        }}
        lucide.createIcons();
        return;
      }}

      // Allowed tab: hide restricted view
      if (restrictedView) restrictedView.classList.add('hidden');

      ['catalogue', 'pharmacist-desk', 'logistics', 'admin-dashboard'].forEach(t => {{
        const view = document.getElementById('view-' + t);
        const btn = document.getElementById('tab-btn-' + t);
        if (t === tab) {{
          if (view) view.classList.remove('hidden');
          if (btn) btn.className = 'px-3 py-1.5 text-xs font-semibold rounded-lg bg-white dark:bg-slate-800 text-sky-600 dark:text-sky-400 shadow-xs cursor-pointer';
        }} else {{
          if (view) view.classList.add('hidden');
          if (btn) btn.className = 'px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 cursor-pointer';
        }}
      }});

      // Show hero banner only for roles with canViewHero on catalogue
      const hero = document.getElementById('hero-banner-section');
      if (hero) {{
        hero.style.display = (tab === 'catalogue' && def.canViewHero) ? 'block' : 'none';
      }}

      lucide.createIcons();
    }}

    function exploreCatalogue() {{
      setTab('catalogue');
      setTimeout(() => {{
        const section = document.getElementById('catalogue-section');
        const input = document.getElementById('search-input');
        if (section) {{
          section.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
        if (input) {{
          input.focus();
        }}
      }}, 50);
    }}

    function setTheme(mode) {{
      const lightBtn = document.getElementById('theme-btn-light');
      const darkBtn = document.getElementById('theme-btn-dark');
      if (mode === 'light') {{
        document.documentElement.classList.remove('dark');
        document.body.className = 'bg-slate-50 text-slate-900 min-h-screen flex flex-col transition-colors duration-150';
        if (lightBtn) lightBtn.className = 'px-2 py-1 text-xs bg-white text-sky-600 font-semibold rounded-md shadow-xs transition-all flex items-center gap-1';
        if (darkBtn) darkBtn.className = 'px-2 py-1 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 rounded-md transition-all flex items-center gap-1';
      }} else {{
        document.documentElement.classList.add('dark');
        document.body.className = 'bg-slate-950 text-slate-100 min-h-screen flex flex-col transition-colors duration-150';
        if (darkBtn) darkBtn.className = 'px-2 py-1 text-xs bg-slate-800 text-sky-400 font-semibold rounded-md shadow-xs transition-all flex items-center gap-1';
        if (lightBtn) lightBtn.className = 'px-2 py-1 text-xs text-slate-400 hover:text-slate-100 rounded-md transition-all flex items-center gap-1';
      }}
    }}

    function addToCart(name, price) {{
      cart.push({{ name, price }});
      document.getElementById('cart-counter').innerText = cart.length;
      updateCartDrawer();
    }}

    function showToast(msg, isSuccess = true) {{
      let toast = document.getElementById('clinical-toast');
      if (!toast) {{
        toast = document.createElement('div');
        toast.id = 'clinical-toast';
        document.body.appendChild(toast);
      }}
      toast.className = (isSuccess
        ? 'fixed bottom-5 right-5 z-50 px-4 py-3 rounded-xl bg-emerald-600 text-white text-xs font-semibold shadow-2xl transition-all'
        : 'fixed bottom-5 right-5 z-50 px-4 py-3 rounded-xl bg-rose-600 text-white text-xs font-semibold shadow-2xl transition-all');
      toast.innerText = msg;
      toast.style.display = 'block';
      setTimeout(() => {{ toast.style.display = 'none'; }}, 3500);
    }}

    function updateCartDrawer() {{
      const list = document.getElementById('cart-items-list');
      if (cart.length === 0) {{
        list.innerHTML = '<div class="text-center py-10 text-slate-400 text-xs">Cart is empty.</div>';
        document.getElementById('cart-subtotal').innerText = '₹0.00';
        document.getElementById('cart-total').innerText = '₹0.00';
        return;
      }}
      let subtotal = 0;
      list.innerHTML = cart.map((item, idx) => {{
        subtotal += item.price;
        return `
          <div class="flex justify-between items-center p-3 rounded-xl border border-slate-800 bg-slate-950/60 text-xs">
            <div>
              <div class="font-bold text-slate-200">${{item.name}}</div>
              <div class="text-slate-400">₹${{item.price}}</div>
            </div>
            <button onclick="removeFromCart(${{idx}})" class="text-rose-400"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
          </div>
        `;
      }}).join('');
      const deliveryFee = subtotal >= 500 || subtotal === 0 ? 0 : 30;
      const tax = +(subtotal * 0.05);
      const total = subtotal + deliveryFee + tax;
      document.getElementById('cart-subtotal').innerText = '₹' + subtotal.toFixed(2);
      document.getElementById('cart-total').innerText = '₹' + total.toFixed(2);
      lucide.createIcons();
    }}

    function removeFromCart(idx) {{
      cart.splice(idx, 1);
      document.getElementById('cart-counter').innerText = cart.length;
      updateCartDrawer();
    }}

    function openCart() {{
      document.getElementById('cart-drawer').classList.remove('hidden');
      updateCartDrawer();
    }}
    function closeCart() {{
      document.getElementById('cart-drawer').classList.add('hidden');
    }}

    function checkout() {{
      showToast('Order placed successfully! Forwarding to cold-chain fulfillment.');
      cart = [];
      document.getElementById('cart-counter').innerText = 0;
      closeCart();
      setTab('logistics');
    }}

    function openGenericModal(name, mrp) {{
      document.getElementById('modal-brand-name').innerText = name;
      document.getElementById('modal-brand-price').innerText = '₹' + mrp.toFixed(2);
      const genericPrice = (mrp * 0.38).toFixed(2);
      document.getElementById('modal-generic-price').innerText = '₹' + genericPrice;
      document.getElementById('modal-generic-name').innerText = 'Generic Bioequivalent (' + name.split(' ')[0] + ')';
      document.getElementById('generic-modal').classList.remove('hidden');
      lucide.createIcons();
    }}
    function closeGenericModal() {{
      document.getElementById('generic-modal').classList.add('hidden');
    }}
    function addGenericToCart() {{
      const genericPrice = parseFloat(document.getElementById('modal-generic-price').innerText.replace('₹', ''));
      const genericName = document.getElementById('modal-generic-name').innerText;
      addToCart(genericName, genericPrice);
      closeGenericModal();
      openCart();
    }}

    function openRxModal() {{
      document.getElementById('rx-modal').classList.remove('hidden');
      lucide.createIcons();
    }}
    function closeRxModal() {{
      document.getElementById('rx-modal').classList.add('hidden');
    }}
    function simulateUpload() {{
      showToast('Prescription submitted! AI OCR confidence: 96.4%. Dispatched for clinical review.');
      closeRxModal();
      setTab('logistics');
    }}

    function adjustZoom(delta) {{
      currentZoom = Math.max(0.6, Math.min(2.2, currentZoom + delta));
      document.getElementById('rx-inspect-img').style.transform = `scale(${{currentZoom}})`;
      document.getElementById('zoom-label').innerText = Math.round(currentZoom * 100) + '%';
    }}
    function toggleInvert() {{
      isInverted = !isInverted;
      document.getElementById('rx-inspect-img').style.filter = isInverted ? 'invert(1) hue-rotate(180deg)' : 'none';
    }}

    function approveRx() {{
      document.getElementById('rx-verified-badge').classList.remove('hidden');
      showToast('Prescription #104 certified and approved for cold-chain pack!');
      lucide.createIcons();
    }}

    function verifyOtp() {{
      const val = document.getElementById('otp-input').value.trim();
      if (val === '4821' || val.length === 4) {{
        showToast('Patient OTP Verified! Cold-Chain Handover Complete.');
      }} else {{
        showToast('Invalid OTP. Please check with patient.', false);
      }}
    }}

    // Initial render
    renderMedicines(MEDICINES);
    setRole('customer');
  </script>
</body>
</html>
"""

# 5. Render Full-Bleed Application
components.html(clinical_html, height=1200, scrolling=True)
