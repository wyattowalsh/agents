import React from "react";

interface State {
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  State
> {
  state: State = { error: null };

  static getDerivedStateFromError(e: Error): State {
    return { error: e };
  }

  render() {
    if (this.state.error) {
      return (
        <div
          className="glass err"
          style={{ margin: "2rem auto", maxWidth: 500 }}
        >
          <h2>Something went wrong</h2>
          <p>{this.state.error.message}</p>
          <button
            style={{ marginTop: "0.75rem" }}
            onClick={() => this.setState({ error: null })}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
