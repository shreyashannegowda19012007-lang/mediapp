/**
 * MediApp Pharmacy / Shop Portal.
 * Live operational metrics, order acceptance and fulfilment workflow,
 * prescription verification, and pharmacy inventory management.
 */

const PharmacyPortal = {
  async init(tab = "dashboard") {
    Sync.stopAll();
    const container = document.getElementById("main-content");

    if (tab === "dashboard") {
      await this.renderDashboard(container);
    } else if (tab === "orders") {
      await this.renderOrders(container);
    } else if (tab === "inventory") {
      await this.renderInventory(container);
    } else if (tab === "prescriptions") {
      await this.renderPrescriptionReview(container);
    }
  },

  async renderDashboard(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <div>
          <h2>Pharmacy Fulfillment Dashboard</h2>
          <p style="color:var(--text-secondary); font-size:0.9rem;" id="pharmacy-header-meta">Loading pharmacy operations...</p>
        </div>
        <button type="button" class="btn-demo-pill" id="btn-refresh-pharm-dash">↻ Refresh Operations</button>
      </div>

      <div class="stats-grid" id="pharmacy-stats-grid">
        <div class="stat-card"><div class="stat-label">Loading Metrics...</div></div>
      </div>

      <h3 style="margin: 28px 0 16px 0;">Live Orders Awaiting Fulfillment</h3>
      <div id="pharmacy-live-orders">
        <div class="loading-screen"><div class="spinner"></div><p>Fetching active pharmacy queue...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-pharm-dash").addEventListener("click", () => this.fetchDashboardData());

    // Register auto-polling
    Sync.register("pharmacy_dashboard", () => this.fetchDashboardData(), 5000);
    await this.fetchDashboardData();
  },

  async fetchDashboardData() {
    const metaEl = document.getElementById("pharmacy-header-meta");
    const statsGrid = document.getElementById("pharmacy-stats-grid");
    const ordersList = document.getElementById("pharmacy-live-orders");
    if (!statsGrid || !ordersList) return;

    try {
      const res = await API.pharmacy.getDashboard();
      const p = res.pharmacy;
      const m = res.metrics;
      const queue = res.active_queue || [];

      if (metaEl) {
        metaEl.innerHTML = `<strong>${p.name}</strong> • License: <code>${p.license_number}</code> • ${p.address} • Rating: ⭐ ${p.rating}`;
      }

      statsGrid.innerHTML = `
        <div class="stat-card stat-accent">
          <div class="stat-label">New Orders</div>
          <div class="stat-val">${m.new_orders}</div>
        </div>
        <div class="stat-card stat-warning">
          <div class="stat-label">Rx Review Queue</div>
          <div class="stat-val">${m.prescription_review}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Accepted / In Prep</div>
          <div class="stat-val">${m.accepted_orders + m.preparing_orders}</div>
        </div>
        <div class="stat-card stat-success">
          <div class="stat-label">Ready for Pickup</div>
          <div class="stat-val">${m.ready_for_pickup}</div>
        </div>
        <div class="stat-card stat-success">
          <div class="stat-label">Total Revenue</div>
          <div class="stat-val">${Components.formatCurrency(m.total_revenue)}</div>
        </div>
        <div class="stat-card stat-warning">
          <div class="stat-label">Low Stock Alerts</div>
          <div class="stat-val">${m.low_stock_alerts}</div>
        </div>
      `;

      if (queue.length === 0) {
        ordersList.innerHTML = `
          <div style="text-align:center; padding: 40px; background:var(--bg-card); border-radius:var(--radius-md); color:var(--text-muted);">
            No active orders waiting in the pharmacy queue.
          </div>
        `;
        return;
      }

      ordersList.innerHTML = queue.map(ord => `
        <div class="order-tracking-card" data-id="${ord.id}">
          <div class="tracking-header">
            <div>
              <div style="font-size:0.75rem; color:var(--text-muted);">Order ID</div>
              <div style="font-size: 1.25rem; font-weight:800; color:#fff;">${ord.id}</div>
              <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:2px;">
                Customer: <strong>${ord.customer_name}</strong> (${ord.customer_phone}) • ${Components.formatDate(ord.created_at)}
              </div>
            </div>
            <div style="text-align:right;">
              <div style="font-size: 1.3rem; font-weight:800; color:#fff;">${Components.formatCurrency(ord.total_amount)}</div>
              <div>${Components.renderStatusBadge(ord.order_status)}</div>
            </div>
          </div>

          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-top:14px;">
            <div style="font-size:0.85rem; color:var(--text-secondary);">
              Notes: ${ord.delivery_notes || 'Standard delivery'}
            </div>
            <div style="display:flex; gap:8px;">
              ${ord.order_status === "PLACED" ? `
                <button type="button" class="btn-checkout-primary btn-accept-order" data-id="${ord.id}" style="width:auto; padding:8px 16px; margin:0; background:var(--emerald);">
                  Accept Order
                </button>
                <button type="button" class="btn-alt-pill btn-reject-order" data-id="${ord.id}" style="color:var(--rose); border-color:var(--rose);">
                  Reject
                </button>
              ` : ''}

              ${ord.order_status === "ACCEPTED" ? `
                <button type="button" class="btn-checkout-primary btn-prep-order" data-id="${ord.id}" style="width:auto; padding:8px 16px; margin:0;">
                  Start Packaging
                </button>
              ` : ''}

              ${ord.order_status === "PREPARING" ? `
                <button type="button" class="btn-checkout-primary btn-ready-order" data-id="${ord.id}" style="width:auto; padding:8px 16px; margin:0; background:var(--emerald);">
                  Mark Ready for Pickup
                </button>
              ` : ''}

              <button type="button" class="btn-alt-pill btn-inspect-order" data-id="${ord.id}">
                Inspect Order
              </button>
            </div>
          </div>
        </div>
      `).join("");

      ordersList.querySelectorAll(".btn-accept-order").forEach(b => {
        b.addEventListener("click", () => this.handleAcceptOrder(b.dataset.id));
      });
      ordersList.querySelectorAll(".btn-reject-order").forEach(b => {
        b.addEventListener("click", () => this.handleRejectOrder(b.dataset.id));
      });
      ordersList.querySelectorAll(".btn-prep-order").forEach(b => {
        b.addEventListener("click", () => this.handleTransition(b.dataset.id, "PREPARING", "Pharmacy packaging items"));
      });
      ordersList.querySelectorAll(".btn-ready-order").forEach(b => {
        b.addEventListener("click", () => this.handleTransition(b.dataset.id, "READY_FOR_PICKUP", "Package ready for rider pickup"));
      });
      ordersList.querySelectorAll(".btn-inspect-order").forEach(b => {
        b.addEventListener("click", () => CustomerPortal.showOrderDetailsModal(b.dataset.id));
      });

    } catch (err) {
      statsGrid.innerHTML = `<div style="color:var(--rose);">Error loading dashboard: ${err.message}</div>`;
    }
  },

  async handleAcceptOrder(orderId) {
    try {
      await API.pharmacy.acceptOrder(orderId);
      Components.toast(`Order ${orderId} accepted!`, "success");
      await this.fetchDashboardData();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async handleRejectOrder(orderId) {
    const reason = prompt("Please provide a rejection reason (e.g. Stock shortage, prescription mismatch):", "Out of stock for prescribed batch");
    if (!reason) return;
    try {
      await API.pharmacy.rejectOrder(orderId, reason);
      Components.toast(`Order ${orderId} rejected. Inventory restored.`, "info");
      await this.fetchDashboardData();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async handleTransition(orderId, targetStatus, notes) {
    try {
      await API.orders.transition(orderId, targetStatus, notes);
      Components.toast(`Order ${orderId} updated to ${targetStatus}.`, "success");
      await this.fetchDashboardData();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async renderOrders(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <h2>Pharmacy Order Management</h2>
        <div style="display:flex; gap:10px;">
          <select id="pharm-order-status-filter" class="select-styled">
            <option value="">All Orders</option>
            <option value="PLACED">Placed</option>
            <option value="ACCEPTED">Accepted</option>
            <option value="PREPARING">Preparing</option>
            <option value="READY_FOR_PICKUP">Ready for Pickup</option>
            <option value="DELIVERED">Delivered</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
          <button type="button" class="btn-demo-pill" id="btn-refresh-orders-tab">↻ Refresh</button>
        </div>
      </div>
      <div id="pharmacy-orders-table-wrapper">
        <div class="loading-screen"><div class="spinner"></div><p>Loading pharmacy orders...</p></div>
      </div>
    `;

    const filterSelect = document.getElementById("pharm-order-status-filter");
    filterSelect.addEventListener("change", () => this.fetchOrdersTable(filterSelect.value));
    document.getElementById("btn-refresh-orders-tab").addEventListener("click", () => this.fetchOrdersTable(filterSelect.value));

    await this.fetchOrdersTable();
  },

  async fetchOrdersTable(status = "") {
    const wrapper = document.getElementById("pharmacy-orders-table-wrapper");
    if (!wrapper) return;

    try {
      const res = await API.pharmacy.getOrders(status);
      const orders = res.orders || [];

      if (orders.length === 0) {
        wrapper.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted); background:var(--bg-card); border-radius:var(--radius-md);">No orders found for selected filter.</div>`;
        return;
      }

      wrapper.innerHTML = `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Created At</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${orders.map(o => `
                <tr>
                  <td><strong>${o.id}</strong></td>
                  <td>${o.customer_name} (${o.customer_phone})</td>
                  <td>${Components.formatDate(o.created_at)}</td>
                  <td><strong>${Components.formatCurrency(o.total_amount)}</strong></td>
                  <td>${Components.renderStatusBadge(o.order_status)}</td>
                  <td>${Components.renderPaymentBadge(o.payment_status)}</td>
                  <td>
                    <button type="button" class="btn-alt-pill btn-inspect-table-order" data-id="${o.id}">
                      Inspect
                    </button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;

      wrapper.querySelectorAll(".btn-inspect-table-order").forEach(b => {
        b.addEventListener("click", () => CustomerPortal.showOrderDetailsModal(b.dataset.id));
      });

    } catch (err) {
      wrapper.innerHTML = `<div style="color:var(--rose);">Error loading orders: ${err.message}</div>`;
    }
  },

  async renderInventory(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px; flex-wrap:wrap; gap:16px;">
        <div>
          <h2>Pharmacy Inventory Management</h2>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Maintain real-time medicine stock, adjust unit pricing, and configure batch thresholds.</p>
        </div>
        <div style="display:flex; gap:10px;">
          <input type="text" id="inv-search-input" class="form-control" placeholder="Search stocked medicines..." style="width:250px;">
          <button type="button" class="btn-demo-pill" id="btn-toggle-low-stock">Show Low Stock Only</button>
        </div>
      </div>

      <div id="pharmacy-inventory-container">
        <div class="loading-screen"><div class="spinner"></div><p>Loading pharmacy inventory...</p></div>
      </div>
    `;

    let lowStockActive = false;
    const searchInput = document.getElementById("inv-search-input");
    const lowStockBtn = document.getElementById("btn-toggle-low-stock");

    searchInput.addEventListener("input", (e) => {
      clearTimeout(this._invSearchTimer);
      this._invSearchTimer = setTimeout(() => {
        this.fetchInventoryTable(e.target.value, lowStockActive);
      }, 300);
    });

    lowStockBtn.addEventListener("click", () => {
      lowStockActive = !lowStockActive;
      lowStockBtn.classList.toggle("active", lowStockActive);
      this.fetchInventoryTable(searchInput.value, lowStockActive);
    });

    await this.fetchInventoryTable();
  },

  async fetchInventoryTable(q = "", lowStockOnly = false) {
    const container = document.getElementById("pharmacy-inventory-container");
    if (!container) return;

    try {
      const res = await API.pharmacy.getInventory({ q, low_stock: lowStockOnly ? true : "" });
      const inventory = res.inventory || [];

      if (inventory.length === 0) {
        container.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted); background:var(--bg-card); border-radius:var(--radius-md);">No inventory records found.</div>`;
        return;
      }

      container.innerHTML = `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Medicine Name</th>
                <th>Generic / Molecule</th>
                <th>Strength</th>
                <th>Batch #</th>
                <th>Unit Price</th>
                <th>Stock Units</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${inventory.map(it => {
                const isLow = it.stock_quantity <= it.low_stock_threshold;
                return `
                  <tr>
                    <td><strong>${it.name}</strong></td>
                    <td style="color:var(--cyan);">${it.generic_name}</td>
                    <td>${it.strength}</td>
                    <td><code>${it.batch_number || 'N/A'}</code></td>
                    <td>${Components.formatCurrency(it.unit_price)}</td>
                    <td>
                      <span style="font-weight:700; ${isLow ? 'color:var(--amber);' : 'color:var(--emerald);'}">
                        ${it.stock_quantity}
                      </span>
                      ${isLow ? '<span class="badge-rx" style="margin-left:4px; font-size:0.65rem;">LOW</span>' : ''}
                    </td>
                    <td>
                      <span class="badge ${it.is_available ? 'badge-otc' : 'badge-rx'}">
                        ${it.is_available ? 'Available' : 'Unavailable'}
                      </span>
                    </td>
                    <td>
                      <button type="button" class="btn-alt-pill btn-edit-stock"
                              data-id="${it.medicine_id}"
                              data-name="${it.name}"
                              data-qty="${it.stock_quantity}"
                              data-price="${it.unit_price}"
                              data-avail="${it.is_available}">
                        Edit Stock
                      </button>
                    </td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      `;

      container.querySelectorAll(".btn-edit-stock").forEach(b => {
        b.addEventListener("click", () => this.openEditStockModal({
          medicine_id: parseInt(b.dataset.id),
          name: b.dataset.name,
          qty: parseInt(b.dataset.qty),
          price: parseFloat(b.dataset.price),
          avail: b.dataset.avail === "1" || b.dataset.avail === "true"
        }));
      });

    } catch (err) {
      container.innerHTML = `<div style="color:var(--rose);">Error loading inventory: ${err.message}</div>`;
    }
  },

  openEditStockModal(item) {
    const modalContent = document.getElementById("order-detail-content");
    document.getElementById("order-detail-title").textContent = `Update Stock — ${item.name}`;

    modalContent.innerHTML = `
      <form id="edit-stock-form">
        <div class="form-group">
          <label class="form-label">Available Stock Quantity (Units) *</label>
          <input type="number" id="edit-stock-qty" class="form-control" min="0" value="${item.qty}" required>
        </div>
        <div class="form-group">
          <label class="form-label">Unit Selling Price (₹) *</label>
          <input type="number" step="0.01" id="edit-stock-price" class="form-control" min="0" value="${item.price}" required>
        </div>
        <div class="form-group" style="display:flex; align-items:center; gap:10px; margin-top:16px;">
          <input type="checkbox" id="edit-stock-avail" ${item.avail ? 'checked' : ''} style="width:18px; height:18px;">
          <label for="edit-stock-avail" style="font-size:0.9rem; cursor:pointer;">Available for Customer Ordering</label>
        </div>
        <button type="submit" class="btn-checkout-primary" style="margin-top:20px;">
          Save Stock Changes
        </button>
      </form>
    `;

    document.getElementById("edit-stock-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const newQty = parseInt(document.getElementById("edit-stock-qty").value);
      const newPrice = parseFloat(document.getElementById("edit-stock-price").value);
      const newAvail = document.getElementById("edit-stock-avail").checked;

      try {
        await API.pharmacy.updateInventory(item.medicine_id, {
          quantity: newQty,
          unit_price: newPrice,
          is_available: newAvail
        });
        Components.toast("Inventory stock updated successfully.", "success");
        Components.closeModal("order-detail-modal");
        await this.fetchInventoryTable();
      } catch (err) {
        Components.toast(err.message, "error");
      }
    });

    Components.openModal("order-detail-modal");
  },

  async renderPrescriptionReview(container) {
    container.innerHTML = `
      <h2>Pharmacist Prescription Verification Queue</h2>
      <p style="color:var(--text-secondary); font-size:0.9rem; margin-bottom:20px;">Review customer prescriptions, verify OCR candidates, and approve or reject with clinical rationales.</p>
      <div id="rx-review-queue-container">
        <div class="loading-screen"><div class="spinner"></div><p>Loading prescription review queue...</p></div>
      </div>
    `;

    try {
      const res = await API.prescriptions.list();
      const list = res.prescriptions || [];
      const queueContainer = document.getElementById("rx-review-queue-container");

      if (list.length === 0) {
        queueContainer.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted); background:var(--bg-card); border-radius:var(--radius-md);">No prescriptions currently awaiting review.</div>`;
        return;
      }

      queueContainer.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap:20px;">
          ${list.map(p => `
            <div class="medicine-card">
              <div>
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                  <span class="badge ${p.status === 'verified' ? 'badge-otc' : (p.status === 'rejected' ? 'badge-rx' : 'badge-pulse')}">${p.status.toUpperCase()}</span>
                  <span style="font-size:0.75rem; color:var(--text-muted);">${Components.formatDate(p.created_at)}</span>
                </div>
                <h4>${p.original_filename}</h4>
                <div style="font-size:0.85rem; color:var(--text-secondary); margin:4px 0;">Customer: <strong>${p.customer_name || 'Customer'}</strong> (${p.customer_email || ''})</div>
                <div style="font-size:0.85rem; color:var(--cyan);">Doctor: ${p.doctor_name || 'Unspecified'}</div>
                <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Confidence: ${Math.round((p.ocr_confidence || 0) * 100)}% (${p.ocr_provider})</div>

                ${p.extracted_medicines && p.extracted_medicines.length > 0 ? `
                  <div style="margin-top:10px; background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:4px; font-size:0.8rem;">
                    <strong>Candidate Extracted Items:</strong>
                    <ul style="margin-left:16px; margin-top:4px;">
                      ${p.extracted_medicines.map(m => `<li>${m}</li>`).join("")}
                    </ul>
                  </div>
                ` : ''}
              </div>

              <div style="display:flex; gap:8px; margin-top:16px; border-top:1px solid var(--border-subtle); padding-top:12px;">
                <a href="/api/prescriptions/${p.id}/file" target="_blank" class="btn-alt-pill" style="text-align:center; flex:1;">Inspect File</a>
                ${p.status === "pending" || p.status === "under_review" ? `
                  <button type="button" class="btn-checkout-primary btn-approve-rx" data-id="${p.id}" style="width:auto; padding:6px 14px; margin:0; background:var(--emerald);">Approve</button>
                  <button type="button" class="btn-alt-pill btn-reject-rx" data-id="${p.id}" style="color:var(--rose); border-color:var(--rose);">Reject</button>
                ` : ''}
              </div>
            </div>
          `).join("")}
        </div>
      `;

      queueContainer.querySelectorAll(".btn-approve-rx").forEach(b => {
        b.addEventListener("click", () => this.handleVerifyPrescription(parseInt(b.dataset.id), "verified"));
      });
      queueContainer.querySelectorAll(".btn-reject-rx").forEach(b => {
        b.addEventListener("click", () => this.handleVerifyPrescription(parseInt(b.dataset.id), "rejected"));
      });

    } catch (err) {
      document.getElementById("rx-review-queue-container").innerHTML = `<div style="color:var(--rose);">${err.message}</div>`;
    }
  },

  async handleVerifyPrescription(rxId, decision) {
    let rejectionReason = null;
    if (decision === "rejected") {
      rejectionReason = prompt("Enter clinical rejection reason (e.g. Expired date, missing doctor signature):", "Doctor signature missing or blurred");
      if (!rejectionReason) return;
    }

    try {
      await API.prescriptions.verify(rxId, decision, rejectionReason);
      Components.toast(`Prescription #${rxId} marked as ${decision}.`, "success");
      await this.init("prescriptions");
    } catch (err) {
      Components.toast(err.message, "error");
    }
  }
};
