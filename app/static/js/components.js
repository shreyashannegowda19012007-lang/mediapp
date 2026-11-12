/**
 * MediApp UI Component Helpers.
 * Modals, Toasts, Confirmation Dialogs, Formatters, and Status Badges.
 */

const Components = {
  // DOM XSS Sanitizer Utility (Entity Encoding)
  escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },

  // Toast notifications with clean SVG icons
  toast(message, type = "info", duration = 3500) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    
    let iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    if (type === "success") {
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
    } else if (type === "error") {
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`;
    } else if (type === "warning") {
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;
    }

    el.innerHTML = `<span>${iconSvg}</span> <span>${message}</span>`;
    container.appendChild(el);

    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translateX(100%)";
      el.style.transition = "all 0.3s ease";
      setTimeout(() => el.remove(), 300);
    }, duration);
  },

  // Modal helpers
  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove("hidden");
      document.body.style.overflow = "hidden";
    }
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add("hidden");
      document.body.style.overflow = "";
    }
  },

  // Currency & Date formatting
  formatCurrency(amount) {
    const val = Number(amount) || 0;
    return `₹${val.toFixed(2)}`;
  },

  formatDate(dateStr) {
    if (!dateStr) return "N/A";
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch {
      return dateStr;
    }
  },

  // Status Badge Generator
  renderStatusBadge(status) {
    const s = (status || "").toUpperCase();
    const config = {
      "PLACED": { label: "Order Placed", cls: "badge-category" },
      "AWAITING_PRESCRIPTION": { label: "Prescription Needed", cls: "badge-rx" },
      "PRESCRIPTION_VERIFIED": { label: "Pharmacist Verified", cls: "badge-otc" },
      "ACCEPTED": { label: "Accepted by Pharmacy", cls: "badge-category" },
      "PREPARING": { label: "Packaging Medicines", cls: "badge-category" },
      "READY_FOR_PICKUP": { label: "Ready for Pickup", cls: "badge-otc" },
      "DELIVERY_ASSIGNED": { label: "Delivery Partner Assigned", cls: "badge-category" },
      "PICKED_UP": { label: "Picked Up by Courier", cls: "badge-category" },
      "IN_TRANSIT": { label: "Out for Delivery", cls: "badge-otc" },
      "DELIVERED": { label: "Delivered", cls: "badge-otc" },
      "CANCELLED": { label: "Cancelled", cls: "badge-rx" },
      "DELIVERY_FAILED": { label: "Delivery Unsuccessful", cls: "badge-rx" }
    };

    const c = config[s] || { label: status, cls: "badge-category" };
    return `<span class="badge ${c.cls}">${c.label}</span>`;
  },

  renderPaymentBadge(status) {
    const s = (status || "").toLowerCase();
    if (s === "paid") {
      return `<span class="badge badge-otc">Paid</span>`;
    } else if (s === "refunded") {
      return `<span class="badge badge-category">Refunded</span>`;
    } else if (s === "failed") {
      return `<span class="badge badge-rx">Payment Failed</span>`;
    }
    return `<span class="badge badge-category">Payment Pending</span>`;
  },

  // Accessible Non-blocking Prompt Modal Dialog
  async promptDialog(title, message, defaultValue = "") {
    return new Promise((resolve) => {
      let modal = document.getElementById("generic-prompt-modal");
      if (!modal) {
        modal = document.createElement("div");
        modal.id = "generic-prompt-modal";
        modal.className = "modal-backdrop hidden";
        modal.setAttribute("role", "dialog");
        modal.setAttribute("aria-modal", "true");
        modal.innerHTML = `
          <div class="modal-card">
            <div class="modal-header">
              <h3 id="prompt-modal-title" style="margin:0;">Confirm Action</h3>
              <button type="button" class="btn-close-modal" id="btn-close-prompt">&times;</button>
            </div>
            <div class="modal-body" style="padding:20px;">
              <p id="prompt-modal-message" style="margin-bottom:12px; color:var(--text-secondary);"></p>
              <input type="text" id="prompt-modal-input" class="input-main-search" style="width:100%; margin-bottom:16px;" />
              <div style="display:flex; justify-content:flex-end; gap:10px;">
                <button type="button" class="btn-alt-pill" id="btn-prompt-cancel" style="padding:8px 16px;">Cancel</button>
                <button type="button" class="btn-add-cart" id="btn-prompt-submit" style="padding:8px 16px;">Confirm</button>
              </div>
            </div>
          </div>
        `;
        document.body.appendChild(modal);
      }

      const titleEl = modal.querySelector("#prompt-modal-title");
      const msgEl = modal.querySelector("#prompt-modal-message");
      const inputEl = modal.querySelector("#prompt-modal-input");
      const btnClose = modal.querySelector("#btn-close-prompt");
      const btnCancel = modal.querySelector("#btn-prompt-cancel");
      const btnSubmit = modal.querySelector("#btn-prompt-submit");

      titleEl.textContent = title;
      msgEl.textContent = message;
      inputEl.value = defaultValue;

      const cleanup = () => {
        modal.classList.add("hidden");
        document.body.style.overflow = "";
      };

      const onConfirm = () => {
        const val = inputEl.value;
        cleanup();
        resolve(val);
      };

      const onCancel = () => {
        cleanup();
        resolve(null);
      };

      btnClose.onclick = onCancel;
      btnCancel.onclick = onCancel;
      btnSubmit.onclick = onConfirm;
      inputEl.onkeydown = (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          onConfirm();
        }
        if (e.key === "Escape") {
          e.preventDefault();
          onCancel();
        }
      };

      modal.classList.remove("hidden");
      document.body.style.overflow = "hidden";
      inputEl.focus();
    });
  }
};

// Global Escape key handler for accessible modal dismissal
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-backdrop:not(.hidden)").forEach(m => {
      m.classList.add("hidden");
    });
    const drawer = document.getElementById("cart-drawer-overlay");
    if (drawer && !drawer.classList.contains("hidden")) {
      drawer.classList.add("hidden");
    }
    const aiWindow = document.getElementById("ai-chat-window");
    if (aiWindow && !aiWindow.classList.contains("hidden")) {
      aiWindow.classList.add("hidden");
    }
    document.body.style.overflow = "";
  }
});
