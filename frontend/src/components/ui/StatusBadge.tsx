import React from "react";
import { CheckCircle2, AlertTriangle, ShieldCheck, ThermometerSnowflake, Sparkles, Clock, Truck } from "lucide-react";
import { clsx } from "clsx";

export type StatusType =
  | "otc"
  | "rx"
  | "cold-chain"
  | "generic-saving"
  | "verified"
  | "pending"
  | "in-transit"
  | "delivered";

interface StatusBadgeProps {
  type: StatusType;
  label?: string;
  size?: "sm" | "md";
  className?: string;
}

export function StatusBadge({ type, label, size = "md", className }: StatusBadgeProps) {
  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs gap-1" : "px-2.5 py-1 text-xs font-semibold gap-1.5";

  switch (type) {
    case "otc":
      return (
        <span
          className={clsx(
            "inline-flex items-center rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-medium",
            sizeClasses,
            className
          )}
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>{label || "OTC - No Rx Required"}</span>
        </span>
      );

    case "rx":
      return (
        <span
          className={clsx(
            "inline-flex items-center rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-800 dark:text-amber-400 font-semibold tracking-wide",
            sizeClasses,
            className
          )}
        >
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>{label || "Prescription (Rx) Required"}</span>
        </span>
      );

    case "cold-chain":
      return (
        <span
          className={clsx(
            "inline-flex items-center rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-800 dark:text-cyan-400 font-medium",
            sizeClasses,
            className
          )}
        >
          <ThermometerSnowflake className="h-3.5 w-3.5" />
          <span>{label || "Cold-Chain (2°C - 8°C)"}</span>
        </span>
      );

    case "generic-saving":
      return (
        <span
          className={clsx(
            "inline-flex items-center rounded-full border border-sky-500/30 bg-sky-500/10 text-sky-800 dark:text-sky-400 font-semibold",
            sizeClasses,
            className
          )}
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>{label || "Bioequivalent Match"}</span>
        </span>
      );

    case "verified":
      return (
        <span
          className={clsx(
            "inline-flex items-center rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-400 font-medium",
            sizeClasses,
            className
          )}
        >
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>{label || "Verified Clinical"}</span>
        </span>
      );

    case "pending":
      return (
        <span
          className={clsx(
            "inline-flex items-center rounded-full border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium",
            sizeClasses,
            className
          )}
        >
          <Clock className="h-3.5 w-3.5" />
          <span>{label || "Under Pharmacist Review"}</span>
        </span>
      );

    case "in-transit":
      return (
        <span
          className={clsx(
            "inline-flex items-center rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-800 dark:text-indigo-400 font-medium",
            sizeClasses,
            className
          )}
        >
          <Truck className="h-3.5 w-3.5" />
          <span>{label || "Out for Delivery"}</span>
        </span>
      );

    case "delivered":
      return (
        <span
          className={clsx(
            "inline-flex items-center rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-400 font-medium",
            sizeClasses,
            className
          )}
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>{label || "Delivered"}</span>
        </span>
      );

    default:
      return null;
  }
}
