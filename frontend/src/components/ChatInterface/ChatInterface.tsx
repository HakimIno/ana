"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { Terminal, Send, Trash2, Loader2, BarChart3, Zap, ShieldAlert } from "lucide-react";
import MetricsChart from "./MetricsChart";
import BrainFlow from "../Brainflow";
import { Message } from "@/types/chat";
import { chatService } from "@/services/api";
import "./styles/ChatInterface.css";

interface ChatInterfaceProps {
  activeFile: any;
  sessionId: string;
  onMessageSent: () => void;
}

export default function ChatInterface({ activeFile, sessionId, onMessageSent }: ChatInterfaceProps) {
  const queryClient = useQueryClient();
  const [input, setInput] = useState("");
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
      return chatService.postQuery(userMsg, activeFile?.filename, sessionId);
    },
    onMutate: async (userMsg) => {
      // 1. Cancel any outgoing refetches (so they don't overwrite our optimistic update)
      await queryClient.cancelQueries({ queryKey: ["chatHistory", sessionId] });

      // 2. Snapshot the previous value
      const previousMessages = queryClient.getQueryData<Message[]>(["chatHistory", sessionId]) || [];

      // 3. Optimistically update to the new value
      queryClient.setQueryData(["chatHistory", sessionId], [
        ...previousMessages,
        { role: "user", content: userMsg }
      ]);

      // 4. Return a context object with the snapshotted value
      return { previousMessages };
    },
    onError: (err, userMsg, context) => {
      // Rollback to previous state
      if (context?.previousMessages) {
        queryClient.setQueryData(["chatHistory", sessionId], context.previousMessages);
      }
      console.error("Query failed:", err);
      alert("Error sending message: " + (err instanceof Error ? err.message : "Internal Server Error"));
    },
    onSettled: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["chatHistory", sessionId] });
      onMessageSent();
    },
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isHistoryLoading, isSending]);

  const handleSend = async () => {
    if (!input.trim() || isSending) return;

    const userMsg = input;
    setInput("");
    setIsSending(true);

    try {
      await sendQueryMutation.mutateAsync(userMsg);
    } finally {
      setIsSending(false);
    }
  };

  const handleClear = async () => {
    if (isHistoryLoading || isSending) return;
    try {
      await chatService.deleteChatHistory(sessionId);
      queryClient.invalidateQueries({ queryKey: ["chatHistory", sessionId] });
      onMessageSent();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="terminal-chat">
      <div className="output-stream" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`terminal-line ${msg.role}`}>
            <span className="prompt-indicator">
              {msg.role === 'user' ? '>' : '┃'}
            </span>
            <div className="terminal-content">


              <div className="text-payload">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>

              {msg.data && (
                <div className="data-attachments">
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

                  {msg.data.key_metrics && Object.keys(msg.data.key_metrics).length > 0 && (
                    <div className="metrics-summary">
                      <p className="summary-title"><BarChart3 size={12} /> KEY_METRICS</p>
                      <div className="metrics-grid">
                        {Object.entries(msg.data.key_metrics).map(([key, val]: any) => (
                          <div key={key} className="metric-item">
                            <span className="key">{key}:</span>
                            <span className="val">{typeof val === 'object' ? val.mean?.toFixed(2) : val}</span>
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
            </div>
          </div>
        ))}
        {(isHistoryLoading || isSending) && (
          <div className="terminal-line ai loading">
            <span className="prompt-indicator">┃</span>
            <div className="terminal-content" style={{ display: 'flex', alignItems: 'center', height: '100px', overflow: 'hidden' }}>
              <BrainFlow size={100} />
            </div>
          </div>
        )}


        {/* <div className="tree-animation">
          <TreeDraw />
        </div> */}
      </div>

      <div className="prompt-area">
        <div className="input-strip">
          <span className="input-prompt">{activeFile ? 'ana ~' : 'system ~'}</span>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={activeFile ? "Enter command or query..." : "Please upload a data source..."}
            disabled={!activeFile || isSending}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            autoFocus
          />
          <div className="actions">
            <button className="icon-btn" onClick={handleClear} title="Clear Terminal">
              <Trash2 size={16} />
            </button>
            <button className="icon-btn primary" onClick={handleSend} disabled={!input.trim() || isSending}>
              {isSending ? <Loader2 size={16} className="spin" /> : <Terminal size={16} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
