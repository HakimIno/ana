'use client';

import React, { useRef, useState } from 'react';
import { Upload, Loader2 } from 'lucide-react';

interface PdfUploaderProps {
    onGenerated: (typstCode: string) => void;
}

export const PdfUploader: React.FC<PdfUploaderProps> = ({ onGenerated }) => {
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please select a valid PDF file.');
            return;
        }

        setIsUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            // Call the FastAPI backend
            const response = await fetch('http://localhost:8000/typst/generate', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Upload failed with status ${response.status}`);
            }

            const data = await response.json();
            if (data.status === 'success' && data.raw_typst) {
                onGenerated(data.raw_typst);
            } else {
                throw new Error(data.message || 'Unknown error occurred');
            }
        } catch (error) {
            console.error('Error generating Typst:', error);
            alert(error instanceof Error ? error.message : 'Failed to generate Typst code.');
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = ''; // Reset input
            }
        }
    };

    return (
        <div className="flex items-center">
            <input
                type="file"
                accept="application/pdf"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
            />
            <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                style={{
                    padding: '4px 12px',
                    backgroundColor: '#007acc',
                    border: 'none',
                    borderRadius: '3px',
                    fontSize: '11px',
                    color: '#fff',
                    cursor: 'pointer',
                    fontWeight: 500,
                }}
                className='flex items-center gap-2'
            >
                {isUploading ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        <span className="text-white animate-pulse">Analyzing Layout...</span>
                    </>
                ) : (
                    <>
                        <Upload className="w-4 h-4 text-white" />
                        <span>Upload PDF</span>
                    </>
                )}
            </button>
        </div>
    );
};
