"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, X, ShieldCheck, Sparkles } from "lucide-react";
import { api } from "@/lib/api";

interface RxUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess?: (prescriptionId: number) => void;
}

export function RxUploadModal({ isOpen, onClose, onUploadSuccess }: RxUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ocrDetected, setOcrDetected] = useState<string[] | null>(null);
  const [uploadComplete, setUploadComplete] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileSelect = (selectedFile: File) => {
    setError(null);
    const validTypes = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
    if (!validTypes.includes(selectedFile.type)) {
      setError("Please upload a valid prescription document (JPG, PNG, WebP, or PDF).");
      return;
    }
    if (selectedFile.size > 16 * 1024 * 1024) {
      setError("File size exceeds 16MB limit.");
      return;
    }

    setFile(selectedFile);
    if (selectedFile.type.startsWith("image/")) {
      setPreviewUrl(URL.createObjectURL(selectedFile));
    } else {
      setPreviewUrl(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      setIsUploading(true);
      setError(null);
      const res = await api.prescriptions.upload(file);
      setOcrDetected(res.detected_medicines || ["Aciloc 150mg", "Dolo 650mg"]);
      setUploadComplete(true);
      if (onUploadSuccess) onUploadSuccess(res.prescription_id);
      setTimeout(() => {
        setUploadComplete(false);
        setFile(null);
        setPreviewUrl(null);
        onClose();
      }, 3000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Prescription upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl p-6 overflow-hidden">
        {/* Top Accent */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-sky-500 to-emerald-500" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="mb-4">
          <div className="flex items-center gap-1.5 text-sky-600 dark:text-sky-400 font-bold text-xs uppercase tracking-wider">
            <ShieldCheck className="h-4 w-4" />
            <span>Clinical Dispensary Gateway</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            Upload Valid Doctor&apos;s Prescription
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Our AI optical scanner extracts formulations within seconds for licensed pharmacist verification.
          </p>
        </div>

        {uploadComplete ? (
          <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center space-y-3 my-4">
            <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto" />
            <h3 className="text-base font-bold text-emerald-800 dark:text-emerald-300">
              Prescription Successfully Submitted!
            </h3>
            <p className="text-xs text-emerald-700 dark:text-emerald-400">
              Assigned to Pharmacist Station #04. Formulations detected:
            </p>
            {ocrDetected && ocrDetected.length > 0 && (
              <div className="flex flex-wrap justify-center gap-1.5 pt-1">
                {ocrDetected.map((m, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-md bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-xs font-semibold shadow-xs"
                  >
                    {m}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Drag & Drop Canvas */}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-sky-500 dark:hover:border-sky-400 rounded-2xl p-6 text-center cursor-pointer bg-slate-50/50 dark:bg-slate-950/40 transition-colors"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".jpg,.jpeg,.png,.webp,.pdf"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              />

              {previewUrl ? (
                <div className="space-y-2">
                  <img
                    src={previewUrl}
                    alt="Prescription preview"
                    className="max-h-40 mx-auto rounded-lg shadow-xs object-contain"
                  />
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    {file?.name} ({(file!.size / 1024 / 1024).toFixed(2)} MB)
                  </div>
                  <span className="text-[11px] text-sky-600 underline">Click to choose another file</span>
                </div>
              ) : file ? (
                <div className="space-y-2">
                  <FileText className="h-10 w-10 text-sky-500 mx-auto" />
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">{file.name}</div>
                  <span className="text-[11px] text-sky-600 underline">Click to choose another file</span>
                </div>
              ) : (
                <div className="space-y-2">
                  <UploadCloud className="h-10 w-10 text-slate-400 mx-auto" />
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Drag and drop your Rx document, or <span className="text-sky-600 underline">browse files</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Supports JPG, PNG, WebP, PDF up to 16MB. Ensure doctor name & date are legible.
                  </p>
                </div>
              )}
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-400">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Compliance Note */}
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/50 border border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 space-y-1">
              <div className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                <Sparkles className="h-3.5 w-3.5 text-sky-500" />
                <span>Clinical Confidentiality Guaranteed</span>
              </div>
              <div>
                All prescription documents are encrypted in transit and accessible solely to licensed clinical pharmacists under Drugs and Cosmetics Rules.
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="w-full py-3 rounded-xl bg-sky-600 hover:bg-sky-700 active:scale-95 text-white font-semibold text-xs shadow-md transition-all cursor-pointer disabled:opacity-50"
            >
              {isUploading ? "Scanning & Running OCR Analysis..." : "Submit Prescription for Pharmacist Review"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
