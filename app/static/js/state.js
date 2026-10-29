/**
 * MediApp Global Reactive State Store.
 * Centralizes auth session, active role, cart count, filters, and subscriptions.
 */

const State = {
  _data: {
    user: null,
    capabilities: {},
    activeRole: "customer",
    activeTab: "catalogue", // e.g. 'catalogue', 'orders', 'prescriptions'
    cart: {
      items: [],
      item_count: 0,
      totals: { subtotal: 0, tax: 0, delivery_fee: 0, discount: 0, total: 0 },
      drug_interactions: { has_interactions: false, interactions: [] }
    },
    selectedPharmacyId: 1,
    searchQuery: "",
    selectedCategory: "",
    selectedDosageForm: "",
    rxFilter: ""
  },

  _listeners: {},

  get(key) {
    return this._data[key];
  },

  set(key, value) {
    this._data[key] = value;
    this.notify(key, value);
  },

  update(key, partial) {
    if (typeof this._data[key] === "object" && this._data[key] !== null) {
      this._data[key] = { ...this._data[key], ...partial };
      this.notify(key, this._data[key]);
    } else {
      this.set(key, partial);
    }
  },

  subscribe(key, callback) {
    if (!this._listeners[key]) {
      this._listeners[key] = [];
    }
    this._listeners[key].push(callback);
    return () => {
      this._listeners[key] = this._listeners[key].filter(cb => cb !== callback);
    };
  },

  notify(key, value) {
    if (this._listeners[key]) {
      this._listeners[key].forEach(cb => {
        try {
          cb(value);
        } catch (e) {
          console.error(`Error in State subscriber for '${key}':`, e);
        }
      });
    }
  }
};
