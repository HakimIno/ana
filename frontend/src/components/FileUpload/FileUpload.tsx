"use client";

import { useState, useRef } from "react";
import { UploadCloud, FileSpreadsheet, Loader2, CheckCircle2, AlertCircle } from "lucide-react";

interface FileUploadProps {
    onUploadSuccess: (fileInfo: any) => void;
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setError(null);
        setSuccess(false);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://localhost:8000/upload", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Upload failed. Verify the file is a valid Excel or CSV.");
            }

            const data = await response.json();
            setSuccess(true);
            onUploadSuccess(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="upload-box">
            <div
                className={`drop-zone ${isUploading ? 'uploading' : ''} ${success ? 'success' : ''}`}
                onClick={() => !isUploading && fileInputRef.current?.click()}
            >
                <div className="icon-container">
                    {isUploading ? (
                        <Loader2 className="icon spin" />
                    ) : success ? (
                        <CheckCircle2 className="icon success-icon" />
                    ) : (
                        <UploadCloud className="icon" />
                    )}
                </div>
                <p>{isUploading ? 'Ingesting data...' : success ? 'Data Loaded' : 'Upload Data File'}</p>
                <p className="subtext">{success ? 'Click to change file' : 'Drag & drop Excel or CSV'}</p>
            </div>

            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                style={{ display: 'none' }}
                accept=".csv, .xlsx, .xls"
            />

            {error && (
                <div className="error-container">
                    <AlertCircle size={14} />
                    <span>{error}</span>
                </div>
            )}

            <style jsx>{`
        .upload-box {
          width: 100%;
        }

        .drop-zone {
          border: 1px dashed var(--border-color);
          border-radius: 12px;
          padding: 24px 16px;
          text-align: center;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          background: rgba(255, 255, 255, 0.02);
        }

        .drop-zone:hover:not(.uploading) {
          border-color: var(--accent-color);
          background: rgba(16, 185, 129, 0.05);
          transform: translateY(-2px);
        }

        .drop-zone.success {
          border-color: var(--accent-color);
          background: rgba(16, 185, 129, 0.03);
        }

        .icon-container {
          margin-bottom: 12px;
          display: flex;
          justify-content: center;
        }

        :global(.icon) {
          width: 28px;
          height: 28px;
          color: var(--text-secondary);
        }

        :global(.spin) {
          animation: spin 2s linear infinite;
          color: var(--accent-secondary);
        }

        :global(.success-icon) {
          color: var(--accent-color);
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        p {
          font-size: 13px;
          font-weight: 600;
        }

        .subtext {
          font-size: 11px;
          color: var(--text-secondary);
          margin-top: 4px;
          font-weight: 400;
        }

        .error-container {
          margin-top: 12px;
          padding: 8px 12px;
          background: rgba(239, 68, 68, 0.1);
          border-radius: 6px;
          color: var(--error);
          font-size: 11px;
          display: flex;
          align-items: center;
          gap: 6px;
          border: 1px solid rgba(239, 68, 68, 0.1);
        }
      `}</style>
        </div>
    );
}
