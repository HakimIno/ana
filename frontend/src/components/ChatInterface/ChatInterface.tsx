"use client";

import React, { useState, useRef, useEffect, memo, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { Terminal, Send, Trash2, Loader2, BarChart3, Zap, ShieldAlert } from "lucide-react";
import MetricsChart from "./MetricsChart";
import AnalysisTable from "./AnalysisTable";
import BrainFlow from "../Brainflow";
import { Message } from "@/types/chat";
import { chatService } from "@/services/api";
import "./styles/ChatInterface.css";

interface ChatInterfaceProps {
  activeFile: any;
  sessionId: string;
  onMessageSent: () => void;
}

// 1. Memoized Message Component to prevent re-rendering old charts/markdown
const ChatMessageItem = memo(({ msg }: { msg: Message }) => {
  return (
    <div className={`terminal-line ${msg.role === 'assistant' ? 'ai' : msg.role}`}>
      <span className="prompt-indicator">
        {msg.role === 'user' ? '>' : '┃'}
      </span>
      <div className="terminal-content">
        <div className="text-payload">
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        </div>

        {msg.data && (
          <div className="data-attachments">
            {msg.data.python_code && (
              <details className="code-execution-block" open={false}>
                <summary className="code-header">
                  <Terminal size={10} /> Code Execution Log
                  <span className="accordion-hint">(Click to expand logic)</span>
                </summary>
                <pre>
                  <code>{msg.data.python_code}</code>
                </pre>
              </details>
            )}

            {(msg.data.charts || []).map((chart: any, idx: number) => (
              <div key={idx} className="chart-wrapper">
                <MetricsChart
                  data={chart.data}
                  title={chart.title}
                  type={chart.type}
                />
              </div>
            ))}



            {msg.data.chart_data && msg.data.chart_data.length > 0 && !(msg.data.charts?.length) && (
              <div className="chart-wrapper">
                <MetricsChart data={msg.data.chart_data} title={msg.data.title} />
              </div>
            )}



            {msg.data.table_data && (
              <AnalysisTable data={msg.data.table_data} />
            )}

            {msg.data.key_metrics && Object.keys(msg.data.key_metrics).length > 0 && (
              <div className="metrics-summary-container">
                <div className="metrics-grid">
                  {Object.entries(msg.data.key_metrics).map(([key, val]: any) => (
                    <div key={key} className="kpi-card">
                      <div className="kpi-label">{key.replace(/_/g, ' ')}</div>
                      <div className="kpi-value">
                        {typeof val === 'number'
                          ? new Intl.NumberFormat('th-TH').format(val)
                          : (typeof val === 'object' ? val.mean?.toFixed(2) : val)
                        }
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {msg.data.recommendations?.length > 0 && (
              <div className="insight-block recommendations">
                <p className="summary-title"><Zap size={12} /> STRATEGIC_ACTION</p>
                <ul>
                  {msg.data.recommendations.map((rec: string, idx: number) => (
                    <li key={idx}>- {rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {msg.data.risks?.length > 0 && (
              <div className="insight-block risks">
                <p className="summary-title"><ShieldAlert size={12} /> RISK_DETECTED</p>
                <ul>
                  {msg.data.risks.map((risk: string, idx: number) => (
                    <li key={idx}>- {risk}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {(msg.role === 'ai' || msg.role === 'assistant') && msg.data?.token_usage && (
          <div className="token-usage-footer">
            <span className="token-stat">
              <Zap size={10} className="token-icon" />
              Tokens: {msg.data.token_usage.total_tokens} (P: {msg.data.token_usage.prompt_tokens} | C: {msg.data.token_usage.completion_tokens})
            </span>
          </div>
        )}
      </div>
    </div>
  );
});

ChatMessageItem.displayName = "ChatMessageItem";

// 2. Isolated Input Component to keep typing state local
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
    <div className="prompt-area">
      <div className="input-strip">
        <span className="input-prompt">{activeFile ? 'ana ~' : 'system ~'}</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={activeFile ? "Enter command or query..." : "Please select a Project or File to begin..."}
          disabled={!activeFile || isSending}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        <div className="actions">
          <button className="icon-btn" onClick={onClear} title="Clear Terminal">
            <Trash2 size={16} />
          </button>
          <button
            className="icon-btn primary"
            onClick={handleBtnSend}
            disabled={!input.trim() || isSending}
          >
            {isSending ? <Loader2 size={16} className="spin" /> : <Terminal size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
});

ChatInput.displayName = "ChatInput";

export default function ChatInterface({ activeFile, sessionId, onMessageSent }: ChatInterfaceProps) {
  const queryClient = useQueryClient();
  const [isSending, setIsSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messages = [], isLoading: isHistoryLoading } = useQuery({
    queryKey: ["chatHistory", sessionId],
    queryFn: async () => {
      const history = await chatService.getChatHistory(sessionId);
      if (!history || history.length === 0) {
        return [{
          role: "ai" as const,
          content: "Session initialized. Ready for analysis."
        }];
      }
      return history;
    },
    staleTime: 1000 * 60, // 1 minute
  });

  const sendQueryMutation = useMutation({
    mutationFn: async (userMsg: string) => {
      return chatService.postQuery(
        userMsg,
        activeFile?.type === 'file' ? activeFile?.filename : undefined,
        sessionId,
        activeFile?.type === 'group' ? activeFile?.group : undefined
      );
    },
    onMutate: async (userMsg) => {
      await queryClient.cancelQueries({ queryKey: ["chatHistory", sessionId] });
      const previousMessages = queryClient.getQueryData<Message[]>(["chatHistory", sessionId]) || [];
      queryClient.setQueryData(["chatHistory", sessionId], [
        ...previousMessages,
        { role: "user", content: userMsg }
      ]);
      return { previousMessages };
    },
    onError: (err, userMsg, context) => {
      if (context?.previousMessages) {
        queryClient.setQueryData(["chatHistory", sessionId], context.previousMessages);
      }
      console.error("Query failed:", err);
      alert("Error sending message: " + (err instanceof Error ? err.message : "Internal Server Error"));
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["chatHistory", sessionId] });
      onMessageSent();
    },
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isHistoryLoading, isSending]);

  const handleSend = useCallback(async (userMsg: string) => {
    if (!userMsg.trim() || isSending) return;
    setIsSending(true);
    try {
      await sendQueryMutation.mutateAsync(userMsg);
    } finally {
      setIsSending(false);
    }
  }, [isSending, sendQueryMutation]);

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
    <div className="terminal-chat">
      <div className="output-stream" ref={scrollRef}>
        {messages.map((msg, i) => (
          <ChatMessageItem key={i} msg={msg} />
        ))}
        {(isHistoryLoading || isSending) && (
          <div className="terminal-line ai loading">
            <span className="prompt-indicator">┃</span>
            <div className="terminal-content" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', height: '140px', justifyContent: 'center' }}>
              <BrainFlow size={80} />
              <div className="status-text-loop">
                {isHistoryLoading ? "Recovering session memory..." : "Programmatic analysis in progress..."}
              </div>
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
    </div>
  );
}
