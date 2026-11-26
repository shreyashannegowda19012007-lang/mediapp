"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  FileText,
  Upload,
  ShieldCheck,
  Clock,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Loader2,
  X,
  Pill,
  ArrowRight,
  Eye,
  Lock,
  User,
} from "lucide-react";
import { api, Prescription } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";
import { AuthModal } from "@/components/auth/AuthModal";
import { clsx } from "clsx";

interface PatientPrescriptionsViewProps {
  onNavigateToCatalogue?: (query?: string) => void;
}

export function PatientPrescriptionsView({
  onNavigateToCatalogue,
}: PatientPrescriptionsViewProps) {
  const { user } = useAuthStore();
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<any | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const isAuthenticated = Boolean(user && (user.email || user.full_name));

  const loadPrescriptions = useCallback(async () => {
    if (!isAuthenticated) {
      setPrescriptions([]);
      setIsLoadingList(false);
      return;
    }
    try {
      setIsLoadingList(true);
      const res = await api.prescriptions.list();
      setPrescriptions(res.prescriptions || []);
    } catch {
      setPrescriptions([]);
    } finally {
      setIsLoadingList(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    loadPrescriptions();
  }, [loadPrescriptions]);

  // Handle local file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setFile(selected);
    setUploadError(null);
    setUploadSuccess(null);

    if (selected.type.startsWith("image/")) {
      setPreviewUrl(URL.createObjectURL(selected));
    } else {
      setPreviewUrl(null);
    }
  };

  const handleClearFile = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    if (!isAuthenticated) {
      setShowAuthModal(true);
      return;
    }

    try {
      setIsUploading(true);
      setUploadError(null);
      const res = await api.prescriptions.upload(file);
      setUploadSuccess(res);
      handleClearFile();
      await loadPrescriptions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload prescription";
      setUploadError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Clinical Trust Banner */}
      <div className="relative rounded-3xl border border-sky-100 dark:border-slate-800 bg-gradient-to-b from-sky-500/10 via-sky-500/5 to-transparent p-6 sm:p-8 backdrop-blur-xs">
        <div className="max-w-3xl mx-auto space-y-3 text-center">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
            <span>Licensed Pharmacist Clinical Verification Gateway</span>
          </div>

          <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900 dark:text-slate-100">
            Patient Prescription Center
          </h2>

          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Upload your registered medical practitioner&apos;s prescription for verification. Our licensed dispensary pharmacists audit active molecules, check contraindications, and certify your order for cold-chain doorstep dispatch.
          </p>
        </div>
      </div>

      {/* Grid: Upload Card (Left 5 Cols) + Guidelines/OCR (Right 7 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Prescription Upload Card */}
        <div className="lg:col-span-5 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-xs flex flex-col justify-between space-y-5">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-bold text-sm">
              <Upload className="h-4 w-4 text-sky-500" />
              <span>Upload New Doctor&apos;s Prescription</span>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400">
              Accepted formats: PNG, JPG, JPEG, or PDF up to 16MB. Ensure doctor&apos;s registration and signature are clearly visible.
            </p>

            {/* Dropzone Container */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className={clsx(
                "rounded-2xl border-2 border-dashed p-6 text-center transition-all cursor-pointer flex flex-col items-center justify-center min-h-[170px]",
                file
                  ? "border-sky-500 bg-sky-50/40 dark:bg-sky-950/20"
                  : "border-slate-300 dark:border-slate-700 hover:border-sky-400 bg-slate-50/50 dark:bg-slate-950/40"
              )}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".png,.jpg,.jpeg,.pdf"
                onChange={handleFileChange}
                className="hidden"
              />

              {file ? (
                <div className="space-y-2">
                  <div className="mx-auto w-10 h-10 rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="font-bold text-xs text-slate-800 dark:text-slate-200 truncate max-w-[240px]">
                    {file.name}
                  </div>
                  <div className="text-[11px] text-slate-400">
                    {(file.size / 1024).toFixed(1)} KB • Ready to submit
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="mx-auto w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center">
                    <Upload className="h-5 w-5" />
                  </div>
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Click to browse or drop prescription file
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Supports high-resolution camera scans
                  </div>
                </div>
              )}
            </div>

            {file && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500 truncate">{file.name}</span>
                <button
                  type="button"
                  onClick={handleClearFile}
                  className="text-rose-600 dark:text-rose-400 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
                >
                  <X className="h-3.5 w-3.5" />
                  <span>Remove</span>
                </button>
              </div>
            )}

            {uploadError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-700 dark:text-rose-400 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{uploadError}</span>
              </div>
            )}
          </div>

          <button
            type="button"
            onClick={handleUploadSubmit}
            disabled={isUploading || !file}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-sky-600 hover:bg-sky-700 active:scale-[0.98] text-white text-xs font-bold transition-all cursor-pointer shadow-md disabled:opacity-50"
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Processing OCR & Uploading...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4" />
                <span>Submit Prescription for Verification</span>
              </>
            )}
          </button>
        </div>

        {/* Right 7 Cols: Upload Feedback or Verification Guidelines */}
        <div className="lg:col-span-7 space-y-4">
          {uploadSuccess ? (
            <div className="p-6 rounded-3xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/60 dark:bg-emerald-950/20 shadow-xs space-y-4 animate-in fade-in duration-200">
              <div className="flex items-center gap-2.5 text-emerald-800 dark:text-emerald-300 font-bold text-sm">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                <span>Prescription Uploaded Successfully (Rx #{uploadSuccess.prescription_id})</span>
              </div>

              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                Your prescription has been forwarded to our dispensary clinical audit desk. An authorized pharmacist is reviewing the active molecules and dosages.
              </p>

              {uploadSuccess.detected_medicines && uploadSuccess.detected_medicines.length > 0 && (
                <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-emerald-100 dark:border-emerald-900/40 space-y-2">
                  <div className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                    <Pill className="h-4 w-4 text-sky-500" />
                    <span>OCR Detected Formulations ({uploadSuccess.detected_medicines.length}):</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {uploadSuccess.detected_medicines.map((m: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg text-xs font-medium bg-sky-50 dark:bg-sky-950/40 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800"
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs space-y-4">
              <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-bold text-sm">
                <ShieldCheck className="h-5 w-5 text-sky-500" />
                <span>Clinical Pharmacy Verification Standards</span>
              </div>

              <div className="space-y-3 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950/50 border border-slate-100 dark:border-slate-800 space-y-1">
                  <strong className="text-slate-800 dark:text-slate-200 block">1. Legible Doctor Credentials</strong>
                  <span>Prescription must display the doctor&apos;s full name, medical council registration number, clinic address, and contact number.</span>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950/50 border border-slate-100 dark:border-slate-800 space-y-1">
                  <strong className="text-slate-800 dark:text-slate-200 block">2. Prescription Date & Patient Details</strong>
                  <span>Valid for 6 months from issue date for chronic medications, or 7 days for acute antibiotics under Indian Drugs & Cosmetics Rules.</span>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-950/50 border border-slate-100 dark:border-slate-800 space-y-1">
                  <strong className="text-slate-800 dark:text-slate-200 block">3. Cold-Chain Verification</strong>
                  <span>Prescriptions for insulin or biologics automatically trigger 2°C - 8°C temperature telemetry logging and insulated courier box dispatch.</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Uploaded Prescriptions List Section */}
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-lg font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <FileText className="h-5 w-5 text-sky-500" />
              <span>Your Prescription Audit History</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Real-time audit status of all prescriptions submitted under your patient profile.
            </p>
          </div>

          <button
            type="button"
            onClick={loadPrescriptions}
            className="text-xs font-semibold text-sky-600 dark:text-sky-400 hover:underline cursor-pointer"
          >
            Refresh Status
          </button>
        </div>

        {/* Content Router */}
        {!isAuthenticated ? (
          <div className="p-8 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-center space-y-3">
            <div className="mx-auto w-12 h-12 rounded-2xl bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center font-bold">
              <Lock className="h-6 w-6" />
            </div>
            <h4 className="font-bold text-base text-slate-900 dark:text-slate-100">
              Sign In to Access Your Prescription Records
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
              Prescription records are confidential medical documents encrypted and restricted to your authenticated patient identity.
            </p>
            <button
              onClick={() => setShowAuthModal(true)}
              className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
            >
              <User className="h-4 w-4" />
              <span>Sign In to MediApp</span>
            </button>
          </div>
        ) : isLoadingList ? (
          <div className="py-16 text-center space-y-2">
            <Loader2 className="h-6 w-6 animate-spin text-sky-500 mx-auto" />
            <div className="text-xs text-slate-400">Loading prescription history...</div>
          </div>
        ) : prescriptions.length === 0 ? (
          <div className="p-12 text-center rounded-3xl border border-dashed border-slate-200 dark:border-slate-800 space-y-2">
            <FileText className="h-10 w-10 text-slate-300 dark:text-slate-600 mx-auto" />
            <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">
              No Prescriptions Uploaded Yet
            </h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Upload your doctor&apos;s prescription above to initiate licensed pharmacist verification and order prescription-grade medications.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {prescriptions.map((rx) => {
              const statusLower = (rx.status || "pending").toLowerCase();
              const isApproved = statusLower === "verified" || statusLower === "approved";
              const isRejected = statusLower === "rejected";
              const isPending = !isApproved && !isRejected;

              const detectedMeds = rx.detected_medicines || rx.extracted_medicines || [];

              return (
                <div
                  key={rx.id}
                  className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-xs space-y-3"
                >
                  {/* Status & ID Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-black text-sm text-slate-900 dark:text-slate-100">
                        Rx #{rx.id}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(rx.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    {isApproved && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
                        <ShieldCheck className="h-3 w-3" />
                        <span>Verified & Approved</span>
                      </span>
                    )}

                    {isPending && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-800 dark:text-amber-400 border border-amber-500/30">
                        <Clock className="h-3 w-3" />
                        <span>Pharmacist Review Pending</span>
                      </span>
                    )}

                    {isRejected && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Rejected</span>
                      </span>
                    )}
                  </div>

                  {/* Metadata Row */}
                  <div className="text-xs text-slate-500 dark:text-slate-400 space-y-1">
                    <div className="truncate">
                      <strong>File:</strong> {rx.original_filename}
                    </div>
                    {rx.doctor_name && (
                      <div>
                        <strong>Doctor:</strong> {rx.doctor_name}
                      </div>
                    )}
                  </div>

                  {/* Detected Medicines */}
                  {detectedMeds.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                        Verified Formulations ({detectedMeds.length}):
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {detectedMeds.map((m: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                          >
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Rejection Notes or Clinical Guidance */}
                  {isRejected && rx.rejection_reason && (
                    <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-800 dark:text-rose-300">
                      <strong>Pharmacist Note:</strong> {rx.rejection_reason}
                    </div>
                  )}

                  {/* Order Prescriptions Action if Approved */}
                  {isApproved && onNavigateToCatalogue && (
                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                      <button
                        id={`btn-order-approved-rx-${rx.id}`}
                        onClick={() => onNavigateToCatalogue(detectedMeds.length > 0 ? detectedMeds[0] : undefined)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
                      >
                        <Pill className="h-3.5 w-3.5" />
                        <span>Order Approved Medicines</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Auth Modal for Unauthenticated Users */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onAuthSuccess={() => {
          setShowAuthModal(false);
          loadPrescriptions();
        }}
      />
    </div>
  );
}
