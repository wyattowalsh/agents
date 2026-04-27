import { Check, Copy } from 'lucide-react';
import * as React from 'react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type InstallCommandProps = {
  command: string;
  title?: string;
  note?: string;
  className?: string;
};

export default function InstallCommand({ command, title = 'Install command', note, className }: InstallCommandProps) {
  const [copied, setCopied] = React.useState(false);

  async function copyCommand() {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <section className={cn('my-6 overflow-hidden rounded-lg border border-border bg-[color:var(--surface-panel)]', className)}>
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div className="min-w-0">
          <p className="m-0 text-sm font-semibold text-foreground">{title}</p>
          {note ? <p className="m-0 mt-1 text-xs text-muted-foreground">{note}</p> : null}
        </div>
        <Button type="button" size="sm" variant="secondary" onClick={copyCommand} aria-label="Copy install command">
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </Button>
      </div>
      <pre className="agents-scrollbar m-0 max-w-full overflow-x-auto p-4 text-sm leading-6">
        <code className="block min-w-max whitespace-pre font-mono">{command}</code>
      </pre>
    </section>
  );
}
