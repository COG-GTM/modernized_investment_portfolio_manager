import { Component } from 'react';
import type { ReactNode, ErrorInfo } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-8">
          <div className="max-w-lg w-full bg-card border border-border rounded-lg shadow-lg p-8 text-center space-y-6">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold text-destructive">System Error</h1>
              <p className="text-muted-foreground">An unexpected error has occurred</p>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-md p-4 text-left space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-medium text-red-800">Error Code:</span>
                <span className="text-sm text-red-700 font-mono">
                  {this.state.error?.name ?? 'UNKNOWN'}
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-medium text-red-800">Details:</span>
                <span className="text-sm text-red-700">
                  {this.state.error?.message ?? 'No additional details available'}
                </span>
              </div>
            </div>

            <button
              onClick={this.handleReset}
              className="inline-flex items-center justify-center px-6 py-3 bg-primary text-primary-foreground font-medium rounded-md hover:bg-primary/90 transition-smooth focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              Press to Continue
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
