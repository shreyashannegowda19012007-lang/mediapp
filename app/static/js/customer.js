/**
 * MediApp Customer Portal.
 * Manages catalogue search with non-jumping input focus, generic recommendations,
 * cart operations, itemized checkout, order tracking, and prescription management.
 */

const CustomerPortal = {
  _debounceTimer: null,

  async init(tab = "catalogue") {
    Sync.stopAll();
    const container = document.getElementById("main-content");
    
    if (tab === "catalogue") {
      await this.renderCatalogue(container);
    } else if (tab === "orders") {
      await this.renderOrders(container);
    } else if (tab === "prescriptions") {
      await this.renderPrescriptions(container);
    }
  },

  async renderCatalogue(container) {
    const selectedPharmId = State.get("selectedPharmacyId") || 1;
    const currentQuery = State.get("searchQuery") || "";
    const currentCat = State.get("selectedCategory") || "";

    container.innerHTML = `
      <section class="customer-hero">
        <span class="hero-tag">Clinical Delivery Network</span>
        <h1 class="hero-title">Trusted Medications Delivered Directly from Licensed Pharmacies</h1>
        <p class="hero-subtitle">Browse over 1,200+ verified prescription and OTC medications with guaranteed authenticity, drug-drug interaction safety checks, and generic savings.</p>
        
        <div class="search-bar-wrapper">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
          <input type="text" id="catalogue-search-input" class="input-main-search"
                 placeholder="Search medicine name, active generic ingredient, or symptoms..."
                 value="${currentQuery}" autocomplete="off">
        </div>

        <div class="filter-pills-bar" id="category-pills-container">
          <button type="button" class="pill-filter ${!currentCat ? 'active' : ''}" data-cat="">All Categories</button>
        </div>
      </section>

      <div class="controls-bar">
        <div class="selector-group">
          <label class="selector-label" for="pharmacy-select">Fulfilling Pharmacy:</label>
          <select id="pharmacy-select" class="select-styled">
            <option value="1">Apollo Pharmacy - Indiranagar</option>
            <option value="2">MedPlus Pharmacy - Koramangala</option>
            <option value="3">Fortis Health Care Chemist</option>
          </select>
        </div>
        <div class="selector-group">
          <label class="selector-label" for="rx-filter-select">Type:</label>
          <select id="rx-filter-select" class="select-styled">
            <option value="">All Medicines</option>
            <option value="0">Over-the-Counter (OTC)</option>
            <option value="1">Prescription Required (Rx)</option>
          </select>
        </div>
      </div>

      <div id="medicine-grid" class="medicine-grid">
        <div class="loading-screen"><div class="spinner"></div><p>Loading medicines...</p></div>
      </div>
    `;

    // Populate category pills
    try {
      const catRes = await API.medicines.getCategories();
      const pillsContainer = document.getElementById("category-pills-container");
      if (pillsContainer && catRes.categories) {
        catRes.categories.slice(0, 10).forEach(c => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = `pill-filter ${currentCat === c.category ? 'active' : ''}`;
          btn.textContent = `${c.category} (${c.count})`;
          btn.dataset.cat = c.category;
          btn.addEventListener("click", () => {
            document.querySelectorAll(".pill-filter").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            State.set("selectedCategory", c.category);
            this.fetchAndRenderMedicines();
          });
          pillsContainer.appendChild(btn);
        });
      }
    } catch (e) {
      console.warn("Could not load categories:", e);
    }

    // Attach search input listener with DEBOUNCE to PRESERVE FOCUS!
    const searchInput = document.getElementById("catalogue-search-input");
    searchInput.addEventListener("input", (e) => {
      clearTimeout(this._debounceTimer);
      const val = e.target.value;
      State.set("searchQuery", val);
      this._debounceTimer = setTimeout(() => {
        this.fetchAndRenderMedicines();
      }, 250);
    });

    const pharmSelect = document.getElementById("pharmacy-select");
    pharmSelect.value = selectedPharmId;
    pharmSelect.addEventListener("change", (e) => {
      State.set("selectedPharmacyId", parseInt(e.target.value));
      this.fetchAndRenderMedicines();
    });

    const rxSelect = document.getElementById("rx-filter-select");
    rxSelect.addEventListener("change", (e) => {
      State.set("rxFilter", e.target.value);
      this.fetchAndRenderMedicines();
    });

    // Initial fetch of medicines
    await this.fetchAndRenderMedicines();
  },

  async fetchAndRenderMedicines() {
    const grid = document.getElementById("medicine-grid");
    if (!grid) return;

    const params = {
      q: State.get("searchQuery") || "",
      category: State.get("selectedCategory") || "",
      rx: State.get("rxFilter") || "",
      pharmacy_id: State.get("selectedPharmacyId") || 1,
      limit: 24
    };

    try {
      const res = await API.medicines.search(params);
      const medicines = res.medicines || [];

      if (medicines.length === 0) {
        grid.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px;">
            <p style="font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 8px;">No medications found matching your search.</p>
            <p style="font-size: 0.875rem; color: var(--text-muted);">Try clearing active filters or searching for common active ingredients like Paracetamol, Amlodipine, or Pantoprazole.</p>
          </div>
        `;
        return;
      }

      grid.innerHTML = medicines.map(med => {
        const isRx = Boolean(med.prescription_required);
        const inStock = med.stock_quantity > 0 && med.is_available;
        const stockClass = !inStock ? "out" : (med.stock_quantity <= 10 ? "low" : "");
        const stockText = !inStock ? "Out of Stock" : (med.stock_quantity <= 10 ? `Low Stock (${med.stock_quantity} left)` : `In Stock (${med.stock_quantity} units)`);

        return `
          <article class="medicine-card" data-id="${med.id}">
            <div class="card-top">
              <div class="card-badges">
                ${isRx ? '<span class="badge-rx">Rx Required</span>' : '<span class="badge-otc">OTC</span>'}
                <span class="badge-category">${med.dosage_form}</span>
                <span class="badge-category">${med.category}</span>
              </div>
              <h3 class="med-name">${med.name}</h3>
              <p class="med-generic">🧪 ${med.generic_name} • ${med.strength}</p>
              <p class="med-mfr">Mfr: ${med.manufacturer}</p>
              ${med.uses ? `<p class="med-uses">${med.uses}</p>` : ''}
            </div>

            <div class="card-bottom">
              <div class="price-box">
                <span class="price-val">${Components.formatCurrency(med.unit_price)}</span>
                <span class="stock-val ${stockClass}">● ${stockText}</span>
              </div>
              <div class="card-actions">
                <button type="button" class="btn-alt-pill btn-view-alt" data-id="${med.id}" title="Find cheaper bioequivalent generic alternatives">
                  Generics
                </button>
                <button type="button" class="btn-add-cart btn-cart-action" data-id="${med.id}" ${!inStock ? 'disabled' : ''}>
                  + Add
                </button>
              </div>
            </div>
          </article>
        `;
      }).join("");

      // Bind action handlers
      grid.querySelectorAll(".btn-view-alt").forEach(btn => {
        btn.addEventListener("click", () => this.showGenericAlternatives(parseInt(btn.dataset.id)));
      });

      grid.querySelectorAll(".btn-cart-action").forEach(btn => {
        btn.addEventListener("click", () => this.handleAddToCart(parseInt(btn.dataset.id)));
      });

    } catch (err) {
      grid.innerHTML = `<div style="grid-column: 1/-1; padding: 40px; color: var(--rose);">Failed to load medicines: ${err.message}</div>`;
    }
  },

  async handleAddToCart(medicineId) {
    const user = State.get("user");
    if (!user) {
      Components.toast("Please sign in or select a demo role from the top banner to add items to your cart.", "warning");
      return;
    }

    try {
      const pharmId = State.get("selectedPharmacyId") || 1;
      await API.cart.addItem(medicineId, 1, pharmId);
      Components.toast("Item added to cart!", "success");
      await this.refreshCart();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async refreshCart() {
    const user = State.get("user");
    if (!user) {
      State.set("cart", { items: [], item_count: 0 });
      const badge = document.getElementById("cart-badge-count");
      if (badge) badge.textContent = "0";
      return;
    }

    try {
      const res = await API.cart.get();
      State.set("cart", res);
      
      const badge = document.getElementById("cart-badge-count");
      if (badge) {
        badge.textContent = res.item_count || 0;
      }
      this.renderCartDrawerContent(res);
    } catch {
      // User session may have expired
    }
  },

  renderCartDrawerContent(cartData) {
    const container = document.getElementById("cart-items-container");
    const footer = document.getElementById("cart-footer-container");
    const ddiAlert = document.getElementById("cart-ddi-alert");
    if (!container || !footer) return;

    const items = cartData.items || [];
    const interactions = cartData.drug_interactions?.interactions || [];

    // Render DDI warnings if any exist
    if (interactions.length > 0) {
      ddiAlert.classList.remove("hidden");
      ddiAlert.innerHTML = `
        <div class="ddi-alert-header">⚠️ Clinical Drug Interaction Detected (${interactions.length})</div>
        ${interactions.map(intx => `
          <div style="margin-top: 6px;">
            <strong>[${intx.severity}]</strong> ${intx.medicine_a} + ${intx.medicine_b}: ${intx.title}
            <div style="font-size: 0.75rem; color: #fecdd3; margin-top: 2px;">${intx.management}</div>
          </div>
        `).join("")}
      `;
    } else {
      ddiAlert.classList.add("hidden");
    }

    if (items.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 40px 10px; color: var(--text-muted);">
          <p style="font-size: 1.1rem; margin-bottom: 6px;">Your cart is empty.</p>
          <p style="font-size: 0.85rem;">Browse medications in the catalogue and add items to begin checkout.</p>
        </div>
      `;
      footer.innerHTML = "";
      return;
    }

    container.innerHTML = items.map(it => `
      <div class="cart-item-row" data-id="${it.medicine_id}">
        <div class="cart-item-info">
          <div class="cart-item-name">${it.name}</div>
          <div class="cart-item-price">${Components.formatCurrency(it.unit_price)} × ${it.quantity} = ${Components.formatCurrency(it.line_total)}</div>
          ${it.prescription_required ? '<span class="badge-rx" style="display:inline-block; margin-top:4px;">Rx Required</span>' : ''}
          ${it.stock_warning ? `<div style="color:var(--rose); font-size:0.75rem; margin-top:2px;">${it.stock_warning}</div>` : ''}
        </div>
        <div class="cart-qty-ctrls">
          <button type="button" class="btn-qty btn-qty-minus" data-id="${it.medicine_id}" data-qty="${it.quantity - 1}">-</button>
          <span class="qty-num">${it.quantity}</span>
          <button type="button" class="btn-qty btn-qty-plus" data-id="${it.medicine_id}" data-qty="${it.quantity + 1}">+</button>
          <button type="button" class="btn-qty btn-remove-item" data-id="${it.medicine_id}" title="Remove" style="color:var(--rose); margin-left:4px;">&times;</button>
        </div>
      </div>
    `).join("");

    const totals = cartData.totals || { subtotal: 0, tax: 0, delivery_fee: 0, discount: 0, total: 0 };
    footer.innerHTML = `
      <div class="totals-row"><span>Items Subtotal:</span> <span>${Components.formatCurrency(totals.subtotal)}</span></div>
      <div class="totals-row"><span>Estimated GST (5%):</span> <span>${Components.formatCurrency(totals.tax)}</span></div>
      <div class="totals-row"><span>Delivery Fee:</span> <span>${totals.delivery_fee === 0 ? '<span style="color:var(--emerald);">FREE</span>' : Components.formatCurrency(totals.delivery_fee)}</span></div>
      ${totals.discount > 0 ? `<div class="totals-row" style="color:var(--emerald);"><span>Promotional Discount:</span> <span>-${Components.formatCurrency(totals.discount)}</span></div>` : ''}
      <div class="totals-row grand-total"><span>Total Authoritative Amount:</span> <span>${Components.formatCurrency(totals.total)}</span></div>
      <button type="button" class="btn-checkout-primary" id="btn-proceed-checkout" ${cartData.has_out_of_stock ? 'disabled' : ''}>
        Proceed to Checkout
      </button>
    `;

    // Bind item quantity change handlers
    container.querySelectorAll(".btn-qty-minus").forEach(b => {
      b.addEventListener("click", () => this.updateCartItem(parseInt(b.dataset.id), parseInt(b.dataset.qty)));
    });
    container.querySelectorAll(".btn-qty-plus").forEach(b => {
      b.addEventListener("click", () => this.updateCartItem(parseInt(b.dataset.id), parseInt(b.dataset.qty)));
    });
    container.querySelectorAll(".btn-remove-item").forEach(b => {
      b.addEventListener("click", () => this.updateCartItem(parseInt(b.dataset.id), 0));
    });

    const proceedBtn = document.getElementById("btn-proceed-checkout");
    if (proceedBtn) {
      proceedBtn.addEventListener("click", () => this.openCheckoutModal());
    }
  },

  async updateCartItem(medicineId, newQty) {
    try {
      await API.cart.updateItem(medicineId, newQty);
      await this.refreshCart();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async showGenericAlternatives(medicineId) {
    try {
      const res = await API.medicines.getGenericAlternatives(medicineId);
      const target = res.target_medicine;
      const alts = res.alternatives || [];
      const content = document.getElementById("generic-modal-content");

      content.innerHTML = `
        <div style="margin-bottom: 20px; padding: 14px; background: rgba(255,255,255,0.04); border-radius: var(--radius-sm);">
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Reference Branded Medicine</div>
          <div style="font-size: 1.15rem; font-weight:700; color:#fff;">${target.name}</div>
          <div style="color:var(--cyan); font-size:0.875rem;">Active Molecule: ${target.generic_name} • ${target.strength} (${target.dosage_form})</div>
          <div style="font-size: 1.1rem; font-weight:800; margin-top:4px;">MRP: ${Components.formatCurrency(target.mrp)}</div>
        </div>

        <h4 style="margin-bottom: 12px; font-size: 1rem;">Bioequivalent Lower-Cost Alternatives:</h4>
        ${alts.length === 0 ? '<p style="color:var(--text-muted);">No cheaper generic alternatives found for this molecule and strength combination.</p>' : `
          <div style="display:flex; flex-direction:column; gap:12px;">
            ${alts.map(a => `
              <div style="background:var(--bg-canvas); border:1px solid var(--border-subtle); border-radius:var(--radius-sm); padding:14px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                  <div style="font-weight:700; color:#fff;">${a.name}</div>
                  <div style="font-size:0.8rem; color:var(--text-muted);">Mfr: ${a.manufacturer}</div>
                  <div style="font-size:0.8rem; color:var(--emerald); font-weight:600; margin-top:2px;">
                    Save ${a.savings_pct}% (${Components.formatCurrency(a.savings_amount)} per pack)
                  </div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:1.15rem; font-weight:800; color:#fff; margin-bottom:6px;">${Components.formatCurrency(a.price)}</div>
                  <button type="button" class="btn-add-cart btn-choose-generic" data-id="${a.id}" style="padding:6px 12px; font-size:0.8rem;">
                    Switch to Generic
                  </button>
                </div>
              </div>
            `).join("")}
          </div>
        `}
      `;

      content.querySelectorAll(".btn-choose-generic").forEach(b => {
        b.addEventListener("click", async () => {
          await this.handleAddToCart(parseInt(b.dataset.id));
          Components.closeModal("generic-modal");
        });
      });

      Components.openModal("generic-modal");
    } catch (err) {
      Components.toast("Failed to load alternatives: " + err.message, "error");
    }
  },

  async openCheckoutModal() {
    const user = State.get("user");
    if (!user) {
      Components.toast("Please log in to checkout.", "warning");
      return;
    }

    const cart = State.get("cart");
    if (!cart || !cart.items || cart.items.length === 0) {
      Components.toast("Cart is empty.", "error");
      return;
    }

    const modalContent = document.getElementById("checkout-modal-content");
    const hasRx = cart.has_rx_required;

    // Fetch user saved prescriptions if Rx required
    let userPrescriptions = [];
    if (hasRx) {
      try {
        const rxRes = await API.prescriptions.list();
        userPrescriptions = rxRes.prescriptions || [];
      } catch {}
    }

    modalContent.innerHTML = `
      <form id="checkout-form">
        <h4 style="margin-bottom: 12px;">1. Delivery Destination Address</h4>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="form-group" style="grid-column: 1/-1;">
            <label class="form-label">Address Line 1 *</label>
            <input type="text" id="chk-addr1" class="form-control" required value="Flat 402, Green Glen Layout">
          </div>
          <div class="form-group" style="grid-column: 1/-1;">
            <label class="form-label">Address Line 2 (Area, Landmark)</label>
            <input type="text" id="chk-addr2" class="form-control" value="Outer Ring Road, Bellandur">
          </div>
          <div class="form-group">
            <label class="form-label">City *</label>
            <input type="text" id="chk-city" class="form-control" required value="Bengaluru">
          </div>
          <div class="form-group">
            <label class="form-label">State *</label>
            <input type="text" id="chk-state" class="form-control" required value="Karnataka">
          </div>
          <div class="form-group">
            <label class="form-label">Pincode *</label>
            <input type="text" id="chk-pin" class="form-control" required value="560103">
          </div>
          <div class="form-group">
            <label class="form-label">Recipient Contact Phone *</label>
            <input type="text" id="chk-phone" class="form-control" required value="${user.phone || '+91 9876543210'}">
          </div>
        </div>

        ${hasRx ? `
          <div style="margin: 20px 0; padding: 14px; background: rgba(244, 63, 94, 0.1); border: 1px solid var(--rose); border-radius: var(--radius-sm);">
            <h4 style="color: #fb7185; margin-bottom: 6px;">2. Prescription Attachment Required (Rx)</h4>
            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 10px;">Your cart contains prescription medications. Attach a verified doctor's prescription to proceed.</p>
            ${userPrescriptions.length > 0 ? `
              <select id="chk-prescription-select" class="select-styled" style="width:100%;">
                ${userPrescriptions.map(p => `
                  <option value="${p.id}">Prescription #${p.id} (${p.original_filename}) - Status: ${p.status}</option>
                `).join("")}
              </select>
            ` : `
              <p style="color:var(--amber); font-size:0.85rem;">No uploaded prescriptions found. Upload one now via the Prescription tab.</p>
            `}
          </div>
        ` : ''}

        <h4 style="margin: 20px 0 12px 0;">3. Payment Gateway</h4>
        <div style="display:flex; flex-direction:column; gap:10px; margin-bottom: 20px;">
          <label style="display:flex; align-items:center; gap:10px; background:rgba(255,255,255,0.05); padding:12px; border-radius:var(--radius-sm); cursor:pointer;">
            <input type="radio" name="payment_method" value="demo" checked>
            <div>
              <div style="font-weight:700;">Simulated Demo Gateway (Instant Verification)</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">Safe local simulation. Exercises full backend order, payment, and inventory flow without charging real currency.</div>
            </div>
          </label>
          <label style="display:flex; align-items:center; gap:10px; background:rgba(255,255,255,0.05); padding:12px; border-radius:var(--radius-sm); cursor:pointer;">
            <input type="radio" name="payment_method" value="razorpay">
            <div>
              <div style="font-weight:700;">Razorpay Secure Gateway</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">Real/Test Razorpay checkout with HMAC-SHA256 signature verification.</div>
            </div>
          </label>
        </div>

        <div style="background:var(--bg-canvas); padding:16px; border-radius:var(--radius-sm); margin-bottom: 20px;">
          <div class="totals-row"><span>Items:</span> <span>${cart.item_count} items</span></div>
          <div class="totals-row"><span>Subtotal:</span> <span>${Components.formatCurrency(cart.totals.subtotal)}</span></div>
          <div class="totals-row"><span>Tax (5%):</span> <span>${Components.formatCurrency(cart.totals.tax)}</span></div>
          <div class="totals-row"><span>Delivery Fee:</span> <span>${Components.formatCurrency(cart.totals.delivery_fee)}</span></div>
          <div class="totals-row grand-total"><span>Authoritative Grand Total:</span> <span>${Components.formatCurrency(cart.totals.total)}</span></div>
        </div>

        <button type="submit" class="btn-checkout-primary" id="btn-submit-order">
          Confirm Order & Complete Payment (${Components.formatCurrency(cart.totals.total)})
        </button>
      </form>
    `;

    document.getElementById("checkout-form").addEventListener("submit", (e) => this.handleOrderSubmit(e));
    Components.openModal("checkout-modal");
  },

  async handleOrderSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-submit-order");
    btn.disabled = true;
    btn.textContent = "Processing Authoritative Order & Payment...";

    const deliveryAddress = {
      line1: document.getElementById("chk-addr1").value.trim(),
      line2: document.getElementById("chk-addr2").value.trim(),
      city: document.getElementById("chk-city").value.trim(),
      state: document.getElementById("chk-state").value.trim(),
      pincode: document.getElementById("chk-pin").value.trim(),
      recipient_phone: document.getElementById("chk-phone").value.trim()
    };

    const rxSelect = document.getElementById("chk-prescription-select");
    const prescriptionId = rxSelect ? parseInt(rxSelect.value) : null;
    const paymentMethod = document.querySelector('input[name="payment_method"]:checked')?.value || "demo";

    try {
      // 1. Create order on backend
      const orderRes = await API.orders.create({
        delivery_address: deliveryAddress,
        prescription_id: prescriptionId
      });
      const order = orderRes.order;

      // 2. Process payment
      if (paymentMethod === "demo") {
        await API.payments.verify(order.id, { status: "success" });
        Components.toast("Order placed and payment confirmed in Demo Mode!", "success");
      } else {
        // Real Razorpay Initiation
        const payInit = await API.payments.createOrder(order.id);
        Components.toast("Razorpay payment initiated: " + payInit.payment_order.provider_order_id, "info");
        // Simulated completion for testing credentials
        await API.payments.verify(order.id, {
          razorpay_order_id: payInit.payment_order.provider_order_id,
          razorpay_payment_id: "pay_test_" + Date.now(),
          razorpay_signature: "mock_test_sig"
        });
      }

      // Close modal, refresh cart and view orders
      Components.closeModal("checkout-modal");
      Components.closeModal("cart-drawer-overlay");
      await this.refreshCart();
      await this.init("orders");
      State.set("activeTab", "orders");

    } catch (err) {
      Components.toast("Order Placement Error: " + err.message, "error");
      btn.disabled = false;
      btn.textContent = "Confirm Order & Complete Payment";
    }
  },

  async renderOrders(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <h2>Your Orders & Real-time Delivery Tracking</h2>
        <button type="button" class="btn-demo-pill" id="btn-refresh-orders">↻ Refresh</button>
      </div>
      <div id="customer-orders-list">
        <div class="loading-screen"><div class="spinner"></div><p>Fetching your orders...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-orders").addEventListener("click", () => this.fetchCustomerOrders());
    
    // Register visibility-aware auto-polling for active orders
    Sync.register("customer_orders", () => this.fetchCustomerOrders(), 5000);
  },

  async fetchCustomerOrders() {
    const listEl = document.getElementById("customer-orders-list");
    if (!listEl) return;

    try {
      const res = await API.orders.list();
      const orders = res.orders || [];

      if (orders.length === 0) {
        listEl.innerHTML = `
          <div style="text-align:center; padding: 60px 20px; background:var(--bg-card); border-radius:var(--radius-md);">
            <p style="font-size:1.1rem; color:var(--text-secondary); margin-bottom:8px;">You haven't placed any orders yet.</p>
            <p style="font-size:0.85rem; color:var(--text-muted);">Explore our medicine catalogue to make your first purchase.</p>
          </div>
        `;
        return;
      }

      listEl.innerHTML = orders.map(ord => `
        <div class="order-tracking-card" data-order-id="${ord.id}">
          <div class="tracking-header">
            <div>
              <div style="font-size:0.75rem; color:var(--text-muted);">Order Reference</div>
              <div style="font-size: 1.25rem; font-weight:800; color:#fff;">${ord.id}</div>
              <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:2px;">
                Pharmacy: <strong>${ord.pharmacy_name}</strong> • ${Components.formatDate(ord.created_at)}
              </div>
            </div>
            <div style="text-align:right;">
              <div style="font-size: 1.3rem; font-weight:800; color:#fff;">${Components.formatCurrency(ord.total_amount)}</div>
              <div style="display:flex; gap:6px; justify-content:flex-end; margin-top:4px;">
                ${Components.renderPaymentBadge(ord.payment_status)}
                ${Components.renderStatusBadge(ord.order_status)}
              </div>
            </div>
          </div>

          ${this.renderStepperHtml(ord.order_status)}

          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px; padding-top:14px; border-top:1px solid var(--border-subtle);">
            <div style="font-size:0.85rem; color:var(--text-muted);">
              ${ord.cancellation_reason ? `<span style="color:var(--rose);">Reason: ${ord.cancellation_reason}</span>` : 'One authoritative backend order shared across all portals'}
            </div>
            <div style="display:flex; gap:8px;">
              ${["PLACED", "AWAITING_PRESCRIPTION", "ACCEPTED"].includes(ord.order_status) ? `
                <button type="button" class="btn-demo-pill btn-cancel-order" data-id="${ord.id}" style="color:var(--rose); border-color:var(--rose);">
                  Cancel Order
                </button>
              ` : ''}
              <button type="button" class="btn-alt-pill btn-view-order-details" data-id="${ord.id}">
                View Details & Invoice
              </button>
            </div>
          </div>
        </div>
      `).join("");

      listEl.querySelectorAll(".btn-view-order-details").forEach(b => {
        b.addEventListener("click", () => this.showOrderDetailsModal(b.dataset.id));
      });

      listEl.querySelectorAll(".btn-cancel-order").forEach(b => {
        b.addEventListener("click", () => this.handleCancelOrder(b.dataset.id));
      });

    } catch (err) {
      listEl.innerHTML = `<div style="color:var(--rose);">Failed to refresh orders: ${err.message}</div>`;
    }
  },

  renderStepperHtml(status) {
    const steps = [
      { key: "PLACED", label: "Placed" },
      { key: "ACCEPTED", label: "Accepted" },
      { key: "PREPARING", label: "Preparing" },
      { key: "READY_FOR_PICKUP", label: "Ready" },
      { key: "IN_TRANSIT", label: "In Transit" },
      { key: "DELIVERED", label: "Delivered" }
    ];

    if (status === "CANCELLED") {
      return `<div style="padding:10px; background:var(--rose-bg); color:#fda4af; border-radius:var(--radius-sm); text-align:center; font-weight:600;">This order has been cancelled and refunded. Inventory was safely restored.</div>`;
    }

    const statusOrder = ["PLACED", "ACCEPTED", "PREPARING", "READY_FOR_PICKUP", "DELIVERY_ASSIGNED", "PICKED_UP", "IN_TRANSIT", "DELIVERED"];
    const currentIdx = statusOrder.indexOf(status);

    return `
      <div class="order-stepper">
        ${steps.map((st, idx) => {
          const stepOrderIdx = statusOrder.indexOf(st.key);
          const isCompleted = currentIdx > stepOrderIdx;
          const isActive = currentIdx === stepOrderIdx || (st.key === "IN_TRANSIT" && ["DELIVERY_ASSIGNED", "PICKED_UP"].includes(status));
          const nodeCls = isCompleted ? "completed" : (isActive ? "active" : "");
          return `
            <div class="step-node ${nodeCls}">
              <div class="step-circle">${isCompleted ? '✓' : idx + 1}</div>
              <span class="step-label">${st.label}</span>
            </div>
          `;
        }).join("")}
      </div>
    `;
  },

  async showOrderDetailsModal(orderId) {
    try {
      const res = await API.orders.get(orderId);
      const ord = res.order;
      const modalContent = document.getElementById("order-detail-content");

      modalContent.innerHTML = `
        <div style="display:flex; justify-content:space-between; margin-bottom: 20px;">
          <div>
            <div style="font-size:0.8rem; color:var(--text-muted);">Authoritative ID</div>
            <div style="font-size:1.3rem; font-weight:800; color:#fff;">${ord.id}</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">${Components.formatDate(ord.created_at)}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:1.4rem; font-weight:800; color:#fff;">${Components.formatCurrency(ord.total_amount)}</div>
            <div>${Components.renderStatusBadge(ord.order_status)}</div>
          </div>
        </div>

        <h4 style="margin: 16px 0 8px 0;">Itemized Medicine Snapshots:</h4>
        <div class="table-responsive" style="margin-bottom: 20px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Medicine Snapshot</th>
                <th>Active Generic</th>
                <th>Unit Price</th>
                <th>Qty</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              ${ord.items.map(it => `
                <tr>
                  <td><strong>${it.medicine_name_snapshot}</strong></td>
                  <td>${it.generic_name_snapshot} (${it.strength_snapshot})</td>
                  <td>${Components.formatCurrency(it.unit_price)}</td>
                  <td>${it.quantity}</td>
                  <td><strong>${Components.formatCurrency(it.total_price)}</strong></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-bottom:20px;">
          <div style="background:rgba(255,255,255,0.03); padding:14px; border-radius:var(--radius-sm);">
            <div style="font-weight:700; margin-bottom:4px;">Delivery Destination</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">
              ${ord.delivery_address.line1}<br>
              ${ord.delivery_address.line2 || ''}<br>
              ${ord.delivery_address.city}, ${ord.delivery_address.state} - ${ord.delivery_address.pincode}<br>
              Phone: ${ord.delivery_address.recipient_phone || 'N/A'}
            </div>
          </div>
          <div style="background:rgba(255,255,255,0.03); padding:14px; border-radius:var(--radius-sm);">
            <div style="font-weight:700; margin-bottom:4px;">Fulfilling Pharmacy</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">
              ${ord.pharmacy_name}<br>
              ${ord.pharmacy_address}<br>
              Phone: ${ord.pharmacy_phone}
            </div>
          </div>
        </div>

        <h4 style="margin: 16px 0 8px 0;">State Transition Timeline Audit:</h4>
        <div style="display:flex; flex-direction:column; gap:8px;">
          ${ord.timeline.map(t => `
            <div style="font-size:0.8rem; background:rgba(255,255,255,0.02); padding:8px 12px; border-radius:4px; display:flex; justify-content:space-between;">
              <span><strong>${t.to_status}</strong>: ${t.notes || 'Status changed'} (${t.role})</span>
              <span style="color:var(--text-muted);">${Components.formatDate(t.created_at)}</span>
            </div>
          `).join("")}
        </div>
      `;

      Components.openModal("order-detail-modal");
    } catch (err) {
      Components.toast("Failed to load order: " + err.message, "error");
    }
  },

  async handleCancelOrder(orderId) {
    if (!confirm(`Are you sure you want to cancel order ${orderId}? This will automatically restore pharmacy inventory.`)) {
      return;
    }
    try {
      await API.orders.cancel(orderId, "Customer initiated cancellation");
      Components.toast("Order cancelled and inventory restored.", "info");
      await this.fetchCustomerOrders();
    } catch (err) {
      Components.toast(err.message, "error");
    }
  },

  async renderPrescriptions(container) {
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px;">
        <div>
          <h2>Prescription Upload & Genuine OCR Verification</h2>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Upload doctor prescriptions (PDF or Image) to extract medication names and doctor credentials.</p>
        </div>
        <button type="button" class="btn-checkout-primary" id="btn-open-rx-upload" style="margin:0; width:auto; padding:10px 20px;">
          + Upload New Prescription
        </button>
      </div>

      <div id="prescriptions-list-container">
        <div class="loading-screen"><div class="spinner"></div><p>Loading your prescriptions...</p></div>
      </div>
    `;

    document.getElementById("btn-open-rx-upload").addEventListener("click", () => this.openPrescriptionUploadModal());
    await this.fetchPrescriptions();
  },

  async fetchPrescriptions() {
    const listEl = document.getElementById("prescriptions-list-container");
    if (!listEl) return;

    try {
      const res = await API.prescriptions.list();
      const prescriptions = res.prescriptions || [];

      if (prescriptions.length === 0) {
        listEl.innerHTML = `
          <div style="text-align:center; padding: 60px 20px; background:var(--bg-card); border-radius:var(--radius-md);">
            <p style="font-size:1.1rem; color:var(--text-secondary); margin-bottom:8px;">No prescriptions uploaded yet.</p>
            <p style="font-size:0.85rem; color:var(--text-muted);">Upload a PDF or prescription image to automatically verify prescription-required medicines.</p>
          </div>
        `;
        return;
      }

      listEl.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px;">
          ${prescriptions.map(p => `
            <div class="medicine-card">
              <div>
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                  <span class="badge ${p.status === 'verified' ? 'badge-otc' : (p.status === 'rejected' ? 'badge-rx' : 'badge-pulse')}">
                    ${p.status.toUpperCase()}
                  </span>
                  <span style="font-size:0.75rem; color:var(--text-muted);">${Components.formatDate(p.created_at)}</span>
                </div>
                <h4 style="color:#fff; margin-bottom:4px;">${p.original_filename}</h4>
                <div style="font-size:0.85rem; color:var(--cyan); margin-bottom:6px;">👨‍⚕️ ${p.doctor_name || 'Doctor not detected'}</div>
                <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:8px;">
                  OCR Confidence: <strong>${Math.round((p.ocr_confidence || 0) * 100)}%</strong> (${p.ocr_provider})
                </div>
                ${p.extracted_medicines && p.extracted_medicines.length > 0 ? `
                  <div style="font-size:0.75rem; background:rgba(255,255,255,0.03); padding:8px; border-radius:4px; margin-top:6px;">
                    <strong>Detected Medicines:</strong>
                    <ul style="margin-left:16px; margin-top:4px;">
                      ${p.extracted_medicines.map(m => `<li>${m}</li>`).join("")}
                    </ul>
                  </div>
                ` : ''}
              </div>
              <div style="margin-top:16px; border-top:1px solid var(--border-subtle); padding-top:12px; display:flex; justify-content:space-between;">
                <a href="/api/prescriptions/${p.id}/file" target="_blank" class="btn-alt-pill" style="text-align:center; flex:1;">
                  View Document
                </a>
              </div>
            </div>
          `).join("")}
        </div>
      `;
    } catch (err) {
      listEl.innerHTML = `<div style="color:var(--rose);">Failed to load prescriptions: ${err.message}</div>`;
    }
  },

  openPrescriptionUploadModal() {
    const content = document.getElementById("prescription-modal-content");
    content.innerHTML = `
      <form id="rx-upload-form">
        <div class="form-group">
          <label class="form-label">Select Prescription File (PDF, PNG, JPG, WEBP) *</label>
          <input type="file" id="rx-file-input" class="form-control" accept=".pdf,.png,.jpg,.jpeg,.webp" required>
        </div>
        <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:16px;">
          Max size: 16MB. The document will be scanned through our OCR engine to extract physician credentials, patient data, and prescribed medicines.
        </p>
        <button type="submit" class="btn-checkout-primary" id="btn-upload-rx-submit">
          Upload & Run OCR Extraction
        </button>
      </form>
      <div id="rx-upload-status" style="margin-top:16px;"></div>
    `;

    document.getElementById("rx-upload-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById("rx-file-input");
      if (!fileInput.files || fileInput.files.length === 0) return;

      const btn = document.getElementById("btn-upload-rx-submit");
      const statusDiv = document.getElementById("rx-upload-status");
      btn.disabled = true;
      btn.textContent = "Uploading & Running Document OCR...";

      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      try {
        const res = await API.prescriptions.upload(formData);
        Components.toast("Prescription uploaded & OCR processed!", "success");
        Components.closeModal("prescription-modal");
        await this.fetchPrescriptions();
      } catch (err) {
        statusDiv.innerHTML = `<div style="color:var(--rose); font-size:0.85rem;">Upload error: ${err.message}</div>`;
        btn.disabled = false;
        btn.textContent = "Upload & Run OCR Extraction";
      }
    });

    Components.openModal("prescription-modal");
  }
};
