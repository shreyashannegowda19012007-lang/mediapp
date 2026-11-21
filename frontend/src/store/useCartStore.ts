import { create } from "zustand";
import { api, CartData, CartItem } from "@/lib/api";

interface CartState {
  cart: CartData | null;
  isOpen: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setIsOpen: (open: boolean) => void;
  fetchCart: () => Promise<void>;
  addItem: (medicineId: number, quantity?: number) => Promise<void>;
  updateQuantity: (cartItemId: number, quantity: number) => Promise<void>;
  removeItem: (cartItemId: number) => Promise<void>;
  clearCart: () => Promise<void>;
}

export const useCartStore = create<CartState>((set, get) => ({
  cart: null,
  isOpen: false,
  isLoading: false,
  error: null,

  setIsOpen: (open) => set({ isOpen: open }),

  fetchCart: async () => {
    try {
      set({ isLoading: true, error: null });
      const data = await api.cart.get();
      set({ cart: data });
    } catch {
      // Graceful fallback when empty
      set({
        cart: {
          cart_id: 0,
          pharmacy_id: 1,
          pharmacy_name: "Apollo Clinical Hub (Central)",
          items: [],
          pricing: { subtotal: 0, delivery_fee: 0, tax: 0, discount: 0, total: 0 },
          has_prescription_items: false,
        },
      });
    } finally {
      set({ isLoading: false });
    }
  },

  addItem: async (medicineId: number, quantity = 1) => {
    try {
      set({ isLoading: true, error: null });
      await api.cart.addItem(medicineId, quantity);
      const updated = await api.cart.get();
      set({ cart: updated, isOpen: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to add item to cart";
      set({ error: msg });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  updateQuantity: async (cartItemId: number, quantity: number) => {
    try {
      set({ isLoading: true, error: null });
      if (quantity <= 0) {
        await get().removeItem(cartItemId);
        return;
      }
      await api.cart.updateItem(cartItemId, quantity);
      const updated = await api.cart.get();
      set({ cart: updated });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update item";
      set({ error: msg });
    } finally {
      set({ isLoading: false });
    }
  },

  removeItem: async (cartItemId: number) => {
    try {
      set({ isLoading: true, error: null });
      await api.cart.removeItem(cartItemId);
      const updated = await api.cart.get();
      set({ cart: updated });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to remove item";
      set({ error: msg });
    } finally {
      set({ isLoading: false });
    }
  },

  clearCart: async () => {
    try {
      set({ isLoading: true, error: null });
      await api.cart.clear();
      set({
        cart: {
          cart_id: 0,
          pharmacy_id: 1,
          pharmacy_name: "Apollo Clinical Hub (Central)",
          items: [],
          pricing: { subtotal: 0, delivery_fee: 0, tax: 0, discount: 0, total: 0 },
          has_prescription_items: false,
        },
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to clear cart";
      set({ error: msg });
    } finally {
      set({ isLoading: false });
    }
  },
}));
