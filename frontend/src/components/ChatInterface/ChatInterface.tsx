"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Terminal, Send, Trash2, Loader2, BarChart3, Zap, ShieldAlert } from "lucide-react";
import MetricsChart from "./MetricsChart";
import BrainFlow from "../Brainflow";
import { Message } from "@/types/chat";
import { chatService } from "@/services/api";
import "./styles/ChatInterface.css";

interface ChatInterfaceProps {
  activeFile: any;
}

export default function ChatInterface({ activeFile }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "ai",
      content: "System initialized. Listening for data streams or analytical queries."
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const history = await chatService.getChatHistory();
        if (history && history.length > 0) {
          setMessages(history);
        }
      } catch (err) {
        console.error("Failed to fetch chat history:", err);
      }
    };
    fetchHistory();
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg = input;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setIsLoading(true);

    try {
      const data = await chatService.postQuery(userMsg);
      setMessages(prev => [...prev, { role: "ai", content: data.answer, data: data }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: "ai", content: "Error: " + (err.response?.data?.message || err.message) }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    if (isLoading) return;
    try {
      await chatService.deleteChatHistory();
      setMessages([{ role: "ai", content: "History cleared. Waiting for input." }]);
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
        {isLoading && (
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
            disabled={!activeFile || isLoading}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            autoFocus
          />
          <div className="actions">
            <button className="icon-btn" onClick={handleClear} title="Clear Terminal">
              <Trash2 size={16} />
            </button>
            <button className="icon-btn primary" onClick={handleSend} disabled={!input.trim() || isLoading}>
              {isLoading ? <Loader2 size={16} className="spin" /> : <Terminal size={16} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
