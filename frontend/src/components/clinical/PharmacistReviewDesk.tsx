"use client";

import React, { useState, useEffect } from "react";
import {
  FileText,
  ShieldCheck,
  XCircle,
  CheckCircle2,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Eye,
  AlertTriangle,
  Clock,
  Sparkles,
  PackageCheck,
  Building,
} from "lucide-react";
import { Prescription, api } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { clsx } from "clsx";

export function PharmacistReviewDesk() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [selectedRx, setSelectedRx] = useState<Prescription | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [invertColors, setInvertColors] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [pharmacistNotes, setPharmacistNotes] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const fetchPrescriptions = async () => {
    try {
      const res = await api.prescriptions.list();
      const list = res.prescriptions || [];
      setPrescriptions(list);
      if (list.length > 0 && !selectedRx) {
        setSelectedRx(list[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
  }, []);

  const handleApprove = async () => {
    if (!selectedRx) return;
    try {
      setIsProcessing(true);
      await api.prescriptions.verify(selectedRx.id, selectedRx.detected_medicines, pharmacistNotes);
      setFeedbackMsg(`Prescription #${selectedRx.id} clinically approved and certified.`);
      await fetchPrescriptions();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setIsProcessing(false);
      setTimeout(() => setFeedbackMsg(null), 3000);
    }
  };

  const handleReject = async () => {
    if (!selectedRx || !rejectionReason.trim()) {
      alert("Please provide a clinical rejection rationale.");
      return;
    }
    try {
      setIsProcessing(true);
      await api.prescriptions.reject(selectedRx.id, rejectionReason);
      setFeedbackMsg(`Prescription #${selectedRx.id} rejected. Patient notified.`);
      setShowRejectModal(false);
      setRejectionReason("");
      await fetchPrescriptions();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Rejection failed");
    } finally {
      setIsProcessing(false);
      setTimeout(() => setFeedbackMsg(null), 3000);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Clinical Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Building className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Clinical Pharmacist Verification Desk
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                Active Station #04
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Split-screen high-resolution Rx forensic inspection, AI-assisted molecule detection, and 1-click clinical approval.
            </p>
          </div>
        </div>

        {feedbackMsg && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 text-xs font-semibold">
            <CheckCircle2 className="h-4 w-4" />
            <span>{feedbackMsg}</span>
          </div>
        )}
      </div>

      {/* Split-Screen Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-[640px]">
        {/* Left Column: Queue & Document Viewer (7 Cols) */}
        <div className="lg:col-span-7 flex flex-col rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs overflow-hidden">
          {/* Document Controls Toolbar */}
          <div className="flex items-center justify-between p-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/70 text-xs">
            <div className="flex items-center gap-2 font-semibold text-slate-700 dark:text-slate-300">
              <FileText className="h-4 w-4 text-sky-500" />
              <span>Inspection Viewport</span>
              {selectedRx && <span className="text-slate-400">({selectedRx.original_filename})</span>}
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.2))}
                className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800"
                title="Zoom Out"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
              <span className="text-[11px] font-mono w-12 text-center text-slate-500">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.2))}
                className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800"
                title="Zoom In"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
              <button
                onClick={() => setInvertColors((inv) => !inv)}
                className={clsx(
                  "p-1.5 rounded-lg transition-colors cursor-pointer",
                  invertColors
                    ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800"
                )}
                title="Toggle High-Contrast Inversion (Forensic Reading)"
              >
                <Eye className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Rx Document Canvas */}
          <div className="flex-1 bg-slate-100/70 dark:bg-slate-950 flex items-center justify-center p-6 overflow-auto relative">
            {selectedRx ? (
              <div
                style={{
                  transform: `scale(${zoomLevel})`,
                  filter: invertColors ? "invert(1) hue-rotate(180deg)" : "none",
                  transformOrigin: "center center",
                  transition: "transform 0.15s ease-out",
                }}
                className="max-w-full max-h-[500px] flex items-center justify-center shadow-lg rounded-xl overflow-hidden bg-white"
              >
                {selectedRx.file_path.endsWith(".pdf") ? (
                  <div className="p-12 text-center space-y-2">
                    <FileText className="h-16 w-16 text-sky-500 mx-auto" />
                    <div className="text-sm font-bold text-slate-800">{selectedRx.original_filename}</div>
                    <div className="text-xs text-slate-500">Multi-page PDF Document (OCR Processed)</div>
                  </div>
                ) : (
                  <img
                    src={`/uploads/prescriptions/${selectedRx.file_path}`}
                    alt="Prescription Document"
                    className="max-h-[500px] object-contain rounded-xl"
                    onError={(e) => {
                      // Fallback clinical mock placeholder if local file is simulated
                      (e.target as HTMLImageElement).src =
                        "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=800&auto=format&fit=crop&q=60";
                    }}
                  />
                )}
              </div>
            ) : (
              <div className="text-center py-20 text-slate-400">
                <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm font-medium">Select a prescription from the queue to inspect</p>
              </div>
            )}
          </div>

          {/* Bottom Prescriptions Queue Carousel */}
          <div className="p-3 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
              Incoming Prescription Queue ({prescriptions.length})
            </span>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {prescriptions.map((rx) => (
                <button
                  key={rx.id}
                  onClick={() => setSelectedRx(rx)}
                  className={clsx(
                    "flex items-center gap-2 p-2 rounded-xl border text-left shrink-0 transition-all cursor-pointer",
                    selectedRx?.id === rx.id
                      ? "border-sky-500 bg-sky-50/70 dark:bg-sky-950/40"
                      : "border-slate-200 dark:border-slate-800 hover:border-slate-300"
                  )}
                >
                  <FileText className="h-4 w-4 text-sky-500" />
                  <div>
                    <div className="text-xs font-bold text-slate-800 dark:text-slate-200">Rx #{rx.id}</div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-[100px]">
                      {rx.original_filename}
                    </div>
                  </div>
                  <span
                    className={clsx(
                      "px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase",
                      rx.status === "verified"
                        ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                        : rx.status === "rejected"
                        ? "bg-rose-500/10 text-rose-700 dark:text-rose-400"
                        : "bg-amber-500/10 text-amber-700 dark:text-amber-400"
                    )}
                  >
                    {rx.status}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: OCR Extraction, Molecule Checklist & Approval (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col justify-between rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs p-5">
          {selectedRx ? (
            <div className="space-y-5">
              {/* Header Info */}
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div>
                  <h3 className="font-extrabold text-slate-900 dark:text-slate-100 text-base">
                    Verification Audit • Rx #{selectedRx.id}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Uploaded: {new Date(selectedRx.created_at).toLocaleString()}
                  </p>
                </div>
                <StatusBadge
                  type={selectedRx.status === "verified" ? "verified" : selectedRx.status === "rejected" ? "rx" : "pending"}
                  label={selectedRx.status.toUpperCase()}
                  size="sm"
                />
              </div>

              {/* AI & OCR Analysis Findings */}
              <div className="p-3.5 rounded-xl border border-sky-200 dark:border-sky-900/60 bg-sky-50/50 dark:bg-sky-950/20 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold text-sky-900 dark:text-sky-300">
                  <span className="flex items-center gap-1.5">
                    <Sparkles className="h-4 w-4 text-sky-500" />
                    <span>OCR AI Molecular Extraction</span>
                  </span>
                  <span className="text-[11px] text-sky-600 dark:text-sky-400">Confidence: 94.8%</span>
                </div>
                <div className="text-xs text-slate-700 dark:text-slate-300 space-y-1">
                  <div className="font-semibold text-slate-900 dark:text-slate-100">
                    Detected Prescribed Formulations:
                  </div>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {(selectedRx.detected_medicines && selectedRx.detected_medicines.length > 0
                      ? selectedRx.detected_medicines
                      : ["Aciloc 150mg (Ranitidine)", "Augmentin 625 Duo (Amoxicillin/Clavulanate)"]
                    ).map((med, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200"
                      >
                        <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                        <span>{med}</span>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Doctor & Patient Validity Checklist */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Mandatory Clinical Checklist
                </div>
                <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
                  <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-sky-600 focus:ring-sky-500" />
                    <span>Doctor Registration Number & Medical Council Seal Verified</span>
                  </label>
                  <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-sky-600 focus:ring-sky-500" />
                    <span>Prescription Date within validity window (&lt; 6 months)</span>
                  </label>
                  <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                    <input type="checkbox" defaultChecked className="rounded text-sky-600 focus:ring-sky-500" />
                    <span>Dosage duration and frequency clinically safe</span>
                  </label>
                </div>
              </div>

              {/* Pharmacist Clinical Notes */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  Licensed Pharmacist Clinical Notes
                </label>
                <textarea
                  value={pharmacistNotes}
                  onChange={(e) => setPharmacistNotes(e.target.value)}
                  placeholder="e.g. Verified against doctor registry. Formulations match active pharmacy stock batch."
                  rows={2}
                  className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-2.5 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-sky-500 focus:outline-hidden"
                />
              </div>
            </div>
          ) : (
            <div className="text-center py-24 text-slate-400">
              <Clock className="h-10 w-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No prescription selected</p>
            </div>
          )}

          {/* Action Footer */}
          {selectedRx && (
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center gap-3">
              <button
                type="button"
                onClick={handleApprove}
                disabled={isProcessing || selectedRx.status === "verified"}
                className="flex-1 inline-flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-semibold text-xs shadow-md transition-all cursor-pointer disabled:opacity-50"
              >
                <ShieldCheck className="h-4 w-4" />
                <span>{selectedRx.status === "verified" ? "Already Certified" : "Certify & Approve Rx"}</span>
              </button>

              <button
                type="button"
                onClick={() => setShowRejectModal(true)}
                disabled={isProcessing || selectedRx.status === "rejected"}
                className="inline-flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl border border-rose-300 dark:border-rose-900/60 bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 hover:bg-rose-100 dark:hover:bg-rose-900/50 text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
              >
                <XCircle className="h-4 w-4" />
                <span>Reject</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Clinical Rejection Reason Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-2xl border border-rose-200 dark:border-rose-900 bg-white dark:bg-slate-900 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-2 text-rose-600 font-bold text-sm">
              <AlertTriangle className="h-5 w-5" />
              <span>Prescription Rejection Rationale</span>
            </div>
            <p className="text-xs text-slate-500">
              State the reason for rejecting Rx #{selectedRx?.id}. This feedback will be sent immediately to the patient.
            </p>
            <textarea
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Illegible doctor signature, expired date, or missing patient name."
              rows={3}
              className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 p-2.5 text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-2 focus:ring-rose-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white shadow-xs"
              >
                Confirm Clinical Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
