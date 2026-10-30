/**
 * MediApp Delivery Personnel Portal.
 * Manages available delivery pool, active delivery workflow execution,
 * pickup confirmations, proof-of-delivery submission, and earnings history.
 */

const DeliveryPortal = {
  async init(tab = "active") {
    Sync.stopAll();
    const container = document.getElementById("main-content");

    if (tab === "active") {
      await this.renderActiveDelivery(container);
    } else if (tab === "available") {
      await this.renderAvailablePool(container);
    } else if (tab === "history") {
      await this.renderHistory(container);
    }
  },

  async renderActiveDelivery(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <div>
          <h2>Active Delivery Assignment</h2>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Follow step-by-step verified fulfillment milestones to complete handover.</p>
        </div>
        <div style="display:flex; gap:10px;">
          <button type="button" class="btn-demo-pill" id="btn-refresh-active-deliv">↻ Refresh Status</button>
        </div>
      </div>
      <div id="active-delivery-container">
        <div class="loading-screen"><div class="spinner"></div><p>Checking active assignments...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-active-deliv").addEventListener("click", () => this.fetchActiveDelivery());

    // Register auto-polling
    Sync.register("active_delivery", () => this.fetchActiveDelivery(), 4000);
    await this.fetchActiveDelivery();
  },

  async fetchActiveDelivery() {
    const container = document.getElementById("active-delivery-container");
    if (!container) return;

    try {
      const res = await API.delivery.getActive();
      const ord = res.active_order;

      if (!ord) {
        container.innerHTML = `
          <div style="text-align:center; padding: 60px 20px; background:var(--bg-card); border-radius:var(--radius-md);">
            <p style="font-size:1.2rem; color:var(--text-secondary); margin-bottom:8px;">No active delivery in progress.</p>
            <p style="font-size:0.875rem; color:var(--text-muted); margin-bottom:20px;">You are currently available for new dispatch requests.</p>
            <button type="button" class="btn-checkout-primary" id="btn-goto-available" style="width:auto; display:inline-block; margin:0; padding:10px 24px;">
              View Available Orders Pool
            </button>
          </div>
        `;
        const gotoBtn = document.getElementById("btn-goto-available");
        if (gotoBtn) {
          gotoBtn.addEventListener("click", () => {
            State.set("activeTab", "available");
            this.init("available");
          });
        }
        return;
      }

      const st = ord.order_status;
      const addr = ord.delivery_address || {};

      container.innerHTML = `
        <div class="order-tracking-card" style="border: 1.5px solid var(--primary);">
          <div class="tracking-header">
            <div>
              <span class="badge badge-pulse">ACTIVE MISSION</span>
              <div style="font-size: 1.4rem; font-weight:800; color:var(--text-primary); margin-top:4px;">${ord.id}</div>
              <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:2px;">
                Earned Delivery Payout: <strong>${Components.formatCurrency(ord.delivery_fee)}</strong>
              </div>
            </div>
            <div style="text-align:right;">
              ${Components.renderStatusBadge(st)}
              <div style="font-size:1.2rem; font-weight:800; color:var(--text-primary); margin-top:4px;">${Components.formatCurrency(ord.total_amount)}</div>
            </div>
          </div>

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin: 20px 0;">
            <!-- Pharmacy Pickup -->
            <div style="background:rgba(255,255,255,0.03); padding:16px; border-radius:var(--radius-sm); border-left:4px solid var(--primary);">
              <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Step 1: Pickup Location</div>
              <div style="font-size:1.1rem; font-weight:700; color:var(--text-primary); margin:4px 0;">${ord.pharmacy_name}</div>
              <div style="font-size:0.85rem; color:var(--text-secondary);">${ord.pharmacy_address}</div>
              <div style="font-size:0.85rem; color:var(--primary); margin-top:4px;">📞 Pharmacy: ${ord.pharmacy_phone}</div>
            </div>

            <!-- Customer Destination -->
            <div style="background:var(--bg-canvas); padding:16px; border-radius:var(--radius-md); border-left:4px solid var(--emerald); border:1px solid var(--border-subtle);">
              <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Step 2: Drop-off Location</div>
              <div style="font-size:1.1rem; font-weight:700; color:var(--text-primary); margin:4px 0;">${ord.customer_name}</div>
              <div style="font-size:0.85rem; color:var(--text-secondary);">
                ${addr.line1 || ''}, ${addr.line2 || ''}<br>
                ${addr.city || ''}, ${addr.state || ''} - ${addr.pincode || ''}
              </div>
              <div style="font-size:0.85rem; color:var(--emerald); margin-top:4px;">📞 Customer: ${addr.recipient_phone || ord.customer_phone}</div>
            </div>
          </div>

          <!-- Live Step Actions -->
          <div style="background:var(--bg-canvas); padding:20px; border-radius:var(--radius-sm); margin-top:20px; border:1px solid var(--border-subtle);">
            <h4 style="margin-bottom:12px;">Fulfillment Milestone Actions:</h4>
            <div style="display:flex; gap:12px; flex-wrap:wrap;">
              ${st === "DELIVERY_ASSIGNED" ? `
                <button type="button" class="btn-checkout-primary" id="btn-do-pickup" style="width:auto; margin:0; padding:12px 24px; background:var(--primary);">
                  📦 Confirm Pickup from Pharmacy
                </button>
              ` : ''}

              ${st === "PICKED_UP" ? `
                <button type="button" class="btn-checkout-primary" id="btn-do-transit" style="width:auto; margin:0; padding:12px 24px; background:#0284c7;">
                  🛵 Mark Out for Delivery (In Transit)
                </button>
              ` : ''}

              ${st === "IN_TRANSIT" ? `
                <button type="button" class="btn-checkout-primary" id="btn-do-complete" style="width:auto; margin:0; padding:12px 24px; background:var(--emerald);">
                  ✅ Confirm Handover & Complete Delivery
                </button>
                <button type="button" class="btn-alt-pill" id="btn-do-fail" style="color:var(--rose); border-color:var(--rose); padding:10px 18px;">
                  ⚠️ Report Delivery Failure
                </button>
              ` : ''}

              <button type="button" class="btn-alt-pill" id="btn-inspect-active-details" style="padding:10px 18px;">
                Inspect Package Items (${ord.items.length})
              </button>
            </div>
          </div>
        </div>
      `;

      const pickupBtn = document.getElementById("btn-do-pickup");
      if (pickupBtn) {
        pickupBtn.addEventListener("click", () => this.handlePickup(ord.id));
      }

      const transitBtn = document.getElementById("btn-do-transit");
      if (transitBtn) {
        transitBtn.addEventListener("click", () => this.handleInTransit(ord.id));
      }

      const completeBtn = document.getElementById("btn-do-complete");
      if (completeBtn) {
        completeBtn.addEventListener("click", () => this.handleComplete(ord.id));
      }

      const failBtn = document.getElementById("btn-do-fail");
      if (failBtn) {
        failBtn.addEventListener("click", () => this.handleFail(ord.id));
      }

      const inspectBtn = document.getElementById("btn-inspect-active-details");
      if (inspectBtn) {
        inspectBtn.addEventListener("click", () => CustomerPortal.showOrderDetailsModal(ord.id));
      }

    } catch (err) {
      container.innerHTML = `<div style="color:var(--rose);">Error loading active delivery: ${err.message}</div>`;
    }
  },

  async handlePickup(orderId) {
    try {
      await API.delivery.pickup(orderId);
      Components.toast("Package picked up from pharmacy!", "success");
      await this.fetchActiveDelivery();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async handleInTransit(orderId) {
    try {
      await API.delivery.inTransit(orderId);
      Components.toast("Status updated: In Transit to customer.", "info");
      await this.fetchActiveDelivery();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async handleComplete(orderId) {
    let proof = "Customer handover confirmed at doorstep";
    if (Components.promptDialog) {
      const res = await Components.promptDialog(
        "Confirm Delivery Handover",
        "Enter customer handover confirmation, recipient OTP, or signature note:",
        proof
      );
      if (res === null) return;
      proof = res.trim() || proof;
    } else {
      const res = prompt("Enter customer handover confirmation or OTP / signature note:", proof);
      if (!res) return;
      proof = res.trim();
    }

    try {
      await API.delivery.complete(orderId, proof);
      Components.toast("Delivery confirmed completed! All four portals synchronized.", "success");
      await this.fetchActiveDelivery();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async handleFail(orderId) {
    let reason = "Customer phone unreachable after 3 attempts";
    if (Components.promptDialog) {
      const res = await Components.promptDialog(
        "Report Delivery Failure",
        "Enter failure reason (e.g. Customer unreachable, door locked):",
        reason
      );
      if (res === null) return;
      reason = res.trim() || reason;
    } else {
      const res = prompt("Enter failure reason (e.g. Customer unreachable, door locked):", reason);
      if (!res) return;
      reason = res.trim();
    }

    try {
      await API.delivery.fail(orderId, reason);
      Components.toast("Delivery reported as failed attempt.", "warning");
      await this.fetchActiveDelivery();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async renderAvailablePool(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <div>
          <h2>Available Orders for Delivery</h2>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Orders prepared by pharmacies and ready for rider collection.</p>
        </div>
        <button type="button" class="btn-demo-pill" id="btn-refresh-available">↻ Refresh Pool</button>
      </div>
      <div id="available-deliveries-list">
        <div class="loading-screen"><div class="spinner"></div><p>Checking available orders...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-available").addEventListener("click", () => this.fetchAvailablePool());

    Sync.register("available_pool", () => this.fetchAvailablePool(), 5000);
    await this.fetchAvailablePool();
  },

  async fetchAvailablePool() {
    const listEl = document.getElementById("available-deliveries-list");
    if (!listEl) return;

    try {
      const res = await API.delivery.getAvailable();
      const orders = res.available_orders || [];

      if (orders.length === 0) {
        listEl.innerHTML = `
          <div style="text-align:center; padding: 60px 20px; background:var(--bg-card); border-radius:var(--radius-md);">
            <p style="font-size:1.1rem; color:var(--text-secondary); margin-bottom:8px;">No orders currently ready for pickup.</p>
            <p style="font-size:0.85rem; color:var(--text-muted);">Pharmacies are packaging new orders. New requests will appear automatically.</p>
          </div>
        `;
        return;
      }

      listEl.innerHTML = orders.map(ord => {
        let addr = {};
        try { addr = JSON.parse(ord.delivery_address_json); } catch {}

        return `
          <div class="order-tracking-card" data-id="${ord.id}">
            <div class="tracking-header">
              <div>
                <span class="badge badge-otc">READY FOR PICKUP</span>
                <div style="font-size: 1.25rem; font-weight:800; color:var(--text-primary); margin-top:4px;">${ord.id}</div>
                <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:2px;">
                  Pharmacy: <strong>${ord.pharmacy_name}</strong> (${ord.pharmacy_address})
                </div>
              </div>
              <div style="text-align:right;">
                <div style="font-size: 1.3rem; font-weight:800; color:var(--emerald);">+ ${Components.formatCurrency(ord.delivery_fee)} Payout</div>
                <div style="font-size:0.85rem; color:var(--text-muted);">Order Value: ${Components.formatCurrency(ord.total_amount)}</div>
              </div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-top:14px;">
              <div style="font-size:0.85rem; color:var(--text-secondary);">
                Destination: ${addr.line1 || ''}, ${addr.city || ''} (Phone: ${addr.recipient_phone || 'N/A'})
              </div>
              <button type="button" class="btn-checkout-primary btn-claim-order" data-id="${ord.id}" style="width:auto; margin:0; padding:10px 22px;">
                ⚡ Claim This Delivery
              </button>
            </div>
          </div>
        `;
      }).join("");

      listEl.querySelectorAll(".btn-claim-order").forEach(b => {
        b.addEventListener("click", () => this.handleClaim(b.dataset.id));
      });

    } catch (err) {
      listEl.innerHTML = `<div style="color:var(--rose);">Error loading available orders: ${err.message}</div>`;
    }
  },

  async handleClaim(orderId) {
    try {
      await API.delivery.claim(orderId);
      Components.toast(`Delivery ${orderId} successfully claimed!`, "success");
      State.set("activeTab", "active");
      await this.init("active");
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async renderHistory(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <h2>Completed Deliveries History</h2>
        <button type="button" class="btn-demo-pill" id="btn-refresh-history">↻ Refresh</button>
      </div>
      <div id="delivery-history-container">
        <div class="loading-screen"><div class="spinner"></div><p>Loading delivery history...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-history").addEventListener("click", () => this.fetchHistory());
    await this.fetchHistory();
  },

  async fetchHistory() {
    const container = document.getElementById("delivery-history-container");
    if (!container) return;

    try {
      const res = await API.delivery.getHistory();
      const history = res.history || [];

      if (history.length === 0) {
        container.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted); background:var(--bg-card); border-radius:var(--radius-md);">No completed deliveries in records yet.</div>`;
        return;
      }

      container.innerHTML = `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Pharmacy</th>
                <th>Order Total</th>
                <th>Rider Payout</th>
                <th>Delivery Time</th>
                <th>Proof / Notes</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${history.map(h => `
                <tr>
                  <td><strong>${h.id}</strong></td>
                  <td>${h.pharmacy_name}</td>
                  <td>${Components.formatCurrency(h.total_amount)}</td>
                  <td><strong style="color:var(--emerald);">${Components.formatCurrency(h.delivery_fee)}</strong></td>
                  <td>${Components.formatDate(h.delivery_time || h.created_at)}</td>
                  <td>${h.proof_of_delivery || h.failure_reason || 'Standard handover'}</td>
                  <td>${Components.renderStatusBadge(h.order_status)}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div style="color:var(--rose);">Error loading history: ${err.message}</div>`;
    }
  }
};
