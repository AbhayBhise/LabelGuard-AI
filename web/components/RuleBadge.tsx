type Severity = "CRITICAL" | "MAJOR" | "MINOR";
type VType = "MISSING" | "FORMAT" | "CONTENT" | "FONT_SIZE" | "PASS";

const sevStyles: Record<Severity, string> = {
  CRITICAL: "bg-danger/15 text-danger",
  MAJOR: "bg-warning/15 text-warning",
  MINOR: "bg-slate-100 text-slate-600",
};

export default function RuleBadge({
  ruleId,
  severity,
  type = "MISSING",
}: {
  ruleId: string;
  severity?: Severity;
  type?: VType;
}) {
  const isPass = type === "PASS";
  if (isPass) {
    return (
      <span className="rounded-md border border-success/30 bg-success/15 px-2 py-0.5 text-xs font-semibold text-success">
        PASS
      </span>
    );
  }
  return (
    <span
      className={`rounded-md px-2 py-0.5 text-xs font-semibold ${
        sevStyles[severity || "MAJOR"]
      }`}
    >
      [{severity}] {ruleId}
    </span>
  );
}
