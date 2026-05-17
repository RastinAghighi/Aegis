import * as React from 'react';

import { cn } from '@/lib/utils';

type DivProps = React.HTMLAttributes<HTMLDivElement>;

interface GlassCardProps extends DivProps {
  interactive?: boolean;
  tone?: 'default' | 'critical' | 'high';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const padMap: Record<NonNullable<GlassCardProps['padding']>, string> = {
  none: 'p-0',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

const toneRing: Record<NonNullable<GlassCardProps['tone']>, string> = {
  default: '',
  critical:
    'before:absolute before:inset-0 before:rounded-[inherit] before:pointer-events-none before:shadow-[inset_0_0_0_1px_rgba(225,29,72,0.35)]',
  high: 'before:absolute before:inset-0 before:rounded-[inherit] before:pointer-events-none before:shadow-[inset_0_0_0_1px_rgba(217,119,6,0.35)]',
};

export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, interactive = false, tone = 'default', padding = 'md', ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'glass relative rounded-xl',
          padMap[padding],
          tone !== 'default' && toneRing[tone],
          interactive &&
            'transition duration-200 ease-out hover:-translate-y-px hover:border-white/15 hover:bg-white/[0.05] hover:shadow-[0_1px_0_rgba(255,255,255,0.08)_inset,0_8px_24px_rgba(0,0,0,0.35)]',
          className,
        )}
        {...props}
      />
    );
  },
);
GlassCard.displayName = 'GlassCard';

export const GlassCardHeader = React.forwardRef<HTMLDivElement, DivProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('mb-4 flex flex-col gap-1.5', className)}
      {...props}
    />
  ),
);
GlassCardHeader.displayName = 'GlassCardHeader';

export const GlassCardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'text-base font-semibold tracking-tight text-ink-primary',
      className,
    )}
    {...props}
  />
));
GlassCardTitle.displayName = 'GlassCardTitle';

export const GlassCardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-ink-secondary', className)}
    {...props}
  />
));
GlassCardDescription.displayName = 'GlassCardDescription';

export const GlassCardEyebrow = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement>
>(({ className, ...props }, ref) => (
  <span
    ref={ref}
    className={cn(
      'text-[0.6875rem] font-semibold uppercase tracking-[0.18em] text-ink-tertiary',
      className,
    )}
    {...props}
  />
));
GlassCardEyebrow.displayName = 'GlassCardEyebrow';
