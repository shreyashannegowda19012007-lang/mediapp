"use client";

import React, { useState } from "react";
import { X, Trash2, Plus, Minus, ShieldCheck, AlertTriangle, ArrowRight, ShoppingBag } from "lucide-react";
import { useCartStore } from "@/store/useCartStore";
import { api } from "@/lib/api";

interface CartDrawerProps {
  onOrderPlaced?: (orderId: number) => void;
}

export function CartDrawer({ onOrderPlaced }: CartDrawerProps) {
  const { cart, isOpen, setIsOpen, updateQuantity, removeItem, clearCart, fetchCart } = useCartStore();
  const [address, setAddress] = useState("Flat 402, Green Glen Layout, Bellandur, Bengaluru 560103");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState<string | null>(null);

  if (!isOpen) return null;

  const items = cart?.items || [];
  const pricing = cart?.pricing || { subtotal: 0, delivery_fee: 40, tax: 0, discount: 0, total: 40 };
  const hasRx = cart?.has_prescription_items || false;

  const handleCheckout = async () => {
    try {
      setIsSubmitting(true);
      const res = await api.orders.create({
        delivery_address: address,
        payment_method: "COD",
      });
      setOrderSuccess(res.order_number);
      await clearCart();
      if (onOrderPlaced) onOrderPlaced(res.order_id);
      setTimeout(() => {
        setOrderSuccess(null);
        setIsOpen(false);
      }, 2500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Checkout failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={() => setIsOpen(false)}
        className="absolute inset-0 bg-slate-950/60 backdrop-blur-xs transition-opacity"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col justify-between">
          {/* Header */}
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-400">
                <ShoppingBag className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Prescription Cart</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {cart?.pharmacy_name || "Apollo Clinical Hub"}
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {orderSuccess ? (
              <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-center space-y-3 my-12">
                <ShieldCheck className="h-12 w-12 text-emerald-500 mx-auto" />
                <h3 className="text-lg font-bold text-emerald-800 dark:text-emerald-300">
                  Order Successfully Dispatched!
                </h3>
                <p className="text-xs text-emerald-700 dark:text-emerald-400">
                  Order Reference: <strong>{orderSuccess}</strong>. Pharmacist review and cold-chain pack scheduled.
                </p>
              </div>
            ) : items.length === 0 ? (
              <div className="text-center py-16 space-y-3">
                <ShoppingBag className="h-12 w-12 text-slate-300 dark:text-slate-700 mx-auto" />
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
                  Your prescription cart is currently empty.
                </p>
              </div>
            ) : (
              <>
                {/* Rx Warning Notice */}
                {hasRx && (
                  <div className="flex items-start gap-2.5 p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/10 text-xs text-amber-800 dark:text-amber-300">
                    <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" />
                    <div>
                      <strong className="block font-semibold">Prescription (Rx) Required</strong>
                      Contains prescription medicines. A valid doctor's prescription must be uploaded or verified by our clinical pharmacist before delivery handoff.
                    </div>
                  </div>
                )}

                {/* Items List */}
                <div className="space-y-3">
                  {items.map((item) => (
                    <div
                      key={item.cart_item_id}
                      className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 flex items-start justify-between gap-3"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm text-slate-900 dark:text-slate-100 truncate">
                          {item.name}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                          {item.generic_name} • {item.dosage_form}
                        </div>
                        <div className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-1">
                          ₹{item.unit_price.toFixed(2)} × {item.quantity} = ₹{item.line_total.toFixed(2)}
                        </div>
                      </div>

                      {/* Quantity Controls */}
                      <div className="flex items-center gap-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-1">
                        <button
                          onClick={() => updateQuantity(item.cart_item_id, item.quantity - 1)}
                          className="p-1 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                        >
                          <Minus className="h-3 w-3" />
                        </button>
                        <span className="w-5 text-center text-xs font-bold">{item.quantity}</span>
                        <button
                          onClick={() => updateQuantity(item.cart_item_id, item.quantity + 1)}
                          className="p-1 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                        >
                          <Plus className="h-3 w-3" />
                        </button>
                      </div>

                      <button
                        onClick={() => removeItem(item.cart_item_id)}
                        className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Delivery Address Input */}
                <div className="space-y-1.5 pt-2">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Clinical Delivery Address
                  </label>
                  <textarea
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    rows={2}
                    className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-2.5 text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-2 focus:ring-sky-500"
                  />
                </div>
              </>
            )}
          </div>

          {/* Footer & Totals */}
          {items.length > 0 && !orderSuccess && (
            <div className="p-6 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/60 space-y-3">
              <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
                <div className="flex justify-between">
                  <span>Subtotal ({items.length} items)</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    ₹{pricing.subtotal.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Cold-Chain Express Delivery</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {pricing.delivery_fee === 0 ? "FREE" : `₹${pricing.delivery_fee.toFixed(2)}`}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Estimated Taxes (GST 5%)</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    ₹{pricing.tax.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between text-sm font-extrabold text-slate-900 dark:text-slate-100 pt-2 border-t border-slate-200 dark:border-slate-800">
                  <span>Total Amount</span>
                  <span>₹{pricing.total.toFixed(2)}</span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleCheckout}
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-sky-600 hover:bg-sky-700 active:scale-95 text-white font-semibold text-sm shadow-md transition-all cursor-pointer disabled:opacity-50"
              >
                <span>{isSubmitting ? "Placing Clinical Order..." : "Confirm & Place Order"}</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
