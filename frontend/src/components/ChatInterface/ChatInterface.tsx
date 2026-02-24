"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Terminal, Send, Trash2, Loader2, BarChart3, Zap, ShieldAlert } from "lucide-react";
import MetricsChart from "./MetricsChart";
import BrainFlow from "../Brainflow";

interface Message {
  role: "user" | "ai";
  content: string;
  data?: any;
}

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
        const response = await fetch("http://localhost:8000/chat/history?session_id=default");
        if (response.ok) {
          const history = await response.json();
          if (history && history.length > 0) {
            setMessages(history);
          }
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
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg }),
      });

      if (!response.ok) throw new Error("Connection failed");

      const data = await response.json();
      setMessages(prev => [...prev, { role: "ai", content: data.answer, data: data }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: "ai", content: "Error: " + err.message }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    if (isLoading) return;
    try {
      await fetch("http://localhost:8000/chat/history?session_id=default", { method: "DELETE" });
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

      <style jsx>{`
        .terminal-chat {
          height: 100%;
          display: flex;
          flex-direction: column;
          background: var(--bg-color);
          font-family: var(--font-mono);
          position: relative;
        }

        .output-stream {
          flex: 1;
          overflow-y: auto;
          padding: 40px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .terminal-line {
          display: flex;
          gap: 16px;
        }

        .prompt-indicator {
          font-weight: bold;
          flex-shrink: 0;
          padding-top: 2px;
        }

        .user .prompt-indicator { color: var(--accent-color); }
        .ai .prompt-indicator { color: var(--text-secondary); opacity: 0.5; }

        .terminal-content {
          flex: 1;
          font-size: 14px;
          line-height: 1.6;
          color: var(--text-primary);
        }

        .user .text-payload {
          color: var(--text-primary);
          font-weight: 500;
        }

        .data-attachments {
          margin-top: 20px;
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .chart-wrapper {
          background: #000;
          border: 1px solid var(--border-color);
          padding: 10px;
          border-radius: 4px;
        }

        .summary-title {
          font-size: 11px;
          font-weight: 700;
          color: var(--text-secondary);
          margin-bottom: 12px;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 12px;
          margin-top: 10px;
        }

        .metric-item {
          display: flex;
          flex-direction: column;
          gap: 6px;
          background: #0a0a0a;
          border: 1px solid #1a1a1a;
          padding: 12px 16px;
          border-radius: 4px;
          transition: all 0.2s ease;
        }

        .metric-item:hover {
          border-color: var(--accent-color);
          background: #111;
          transform: translateY(-2px);
        }
    
        .metric-item .key { 
          color: var(--text-secondary); 
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }
        .metric-item .val { 
          color: var(--accent-color); 
          font-weight: 600; 
          font-size: 16px;
          font-family: var(--font-mono);
        }

        .insight-block ul {
          list-style: none;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .insight-block li {
          font-size: 13px;
          color: var(--text-primary);
        }

        .recommendations .summary-title { color: var(--accent-color); }
        .risks .summary-title { color: var(--error); }

        .ai-thought-process {
          background: rgba(var(--accent-rgb), 0.05);
          border-left: 2px solid var(--accent-color);
          padding: 8px 12px;
          margin-bottom: 12px;
          font-size: 11px;
          color: var(--text-secondary);
          animation: revealAndFade 6s forwards;
          border-radius: 0 4px 4px 0;
          overflow: hidden;
        }

        .thought-header {
          display: flex;
          align-items: center;
          gap: 6px;
          font-weight: bold;
          font-size: 9px;
          letter-spacing: 0.1em;
          margin-bottom: 4px;
          color: var(--accent-color);
        }

        .pulse-icon {
          animation: pulse 1.5s infinite;
        }

        @keyframes revealAndFade {
          0% { opacity: 0; max-height: 0; transform: translateY(-10px); }
          10% { opacity: 0.8; max-height: 200px; transform: translateY(0); }
          80% { opacity: 0.8; max-height: 200px; }
          100% { opacity: 0; max-height: 0; margin-bottom: 0; padding: 0; }
        }

        .thinking {
          color: var(--accent-color);
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .thinking::after {
          content: '...';
          animation: dots 1.5s steps(5, end) infinite;
          width: 20px;
        }

        @keyframes dots {
          0%, 20% { content: '.'; }
          40% { content: '..'; }
          60% { content: '...'; }
        }

        @keyframes pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }

        .prompt-area {
          padding: 20px 40px 40px;
          background: linear-gradient(transparent, var(--bg-color) 40%);
        }

        .input-strip {
          display: flex;
          align-items: center;
          gap: 12px;
          background: var(--surface-color);
          border: 1px solid var(--border-color);
          padding: 8px 16px;
          border-radius: 4px;
        }

        .input-prompt {
          color: var(--accent-color);
          font-weight: 600;
          font-size: 13px;
          white-space: nowrap;
        }

        input {
          flex: 1;
          background: transparent !important;
          border: none !important;
          padding: 8px 0 !important;
          font-size: 14px;
          color: white;
          outline: none;
        }

        .actions {
          display: flex;
          gap: 8px;
        }

        .icon-btn {
          background: transparent;
          border: none;
          color: var(--text-secondary);
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .icon-btn:hover:not(:disabled) {
          background: #1a1a1a;
          color: white;
        }

        .icon-btn.primary {
          color: var(--accent-color);
        }

        .icon-btn.primary:hover:not(:disabled) {
          background: var(--accent-color);
          color: white;
        }

        .icon-btn:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        /* Custom Scrollbar */
        .output-stream::-webkit-scrollbar { width: 4px; }
        .output-stream::-webkit-scrollbar-track { background: transparent; }
        .output-stream::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; }
        .output-stream::-webkit-scrollbar-thumb:hover { background: #333; }

        .tree-animation {
          display: flex;
          justify-content: center;
          align-items: center;
        }
      `}</style>
    </div>
  );
}
