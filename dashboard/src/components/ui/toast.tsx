import * as React from 'react';

import { cn } from '@/lib/utils';

type ToastVariant = 'default' | 'destructive' | 'success';

interface Toast {
  id: number;
  title?: string;
  description?: string;
  variant?: ToastVariant;
  durationMs?: number;
}

interface ToastContextValue {
  toast: (t: Omit<Toast, 'id'>) => void;
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

let _seq = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<Toast[]>([]);

  const dismiss = React.useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = React.useCallback(
    (t: Omit<Toast, 'id'>) => {
      const id = ++_seq;
      const duration = t.durationMs ?? 5000;
      setItems((prev) => [...prev, { ...t, id }]);
      window.setTimeout(() => dismiss(id), duration);
    },
    [dismiss],
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={cn(
              'pointer-events-auto overflow-hidden rounded-md border p-4 shadow-lg backdrop-blur',
              t.variant === 'destructive' &&
                'border-rose-700 bg-rose-950/90 text-rose-50',
              t.variant === 'success' &&
                'border-emerald-700 bg-emerald-950/90 text-emerald-50',
              (!t.variant || t.variant === 'default') &&
                'border-slate-700 bg-slate-900/90 text-slate-50',
            )}
            role="status"
          >
            {t.title && <div className="text-sm font-semibold">{t.title}</div>}
            {t.description && (
              <div className="mt-1 text-xs opacity-90">{t.description}</div>
            )}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
