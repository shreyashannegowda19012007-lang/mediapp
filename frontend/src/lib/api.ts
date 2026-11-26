/**
 * MediApp Clinical API Client
 * Strongly-typed asynchronous fetch interface communicating with the Flask REST API.
 */

export interface Medicine {
  id: number;
  name: string;
  generic_name: string;
  category: string;
  dosage_form: string;
  strength: string;
  manufacturer: string;
  prescription_required: number; // 0 or 1
  mrp: number;
  unit_price?: number;
  stock_quantity?: number;
  is_available?: number;
  uses?: string;
  side_effects?: string;
  contraindications?: string;
  cold_chain?: boolean; // Evaluated or mapped for temperature-sensitive items
  requires_cold_chain?: boolean | number; // Direct database column indicator
}

export interface GenericAlternative {
  target_medicine?: {
    id: number;
    name: string;
    generic_name: string;
    mrp: number;
  };
  has_alternatives?: boolean;
  alternatives?: Array<{
    id: number;
    name: string;
    generic_name: string;
    dosage_form: string;
    strength: string;
    price: number;
    manufacturer: string;
    is_cheaper: boolean;
    savings_pct: number;
    savings_amount: number;
    match_type: string;
  }>;
  // Legacy / fallback flat format
  brand_id?: number;
  brand_name?: string;
  generic_name?: string;
  brand_price?: number;
  savings_amount?: number;
  savings_percentage?: number;
  has_cheaper_generic?: boolean;
  generic_alternative?: {
    id: number;
    name: string;
    generic_name: string;
    dosage_form: string;
    strength: string;
    unit_price: number;
    manufacturer: string;
  } | null;
}

export interface CartItem {
  cart_item_id: number;
  medicine_id: number;
  quantity: number;
  name: string;
  generic_name: string;
  strength: string;
  dosage_form: string;
  category: string;
  prescription_required: number;
  mrp: number;
  unit_price: number;
  line_total: number;
  is_available: number;
  stock_quantity: number;
}

export interface CartData {
  cart_id: number;
  pharmacy_id: number;
  pharmacy_name: string;
  items: CartItem[];
  pricing: {
    subtotal: number;
    delivery_fee: number;
    tax: number;
    discount: number;
    total: number;
  };
  has_prescription_items: boolean;
  drug_interactions?: {
    has_interactions: boolean;
    interactions: Array<{
      severity: string;
      description: string;
      drugs: string[];
    }>;
  };
}

export interface Order {
  id: number;
  order_number: string;
  status: string;
  order_status?: string;
  prescription_id?: number | null;
  payment_status: string;
  total_amount: number;
  delivery_address: string;
  created_at: string;
  estimated_delivery_time?: string;
  cold_chain?: boolean;
  delivery_agent_name?: string;
  delivery_agent_phone?: string;
  otp?: string;
  delivery_otp?: string;
  items?: Array<{
    id: number;
    medicine_name: string;
    quantity: number;
    unit_price: number;
    prescription_required: number;
  }>;
}

export interface Prescription {
  id: number;
  user_id?: number;
  customer_id?: number;
  customer_name?: string;
  customer_email?: string;
  file_path?: string;
  original_filename: string;
  file_size?: number;
  mime_type?: string;
  status: "pending" | "verified" | "rejected";
  doctor_name?: string | null;
  patient_name?: string | null;
  prescription_date?: string | null;
  ocr_extracted_text?: string;
  extracted_text?: string;
  ocr_confidence?: number;
  ocr_provider?: string;
  detected_medicines?: string[];
  extracted_medicines?: string[];
  rejection_reason?: string | null;
  clinical_notes?: string | null;
  created_at: string;
}

export interface UserSession {
  user_id: number;
  email: string;
  full_name: string;
  role: "customer" | "pharmacy" | "delivery" | "admin";
  phone?: string;
  authorized_roles?: string[];
}

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const defaultHeaders: HeadersInit = {
    Accept: "application/json",
  };

  if (!(options.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  if (typeof window !== "undefined") {
    const token = localStorage.getItem("mediapp_token") || sessionStorage.getItem("mediapp_token");
    if (token) {
      (defaultHeaders as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(endpoint, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: "include",
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data.error || data.message || `API Error: ${response.status} ${response.statusText}`;
    throw new Error(errorMsg);
  }

  return data as T;
}

export const api = {
  // Authentication & Session
  auth: {
    getSession: () => apiFetch<{ status: string; authenticated: boolean; user?: UserSession }>("/api/auth/session"),
    getCurrentUser: () =>
      apiFetch<{ status: string; authenticated: boolean; user?: UserSession & { address?: string } }>("/api/auth/me"),
    register: (payload: { email: string; password: string; full_name: string; phone: string; address?: string }) =>
      apiFetch<{ status: string; message: string; user: UserSession }>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    login: async (credentials: { email: string; password?: string; role?: string }) => {
      const res = await apiFetch<{ status: string; user: UserSession; token?: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      });
      if (typeof window !== "undefined" && res.token) {
        localStorage.setItem("mediapp_token", res.token);
      }
      return res;
    },
    getGoogleUrl: (origin?: string, role?: string) => {
      const params = new URLSearchParams();
      if (origin) params.append("origin", origin);
      if (role) params.append("role", role);
      const q = params.toString() ? `?${params.toString()}` : "";
      return apiFetch<{ status: string; url: string; state: string }>(`/api/auth/google/url${q}`);
    },
    switchRole: (role: "customer" | "pharmacy" | "delivery" | "admin") =>
      apiFetch<{ status: string; message: string; active_role: string; pharmacy_id?: number }>("/api/auth/switch-role", {
        method: "POST",
        body: JSON.stringify({ role }),
      }),
    logout: async () => {
      if (typeof window !== "undefined") {
        localStorage.removeItem("mediapp_token");
      }
      return apiFetch<{ status: string }>("/api/auth/logout", { method: "POST" });
    },
  },

  // Medicines & Discovery
  medicines: {
    search: (params: { q?: string; category?: string; dosage_form?: string; rx?: number; cold_chain?: number | boolean; page?: number; limit?: number }) => {
      const query = new URLSearchParams();
      if (params.q) query.append("q", params.q);
      if (params.category) query.append("category", params.category);
      if (params.dosage_form) query.append("dosage_form", params.dosage_form);
      if (params.rx !== undefined) query.append("rx", params.rx.toString());
      if (params.cold_chain !== undefined) query.append("cold_chain", params.cold_chain ? "1" : "0");
      if (params.page) query.append("page", params.page.toString());
      if (params.limit) query.append("limit", params.limit.toString());
      return apiFetch<{ status: string; medicines: Medicine[]; pagination: { total_count: number; total_pages: number; page: number } }>(
        `/api/medicines?${query.toString()}`
      );
    },
    getById: (id: number) => apiFetch<{ status: string; medicine: Medicine }>(`/api/medicines/${id}`),
    getCategories: () => apiFetch<{ status: string; categories: Array<{ category: string; count: number }> }>("/api/medicines/categories"),
    getDosageForms: () => apiFetch<{ status: string; dosage_forms: string[] }>("/api/medicines/dosage-forms"),
    getGenericAlternatives: (id: number) => apiFetch<GenericAlternative>(`/api/medicines/${id}/generic-alternatives`),
    checkDDI: (medicineIds: number[]) =>
      apiFetch<{ has_interactions: boolean; interactions: Array<{ severity: string; description: string; drugs: string[] }> }>(
        "/api/medicines/check-ddi",
        {
          method: "POST",
          body: JSON.stringify({ medicine_ids: medicineIds }),
        }
      ),
  },

  // Cart
  cart: {
    get: () => apiFetch<CartData>("/api/cart"),
    addItem: (medicine_id: number, quantity = 1) =>
      apiFetch<CartData>("/api/cart/items", {
        method: "POST",
        body: JSON.stringify({ medicine_id, quantity }),
      }),
    updateItem: (cart_item_id: number, quantity: number) =>
      apiFetch<CartData>(`/api/cart/items/${cart_item_id}`, {
        method: "PUT",
        body: JSON.stringify({ quantity }),
      }),
    removeItem: (cart_item_id: number) =>
      apiFetch<CartData>(`/api/cart/items/${cart_item_id}`, {
        method: "DELETE",
      }),
    clear: () => apiFetch<{ status: string }>("/api/cart", { method: "DELETE" }),
  },

  // Prescriptions & OCR
  prescriptions: {
    upload: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiFetch<{ status: string; prescription_id: number; ocr_status: string; detected_medicines?: string[] }>(
        "/api/prescriptions/upload",
        {
          method: "POST",
          body: formData,
        }
      );
    },
    list: (status?: string) =>
      apiFetch<{ status: string; prescriptions: Prescription[] }>(
        `/api/prescriptions${status ? `?status=${status}` : ""}`
      ),
    verify: (id: number, approvedMedicines?: string[], notes?: string) =>
      apiFetch<{ status: string; message: string }>(`/api/prescriptions/${id}/verify`, {
        method: "POST",
        body: JSON.stringify({ decision: "verified", approved_medicines: approvedMedicines, clinical_notes: notes }),
      }),
    reject: (id: number, reason: string) =>
      apiFetch<{ status: string; message: string }>(`/api/prescriptions/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ decision: "rejected", reason, rejection_reason: reason }),
      }),
  },

  // Orders & Lifecycle
  orders: {
    list: () => apiFetch<{ status: string; orders: Order[] }>("/api/orders"),
    getById: (id: number) => apiFetch<{ status: string; order: Order }>(`/api/orders/${id}`),
    create: (payload: { delivery_address: string; prescription_id?: number; payment_method?: string }) =>
      apiFetch<{ status: string; order_id: number; order_number: string; total_amount: number; order?: Order }>("/api/orders", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    cancel: (id: number | string, reason?: string) =>
      apiFetch<{ status: string; message: string; order?: Order }>(`/api/orders/${id}/cancel`, {
        method: "POST",
        body: JSON.stringify({ reason: reason || "Cancelled by customer" }),
      }),
  },

  // Pharmacy Clinical Desk
  pharmacy: {
    getPendingOrders: () => apiFetch<{ status: string; orders: Order[] }>("/api/pharmacy/orders"),
    getOrders: () => apiFetch<{ status: string; orders: Order[] }>("/api/pharmacy/orders"),
    packOrder: (orderId: number | string) =>
      apiFetch<{ status: string }>(`/api/pharmacy/orders/${orderId}/pack`, { method: "POST" }),
    dispatchOrder: (orderId: number | string, coldChainBatch?: string) =>
      apiFetch<{ status: string }>(`/api/pharmacy/orders/${orderId}/dispatch`, {
        method: "POST",
        body: JSON.stringify({ cold_chain_batch: coldChainBatch || "CC-2026-N8" }),
      }),
    getInventory: () =>
      apiFetch<{ status: string; inventory: Array<{ medicine_id: number; name: string; stock_quantity: number; unit_price: number }> }>(
        "/api/pharmacy/inventory"
      ),
  },

  // Delivery Logistics
  delivery: {
    getAvailableRuns: async () => {
      const res = await apiFetch<any>("/api/delivery/available");
      const list = (res.orders || res.available_orders || []) as Order[];
      return { status: res.status || "success", orders: list };
    },
    acceptRun: (orderId: number | string) =>
      apiFetch<{ status: string }>(`/api/delivery/orders/${orderId}/accept`, { method: "POST" }),
    pickup: (orderId: number | string) =>
      apiFetch<{ status: string; message: string }>(`/api/delivery/orders/${orderId}/pickup`, { method: "POST" }),
    markInTransit: (orderId: number | string) =>
      apiFetch<{ status: string; message: string }>(`/api/delivery/orders/${orderId}/in-transit`, { method: "POST" }),
    updateLocation: (latitude: number, longitude: number) =>
      apiFetch<{ status: string; location: { latitude: number; longitude: number } }>("/api/delivery/location", {
        method: "POST",
        body: JSON.stringify({ latitude, longitude }),
      }),
    verifyHandoff: (orderId: number | string, otp: string) =>
      apiFetch<{ status: string; message: string }>(`/api/delivery/orders/${orderId}/verify-otp`, {
        method: "POST",
        body: JSON.stringify({ otp }),
      }),
  },

  // Payment Processing & Gateways
  payments: {
    createOrder: (orderId: number | string) =>
      apiFetch<{ status: string; payment_order: any }>("/api/payments/create-order", {
        method: "POST",
        body: JSON.stringify({ order_id: orderId }),
      }),
    verify: (orderId: number | string, paymentData: any) =>
      apiFetch<{ status: string; message: string }>("/api/payments/verify", {
        method: "POST",
        body: JSON.stringify({ order_id: orderId, ...paymentData }),
      }),
  },

  // AI Clinical Consultation & Emergency Triage
  ai: {
    consult: (query: string) =>
      apiFetch<{ status: string; result: any }>("/api/ai/consult", {
        method: "POST",
        body: JSON.stringify({ query }),
      }),
  },

  // Admin Oversight & Analytics
  admin: {
    getAnalytics: (timeframe?: string) =>
      apiFetch<{
        status: string;
        metrics: {
          total_revenue: number;
          total_orders: number;
          cold_chain_compliance_rate: number;
          avg_fulfillment_time_mins: number;
          generic_savings_total: number;
          low_stock_alerts?: number;
          hourly_fulfillment?: Array<{ hour: string; orders: number; avgMins: number }>;
          category_savings?: Array<{ category: string; savingsPct: number; brandedPrice: number; genericPrice: number }>;
        };
        recent_activity: Array<{ id: number; action: string; timestamp: string; details: string }>;
        low_stock?: Array<{ id: number; name: string; generic_name: string; stock: number; minThreshold: number; pharmacy: string; status: string }>;
        hourly_fulfillment?: Array<{ hour: string; orders: number; avgMins: number }>;
        category_savings?: Array<{ category: string; savingsPct: number; brandedPrice: number; genericPrice: number }>;
      }>(timeframe && timeframe !== "all" ? `/api/admin/analytics?timeframe=${encodeURIComponent(timeframe)}` : "/api/admin/analytics"),
  },
};
