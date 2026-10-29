/**
 * MediApp Main Application Coordinator.
 * SPA routing, portal navigation management, demo switcher, cart drawer,
 * and AI Ailment Assistant chat widget initialization.
 */

const App = {
  async init() {
    console.log("MediApp Initializing Full-Stack Client...");

    // 1. Fetch current session and capabilities
    try {
      const meRes = await API.auth.getMe();
      if (meRes.authenticated && meRes.user) {
        State.set("user", meRes.user);
        State.set("activeRole", meRes.user.role);
      }
      State.set("capabilities", meRes.capabilities || {});
      this.updateBannerCapabilities(meRes.capabilities);
    } catch (err) {
      console.warn("Could not retrieve session:", err);
    }

    // 2. Wire Global Header & Navigation Listeners
    this.bindHeaderEvents();

    // 3. Wire Demo Role Switcher
    this.bindDemoSwitcher();

    // 4. Wire Slide-over Cart & Modals
    this.bindCartAndModals();

    // 5. Wire AI Ailment Assistant Widget
    this.bindAIAssistant();

    // 6. Initial render of Portal
    const initialRole = State.get("activeRole") || "customer";
    this.switchPortal(initialRole);

    // 7. Refresh cart count
    await CustomerPortal.refreshCart();
  },

  updateBannerCapabilities(caps) {
    const modeBadge = document.getElementById("banner-mode-badge");
    const bannerMsg = document.getElementById("banner-message");
    if (caps && caps.is_demo) {
      if (modeBadge) modeBadge.textContent = "DEMO MODE";
      if (bannerMsg) bannerMsg.textContent = "Simulated Gateway & Local Verified OCR Active • Real-time Order State Engine Running";
    } else if (caps && !caps.is_demo) {
      if (modeBadge) {
        modeBadge.textContent = "REAL MODE";
        modeBadge.style.color = "var(--emerald)";
        modeBadge.style.borderColor = "var(--emerald)";
      }
      if (bannerMsg) bannerMsg.textContent = "Live Razorpay & Gemini Integrations Configured";
    }
  },

  bindHeaderEvents() {
    // Brand home click
    document.getElementById("brand-home-link")?.addEventListener("click", (e) => {
      e.preventDefault();
      const role = State.get("activeRole");
      const defaultTab = role === "customer" ? "catalogue" : (role === "pharmacy" ? "dashboard" : (role === "delivery" ? "active" : "analytics"));
      State.set("activeTab", defaultTab);
      this.renderCurrentPortalTab();
    });
  },

  bindDemoSwitcher() {
    const switcher = document.getElementById("demo-switcher");
    if (!switcher) return;

    switcher.querySelectorAll(".btn-demo-pill").forEach(btn => {
      btn.addEventListener("click", async () => {
        const targetRole = btn.dataset.role;
        try {
          const res = await API.auth.demoLogin(targetRole);
          State.set("user", res.user);
          State.set("activeRole", res.user.role);
          
          switcher.querySelectorAll(".btn-demo-pill").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");

          Components.toast(`Switched to Demo ${targetRole.toUpperCase()} account (${res.user.full_name})`, "info");
          
          const defaultTab = targetRole === "customer" ? "catalogue" : (targetRole === "pharmacy" ? "dashboard" : (targetRole === "delivery" ? "active" : "analytics"));
          State.set("activeTab", defaultTab);
          this.switchPortal(targetRole);
          await CustomerPortal.refreshCart();
        } catch (err) {
          Components.toast("Failed to switch demo role: " + err.message, "error");
        }
      });
    });

    // Mark current active role in switcher
    const curRole = State.get("activeRole") || "customer";
    const currentBtn = switcher.querySelector(`[data-role="${curRole}"]`);
    if (currentBtn) currentBtn.classList.add("active");
  },

  switchPortal(role) {
    this.renderPortalNav(role);
    this.renderUserMenu();
    this.renderCurrentPortalTab();
  },

  renderPortalNav(role) {
    const nav = document.getElementById("portal-nav");
    if (!nav) return;

    let tabs = [];
    if (role === "customer") {
      tabs = [
        { id: "catalogue", label: "Medicine Catalogue" },
        { id: "orders", label: "My Orders & Tracking" },
        { id: "prescriptions", label: "Prescriptions (OCR)" }
      ];
    } else if (role === "pharmacy") {
      tabs = [
        { id: "dashboard", label: "Fulfillment Dashboard" },
        { id: "orders", label: "Orders Queue" },
        { id: "inventory", label: "Stock Inventory" },
        { id: "prescriptions", label: "Rx Review" }
      ];
    } else if (role === "delivery") {
      tabs = [
        { id: "active", label: "Active Mission" },
        { id: "available", label: "Available Pool" },
        { id: "history", label: "Completed History" }
      ];
    } else if (role === "admin") {
      tabs = [
        { id: "analytics", label: "Platform Intelligence" },
        { id: "users", label: "User Governance" },
        { id: "pharmacies", label: "Pharmacy Partners" },
        { id: "orders", label: "Global Orders" },
        { id: "diagnostics", label: "System Health" }
      ];
    }

    const activeTab = State.get("activeTab") || tabs[0].id;

    nav.innerHTML = tabs.map(t => `
      <button type="button" class="nav-tab-btn ${t.id === activeTab ? 'active' : ''}" data-tab="${t.id}">
        ${t.label}
      </button>
    `).join("");

    nav.querySelectorAll(".nav-tab-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        nav.querySelectorAll(".nav-tab-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        State.set("activeTab", btn.dataset.tab);
        this.renderCurrentPortalTab();
      });
    });
  },

  renderUserMenu() {
    const container = document.getElementById("user-menu-container");
    if (!container) return;

    const user = State.get("user");
    if (user) {
      container.innerHTML = `
        <div class="user-badge-btn" id="btn-user-badge">
          <div class="user-avatar-circle">${user.full_name.charAt(0).toUpperCase()}</div>
          <span style="font-weight:600;">${user.full_name.split(' ')[0]}</span>
          <span class="badge ${user.role === 'admin' ? 'badge-rx' : (user.role === 'pharmacy' ? 'badge-pulse' : (user.role === 'delivery' ? 'badge-otc' : 'badge-category'))}">
            ${user.role}
          </span>
        </div>
      `;
    } else {
      container.innerHTML = `
        <button type="button" class="btn-demo-pill" id="btn-header-login">
          Sign In
        </button>
      `;
      document.getElementById("btn-header-login")?.addEventListener("click", () => {
        // In demo mode, trigger demo customer login
        document.querySelector('.btn-demo-pill[data-role="customer"]')?.click();
      });
    }
  },

  renderCurrentPortalTab() {
    const role = State.get("activeRole") || "customer";
    const tab = State.get("activeTab");

    if (role === "customer") {
      CustomerPortal.init(tab || "catalogue");
    } else if (role === "pharmacy") {
      PharmacyPortal.init(tab || "dashboard");
    } else if (role === "delivery") {
      DeliveryPortal.init(tab || "active");
    } else if (role === "admin") {
      AdminPortal.init(tab || "analytics");
    }
  },

  bindCartAndModals() {
    // Open Cart Drawer
    const btnOpenCart = document.getElementById("btn-open-cart");
    const cartDrawerOverlay = document.getElementById("cart-drawer-overlay");
    const btnCloseCart = document.getElementById("btn-close-cart");

    if (btnOpenCart && cartDrawerOverlay) {
      btnOpenCart.addEventListener("click", () => {
        CustomerPortal.refreshCart();
        cartDrawerOverlay.classList.remove("hidden");
        document.body.style.overflow = "hidden";
      });
    }

    if (btnCloseCart && cartDrawerOverlay) {
      btnCloseCart.addEventListener("click", () => {
        cartDrawerOverlay.classList.add("hidden");
        document.body.style.overflow = "";
      });
    }

    // Close on overlay click outside drawer
    cartDrawerOverlay?.addEventListener("click", (e) => {
      if (e.target === cartDrawerOverlay) {
        cartDrawerOverlay.classList.add("hidden");
        document.body.style.overflow = "";
      }
    });

    // Close buttons for modals
    document.getElementById("btn-close-generic")?.addEventListener("click", () => Components.closeModal("generic-modal"));
    document.getElementById("btn-close-checkout")?.addEventListener("click", () => Components.closeModal("checkout-modal"));
    document.getElementById("btn-close-rx")?.addEventListener("click", () => Components.closeModal("prescription-modal"));
    document.getElementById("btn-close-order-detail")?.addEventListener("click", () => Components.closeModal("order-detail-modal"));
  },

  bindAIAssistant() {
    const btnToggleAI = document.getElementById("btn-toggle-ai");
    const btnCloseAI = document.getElementById("btn-close-ai");
    const chatWindow = document.getElementById("ai-chat-window");
    const chatForm = document.getElementById("ai-chat-form");
    const queryInput = document.getElementById("ai-query-input");
    const messagesContainer = document.getElementById("ai-messages-container");

    if (btnToggleAI && chatWindow) {
      btnToggleAI.addEventListener("click", () => {
        chatWindow.classList.toggle("hidden");
        if (!chatWindow.classList.contains("hidden") && queryInput) {
          queryInput.focus();
        }
      });
    }

    if (btnCloseAI && chatWindow) {
      btnCloseAI.addEventListener("click", () => {
        chatWindow.classList.add("hidden");
      });
    }

    if (chatForm && queryInput && messagesContainer) {
      chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = queryInput.value.trim();
        if (!text) return;

        // Append user message
        const userMsg = document.createElement("div");
        userMsg.className = "ai-message user";
        userMsg.textContent = text;
        messagesContainer.appendChild(userMsg);
        queryInput.value = "";
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Append thinking placeholder
        const placeholder = document.createElement("div");
        placeholder.className = "ai-message assistant";
        placeholder.textContent = "Reviewing symptoms and clinical guidelines...";
        messagesContainer.appendChild(placeholder);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
          const res = await API.ai.consult(text);
          const r = res.result;
          
          if (r.is_emergency) {
            placeholder.innerHTML = `
              <div style="background:var(--rose-bg); border:1px solid var(--rose); padding:10px; border-radius:4px; color:#fda4af; font-weight:700;">
                🚨 ${r.response}
              </div>
            `;
          } else {
            // Render structured markdown-style formatting safely
            const formatted = r.response.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
            placeholder.innerHTML = `
              ${formatted}
              <div style="font-size:0.7rem; color:var(--text-muted); margin-top:8px; border-top:1px solid var(--border-subtle); padding-top:4px;">
                ${r.disclaimer}
              </div>
            `;
          }
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } catch (err) {
          placeholder.textContent = "AI Assistant Error: " + err.message;
        }
      });
    }
  }
};

// Start application when DOM is loaded
document.addEventListener("DOMContentLoaded", () => App.init());
