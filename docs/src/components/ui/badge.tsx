import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'border-border bg-[color:var(--surface-panel)] text-foreground',
        skill: 'border-purple-400/40 bg-purple-500/10 text-purple-200',
        installed: 'border-amber-400/40 bg-amber-500/10 text-amber-200',
        external: 'border-cyan-400/40 bg-cyan-500/10 text-cyan-200',
        success: 'border-emerald-400/40 bg-emerald-500/10 text-emerald-200',
        warning: 'border-orange-400/40 bg-orange-500/10 text-orange-200',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />;
}
