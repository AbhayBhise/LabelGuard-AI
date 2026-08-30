export type ComplianceStatus = "COMPLIANT" | "NON_COMPLIANT" | "PARTIAL";

const styles: Record<ComplianceStatus, string> = {
  COMPLIANT: "bg-success/15 text-success border-success/30",
  NON_COMPLIANT: "bg-danger/15 text-danger border-danger/30",
  PARTIAL: "bg-warning/15 text-warning border-warning/30",
};

const dots: Record<ComplianceStatus, string> = {
  COMPLIANT: "bg-success",
  NON_COMPLIANT: "bg-danger",
  PARTIAL: "bg-warning",
};

export default function ComplianceBadge({
  status,
}: {
  status: ComplianceStatus;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-semibold ${styles[status]}`}
    >
      <span className={`h-2 w-2 rounded-full ${dots[status]}`} />
      {status}
    </span>
  );
}
