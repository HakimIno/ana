"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Send, Bot, User, Zap, ShieldAlert, BarChart3, Info } from "lucide-react";

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
            content: "Hello! I'm your AI Business Analyst. Once you upload a file, I can analyze trends, calculate growth, and provide strategic recommendations based on verified data."
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

            if (!response.ok) throw new Error("Analysis engine unavailable");

            const data = await response.json();
            setMessages(prev => [...prev, { role: "ai", content: data.answer, data: data }]);
        } catch (err: any) {
            setMessages(prev => [...prev, { role: "ai", content: "⚠️ **System Error:** " + err.message }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-interface glass-panel">
            <div className="messages-list" ref={scrollRef}>
                {messages.map((msg, i) => (
                    <div key={i} className={`message-wrapper ${msg.role}`}>
                        <div className={`avatar ${msg.role}`}>
                            {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                        </div>
                        <div className={`message ${msg.role === 'user' ? 'message-user' : 'message-ai'}`}>
                            <div className="content">
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>

                            {msg.data && msg.data.key_metrics && Object.keys(msg.data.key_metrics).length > 0 && (
                                <div className="analysis-summary">
                                    <div className="section-header">
                                        <BarChart3 size={14} className="icon-emerald" />
                                        <span>Key Metrics</span>
                                    </div>
                                    <div className="metrics-grid">
                                        {Object.entries(msg.data.key_metrics).map(([key, val]: any) => (
                                            <div key={key} className="metric-card">
                                                <span className="key">{key}</span>
                                                <span className="val">{typeof val === 'object' ? val.mean?.toLocaleString() : val}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {msg.data && msg.data.recommendations?.length > 0 && (
                                <div className="ai-section recommendations">
                                    <div className="section-header">
                                        <Zap size={14} className="icon-blue" />
                                        <span>Strategic Advice</span>
                                    </div>
                                    <ul>
                                        {msg.data.recommendations.map((rec: string, idx: number) => (
                                            <li key={idx}>{rec}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {msg.data && msg.data.risks?.length > 0 && (
                                <div className="ai-section risks">
                                    <div className="section-header">
                                        <ShieldAlert size={14} className="icon-rose" />
                                        <span>Detected Risks</span>
                                    </div>
                                    <ul>
                                        {msg.data.risks.map((risk: string, idx: number) => (
                                            <li key={idx}>{risk}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {msg.data && msg.data.confidence_score && (
                                <div className="confidence-score">
                                    <Info size={10} />
                                    Confidence: {Math.round(msg.data.confidence_score * 100)}%
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message-wrapper ai">
                        <div className="avatar ai"><Bot size={16} /></div>
                        <div className="message message-ai loading">
                            <span className="pulse">Analysing data streams...</span>
                        </div>
                    </div>
                )}
            </div>

            <div className="input-area">
                <div className="input-container">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={activeFile ? "Ask a question about your business data..." : "Upload a file to begin analysis"}
                        disabled={!activeFile || isLoading}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    />
                    <button
                        className="send-button"
                        onClick={handleSend}
                        disabled={!activeFile || isLoading || !input.trim()}
                    >
                        <Send size={18} />
                    </button>
                </div>
            </div>

            <style jsx>{`
        .chat-interface {
          height: 100%;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          background: rgba(255, 255, 255, 0.01);
        }

        .messages-list {
          flex-grow: 1;
          overflow-y: auto;
          padding: 32px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .message-wrapper {
          display: flex;
          gap: 16px;
          width: 100%;
        }

        .message-wrapper.user { flex-direction: row-reverse; }

        .avatar {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          margin-top: 4px;
        }

        .avatar.ai { background: rgba(16, 185, 129, 0.1); color: var(--accent-color); border: 1px solid rgba(16, 185, 129, 0.2); }
        .avatar.user { background: rgba(59, 130, 246, 0.1); color: var(--accent-secondary); border: 1px solid rgba(59, 130, 246, 0.2); }

        .message {
          max-width: 80%;
          line-height: 1.6;
          font-size: 14px;
        }

        .message.message-ai {
          padding: 8px 0;
          color: var(--text-primary);
        }

        .message.message-user {
          background: rgba(59, 130, 246, 0.1);
          padding: 12px 16px;
          border-radius: 12px 12px 0 12px;
          border: 1px solid rgba(59, 130, 246, 0.1);
        }

        .analysis-summary {
          margin-top: 20px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 12px;
          padding: 16px;
          border: 1px solid var(--border-color);
        }

        .section-header {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 12px;
          color: var(--text-secondary);
        }

        .icon-emerald { color: var(--accent-color); }
        .icon-blue { color: var(--accent-secondary); }
        .icon-rose { color: var(--error); }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
          gap: 12px;
        }

        .metric-card {
          background: rgba(255, 255, 255, 0.02);
          padding: 10px;
          border-radius: 8px;
          border: 1px solid var(--border-color);
        }

        .metric-card .key {
          display: block;
          font-size: 10px;
          color: var(--text-secondary);
          margin-bottom: 4px;
        }

        .metric-card .val {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary);
        }

        .ai-section {
          margin-top: 20px;
        }

        .ai-section ul {
          list-style: none;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .ai-section li {
          font-size: 13px;
          background: rgba(255, 255, 255, 0.02);
          padding: 10px 12px;
          border-radius: 8px;
          border-left: 3px solid transparent;
        }

        .recommendations li { border-left-color: var(--accent-secondary); }
        .risks li { border-left-color: var(--error); background: rgba(239, 68, 68, 0.02); }

        .confidence-score {
          margin-top: 16px;
          font-size: 10px;
          color: var(--text-secondary);
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .input-area {
          padding: 24px 32px 32px;
          background: linear-gradient(to top, var(--bg-color), transparent);
        }

        .input-container {
          position: relative;
          display: flex;
          align-items: center;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 4px;
          transition: border-color 0.2s;
        }

        .input-container:focus-within {
          border-color: var(--accent-secondary);
        }

        input {
          flex-grow: 1;
          background: transparent;
          border: none;
          padding: 12px 16px;
          color: white;
          font-size: 14px;
          outline: none;
        }

        .send-button {
          background: var(--accent-secondary);
          color: white;
          border: none;
          width: 40px;
          height: 40px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: transform 0.2s;
        }

        .send-button:hover:not(:disabled) {
          transform: scale(1.05);
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          background: var(--text-secondary);
        }

        .pulse {
          animation: pulse 2s infinite;
          font-size: 12px;
          color: var(--text-secondary);
        }

        @keyframes pulse {
          0% { opacity: 0.5; }
          50% { opacity: 1; }
          100% { opacity: 0.5; }
        }
      `}</style>
        </div>
    );
}
