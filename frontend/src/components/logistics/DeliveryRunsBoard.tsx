"use client";

import React, { useState, useEffect } from "react";
import { Truck, Package, MapPin, CheckCircle2, ThermometerSnowflake, ShieldCheck, RefreshCw, AlertCircle } from "lucide-react";
import { Order, api } from "@/lib/api";

interface DeliveryRunsBoardProps {
  onRunClaimed?: () => void;
}

export function DeliveryRunsBoard({ onRunClaimed }: DeliveryRunsBoardProps) {
  const [runs, setRuns] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [claimingId, setClaimingId] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchRuns = async () => {
    try {
      setLoading(true);
      const res = await api.delivery.getAvailableRuns();
      setRuns(res.orders || []);
    } catch {
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleAcceptRun = async (orderId: number) => {
    try {
      setClaimingId(orderId);
      await api.delivery.acceptRun(orderId);
      setSuccessMessage(`Delivery run for Order #${orderId} claimed successfully.`);
      await fetchRuns();
      if (onRunClaimed) onRunClaimed();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to claim delivery run.");
    } finally {
      setClaimingId(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    }
  };

  return (
    <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-400">
            <Truck className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Available Courier Transit Runs
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 border border-cyan-500/20">
                {runs.length} Available
              </span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Claim ready cold-chain packages dispatched from partner clinical pharmacies.
            </p>
          </div>
        </div>

        <button
          onClick={fetchRuns}
          disabled={loading}
          type="button"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all cursor-pointer"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {successMessage && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800 dark:text-emerald-300 font-semibold">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span>{successMessage}</span>
        </div>
      )}

      {loading ? (
        <div className="py-8 text-center text-xs text-slate-400">Loading transit queue...</div>
      ) : runs.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500 dark:text-slate-400">
          No unassigned runs pending at this moment. All active dispatches are in transit.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {runs.map((run) => (
            <div
              key={run.id}
              className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 flex flex-col justify-between space-y-3"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-900 dark:text-slate-100">
                    {run.order_number || `ORD-#${run.id}`}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20">
                    {run.status || run.order_status || "Packed"}
                  </span>
                </div>

                <div className="flex items-start gap-1.5 text-xs text-slate-600 dark:text-slate-400">
                  <MapPin className="h-3.5 w-3.5 shrink-0 mt-0.5 text-sky-500" />
                  <span className="line-clamp-2">{run.delivery_address || "Bengaluru Express Delivery Hub"}</span>
                </div>

                <div className="flex items-center gap-2 pt-1 text-[11px] text-slate-500">
                  <span className="inline-flex items-center gap-1 text-cyan-600 dark:text-cyan-400 font-semibold">
                    <ThermometerSnowflake className="h-3 w-3" />
                    2°C - 8°C Monitored
                  </span>
                  <span>•</span>
                  <span>₹{run.total_amount?.toFixed(2)}</span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleAcceptRun(run.id)}
                disabled={claimingId === run.id}
                className="w-full flex items-center justify-center gap-1.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-700 active:scale-95 text-white font-semibold text-xs transition-all cursor-pointer disabled:opacity-50"
              >
                <Package className="h-3.5 w-3.5" />
                <span>{claimingId === run.id ? "Claiming..." : "Accept Delivery Run"}</span>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
