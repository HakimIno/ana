"use client";

import React, { useState, useRef, useEffect, memo, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { Terminal, Search, Trash2, Send, Loader2, Pin, Paperclip, Maximize2, Minimize2, Check, X, Sparkles, Circle } from "lucide-react";
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
}

// --- Styled Components for Arc UI ---
const ChatWrapper = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0 5%;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
  position: relative;
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
  border-top: 1px solid rgba(0,0,0,0.02);
`;

const ChatMessageItem = memo(({ msg }: { msg: Message }) => {
  const isAI = msg.role === 'assistant' || msg.role === 'ai';

  return (
    <MessageBlock role={msg.role}>
      <ContentArea isAI={isAI}>
        <div className="text-payload">
          <ReactMarkdown>{msg.content}</ReactMarkdown>
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
          </DataTray>
        )}
      </ContentArea>
    </MessageBlock>
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
  onClear
}: {
  activeFile: any,
  isSending: boolean,
  onSend: (msg: string) => void,
  onClear: () => void
}) => {
  const [input, setInput] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim() && !isSending) {
      onSend(input);
      setInput("");
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
      <InputPill>
        <StyledInput
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={activeFile ? "Ask ana.arc anything..." : "Please link a data source..."}
          disabled={!activeFile || isSending}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        <div style={{ display: 'flex', gap: '4px' }}>
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

export default function ChatInterface({ activeFile, sessionId, onMessageSent, selectedModel }: ChatInterfaceProps) {
  const queryClient = useQueryClient();
  const [isSending, setIsSending] = useState(false);
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
      />
    </ChatWrapper>
  );
}

