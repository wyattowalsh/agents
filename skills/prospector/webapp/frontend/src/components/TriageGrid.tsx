import type { Opportunity } from "../types";
import { DIMENSION_LABELS, TRIAGE_DIMENSIONS } from "../types";

export function TriageMini({ opp }: { opp: Opportunity }) {
  return (
    <div className="triage-mini">
      {TRIAGE_DIMENSIONS.map((dim) => {
        const val = opp[dim as keyof Opportunity] as string | undefined;
        return (
          <div key={dim} className="td-item">
            <span className="td-label">{DIMENSION_LABELS[dim]}</span>
            <span className={`td-val ${val || ""}`}>{val || "-"}</span>
          </div>
        );
      })}
    </div>
  );
}

export function TriageFull({ opp }: { opp: Opportunity }) {
  return (
    <div className="triage-full">
      {TRIAGE_DIMENSIONS.map((dim) => {
        const val = opp[dim as keyof Opportunity] as string | undefined;
        return (
          <div key={dim} className="tf-item">
            <span className="tf-label">{DIMENSION_LABELS[dim]}</span>
            <span className={`tf-val ${val || ""}`} style={{ color: tierColor(val) }}>
              {val || "-"}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function tierColor(val?: string): string {
  if (val === "strong") return "var(--ok)";
  if (val === "moderate") return "var(--warn)";
  if (val === "weak") return "var(--bad)";
  return "var(--text-2)";
}
