"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import FileUpload from "@/components/FileUpload/FileUpload";
import ChatInterface from "@/components/ChatInterface/ChatInterface";
import Tree5 from "@/components/Tree5";
import Image from "next/image";
import {
  Trash2, Plus, MessageSquare,
  FileText, PanelLeftClose, ChevronDown as ChevDown,
  Sparkles, Circle, LayoutGrid, Layout
} from "lucide-react";
import { chatService } from "@/services/api";
import "./page.css";

export default function Home() {
  const queryClient = useQueryClient();
  const [activeFile, setActiveFile] = useState<any>(null);
  const [activeSessionId, setActiveSessionId] = useState<string>("default");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    if (typeof window !== "undefined") return localStorage.getItem("selectedModel") || "gpt-4o";
    return "gpt-4o";
  });
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const modelMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (modelMenuRef.current && !modelMenuRef.current.contains(e.target as Node)) {
        setModelMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const toggleGroup = (groupName: string) => {
    setExpandedGroups(prev => {
      const next = new Set(prev);
      if (next.has(groupName)) next.delete(groupName);
      else next.add(groupName);
      return next;
    });
  };

  const { data: files = [] } = useQuery({
    queryKey: ["files"],
    queryFn: async () => {
      const res = await fetch("http://localhost:8000/files");
      if (!res.ok) throw new Error("Failed to fetch files");
      return res.json();
    }
  });

  const { data: sessions = [] } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => chatService.listSessions()
  });

  const { data: availableModels = [] } = useQuery({
    queryKey: ["models"],
    queryFn: () => chatService.listModels(),
    staleTime: 1000 * 60 * 5,
  });

  const handleSelectModel = (modelId: string) => {
    setSelectedModel(modelId);
    if (typeof window !== "undefined") localStorage.setItem("selectedModel", modelId);
    setModelMenuOpen(false);
  };

  const deleteFileMutation = useMutation({
    mutationFn: async (filename: string) => {
      const res = await fetch(`http://localhost:8000/files/${filename}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete file");
      return filename;
    },
    onSuccess: (filename) => {
      queryClient.invalidateQueries({ queryKey: ["files"] });
      if (activeFile?.filename === filename) setActiveFile(null);
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => chatService.deleteChatHistory(sessionId),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      if (activeSessionId === sessionId) setActiveSessionId("default");
    },
  });

  const handleCreateSession = () => {
    const newId = `session_${Date.now()}`;
    setActiveSessionId(newId);
  };

  const handleDeleteFile = (e: React.MouseEvent, filename: string) => {
    e.stopPropagation();
    if (confirm(`Delete ${filename}?`)) deleteFileMutation.mutate(filename);
  };

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (confirm(`Delete chat history for "${sessionId}"?`)) deleteSessionMutation.mutate(sessionId);
  };

  const currentModel = availableModels.find((m: any) => m.id === selectedModel);
  const ungroupedFiles = files.filter((f: any) => !f.group);
  const groupNames = Array.from(new Set(files.map((f: any) => f.group).filter(Boolean))).sort() as string[];

  return (
    <div className="arc-shell">
      {/* ── ARC SIDEBAR (Glassy) ── */}
      <aside className={`arc-sidebar arc-glass ${sidebarOpen ? "" : "arc-sidebar--collapsed"}`}>

        {/* Header/Brand */}
        <div className="arc-sidebar-header">
          <div className="arc-logo">
            <Image src="/book.gif" alt="Logo" width={24} height={24} unoptimized />
            <span>ana.arc</span>
          </div>
          <button className="arc-btn-icon" onClick={() => setSidebarOpen(false)}>
            <PanelLeftClose size={14} />
          </button>
        </div>

        {/* Global Nav */}
        <div className="arc-nav-scroller">

          <div className="arc-nav-section">
            <div className="arc-nav-title">Assets</div>
            <div className="arc-upload-wrapper">
              <FileUpload onUploadSuccess={(fileInfo) => {
                queryClient.invalidateQueries({ queryKey: ["files"] });
                setActiveFile(fileInfo);
              }} />
            </div>

            {/* Group Chips */}
            {groupNames.length > 0 && (
              <div className="arc-group-chips">
                {/* "All" chip — clear group filter */}
                <button
                  className={`arc-chip ${!activeFile || activeFile.type !== "group" ? "arc-chip--all" : ""}`}
                  onClick={() => setActiveFile(null)}
                >
                  All
                </button>
                {groupNames.map((g) => (
                  <button
                    key={g}
                    className={`arc-chip ${activeFile?.type === "group" && activeFile?.group === g ? "arc-chip--active" : ""}`}
                    onClick={() => setActiveFile({ group: g, type: "group", filename: g })}
                  >
                    {g}
                    <span className="arc-chip-count">
                      {files.filter((f: any) => f.group === g).length}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {/* File list — shows group files or ungrouped files */}
            <div className="arc-file-list">
              {(activeFile?.type === "group"
                ? files.filter((f: any) => f.group === activeFile.group)
                : ungroupedFiles.length > 0
                  ? ungroupedFiles
                  : groupNames.length > 0
                    ? files  // show all if no group is selected and no ungrouped files
                    : []
              ).map((file: any) => (
                <div
                  key={file.filename}
                  className={`arc-file-row ${activeFile?.type === "file" && activeFile?.filename === file.filename ? "is-active" : ""}`}
                  onClick={() => setActiveFile({ ...file, type: "file" })}
                >
                  <FileText size={12} className="arc-file-icon" />
                  <span className="arc-file-name">{file.filename.replace(/\.(csv|xlsx|xls)$/i, "")}</span>
                  <button
                    className="arc-file-delete"
                    onClick={(e) => handleDeleteFile(e, file.filename)}
                    title={`Delete ${file.filename}`}
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="arc-nav-section">
            <div className="arc-nav-title">
              <span>Conversations</span>
              <button className="mini-plus" onClick={handleCreateSession}><Plus size={12} /></button>
            </div>
            <div className="arc-list">
              <div
                className={`arc-item ${activeSessionId === "default" ? "is-active" : ""}`}
                onClick={() => setActiveSessionId("default")}
              >
                <Layout size={14} />
                <span className="label">Main Canvas</span>
              </div>

              {sessions.filter((s: any) => s.session_id !== "default").map((session: any) => (
                <div
                  key={session.session_id}
                  className={`arc-item ${activeSessionId === session.session_id ? "is-active" : ""}`}
                  onClick={() => setActiveSessionId(session.session_id)}
                >
                  <MessageSquare size={14} />
                  <span className="label">{session.session_id.replace("session_", "Chat ")}</span>
                  <button className="delete-btn" onClick={(e) => handleDeleteSession(e, session.session_id)}>
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="arc-sidebar-footer">
          <Tree5 />
        </div>
      </aside>

      {/* ── FLOATING WINDOW ── */}
      <main className="arc-window">

        {/* Window Top Bar */}
        <header className="arc-window-header">
          <div className="arc-header-left">
            {!sidebarOpen && (
              <button className="arc-btn-icon" onClick={() => setSidebarOpen(true)}>
                <LayoutGrid size={18} />
              </button>
            )}
            <div className="arc-window-status">
              <Circle size={6} fill={activeFile ? "#000" : "#ddd"} stroke="none" />
              <span>{activeFile ? activeFile.filename?.split("/").pop() : "standby"}</span>
            </div>
          </div>

          <div className="arc-header-center" ref={modelMenuRef}>
            <button className="arc-model-pill" onClick={() => setModelMenuOpen(!modelMenuOpen)}>
              <Sparkles size={13} className="sparkle-icon" />
              <span>{currentModel?.label || selectedModel}</span>
              <ChevDown size={11} className={`chev ${modelMenuOpen ? 'up' : ''}`} />
            </button>

            {modelMenuOpen && (
              <div className="arc-model-menu arc-card">
                {availableModels.map((m: any) => (
                  <button
                    key={m.id}
                    className={`arc-menu-item ${selectedModel === m.id ? "is-active" : ""}`}
                    onClick={() => handleSelectModel(m.id)}
                  >
                    <span className="name">{m.label}</span>
                    <span className="dot" />
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="arc-header-right">
            {/* Additional actions if needed */}
          </div>
        </header>

        {/* Canvas Area */}
        <div className="arc-canvas-scroller">
          <ChatInterface
            activeFile={activeFile}
            sessionId={activeSessionId}
            onMessageSent={() => queryClient.invalidateQueries({ queryKey: ["sessions"] })}
            selectedModel={selectedModel}
          />
        </div>
      </main>
    </div>
  );
}
