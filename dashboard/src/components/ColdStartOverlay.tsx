import { Loader2 } from 'lucide-react';

export default function ColdStartOverlay() {
  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-950/85 backdrop-blur-xl"
      role="status"
      aria-live="polite"
    >
      <div className="glass-strong mx-4 flex max-w-md flex-col items-center gap-7 rounded-2xl p-10 text-center">
        <span className="text-sm font-medium uppercase tracking-[0.32em] text-ink-primary">
          Aegis
        </span>

        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-ink-secondary" />
          <div className="text-base font-semibold text-ink-primary">
            Connecting to audit engine
          </div>
        </div>

        <p className="max-w-[34ch] text-[0.8125rem] leading-relaxed text-ink-secondary">
          The audit engine may take up to 60 seconds to wake up if it has been
          idle. This is expected behavior on the free hosting tier.
        </p>
      </div>
    </div>
  );
}
