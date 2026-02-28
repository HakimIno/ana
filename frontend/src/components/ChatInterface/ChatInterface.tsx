"use client";

import React, { useState, useRef, useEffect, memo, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Terminal, Search, Trash2, Send, Loader2, Pin, Paperclip, Maximize2, Minimize2, Check, X, Sparkles, Circle, FileDown, FileText } from "lucide-react";
import MetricsChart from "./MetricsChart";
import AnalysisTable from "./AnalysisTable";
import BrainFlow from "../Brainflow";
import { Message } from "@/types/chat";
import { chatService } from "@/services/api";
import styled from "@emotion/styled";
import "./styles/ChatInterface.css";

interface ChatInterfaceProps {
  activeFile: any;
  sessionId: string;
  onMessageSent: () => void;
  selectedModel?: string;
  files?: any[];
}

// --- Styled Components for Arc UI ---
const ChatWrapper = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  overflow: hidden;
  padding: 0 5%;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;

  .output-stream {
    flex: 1;
    overflow-y: auto;
    padding-bottom: 120px;
    scroll-behavior: smooth;
    
    &::-webkit-scrollbar { display: none; }
    -ms-overflow-style: none;  /* IE and Edge */
    scrollbar-width: none;  /* Firefox */
  }
`;

const MessageBlock = styled.div<{ role: string }>`
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  z-index: 1;

  ${props => props.role === 'user' ? `
    padding: 0 0 0 0;
    opacity: 0.8;
  ` : `
    padding: 14px 18px;
    border-radius: 14px;
    margin: 4px 0 16px 0;
  `}
`;

const ContentArea = styled.div<{ isAI: boolean }>`
  font-size: 15px;
  font-weight: 400;
  color: #111;
  letter-spacing: -0.01em;
  
  p { margin-bottom: 8px; }
  ul, ol { margin: 8px 0; padding-left: 18px; }
  li { margin-bottom: 4px; }

  code {
    background: rgba(0, 0, 0, 0.04);
    padding: 2px 5px;
    border-radius: 6px;
    font-family: var(--font-mono);
    font-size: 0.85em;
  }
`;

const DataTray = styled.div`
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.02);
`;

const ChatMessageItem = memo(({ msg }: { msg: Message }) => {
  const isAI = msg.role === 'assistant' || msg.role === 'ai';

  return (
    <MessageBlock role={msg.role}>
      <ContentArea isAI={isAI}>
        <div className="text-payload">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
        </div>

        {isAI && msg.data && (
          <DataTray>
            {msg.data.python_code && (
              <details className="arc-code-block" style={{ border: '1px solid rgba(0,0,0,0.03)', borderRadius: '10px', background: '#fcfcfc' }}>
                <summary style={{ padding: '8px 12px', fontSize: '10px', fontWeight: 700, cursor: 'pointer', color: '#ccc' }}>
                  LOGIC_TRACE
                </summary>
                <pre style={{ padding: '12px', background: '#fff', fontSize: '12.5px', overflowX: 'auto', borderTop: '1px solid rgba(0,0,0,0.01)' }}>
                  <code>{msg.data.python_code}</code>
                </pre>
              </details>
            )}

            {(msg.data?.charts || []).map((chart: any, idx: number) => (
              <MetricsChart
                key={idx}
                data={chart.data}
                title={chart.title}
                type={chart.type}
              />
            ))}

            {msg.data.table_data && (
              <AnalysisTable data={msg.data.table_data} />
            )}

            {msg.data.key_metrics && Object.keys(msg.data.key_metrics).length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                {Object.entries(msg.data.key_metrics).map(([key, val]: any) => (
                  <div key={key} style={{ padding: '12px', borderRadius: '10px', background: 'rgba(0,0,0,0.01)' }}>
                    <div style={{ fontSize: '8px', fontWeight: 700, color: '#bbb', textTransform: 'uppercase' }}>{key}</div>
                    <div style={{ fontSize: '18px', fontWeight: 600, marginTop: '2px', color: '#222' }}>
                      {typeof val === 'number' ? new Intl.NumberFormat().format(val) : val}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {msg.data.generated_file && (() => {
              const fileUrl = msg.data.generated_file.startsWith('data:')
                ? msg.data.generated_file
                : `http://localhost:8000${msg.data.generated_file}`;
              return (
                <a
                  href={fileUrl}
                  download="report.pdf"
                  style={{
                    color: 'oklch(51.1% 0.262 276.966)',
                    fontSize: 12,
                  }}
                  onMouseOver={(e) => e.currentTarget.style.opacity = '0.9'}
                  onMouseOut={(e) => e.currentTarget.style.opacity = '1'}
                >
                  <FileDown size={14} />
                  ดาวน์โหลดรายงาน PDF
                </a>
              );
            })()}
          </DataTray >
        )}
      </ContentArea >
    </MessageBlock >
  );
});

ChatMessageItem.displayName = "ChatMessageItem";

// --- Styled Components for Floating Input ---
const FloatingInputArea = styled.div`
  position: sticky;
  bottom: 24px;
  width: 100%;
  z-index: 1000;
  margin-top: 48px;
`;

const InputPill = styled.div`
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 24px;
  padding: 4px 4px 4px 24px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:focus-within {
    border-color: rgba(0, 0, 0, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    background: #fff;
  }
`;

const StyledInput = styled.input`
  flex: 1;
  background: transparent;
  border: none;
  padding: 4px 0;
  font-size: 15px;
  color: #000;
  outline: none;
  font-family: var(--font-sans);
  font-weight: 400;
  border-radius: 100px;
  &::placeholder { color: #bbb; font-weight: 400; }
`;

const ActionBtn = styled.button`
  background: #000;
  color: #fff;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover:not(:disabled) { 
    transform: translateY(-1px); 
    background: #222; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
  &:active:not(:disabled) { transform: scale(0.96); }
  &:disabled { opacity: 0.1; cursor: not-allowed; }
`;

const InputMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-left: 20px;
  font-size: 10px;
  font-weight: 800;
  color: #bbb;
  text-transform: uppercase;
  letter-spacing: 0.1em;
`;

const ChatInput = memo(({
  activeFile,
  isSending,
  onSend,
  onClear,
  onExport,
  isExporting,
  files = []
}: {
  activeFile: any,
  isSending: boolean,
  onSend: (msg: string) => void,
  onClear: () => void,
  onExport: () => void,
  isExporting: boolean,
  files?: any[]
}) => {
  const [input, setInput] = useState("");
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);
  const [mentionIndex, setMentionIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  // Get base files matching query
  let filteredFiles = files.filter(f =>
    mentionQuery !== null && f.filename.toLowerCase().includes(mentionQuery.toLowerCase())
  );

  // If default templates aren't explicitly in the uploaded files, add them as options
  const defaultTemplates = ["branch_report.typ", "mega_report.typ"];
  if (mentionQuery !== null) {
    defaultTemplates.forEach(template => {
      if (
        template.includes(mentionQuery.toLowerCase()) &&
        !filteredFiles.some(f => f.filename === template)
      ) {
        filteredFiles.push({ filename: template, isTemplate: true });
      }
    });
  }

  // Also map existing .typ files to mark them as templates
  const suggestedFiles = filteredFiles.map(f => ({
    ...f,
    isTemplate: f.isTemplate || f.filename.endsWith('.typ')
  })).slice(0, 5); // Max 5 suggestions

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInput(val);

    // Basic regex to find `@` followed by any characters until a space or end of string, right before cursor
    const cursor = e.target.selectionStart || 0;
    const textBeforeCursor = val.slice(0, cursor);

    // Look for @ at the end of the string, optionally followed by non-space chars
    const match = textBeforeCursor.match(/@([^\s]*)$/);

    if (match) {
      setMentionQuery(match[1]); // match[1] will be "" if just "@" was typed
      if (mentionQuery === null) {
        setMentionIndex(0); // Only reset selection if we just opened the menu
      }
    } else {
      setMentionQuery(null);
    }
  };

  const insertMention = (filename: string) => {
    if (!inputRef.current) return;
    const cursor = inputRef.current.selectionStart || 0;
    const textBeforeCursor = input.slice(0, cursor);
    const textAfterCursor = input.slice(cursor);

    // Find the `@` we are completing
    const match = textBeforeCursor.match(/@([^\s]*)$/);
    if (match) {
      const mentionStart = cursor - match[0].length;
      const newTextBefore = input.slice(0, mentionStart) + `@${filename} `;
      setInput(newTextBefore + textAfterCursor);
      // We can't immediately set cursor here syncly, but it's fine
    }
    setMentionQuery(null);
    inputRef.current.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Handle mention suggestions navigation
    if (mentionQuery !== null && suggestedFiles.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setMentionIndex(prev => Math.min(prev + 1, suggestedFiles.length - 1));
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setMentionIndex(prev => Math.max(prev - 1, 0));
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        if (suggestedFiles[mentionIndex]) {
          insertMention(suggestedFiles[mentionIndex].filename);
        } else {
          insertMention(suggestedFiles[0].filename);
        }
        return;
      }
      if (e.key === 'Escape') {
        setMentionQuery(null);
        return;
      }
    }

    if (e.key === 'Enter' && input.trim() && !isSending) {
      onSend(input);
      setInput("");
      setMentionQuery(null);
    }
  };

  const handleBtnSend = () => {
    if (input.trim() && !isSending) {
      onSend(input);
      setInput("");
    }
  };

  return (
    <FloatingInputArea>
      <InputMeta>
        <Circle size={4} fill={activeFile ? "#000" : "#ddd"} stroke="none" />
        <span>{activeFile ? "Agent active • session_linked" : "Agent standby • select source"}</span>
      </InputMeta>
      <InputPill style={{ position: 'relative' }}>
        {/* Mention Dropdown */}
        {mentionQuery !== null && suggestedFiles.length > 0 && (
          <div style={{
            position: 'absolute', bottom: '100%', left: '20px', marginBottom: '8px',
            background: '#fff', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(0,0,0,0.1)', overflow: 'hidden', padding: '4px',
            zIndex: 2000, width: '250px'
          }}>
            <div style={{ fontSize: '10px', fontWeight: 700, color: '#bbb', margin: '4px 8px', textTransform: 'uppercase' }}>ไฟล์ที่อัปโหลดไว้</div>
            {suggestedFiles.map((f, i) => (
              <div
                key={f.filename}
                style={{
                  padding: '6px 8px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '6px',
                  background: i === mentionIndex
                    ? (f.isTemplate ? 'rgba(168, 85, 247, 0.1)' : '#f0f0f0')
                    : 'transparent',
                  color: f.isTemplate ? '#9333ea' : '#333',
                  fontWeight: i === mentionIndex ? 600 : 400
                }}
                onMouseDown={(e) => { e.preventDefault(); insertMention(f.filename); }}
                onMouseEnter={() => setMentionIndex(i)}
              >
                <FileText size={12} color={f.isTemplate ? "#9333ea" : (i === mentionIndex ? "#000" : "#888")} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {f.filename}
                  {f.isTemplate && <span style={{ fontSize: '9px', marginLeft: '6px', padding: '2px 4px', background: 'rgba(168, 85, 247, 0.15)', borderRadius: '4px', fontWeight: 700 }}>TEMPLATE</span>}
                </span>
              </div>
            ))}
          </div>
        )}

        <StyledInput
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder={activeFile ? "Ask ana.arc anything (type @ for files)..." : "Please link a data source..."}
          disabled={!activeFile || isSending}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        <div style={{ display: 'flex', gap: '4px' }}>
          <button onClick={onExport} disabled={isExporting} style={{ background: 'transparent', border: 'none', color: '#aaa', padding: '10px', cursor: 'pointer' }} title="Export PDF">
            {isExporting ? <Loader2 size={16} className="spin" /> : <FileDown size={16} />}
          </button>
          <button onClick={onClear} style={{ background: 'transparent', border: 'none', color: '#aaa', padding: '10px', cursor: 'pointer' }} title="Reset">
            <Trash2 size={16} />
          </button>
          <ActionBtn onClick={handleBtnSend} disabled={!input.trim() || isSending}>
            {isSending ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
          </ActionBtn>
        </div>
      </InputPill>
    </FloatingInputArea>
  );
});


ChatInput.displayName = "ChatInput";

export default function ChatInterface({ activeFile, sessionId, onMessageSent, selectedModel, files }: ChatInterfaceProps) {
  const queryClient = useQueryClient();
  const [isSending, setIsSending] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [streamStatus, setStreamStatus] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messages = [], isLoading: isHistoryLoading } = useQuery({
    queryKey: ["chatHistory", sessionId],
    queryFn: async () => {
      const history = await chatService.getChatHistory(sessionId);

      return history;
    },
    staleTime: 1000 * 60,
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isHistoryLoading, isSending]);

  const handleSend = useCallback(async (userMsg: string) => {
    if (!userMsg.trim() || isSending) return;
    setIsSending(true);
    setStreamStatus("Analyzing...");

    // Add user message + placeholder AI message immediately
    const currentMessages = queryClient.getQueryData<Message[]>(["chatHistory", sessionId]) || [];
    const userMessage: Message = { role: "user", content: userMsg };
    const aiPlaceholder: Message = { role: "assistant", content: "" };
    queryClient.setQueryData(["chatHistory", sessionId], [...currentMessages, userMessage, aiPlaceholder]);

    try {
      const response = await chatService.postQuery(
        userMsg,
        activeFile?.type === 'file' ? activeFile?.filename : undefined,
        sessionId,
        activeFile?.type === 'group' ? activeFile?.group : undefined,
        undefined, // filenames
        selectedModel,
      );

      // Set final message with full data (includes charts, metrics, etc.)
      queryClient.setQueryData(["chatHistory", sessionId], (prev: Message[] | undefined) => {
        if (!prev) return prev;
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: response.answer || "Analysis complete.",
          data: response,
        };
        return updated;
      });
    } catch (err) {
      queryClient.setQueryData(["chatHistory", sessionId], (prev: Message[] | undefined) => {
        if (!prev) return prev;
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: `⚠️ Error: ${err instanceof Error ? err.message : "Unknown error"}`,
        };
        return updated;
      });
    } finally {
      setIsSending(false);
      setStreamStatus("");
      onMessageSent();
    }
  }, [isSending, activeFile, sessionId, queryClient, onMessageSent, selectedModel]);

  const handleClear = useCallback(async () => {
    if (isHistoryLoading || isSending) return;
    try {
      await chatService.deleteChatHistory(sessionId);
      queryClient.invalidateQueries({ queryKey: ["chatHistory", sessionId] });
      onMessageSent();
    } catch (err) {
      console.error(err);
    }
  }, [isHistoryLoading, isSending, sessionId, queryClient, onMessageSent]);

  const handleExportPdf = useCallback(async () => {
    if (messages.length === 0 || isExporting) return;

    setIsExporting(true);
    try {
      // Find the latest message that has data
      const latestDataMsg = [...messages].reverse().find(m => m.data);

      const pydanticMessages = messages.map(m => ({
        role: m.role === 'ai' ? 'assistant' : m.role,
        content: m.content
      }));

      const payload = {
        title: "Analysis Report",
        messages: pydanticMessages,
        analysis_data: latestDataMsg?.data?.table_data || [],
        metrics: latestDataMsg?.data?.key_metrics || {}
      };

      const response = await fetch("http://localhost:8000/export/pdf", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error("Export failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = "analysis_export.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error exporting PDF:", error);
      alert("Failed to export PDF.");
    } finally {
      setIsExporting(false);
    }
  }, [messages, isExporting]);

  return (
    <ChatWrapper>
      <div className="output-stream" ref={scrollRef}>
        {messages.map((msg, i) => (
          <ChatMessageItem key={`${msg.role}-${i}`} msg={msg} />
        ))}
        {isHistoryLoading && (
          <div className="status-overlay" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '200px', justifyContent: 'center' }}>
            <BrainFlow size={80} />
            <div className="status-text-loop">Waking up ana...</div>
          </div>
        )}
        {isSending && (
          <div className="stream-indicator" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '4px 0', color: 'var(--text-primary)' }}>
            <BrainFlow size={22} />
            <div className="stream-status-text">
              <span className="stream-status-label" style={{ fontWeight: 800, fontSize: '10px', textTransform: 'uppercase', color: 'inherit' }}>{streamStatus || "Thinking..."}</span>
            </div>
          </div>
        )}
      </div>

      <ChatInput
        activeFile={activeFile}
        isSending={isSending}
        onSend={handleSend}
        onClear={handleClear}
        onExport={handleExportPdf}
        isExporting={isExporting}
        files={files}
      />
    </ChatWrapper>
  );
}

