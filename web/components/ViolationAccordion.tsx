"use client";

import { useState } from "react";

type Violation = {
  rule_id: string;
  rule_title?: string;
  violation_type?: string;
  severity?: string;
  finding?: string;
  found_value?: string;
  expected_format?: string;
};

const sevDot: Record<string, string> = {
  CRITICAL: "bg-danger",
  MAJOR: "bg-warning",
  MINOR: "bg-slate-300",
};

export default function ViolationAccordion({
  violations,
}: {
  violations: Violation[];
}) {
  const [open, setOpen] = useState<string | null>(null);

  if (!violations || violations.length === 0) {
    return (
      <div className="rounded-md bg-success/10 p-4 text-sm text-success">
        ✅ No violations found — fully compliant.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {violations.map((v) => {
        const key = `${v.rule_id}-${v.finding}`;
        const isOpen = open === key;
        return (
          <div
            key={key}
            className="overflow-hidden rounded-lg border border-slate-200 bg-white"
          >
            <button
              onClick={() => setOpen(isOpen ? null : key)}
              className="flex w-full items-center justify-between px-4 py-3 text-left"
            >
              <div className="flex items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    sevDot[v.severity || "MAJOR"] || "bg-slate-300"
                  }`}
                />
                <span className="text-sm font-semibold text-slate-800">
                  Rule {v.rule_id} — {v.rule_title}
                </span>
              </div>
              <span className="text-xs text-slate-400">
                {v.severity} {isOpen ? "▲" : "▼"}
              </span>
            </button>
            {isOpen && (
              <div className="border-t border-slate-100 bg-slate-50 px-4 py-3 text-sm">
                {v.finding && (
                  <p className="text-slate-700">
                    <span className="font-semibold">Finding:</span> {v.finding}
                  </p>
                )}
                {v.found_value && (
                  <p className="mt-1 text-slate-600">
                    <span className="font-semibold">Found:</span>{" "}
                    <code className="text-danger">{v.found_value}</code>
                  </p>
                )}
                {v.expected_format && (
                  <p className="mt-1 text-success">
                    <span className="font-semibold">Required:</span>{" "}
                    {v.expected_format}
                  </p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
