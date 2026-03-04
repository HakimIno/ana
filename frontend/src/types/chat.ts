export interface Message {
    role: "user" | "ai" | "assistant";
    content: string;
    thought?: string;
    python_code?: string;
    data?: any;
}

export interface ChatHistoryResponse extends Array<Message> { }

export interface QueryResponse {
    answer: string;
    [key: string]: any;
}
