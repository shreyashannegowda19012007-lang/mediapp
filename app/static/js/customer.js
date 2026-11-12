/**
 * MediApp Commercial Customer Portal.
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
      <!-- Commercial Healthcare Hero Banner -->
      <section class="customer-hero">
        <div class="hero-content">
          <span class="hero-tag">Licensed Healthcare Delivery Network</span>
          <h1 class="hero-title">Authentic Medicines & Clinical Care, Delivered Fast</h1>
          <p class="hero-subtitle">Browse over 1,250+ verified prescription drugs and daily healthcare essentials with guaranteed cold-chain safety, pharmacist reviews, and up to 70% savings on bioequivalent generics.</p>
          
          <div class="hero-cta-group">
            <button type="button" class="btn-hero-primary" id="btn-hero-upload-rx">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
              <span>Upload Prescription</span>
            </button>
            <button type="button" class="btn-hero-secondary" id="btn-hero-consult">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              <span>Consult Care Assistant</span>
            </button>
          </div>
        </div>

        <!-- Quick Healthcare Service Action Cards -->
        <div class="hero-quick-cards">
          <div class="quick-service-card" id="quick-card-rx">
            <div class="service-card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <div>
              <div class="service-card-title">Order with Rx</div>
              <div class="service-card-desc">15-minute pharmacist review & fast dispatch</div>
            </div>
          </div>

          <div class="quick-service-card" id="quick-card-generics">
            <div class="service-card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>
            </div>
            <div>
              <div class="service-card-title">Generic Savings</div>
              <div class="service-card-desc">Save 50-70% with identical active molecules</div>
            </div>
          </div>

          <div class="quick-service-card" id="quick-card-triage">
            <div class="service-card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            </div>
            <div>
              <div class="service-card-title">Clinical Desk</div>
              <div class="service-card-desc">Check safe non-prescription OTC guidance</div>
            </div>
          </div>

          <div class="quick-service-card" id="quick-card-express">
            <div class="service-card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
            </div>
            <div>
              <div class="service-card-title">45-Min Delivery</div>
              <div class="service-card-desc">Local pharmacy fulfillment to your door</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Trust Assurance Pillars Bar -->
      <section class="trust-bar" aria-label="Commercial quality and safety standards">
        <div class="trust-pillar">
          <div class="trust-pillar-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
          <div class="trust-pillar-info">
            <h4>100% Genuine Medicines</h4>
            <p>Direct from verified manufacturers</p>
          </div>
        </div>

        <div class="trust-pillar">
          <div class="trust-pillar-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>
          </div>
          <div class="trust-pillar-info">
            <h4>Licensed Pharmacists</h4>
            <p>Every prescription reviewed before dispatch</p>
          </div>
        </div>

        <div class="trust-pillar">
          <div class="trust-pillar-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          </div>
          <div class="trust-pillar-info">
            <h4>Generic Price Match</h4>
            <p>Save up to 70% on equivalent bio-drugs</p>
          </div>
        </div>

        <div class="trust-pillar">
          <div class="trust-pillar-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
          <div class="trust-pillar-info">
            <h4>Cold-Chain Delivery</h4>
            <p>Temperature-controlled transport safe packaging</p>
          </div>
        </div>
      </section>

      <!-- Search, Category & Filter Control Section -->
      <section class="search-filter-section">
        <div class="search-bar-wrapper">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
          </svg>
          <input type="text" id="catalogue-search-input" class="input-main-search"
                 placeholder="Search medicine brand, active generic molecule (e.g. Paracetamol, Amlodipine), or health condition..."
                 value="${currentQuery}" autocomplete="off">
        </div>

        <!-- Popular Suggested Searches -->
        <div class="search-chips-row">
          <span class="chips-label">Popular:</span>
          <button type="button" class="search-chip" data-search="Paracetamol">Paracetamol</button>
          <button type="button" class="search-chip" data-search="Azithromycin">Azithromycin</button>
          <button type="button" class="search-chip" data-search="Metformin">Metformin</button>
          <button type="button" class="search-chip" data-search="Atorvastatin">Atorvastatin</button>
          <button type="button" class="search-chip" data-search="Cetirizine">Cetirizine</button>
          <button type="button" class="search-chip" data-search="Pantoprazole">Pantoprazole</button>
          <button type="button" class="search-chip" data-search="Amoxicillin">Amoxicillin</button>
        </div>

        <!-- Category Filter Pills Bar -->
        <div class="filter-pills-bar" id="category-pills-container">
          <button type="button" class="pill-filter ${!currentCat ? 'active' : ''}" data-cat="">All Categories</button>
        </div>

        <!-- Operational Secondary Controls (Pharmacy Store & Rx Filter) -->
        <div class="controls-bar">
          <div class="selector-group">
            <label class="selector-label" for="pharmacy-select">Fulfilling Store:</label>
            <select id="pharmacy-select" class="select-styled">
              <option value="1">Apollo Pharmacy — Indiranagar (⚡ 35-45 mins)</option>
              <option value="2">MedPlus Pharmacy — Koramangala (⚡ 40-50 mins)</option>
              <option value="3">Fortis Health Care Chemist — Bannerghatta (⚡ 45-60 mins)</option>
            </select>
          </div>

          <div class="selector-group">
            <label class="selector-label" for="rx-filter-select">Regulation:</label>
            <select id="rx-filter-select" class="select-styled">
              <option value="">All Medicines</option>
              <option value="0">Over-the-Counter (OTC Only)</option>
              <option value="1">Doctor Prescription (Rx Required)</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Medicine Product Catalog Grid -->
      <div id="medicine-grid" class="medicine-grid">
        <div class="loading-screen"><div class="spinner"></div><p style="color:var(--text-muted);">Loading verified catalog inventory...</p></div>
      </div>
    `;

    // Populate category pills
    try {
      const catRes = await API.medicines.getCategories();
      const pillsContainer = document.getElementById("category-pills-container");
      if (pillsContainer) {
        const allCatBtn = pillsContainer.querySelector('.pill-filter[data-cat=""]');
        if (allCatBtn) {
          allCatBtn.addEventListener("click", () => {
            document.querySelectorAll(".pill-filter").forEach(b => b.classList.remove("active"));
            allCatBtn.classList.add("active");
            State.set("selectedCategory", "");
            this.fetchAndRenderMedicines();
          });
        }
      }
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

    // Attach search input listener with DEBOUNCE to PRESERVE FOCUS
    const searchInput = document.getElementById("catalogue-search-input");
    searchInput.addEventListener("input", (e) => {
      clearTimeout(this._debounceTimer);
      const val = e.target.value;
      State.set("searchQuery", val);
      this._debounceTimer = setTimeout(() => {
        this.fetchAndRenderMedicines();
      }, 250);
    });

    // Wire popular search chips
    container.querySelectorAll(".search-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const query = chip.dataset.search;
        searchInput.value = query;
        State.set("searchQuery", query);
        this.fetchAndRenderMedicines();
      });
    });

    // Wire hero action buttons
    document.getElementById("btn-hero-upload-rx")?.addEventListener("click", () => {
      this.openPrescriptionUploadModal();
    });
    document.getElementById("btn-hero-consult")?.addEventListener("click", () => {
      document.getElementById("btn-toggle-ai")?.click();
    });
    document.getElementById("quick-card-rx")?.addEventListener("click", () => {
      this.openPrescriptionUploadModal();
    });
    document.getElementById("quick-card-generics")?.addEventListener("click", () => {
      searchInput.value = "Generic";
      State.set("searchQuery", "Generic");
      this.fetchAndRenderMedicines();
    });
    document.getElementById("quick-card-triage")?.addEventListener("click", () => {
      document.getElementById("btn-toggle-ai")?.click();
    });
    document.getElementById("quick-card-express")?.addEventListener("click", () => {
      document.getElementById("pharmacy-select")?.focus();
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

  getDosageIconSvg(form) {
    const f = (form || "").toLowerCase();
    if (f.includes("tablet")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><line x1="6" y1="12" x2="18" y2="12"/></svg>`;
    } else if (f.includes("capsule")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="8" width="14" height="8" rx="4" transform="rotate(45 12 12)"/><line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/></svg>`;
    } else if (f.includes("syrup") || f.includes("suspension") || f.includes("solution")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3h6v3H9z"/><path d="M8 6h8a2 2 0 0 1 2 2v11a3 3 0 0 1-3 3H9a3 3 0 0 1-3-3V8a2 2 0 0 1 2-2z"/></svg>`;
    } else if (f.includes("inhaler")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="7" y="3" width="10" height="12" rx="2"/><path d="M7 15v4a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-4"/></svg>`;
    } else if (f.includes("injection")) {
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m18 2 4 4-2 2-4-4 2-2z"/><path d="m14 6-9.5 9.5a2.5 2.5 0 0 0 0 3.5l.5.5a2.5 2.5 0 0 0 3.5 0L18 10"/><line x1="2" y1="22" x2="6.5" y2="17.5"/></svg>`;
    }
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M2 12h20"/></svg>`;
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
          <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-lg);">
            <div style="width:48px; height:48px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; margin:0 auto 16px auto;">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </div>
            <p style="font-size: 1.15rem; font-weight:700; color: var(--text-primary); margin-bottom: 6px;">No medications found matching "${params.q || 'filters'}".</p>
            <p style="font-size: 0.875rem; color: var(--text-muted); max-width:500px; margin:0 auto 16px auto;">Try clearing active filters or searching for active ingredients such as Paracetamol, Amlodipine, Pantoprazole, or Cetirizine.</p>
            <button type="button" class="btn-alt-pill" id="btn-clear-search-filters">Clear All Search Filters</button>
          </div>
        `;
        document.getElementById("btn-clear-search-filters")?.addEventListener("click", () => {
          State.set("searchQuery", "");
          State.set("selectedCategory", "");
          State.set("rxFilter", "");
          const searchInput = document.getElementById("catalogue-search-input");
          if (searchInput) searchInput.value = "";
          document.querySelectorAll(".pill-filter").forEach(b => b.classList.remove("active"));
          document.querySelector('.pill-filter[data-cat=""]')?.classList.add("active");
          this.fetchAndRenderMedicines();
        });
        return;
      }

      grid.innerHTML = medicines.map(med => {
        const isRx = Boolean(med.prescription_required);
        const inStock = med.stock_quantity > 0 && med.is_available;
        const stockClass = !inStock ? "out" : (med.stock_quantity <= 10 ? "low" : "");
        const stockText = !inStock ? "Out of Stock" : (med.stock_quantity <= 10 ? `Low Stock (${med.stock_quantity} left)` : `In Stock`);
        
        // Compute realistic original MRP (e.g. 15% discount for commercial presentation)
        const mrp = (med.unit_price * 1.18).toFixed(2);
        const discountPct = "15% OFF";

        return `
          <article class="medicine-card" data-id="${med.id}">
            <div class="card-top">
              <div class="card-badges">
                <span class="badge-dosage">
                  ${this.getDosageIconSvg(med.dosage_form)}
                  ${med.dosage_form}
                </span>
                ${isRx ? '<span class="badge-rx">Rx Required</span>' : '<span class="badge-otc">OTC</span>'}
                <span class="badge-category">${med.category}</span>
              </div>

              <div class="med-mfr">${med.manufacturer || 'Certified Pharma'}</div>
              <h3 class="med-name">${med.name}</h3>
              <p class="med-generic">
                <span>Molecule: ${med.generic_name} • ${med.strength}</span>
              </p>
              ${med.uses ? `<p class="med-uses">${med.uses}</p>` : ''}
            </div>

            <div class="card-bottom">
              <div class="price-box">
                <div class="price-row">
                  <span class="price-val">${Components.formatCurrency(med.unit_price)}</span>
                  <span class="price-mrp">₹${mrp}</span>
                  <span class="price-discount">${discountPct}</span>
                </div>
                <span class="stock-val ${stockClass}">● ${stockText}</span>
              </div>

              <div class="card-actions">
                <button type="button" class="btn-alt-pill btn-view-alt" data-id="${med.id}" title="Compare generic equivalents and save up to 70%">
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
      Components.toast("Please sign in to add medicines to your cart.", "warning");
      Components.openModal("auth-modal");
      return;
    }

    try {
      const pharmId = State.get("selectedPharmacyId") || 1;
      await API.cart.addItem(medicineId, 1, pharmId);
      Components.toast("Added to cart successfully!", "success");
      await this.refreshCart();
    } catch (err) {
      if (err.status === 409 || (err.data && err.data.conflict)) {
        const confirmSwitch = confirm(`${err.message}\n\nWould you like to clear your current cart and switch to this pharmacy?`);
        if (confirmSwitch) {
          try {
            const pharmId = State.get("selectedPharmacyId") || 1;
            await API.cart.addItem(medicineId, 1, pharmId, true);
            Components.toast("Cart updated to new fulfilling pharmacy!", "success");
            await this.refreshCart();
          } catch (retryErr) {
            Components.toast(retryErr.message, "error");
          }
        }
      } else {
        Components.toast(err.message, "error");
      }
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
        <div class="ddi-alert-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          Clinical Drug Interaction Detected (${interactions.length})
        </div>
        ${interactions.map(intx => `
          <div style="margin-top: 6px; font-size:0.8rem;">
            <strong>[${intx.severity}]</strong> ${intx.medicine_a} + ${intx.medicine_b}: ${intx.title}
            <div style="font-size: 0.75rem; color: #b91c1c; margin-top: 2px;">${intx.management}</div>
          </div>
        `).join("")}
      `;
    } else {
      ddiAlert.classList.add("hidden");
    }

    if (items.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 40px 10px; color: var(--text-muted);">
          <div style="width:48px; height:48px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; margin:0 auto 12px auto;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
          </div>
          <p style="font-size: 1.05rem; font-weight:600; color:var(--text-primary); margin-bottom: 6px;">Your cart is empty.</p>
          <p style="font-size: 0.85rem;">Browse medicines in the catalogue and add items to begin checkout.</p>
        </div>
      `;
      footer.innerHTML = "";
      return;
    }

    container.innerHTML = items.map(it => `
      <div class="cart-item-row" data-id="${it.medicine_id}">
        <div class="cart-item-info">
          <div class="cart-item-name">${it.name}</div>
          <div class="cart-item-price">${Components.formatCurrency(it.unit_price)} × ${it.quantity} = <strong>${Components.formatCurrency(it.line_total)}</strong></div>
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
      <div class="totals-row"><span>Doorstep Delivery:</span> <span>${totals.delivery_fee === 0 ? '<span style="color:var(--emerald); font-weight:700;">FREE</span>' : Components.formatCurrency(totals.delivery_fee)}</span></div>
      ${totals.discount > 0 ? `<div class="totals-row" style="color:var(--emerald);"><span>Promotional Discount:</span> <span>-${Components.formatCurrency(totals.discount)}</span></div>` : ''}
      <div class="totals-row grand-total"><span>Order Total:</span> <span>${Components.formatCurrency(totals.total)}</span></div>
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
        <div style="margin-bottom: 20px; padding: 16px; background: var(--bg-canvas); border:1px solid var(--border-subtle); border-radius: var(--radius-md);">
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Reference Branded Medicine</div>
          <div style="font-size: 1.15rem; font-weight:700; color:var(--text-primary); margin-top:2px;">${target.name}</div>
          <div style="color:var(--cyan); font-size:0.875rem; font-weight:600;">Active Molecule: ${target.generic_name} • ${target.strength} (${target.dosage_form})</div>
          <div style="font-size: 1.1rem; font-weight:800; margin-top:6px; color:var(--text-primary);">MRP: ${Components.formatCurrency(target.mrp)}</div>
        </div>

        <h4 style="margin-bottom: 12px; font-size: 1rem; color:var(--text-primary);">Bioequivalent Lower-Cost Alternatives:</h4>
        ${alts.length === 0 ? '<p style="color:var(--text-muted);">No cheaper generic alternatives found for this molecule and strength combination.</p>' : `
          <div style="display:flex; flex-direction:column; gap:12px;">
            ${alts.map(a => `
              <div style="background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:16px; display:flex; justify-content:space-between; align-items:center; box-shadow:var(--shadow-xs);">
                <div>
                  <div style="font-weight:700; color:var(--text-primary); font-size:1rem;">${a.name}</div>
                  <div style="font-size:0.8rem; color:var(--text-muted);">Manufacturer: ${a.manufacturer}</div>
                  <div style="font-size:0.8rem; color:var(--emerald); font-weight:700; margin-top:3px;">
                    ✓ Save ${a.savings_pct}% (${Components.formatCurrency(a.savings_amount)} per pack)
                  </div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:1.2rem; font-weight:800; color:var(--text-primary); margin-bottom:6px;">${Components.formatCurrency(a.price)}</div>
                  <button type="button" class="btn-add-cart btn-choose-generic" data-id="${a.id}" style="padding:6px 14px; font-size:0.8rem;">
                    Switch & Save
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

    // Fetch saved customer addresses
    let savedAddresses = [];
    try {
      const addrRes = await API.auth.getAddresses();
      savedAddresses = addrRes.addresses || [];
    } catch {}

    const defaultAddr = savedAddresses.find(a => a.is_default) || savedAddresses[0] || null;
    const initAddr1 = defaultAddr ? defaultAddr.line1 : "Flat 402, Green Glen Layout";
    const initAddr2 = defaultAddr ? (defaultAddr.line2 || "") : "Outer Ring Road, Bellandur";
    const initCity = defaultAddr ? defaultAddr.city : "Bengaluru";
    const initState = defaultAddr ? defaultAddr.state : "Karnataka";
    const initPin = defaultAddr ? defaultAddr.pincode : "560103";

    modalContent.innerHTML = `
      <form id="checkout-form">
        <h4 style="margin-bottom: 12px; color:var(--text-primary);">1. Delivery Destination Address</h4>
        
        ${savedAddresses.length > 0 ? `
          <div class="form-group" style="margin-bottom: 14px;">
            <label class="form-label">Choose Saved Address:</label>
            <select id="chk-saved-addr-select" class="select-styled" style="width:100%;">
              ${savedAddresses.map((a, idx) => `
                <option value="${idx}" ${a.id === (defaultAddr ? defaultAddr.id : null) ? 'selected' : ''}>
                  ${Components.escapeHtml(a.line1)}, ${Components.escapeHtml(a.city)} (${Components.escapeHtml(a.pincode)})${a.is_default ? ' [Default]' : ''}
                </option>
              `).join("")}
              <option value="custom">-- Enter New / Custom Address --</option>
            </select>
          </div>
        ` : ''}

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="form-group" style="grid-column: 1/-1;">
            <label class="form-label">Address Line 1 *</label>
            <input type="text" id="chk-addr1" class="form-control" required value="${Components.escapeHtml(initAddr1)}">
          </div>
          <div class="form-group" style="grid-column: 1/-1;">
            <label class="form-label">Address Line 2 (Area, Landmark)</label>
            <input type="text" id="chk-addr2" class="form-control" value="${Components.escapeHtml(initAddr2)}">
          </div>
          <div class="form-group">
            <label class="form-label">City *</label>
            <input type="text" id="chk-city" class="form-control" required value="${Components.escapeHtml(initCity)}">
          </div>
          <div class="form-group">
            <label class="form-label">State *</label>
            <input type="text" id="chk-state" class="form-control" required value="${Components.escapeHtml(initState)}">
          </div>
          <div class="form-group">
            <label class="form-label">Pincode *</label>
            <input type="text" id="chk-pin" class="form-control" required value="${Components.escapeHtml(initPin)}">
          </div>
          <div class="form-group">
            <label class="form-label">Recipient Contact Phone *</label>
            <input type="text" id="chk-phone" class="form-control" required value="${Components.escapeHtml(user.phone || '+91 9876543210')}">
          </div>
        </div>

        ${hasRx ? `
          <div style="margin: 20px 0; padding: 14px; background: var(--rose-bg); border: 1px solid var(--rose-border); border-radius: var(--radius-md);">
            <h4 style="color: var(--rose); margin-bottom: 6px;">2. Prescription Attachment Required (Rx)</h4>
            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 10px;">Your cart contains prescription medications. Attach a verified doctor's prescription to proceed.</p>
            ${userPrescriptions.length > 0 ? `
              <select id="chk-prescription-select" class="select-styled" style="width:100%;">
                ${userPrescriptions.map(p => `
                  <option value="${p.id}">Prescription #${p.id} (${p.original_filename}) — Status: ${p.status}</option>
                `).join("")}
              </select>
            ` : `
              <p style="color:var(--amber); font-size:0.85rem;">No uploaded prescriptions found. Upload one now via the Prescription tab.</p>
            `}
          </div>
        ` : ''}

        <h4 style="margin: 20px 0 12px 0; color:var(--text-primary);">3. Select Payment Method</h4>
        <div style="display:flex; flex-direction:column; gap:10px; margin-bottom: 20px;">
          <label style="display:flex; align-items:center; gap:10px; background:var(--bg-canvas); border:1px solid var(--border-subtle); padding:14px; border-radius:var(--radius-md); cursor:pointer;">
            <input type="radio" name="payment_method" value="demo" checked>
            <div>
              <div style="font-weight:700; color:var(--text-primary);">Instant Verification Payment (Demo Gateway)</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">Safe local simulation. Exercises full backend order, payment, and inventory flow.</div>
            </div>
          </label>
          <label style="display:flex; align-items:center; gap:10px; background:var(--bg-canvas); border:1px solid var(--border-subtle); padding:14px; border-radius:var(--radius-md); cursor:pointer;">
            <input type="radio" name="payment_method" value="razorpay">
            <div>
              <div style="font-weight:700; color:var(--text-primary);">Razorpay Secure Checkout</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">Real/Test Razorpay checkout with HMAC-SHA256 signature verification.</div>
            </div>
          </label>
        </div>

        <div style="background:var(--bg-canvas); border:1px solid var(--border-subtle); padding:16px; border-radius:var(--radius-md); margin-bottom: 20px;">
          <div class="totals-row"><span>Items:</span> <span>${cart.item_count} items</span></div>
          <div class="totals-row"><span>Subtotal:</span> <span>${Components.formatCurrency(cart.totals.subtotal)}</span></div>
          <div class="totals-row"><span>Tax (5%):</span> <span>${Components.formatCurrency(cart.totals.tax)}</span></div>
          <div class="totals-row"><span>Delivery Fee:</span> <span>${Components.formatCurrency(cart.totals.delivery_fee)}</span></div>
          <div class="totals-row grand-total"><span>Order Total:</span> <span>${Components.formatCurrency(cart.totals.total)}</span></div>
        </div>

        <button type="submit" class="btn-checkout-primary" id="btn-submit-order">
          Confirm Order & Pay ${Components.formatCurrency(cart.totals.total)}
        </button>
      </form>
    `;

    document.getElementById("checkout-form").addEventListener("submit", (e) => this.handleOrderSubmit(e));

    const addrSelect = document.getElementById("chk-saved-addr-select");
    if (addrSelect) {
      addrSelect.addEventListener("change", (e) => {
        const val = e.target.value;
        if (val !== "custom") {
          const a = savedAddresses[parseInt(val)];
          if (a) {
            document.getElementById("chk-addr1").value = a.line1 || "";
            document.getElementById("chk-addr2").value = a.line2 || "";
            document.getElementById("chk-city").value = a.city || "";
            document.getElementById("chk-state").value = a.state || "";
            document.getElementById("chk-pin").value = a.pincode || "";
          }
        } else {
          document.getElementById("chk-addr1").value = "";
          document.getElementById("chk-addr2").value = "";
          document.getElementById("chk-city").value = "";
          document.getElementById("chk-state").value = "";
          document.getElementById("chk-pin").value = "";
        }
      });
    }

    Components.openModal("checkout-modal");
  },

  async handleOrderSubmit(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-submit-order");
    btn.disabled = true;
    btn.textContent = "Processing Order & Payment...";

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
        Components.toast("Order placed and payment verified successfully!", "success");
      } else {
        // Real Razorpay Initiation
        const payInit = await API.payments.createOrder(order.id);
        const pOrder = payInit.payment_order;

        if (window.Razorpay) {
          const user = State.get("user") || {};
          await new Promise((resolve, reject) => {
            const rzp = new window.Razorpay({
              key: pOrder.key,
              amount: pOrder.amount * 100,
              currency: pOrder.currency || "INR",
              name: "MediApp Healthcare",
              description: `Prescription Order ${order.id}`,
              order_id: pOrder.provider_order_id,
              prefill: {
                name: user.full_name || "",
                email: user.email || "",
                contact: user.phone || ""
              },
              theme: { color: "#0284c7" },
              handler: async (response) => {
                try {
                  await API.payments.verify(order.id, {
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_signature: response.razorpay_signature
                  });
                  resolve();
                } catch (vErr) {
                  reject(vErr);
                }
              },
              modal: {
                ondismiss: () => {
                  reject(new Error("Razorpay payment modal was dismissed without completion."));
                }
              }
            });
            rzp.on("payment.failed", (resp) => {
              reject(new Error(resp.error?.description || "Payment failed at gateway."));
            });
            rzp.open();
          });
          Components.toast("Payment completed and verified via Razorpay!", "success");
        } else {
          Components.toast("Razorpay SDK offline: simulating verification...", "info");
          await API.payments.verify(order.id, {
            razorpay_order_id: pOrder.provider_order_id,
            razorpay_payment_id: "pay_test_" + Date.now(),
            razorpay_signature: "mock_test_sig"
          });
        }
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
        <div>
          <h2>Your Orders & Real-time Delivery Tracking</h2>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Track live courier progress and prescription verification status.</p>
        </div>
        <button type="button" class="btn-alt-pill" id="btn-refresh-orders">↻ Refresh</button>
      </div>
      <div id="customer-orders-list">
        <div class="loading-screen"><div class="spinner"></div><p style="color:var(--text-muted);">Fetching your orders...</p></div>
      </div>
    `;

    document.getElementById("btn-refresh-orders").addEventListener("click", () => this.fetchCustomerOrders());
    
    // Register visibility-aware auto-polling for active orders
    Sync.register("customer_orders", () => this.fetchCustomerOrders(), 5000);
    await this.fetchCustomerOrders();
  },

  async fetchCustomerOrders() {
    const listEl = document.getElementById("customer-orders-list");
    if (!listEl) return;

    try {
      const res = await API.orders.list();
      const orders = res.orders || [];

      if (orders.length === 0) {
        listEl.innerHTML = `
          <div style="text-align:center; padding: 60px 20px; background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-lg);">
            <div style="width:48px; height:48px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; margin:0 auto 12px auto;">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
            </div>
            <p style="font-size:1.1rem; font-weight:700; color:var(--text-primary); margin-bottom:6px;">You haven't placed any orders yet.</p>
            <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:16px;">Explore our medicine catalogue to make your first purchase.</p>
            <button type="button" class="btn-add-cart" id="btn-browse-catalogue-empty">Browse Catalog</button>
          </div>
        `;
        document.getElementById("btn-browse-catalogue-empty")?.addEventListener("click", () => {
          State.set("activeTab", "catalogue");
          document.querySelector('.nav-tab-btn[data-tab="catalogue"]')?.click();
        });
        return;
      }

      listEl.innerHTML = orders.map(ord => `
        <div class="stat-card" style="margin-bottom:18px;" data-order-id="${ord.id}">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px;">
            <div>
              <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase;">Order ID: #${ord.id}</div>
              <div style="font-size:0.875rem; color:var(--text-secondary); margin-top:2px;">
                Pharmacy: <strong>${Components.escapeHtml(ord.pharmacy_name)}</strong> • ${Components.formatDate(ord.created_at)}
              </div>
            </div>
            <div style="text-align:right;">
              <div style="font-size: 1.35rem; font-weight:800; color:var(--text-primary);">${Components.formatCurrency(ord.total_amount)}</div>
              <div style="display:flex; gap:6px; justify-content:flex-end; margin-top:4px;">
                ${Components.renderPaymentBadge(ord.payment_status)}
                ${Components.renderStatusBadge(ord.order_status)}
              </div>
            </div>
          </div>

          ${this.renderStepperHtml(ord.order_status)}

          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px; padding-top:14px; border-top:1px solid var(--border-subtle);">
            <div style="font-size:0.85rem; color:var(--text-muted);">
              ${ord.cancellation_reason ? `<span style="color:var(--rose);">Reason: ${Components.escapeHtml(ord.cancellation_reason)}</span>` : 'Fulfilled by certified pharmacy partner'}
            </div>
            <div style="display:flex; gap:8px;">
              ${["PLACED", "AWAITING_PRESCRIPTION"].includes(ord.order_status) ? `
                <button type="button" class="btn-alt-pill btn-cancel-order" data-id="${ord.id}" style="color:var(--rose); border-color:var(--rose-border);">
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
      { key: "IN_TRANSIT", label: "Out for Delivery" },
      { key: "DELIVERED", label: "Delivered" }
    ];

    if (status === "CANCELLED") {
      return `<div style="padding:10px; background:var(--rose-bg); color:var(--rose); border-radius:var(--radius-sm); text-align:center; font-weight:600;">This order has been cancelled and refunded. Inventory was safely restored.</div>`;
    }

    const statusOrder = ["PLACED", "ACCEPTED", "PREPARING", "READY_FOR_PICKUP", "DELIVERY_ASSIGNED", "PICKED_UP", "IN_TRANSIT", "DELIVERED"];
    const currentIdx = statusOrder.indexOf(status);

    return `
      <div style="display:flex; align-items:center; justify-content:space-between; margin:16px 0; position:relative;">
        ${steps.map((st, idx) => {
          const stepOrderIdx = statusOrder.indexOf(st.key);
          const isCompleted = currentIdx > stepOrderIdx;
          const isActive = currentIdx === stepOrderIdx || (st.key === "IN_TRANSIT" && ["DELIVERY_ASSIGNED", "PICKED_UP"].includes(status));
          const color = isCompleted || isActive ? 'var(--primary)' : 'var(--border-muted)';
          return `
            <div style="display:flex; flex-direction:column; align-items:center; z-index:2; flex:1;">
              <div style="width:26px; height:26px; border-radius:50%; background:${isCompleted ? 'var(--primary)' : (isActive ? 'var(--primary-light)' : 'var(--bg-canvas)')}; border:2px solid ${color}; color:${isCompleted ? '#fff' : (isActive ? 'var(--primary)' : 'var(--text-muted)')}; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700;">
                ${isCompleted ? '✓' : idx + 1}
              </div>
              <span style="font-size:0.725rem; font-weight:600; color:${isActive ? 'var(--primary)' : 'var(--text-muted)'}; margin-top:4px; text-align:center;">
                ${st.label}
              </span>
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
      const modalTitle = document.getElementById("order-detail-title");
      if (modalTitle) {
        modalTitle.textContent = `Order Details — #${ord.id}`;
      }

      modalContent.innerHTML = `
        <div style="display:flex; justify-content:space-between; margin-bottom: 20px;">
          <div>
            <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Order Reference</div>
            <div style="font-size:1.3rem; font-weight:800; color:var(--text-primary);">#${ord.id}</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">${Components.formatDate(ord.created_at)}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:1.4rem; font-weight:800; color:var(--text-primary);">${Components.formatCurrency(ord.total_amount)}</div>
            <div>${Components.renderStatusBadge(ord.order_status)}</div>
          </div>
        </div>

        <h4 style="margin: 16px 0 8px 0; color:var(--text-primary);">Itemized Medicine Invoice:</h4>
        <div class="table-responsive" style="margin-bottom: 20px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Active Generic</th>
                <th>Unit Price</th>
                <th>Qty</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              ${ord.items.map(it => `
                <tr>
                  <td><strong>${Components.escapeHtml(it.medicine_name_snapshot)}</strong></td>
                  <td>${Components.escapeHtml(it.generic_name_snapshot)} (${Components.escapeHtml(it.strength_snapshot)})</td>
                  <td>${Components.formatCurrency(it.unit_price)}</td>
                  <td>${it.quantity}</td>
                  <td><strong>${Components.formatCurrency(it.total_price)}</strong></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-bottom:20px;">
          <div style="background:var(--bg-canvas); border:1px solid var(--border-subtle); padding:14px; border-radius:var(--radius-md);">
            <div style="font-weight:700; margin-bottom:4px; color:var(--text-primary);">Delivery Destination</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">
              ${Components.escapeHtml(ord.delivery_address.line1)}<br>
              ${ord.delivery_address.line2 ? `${Components.escapeHtml(ord.delivery_address.line2)}<br>` : ''}
              ${Components.escapeHtml(ord.delivery_address.city)}, ${Components.escapeHtml(ord.delivery_address.state)} - ${Components.escapeHtml(ord.delivery_address.pincode)}<br>
              Phone: ${Components.escapeHtml(ord.delivery_address.recipient_phone || 'N/A')}
            </div>
          </div>
          <div style="background:var(--bg-canvas); border:1px solid var(--border-subtle); padding:14px; border-radius:var(--radius-md);">
            <div style="font-weight:700; margin-bottom:4px; color:var(--text-primary);">Fulfilling Pharmacy</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">
              ${Components.escapeHtml(ord.pharmacy_name)}<br>
              ${Components.escapeHtml(ord.pharmacy_address)}<br>
              Phone: ${Components.escapeHtml(ord.pharmacy_phone)}
            </div>
          </div>
        </div>

        <h4 style="margin: 16px 0 8px 0; color:var(--text-primary);">Order Timeline:</h4>
        <div style="display:flex; flex-direction:column; gap:8px;">
          ${ord.timeline.map(t => `
            <div style="font-size:0.8rem; background:var(--bg-canvas); border:1px solid var(--border-subtle); padding:8px 12px; border-radius:var(--radius-sm); display:flex; justify-content:space-between;">
              <span><strong>${Components.escapeHtml(t.to_status)}</strong>: ${Components.escapeHtml(t.notes || 'Status updated')}</span>
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
          <h2>Prescription Management & Verification</h2>
          <p style="color:var(--text-secondary); font-size:0.9rem;">Upload valid doctor prescriptions (PDF or Image) for pharmacist review and automatic cart item matching.</p>
        </div>
        <button type="button" class="btn-checkout-primary" id="btn-open-rx-upload" style="margin:0; width:auto; padding:10px 20px;">
          + Upload New Prescription
        </button>
      </div>

      <div id="prescriptions-list-container">
        <div class="loading-screen"><div class="spinner"></div><p style="color:var(--text-muted);">Loading your prescriptions...</p></div>
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
          <div style="text-align:center; padding: 60px 20px; background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-lg);">
            <div style="width:48px; height:48px; border-radius:50%; background:var(--primary-light); color:var(--primary); display:flex; align-items:center; justify-content:center; margin:0 auto 12px auto;">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <p style="font-size:1.1rem; font-weight:700; color:var(--text-primary); margin-bottom:6px;">No prescriptions uploaded yet.</p>
            <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:16px;">Upload a PDF or prescription photo to automatically verify prescription-required medicines.</p>
            <button type="button" class="btn-add-cart" id="btn-empty-upload-rx">+ Upload Prescription</button>
          </div>
        `;
        document.getElementById("btn-empty-upload-rx")?.addEventListener("click", () => this.openPrescriptionUploadModal());
        return;
      }

      listEl.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px;">
          ${prescriptions.map(p => `
            <div class="medicine-card">
              <div>
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                  <span class="badge ${p.status === 'verified' ? 'badge-otc' : (p.status === 'rejected' ? 'badge-rx' : 'badge-category')}">
                    ${p.status.toUpperCase()}
                  </span>
                  <span style="font-size:0.75rem; color:var(--text-muted);">${Components.formatDate(p.created_at)}</span>
                </div>
                <h4 style="color:var(--text-primary); margin-bottom:4px;">${p.original_filename}</h4>
                <div style="font-size:0.85rem; color:var(--primary); font-weight:600; margin-bottom:6px;">Prescriber: ${p.doctor_name || 'Physician Review Pending'}</div>
                <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:8px;">
                  OCR Confidence: <strong>${Math.round((p.ocr_confidence || 0) * 100)}%</strong> (${p.ocr_provider})
                </div>
                ${p.extracted_medicines && p.extracted_medicines.length > 0 ? `
                  <div style="font-size:0.775rem; background:var(--bg-canvas); border:1px solid var(--border-subtle); padding:10px; border-radius:var(--radius-sm); margin-top:8px;">
                    <strong>Detected Prescribed Items:</strong>
                    <ul style="margin-left:16px; margin-top:4px;">
                      ${p.extracted_medicines.map(m => `<li>${m}</li>`).join("")}
                    </ul>
                  </div>
                ` : ''}
              </div>
              <div style="margin-top:16px; border-top:1px solid var(--border-subtle); padding-top:12px; display:flex; justify-content:space-between;">
                <a href="/api/prescriptions/${p.id}/file" target="_blank" class="btn-alt-pill" style="text-align:center; flex:1;">
                  View Original Document
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
          Max file size: 16MB. Our clinical OCR pipeline will verify doctor registration, signature, date, and prescribed medicine names.
        </p>
        <button type="submit" class="btn-checkout-primary" id="btn-upload-rx-submit">
          Upload & Verify Prescription
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
      btn.textContent = "Processing Prescription Document...";

      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      try {
        const res = await API.prescriptions.upload(formData);
        Components.toast("Prescription uploaded & verified!", "success");
        Components.closeModal("prescription-modal");
        await this.fetchPrescriptions();
      } catch (err) {
        statusDiv.innerHTML = `<div style="color:var(--rose); font-size:0.85rem;">Upload error: ${err.message}</div>`;
        btn.disabled = false;
        btn.textContent = "Upload & Verify Prescription";
      }
    });

    Components.openModal("prescription-modal");
  }
};
