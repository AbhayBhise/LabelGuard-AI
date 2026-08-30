"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ComplianceBadge, {
  ComplianceStatus,
} from "@/components/ComplianceBadge";
import ViolationAccordion from "@/components/ViolationAccordion";
import ExtractedFieldsTable from "@/components/ExtractedFieldsTable";
import { get } from "@/lib/api";
import { downloadReport } from "@/lib/reports";

type ScanResult = {
  scan_id: string;
  overall_status: string | null;
  compliance_score: number | null;
  status?: string;
  product?: any;
  extracted_fields: any[];
  violations: any[];
  annotated_image_url?: string | null;
};

export default function ScanResultPage() {
  const params = useParams<{ scanId: string }>();
  const [data, setData] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    function load() {
      get<ScanResult>(`/scans/${params.scanId}`)
        .then((d) => {
          if (!alive) return;
          setData(d);
          setLoading(false);
          if (d.status === "processing" || d.status === undefined) {
            setTimeout(load, 2500);
          }
        })
        .catch(() => setLoading(false));
    }
    load();
    return () => {
      alive = false;
    };
  }, [params.scanId]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        Loading scan result…
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex h-64 items-center justify-center text-slate-400">
        Scan not found.
      </div>
    );
  }

  const status: ComplianceStatus =
    data.overall_status === "COMPLIANT"
      ? "COMPLIANT"
      : data.overall_status === "NON_COMPLIANT"
      ? "NON_COMPLIANT"
      : "PARTIAL";

  return (
    <div className="grid grid-cols-5 gap-6">
      <div className="col-span-3 space-y-6">
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold text-slate-900">
                {data.product?.name || "Product Label Scan"}
              </h1>
              <p className="font-mono text-xs text-slate-400">
                Scan {data.scan_id.slice(0, 16)}
              </p>
            </div>
            <div className="text-right">
              <ComplianceBadge status={status} />
              <div className="mt-2 text-sm font-semibold text-slate-700">
                Score: {data.compliance_score ?? "—"}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Rule Violations
          </h2>
          <ViolationAccordion violations={data.violations} />
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Extracted Data
          </h2>
          <ExtractedFieldsTable fields={data.extracted_fields} />
        </div>
      </div>

      <div className="col-span-2 space-y-6">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Label Image
          </h2>
          <div className="flex h-64 items-center justify-center rounded-md bg-slate-100 text-sm text-slate-400">
            {data.annotated_image_url
              ? "Annotated image"
              : "Annotated image will appear here"}
          </div>
          <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500">
            <span className="flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-success" /> Compliant
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-danger" /> Violation
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2.5 w-2.5 rounded-full bg-warning" /> Partial
            </span>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Report Actions
          </h2>
          <div className="space-y-2">
            <button
              onClick={() => downloadReport(data.scan_id, "pdf")}
              className="w-full rounded-md bg-[#1B4FD8] py-2 text-sm font-semibold text-white hover:bg-[#1740ad]"
            >
              📥 Download PDF Report
            </button>
            <button
              onClick={() => downloadReport(data.scan_id, "docx")}
              className="w-full rounded-md border border-slate-300 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              📝 Download DOCX Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
