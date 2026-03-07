/**
 * Yahboom webapp API client. Uses relative URLs so Vite proxy (/api -> backend) works.
 * Backend: http://localhost:10792 (start.ps1).
 */

const API_BASE = '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...options?.headers },
        ...options,
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
    }
    return res.json() as Promise<T>;
}

export interface Health {
    status: string;
    connected: boolean;
    service?: string;
    timestamp?: string;
}

export interface Telemetry {
    battery: number | null;
    voltage: number | null;
    imu: Record<string, unknown> | null;
    velocity: { linear: number; angular: number };
    position: { x: number; y: number; z: number } | null;
    scan: Record<string, unknown> | null;
    source: 'live' | 'simulated';
    timestamp?: string;
}

export interface OllamaStatus {
    connected: boolean;
    base_url: string;
}

export interface OllamaModel {
    name: string;
    size?: number;
    modified_at?: string;
}

export interface OllamaModelsResponse {
    models: OllamaModel[];
    error?: string;
}

export interface LLMSettings {
    provider: string;
    model: string;
}

export interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

export interface ChatResponse {
    message: ChatMessage;
}

export const api = {
    getHealth: () => request<Health>('/api/v1/health'),
    getTelemetry: () => request<Telemetry>('/api/v1/telemetry'),
    postMove: (linear: number, angular: number) =>
        request<{ status: string; command: { linear: number; angular: number } }>(
            `/api/v1/control/move?linear=${encodeURIComponent(linear)}&angular=${encodeURIComponent(angular)}`,
            { method: 'POST' }
        ),
    getOllamaStatus: () => request<OllamaStatus>('/api/v1/settings/ollama/status'),
    getOllamaModels: () => request<OllamaModelsResponse>('/api/v1/settings/ollama/models'),
    getLlmSettings: () => request<LLMSettings>('/api/v1/settings/llm'),
    putLlmSettings: (model: string) =>
        request<LLMSettings>('/api/v1/settings/llm', {
            method: 'PUT',
            body: JSON.stringify({ model }),
        }),
    postChat: (messages: ChatMessage[]) =>
        request<ChatResponse>('/api/v1/chat', {
            method: 'POST',
            body: JSON.stringify({ messages }),
        }),
};
