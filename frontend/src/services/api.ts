import axios from "axios";
import { Message, ChatHistoryResponse, QueryResponse } from "../types/chat";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

export const chatService = {
    getChatHistory: async (sessionId: string = "default"): Promise<ChatHistoryResponse> => {
        const response = await api.get<ChatHistoryResponse>(`/chat/history?session_id=${sessionId}`);
        return response.data;
    },

    postQuery: async (question: string, filename?: string, sessionId: string = "default", group?: string, filenames?: string[], model?: string): Promise<QueryResponse> => {
        const response = await api.post<QueryResponse>("/query", {
            question,
            filename,
            filenames,
            group,
            session_id: sessionId,
            model,
        });
        return response.data;
    },

    listSessions: async (): Promise<any[]> => {
        const response = await api.get<any[]>("/chat/sessions");
        return response.data;
    },

    listModels: async (): Promise<any[]> => {
        const response = await api.get<any[]>("/models");
        return response.data;
    },

    deleteChatHistory: async (sessionId: string = "default"): Promise<void> => {
        await api.delete(`/chat/history?session_id=${sessionId}`);
    },

    postQueryStream: async (
        question: string,
        onEvent: (event: { type: string; data: any }) => void,
        filename?: string,
        sessionId: string = "default",
        group?: string,
        filenames?: string[],
        model?: string,
    ): Promise<void> => {
        const response = await fetch(`${API_BASE_URL}/query/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, filename, filenames, group, session_id: sessionId, model }),
        });

        if (!response.ok) throw new Error(`Stream failed: ${response.statusText}`);
        if (!response.body) throw new Error("No response body");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    try {
                        const event = JSON.parse(line.slice(6));
                        onEvent(event);
                    } catch {
                        // Skip malformed events
                    }
                }
            }
        }
    },
};

export default api;
