import { useEffect, useRef, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import Sidebar, { SidebarToggle } from './components/Sidebar';
import Welcome from './components/Welcome';
import Message from './components/Message';
import Composer from './components/Composer';
import SettingsModal from './components/SettingsModal';
import { api, streamChat } from './api';
import type { ConversationSummary, Message as Msg, Health } from './types';

export default function App() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileDrawer, setMobileDrawer] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('theme') as 'light' | 'dark') || 'light';
  });
  const [lastUserMessage, setLastUserMessage] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const reqIdRef = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef(true);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  const refreshConversations = async () => {
    try {
      setConversations(await api.listConversations());
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    refreshConversations();
  }, []);

  const loadConversation = async (id: number) => {
    setError(null);
    try {
      const detail = await api.getConversation(id);
      setActiveId(id);
      setMessages(detail.messages);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleNew = () => {
    setActiveId(null);
    setMessages([]);
    setError(null);
    setMobileDrawer(false);
  };

  const handleSend = async (text: string) => {
    if (generating) return;
    setError(null);
    setLastUserMessage(text);
    const tempUserId = -Date.now();
    const tempAssistantId = tempUserId - 1;
    setMessages((m) => [
      ...m,
      {
        id: tempUserId,
        conversation_id: activeId ?? 0,
        role: 'user',
        content: text,
        created_at: new Date().toISOString(),
      },
      {
        id: tempAssistantId,
        conversation_id: activeId ?? 0,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
      },
    ]);
    setGenerating(true);
    autoScrollRef.current = true;
    const controller = new AbortController();
    abortRef.current = controller;
    const myReq = ++reqIdRef.current;

    try {
      await streamChat(
        activeId,
        text,
        {
          onMeta: (data) => {
            if (myReq !== reqIdRef.current) return;
            if (data?.conversation_id) setActiveId(data.conversation_id);
          },
          onChunk: (content) => {
            if (myReq !== reqIdRef.current) return;
            setMessages((m) =>
              m.map((msg) =>
                msg.id === tempAssistantId
                  ? { ...msg, content: msg.content + content }
                  : msg,
              ),
            );
          },
          onDone: (data) => {
            if (myReq !== reqIdRef.current) return;
            if (data?.assistant_message_id) {
              setMessages((m) =>
                m.map((msg) =>
                  msg.id === tempAssistantId ? { ...msg, id: data.assistant_message_id } : msg,
                ),
              );
            }
            refreshConversations();
          },
          onError: (message) => {
            if (myReq !== reqIdRef.current) return;
            setError(message);
            setMessages((m) => m.filter((msg) => msg.id !== tempAssistantId));
          },
        },
        controller.signal,
      );
      if (myReq !== reqIdRef.current) return;
    } catch (e) {
      if (myReq !== reqIdRef.current) return;
      if ((e as Error).name !== 'AbortError') {
        setError((e as Error).message);
        setMessages((m) => m.filter((msg) => msg.id !== tempAssistantId));
      }
    } finally {
      if (myReq === reqIdRef.current) setGenerating(false);
      abortRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const handleStop = () => {
    abortRef.current?.abort();
    reqIdRef.current++;
    setGenerating(false);
  };

  const handleRetry = () => {
    if (lastUserMessage) handleSend(lastUserMessage);
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteConversation(id);
      if (activeId === id) handleNew();
      await refreshConversations();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const handleRename = async (id: number, title: string) => {
    try {
      await api.renameConversation(id, title);
      await refreshConversations();
      if (activeId === id) {
        setMessages((m) => m); // no-op
      }
    } catch (e) {
      setError((e as Error).message);
    }
  };

  // auto scroll
  useEffect(() => {
    if (autoScrollRef.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, generating]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    autoScrollRef.current = nearBottom;
  };

  const sidebarProps = {
    conversations,
    activeId,
    onSelect: (id: number) => {
      loadConversation(id);
      setMobileDrawer(false);
    },
    onNew: () => {
      handleNew();
      setMobileDrawer(false);
    },
    onDelete: handleDelete,
    onRename: handleRename,
    onSettings: () => setSettingsOpen(true),
    collapsed: false,
    onToggle: () => setMobileDrawer(false),
  };

  return (
    <div className="flex h-full">
      {/* Desktop sidebar */}
      <div className="hidden md:block">
        <Sidebar {...sidebarProps} collapsed={!sidebarOpen} onToggle={() => setSidebarOpen(false)} />
        {!sidebarOpen && (
          <div className="absolute left-2 top-2 z-10">
            <SidebarToggle onClick={() => setSidebarOpen(true)} />
          </div>
        )}
      </div>

      {/* Mobile drawer */}
      {mobileDrawer && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileDrawer(false)} />
          <div className="relative z-10 h-full">
            <Sidebar {...sidebarProps} collapsed={false} onToggle={() => setMobileDrawer(false)} />
          </div>
        </div>
      )}

      <main className="flex flex-1 flex-col">
        {/* Top bar */}
        <header className="flex items-center justify-between border-b border-border bg-bg px-4 py-3">
          <div className="flex items-center gap-2 md:hidden">
            <button onClick={() => setMobileDrawer(true)} className="text-muted">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <span className="font-semibold">Nexora</span>
          </div>
          <div className="hidden md:block" />
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="rounded p-1 text-muted hover:bg-surface focus:outline-none focus:ring-2 focus:ring-accent"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        {/* Messages */}
        <div ref={scrollRef} onScroll={handleScroll} className="flex-1 overflow-y-auto">
          {messages.length === 0 && !generating ? (
            <Welcome />
          ) : (
            <div className="mx-auto max-w-3xl py-4">
              {messages.map((m) => (
                <Message
                  key={m.id}
                  message={m}
                  onRetry={m.role === 'assistant' ? handleRetry : undefined}
                />
              ))}
              {generating && (
                <div className="flex justify-start px-4 py-2">
                  <div className="rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-muted">
                    <span className="animate-pulse">Thinking…</span>
                  </div>
                </div>
              )}
              {error && (
                <div className="mx-4 my-2 rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-300">
                  {error}
                  {lastUserMessage && (
                    <button onClick={handleRetry} className="ml-2 underline">
                      Retry
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        <Composer onSend={handleSend} onStop={handleStop} disabled={generating} generating={generating} />
      </main>

      {settingsOpen && (
        <SettingsModal
          health={health}
          theme={theme}
          onTheme={setTheme}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </div>
  );
}
