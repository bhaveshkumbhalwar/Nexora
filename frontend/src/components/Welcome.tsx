import { Sparkles } from 'lucide-react';

export default function Welcome() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent text-accent-fg">
        <Sparkles size={24} />
      </div>
      <h1 className="text-2xl font-semibold">What would you like to learn today?</h1>
      <p className="mt-2 max-w-md text-sm text-muted">
        Ask questions on programming, science, math, and more. Conversations are saved locally.
      </p>
    </div>
  );
}
