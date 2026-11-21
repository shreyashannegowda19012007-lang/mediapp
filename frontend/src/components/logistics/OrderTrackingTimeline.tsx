"use client";

import React, { useState, useEffect } from "react";
import {
  Truck,
  CheckCircle2,
  Clock,
  ThermometerSnowflake,
  ShieldCheck,
  Package,
  KeyRound,
  MapPin,
  Phone,
  AlertCircle,
  Activity,
  ArrowRight,
} from "lucide-react";
import { Order, api } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { DeliveryRunsBoard } from "@/components/logistics/DeliveryRunsBoard";
import { useAuthStore } from "@/store/useAuthStore";
import { clsx } from "clsx";

export function OrderTrackingTimeline() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [otpInput, setOtpInput] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const { activeRole } = useAuthStore();

  const handleCancelOrder = async () => {
    if (!selectedOrder) return;
    if (!confirm("Are you sure you wish to cancel this clinical order? Reserved pharmacy stock will be released.")) {
      return;
    }
    try {
      setIsCancelling(true);
      await api.orders.cancel(selectedOrder.id, "Customer requested cancellation");
      setActionSuccess("Order has been cancelled and pharmacy stock restored.");
      await reloadOrders();
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to cancel order");
    } finally {
      setIsCancelling(false);
    }
  };

  const reloadOrders = async () => {
    try {
      const res = await api.orders.list();
      const list = res.orders || [];
      setOrders(list);
      if (list.length > 0) {
        setSelectedOrder((prev) => (prev ? list.find((o) => o.id === prev.id) || list[0] : list[0]));
      } else {
        setSelectedOrder(null);
      }
    } catch {
      setOrders([]);
      setSelectedOrder(null);
    }
  };

  useEffect(() => {
    let ignore = false;
    api.orders
      .list()
      .then((res) => {
        if (!ignore) {
          const list = res.orders || [];
          setOrders(list);
          if (list.length > 0) {
            setSelectedOrder((prev) => (prev ? list.find((o) => o.id === prev.id) || list[0] : list[0]));
          } else {
            setSelectedOrder(null);
          }
        }
      })
      .catch(() => {
        if (!ignore) {
          setOrders([]);
          setSelectedOrder(null);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  const milestones = [
    { key: "placed", label: "Order Placed", desc: "Digital clinical prescription logged" },
    { key: "verified", label: "Rx Clinically Approved", desc: "Checked by licensed pharmacist" },
    { key: "packed", label: "Cold-Chain Sealed", desc: "Batch packaging under thermal control" },
    { key: "out_for_delivery", label: "Out for Express Transit", desc: "Dispatched with IoT temperature monitor" },
    { key: "delivered", label: "Delivered & Verified", desc: "Handed over with patient OTP" },
  ];

  const getStepIndex = (status?: string) => {
    switch ((status || "").toLowerCase()) {
      case "placed":
      case "pending":
        return 0;
      case "approved":
      case "verified":
        return 1;
      case "packed":
      case "ready_for_pickup":
        return 2;
      case "out_for_delivery":
      case "in_transit":
      case "assigned":
        return 3;
      case "delivered":
      case "completed":
        return 4;
      default:
        return 0;
    }
  };

  const handleVerifyOtp = async () => {
    if (!selectedOrder || !otpInput.trim()) {
      alert("Please enter patient OTP.");
      return;
    }
    try {
      setIsVerifying(true);
      await api.delivery.verifyHandoff(selectedOrder.id, otpInput);
      setActionSuccess("Patient OTP Verified! Cold-chain delivery marked complete.");
      setOtpInput("");
      await reloadOrders();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "OTP Verification failed");
    } finally {
      setIsVerifying(false);
      setTimeout(() => setActionSuccess(null), 3000);
    }
  };

  const currentStep = selectedOrder ? getStepIndex(selectedOrder.status || selectedOrder.order_status) : 0;

  return (
    <div className="space-y-5">
      {/* Top Clinical Logistics Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-400">
            <Truck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Order Tracking & Logistics
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 border border-cyan-500/20">
                Live
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Real-time delivery progress, cold-chain temperature status, and OTP verification.
            </p>
          </div>
        </div>

        {actionSuccess && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 text-xs font-semibold">
            <CheckCircle2 className="h-4 w-4" />
            <span>{actionSuccess}</span>
          </div>
        )}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Orders Queue (4 Cols) */}
        <div className="lg:col-span-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-100 dark:border-slate-800">
            <span>Recent Clinical Orders</span>
            <span>{orders.length} Records</span>
          </div>

          <div className="space-y-2 max-h-[580px] overflow-y-auto pr-1">
            {orders.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Truck className="h-8 w-8 mx-auto mb-2 opacity-40" />
                <p className="text-xs font-medium">No active clinical orders</p>
                <p className="text-[10px] text-slate-400 mt-1">Orders placed from the catalogue will appear here.</p>
              </div>
            ) : (
              orders.map((o) => (
                <button
                  key={o.id}
                  onClick={() => setSelectedOrder(o)}
                  className={clsx(
                    "w-full p-3.5 rounded-xl border text-left transition-all cursor-pointer",
                    selectedOrder?.id === o.id
                      ? "border-sky-500 bg-sky-50/70 dark:bg-sky-950/40 shadow-xs"
                      : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                      {o.order_number}
                    </span>
                    <span className="font-mono text-xs font-semibold text-slate-700 dark:text-slate-300">
                      ₹{o.total_amount?.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">
                    {o.delivery_address}
                  </div>
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 text-[11px]">
                    <span className="text-slate-400">{new Date(o.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    <span className="capitalize font-semibold text-sky-600 dark:text-sky-400">
                      {(o.status || o.order_status || "PLACED").replace(/_/g, " ")}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Visual Timeline & Cold-Chain Badge (8 Cols) */}
        <div className="lg:col-span-8 space-y-5">
          {selectedOrder ? (
            <>
              {/* Cold-Chain IoT Telemetry Card */}
              <div className="p-5 rounded-2xl border border-cyan-200 dark:border-cyan-900/60 bg-gradient-to-r from-cyan-500/10 via-sky-500/5 to-transparent shadow-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-cyan-500/20 text-cyan-600 dark:text-cyan-300">
                      <ThermometerSnowflake className="h-6 w-6" />
                    </div>
                    <div>
                      <div className="text-xs font-bold uppercase tracking-wider text-cyan-800 dark:text-cyan-400">
                        Cold-Chain Active Guarantee
                      </div>
                      <div className="text-base font-extrabold text-slate-900 dark:text-slate-100">
                        Insulated Thermal Case #CC-842 • 4.2°C Nominal
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        Safe Operating Range: <strong>2.0°C to 8.0°C</strong>. Continuous Bluetooth IoT telemetry.
                      </div>
                    </div>
                  </div>

                  <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 text-xs font-bold">
                    <ShieldCheck className="h-4 w-4" />
                    <span>Integrity Verified</span>
                  </div>
                </div>
              </div>

              {/* Patient Delivery Handover OTP Card */}
              {selectedOrder.delivery_otp && (
                <div className="p-4 rounded-2xl border border-sky-200 dark:border-sky-900 bg-sky-50/70 dark:bg-sky-950/30 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-sky-500/20 text-sky-600 dark:text-sky-300">
                      <KeyRound className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-xs font-bold uppercase tracking-wider text-sky-800 dark:text-sky-300">
                        Patient Handover Security OTP
                      </div>
                      <div className="text-xs text-slate-600 dark:text-slate-400">
                        Provide this 6-digit verification code to your courier upon doorstep arrival to complete handoff.
                      </div>
                    </div>
                  </div>
                  <div className="px-5 py-2 rounded-xl bg-white dark:bg-slate-900 border border-sky-300 dark:border-sky-800 shadow-xs text-center">
                    <span className="font-mono text-xl font-extrabold tracking-widest text-sky-600 dark:text-sky-400">
                      {selectedOrder.delivery_otp}
                    </span>
                  </div>
                </div>
              )}

              {/* Step-by-Step Visual Timeline */}
              <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs space-y-6">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                  <div>
                    <h3 className="font-extrabold text-slate-900 dark:text-slate-100 text-base">
                      Fulfillment Milestone Progression
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Tracking order: <strong>{selectedOrder.order_number}</strong>
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      Est. Delivery: 45 Min Doorstep
                    </span>
                    {["PLACED", "AWAITING_PRESCRIPTION"].includes(
                      (selectedOrder.status || selectedOrder.order_status || "").toUpperCase()
                    ) && (
                      <button
                        type="button"
                        onClick={handleCancelOrder}
                        disabled={isCancelling}
                        aria-label="Cancel this order"
                        className="px-3 py-1.5 rounded-xl border border-rose-300 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-900/40 text-xs font-bold transition-all cursor-pointer disabled:opacity-50"
                      >
                        {isCancelling ? "Cancelling..." : "Cancel Order"}
                      </button>
                    )}
                  </div>
                </div>

                {/* Milestone Stepper */}
                <div className="space-y-4">
                  {milestones.map((m, idx) => {
                    const isDone = idx < currentStep;
                    const isCurrent = idx === currentStep;

                    return (
                      <div key={m.key} className="flex items-start gap-4 relative">
                        {/* Vertical line connecting nodes */}
                        {idx < milestones.length - 1 && (
                          <div
                            className={clsx(
                              "absolute left-4 top-8 bottom-0 w-0.5 -ml-px",
                              isDone ? "bg-emerald-500" : "bg-slate-200 dark:bg-slate-800"
                            )}
                          />
                        )}

                        {/* Milestone Node */}
                        <div
                          className={clsx(
                            "h-8 w-8 rounded-full flex items-center justify-center shrink-0 z-10 font-bold text-xs transition-all",
                            isDone
                              ? "bg-emerald-500 text-white shadow-xs"
                              : isCurrent
                              ? "bg-sky-600 text-white ring-4 ring-sky-500/20 shadow-xs"
                              : "bg-slate-100 dark:bg-slate-800 text-slate-400 border border-slate-200 dark:border-slate-700"
                          )}
                        >
                          {isDone ? <CheckCircle2 className="h-4 w-4" /> : idx + 1}
                        </div>

                        {/* Milestone Description */}
                        <div className="flex-1 pt-0.5">
                          <div
                            className={clsx(
                              "text-sm font-bold",
                              isCurrent
                                ? "text-sky-600 dark:text-sky-400"
                                : isDone
                                ? "text-slate-900 dark:text-slate-100"
                                : "text-slate-400"
                            )}
                          >
                            {m.label}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400">{m.desc}</div>
                        </div>

                        {isCurrent && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20">
                            Current Stage
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Delivery Agent & OTP Handoff Section */}
              <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Assigned Delivery Agent
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-slate-700 dark:text-slate-300">
                      MK
                    </div>
                    <div>
                      <div className="font-bold text-sm text-slate-900 dark:text-slate-100">
                        {selectedOrder.delivery_agent_name || "Manoj Kumar (Certified Cold-Chain Fleet)"}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        <span>+91 98450 12849 • Thermal Van KA-05-MH-2914</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Patient OTP Verification Box */}
                <div className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 space-y-2">
                  <div className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <KeyRound className="h-3.5 w-3.5 text-sky-500" />
                    <span>Patient Handover OTP Verification</span>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      maxLength={6}
                      value={otpInput}
                      onChange={(e) => setOtpInput(e.target.value)}
                      placeholder="Enter 4-digit OTP (e.g. 4821)"
                      className="flex-1 text-xs rounded-lg border border-slate-200 dark:border-slate-800 px-3 py-2 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-mono tracking-widest text-center"
                    />
                    <button
                      type="button"
                      onClick={handleVerifyOtp}
                      disabled={isVerifying || !otpInput.trim()}
                      className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
                    >
                      {isVerifying ? "Verifying..." : "Verify OTP"}
                    </button>
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Patient receives OTP via SMS/App upon clinical dispatch to prevent medication diversion.
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-24 text-slate-400 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800">
              <Truck className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm font-medium">No Active Deliveries Selected</p>
              <p className="text-xs text-slate-400 mt-1">Select an order from the list or explore the medicine catalogue to place an order.</p>
            </div>
          )}
        </div>
      </div>

      {/* Rider Available Runs Board (shown for delivery riders and admins) */}
      {(activeRole === "delivery" || activeRole === "admin") && (
        <DeliveryRunsBoard onRunClaimed={reloadOrders} />
      )}
    </div>
  );
}
