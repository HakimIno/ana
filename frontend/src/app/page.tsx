"use client";

import { useState, useEffect } from "react";
import FileUpload from "@/components/FileUpload/FileUpload";
import ChatInterface from "@/components/ChatInterface/ChatInterface";

export default function Home() {
  const [currentFile, setCurrentFile] = useState<any>(null);

  return (
    <div className="dashboard-container">
      <aside className="glass-panel sidebar">
        <div className="brand">
          <div className="brand-logo">📊</div>
          <h2>AI Analyst</h2>
        </div>

        <div className="sidebar-section">
          <h3>Data Ingestion</h3>
          <FileUpload onUploadSuccess={(fileInfo) => setCurrentFile(fileInfo)} />
        </div>

        {currentFile && (
          <div className="file-info glass-panel">
            <p className="label">Active File</p>
            <p className="filename">{currentFile.filename}</p>
            <div className="file-stats">
              <span>{currentFile.row_count} rows</span>
              <span>{currentFile.sheet_name}</span>
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          <p>© 2026 AI Analyst Pro</p>
        </div>
      </aside>

      <main className="main-content">
        <header className="main-header glass-panel">
          <div className="status-indicator">
            <span className={`dot ${currentFile ? 'active' : ''}`}></span>
            {currentFile ? 'System Ready' : 'Awaiting Data'}
          </div>
          <h1>Business Intelligence Dashboard</h1>
        </header>

        <section className="chat-container">
          <ChatInterface activeFile={currentFile} />
        </section>
      </main>

      <style jsx>{`
        .dashboard-container {
          display: flex;
          height: 100vh;
          width: 100vw;
          padding: 16px;
          gap: 16px;
          overflow: hidden;
        }

        .sidebar {
          width: 320px;
          display: flex;
          flex-direction: column;
          padding: 24px;
          flex-shrink: 0;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 40px;
        }

        .brand-logo {
          font-size: 32px;
        }

        .sidebar-section {
          flex-grow: 1;
        }

        .sidebar-section h3 {
          font-size: 12px;
          text-transform: uppercase;
          color: var(--text-secondary);
          margin-bottom: 16px;
          letter-spacing: 0.1em;
        }

        .file-info {
          margin-top: 24px;
          padding: 16px;
          background: rgba(255, 255, 255, 0.05);
        }

        .file-info .label {
          font-size: 10px;
          text-transform: uppercase;
          color: var(--accent-color);
          margin-bottom: 4px;
        }

        .file-info .filename {
          font-weight: 600;
          font-size: 14px;
          margin-bottom: 8px;
        }

        .file-stats {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: var(--text-secondary);
        }

        .main-content {
          flex-grow: 1;
          display: flex;
          flex-direction: column;
          gap: 16px;
          overflow: hidden;
        }

        .main-header {
          padding: 20px 32px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: var(--text-secondary);
        }

        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #334155;
        }

        .dot.active {
          background: var(--accent-color);
          box-shadow: 0 0 8px var(--accent-color);
        }

        .chat-container {
          flex-grow: 1;
          overflow: hidden;
        }

        .sidebar-footer {
          margin-top: auto;
          font-size: 12px;
          color: var(--text-secondary);
          text-align: center;
        }
      `}</style>
    </div>
  );
}
