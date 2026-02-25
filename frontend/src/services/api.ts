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

    postQuery: async (question: string, filename?: string, sessionId: string = "default", group?: string, filenames?: string[]): Promise<QueryResponse> => {
        const response = await api.post<QueryResponse>("/query", {
            question,
            filename,
            filenames,
            group,
            session_id: sessionId
        });
        return response.data;
    },

    listSessions: async (): Promise<any[]> => {
        const response = await api.get<any[]>("/chat/sessions");
        return response.data;
    },

    deleteChatHistory: async (sessionId: string = "default"): Promise<void> => {
        await api.delete(`/chat/history?session_id=${sessionId}`);
    },
};

export default api;
