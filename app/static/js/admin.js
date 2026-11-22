/**
 * MediApp Administrator Portal.
 * System-wide analytics, user and pharmacy lifecycle governance,
 * order monitoring, audit history, and live platform diagnostics.
 */

const AdminPortal = {
  async init(tab = "analytics") {
    Sync.stopAll();
    const container = document.getElementById("main-content");

    if (tab === "analytics") {
      await this.renderAnalytics(container);
    } else if (tab === "users") {
      await this.renderUsers(container);
    } else if (tab === "pharmacies") {
      await this.renderPharmacies(container);
    } else if (tab === "orders") {
      await this.renderAllOrders(container);
    } else if (tab === "diagnostics") {
      await this.renderDiagnostics(container);
    }
  },

  async renderAnalytics(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <div>
          <h2>Platform Operations & Revenue Intelligence</h2>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Authoritative aggregated metrics calculated directly from database records.</p>
        </div>
        <button type="button" class="btn-demo-pill" id="btn-refresh-admin-stats">Refresh Analytics</button>
      </div>

      <div class="stats-grid" id="admin-stats-grid">
        <div class="stat-card"><div class="stat-label">Calculating metrics...</div></div>
      </div>

      <h3 style="margin: 28px 0 16px 0;">Recent Orders Across All Pharmacies</h3>
      <div id="admin-recent-orders-table">
        <div class="loading-screen"><div class="spinner"></div><p>Fetching platform orders...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-admin-stats").addEventListener("click", () => this.fetchAnalyticsData());

    Sync.register("admin_analytics", () => this.fetchAnalyticsData(), 6000);
    await this.fetchAnalyticsData();
  },

  async fetchAnalyticsData() {
    const statsGrid = document.getElementById("admin-stats-grid");
    const recentOrders = document.getElementById("admin-recent-orders-table");
    if (!statsGrid || !recentOrders) return;

    try {
      const res = await API.admin.getStats();
      const m = res.metrics;
      const orders = res.recent_orders || [];

      statsGrid.innerHTML = `
        <div class="stat-card stat-success">
          <div class="stat-label">Total Platform Revenue</div>
          <div class="stat-val">${Components.formatCurrency(m.total_revenue)}</div>
        </div>
        <div class="stat-card stat-accent">
          <div class="stat-label">Total Orders Placed</div>
          <div class="stat-val">${m.total_orders}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Registered Users</div>
          <div class="stat-val">${m.total_users}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Partner Pharmacies</div>
          <div class="stat-val">${m.total_pharmacies}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Catalogue Medicines</div>
          <div class="stat-val">${m.total_catalogue_medicines}</div>
        </div>
        <div class="stat-card stat-warning">
          <div class="stat-label">Global Low-Stock Items</div>
          <div class="stat-val">${m.low_stock_alerts}</div>
        </div>
      `;

      if (orders.length === 0) {
        recentOrders.innerHTML = `<div style="padding:40px; text-align:center; color:var(--text-muted); background:var(--bg-card); border-radius:var(--radius-md);">No orders found.</div>`;
        return;
      }

      recentOrders.innerHTML = `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Pharmacy</th>
                <th>Date</th>
                <th>Total</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${orders.map(o => `
                <tr>
                  <td><strong>${o.id}</strong></td>
                  <td>${Components.escapeHtml(o.customer_name)}</td>
                  <td>${Components.escapeHtml(o.pharmacy_name)}</td>
                  <td>${Components.formatDate(o.created_at)}</td>
                  <td><strong>${Components.formatCurrency(o.total_amount)}</strong></td>
                  <td>${Components.renderStatusBadge(o.order_status)}</td>
                  <td>${Components.renderPaymentBadge(o.payment_status)}</td>
                  <td>
                    <button type="button" class="btn-alt-pill btn-admin-inspect-order" data-id="${o.id}">
                      Audit Order
                    </button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;

      recentOrders.querySelectorAll(".btn-admin-inspect-order").forEach(b => {
        b.addEventListener("click", () => CustomerPortal.showOrderDetailsModal(b.dataset.id));
      });

    } catch (err) {
      statsGrid.innerHTML = `<div style="color:var(--rose);">Failed to calculate metrics: ${err.message}</div>`;
    }
  },

  async renderUsers(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <h2>User Identity & Access Governance</h2>
        <div style="display:flex; gap:10px;">
          <select id="admin-user-role-filter" class="select-styled">
            <option value="">All Roles</option>
            <option value="customer">Customer</option>
            <option value="pharmacy">Pharmacy</option>
            <option value="delivery">Delivery</option>
            <option value="admin">Administrator</option>
          </select>
          <button type="button" class="btn-demo-pill" id="btn-refresh-users">Refresh</button>
        </div>
      </div>
      <div id="admin-users-table-container">
        <div class="loading-screen"><div class="spinner"></div><p>Loading user directory...</p></div>
      </div>
    `;

    const roleSelect = document.getElementById("admin-user-role-filter");
    roleSelect.addEventListener("change", () => this.fetchUsers(roleSelect.value));
    document.getElementById("btn-refresh-users").addEventListener("click", () => this.fetchUsers(roleSelect.value));

    await this.fetchUsers();
  },

  async fetchUsers(role = "") {
    const container = document.getElementById("admin-users-table-container");
    if (!container) return;

    try {
      const res = await API.admin.getUsers({ role });
      const users = res.users || [];

      container.innerHTML = `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Full Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Role</th>
                <th>Auth Type</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              ${users.map(u => `
                <tr>
                  <td>${u.id}</td>
                  <td><strong>${Components.escapeHtml(u.full_name)}</strong></td>
                  <td>${Components.escapeHtml(u.email)}</td>
                  <td>${Components.escapeHtml(u.phone || 'N/A')}</td>
                  <td><span class="badge ${u.role === 'admin' ? 'badge-rx' : (u.role === 'pharmacy' ? 'badge-pulse' : (u.role === 'delivery' ? 'badge-otc' : 'badge-category'))}">${u.role.toUpperCase()}</span></td>
                  <td>${u.google_id ? 'Google OAuth 2.0' : 'Email/Password'}</td>
                  <td><span class="badge ${u.is_active ? 'badge-otc' : 'badge-rx'}">${u.is_active ? 'Active' : 'Suspended'}</span></td>
                  <td>
                    ${u.role !== 'admin' ? `
                      <button type="button" class="btn-alt-pill btn-toggle-user-status" data-id="${u.id}" data-active="${u.is_active}">
                        ${u.is_active ? 'Suspend' : 'Activate'}
                      </button>
                    ` : '<span style="color:var(--text-muted); font-size:0.75rem;">Protected</span>'}
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;

      container.querySelectorAll(".btn-toggle-user-status").forEach(b => {
        b.addEventListener("click", async () => {
          const userId = parseInt(b.dataset.id);
          const currentActive = b.dataset.active === "1";
          try {
            await API.admin.toggleUserStatus(userId, !currentActive);
            Components.toast(`User #${userId} status updated.`, "success");
            await this.fetchUsers(document.getElementById("admin-user-role-filter")?.value || "");
          } catch (err) {
            Components.toast(err.message, "error");
          }
        });
      });

    } catch (err) {
      container.innerHTML = `<div style="color:var(--rose);">Error loading users: ${err.message}</div>`;
    }
  },

  async renderPharmacies(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <h2>Pharmacy Network Onboarding & Approvals</h2>
        <button type="button" class="btn-demo-pill" id="btn-refresh-pharmacies">Refresh</button>
      </div>
      <div id="admin-pharmacies-table-container">
        <div class="loading-screen"><div class="spinner"></div><p>Loading pharmacy partners...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-pharmacies").addEventListener("click", () => this.fetchPharmacies());
    await this.fetchPharmacies();
  },

  async fetchPharmacies() {
    const container = document.getElementById("admin-pharmacies-table-container");
    if (!container) return;

    try {
      const res = await API.admin.getPharmacies();
      const pharms = res.pharmacies || [];

      container.innerHTML = `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Pharmacy Name</th>
                <th>License #</th>
                <th>City & Address</th>
                <th>Contact</th>
                <th>Rating</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${pharms.map(p => `
                <tr>
                  <td>${p.id}</td>
                  <td><strong>${Components.escapeHtml(p.name)}</strong></td>
                  <td><code>${Components.escapeHtml(p.license_number)}</code></td>
                  <td>${Components.escapeHtml(p.city)} (${Components.escapeHtml(p.address)})</td>
                  <td>${Components.escapeHtml(p.phone)}</td>
                  <td>${p.rating} / 5.0</td>
                  <td><span class="badge ${p.status === 'approved' ? 'badge-otc' : (p.status === 'suspended' ? 'badge-rx' : 'badge-pulse')}">${p.status.toUpperCase()}</span></td>
                  <td>
                    <div style="display:flex; gap:6px;">
                      ${p.status !== 'approved' ? `
                        <button type="button" class="btn-demo-pill btn-set-pharm-status" data-id="${p.id}" data-st="approved" style="color:var(--emerald); border-color:var(--emerald);">Approve</button>
                      ` : ''}
                      ${p.status !== 'suspended' ? `
                        <button type="button" class="btn-demo-pill btn-set-pharm-status" data-id="${p.id}" data-st="suspended" style="color:var(--amber); border-color:var(--amber);">Suspend</button>
                      ` : ''}
                    </div>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;

      container.querySelectorAll(".btn-set-pharm-status").forEach(b => {
        b.addEventListener("click", async () => {
          try {
            await API.admin.updatePharmacyStatus(parseInt(b.dataset.id), b.dataset.st);
            Components.toast(`Pharmacy #${b.dataset.id} status updated to ${b.dataset.st}.`, "success");
            await this.fetchPharmacies();
          } catch (err) {
            Components.toast(err.message, "error");
          }
        });
      });

    } catch (err) {
      container.innerHTML = `<div style="color:var(--rose);">Error loading pharmacies: ${err.message}</div>`;
    }
  },

  async renderAllOrders(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <h2>Global Order Monitor & Cross-Portal Audit</h2>
        <button type="button" class="btn-demo-pill" id="btn-refresh-all-orders">Refresh</button>
      </div>
      <div id="admin-all-orders-container">
        <div class="loading-screen"><div class="spinner"></div><p>Fetching platform orders...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-all-orders").addEventListener("click", () => this.fetchAllOrders());
    await this.fetchAllOrders();
  },

  async fetchAllOrders() {
    const container = document.getElementById("admin-all-orders-container");
    if (!container) return;

    try {
      const res = await API.orders.list();
      const orders = res.orders || [];

      container.innerHTML = `
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Pharmacy</th>
                <th>Assigned Rider</th>
                <th>Order Total</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Audit</th>
              </tr>
            </thead>
            <tbody>
              ${orders.map(o => `
                <tr>
                  <td><strong>${o.id}</strong></td>
                  <td>${Components.escapeHtml(o.customer_name)}</td>
                  <td>${Components.escapeHtml(o.pharmacy_name)}</td>
                  <td>${o.delivery_name ? Components.escapeHtml(o.delivery_name) : '<span style="color:var(--text-muted);">Unassigned</span>'}</td>
                  <td><strong>${Components.formatCurrency(o.total_amount)}</strong></td>
                  <td>${Components.renderStatusBadge(o.order_status)}</td>
                  <td>${Components.renderPaymentBadge(o.payment_status)}</td>
                  <td>
                    <button type="button" class="btn-alt-pill btn-inspect-global-order" data-id="${o.id}">
                      Audit Details
                    </button>
                  </td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;

      container.querySelectorAll(".btn-inspect-global-order").forEach(b => {
        b.addEventListener("click", () => CustomerPortal.showOrderDetailsModal(b.dataset.id));
      });

    } catch (err) {
      container.innerHTML = `<div style="color:var(--rose);">Error: ${err.message}</div>`;
    }
  },

  async renderDiagnostics(container) {
    container.innerHTML = `<div class="loading-screen"><div class="spinner"></div><p>Running platform diagnostics...</p></div>`;

    try {
      const res = await API.admin.getSystemHealth();
      const caps = res.capabilities || {};
      const validation = res.config_validation || {};

      container.innerHTML = `
        <h2>System Health, Configuration & External Integration Readiness</h2>
        <p style="color:var(--text-secondary); font-size:0.9rem; margin-bottom:24px;">Verified operational diagnostic matrix. Real secrets are never disclosed.</p>

        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:20px; margin-bottom:28px;">
          <div class="stat-card ${(res.database_ready || res.database_connected) ? 'stat-success' : 'stat-warning'}">
            <div class="stat-label">SQLite Relational Database</div>
            <div class="stat-val" style="font-size:1.4rem;">${(res.database_ready || res.database_connected) ? 'Connected & Enforcing FKs' : 'Disconnected'}</div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Journal Mode: WAL • Foreign Keys: ON</div>
          </div>

          <div class="stat-card stat-accent">
            <div class="stat-label">Application Mode</div>
            <div class="stat-val" style="font-size:1.4rem;">${res.app_mode.toUpperCase()}</div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">Environment: ${res.app_env}</div>
          </div>

          <div class="stat-card ${validation.is_valid ? 'stat-success' : 'stat-warning'}">
            <div class="stat-label">Configuration Validation</div>
            <div class="stat-val" style="font-size:1.4rem;">${validation.is_valid ? 'Valid' : 'Warnings Found'}</div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">${validation.issues.length} operational issues flagged</div>
          </div>
        </div>

        <h3 style="margin-bottom:16px;">External Service Readiness Matrix:</h3>
        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Service Provider</th>
                <th>Target Feature</th>
                <th>Configuration State</th>
                <th>Active Fallback / Behavior</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Google OAuth 2.0</strong></td>
                <td>Single Sign-On Authentication</td>
                <td><span class="badge ${caps.google_oauth_configured ? 'badge-otc' : 'badge-pulse'}">${caps.google_oauth_configured ? 'Configured' : 'Missing Credentials'}</span></td>
                <td>Demo 1-Click Role Switcher active for testing</td>
              </tr>
              <tr>
                <td><strong>Razorpay Payments</strong></td>
                <td>Credit Card, UPI, Netbanking</td>
                <td><span class="badge ${caps.razorpay_configured ? 'badge-otc' : 'badge-pulse'}">${caps.razorpay_configured ? 'Configured' : 'Missing Credentials'}</span></td>
                <td>Simulated Gateway with instant verified order state updates</td>
              </tr>
              <tr>
                <td><strong>Google Gemini AI</strong></td>
                <td>Ailment Assistant & Triage</td>
                <td><span class="badge ${caps.gemini_configured ? 'badge-otc' : 'badge-pulse'}">${caps.gemini_configured ? 'Configured' : 'Missing API Key'}</span></td>
                <td>Deterministic clinical knowledge base with emergency red-flag screening</td>
              </tr>
              <tr>
                <td><strong>OCR Engine</strong></td>
                <td>Prescription Text Extraction</td>
                <td><span class="badge ${caps.tesseract_configured ? 'badge-otc' : 'badge-pulse'}">${caps.tesseract_configured ? 'Tesseract Available' : 'PyPDF & Heuristic Active'}</span></td>
                <td>Native Python PyPDF and Medical Pattern Recognition Engine</td>
              </tr>
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div style="color:var(--rose);">Diagnostics error: ${err.message}</div>`;
    }
  }
};
