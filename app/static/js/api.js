/**
 * MediApp API Client.
 * Handles unified request dispatching, session cookies, JSON serialization,
 * and traceable error normalization across all four portals.
 */

const API = {
  async request(endpoint, options = {}) {
    const defaultHeaders = {
      "Accept": "application/json"
    };

    if (!(options.body instanceof FormData)) {
      defaultHeaders["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers
      },
      credentials: "same-origin"
    };

    try {
      const response = await fetch(endpoint, config);
      const isJson = (response.headers.get("content-type") || "").includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        const errorMsg = (typeof data === "object" && data.error) ? data.error : `HTTP ${response.status}: ${response.statusText}`;
        const error = new Error(errorMsg);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      console.error(`API Error on [${options.method || "GET"} ${endpoint}]:`, err);
      throw err;
    }
  },

  get(endpoint, params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${endpoint}?${query}` : endpoint;
    return this.request(url, { method: "GET" });
  },

  post(endpoint, body = {}) {
    return this.request(endpoint, {
      method: "POST",
      body: body instanceof FormData ? body : JSON.stringify(body)
    });
  },

  put(endpoint, body = {}) {
    return this.request(endpoint, {
      method: "PUT",
      body: JSON.stringify(body)
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  },

  // Auth Endpoints
  auth: {
    login: (email, password) => API.post("/api/auth/login", { email, password }),
    demoLogin: (role) => API.post("/api/auth/demo-login", { role }),
    logout: () => API.post("/api/auth/logout"),
    getMe: () => API.get("/api/auth/me"),
    getGoogleUrl: () => API.get("/api/auth/google/url"),
    updateProfile: (profile) => API.put("/api/auth/profile", profile)
  },

  // Medicine Catalogue Endpoints
  medicines: {
    search: (params) => API.get("/api/medicines", params),
    getDetail: (id, pharmacy_id) => API.get(`/api/medicines/${id}`, pharmacy_id ? { pharmacy_id } : {}),
    getCategories: () => API.get("/api/medicines/categories"),
    getDosageForms: () => API.get("/api/medicines/dosage-forms"),
    checkDDI: (medicine_ids) => API.post("/api/medicines/check-ddi", { medicine_ids }),
    getGenericAlternatives: (id) => API.get(`/api/medicines/${id}/generic-alternatives`)
  },

  // Cart Endpoints
  cart: {
    get: () => API.get("/api/cart"),
    addItem: (medicine_id, quantity = 1, pharmacy_id) => API.post("/api/cart/items", { medicine_id, quantity, pharmacy_id }),
    updateItem: (medicine_id, quantity) => API.put(`/api/cart/items/${medicine_id}`, { quantity }),
    removeItem: (medicine_id) => API.delete(`/api/cart/items/${medicine_id}`),
    clear: () => API.delete("/api/cart")
  },

  // Orders Endpoints
  orders: {
    create: (payload) => API.post("/api/orders", payload),
    list: () => API.get("/api/orders"),
    get: (order_id) => API.get(`/api/orders/${order_id}`),
    transition: (order_id, target_status, notes) => API.post(`/api/orders/${order_id}/transition`, { target_status, notes }),
    cancel: (order_id, reason) => API.post(`/api/orders/${order_id}/cancel`, { reason })
  },

  // Pharmacy Portal Endpoints
  pharmacy: {
    getDashboard: (pharmacy_id) => API.get("/api/pharmacy/dashboard", pharmacy_id ? { pharmacy_id } : {}),
    getOrders: (status) => API.get("/api/pharmacy/orders", status ? { status } : {}),
    acceptOrder: (order_id) => API.post(`/api/pharmacy/orders/${order_id}/accept`),
    rejectOrder: (order_id, reason) => API.post(`/api/pharmacy/orders/${order_id}/reject`, { reason }),
    getInventory: (params) => API.get("/api/pharmacy/inventory", params),
    addInventory: (item) => API.post("/api/pharmacy/inventory", item),
    updateInventory: (medicine_id, updates) => API.put(`/api/pharmacy/inventory/${medicine_id}`, updates)
  },

  // Delivery Portal Endpoints
  delivery: {
    getProfile: () => API.get("/api/delivery/profile"),
    getAvailable: () => API.get("/api/delivery/available"),
    getActive: () => API.get("/api/delivery/active"),
    claim: (order_id) => API.post(`/api/delivery/orders/${order_id}/claim`),
    pickup: (order_id) => API.post(`/api/delivery/orders/${order_id}/pickup`),
    inTransit: (order_id) => API.post(`/api/delivery/orders/${order_id}/in-transit`),
    complete: (order_id, proof) => API.post(`/api/delivery/orders/${order_id}/complete`, { proof }),
    fail: (order_id, reason) => API.post(`/api/delivery/orders/${order_id}/fail`, { reason }),
    getHistory: () => API.get("/api/delivery/history")
  },

  // Administrator Endpoints
  admin: {
    getStats: () => API.get("/api/admin/stats"),
    getUsers: (params) => API.get("/api/admin/users", params),
    toggleUserStatus: (user_id, is_active) => API.put(`/api/admin/users/${user_id}/status`, { is_active }),
    getPharmacies: (status) => API.get("/api/admin/pharmacies", status ? { status } : {}),
    updatePharmacyStatus: (pharmacy_id, status) => API.put(`/api/admin/pharmacies/${pharmacy_id}/status`, { status }),
    getAuditLogs: () => API.get("/api/admin/audit-logs"),
    getSystemHealth: () => API.get("/api/admin/system-health")
  },

  // Payments Endpoints
  payments: {
    createOrder: (order_id) => API.post("/api/payments/create-order", { order_id }),
    verify: (order_id, payload) => API.post("/api/payments/verify", { order_id, ...payload })
  },

  // Prescriptions Endpoints
  prescriptions: {
    upload: (formData) => API.post("/api/prescriptions/upload", formData),
    list: () => API.get("/api/prescriptions"),
    get: (id) => API.get(`/api/prescriptions/${id}`),
    verify: (id, decision, rejection_reason) => API.post(`/api/prescriptions/${id}/verify`, { decision, rejection_reason })
  },

  // AI Ailment Assistant
  ai: {
    consult: (query) => API.post("/api/ai/consult", { query })
  }
};
