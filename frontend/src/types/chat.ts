export interface Message {
    role: "user" | "ai";
    content: string;
    data?: any;
}

export interface ChatHistoryResponse extends Array<Message> { }

export interface QueryResponse {
    answer: string;
    [key: string]: any;
}
