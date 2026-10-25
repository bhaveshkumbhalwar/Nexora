import { X } from 'lucide-react';
import type { Health } from '../types';

interface Props {
  health: Health | null;
  theme: 'light' | 'dark';
  onTheme: (t: 'light' | 'dark') => void;
  onClose: () => void;
}

export default function SettingsModal({ health, theme, onTheme, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-surface p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button onClick={onClose} className="text-muted hover:text-fg">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-4 text-sm">
          <div>
            <p className="font-medium">Provider</p>
            <p className="text-muted">{health?.provider ?? '—'} / {health?.model ?? '—'}</p>
            <p className={health?.configured ? 'text-green-600' : 'text-amber-600'}>
              {health?.configured ? 'Configured' : 'Not configured (set LLM_API_KEY)'}
            </p>
          </div>
          <div>
            <p className="mb-2 font-medium">Theme</p>
            <div className="flex gap-2">
              {(['light', 'dark'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => onTheme(t)}
                  className={`rounded-lg border px-3 py-1.5 ${
                    theme === t ? 'border-accent bg-accent text-accent-fg' : 'border-border'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          <p className="text-xs text-muted">
            API keys are stored only on the backend. This app is local, single-user.
          </p>
        </div>
      </div>
    </div>
  );
}
