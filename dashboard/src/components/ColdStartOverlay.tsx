import { Loader2, ShieldCheck } from 'lucide-react';

export default function ColdStartOverlay() {
  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center bg-slate-950/95 backdrop-blur"
      role="status"
      aria-live="polite"
    >
      <div className="mx-4 flex max-w-md flex-col items-center gap-6 rounded-xl border border-slate-800 bg-slate-900/80 p-8 text-center shadow-2xl">
        <div className="flex items-center gap-3">
          <ShieldCheck className="h-8 w-8 text-rose-500" />
          <span className="text-xl font-bold tracking-[0.3em]">AEGIS</span>
        </div>

        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-10 w-10 animate-spin text-slate-400" />
          <div className="text-base font-semibold text-slate-100">
            Connecting to Aegis...
          </div>
        </div>

        <p className="text-sm leading-relaxed text-slate-400">
          The audit engine may take up to 60 seconds to wake up if it has been
          idle. This is expected behavior on the free hosting tier.
        </p>
      </div>
    </div>
  );
}
