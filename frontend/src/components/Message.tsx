import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize from 'rehype-sanitize';
import type { Message as Msg } from '../types';

interface Props {
  message: Msg;
  onRetry?: () => void;
}

function CodeBlock({ children }: { children: React.ReactNode }) {
  const [copied, setCopied] = useState(false);
  // extract text
  const text = String(children).replace(/\n$/, '');
  return (
    <div className="group relative my-2">
      <button
        onClick={() => {
          navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        }}
        className="absolute right-2 top-2 rounded bg-border/60 px-2 py-1 text-xs opacity-0 group-hover:opacity-100"
      >
        {copied ? <Check size={12} /> : <Copy size={12} />}
      </button>
      <pre className="overflow-x-auto rounded-lg bg-code p-3 text-sm">{children}</pre>
    </div>
  );
}

export default function Message({ message, onRetry }: Props) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const copyAll = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4 py-2`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-accent text-accent-fg'
            : 'bg-surface border border-border text-fg'
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeSanitize, rehypeHighlight]}
              components={{
                pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
                code: ({ className, children }) =>
                  className ? (
                    <code className={className}>{children}</code>
                  ) : (
                    <code className="rounded bg-code px-1 py-0.5 text-sm">{children}</code>
                  ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        {!isUser && (
          <div className="mt-2 flex items-center gap-2 text-xs text-muted">
            <button onClick={copyAll} className="flex items-center gap-1 hover:text-fg">
              {copied ? <Check size={12} /> : <Copy size={12} />} Copy
            </button>
            {onRetry && (
              <button onClick={onRetry} className="hover:text-fg">
                Retry
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
