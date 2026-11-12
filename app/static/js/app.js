/**
 * MediApp Main Application Coordinator.
 * SPA routing, portal navigation management, theme toggle, demo switcher, cart drawer,
 * authentication modal, and Clinical Health Assistant chat widget initialization.
 */

const App = {
  async init() {
    console.log("MediApp Initializing Commercial Healthcare Client...");

    // 1. Initialize Theme (Light Mode Default with Dark Mode Option)
    this.initTheme();

    // 2. Fetch current session and capabilities
    try {
      const meRes = await API.auth.getMe();
      if (meRes.authenticated && meRes.user) {
        State.set("user", meRes.user);
        State.set("activeRole", meRes.user.active_role || meRes.user.role);
      } else {
        State.set("user", null);
        State.set("activeRole", "customer");
      }
      State.set("capabilities", meRes.capabilities || {});
    } catch (err) {
      console.warn("Could not retrieve session:", err);
    }

    // 3. Check for OAuth callback URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has("auth_error")) {
      const err = urlParams.get("auth_error");
      Components.toast(`Authentication Notice: ${err}`, "error", 6000);
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (urlParams.has("login_success")) {
      const user = State.get("user");
      const roleParam = urlParams.get("role");
      if (user && roleParam && Array.isArray(user.authorized_roles) && user.authorized_roles.includes(roleParam)) {
        State.set("activeRole", roleParam);
      } else if (user) {
        State.set("activeRole", user.active_role || user.role || "customer");
      }
      Components.toast("Signed in successfully via Google OAuth 2.0!", "success");
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    // 4. Wire Global Header, Location & Navigation Listeners
    this.bindHeaderEvents();

    // 5. Wire Demo Role Switcher
    this.bindDemoSwitcher();

    // 6. Wire Slide-over Cart & Modals
    this.bindCartAndModals();

    // 7. Wire Auth & Registration Modal
    this.bindAuthModal();

    // 8. Wire Clinical Ailment Assistant Widget
    this.bindAIAssistant();

    // 9. Wire Footer Navigation Links
    this.bindFooterEvents();

    // 10. Initial render of Portal
    const initialRole = State.get("activeRole") || "customer";
    this.switchPortal(initialRole);

    // 11. Refresh cart count
    await CustomerPortal.refreshCart();
  },

  initTheme() {
    const savedTheme = localStorage.getItem("mediapp_theme") || "light";
    this.applyTheme(savedTheme);

    const toggleBtn = document.getElementById("btn-theme-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        const isDark = document.body.classList.contains("theme-dark");
        const nextTheme = isDark ? "light" : "dark";
        this.applyTheme(nextTheme);
        localStorage.setItem("mediapp_theme", nextTheme);
        Components.toast(`Switched to ${nextTheme === 'dark' ? 'Dark' : 'Light'} theme`, "info", 2000);
      });
    }
  },

  applyTheme(theme) {
    const sunIcon = document.getElementById("theme-icon-sun");
    const moonIcon = document.getElementById("theme-icon-moon");

    if (theme === "dark") {
      document.body.classList.remove("theme-light");
      document.body.classList.add("theme-dark");
      if (sunIcon) sunIcon.style.display = "block";
      if (moonIcon) moonIcon.style.display = "none";
    } else {
      document.body.classList.remove("theme-dark");
      document.body.classList.add("theme-light");
      if (sunIcon) sunIcon.style.display = "none";
      if (moonIcon) moonIcon.style.display = "block";
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

    // Quick Rx Upload Header Button
    document.getElementById("btn-header-upload-rx")?.addEventListener("click", () => {
      CustomerPortal.openPrescriptionUploadModal();
    });

    // Delivery Location Picker
    document.getElementById("header-location-picker")?.addEventListener("click", async () => {
      const pin = await Components.promptDialog("Change Delivery Location", "Enter delivery pincode or area (e.g. 560038, Indiranagar):", "Bengaluru 560038");
      if (pin && pin.trim()) {
        const valEl = document.querySelector("#header-location-picker .location-val");
        if (valEl) valEl.textContent = `${Components.escapeHtml(pin.trim())} ▾`;
        Components.toast(`Delivery address updated to ${pin.trim()}`, "success");
      }
    });
  },

  bindFooterEvents() {
    document.querySelectorAll(".footer-link-action").forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const cat = link.dataset.cat;
        State.set("activeRole", "customer");
        State.set("activeTab", "catalogue");
        State.set("selectedCategory", cat);
        this.switchPortal("customer");
        window.scrollTo({ top: 350, behavior: "smooth" });
      });
    });
  },

  bindDemoSwitcher() {
    const switcher = document.getElementById("demo-switcher");
    if (!switcher) return;

    const caps = State.get("capabilities") || {};
    if (caps.app_mode === "real") {
      switcher.style.display = "none";
      return;
    }

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

  bindAuthModal() {
    const btnCloseAuth = document.getElementById("btn-close-auth");
    const tabSignIn = document.getElementById("tab-btn-signin");
    const tabRegister = document.getElementById("tab-btn-register");
    const paneSignIn = document.getElementById("auth-signin-pane");
    const paneRegister = document.getElementById("auth-register-pane");

    if (btnCloseAuth) {
      btnCloseAuth.addEventListener("click", () => Components.closeModal("auth-modal"));
    }

    if (tabSignIn && tabRegister && paneSignIn && paneRegister) {
      tabSignIn.addEventListener("click", () => {
        tabSignIn.classList.add("active");
        tabRegister.classList.remove("active");
        paneSignIn.classList.remove("hidden");
        paneRegister.classList.add("hidden");
      });

      tabRegister.addEventListener("click", () => {
        tabRegister.classList.add("active");
        tabSignIn.classList.remove("active");
        paneRegister.classList.remove("hidden");
        paneSignIn.classList.add("hidden");
      });
    }

    // Sign In form submit
    const formSignIn = document.getElementById("form-signin");
    if (formSignIn) {
      formSignIn.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("signin-email").value.trim();
        const password = document.getElementById("signin-password").value;
        const btnSubmit = document.getElementById("btn-submit-signin");
        btnSubmit.disabled = true;
        btnSubmit.textContent = "Signing In...";

        try {
          const res = await API.auth.login(email, password);
          State.set("user", res.user);
          State.set("activeRole", res.user.role);
          Components.toast(`Welcome back, ${res.user.full_name}!`, "success");
          Components.closeModal("auth-modal");
          this.switchPortal(res.user.role);
          await CustomerPortal.refreshCart();
        } catch (err) {
          Components.toast(err.message, "error");
        } finally {
          btnSubmit.disabled = false;
          btnSubmit.textContent = "Sign In";
        }
      });
    }

    // Register form submit
    const formRegister = document.getElementById("form-register");
    if (formRegister) {
      formRegister.addEventListener("submit", async (e) => {
        e.preventDefault();
        const full_name = document.getElementById("reg-name").value.trim();
        const email = document.getElementById("reg-email").value.trim();
        const phone = document.getElementById("reg-phone").value.trim();
        const password = document.getElementById("reg-password").value;
        const address = document.getElementById("reg-address").value.trim();
        const btnSubmit = document.getElementById("btn-submit-register");
        btnSubmit.disabled = true;
        btnSubmit.textContent = "Creating Account...";

        try {
          const payload = {
            full_name, email, phone, password,
            address: address ? { address_line1: address, city: "Bengaluru", state: "Karnataka", pincode: "560038" } : null
          };
          const res = await API.auth.register(payload);
          State.set("user", res.user);
          State.set("activeRole", "customer");
          Components.toast(`Account created successfully! Welcome, ${res.user.full_name}`, "success");
          Components.closeModal("auth-modal");
          this.switchPortal("customer");
          await CustomerPortal.refreshCart();
        } catch (err) {
          Components.toast(err.message, "error");
        } finally {
          btnSubmit.disabled = false;
          btnSubmit.textContent = "Create Customer Account";
        }
      });
    }

    // Google Sign-In trigger
    const btnGoogle = document.getElementById("btn-google-signin");
    const googleNotice = document.getElementById("google-auth-notice");
    if (btnGoogle) {
      btnGoogle.addEventListener("click", async () => {
        const caps = State.get("capabilities") || {};
        if (!caps.google_oauth_configured) {
          if (googleNotice) {
            googleNotice.textContent = "Google OAuth credentials are not configured on this server.";
            googleNotice.style.color = "var(--rose)";
          }
          Components.toast("Google OAuth is not configured in server environment.", "warning");
          return;
        }

        try {
          const res = await API.auth.getGoogleUrl();
          if (res.url) {
            window.location.href = res.url;
          }
        } catch (err) {
          Components.toast("Failed to initiate Google OAuth: " + err.message, "error");
        }
      });
    }

    // Quick demo buttons in auth modal
    document.querySelectorAll(".btn-quick-demo").forEach(btn => {
      btn.addEventListener("click", async () => {
        const role = btn.dataset.role;
        try {
          const res = await API.auth.demoLogin(role);
          State.set("user", res.user);
          State.set("activeRole", res.user.role);
          Components.toast(`Logged into Demo ${role.toUpperCase()} account (${res.user.full_name})`, "info");
          Components.closeModal("auth-modal");
          this.switchPortal(role);
          await CustomerPortal.refreshCart();
        } catch (err) {
          Components.toast("Demo login failed: " + err.message, "error");
        }
      });
    });
  },

  switchPortal(role) {
    const user = State.get("user");
    const caps = State.get("capabilities") || {};

    // In real mode, check authorization
    if (caps.app_mode === "real" && role !== "customer") {
      if (!user) {
        Components.toast(`Please sign in with authorized credentials to access ${role} portal.`, "warning");
        Components.openModal("auth-modal");
        return;
      }
      const authorizedRoles = user.authorized_roles || [user.role];
      if (!authorizedRoles.includes(role)) {
        Components.toast(`Access Denied: Your account is not authorized for the ${role} portal.`, "error");
        return;
      }
    }

    State.set("activeRole", role);
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
        ${Components.escapeHtml(t.label)}
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
      const activeRole = State.get("activeRole") || user.role;
      const roleBadgeClass = activeRole === 'admin' ? 'badge-rx' : (activeRole === 'pharmacy' ? 'badge-category' : (activeRole === 'delivery' ? 'badge-otc' : 'badge-category'));

      container.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px;">
          <div class="user-badge-btn" id="btn-user-badge" title="${Components.escapeHtml(user.email)}">
            <div class="user-avatar-circle">${Components.escapeHtml(user.full_name.charAt(0).toUpperCase())}</div>
            <span style="font-weight:600; max-width:90px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${Components.escapeHtml(user.full_name.split(' ')[0])}</span>
            <span class="badge ${roleBadgeClass}">${Components.escapeHtml(activeRole)}</span>
          </div>
          <button type="button" class="btn-alt-pill" id="btn-header-logout" title="Sign Out of Account" style="padding:6px 12px; font-size:0.75rem; border-color:var(--border-subtle);">
            Sign Out
          </button>
        </div>
      `;

      document.getElementById("btn-header-logout")?.addEventListener("click", async () => {
        try {
          await API.auth.logout();
          State.set("user", null);
          State.set("activeRole", "customer");
          Components.toast("Signed out successfully.", "info");
          this.switchPortal("customer");
          await CustomerPortal.refreshCart();
        } catch (err) {
          Components.toast("Logout error: " + err.message, "error");
        }
      });
    } else {
      container.innerHTML = `
        <button type="button" class="btn-checkout-primary" id="btn-header-login" style="padding:8px 16px; margin:0; font-size:0.85rem; width:auto; background:var(--primary);">
          Sign In / Register
        </button>
      `;
      document.getElementById("btn-header-login")?.addEventListener("click", () => {
        Components.openModal("auth-modal");
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
        placeholder.textContent = "Analyzing symptoms against clinical safety guidelines...";
        messagesContainer.appendChild(placeholder);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
          const res = await API.ai.consult(text);
          const r = res.result;
          
          if (r.is_emergency) {
            placeholder.innerHTML = `
              <div style="background:var(--rose-bg); border:1px solid var(--rose); padding:10px; border-radius:var(--radius-sm); color:var(--rose); font-weight:700;">
                🚨 EMERGENCY ALERT: ${Components.escapeHtml(r.response)}
              </div>
            `;
          } else {
            // Render structured markdown-style formatting safely
            const safeContent = Components.escapeHtml(r.response);
            const formatted = safeContent.replace(/\n/g, "<br>").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
            placeholder.innerHTML = `
              ${formatted}
              <div style="font-size:0.7rem; color:var(--text-muted); margin-top:8px; border-top:1px solid var(--border-subtle); padding-top:4px;">
                ${Components.escapeHtml(r.disclaimer || 'Guidance provided for non-emergency educational and triage reference only.')}
              </div>
            `;
          }
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        } catch (err) {
          placeholder.textContent = "Assistant Notice: " + err.message;
        }
      });
    }
  }
};

// Start application when DOM is loaded
document.addEventListener("DOMContentLoaded", () => App.init());
