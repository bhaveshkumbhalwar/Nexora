import { Plus, MessageSquare, Trash2, Settings, PanelLeftClose, PanelLeft } from 'lucide-react';
import type { ConversationSummary } from '../types';

interface Props {
  conversations: ConversationSummary[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onNew: () => void;
  onDelete: (id: number) => void;
  onRename: (id: number, title: string) => void;
  onSettings: () => void;
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onRename,
  onSettings,
  collapsed,
  onToggle,
}: Props) {
  return (
    <aside
      className={`flex h-full flex-col border-r border-border bg-surface transition-all ${
        collapsed ? 'w-0 overflow-hidden' : 'w-72'
      }`}
    >
      <div className="flex items-center justify-between px-4 py-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-fg">
            <MessageSquare size={16} />
          </div>
          <span className="font-semibold">Nexora</span>
        </div>
        <button
          onClick={onToggle}
          className="rounded p-1 text-muted hover:bg-bg focus:outline-none focus:ring-2 focus:ring-accent"
          aria-label="Collapse sidebar"
        >
          <PanelLeftClose size={18} />
        </button>
      </div>

      <div className="px-3">
        <button
          onClick={onNew}
          className="flex w-full items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm font-medium hover:bg-bg focus:outline-none focus:ring-2 focus:ring-accent"
        >
          <Plus size={16} /> New chat
        </button>
      </div>

      <div className="mt-3 flex-1 overflow-y-auto px-2">
        {conversations.length === 0 && (
          <p className="px-2 py-4 text-sm text-muted">No conversations yet.</p>
        )}
        {conversations.map((c) => (
          <div
            key={c.id}
            className={`group mb-1 flex items-center rounded-lg px-2 py-2 text-sm ${
              activeId === c.id ? 'bg-bg' : 'hover:bg-bg'
            }`}
          >
            <button
              onClick={() => onSelect(c.id)}
              className="flex-1 truncate text-left"
              title={c.title}
            >
              {c.title}
            </button>
            <button
              onClick={() => {
                const t = prompt('Rename conversation', c.title);
                if (t && t.trim()) onRename(c.id, t.trim());
              }}
              className="opacity-0 group-hover:opacity-100 text-muted hover:text-fg"
              aria-label="Rename"
            >
              ✎
            </button>
            <button
              onClick={() => {
                if (confirm('Delete this conversation?')) onDelete(c.id);
              }}
              className="ml-1 opacity-0 group-hover:opacity-100 text-muted hover:text-red-500"
              aria-label="Delete"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>

      <div className="border-t border-border p-3">
        <button
          onClick={onSettings}
          className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-muted hover:bg-bg focus:outline-none focus:ring-2 focus:ring-accent"
        >
          <Settings size={16} /> Settings
        </button>
      </div>
    </aside>
  );
}

export function SidebarToggle({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="rounded p-1 text-muted hover:bg-surface focus:outline-none focus:ring-2 focus:ring-accent"
      aria-label="Open sidebar"
    >
      <PanelLeft size={18} />
    </button>
  );
}
