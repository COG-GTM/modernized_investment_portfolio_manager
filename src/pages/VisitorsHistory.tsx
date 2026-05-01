import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, SkeletonLoader, Alert } from '../components';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '../components/ui/table';
import { fetchVisitorsHistory, ApiError } from '../services/api';
import type { VisitorsHistoryResponse } from '../services/api';

export default function VisitorsHistory() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<VisitorsHistoryResponse | null>(null);

  useEffect(() => {
    const loadVisitors = async () => {
      try {
        const result = await fetchVisitorsHistory();
        setData(result);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('An unexpected error occurred while loading visitors history.');
        }
      } finally {
        setLoading(false);
      }
    };

    loadVisitors();
  }, []);

  const formatTimestamp = (ts: string) => {
    const date = new Date(ts);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <Link to={ROUTES.MAIN_MENU}>
              <Button variant="secondary" size="sm">
                ← Back to Main Menu
              </Button>
            </Link>
          </div>
          <PageHeader
            title="Visitors History"
            subtitle="Track portfolio access and visitor activity"
          />

          <main className="space-y-6 animate-slide-up">
            {error && (
              <Alert variant="destructive" className="animate-fade-in">
                {error}
              </Alert>
            )}

            {loading ? (
              <Card hover className="animate-fade-in">
                <div className="space-y-4">
                  <SkeletonLoader lines={5} />
                  <SkeletonLoader lines={1} height="h-2" />
                </div>
              </Card>
            ) : data ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fade-in">
                  <Card hover>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Total Visits</p>
                      <p className="text-3xl font-bold text-primary">{data.totalVisits}</p>
                    </div>
                  </Card>
                  <Card hover>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Unique Accounts Viewed</p>
                      <p className="text-3xl font-bold text-primary">
                        {new Set(data.visitors.map(v => v.accountNumber)).size}
                      </p>
                    </div>
                  </Card>
                  <Card hover>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Last Updated</p>
                      <p className="text-lg font-medium">{data.lastUpdated}</p>
                    </div>
                  </Card>
                </div>

                <Card hover className="animate-fade-in" style={{ animationDelay: '100ms' }}>
                  <h2 className="text-2xl font-semibold mb-4">Access Log</h2>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Visitor ID</TableHead>
                        <TableHead>Visitor</TableHead>
                        <TableHead>Account</TableHead>
                        <TableHead>Action</TableHead>
                        <TableHead>IP Address</TableHead>
                        <TableHead>Time</TableHead>
                        <TableHead>Duration</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.visitors.map((visitor, index) => (
                        <TableRow
                          key={visitor.visitorId}
                          className="animate-fade-in"
                          style={{ animationDelay: `${index * 50}ms` }}
                        >
                          <TableCell className="font-mono text-xs">{visitor.visitorId}</TableCell>
                          <TableCell className="font-medium">{visitor.visitorName}</TableCell>
                          <TableCell className="font-mono text-sm">{visitor.accountNumber}</TableCell>
                          <TableCell>
                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                              visitor.action === 'Portfolio Inquiry'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-purple-100 text-purple-800'
                            }`}>
                              {visitor.action}
                            </span>
                          </TableCell>
                          <TableCell className="font-mono text-xs text-muted-foreground">
                            {visitor.ipAddress}
                          </TableCell>
                          <TableCell className="text-sm">{formatTimestamp(visitor.timestamp)}</TableCell>
                          <TableCell className="text-sm">{visitor.duration}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              </>
            ) : (
              <Card hover className="animate-fade-in">
                <h2 className="text-2xl font-semibold mb-4">No Visitor Data</h2>
                <p className="text-muted-foreground">
                  No visitor history is available at this time. Visitor records will appear here
                  as users access portfolio accounts.
                </p>
              </Card>
            )}
          </main>
        </div>
      </Container>
    </div>
  );
}
