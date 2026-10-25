import { vi, describe, it, expect, beforeEach } from 'vitest';
import { resolveApiBase, api, streamChat } from './api';

describe('resolveApiBase', () => {
  it('appends /api to a host-only URL', () => {
    expect(resolveApiBase('https://nexora-efxd.onrender.com')).toBe('https://nexora-efxd.onrender.com/api');
  });

  it('does not duplicate /api', () => {
    expect(resolveApiBase('https://nexora-efxd.onrender.com/api')).toBe('https://nexora-efxd.onrender.com/api');
  });

  it('trims trailing slashes', () => {
    expect(resolveApiBase('https://nexora-efxd.onrender.com/api/')).toBe('https://nexora-efxd.onrender.com/api');
  });

  it('falls back to /api when empty', () => {
    expect(resolveApiBase('')).toBe('/api');
    expect(resolveApiBase(undefined)).toBe('/api');
  });
});

describe('API URL construction', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('calls health with /api/health', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'ok', provider: 'openai', model: 'm', configured: true }),
    });
    vi.stubGlobal('fetch', fetchMock);
    await api.health();
    expect(fetchMock).toHaveBeenCalledWith('/api/health', expect.any(Object));
  });

  it('calls conversations with /api/conversations', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });
    vi.stubGlobal('fetch', fetchMock);
    await api.listConversations();
    expect(fetchMock).toHaveBeenCalledWith('/api/conversations', expect.any(Object));
  });

  it('streams chat with /api/chat/stream', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: {
        getReader: () => ({
          read: async () => ({ done: true, value: undefined }),
        }),
      },
    });
    vi.stubGlobal('fetch', fetchMock);
    await streamChat(null, 'hi', {});
    expect(fetchMock).toHaveBeenCalledWith('/api/chat/stream', expect.any(Object));
  });
});
