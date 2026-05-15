import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { listFindings, severityColor, type Finding } from '@/lib/api';

export default function Findings() {
  const { data: findings = [], isLoading } = useQuery({
    queryKey: ['findings'],
    queryFn: listFindings,
  });

  const [selected, setSelected] = useState<Finding | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Findings</h1>
        <p className="text-muted-foreground">
          {isLoading ? 'Loading…' : `${findings.length} findings detected.`}
        </p>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[100px]">Rule</TableHead>
            <TableHead>Title</TableHead>
            <TableHead>File</TableHead>
            <TableHead>Severity</TableHead>
            <TableHead className="w-[100px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {findings.map((f) => (
            <TableRow key={f.id}>
              <TableCell className="font-mono text-xs">{f.rule_id}</TableCell>
              <TableCell>{f.rule_title}</TableCell>
              <TableCell className="font-mono text-xs">
                {f.evidence.file}:{f.evidence.line_start}
              </TableCell>
              <TableCell>
                <Badge className={severityColor(f.severity)}>{f.severity}</Badge>
              </TableCell>
              <TableCell>
                <Button variant="outline" size="sm" onClick={() => setSelected(f)}>
                  View
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="max-w-2xl">
          {selected && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  <span className="font-mono text-sm">{selected.rule_id}</span>
                  <span>{selected.rule_title}</span>
                  <Badge className={severityColor(selected.severity)}>{selected.severity}</Badge>
                </DialogTitle>
                <DialogDescription>
                  45 CFR §{selected.cfr.section} — {selected.cfr.title}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 text-sm">
                <div>
                  <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
                    CFR text
                  </div>
                  <p className="rounded-md border bg-muted/50 p-3 italic">{selected.cfr.text}</p>
                </div>

                <div>
                  <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
                    Evidence
                  </div>
                  <div className="font-mono text-xs text-muted-foreground">
                    {selected.evidence.file}:{selected.evidence.line_start}-
                    {selected.evidence.line_end}
                  </div>
                  <pre className="mt-1 overflow-x-auto rounded-md border bg-slate-950 p-3 text-xs text-slate-50">
                    <code>{selected.evidence.snippet}</code>
                  </pre>
                  <p className="mt-2 text-muted-foreground">{selected.evidence.why}</p>
                </div>

                <div>
                  <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
                    Remediation
                  </div>
                  <p>{selected.remediation}</p>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
