"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import FileUpload from "@/components/FileUpload/FileUpload";
import ChatInterface from "@/components/ChatInterface/ChatInterface";

import Tree5 from "@/components/Tree5";
import Image from "next/image";
import { Trash2, Plus, MessageSquare, ChevronRight, ChevronDown, Folder, FileText } from "lucide-react";
import { chatService } from "@/services/api";

export default function Home() {
  const queryClient = useQueryClient();
  const [activeFile, setActiveFile] = useState<any>(null);
  const [activeSessionId, setActiveSessionId] = useState<string>("default");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const toggleGroup = (groupName: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(groupName)) {
        next.delete(groupName);
      } else {
        next.add(groupName);
      }
      return next;
    });
  };

  // --- Queries ---
  const { data: files = [], refetch: refetchFiles } = useQuery({
    queryKey: ["files"],
    queryFn: async () => {
      const response = await fetch("http://localhost:8000/files");
      if (!response.ok) throw new Error("Failed to fetch files");
      const data = await response.json();
      return data;
    }
  });

  const { data: sessions = [] } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => chatService.listSessions()
  });

  // Set default active file when files load
  useEffect(() => {
    if (files.length > 0 && !activeFile) {
      const sorted = [...files].sort((a: any, b: any) => b.created_at - a.created_at);
      setActiveFile({ ...sorted[0], type: 'file' });
    }
  }, [files, activeFile]);

  // --- Mutations ---
  const deleteFileMutation = useMutation({
    mutationFn: async (filename: string) => {
      const response = await fetch(`http://localhost:8000/files/${filename}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to delete file");
      return filename;
    },
    onSuccess: (filename) => {
      queryClient.invalidateQueries({ queryKey: ["files"] });
      if (activeFile?.filename === filename) {
        setActiveFile(null);
      }
    },
    onError: (err) => {
      console.error("Error deleting file:", err);
      alert("Failed to delete file");
    }
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => chatService.deleteChatHistory(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      if (activeSessionId === sessionId) {
        setActiveSessionId("default");
      }
    },
    onError: (err) => {
      console.error("Failed to delete session:", err);
    }
  });

  const handleCreateSession = () => {
    const newId = `session_${Date.now()}`;
    setActiveSessionId(newId);
    // Note: session will appear in list after first message is sent and list is invalidated
  };

  const handleDeleteFile = (e: React.MouseEvent, filename: string) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete ${filename}? This will also clear the index.`)) {
      deleteFileMutation.mutate(filename);
    }
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (confirm(`Permanently delete chat history for "${sessionId}"?`)) {
      deleteSessionMutation.mutate(sessionId);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar glass-panel">
        <div className="branding">
          <Image src="/book.gif" alt="Book" width={32} height={32} unoptimized />
          <span className="brand-name">ana</span>
          <span className="cursor-blink">_</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">
            <span className="section-title">ENGINE</span>
            <div className="upload-wrapper">
              <FileUpload onUploadSuccess={(fileInfo) => {
                queryClient.invalidateQueries({ queryKey: ["files"] });
                setActiveFile(fileInfo);
              }} />
            </div>
          </div>

          <div className="nav-section scrollable">
            <span className="section-title">PROJECTS</span>
            <div className="accordion-list">
              {/* Unique Groups */}
              {Array.from(new Set(files.map((f: any) => f.group).filter(Boolean))).sort().map((groupName: any) => {
                const isExpanded = expandedGroups.has(groupName);
                const groupFiles = files.filter((f: any) => f.group === groupName);

                return (
                  <div key={`group-container-${groupName}`} className="accordion-item">
                    <div
                      className={`group-header mono ${activeFile?.type === 'group' && activeFile?.group === groupName ? 'active' : ''}`}
                      onClick={() => setActiveFile({ type: 'group', group: groupName, filename: `Group: ${groupName}` })}
                    >
                      <div className="header-content">
                        <button
                          className="expand-toggle"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleGroup(groupName);
                          }}
                        >
                          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </button>
                        <Folder size={14} className="folder-icon" />
                        <span className="group-name">{groupName}</span>
                      </div>
                      <span className="badge">{groupFiles.length}</span>
                    </div>

                    {isExpanded && (
                      <div className="group-content">
                        {groupFiles.map((file: any) => (
                          <div
                            key={file.filename}
                            className={`file-item mono ${activeFile?.type === 'file' && activeFile?.filename === file.filename ? 'active' : ''}`}
                            onClick={() => setActiveFile({ ...file, type: 'file' })}
                          >
                            <div className="file-link">
                              <FileText size={12} className="file-icon" />
                              <span className="filename">{file.filename}</span>
                            </div>
                            <button
                              className="delete-btn small"
                              onClick={(e) => handleDeleteFile(e, file.filename)}
                              title="Delete File"
                            >
                              <Trash2 size={10} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

          </div>

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
            <span className={`status-dot ${activeFile ? 'online' : 'idle'}`}></span>
            {activeFile ? 'CONNECTED' : 'STANDBY'}
          </div>
          <div className="session-context mono">
            <span className="label">SESSION:</span>
            <span className="value">{activeSessionId}</span>
          </div>
          <h1 className="mono">Intelligence Analyst</h1>
        </header>

        <section className="interaction-zone glass-panel">
          <ChatInterface
            activeFile={activeFile}
            sessionId={activeSessionId}
            onMessageSent={() => queryClient.invalidateQueries({ queryKey: ["sessions"] })}
          />
        </section>
      </main>

      <aside className="right-sidebar glass-panel">
        <div className="nav-section">
          <div className="section-header">
            <span className="section-title">HISTORY</span>
            <button className="new-chat-btn" onClick={handleCreateSession} title="New Chat">
              <Plus size={14} />
            </button>
          </div>

          <div className="session-list scrollable">
            <div
              className={`session-item mono ${activeSessionId === 'default' ? 'active' : ''}`}
              onClick={() => setActiveSessionId('default')}
            >
              <div className="session-info">
                <MessageSquare size={12} className="session-icon" />
                <span className="session-name">default</span>
              </div>
            </div>

            {sessions.filter(s => s.session_id !== 'default').map((session) => (
              <div
                key={session.session_id}
                className={`session-item mono ${activeSessionId === session.session_id ? 'active' : ''}`}
                onClick={() => setActiveSessionId(session.session_id)}
              >
                <div className="session-info">
                  <MessageSquare size={12} className="session-icon" />
                  <span className="session-name">{session.session_id.replace('session_', '')}</span>
                </div>
                <button
                  className="delete-session-btn"
                  onClick={(e) => handleDeleteSession(e, session.session_id)}
                  title="Delete Session"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </aside>

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

        .file-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .scrollable {
          overflow-y: auto;
          max-height: 400px;
          padding-right: 4px;
        }

        .scrollable::-webkit-scrollbar {
          width: 4px;
        }

        .scrollable::-webkit-scrollbar-thumb {
          background: #222;
          border-radius: 2px;
        }

        .file-info {
          padding: 12px;
          background: var(--surface-color);
          border-radius: 4px;
          border: 1px solid var(--border-color);
          cursor: pointer;
          transition: all 0.2s;
        }

        .file-info:hover {
          border-color: #333;
        }

        .file-info.active {
          border-color: var(--accent-color);
          background: rgba(139, 92, 246, 0.05);
          box-shadow: 0 0 15px rgba(139, 92, 246, 0.1);
        }

        .file-info.group {
          background: linear-gradient(90deg, rgba(139, 92, 246, 0.05) 0%, transparent 100%);
        }

        .file-info.group .filename {
          font-weight: 700;
          color: var(--accent-color);
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

        .accordion-list {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .accordion-item {
          border-radius: 6px;
          overflow: hidden;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .group-header {
          padding: 10px 12px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          cursor: pointer;
          transition: all 0.2s;
          user-select: none;
          border-left: 2px solid transparent;
        }

        .group-header:hover {
          background: rgba(139, 92, 246, 0.08);
        }

        .group-header.active {
          background: rgba(139, 92, 246, 0.1);
          border-left-color: var(--accent-color);
        }

        .header-content {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .expand-toggle {
          background: transparent;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 4px;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .expand-toggle:hover {
          background: rgba(255, 255, 255, 0.1);
          color: var(--accent-color);
        }

        .folder-icon {
          color: var(--accent-color);
          opacity: 0.8;
        }

        .group-name {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .badge {
          font-size: 10px;
          background: rgba(139, 92, 246, 0.2);
          color: var(--accent-color);
          padding: 2px 6px;
          border-radius: 10px;
          font-weight: 700;
        }

        .group-content {
          padding: 4px 0 8px 12px;
          display: flex;
          flex-direction: column;
          gap: 2px;
          border-left: 1px solid rgba(139, 92, 246, 0.2);
          margin-left: 18px;
        }

        .file-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 12px;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .file-item:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .file-item.active {
          color: var(--accent-color);
          background: rgba(139, 92, 246, 0.05);
        }

        .file-link {
          display: flex;
          align-items: center;
          gap: 8px;
          overflow: hidden;
        }

        .file-icon {
          color: var(--text-secondary);
          flex-shrink: 0;
        }

        .file-item.active .file-icon {
          color: var(--accent-color);
        }

        .file-item .filename {
          font-size: 12px;
          margin-bottom: 0;
        }

        .delete-btn.small {
          padding: 2px;
          opacity: 0;
        }

        .file-item:hover .delete-btn.small {
          opacity: 1;
        }

        .filename-container {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }

        .empty-state {
          font-size: 11px;
          color: #444;
          text-align: center;
          padding: 20px 0;
          border: 1px dashed #222;
          border-radius: 4px;
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

        .file-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;
        }

        .delete-btn {
          background: transparent;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .delete-btn:hover {
          color: #ef4444;
          background: rgba(239, 68, 68, 0.1);
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

        .session-context {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11px;
          color: var(--text-secondary);
        }

        .session-context .value {
          color: var(--accent-color);
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

        .right-sidebar {
          width: 240px;
          border-left: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
          padding: 24px;
          background: #080808;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .new-chat-btn {
          background: var(--surface-color);
          border: 1px solid var(--border-color);
          color: var(--text-primary);
          padding: 4px 8px;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .new-chat-btn:hover {
          border-color: var(--accent-color);
          color: var(--accent-color);
        }

        .session-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .session-item {
          padding: 10px 12px;
          background: transparent;
          border: 1px solid transparent;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: space-between;
          transition: all 0.2s;
        }

        .session-item:hover {
          background: #111;
          border-color: #222;
        }

        .session-item.active {
          background: rgba(139, 92, 246, 0.05);
          border-color: var(--accent-color);
          box-shadow: 0 0 10px rgba(139, 92, 246, 0.05);
        }

        .session-info {
          display: flex;
          align-items: center;
          gap: 8px;
          overflow: hidden;
        }

        .session-icon {
          color: var(--text-secondary);
          flex-shrink: 0;
        }

        .session-item.active .session-icon {
          color: var(--accent-color);
        }

        .session-name {
          font-size: 12px;
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .delete-session-btn {
          background: transparent;
          border: none;
          color: #333;
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          opacity: 0;
        }

        .session-item:hover .delete-session-btn {
          opacity: 1;
        }

        .delete-session-btn:hover {
          color: #ef4444;
          background: rgba(239, 68, 68, 0.1);
        }
      `}</style>
    </div>
  );
}
