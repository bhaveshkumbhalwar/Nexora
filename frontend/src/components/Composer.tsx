import { useRef, useState } from 'react';
import { Send, Square } from 'lucide-react';

interface Props {
  onSend: (text: string) => void;
  onStop?: () => void;
  disabled: boolean;
  generating: boolean;
}

export default function Composer({ onSend, onStop, disabled, generating }: Props) {
  const [value, setValue] = useState('');
  const ref = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue('');
    if (ref.current) ref.current.style.height = 'auto';
  };

  return (
    <div className="border-t border-border bg-bg p-3">
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-border bg-surface p-2">
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask anything..."
          rows={1}
          disabled={disabled}
          className="flex-1 resize-none bg-transparent px-2 py-1 text-sm outline-none placeholder:text-muted disabled:opacity-60"
        />
        {generating && onStop ? (
          <button
            onClick={onStop}
            className="rounded-lg bg-border p-2 text-fg hover:bg-muted/30"
            aria-label="Stop generating"
          >
            <Square size={16} />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={disabled || !value.trim()}
            className="rounded-lg bg-accent p-2 text-accent-fg disabled:opacity-40"
            aria-label="Send"
          >
            <Send size={16} />
          </button>
        )}
      </div>
      <p className="mt-2 text-center text-xs text-muted">
        Enter to send, Shift+Enter for new line.
      </p>
    </div>
  );
}
