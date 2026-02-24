"use client";

import { useState, useEffect } from "react";
import FileUpload from "@/components/FileUpload/FileUpload";
import ChatInterface from "@/components/ChatInterface/ChatInterface";

import Tree5 from "@/components/Tree5";
import TreeDraw from "@/components/Treedraw";
import Image from "next/image";

export default function Home() {
  const [currentFile, setCurrentFile] = useState<any>(null);

  useEffect(() => {
    // Fetch latest file from backend if exists
    const fetchFiles = async () => {
      try {
        const response = await fetch("http://localhost:8000/files");
        if (response.ok) {
          const files = await response.json();
          if (files && files.length > 0) {
            // Sort by created_at descending and pick the latest
            const sortedFiles = files.sort((a: any, b: any) => b.created_at - a.created_at);
            setCurrentFile(sortedFiles[0]);
          }
        }
      } catch (err) {
        console.error("Failed to fetch files:", err);
      }
    };
    fetchFiles();
  }, []);

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="branding">
          <Image src="/book.gif" alt="Book" width={32} height={32} />
          <span className="brand-name">ana</span>
          <span className="cursor-blink">_</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">
            <span className="section-title">ENGINE</span>
            <div className="upload-wrapper">
              <FileUpload onUploadSuccess={(fileInfo) => setCurrentFile(fileInfo)} />
            </div>
          </div>

          {currentFile && (
            <div className="active-session">
              <span className="section-title">SESSION</span>
              <div className="file-info mono">
                <p className="filename">{currentFile.filename}</p>
                <div className="stats">
                  {currentFile.row_count} rows | {currentFile.sheet_name}
                </div>
              </div>
            </div>
          )}

          <div className="sidebar-animation">
            <Tree5 />
          </div>
        </nav>

        <footer className="sidebar-footer mono">
          <p>v0.4.2-stable</p>
        </footer>
      </aside>

      <main className="main-stage">
        <header className="page-header">
          <div className="status-bar mono">
            <span className={`status-dot ${currentFile ? 'online' : 'idle'}`}></span>
            {currentFile ? 'CONNECTED' : 'STANDBY'}
          </div>
          <h1 className="mono">Intelligence Analyst</h1>
        </header>

        <section className="interaction-zone">
          <ChatInterface activeFile={currentFile} />
        </section>
      </main>

      <style jsx>{`
        .app-container {
          display: flex;
          height: 100vh;
          width: 100vw;
          background: var(--bg-color);
          color: var(--text-primary);
        }

        .sidebar {
          width: 280px;
          border-right: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
          padding: 24px;
          background: #080808;
        }

        .branding {
          font-family: var(--font-mono);
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 40px;
          color: var(--accent-color);
          display: flex;
          align-items: center;
        }

        .cursor-blink {
          animation: blink 1s step-end infinite;
        }

        @keyframes blink {
          50% { opacity: 0; }
        }

        .sidebar-nav {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 32px;
        }

        .section-title {
          display: block;
          font-family: var(--font-mono);
          font-size: 11px;
          color: var(--text-secondary);
          margin-bottom: 12px;
          letter-spacing: 0.1em;
        }

        .file-info {
          padding: 12px;
          background: var(--surface-color);
          border-radius: 4px;
          border: 1px solid var(--border-color);
        }

        .filename {
          font-size: 13px;
          color: var(--text-primary);
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .stats {
          font-size: 11px;
          color: var(--text-secondary);
        }

        .sidebar-animation {
          margin-top: auto;
          width: 100%;
          height: 140px;
          display: flex;
          align-items: flex-end;
          overflow: hidden;
          opacity: 0.8;
          /* Filter to make it look slightly more integrated */
          filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.1));
        }

        .sidebar-footer {
          font-size: 10px;
          color: #333;
          padding-top: 20px;
          border-top: 1px solid #1a1a1a;
          margin-top: 24px;
        }

        .main-stage {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          background: var(--bg-color);
        }

        .page-header {
          padding: 20px 40px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid var(--border-color);
        }

        .page-header h1 {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-secondary);
        }

        .status-bar {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11px;
          font-weight: 600;
        }

        .status-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
        }

        .status-dot.online { background: var(--terminal-green); box-shadow: 0 0 8px var(--terminal-green); }
        .status-dot.idle { background: #333; }

        .interaction-zone {
          flex: 1;
          padding: 0;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
}
