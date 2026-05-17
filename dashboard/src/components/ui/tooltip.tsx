import * as React from 'react';

import { cn } from '@/lib/utils';

interface TooltipProps {
  label: React.ReactNode;
  children: React.ReactElement;
  side?: 'top' | 'bottom';
  className?: string;
}

export function Tooltip({ label, children, side = 'top', className }: TooltipProps) {
  const [open, setOpen] = React.useState(false);

  const show = () => setOpen(true);
  const hide = () => setOpen(false);

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      <span
        role="tooltip"
        aria-hidden={!open}
        className={cn(
          'pointer-events-none absolute left-1/2 z-50 -translate-x-1/2 whitespace-nowrap rounded-md border border-white/10 bg-slate-900/90 px-2.5 py-1.5 text-xs text-ink-primary shadow-lg backdrop-blur transition-all duration-150',
          side === 'top'
            ? 'bottom-full mb-2 -translate-y-0'
            : 'top-full mt-2 translate-y-0',
          open
            ? 'opacity-100 translate-y-0'
            : 'opacity-0 ' + (side === 'top' ? 'translate-y-1' : '-translate-y-1'),
          className,
        )}
      >
        {label}
      </span>
    </span>
  );
}
