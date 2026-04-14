import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Robust Error Boundary that avoids complex dependencies like framer-motion
 * to ensure it can render even when the main app substrate is corrupted.
 */
class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[ErrorBoundary] CRITICAL RENDERING FAILURE:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            width: "100%",
            backgroundColor: "#0a0a0c",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
            fontFamily: "sans-serif",
          }}
        >
          <div
            style={{
              maxWidth: "400px",
              width: "100%",
              backgroundColor: "#0f0f12",
              border: "1px solid rgba(239, 68, 68, 0.2)",
              borderRadius: "32px",
              padding: "40px",
              textAlign: "center",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
              position: "relative",
            }}
          >
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                width: "80px",
                height: "80px",
                borderRadius: "24px",
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                marginBottom: "32px",
                border: "1px solid rgba(239, 68, 68, 0.2)",
              }}
            >
              <AlertTriangle color="#ef4444" size={40} />
            </div>

            <h1
              style={{
                fontSize: "24px",
                fontWeight: 900,
                color: "white",
                marginBottom: "16px",
                textTransform: "uppercase",
              }}
            >
              Subsystem Failure
            </h1>
            <p
              style={{ color: "#94a3b8", fontSize: "14px", lineHeight: 1.6, marginBottom: "40px" }}
            >
              The G1 Mission Control interface encountered a critical rendering exception. Virtual
              telemetry link may be unstable.
            </p>

            <div
              style={{
                padding: "16px",
                backgroundColor: "rgba(0, 0, 0, 0.4)",
                borderRadius: "16px",
                border: "1px solid rgba(255, 255, 255, 0.05)",
                fontFamily: "monospace",
                fontSize: "10px",
                color: "rgba(248, 113, 113, 0.8)",
                marginBottom: "32px",
                textAlign: "left",
                wordBreak: "break-all",
              }}
            >
              {this.state.error?.message || "Unknown Execution Error"}
            </div>

            <button
              onClick={this.handleReset}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "12px",
                padding: "16px",
                backgroundColor: "#dc2626",
                color: "white",
                borderRadius: "16px",
                fontWeight: "bold",
                textTransform: "uppercase",
                cursor: "pointer",
                border: "none",
              }}
            >
              <RefreshCcw size={18} />
              Restart Substrate
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
