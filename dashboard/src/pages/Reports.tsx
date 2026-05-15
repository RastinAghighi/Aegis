import { useQuery } from '@tanstack/react-query';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { listReports, severityColor } from '@/lib/api';

export default function Reports() {
  const { data: reports = [] } = useQuery({
    queryKey: ['reports'],
    queryFn: listReports,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">Generated audit packages with CFR-linked evidence.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">Export JSON</Button>
          <Button>Export PDF</Button>
        </div>
      </div>

      <Tabs defaultValue={reports[0]?.id ?? 'none'}>
        <TabsList>
          {reports.map((r) => (
            <TabsTrigger key={r.id} value={r.id}>
              {new Date(r.generated_at).toLocaleString()}
            </TabsTrigger>
          ))}
        </TabsList>

        {reports.map((r) => (
          <TabsContent key={r.id} value={r.id} className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>{r.target}</CardTitle>
                <CardDescription>
                  Generated {new Date(r.generated_at).toLocaleString()} — {r.findings.length} findings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {r.findings.map((f) => (
                  <div
                    key={f.id}
                    className="flex items-center justify-between rounded-md border p-3 text-sm"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs text-muted-foreground">{f.rule_id}</span>
                      <span className="font-medium">{f.rule_title}</span>
                    </div>
                    <Badge className={severityColor(f.severity)}>{f.severity}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
