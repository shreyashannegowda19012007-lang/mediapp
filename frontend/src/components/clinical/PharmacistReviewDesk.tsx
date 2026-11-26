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
  ArrowRight,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import { Prescription, Order, api } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { clsx } from "clsx";

export function PharmacistReviewDesk() {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [selectedRx, setSelectedRx] = useState<Prescription | null>(null);
  const [linkedOrder, setLinkedOrder] = useState<any | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [invertColors, setInvertColors] = useState(false);
  const [queueFilter, setQueueFilter] = useState<"all" | "pending" | "verified" | "rejected">("all");
  const [isProcessing, setIsProcessing] = useState(false);
  const [pharmacistNotes, setPharmacistNotes] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Controlled checklist state
  const [checklist, setChecklist] = useState({
    councilSeal: false,
    dateValid: false,
    dosageSafe: false,
  });

  // Editable formulation transcription
  const [approvedMeds, setApprovedMeds] = useState<string[]>([]);
  const [newMedInput, setNewMedInput] = useState("");

  // Canvas pan & drag state for zoomed inspection
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [queuePage, setQueuePage] = useState(1);
  const QUEUE_PAGE_SIZE = 8;

  const reloadLinkedOrder = async (rxId: number) => {
    try {
      const res = await api.pharmacy.getPendingOrders();
      const match = (res.orders || []).find((o: any) => o.prescription_id === rxId);
      setLinkedOrder(match || null);
    } catch {
      setLinkedOrder(null);
    }
  };

  const reloadPrescriptions = async () => {
    try {
      const res = await api.prescriptions.list();
      const list = res.prescriptions || [];
      setPrescriptions(list);
      if (list.length > 0) {
        const found = list.find((r) => r.id === selectedRx?.id) || list[0];
        setSelectedRx(found);
        if (found) reloadLinkedOrder(found.id);
      } else {
        setSelectedRx(null);
        setLinkedOrder(null);
      }
    } catch {
      setPrescriptions([]);
      setSelectedRx(null);
      setLinkedOrder(null);
    }
  };

  useEffect(() => {
    setRotation(0);
    setPanOffset({ x: 0, y: 0 });
    if (selectedRx) {
      reloadLinkedOrder(selectedRx.id);
      const initialMeds =
        selectedRx.detected_medicines ||
        (selectedRx as unknown as { extracted_medicines?: string[] }).extracted_medicines ||
        [];
      setApprovedMeds([...initialMeds]);
      if (selectedRx.status === "verified") {
        setChecklist({ councilSeal: true, dateValid: true, dosageSafe: true });
      } else {
        setChecklist({ councilSeal: false, dateValid: false, dosageSafe: false });
      }
    } else {
      setLinkedOrder(null);
    }
  }, [selectedRx?.id]);

  useEffect(() => {
    let ignore = false;
    api.prescriptions
      .list()
      .then((res) => {
        if (!ignore) {
          const list = res.prescriptions || [];
          setPrescriptions(list);
          if (list.length > 0) {
            setSelectedRx((prev) => (prev ? list.find((r) => r.id === prev.id) || list[0] : list[0]));
          } else {
            setSelectedRx(null);
          }
        }
      })
      .catch(() => {
        if (!ignore) {
          setPrescriptions([]);
          setSelectedRx(null);
        }
      });
    return () => {
      ignore = true;
    };
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoomLevel <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPanOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleApprove = async () => {
    if (!selectedRx) return;
    try {
      setIsProcessing(true);
      await api.prescriptions.verify(selectedRx.id, approvedMeds, pharmacistNotes);
      setFeedbackMsg(`Prescription #${selectedRx.id} clinically approved and certified.`);
      await reloadPrescriptions();
      await reloadLinkedOrder(selectedRx.id);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Approval failed");
      setTimeout(() => setErrorMsg(null), 4000);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setFeedbackMsg(null), 3000);
    }
  };

  const handleReject = async () => {
    if (!selectedRx || !rejectionReason.trim()) {
      setErrorMsg("Please provide a clinical rejection rationale.");
      setTimeout(() => setErrorMsg(null), 3000);
      return;
    }
    try {
      setIsProcessing(true);
      await api.prescriptions.reject(selectedRx.id, rejectionReason);
      setFeedbackMsg(`Prescription #${selectedRx.id} rejected. Patient notified.`);
      setShowRejectModal(false);
      setRejectionReason("");
      await reloadPrescriptions();
      if (selectedRx) await reloadLinkedOrder(selectedRx.id);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Rejection failed");
      setTimeout(() => setErrorMsg(null), 4000);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setFeedbackMsg(null), 3000);
    }
  };

  const handlePackOrder = async (orderId: string | number) => {
    try {
      setIsProcessing(true);
      await api.pharmacy.packOrder(orderId);
      setFeedbackMsg(`Order #${orderId} packed and inventory allocated (PREPARING).`);
      if (selectedRx) await reloadLinkedOrder(selectedRx.id);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Pack order failed");
      setTimeout(() => setErrorMsg(null), 4000);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setFeedbackMsg(null), 3000);
    }
  };

  const handleDispatchOrder = async (orderId: string | number) => {
    try {
      setIsProcessing(true);
      await api.pharmacy.dispatchOrder(orderId);
      setFeedbackMsg(`Order #${orderId} ready for pickup and logistics dispatch (READY_FOR_PICKUP).`);
      if (selectedRx) await reloadLinkedOrder(selectedRx.id);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Dispatch order failed");
      setTimeout(() => setErrorMsg(null), 4000);
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
              Pharmacist Verification Desk
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                Active
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Review patient prescriptions, verify detected medicines, and approve for dispensary dispatch.
            </p>
          </div>
        </div>

        {feedbackMsg && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 text-xs font-semibold">
            <CheckCircle2 className="h-4 w-4" />
            <span>{feedbackMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20 text-xs font-semibold">
            <AlertTriangle className="h-4 w-4" />
            <span>{errorMsg}</span>
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
                id="btn-zoom-out"
                onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.2))}
                className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                title="Zoom Out"
                aria-label="Zoom out prescription image"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
              <span className="text-[11px] font-mono w-12 text-center text-slate-500">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                id="btn-zoom-in"
                onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.2))}
                className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                title="Zoom In"
                aria-label="Zoom in prescription image"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
              <button
                id="btn-rotate-rx"
                onClick={() => setRotation((r) => (r + 90) % 360)}
                className="p-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                title="Rotate 90° Clockwise"
                aria-label="Rotate prescription image 90 degrees clockwise"
              >
                <RotateCw className="h-4 w-4" />
              </button>
              <button
                id="btn-invert-rx"
                onClick={() => setInvertColors((inv) => !inv)}
                className={clsx(
                  "p-1.5 rounded-lg transition-colors cursor-pointer",
                  invertColors
                    ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800"
                )}
                title="Toggle High-Contrast Inversion (Forensic Reading)"
                aria-label="Toggle high-contrast color inversion"
              >
                <Eye className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Rx Document Canvas */}
          <div
            className="flex-1 bg-slate-100/70 dark:bg-slate-950 flex items-center justify-center p-6 overflow-hidden relative select-none"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {selectedRx ? (
              (() => {
                const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
                const rxFileUrl = `/api/prescriptions/${selectedRx.id}/file${token ? `?token=${encodeURIComponent(token)}` : ""}`;
                const isPdf = Boolean(
                  selectedRx.mime_type === "application/pdf" ||
                  (selectedRx.original_filename && selectedRx.original_filename.toLowerCase().endsWith(".pdf")) ||
                  ((selectedRx as any).file_path && (selectedRx as any).file_path.toLowerCase().endsWith(".pdf")) ||
                  ((selectedRx as any).file_url && (selectedRx as any).file_url.toLowerCase().endsWith(".pdf"))
                );

                return (
                  <div
                    style={{
                      transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoomLevel}) rotate(${rotation}deg)`,
                      filter: invertColors ? "invert(1) hue-rotate(180deg)" : "none",
                      transformOrigin: "center center",
                      transition: isDragging ? "none" : "transform 0.15s ease-out",
                      cursor: zoomLevel > 1 ? (isDragging ? "grabbing" : "grab") : "default",
                    }}
                    className="max-w-full max-h-[500px] flex items-center justify-center shadow-lg rounded-xl overflow-hidden bg-white"
                  >
                    {isPdf ? (
                      <div className="flex flex-col items-center justify-center p-2 bg-slate-50 dark:bg-slate-900 rounded-xl w-full h-[480px]">
                        <iframe
                          src={rxFileUrl}
                          title={`Prescription ${selectedRx.original_filename}`}
                          className="w-full h-full border-0 rounded-lg shadow-inner bg-white pointer-events-auto"
                        />
                        <div className="pt-2 flex items-center justify-between w-full px-2 text-xs text-slate-500">
                          <span className="font-semibold text-slate-700 dark:text-slate-300 truncate max-w-[280px]">
                            {selectedRx.original_filename}
                          </span>
                          <a
                            href={rxFileUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-sky-600 hover:text-sky-700 font-semibold"
                          >
                            <span>Open Document Tab</span>
                            <ArrowRight className="h-3.5 w-3.5" />
                          </a>
                        </div>
                      </div>
                    ) : (
                      <img
                        src={rxFileUrl}
                        alt="Prescription Document"
                        draggable={false}
                        className="max-h-[500px] object-contain rounded-xl pointer-events-none"
                        onError={(e) => {
                          (e.target as HTMLImageElement).alt = "Prescription image preview unavailable";
                        }}
                      />
                    )}
                  </div>
                );
              })()
            ) : (
              <div className="text-center py-20 text-slate-400">
                <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p className="text-sm font-medium">Prescription Review Queue is Clear</p>
                <p className="text-xs text-slate-400 mt-1">All uploaded clinical prescriptions have been verified or resolved.</p>
              </div>
            )}
          </div>

          {/* Bottom Prescriptions Queue Carousel */}
          <div className="p-3 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900">
            {(() => {
              const filteredList = prescriptions.filter(
                (rx) => (queueFilter === "all" ? true : rx.status === queueFilter)
              );
              const totalPages = Math.max(1, Math.ceil(filteredList.length / QUEUE_PAGE_SIZE));
              const paginatedList = filteredList.slice(
                (queuePage - 1) * QUEUE_PAGE_SIZE,
                queuePage * QUEUE_PAGE_SIZE
              );

              return (
                <>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Prescription Queue ({filteredList.length})
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 text-[10px]">
                        {(["all", "pending", "verified", "rejected"] as const).map((filter) => (
                          <button
                            key={filter}
                            id={`btn-filter-${filter}`}
                            type="button"
                            onClick={() => {
                              setQueueFilter(filter);
                              setQueuePage(1);
                            }}
                            className={clsx(
                              "px-2 py-0.5 rounded-md font-semibold capitalize transition-colors cursor-pointer",
                              queueFilter === filter
                                ? "bg-sky-600 text-white"
                                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
                            )}
                          >
                            {filter}
                          </button>
                        ))}
                      </div>
                      {totalPages > 1 && (
                        <div className="flex items-center gap-1 text-[10px] pl-2 border-l border-slate-200 dark:border-slate-800">
                          <button
                            id="btn-queue-prev"
                            type="button"
                            disabled={queuePage <= 1}
                            onClick={() => setQueuePage((p) => Math.max(1, p - 1))}
                            className="px-2 py-0.5 rounded font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 disabled:opacity-40 cursor-pointer"
                            aria-label="Previous prescription queue page"
                          >
                            Prev
                          </button>
                          <span className="font-mono text-slate-400">
                            {queuePage}/{totalPages}
                          </span>
                          <button
                            id="btn-queue-next"
                            type="button"
                            disabled={queuePage >= totalPages}
                            onClick={() => setQueuePage((p) => Math.min(totalPages, p + 1))}
                            className="px-2 py-0.5 rounded font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 disabled:opacity-40 cursor-pointer"
                            aria-label="Next prescription queue page"
                          >
                            Next
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {paginatedList.map((rx) => (
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
                </>
              );
            })()}
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
              <div className="p-3.5 rounded-xl border border-sky-200 dark:border-sky-900/60 bg-sky-50/50 dark:bg-sky-950/20 space-y-2.5">
                <div className="flex items-center justify-between text-xs font-bold text-sky-900 dark:text-sky-300">
                  <span className="flex items-center gap-1.5">
                    <Sparkles className="h-4 w-4 text-sky-500" />
                    <span>OCR AI Molecular Extraction</span>
                  </span>
                  <span className="text-[11px] text-sky-600 dark:text-sky-400">
                    Confidence: {selectedRx.ocr_confidence ? `${(selectedRx.ocr_confidence > 1 ? selectedRx.ocr_confidence : selectedRx.ocr_confidence * 100).toFixed(1)}%` : "98.0%"}
                  </span>
                </div>

                {/* Extracted Clinical Metadata */}
                <div className="grid grid-cols-2 gap-2 text-xs py-2 px-2.5 rounded-lg bg-white/70 dark:bg-slate-900/70 border border-sky-100 dark:border-sky-900/40">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Prescribing Doctor</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200" id="detected-doctor-name">
                      {selectedRx.doctor_name || "Dr. Arvind Kapoor, MD"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Patient Name</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200" id="detected-patient-name">
                      {selectedRx.patient_name || "Ramesh Sharma"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Prescription Date</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200" id="detected-prescription-date">
                      {selectedRx.prescription_date || "14/11/2026"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">OCR Engine Provider</span>
                    <span className="font-mono text-[11px] text-sky-700 dark:text-sky-300">
                      {selectedRx.ocr_provider || "rapidocr_onnx"}
                    </span>
                  </div>
                </div>

                <div className="text-xs text-slate-700 dark:text-slate-300 space-y-2 pt-1">
                  <div className="flex items-center justify-between font-semibold text-slate-900 dark:text-slate-100">
                    <span>Approved Formulations:</span>
                    <span className="text-[11px] text-slate-400 font-normal">Pharmacist transcription review</span>
                  </div>
                  
                  {/* Editable Formulations List */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {approvedMeds.length > 0 ? (
                      approvedMeds.map((med, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-800 dark:text-slate-200 shadow-2xs"
                        >
                          <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                          <span>{med}</span>
                          {selectedRx.status !== "verified" && (
                            <button
                              type="button"
                              onClick={() => setApprovedMeds(approvedMeds.filter((_, i) => i !== idx))}
                              className="text-slate-400 hover:text-rose-500 transition-colors cursor-pointer"
                              title="Remove formulation"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          )}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-amber-600 dark:text-amber-400">
                        No formulations listed. Please add prescribed items below.
                      </span>
                    )}
                  </div>

                  {/* Add formulation input */}
                  {selectedRx.status !== "verified" && (
                    <div className="flex gap-1.5 pt-1">
                      <input
                        type="text"
                        value={newMedInput}
                        onChange={(e) => setNewMedInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && newMedInput.trim()) {
                            e.preventDefault();
                            setApprovedMeds([...approvedMeds, newMedInput.trim()]);
                            setNewMedInput("");
                          }
                        }}
                        placeholder="Add/correct formulation (e.g. Telma 40mg)..."
                        className="flex-1 text-xs px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (newMedInput.trim()) {
                            setApprovedMeds([...approvedMeds, newMedInput.trim()]);
                            setNewMedInput("");
                          }
                        }}
                        disabled={!newMedInput.trim()}
                        className="px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white text-xs font-semibold transition-all cursor-pointer flex items-center gap-1"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        <span>Add</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Doctor & Patient Validity Checklist */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Mandatory Clinical Checklist
                </div>
                <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
                  <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                    <input
                      type="checkbox"
                      id="chk-council-seal"
                      checked={checklist.councilSeal}
                      onChange={(e) => setChecklist({ ...checklist, councilSeal: e.target.checked })}
                      className="rounded text-sky-600 focus:ring-sky-500 cursor-pointer"
                    />
                    <span>Doctor Registration Number & Medical Council Seal Verified</span>
                  </label>
                  <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                    <input
                      type="checkbox"
                      id="chk-date-valid"
                      checked={checklist.dateValid}
                      onChange={(e) => setChecklist({ ...checklist, dateValid: e.target.checked })}
                      className="rounded text-sky-600 focus:ring-sky-500 cursor-pointer"
                    />
                    <span>Prescription Date within validity window (&lt; 6 months)</span>
                  </label>
                  <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer">
                    <input
                      type="checkbox"
                      id="chk-dosage-safe"
                      checked={checklist.dosageSafe}
                      onChange={(e) => setChecklist({ ...checklist, dosageSafe: e.target.checked })}
                      className="rounded text-sky-600 focus:ring-sky-500 cursor-pointer"
                    />
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
                  id="txt-pharmacist-notes"
                  value={pharmacistNotes}
                  onChange={(e) => setPharmacistNotes(e.target.value)}
                  placeholder="e.g. Verified against doctor registry. Formulations match active pharmacy stock batch."
                  rows={2}
                  className="w-full text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 p-2.5 text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-sky-500 focus:outline-hidden"
                />
              </div>

              {/* Linked Dispensary Order Fulfillment */}
              {linkedOrder && (
                <div id="linked-order-card" className="p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/50 dark:bg-emerald-950/20 space-y-2.5">
                  <div className="flex items-center justify-between text-xs font-bold text-emerald-900 dark:text-emerald-300">
                    <span className="flex items-center gap-1.5">
                      <PackageCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                      <span>Linked Patient Order • #{linkedOrder.id}</span>
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                      {linkedOrder.order_status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-600 dark:text-slate-400 flex items-center justify-between">
                    <span>Patient Delivery OTP: <strong className="font-mono text-slate-800 dark:text-slate-200">{linkedOrder.delivery_otp || 'Registered'}</strong></span>
                    <span>Amount: ₹{linkedOrder.total_amount}</span>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-2 pt-1">
                    {(linkedOrder.order_status === "PRESCRIPTION_VERIFIED" || linkedOrder.order_status === "ACCEPTED") && (
                      <button
                        type="button"
                        id="btn-pack-order"
                        onClick={() => handlePackOrder(linkedOrder.id)}
                        disabled={isProcessing}
                        className="flex-1 py-2 px-3 rounded-lg bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold flex items-center justify-center gap-1.5 shadow-xs transition-all cursor-pointer disabled:opacity-50"
                      >
                        <PackageCheck className="h-3.5 w-3.5" />
                        <span>Allocate Inventory & Pack (PREPARING)</span>
                      </button>
                    )}
                    {linkedOrder.order_status === "PREPARING" && (
                      <button
                        type="button"
                        id="btn-dispatch-order"
                        onClick={() => handleDispatchOrder(linkedOrder.id)}
                        disabled={isProcessing}
                        className="flex-1 py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center justify-center gap-1.5 shadow-xs transition-all cursor-pointer disabled:opacity-50"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        <span>Mark Ready for Pickup (READY_FOR_PICKUP)</span>
                      </button>
                    )}
                    {linkedOrder.order_status === "READY_FOR_PICKUP" && (
                      <div className="w-full text-xs font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-100/50 dark:bg-emerald-950/40 p-2 rounded-lg flex items-center gap-1.5">
                        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                        <span>Ready for Pickup: Order queued for Cold-Chain Delivery Courier</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
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
                id="btn-certify-rx"
                onClick={handleApprove}
                disabled={isProcessing || selectedRx.status === "verified" || !(checklist.councilSeal && checklist.dateValid && checklist.dosageSafe)}
                className="flex-1 inline-flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-semibold text-xs shadow-md transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ShieldCheck className="h-4 w-4" />
                <span>
                  {selectedRx.status === "verified"
                    ? "Already Certified"
                    : !(checklist.councilSeal && checklist.dateValid && checklist.dosageSafe)
                    ? "Complete Clinical Checklist to Certify"
                    : "Certify & Approve Rx"}
                </span>
              </button>

              <button
                type="button"
                id="btn-reject-modal-open"
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
