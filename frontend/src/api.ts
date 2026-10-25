import type { ConversationSummary, ConversationDetail, Health } from './types';

const RAW_BASE = import.meta.env.VITE_API_URL || '/api';
const BASE = RAW_BASE.replace(/\/+$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) msg = data.detail;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  health: () => request<Health>('/health'),
  listConversations: () => request<ConversationSummary[]>('/conversations'),
  getConversation: (id: number) => request<ConversationDetail>(`/conversations/${id}`),
  renameConversation: (id: number, title: string) =>
    request<ConversationSummary>(`/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),
  deleteConversation: (id: number) =>
    request<void>(`/conversations/${id}`, { method: 'DELETE' }),
  chat: (conversationId: number | null, message: string) =>
    request<any>('/chat', {
      method: 'POST',
      body: JSON.stringify({ conversation_id: conversationId, message }),
    }),
};

export interface StreamHandlers {
  onMeta?: (data: any) => void;
  onChunk?: (content: string) => void;
  onDone?: (data: any) => void;
  onError?: (message: string) => void;
}

export async function streamChat(
  conversationId: number | null,
  message: string,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(BASE + '/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, message }),
    signal,
  });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) msg = data.detail;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  if (!res.body) throw new Error('No response body');
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data:')) continue;
      const payload = trimmed.slice(5).trim();
      if (!payload) continue;
      try {
        const data = JSON.parse(payload);
        if (data.type === 'meta') handlers.onMeta?.(data);
        else if (data.type === 'chunk') handlers.onChunk?.(data.content ?? '');
        else if (data.type === 'done') handlers.onDone?.(data);
        else if (data.type === 'error') handlers.onError?.(data.detail ?? 'Unknown error');
      } catch {
        /* ignore malformed */
      }
    }
  }
}
